"""Create or promote the administrator account using runtime-provided credentials."""

import getpass
import os
import sys
from pathlib import Path

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import Profile, User, UserRole  # noqa: E402


def read_email() -> str:
    value = os.getenv("DOLEAN_ADMIN_EMAIL") or input("Correo del administrador: ")
    try:
        return str(TypeAdapter(EmailStr).validate_python(value)).strip().lower()
    except ValidationError as exc:
        raise SystemExit("El correo del administrador no es válido.") from exc


def read_password() -> str:
    value = os.getenv("DOLEAN_ADMIN_PASSWORD") or getpass.getpass("Contraseña del administrador: ")
    if len(value) < 8:
        raise SystemExit("La contraseña del administrador debe tener al menos 8 caracteres.")
    return value


def main() -> None:
    email = read_email()
    password = read_password()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, password_hash=hash_password(password), role=UserRole.ADMIN, is_active=True)
            user.profile = Profile()
            db.add(user)
            action = "creada"
        else:
            user.password_hash = hash_password(password)
            user.role = UserRole.ADMIN
            user.is_active = True
            if user.profile is None:
                user.profile = Profile()
            action = "actualizada"
        db.commit()
    print(f"Cuenta administrativa {action}: {email}")


if __name__ == "__main__":
    main()
