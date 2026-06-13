from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.enums import AccountStatus, UserRole


class UserRead(BaseModel):
    id: int
    public_user_id: str | None = None
    username: str | None = None
    name: str
    email: EmailStr
    role: UserRole
    profile_picture_url: str | None = None
    bio: str | None = None
    profile_visibility: str = "PUBLIC"
    accepted_terms: bool
    accepted_privacy: bool = False
    accepted_terms_at: datetime | None = None
    accepted_privacy_at: datetime | None = None
    email_verified: bool = False
    email_verified_at: datetime | None = None
    twofa_enabled: bool = False
    account_status: AccountStatus = AccountStatus.ACTIVE
    suspension_reason: str | None = None
    is_protected_owner: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)
    role: UserRole
    accepted_terms: bool
    accepted_privacy: bool
    captcha_challenge_id: str | None = None
    captcha_answer: str | None = None

    @model_validator(mode="after")
    def validate_signup(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        if not self.accepted_terms:
            raise ValueError("Terms and Conditions must be accepted")
        if not self.accepted_privacy:
            raise ValueError("Privacy Policy must be accepted")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    selected_portal: UserRole
    captcha_challenge_id: str | None = None
    captcha_answer: str | None = None


class AuthResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    user: UserRead | None = None
    requires_email_verification: bool = False
    requires_2fa: bool = False
    twofa_recommended: bool = False
    login_challenge_id: str | None = None
    message: str


class TokenResponse(AuthResponse):
    access_token: str
    user: UserRead
    message: str = "Authenticated"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    captcha_challenge_id: str | None = None
    captcha_answer: str | None = None


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: str | None = None
    reset_url: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_new_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_passwords(self) -> "ResetPasswordRequest":
        if self.new_password != self.confirm_new_password:
            raise ValueError("Passwords do not match")
        return self


class EmailOTPRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class VerifyLoginOTPRequest(BaseModel):
    login_challenge_id: str = Field(min_length=10, max_length=80)
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    remember_device: bool = False


class ResendLoginOTPRequest(BaseModel):
    login_challenge_id: str = Field(min_length=10, max_length=80)


class CaptchaResponse(BaseModel):
    challenge_id: str
    question: str
    purpose: str
    expires_at: datetime
