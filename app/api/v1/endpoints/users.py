from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.models import Profile, RefreshSession, User
from app.schemas.auth import ChangePasswordRequest, ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def profile_response(user: User) -> ProfileResponse:
    if user.profile is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Perfil no disponible")
    return ProfileResponse(
        id=user.profile.id,
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        display_name=user.profile.display_name,
        bio=user.profile.bio,
        created_at=user.profile.created_at,
        updated_at=user.profile.updated_at,
    )


@router.get("/me", response_model=ProfileResponse, summary="Consultar el perfil autenticado")
def get_my_profile(current_user: User = Depends(get_current_user)) -> ProfileResponse:
    return profile_response(current_user)


@router.patch("/me", response_model=ProfileResponse, summary="Actualizar el perfil autenticado")
def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    if not payload.model_fields_set:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Debe enviar al menos un campo")
    if current_user.profile is None:
        current_user.profile = Profile()
    if "display_name" in payload.model_fields_set:
        current_user.profile.display_name = payload.display_name
    if "bio" in payload.model_fields_set:
        current_user.profile.bio = payload.bio
    db.commit()
    db.refresh(current_user)
    return profile_response(current_user)


@router.put("/me/password", response_model=None, status_code=status.HTTP_204_NO_CONTENT, summary="Cambiar contraseña")
def change_my_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if not verify_password(payload.current_password, current_user.password_hash or ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La contraseña actual no es correcta")
    current_user.password_hash = hash_password(payload.new_password)
    now = utc_now()
    for session in db.scalars(select(RefreshSession).where(RefreshSession.user_id == current_user.id, RefreshSession.revoked_at.is_(None))):
        session.revoked_at = now
    db.commit()
