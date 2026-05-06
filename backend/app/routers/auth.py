from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.models.company_profile import CompanyProfile
from app.models.enums import UserRole
from app.models.job_seeker_profile import JobSeekerProfile
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

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
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
        db.add(CompanyProfile(recruiter_id=user.id))

    db.commit()
    db.refresh(user)
    access_token = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=access_token, user=user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    access_token = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=access_token, user=user)


@router.get("/me", response_model=UserRead)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Annotated[Session, Depends(get_db)]) -> ForgotPasswordResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    message = "If this email exists, a password reset token has been generated."
    if user is None:
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
        print(f"[JobSwipe] Password reset token for {user.email}: {reset_token}")
        return ForgotPasswordResponse(message=message, reset_token=reset_token, reset_url=reset_url)
    return ForgotPasswordResponse(message=message)


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
