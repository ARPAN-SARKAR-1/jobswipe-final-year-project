import logging
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import bearer_scheme, create_access_token, decode_access_token, get_current_user, hash_password, verify_password
from app.models.company import Company
from app.models.company_profile import CompanyProfile
from app.models.company_member import CompanyMember
from app.models.enums import AccountStatus, CompanyMemberRole, UserRole
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.recruiter_profile import RecruiterProfile
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserRead,
)
from app.services.captcha import verify_captcha
from app.services.login_attempts import record_login_attempt
from app.services.rate_limiter import rate_limit_key, rate_limiter
from app.services.token_revocation import token_denylist
from app.services.user_risk_assessment import update_user_risk

router = APIRouter(prefix="/auth", tags=["Auth"])
PASSWORD_RESET_MESSAGE = "If an account exists with this email, password reset instructions have been generated."
logger = logging.getLogger(__name__)


def hash_reset_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    verify_captcha(db, payload.captcha_id, payload.captcha_answer, "signup")
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=payload.role.value,
        accepted_terms=True,
        accepted_terms_at=datetime.now(timezone.utc).replace(tzinfo=None),
        accepted_privacy=True,
        accepted_privacy_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(user)
    db.flush()

    if payload.role == UserRole.JOB_SEEKER:
        db.add(JobSeekerProfile(user_id=user.id))
    elif payload.role == UserRole.RECRUITER:
        company = Company(company_name=f"{user.name}'s Company", verification_status="PENDING")
        db.add(company)
        db.flush()
        db.add(RecruiterProfile(user_id=user.id, company_id=company.id, official_email=user.email))
        db.add(
            CompanyMember(
                company_id=company.id,
                user_id=user.id,
                company_role=CompanyMemberRole.COMPANY_OWNER.value,
                verification_status="PENDING",
            )
        )
        db.add(CompanyProfile(recruiter_id=user.id))

    db.commit()
    update_user_risk(db, user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=access_token, user=user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    rate_limiter.check(rate_limit_key("auth:login", request, payload.email), max_attempts=5, window_seconds=10 * 60)
    verify_captcha(db, payload.captcha_id, payload.captcha_answer, "login")
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        record_login_attempt(db, request, str(payload.email), payload.selected_role.value, False, "invalid_credentials")
        if user is not None:
            update_user_risk(db, user)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials or selected role.")
    if user.role != payload.selected_role.value:
        record_login_attempt(db, request, str(payload.email), payload.selected_role.value, False, "role_mismatch")
        update_user_risk(db, user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or selected role.",
        )
    if user.account_status == AccountStatus.SUSPENDED.value:
        record_login_attempt(db, request, str(payload.email), payload.selected_role.value, False, "account_suspended")
        update_user_risk(db, user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is suspended. Please contact support.",
        )
    record_login_attempt(db, request, str(payload.email), payload.selected_role.value, True)
    update_user_risk(db, user)
    db.commit()
    access_token = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=access_token, user=user)


@router.get("/me", response_model=UserRead)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.post("/logout")
def logout(credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]) -> dict[str, str]:
    payload = decode_access_token(credentials.credentials)
    token_denylist.revoke(str(payload["jti"]), int(payload["exp"]))
    return {"message": "Logged out successfully"}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> ForgotPasswordResponse:
    rate_limiter.check(rate_limit_key("auth:forgot-password", request, payload.email), max_attempts=3, window_seconds=15 * 60)
    verify_captcha(db, payload.captcha_id, payload.captcha_answer, "forgot_password")
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None:
        return ForgotPasswordResponse(message=PASSWORD_RESET_MESSAGE)

    reset_token = token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token=hash_reset_token(reset_token),
            expiry_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1),
        )
    )
    db.commit()

    reset_url = f"{settings.frontend_url.split(',')[0].rstrip('/')}/reset-password?token={reset_token}"
    if settings.env.strip().lower() == "development":
        logger.debug("[JobSwipe] Password reset token for %s: %s", user.email, reset_token)
        logger.debug("[JobSwipe] Password reset URL for %s: %s", user.email, reset_url)
    return ForgotPasswordResponse(message=PASSWORD_RESET_MESSAGE)


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    rate_limiter.check(rate_limit_key("auth:reset-password", request, payload.token[:16]), max_attempts=5, window_seconds=15 * 60)
    verify_captcha(db, payload.captcha_id, payload.captcha_answer, "reset_password")
    token_hash = hash_reset_token(payload.token)
    record = db.scalar(
        select(PasswordResetToken)
        .where(or_(PasswordResetToken.token == token_hash, PasswordResetToken.token == payload.token))
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
