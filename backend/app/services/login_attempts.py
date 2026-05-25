from fastapi import Request
from sqlalchemy.orm import Session

from app.models.login_attempt import LoginAttempt
from app.services.rate_limiter import client_ip


def record_login_attempt(
    db: Session,
    request: Request,
    email: str,
    role_selected: str | None,
    success: bool,
    failure_reason: str | None = None,
) -> None:
    db.add(
        LoginAttempt(
            email=email.strip().lower(),
            role_selected=role_selected,
            ip_address=client_ip(request),
            success=success,
            failure_reason=failure_reason,
        )
    )
