from datetime import datetime, timedelta, timezone
import logging
from secrets import token_urlsafe
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.models.company_profile import CompanyProfile
from app.models.enums import UserRole
from app.models.job_seeker_profile import JobSeekerProfile
from app.services.trust import get_or_create_recruiter_membership
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.services.email_service import EMAIL_DELIVERY_ERROR
from app.services.public_identity import ensure_company_public_identity, ensure_user_public_identity
from app.schemas.auth import (
    AuthResponse,
    CaptchaResponse,
    EmailOTPRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResendLoginOTPRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserRead,
    VerifyEmailRequest,
    VerifyLoginOTPRequest,
)
from app.services.security_challenges import (
    captcha_image_data_url,
    create_captcha,
    create_email_verification_otp,
    create_login_otp_challenge,
    has_valid_trusted_device,
    remember_trusted_device,
    resend_login_otp_challenge,
    verify_captcha,
    verify_email_otp,
    verify_login_otp_challenge,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
PUBLIC_SIGNUP_ROLES = {UserRole.JOB_SEEKER.value, UserRole.RECRUITER.value}
logger = logging.getLogger(__name__)


def token_response(user: User, message: str = "Authenticated", twofa_recommended: bool = False) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role),
        user=user,
        message=message,
        twofa_recommended=twofa_recommended,
    )


def validate_login_portal(user: User, selected_portal: UserRole) -> None:
    selected_role = selected_portal.value
    allowed_portals = {UserRole.ADMIN.value, UserRole.OWNER.value} if user.role == UserRole.OWNER.value else {user.role}
    if selected_role not in allowed_portals:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account cannot access the selected portal.")


@router.get("/captcha", response_model=CaptchaResponse)
def captcha(
    db: Annotated[Session, Depends(get_db)],
    purpose: str = Query(..., min_length=3, max_length=40),
) -> CaptchaResponse:
    try:
        challenge = create_captcha(db, purpose)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "CAPTCHA challenge creation failed for purpose=%s error_class=%s error=%s",
            purpose,
            exc.__class__.__name__,
            str(exc).splitlines()[0],
        )
        raise
    return CaptchaResponse(
        challenge_id=challenge.id,
        image_base64=captcha_image_data_url(challenge.question),
        purpose=challenge.purpose,
        expires_at=challenge.expires_at,
        expires_in_seconds=max(0, int((challenge.expires_at - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds())),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> AuthResponse:
    if payload.role.value not in PUBLIC_SIGNUP_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Public signup is only available for job seekers and recruiters.")
    verify_captcha(db, "signup", payload.captcha_challenge_id, payload.captcha_answer)
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    email_verified = not settings.email_verification_required
    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=payload.role.value,
        accepted_terms=True,
        accepted_terms_at=now,
        accepted_privacy=True,
        accepted_privacy_at=now,
        email_verified=email_verified,
        email_verified_at=now if email_verified else None,
    )
    db.add(user)
    db.flush()
    ensure_user_public_identity(db, user)

    if payload.role == UserRole.JOB_SEEKER:
        db.add(JobSeekerProfile(user_id=user.id))
    elif payload.role == UserRole.RECRUITER:
        company = CompanyProfile(recruiter_id=user.id)
        db.add(company)
        db.flush()
        ensure_company_public_identity(db, company)
        get_or_create_recruiter_membership(db, user, company)

    if settings.email_verification_required:
        create_email_verification_otp(db, user)
        db.commit()
        db.refresh(user)
        return AuthResponse(
            user=user,
            requires_email_verification=True,
            message="Account created successfully. Please verify your email to continue.",
        )

    db.commit()
    db.refresh(user)
    return token_response(user, message="Registration successful", twofa_recommended=user.role == UserRole.JOB_SEEKER.value)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    verify_captcha(db, "login", payload.captcha_challenge_id, payload.captcha_answer)
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    validate_login_portal(user, payload.selected_portal)
    if settings.email_verification_required and not user.email_verified:
        db.commit()
        return AuthResponse(
            user=user,
            requires_email_verification=True,
            message="Email verification is required before login.",
        )
    if user.role in settings.twofa_required_role_set:
        trusted_token = request.cookies.get(settings.trusted_device_cookie_name)
        if has_valid_trusted_device(db, user, trusted_token):
            db.commit()
            return token_response(user, message="Trusted device recognized")
        try:
            login_challenge_id = create_login_otp_challenge(db, user)
        except HTTPException as exc:
            db.rollback()
            if exc.status_code >= 500:
                logger.error(
                    "Login 2FA email failed role=%s error_class=%s error=%s",
                    user.role,
                    exc.__class__.__name__,
                    str(exc.detail).splitlines()[0],
                )
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=EMAIL_DELIVERY_ERROR) from exc
            raise
        except Exception as exc:
            db.rollback()
            logger.error(
                "Login 2FA email failed role=%s error_class=%s error=%s",
                user.role,
                exc.__class__.__name__,
                str(exc).splitlines()[0],
            )
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=EMAIL_DELIVERY_ERROR) from exc
        db.commit()
        return AuthResponse(
            user=user,
            requires_2fa=True,
            login_challenge_id=login_challenge_id,
            message="Two-factor verification is required.",
        )
    db.commit()
    return token_response(user, twofa_recommended=user.role == UserRole.JOB_SEEKER.value)


