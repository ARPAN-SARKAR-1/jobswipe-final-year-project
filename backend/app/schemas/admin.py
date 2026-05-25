from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.enums import RiskAutoAction, RiskLevel


class AdminReasonRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


class AdminNoteRequest(BaseModel):
    admin_note: str = Field(min_length=3, max_length=1000)


class AdminCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_passwords(self) -> "AdminCreateRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class AdminActionLogRead(BaseModel):
    id: int
    admin_id: int
    action_type: str
    target_type: str
    target_id: int
    reason: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobRiskAssessmentRead(BaseModel):
    id: int
    job_id: int
    risk_score: int
    risk_level: RiskLevel
    reasons: str | None = None
    auto_action: RiskAutoAction
    reviewed_by_admin_id: int | None = None
    reviewed_at: datetime | None = None
    job_title: str | None = None
    company_name: str | None = None
    recruiter_id: int | None = None
    recruiter_name: str | None = None
    moderation_status: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateRiskAssessmentRead(BaseModel):
    id: int
    job_seeker_id: int
    risk_score: int
    risk_level: RiskLevel
    reasons: str | None = None
    reviewed_by_admin_id: int | None = None
    reviewed_at: datetime | None = None
    admin_note: str | None = None
    job_seeker_name: str | None = None
    job_seeker_email: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRiskAssessmentRead(BaseModel):
    id: int
    user_id: int
    risk_score: int
    risk_level: RiskLevel
    reasons: str | None = None
    last_evaluated_at: datetime | None = None
    reviewed_by_admin_id: int | None = None
    reviewed_at: datetime | None = None
    admin_note: str | None = None
    user_name: str | None = None
    user_email: str | None = None
    user_role: str | None = None
    account_status: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
