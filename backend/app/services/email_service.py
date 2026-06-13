import json
import logging
import smtplib
from email.message import EmailMessage
from urllib import request
from urllib.error import HTTPError, URLError

from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)
EMAIL_DELIVERY_ERROR = "Could not send verification email. Please try again later."


def recipient_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower() if "@" in email else "unknown"


def ensure_email_provider_configured() -> None:
    provider = settings.email_provider.lower()
    if not settings.is_production and provider == "console":
        return
    if provider == "resend" and settings.resend_api_key and settings.email_from:
        return
    if provider == "brevo_api" and settings.brevo_api_key and settings.email_from:
        return
    if provider == "smtp" and settings.smtp_host and settings.email_from and settings.smtp_user and settings.smtp_password:
        return
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=EMAIL_DELIVERY_ERROR,
    )


def send_security_code(to_email: str, code: str, subject: str) -> None:
    provider = settings.email_provider.lower()
    if not settings.is_production and provider == "console":
        print(f"[Swipe for Success] {subject} for {to_email}: {code}")
        return
    try:
        ensure_email_provider_configured()
        if provider == "resend":
            send_resend_email(to_email, code, subject)
            return
        if provider == "brevo_api":
            send_brevo_email(to_email, code, subject)
            return
        if provider == "smtp":
            send_smtp_email(to_email, code, subject)
            return
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=EMAIL_DELIVERY_ERROR,
        )
    except HTTPException:
        raise
    except (OSError, smtplib.SMTPException, HTTPError, URLError) as exc:
        logger.error(
            "Security email delivery failed provider=%s recipient_domain=%s error_class=%s error=%s",
            provider,
            recipient_domain(to_email),
            exc.__class__.__name__,
            str(exc).splitlines()[0],
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=EMAIL_DELIVERY_ERROR) from exc


def send_smtp_email(to_email: str, code: str, subject: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from or ""
    message["To"] = to_email
    message.set_content(f"Your Swipe for Success verification code is {code}. It expires in {settings.otp_expire_minutes} minutes.")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)


def security_code_text(code: str) -> str:
    return f"Your Swipe for Success verification code is {code}. It expires in {settings.otp_expire_minutes} minutes."


def security_code_html(code: str) -> str:
    return (
        "<p>Your Swipe for Success verification code is "
        f"<strong>{code}</strong>.</p>"
        f"<p>It expires in {settings.otp_expire_minutes} minutes.</p>"
    )


def send_resend_email(to_email: str, code: str, subject: str) -> None:
    payload = {
        "from": settings.email_from,
        "to": [to_email],
        "subject": subject,
        "text": security_code_text(code),
    }
    req = request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=20) as response:
        if response.status >= 400:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=EMAIL_DELIVERY_ERROR)


def safe_provider_response(exc: HTTPError) -> str:
    try:
        body = exc.read(500).decode("utf-8", errors="replace")
    except Exception:
        return ""
    return " ".join(body.split())[:300]


def send_brevo_email(to_email: str, code: str, subject: str) -> None:
    payload = {
        "sender": {
            "name": settings.email_from_name,
            "email": settings.email_from,
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": security_code_html(code),
        "textContent": security_code_text(code),
    }
    req = request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": settings.brevo_api_key or "",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            if response.status < 200 or response.status >= 300:
                logger.error(
                    "Brevo API email rejected recipient_domain=%s status_code=%s",
                    recipient_domain(to_email),
                    response.status,
                )
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=EMAIL_DELIVERY_ERROR)
    except HTTPError as exc:
        logger.error(
            "Brevo API email failed recipient_domain=%s status_code=%s response=%s",
            recipient_domain(to_email),
            exc.code,
            safe_provider_response(exc),
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=EMAIL_DELIVERY_ERROR) from exc
