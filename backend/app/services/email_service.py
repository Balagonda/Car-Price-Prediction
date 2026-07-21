"""
AutoWorth AI — Email Service

Sends transactional emails (verification, password reset).
Falls back gracefully when SMTP is not configured (development mode).

Layer: Infrastructure / Service
Dependencies: fastapi-mail, Settings
"""

import logging
from typing import Any

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ──────────────────────────────────────────────
# Mail Configuration
# ──────────────────────────────────────────────
def _get_mail_config() -> ConnectionConfig | None:
    """Build FastMail connection config from settings. Returns None if not configured."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP_USER or SMTP_PASSWORD not configured — email sending disabled."
        )
        return None
    return ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.SMTP_USER,
        MAIL_FROM_NAME=settings.EMAIL_FROM_NAME,
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_HOST,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


class EmailService:
    """
    Sends transactional emails via FastMail/SMTP.

    In development (SMTP not configured), log the email content instead of sending.
    """

    def __init__(self) -> None:
        self._config = _get_mail_config()
        self._mail = FastMail(self._config) if self._config else None

    async def _send(self, subject: str, recipients: list[str], body: str) -> None:
        """Send an HTML email or log it if SMTP is unconfigured."""
        if self._mail is None:
            logger.info(
                "📧 [DEV MODE — Email not sent]\n"
                f"  To: {recipients}\n"
                f"  Subject: {subject}\n"
                f"  Body: {body}"
            )
            return

        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=body,
            subtype=MessageType.html,
        )
        await self._mail.send_message(message)

    async def send_verification_email(
        self, *, to_email: str, first_name: str, token: str
    ) -> None:
        """Send account email verification link."""
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        body = _verification_email_html(first_name=first_name, verify_url=verify_url)
        await self._send(
            subject=f"Verify your {settings.APP_NAME} account",
            recipients=[to_email],
            body=body,
        )

    async def send_password_reset_email(
        self, *, to_email: str, first_name: str, token: str
    ) -> None:
        """Send password reset link."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        body = _reset_email_html(first_name=first_name, reset_url=reset_url)
        await self._send(
            subject=f"Reset your {settings.APP_NAME} password",
            recipients=[to_email],
            body=body,
        )


# ──────────────────────────────────────────────
# Email Templates (inline HTML)
# ──────────────────────────────────────────────
def _verification_email_html(*, first_name: str, verify_url: str) -> str:
    return f"""
    <html><body style="font-family:Inter,sans-serif;background:#0a0a0f;color:#e2e8f0;padding:40px;">
      <div style="max-width:600px;margin:0 auto;background:#1a1a2e;border-radius:16px;padding:40px;">
        <h1 style="color:#6366f1;margin-bottom:8px;">AutoWorth AI</h1>
        <h2 style="margin-top:0;">Verify your email</h2>
        <p>Hi {first_name},</p>
        <p>Thanks for signing up! Please verify your email address to start using AutoWorth AI.</p>
        <a href="{verify_url}"
           style="display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                  color:white;padding:14px 28px;border-radius:8px;text-decoration:none;
                  font-weight:600;margin:16px 0;">
          Verify Email Address
        </a>
        <p style="color:#94a3b8;font-size:14px;">
          This link expires in 24 hours. If you didn't create an account, you can ignore this email.
        </p>
      </div>
    </body></html>
    """


def _reset_email_html(*, first_name: str, reset_url: str) -> str:
    return f"""
    <html><body style="font-family:Inter,sans-serif;background:#0a0a0f;color:#e2e8f0;padding:40px;">
      <div style="max-width:600px;margin:0 auto;background:#1a1a2e;border-radius:16px;padding:40px;">
        <h1 style="color:#6366f1;margin-bottom:8px;">AutoWorth AI</h1>
        <h2 style="margin-top:0;">Reset your password</h2>
        <p>Hi {first_name},</p>
        <p>We received a request to reset your password.</p>
        <a href="{reset_url}"
           style="display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                  color:white;padding:14px 28px;border-radius:8px;text-decoration:none;
                  font-weight:600;margin:16px 0;">
          Reset Password
        </a>
        <p style="color:#94a3b8;font-size:14px;">
          This link expires in 1 hour. If you didn't request this, please ignore this email.
        </p>
      </div>
    </body></html>
    """
