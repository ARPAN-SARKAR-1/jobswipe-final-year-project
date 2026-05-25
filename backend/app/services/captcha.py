import hashlib
import random
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.captcha_challenge import CaptchaChallenge
from app.models.security_settings import SecuritySettings

CAPTCHA_TTL_MINUTES = 5


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_captcha_answer(challenge_id: str, answer: str) -> str:
    normalized_answer = answer.strip().lower()
    return hashlib.sha256(f"{challenge_id}:{normalized_answer}".encode("utf-8")).hexdigest()


def get_security_settings(db: Session) -> SecuritySettings:
    settings = db.get(SecuritySettings, 1)
    if settings is None:
        settings = SecuritySettings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def captcha_required_for_flow(db: Session, flow: str) -> bool:
    settings = get_security_settings(db)
    if flow == "login":
        return settings.captcha_login_enabled
    if flow == "signup":
        return settings.captcha_signup_enabled
    if flow in {"forgot_password", "reset_password"}:
        return settings.captcha_forgot_password_enabled
    if flow == "reports":
        return settings.captcha_reports_enabled
    if flow == "company_claims":
        return settings.captcha_company_claims_enabled
    return True


def create_captcha_challenge(db: Session) -> CaptchaChallenge:
    left = random.randint(2, 12)
    right = random.randint(2, 12)
    challenge_id = uuid4().hex
    answer = str(left + right)
    challenge = CaptchaChallenge(
        challenge_id=challenge_id,
        answer_hash=hash_captcha_answer(challenge_id, answer),
        expires_at=utc_now_naive() + timedelta(minutes=CAPTCHA_TTL_MINUTES),
    )
    setattr(challenge, "question", f"What is {left} + {right}?")
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    setattr(challenge, "question", f"What is {left} + {right}?")
    return challenge


def verify_captcha(db: Session, captcha_id: str | None, captcha_answer: str | None, flow: str) -> None:
    if not captcha_required_for_flow(db, flow):
        return
    if not captcha_id or not captcha_answer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CAPTCHA verification failed.")

    challenge = db.scalar(select(CaptchaChallenge).where(CaptchaChallenge.challenge_id == captcha_id))
    if challenge is None or challenge.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CAPTCHA verification failed.")
    if challenge.expires_at < utc_now_naive():
        challenge.used = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CAPTCHA expired. Please try again.")
    if challenge.answer_hash != hash_captcha_answer(challenge.challenge_id, captcha_answer):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CAPTCHA verification failed.")

    challenge.used = True
    db.commit()
