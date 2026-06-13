from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CompanyJoinStatus, CompanyType, CompanyVerificationStatus, RecruiterVerificationStatus, ReviewModerationStatus
from app.schemas.job import JobRead


class RecruiterCompanyMemberRead(BaseModel):
    id: int
    recruiter_id: int
    company_id: int
    recruiter_name: str | None = None
    recruiter_email: str | None = None
    company_name: str | None = None
    designation: str | None = None
    work_email: str | None = None
    verification_status: RecruiterVerificationStatus = RecruiterVerificationStatus.PENDING
    company_join_status: CompanyJoinStatus = CompanyJoinStatus.PENDING
    verified_at: datetime | None = None
    verified_by_admin_id: int | None = None
    verified_by_company_owner_id: int | None = None
    approved_by_admin_id: int | None = None
    approved_at: datetime | None = None
    admin_note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: str = Field(min_length=3, max_length=160)
    review_text: str = Field(min_length=10, max_length=4000)
    work_culture_rating: int | None = Field(default=None, ge=1, le=5)
    interview_process_rating: int | None = Field(default=None, ge=1, le=5)
    growth_rating: int | None = Field(default=None, ge=1, le=5)


class CompanyReviewRead(BaseModel):
    id: int
    company_id: int
    reviewer_user_id: int
    reviewer_name: str | None = None
    application_id: int | None = None
    rating: int
    title: str
    review_text: str
    work_culture_rating: int | None = None
    interview_process_rating: int | None = None
    growth_rating: int | None = None
    is_visible: bool
    is_flagged: bool
    moderation_status: ReviewModerationStatus = ReviewModerationStatus.VISIBLE
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyReviewModerationRequest(BaseModel):
    moderation_status: ReviewModerationStatus
    admin_note: str | None = Field(default=None, max_length=1000)


class CompanyPublicRead(BaseModel):
    id: int
    public_company_id: str | None = None
    slug: str | None = None
    name: str | None = None
    company_name: str | None = None
    logo_url: str | None = None
    company_logo_url: str | None = None
    company_type: CompanyType = CompanyType.OTHER
    industry: str | None = None
    location: str | None = None
    website: str | None = None
    description: str | None = None
    verification_status: CompanyVerificationStatus = CompanyVerificationStatus.PENDING
    average_rating: float | None = None
    review_count: int = 0
    visible_reviews: list[CompanyReviewRead] = []
    verified_recruiter_count: int = 0
    verified_recruiters: list[RecruiterCompanyMemberRead] = []
    active_jobs: list[JobRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
