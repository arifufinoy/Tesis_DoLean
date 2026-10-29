import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_password_reset_email(recipient: str, token: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Restablecimiento de contraseña — DoLean"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    reset_url = f"{settings.password_reset_url}?token={token}"
    message.set_content(
        "Recibimos una solicitud para restablecer tu contraseña de DoLean.\n\n"
        f"Usa este enlace antes de {settings.password_reset_expire_minutes} minutos:\n{reset_url}\n\n"
        "Si no solicitaste este cambio, ignora este mensaje."
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=5) as smtp:
        smtp.send_message(message)
    logger.info("Password reset email queued for recipient")

