import hmac
import base64
from io import BytesIO
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import randbelow, token_urlsafe
from uuid import uuid4

from fastapi import HTTPException, Response, status
from PIL import Image, ImageDraw, ImageFont
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


def generate_captcha_expression() -> tuple[str, str]:
    operation = randbelow(4)
    if operation == 0:
        left = randbelow(8) + 2
        right = randbelow(8) + 2
        return f"{left} + {right}", str(left + right)
    if operation == 1:
        left = randbelow(8) + 8
        right = randbelow(7) + 2
        return f"{left} - {right}", str(left - right)
    if operation == 2:
        left = randbelow(7) + 2
        right = randbelow(4) + 2
        return f"{left} x {right}", str(left * right)
    divisor = randbelow(7) + 2
    answer = randbelow(7) + 2
    return f"{divisor * answer} / {divisor}", str(answer)


def captcha_image_data_url(expression: str) -> str:
    width = 240
    height = 84
    image = Image.new("RGB", (width, height), "#fbfaf7")
    draw = ImageDraw.Draw(image)
    for _ in range(9):
        color = (160 + randbelow(50), 180 + randbelow(45), 185 + randbelow(45))
        draw.line(
            (
                randbelow(width),
                randbelow(height),
                randbelow(width),
                randbelow(height),
            ),
            fill=color,
            width=1,
        )
    for _ in range(90):
        x = randbelow(width)
        y = randbelow(height)
        color = (120 + randbelow(80), 130 + randbelow(80), 150 + randbelow(80))
        draw.point((x, y), fill=color)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 38)
    except OSError:
        try:
            font = ImageFont.truetype("arial.ttf", 38)
        except OSError:
            font = ImageFont.load_default()

    text_layer = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    text_draw = ImageDraw.Draw(text_layer)
    bbox = text_draw.textbbox((0, 0), expression, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_draw.text(
        ((width - text_width) / 2, (height - text_height) / 2 - 4),
        expression,
        font=font,
        fill=(23, 32, 38, 255),
    )
    rotated = text_layer.rotate(randbelow(7) - 3, resample=Image.Resampling.BICUBIC, center=(width / 2, height / 2))
    image = Image.alpha_composite(image.convert("RGBA"), rotated).convert("RGB")

    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def create_captcha(db: Session, purpose: str) -> CaptchaChallenge:
    normalized_purpose = purpose.strip().lower()
    if normalized_purpose not in CAPTCHA_PURPOSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported CAPTCHA purpose")
    expression, answer = generate_captcha_expression()
    challenge = CaptchaChallenge(
        id=uuid4().hex,
        purpose=normalized_purpose,
        answer_hash=hash_security_value(answer, f"captcha:{normalized_purpose}"),
        question=expression,
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Security check is required")
    normalized_purpose = purpose.strip().lower()
    challenge = db.get(CaptchaChallenge, challenge_id)
    if (
        challenge is None
        or challenge.purpose != normalized_purpose
        or challenge.used_at is not None
        or challenge.expires_at < utcnow()
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired security check")
    expected = hash_security_value(answer.strip(), f"captcha:{normalized_purpose}")
    if not hmac.compare_digest(challenge.answer_hash, expected):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid security check answer")
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


def resend_login_otp_challenge(db: Session, challenge_id: str) -> str:
    challenge = db.get(LoginOTPChallenge, challenge_id)
    now = utcnow()
    if challenge is None or challenge.used_at is not None or challenge.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired login OTP")
    user = db.get(User, challenge.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    latest = db.scalar(
        select(LoginOTPChallenge)
        .where(LoginOTPChallenge.user_id == user.id)
        .order_by(LoginOTPChallenge.created_at.desc(), LoginOTPChallenge.id.desc())
        .limit(1)
    )
    if latest and latest.created_at and (now - latest.created_at).total_seconds() < settings.email_otp_resend_cooldown_seconds:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Please wait before requesting another login OTP")
    challenge.used_at = now
    db.flush()
    return create_login_otp_challenge(db, user)


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
