import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import InvalidTokenError, create_jwt, decode_jwt, generate_opaque_token, hash_opaque_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Profile, RecoveryToken, RefreshSession, User, UserRole
from app.schemas.auth import ForgotPasswordRequest, LoginRequest, MessageResponse, RefreshTokenRequest, RegisterRequest, ResetPasswordRequest, TokenResponse, UserSummary
from app.services.email import send_password_reset_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def user_response(user: User) -> UserSummary:
    return UserSummary(id=user.id, email=user.email, role=user.role.value, is_active=user.is_active, created_at=user.created_at)


def issue_token_pair(db: Session, user: User) -> TokenResponse:
    session_id = uuid.uuid4()
    access_expiry = timedelta(minutes=settings.access_token_expire_minutes)
    refresh_expiry = timedelta(days=settings.refresh_token_expire_days)
    refresh_token = create_jwt(user.id, "refresh", refresh_expiry, jti=str(session_id))
    db.add(
        RefreshSession(
            id=session_id,
            user_id=user.id,
            token_hash=hash_opaque_token(refresh_token),
            expires_at=utc_now() + refresh_expiry,
        )
    )
    return TokenResponse(
        access_token=create_jwt(user.id, "access", access_expiry),
        refresh_token=refresh_token,
        expires_in=int(access_expiry.total_seconds()),
    )


@router.post("/register", response_model=UserSummary, status_code=status.HTTP_201_CREATED, summary="Registrar un usuario")
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserSummary:
    email = str(payload.email).strip().lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")
    user = User(email=email, password_hash=hash_password(payload.password), role=UserRole.USER)
    user.profile = Profile()
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado") from exc
    return user_response(user)


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or user.password_hash is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La cuenta está desactivada")
    tokens = issue_token_pair(db, user)
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenResponse, summary="Renovar la sesión")
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        claims = decode_jwt(payload.refresh_token, "refresh")
        user_id = uuid.UUID(claims["sub"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido") from exc
    token_hash = hash_opaque_token(payload.refresh_token)
    session = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == token_hash, RefreshSession.revoked_at.is_(None)))
    now = utc_now()
    if session is None:
        logger.warning("Refresh rejected: active session not found")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido o expirado")
    if session.expires_at <= now:
        logger.warning("Refresh rejected: session expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido o expirado")
    if session.user_id != user_id:
        logger.warning("Refresh rejected: token subject does not match session owner")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido o expirado")
    user = db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no disponible")
    session.revoked_at = now
    tokens = issue_token_pair(db, user)
    db.commit()
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Cerrar sesión")
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> Response:
    try:
        decode_jwt(payload.refresh_token, "refresh")
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido") from exc
    session = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == hash_opaque_token(payload.refresh_token)))
    if session is None or session.revoked_at is not None or session.expires_at <= utc_now():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido, expirado o ya revocado")
    session.revoked_at = utc_now()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED, summary="Solicitar recuperación de contraseña")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email, User.is_active.is_(True)))
    if user is not None:
        token = generate_opaque_token()
        db.add(RecoveryToken(user_id=user.id, token_hash=hash_opaque_token(token), expires_at=utc_now() + timedelta(minutes=settings.password_reset_expire_minutes)))
        db.commit()
        try:
            send_password_reset_email(user.email, token)
        except OSError:
            logger.exception("Password reset email could not be delivered")
    return MessageResponse(message="Si el correo existe, recibirás instrucciones para restablecer tu contraseña.")


@router.post("/reset-password", response_model=MessageResponse, summary="Restablecer contraseña")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    token_record = db.scalar(select(RecoveryToken).where(RecoveryToken.token_hash == hash_opaque_token(payload.token), RecoveryToken.used_at.is_(None), RecoveryToken.expires_at > utc_now()))
    if token_record is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El token no es válido o ya expiró")
    user = db.get(User, token_record.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El token no es válido")
    user.password_hash = hash_password(payload.new_password)
    token_record.used_at = utc_now()
    for session in db.scalars(select(RefreshSession).where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None))):
        session.revoked_at = utc_now()
    db.commit()
    return MessageResponse(message="La contraseña fue restablecida correctamente.")

