from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import (
    CompanyClaimStatus,
    CompanyMemberRole,
    CompanyType,
    CompanyVerificationStatus,
    RecruiterVerificationStatus,
    ReviewModerationStatus,
    RiskLevel,
)
from app.schemas.job import JobRead
from app.services.company_claims import normalize_domain


class CompanyRead(BaseModel):
    id: int
    company_name: str
    company_logo_url: str | None = None
    company_type: CompanyType = CompanyType.OTHER
    industry: str | None = None
    website: str | None = None
    official_email_domain: str | None = None
    description: str | None = None
    headquarters_location: str | None = None
    founded_year: int | None = None
    company_size: str | None = None
    registration_number: str | None = None
    verification_status: CompanyVerificationStatus = CompanyVerificationStatus.PENDING
    verification_note: str | None = None
    verified_by_admin_id: int | None = None
    verified_at: datetime | None = None
    average_rating: float = 0
    total_reviews: int = 0
    active_jobs_count: int = 0
    recruiter_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyRecruiterRead(BaseModel):
    id: int
    user_id: int
    recruiter_name: str
    recruiter_email: str
    designation: str | None = None
    department: str | None = None
    official_email: str | None = None
    recruiter_verification_status: RecruiterVerificationStatus = RecruiterVerificationStatus.PENDING
    account_status: str
    verified_at: datetime | None = None
    average_rating: float = 0
    total_reviews: int = 0


class CompanyDetailRead(CompanyRead):
    recruiters: list[CompanyRecruiterRead] = Field(default_factory=list)
    active_jobs: list[JobRead] = Field(default_factory=list)


class CompanyClaimCreate(BaseModel):
    requested_company_name: str = Field(min_length=2, max_length=160)
    requested_domain: str = Field(min_length=4, max_length=160)
    official_email: EmailStr

    @field_validator("requested_company_name")
    @classmethod
    def clean_company_name(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Company name is required")
        return text

    @field_validator("requested_domain")
    @classmethod
    def clean_domain(cls, value: str) -> str:
        return normalize_domain(value)


class CompanyClaimRead(BaseModel):
    id: int
    company_id: int | None = None
    requested_company_name: str
    requested_domain: str
    requester_user_id: int
    official_email: EmailStr
    claim_status: CompanyClaimStatus
    email_verified_at: datetime | None = None
    reviewed_by_admin_id: int | None = None
    admin_note: str | None = None
    risk_score: int = 0
    risk_level: RiskLevel = RiskLevel.LOW
    requires_admin_review: bool = False
    risk_reasons: str | None = None
    company_name: str | None = None
    requester_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyClaimVerifyRead(BaseModel):
    message: str
    claim: CompanyClaimRead


class CompanyJoinRequestRead(BaseModel):
    id: int
    company_id: int
    user_id: int
    company_role: CompanyMemberRole
    verification_status: RecruiterVerificationStatus
    requested_at: datetime | None = None
    verified_at: datetime | None = None
    verified_by_user_id: int | None = None
    note: str | None = None
    user_name: str | None = None
    user_email: str | None = None
    company_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyMemberRoleUpdate(BaseModel):
    company_role: CompanyMemberRole
    note: str | None = Field(default=None, max_length=1000)


class CompanyMemberActionRequest(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


class CompanyReviewCreate(BaseModel):
    overall_rating: int = Field(ge=1, le=5)
    work_culture_rating: int = Field(ge=1, le=5)
    interview_process_rating: int = Field(ge=1, le=5)
    salary_transparency_rating: int = Field(ge=1, le=5)
    growth_opportunity_rating: int = Field(ge=1, le=5)
    review_title: str | None = Field(default=None, max_length=160)
    review_text: str | None = Field(default=None, max_length=3000)
    pros: str | None = Field(default=None, max_length=1500)
    cons: str | None = Field(default=None, max_length=1500)
    is_anonymous: bool = False

    @field_validator("review_title", "review_text", "pros", "cons")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None


class CompanyReviewRead(BaseModel):
    id: int
    company_id: int
    job_seeker_id: int
    application_id: int | None = None
    rating: int
    overall_rating: int
    work_culture_rating: int
    interview_process_rating: int
    salary_transparency_rating: int
    growth_opportunity_rating: int
    review_title: str | None = None
    review_text: str | None = None
    pros: str | None = None
    cons: str | None = None
    is_anonymous: bool = False
    is_visible: bool = True
    moderation_status: ReviewModerationStatus = ReviewModerationStatus.VISIBLE
    reviewer_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminCompanyReviewRead(CompanyReviewRead):
    company_name: str | None = None
    reviewer_email: str | None = None


class CompanyReviewSummaryRead(BaseModel):
    company_id: int
    average_overall_rating: float = 0
    work_culture_average: float = 0
    interview_process_average: float = 0
    salary_transparency_average: float = 0
    growth_opportunity_average: float = 0
    total_reviews: int = 0
    flagged_reviews: int = 0
    hidden_reviews: int = 0
    top_positive_keywords: list[str] = Field(default_factory=list)
    top_negative_keywords: list[str] = Field(default_factory=list)
