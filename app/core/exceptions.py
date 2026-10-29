import logging

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "La solicitud no pudo procesarse."
    return JSONResponse(status_code=exc.status_code, headers=exc.headers, content={"error": {"code": f"http_{exc.status_code}", "message": detail}})


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": "La solicitud no es válida.", "details": jsonable_encoder(exc.errors())}})


async def database_exception_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Database error", exc_info=exc)
    return JSONResponse(status_code=503, content={"error": {"code": "database_unavailable", "message": "La base de datos no está disponible."}})


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "Error interno del servidor."}})

