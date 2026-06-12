import hmac
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import randbelow, token_urlsafe
from uuid import uuid4

from fastapi import HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.captcha_challenge import CaptchaChallenge
from app.models.email_otp import EmailOTP
from app.models.login_otp_challenge import LoginOTPChallenge
from app.models.trusted_device import TrustedDevice
from app.models.user import User
from app.services.email_service import send_security_code

CAPTCHA_PURPOSES = {"login", "signup", "forgot_password", "report"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_security_value(value: str, purpose: str) -> str:
    return hmac.new(settings.jwt_secret.encode("utf-8"), f"{purpose}:{value}".encode("utf-8"), sha256).hexdigest()


def generate_otp() -> str:
    return f"{randbelow(1_000_000):06d}"


def create_captcha(db: Session, purpose: str) -> CaptchaChallenge:
    normalized_purpose = purpose.strip().lower()
    if normalized_purpose not in CAPTCHA_PURPOSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported CAPTCHA purpose")
    left = randbelow(8) + 2
    right = randbelow(8) + 2
    answer = str(left + right)
    challenge = CaptchaChallenge(
        id=uuid4().hex,
        purpose=normalized_purpose,
        answer_hash=hash_security_value(answer, f"captcha:{normalized_purpose}"),
        question=f"What is {left} + {right}?",
        expires_at=utcnow() + timedelta(minutes=settings.captcha_expire_minutes),
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


def verify_captcha(db: Session, purpose: str, challenge_id: str | None, answer: str | None) -> None:
    if not settings.captcha_enabled:
        return
    if not challenge_id or not answer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CAPTCHA is required")
    normalized_purpose = purpose.strip().lower()
    challenge = db.get(CaptchaChallenge, challenge_id)
    if (
        challenge is None
        or challenge.purpose != normalized_purpose
        or challenge.used_at is not None
        or challenge.expires_at < utcnow()
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired CAPTCHA")
    expected = hash_security_value(answer.strip(), f"captcha:{normalized_purpose}")
    if not hmac.compare_digest(challenge.answer_hash, expected):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CAPTCHA answer")
    challenge.used_at = utcnow()
    db.flush()


def create_email_verification_otp(db: Session, user: User) -> None:
    if user.email_verified:
        return
    now = utcnow()
    latest = db.scalar(
        select(EmailOTP)
        .where(EmailOTP.user_id == user.id)
        .order_by(EmailOTP.created_at.desc(), EmailOTP.id.desc())
        .limit(1)
    )
    if latest and latest.last_sent_at and (now - latest.last_sent_at).total_seconds() < settings.email_otp_resend_cooldown_seconds:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Please wait before requesting another email OTP")
    code = generate_otp()
    db.add(
        EmailOTP(
            user_id=user.id,
            otp_hash=hash_security_value(code, "email-verification"),
            expires_at=now + timedelta(minutes=settings.otp_expire_minutes),
            last_sent_at=now,
        )
    )
    db.flush()
    send_security_code(user.email, code, "Verify your Swipe for Success email")


def verify_email_otp(db: Session, user: User, otp: str) -> None:
    challenge = db.scalar(
        select(EmailOTP)
        .where(EmailOTP.user_id == user.id)
        .where(EmailOTP.used_at.is_(None))
        .order_by(EmailOTP.created_at.desc(), EmailOTP.id.desc())
        .limit(1)
    )
    if challenge is None or challenge.expires_at < utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired email OTP")
    if challenge.attempts >= settings.otp_max_attempts:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Email OTP attempt limit exceeded")
    if not hmac.compare_digest(challenge.otp_hash, hash_security_value(otp.strip(), "email-verification")):
        challenge.attempts += 1
        db.flush()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email OTP")
    now = utcnow()
    challenge.used_at = now
    user.email_verified = True
    user.email_verified_at = now
    db.flush()


def create_login_otp_challenge(db: Session, user: User) -> str:
    code = generate_otp()
    challenge_id = uuid4().hex
    db.add(
        LoginOTPChallenge(
            id=challenge_id,
            user_id=user.id,
            otp_hash=hash_security_value(code, "login-2fa"),
            expires_at=utcnow() + timedelta(minutes=settings.otp_expire_minutes),
        )
    )
    db.flush()
    send_security_code(user.email, code, "Swipe for Success login verification")
    return challenge_id


def verify_login_otp_challenge(db: Session, challenge_id: str, otp: str) -> User:
    challenge = db.get(LoginOTPChallenge, challenge_id)
    if challenge is None or challenge.used_at is not None or challenge.expires_at < utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired login OTP")
    if challenge.attempts >= settings.otp_max_attempts:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Login OTP attempt limit exceeded")
    if not hmac.compare_digest(challenge.otp_hash, hash_security_value(otp.strip(), "login-2fa")):
        challenge.attempts += 1
        db.flush()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid login OTP")
    user = db.get(User, challenge.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    challenge.used_at = utcnow()
    db.flush()
    return user


def has_valid_trusted_device(db: Session, user: User, token: str | None) -> bool:
    if not token:
        return False
    token_hash = hash_security_value(token, "trusted-device")
    trusted_device = db.scalar(
        select(TrustedDevice)
        .where(TrustedDevice.user_id == user.id)
        .where(TrustedDevice.token_hash == token_hash)
        .where(TrustedDevice.revoked_at.is_(None))
        .where(TrustedDevice.expires_at >= utcnow())
        .limit(1)
    )
    if trusted_device is None:
        return False
    trusted_device.last_used_at = utcnow()
    db.flush()
    return True


def remember_trusted_device(db: Session, user: User, response: Response) -> None:
    raw_token = token_urlsafe(48)
    max_age = settings.trusted_device_days * 24 * 60 * 60
    db.add(
        TrustedDevice(
            user_id=user.id,
            token_hash=hash_security_value(raw_token, "trusted-device"),
            expires_at=utcnow() + timedelta(days=settings.trusted_device_days),
        )
    )
    response.set_cookie(
        settings.trusted_device_cookie_name,
        raw_token,
        max_age=max_age,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )
    db.flush()