@router.get("/me", response_model=UserRead)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Annotated[Session, Depends(get_db)]) -> ForgotPasswordResponse:
    verify_captcha(db, "forgot_password", payload.captcha_challenge_id, payload.captcha_answer)
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    message = "If this email exists, a password reset token has been generated."
    if user is None:
        db.commit()
        return ForgotPasswordResponse(message=message)

    reset_token = token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expiry_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1),
        )
    )
    db.commit()

    reset_url = f"{settings.frontend_url.split(',')[0].rstrip('/')}/reset-password?token={reset_token}"
    if settings.env == "development":
        print(f"[Swipe for Success] Password reset token for {user.email}: {reset_token}")
        return ForgotPasswordResponse(message=message, reset_token=reset_token, reset_url=reset_url)
    return ForgotPasswordResponse(message=message)


@router.post("/send-email-otp")
def send_email_otp(payload: EmailOTPRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user and not user.email_verified:
        create_email_verification_otp(db, user)
        db.commit()
    return {"message": "If this account needs verification, an email OTP has been sent."}


@router.post("/resend-email-otp")
def resend_email_otp(payload: EmailOTPRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user and not user.email_verified:
        create_email_verification_otp(db, user)
        db.commit()
    return {"message": "If this account needs verification, a new email OTP has been sent."}


@router.post("/verify-email", response_model=AuthResponse)
def verify_email(payload: VerifyEmailRequest, db: Annotated[Session, Depends(get_db)]) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.email_verified:
        return AuthResponse(user=user, message="Email is already verified. Please log in to continue.")
    verify_email_otp(db, user, payload.otp)
    db.commit()
    db.refresh(user)
    return token_response(user, message="Email verified successfully. Complete your profile.")


@router.post("/verify-login-otp", response_model=AuthResponse)
def verify_login_otp(
    payload: VerifyLoginOTPRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    user = verify_login_otp_challenge(db, payload.login_challenge_id, payload.otp)
    if settings.email_verification_required and not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email verification is required before login.")
    if payload.remember_device and user.role in settings.twofa_required_role_set:
        remember_trusted_device(db, user, response)
    db.commit()
    db.refresh(user)
    return token_response(user, message="Two-factor verification complete")


@router.post("/resend-login-otp")
def resend_login_otp(payload: ResendLoginOTPRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    try:
        login_challenge_id = resend_login_otp_challenge(db, payload.login_challenge_id)
    except HTTPException as exc:
        db.rollback()
        if exc.status_code >= 500:
            logger.error(
                "Login 2FA resend email failed error_class=%s error=%s",
                exc.__class__.__name__,
                str(exc.detail).splitlines()[0],
            )
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=EMAIL_DELIVERY_ERROR) from exc
        raise
    except Exception as exc:
        db.rollback()
        logger.error(
            "Login 2FA resend email failed error_class=%s error=%s",
            exc.__class__.__name__,
            str(exc).splitlines()[0],
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=EMAIL_DELIVERY_ERROR) from exc
    db.commit()
    return {"message": "New OTP sent. Check inbox or spam.", "login_challenge_id": login_challenge_id}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    record = db.scalar(
        select(PasswordResetToken)
        .where(PasswordResetToken.token == payload.token)
        .where(PasswordResetToken.used.is_(False))
    )
    if record is None or record.expiry_date < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    record.used = True
    db.commit()
    return {"message": "Password reset successful"}
