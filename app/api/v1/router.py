from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.audio_files import router as audio_files_router
from app.api.v1.endpoints.analyses import router as analyses_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(projects_router)
api_router.include_router(audio_files_router)
api_router.include_router(analyses_router)

