import asyncio
import logging
import smtplib
from app.config.settings import get_settings

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

settings = get_settings()
logger = logging.getLogger(__name__)

def _send_email_sync(
    to_email: str,
    subject: str,
    html: str,
):
    msg = MIMEMultipart("alternative")

    msg["Subject"] = subject
    sender = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    if not sender or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        raise RuntimeError("SMTP is not configured")

    msg["From"] = sender
    msg["To"] = to_email

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT_SECONDS) as server:
        server.starttls()

        server.login(
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
        )

        server.sendmail(
            sender,
            to_email,
            msg.as_string(),
        )

async def send_email(
    to_email: str,
    subject: str,
    html: str,
)-> bool:
    """Send an email without blocking the event loop.

    Account creation remains successful if SMTP is temporarily unavailable; the
    caller can expose a resend-verification endpoint later.
    """
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.warning("SMTP is not configured; verification email was not sent")
        return False

    await asyncio.to_thread(
        _send_email_sync,
        to_email,
        subject,
        html,
    )
    return True
