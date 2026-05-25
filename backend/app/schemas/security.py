from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CaptchaChallengeRead(BaseModel):
    captcha_id: str
    question: str


class SecuritySettingsRead(BaseModel):
    id: int
    captcha_login_enabled: bool
    captcha_signup_enabled: bool
    captcha_forgot_password_enabled: bool
    captcha_reports_enabled: bool
    captcha_company_claims_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SecuritySettingsUpdate(BaseModel):
    captcha_login_enabled: bool | None = None
    captcha_signup_enabled: bool | None = None
    captcha_forgot_password_enabled: bool | None = None
    captcha_reports_enabled: bool | None = None
    captcha_company_claims_enabled: bool | None = None
