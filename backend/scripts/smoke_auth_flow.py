from datetime import timedelta
from pathlib import Path
import sys
from unittest.mock import patch
from uuid import uuid4


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.database import Base
from app.core.security import hash_password
from app.models.captcha_challenge import CaptchaChallenge
from app.models.enums import UserRole
from app.models.user import User
from app.routers.auth import login
from app.schemas.auth import LoginRequest
from app.services.security_challenges import hash_security_value, utcnow


PASSWORD = "local-smoke-password-123"


class RequestStub:
    cookies: dict[str, str] = {}


def add_user(db: Session, email: str, role: UserRole) -> User:
    user = User(
        name=f"{role.value.title()} Smoke",
        email=email,
        password_hash=hash_password(PASSWORD),
        role=role.value,
        accepted_terms=True,
        accepted_privacy=True,
        email_verified=True,
        account_status="ACTIVE",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def add_login_captcha(db: Session) -> tuple[str, str]:
    answer = "5"
    challenge = CaptchaChallenge(
        id=uuid4().hex,
        purpose="login",
        answer_hash=hash_security_value(answer, "captcha:login"),
        question="What is 2 + 3?",
        expires_at=utcnow() + timedelta(minutes=5),
    )
    db.add(challenge)
    db.commit()
    return challenge.id, answer


def login_payload(db: Session, email: str, role: UserRole) -> LoginRequest:
    challenge_id, answer = add_login_captcha(db)
    return LoginRequest(
        email=email,
        password=PASSWORD,
        selected_portal=role,
        captcha_challenge_id=challenge_id,
        captcha_answer=answer,
    )


def main() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db, patch("app.services.security_challenges.send_security_code", lambda *_args, **_kwargs: None):
        add_user(db, "owner.smoke@example.com", UserRole.OWNER)
        add_user(db, "jobseeker.smoke@example.com", UserRole.JOB_SEEKER)

        owner_response = login(login_payload(db, "owner.smoke@example.com", UserRole.OWNER), RequestStub(), db)
        print(f"OWNER_REQUIRES_2FA={owner_response.requires_2fa}")
        print(f"OWNER_JWT_RETURNED_BEFORE_OTP={bool(owner_response.access_token)}")
        print(f"OWNER_LOGIN_CHALLENGE_PRESENT={bool(owner_response.login_challenge_id)}")

        jobseeker_response = login(login_payload(db, "jobseeker.smoke@example.com", UserRole.JOB_SEEKER), RequestStub(), db)
        print(f"JOB_SEEKER_JWT_PRESENT={bool(jobseeker_response.access_token)}")
        print(f"JOB_SEEKER_REQUIRES_2FA={jobseeker_response.requires_2fa}")

        try:
            login(login_payload(db, "jobseeker.smoke@example.com", UserRole.RECRUITER), RequestStub(), db)
        except HTTPException as exc:
            print(f"WRONG_PORTAL_REJECTED={exc.status_code == 403}")
        else:
            raise SystemExit("Wrong portal login was not rejected")


if __name__ == "__main__":
    main()
