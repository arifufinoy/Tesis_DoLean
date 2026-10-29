from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.endpoints.health import health_payload, readiness_payload
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import database_exception_handler, http_exception_handler, unhandled_exception_handler, validation_exception_handler
from app.core.logging import configure_logging

configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version=settings.app_version, description="API base para análisis y corrección de afinación de audio monofónico.", docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["system"], include_in_schema=True)
def root_health():
    return health_payload()


@app.get("/ready", tags=["system"], include_in_schema=True)
def root_ready():
    payload, code = readiness_payload()
    if code != 200:
        return JSONResponse(status_code=code, content=payload.model_dump(mode="json"))
    return payload

