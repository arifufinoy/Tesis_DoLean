import logging
import smtplib
from datetime import datetime, timezone

import redis
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from minio import Minio

from app.core.config import settings
from app.db.session import check_database_connection
from app.schemas.health import HealthResponse, ReadinessResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


def health_payload() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name, version=settings.app_version, timestamp=datetime.now(timezone.utc))


def readiness_payload() -> tuple[ReadinessResponse, int]:
    checks: dict[str, str] = {}
    try:
        check_database_connection()
        checks["postgresql"] = "ok"
    except Exception:
        logger.exception("PostgreSQL readiness check failed")
        checks["postgresql"] = "unavailable"
    try:
        redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1).ping()
        checks["redis"] = "ok"
    except Exception:
        logger.exception("Redis readiness check failed")
        checks["redis"] = "unavailable"
    try:
        Minio(settings.minio_endpoint, access_key=settings.minio_access_key, secret_key=settings.minio_secret_key, secure=settings.minio_secure).list_buckets()
        checks["minio"] = "ok"
    except Exception:
        logger.exception("MinIO readiness check failed")
        checks["minio"] = "unavailable"
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=1) as smtp:
            smtp.noop()
        checks["mailpit"] = "ok"
    except Exception:
        logger.exception("Mailpit readiness check failed")
        checks["mailpit"] = "unavailable"
    ready = all(value == "ok" for value in checks.values())
    return ReadinessResponse(status="ready" if ready else "not_ready", checks=checks, timestamp=datetime.now(timezone.utc)), status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/health", response_model=HealthResponse, summary="Comprobar que la API está viva")
def health() -> HealthResponse:
    return health_payload()


@router.get("/ready", response_model=ReadinessResponse, summary="Comprobar dependencias de infraestructura")
def ready():
    payload, code = readiness_payload()
    if code != status.HTTP_200_OK:
        return JSONResponse(status_code=code, content=payload.model_dump(mode="json"))
    return payload

