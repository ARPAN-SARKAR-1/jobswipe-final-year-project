from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.enums import AccountStatus, UserRole


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    profile_picture_url: str | None = None
    accepted_terms: bool
    accepted_privacy: bool = False
    accepted_terms_at: datetime | None = None
    accepted_privacy_at: datetime | None = None
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

    @model_validator(mode="after")
    def validate_signup(self) -> "RegisterRequest":
        if self.role in {UserRole.ADMIN, UserRole.OWNER}:
            raise ValueError("Public signup cannot create admin or owner accounts.")
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


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


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
