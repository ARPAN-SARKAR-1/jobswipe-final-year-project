from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import RecruiterVerificationStatus, ReviewModerationStatus


class RecruiterPublicRead(BaseModel):
    id: int
    name: str
    company_id: int | None = None
    company_name: str | None = None
    company_logo_url: str | None = None
    company_verification_status: str | None = None
    designation: str | None = None
    department: str | None = None
    recruiter_verification_status: RecruiterVerificationStatus = RecruiterVerificationStatus.PENDING
    average_rating: float = 0
    total_reviews: int = 0
    active_jobs_count: int = 0
    created_at: datetime


class RecruiterReviewCreate(BaseModel):
    overall_rating: int = Field(ge=1, le=5)
    communication_rating: int = Field(ge=1, le=5)
    response_time_rating: int = Field(ge=1, le=5)
    professionalism_rating: int = Field(ge=1, le=5)
    transparency_rating: int = Field(ge=1, le=5)
    review_title: str | None = Field(default=None, max_length=160)
    review_text: str | None = Field(default=None, max_length=3000)
    is_anonymous: bool = False

    @field_validator("review_title", "review_text")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None


class RecruiterReviewRead(BaseModel):
    id: int
    recruiter_id: int
    job_seeker_id: int
    application_id: int | None = None
    overall_rating: int
    communication_rating: int
    response_time_rating: int
    professionalism_rating: int
    transparency_rating: int
    review_title: str | None = None
    review_text: str | None = None
    is_anonymous: bool = False
    is_visible: bool = True
    moderation_status: ReviewModerationStatus = ReviewModerationStatus.VISIBLE
    reviewer_name: str | None = None
    recruiter_name: str | None = None
    recruiter_email: str | None = None
    company_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecruiterReviewSummaryRead(BaseModel):
    recruiter_id: int
    average_overall_rating: float = 0
    communication_average: float = 0
    response_time_average: float = 0
    professionalism_average: float = 0
    transparency_average: float = 0
    total_reviews: int = 0
    flagged_reviews: int = 0
    hidden_reviews: int = 0
    top_feedback_keywords: list[str] = Field(default_factory=list)


class ReviewAnalyticsRead(BaseModel):
    highest_rated_companies: list[dict] = Field(default_factory=list)
    lowest_rated_companies: list[dict] = Field(default_factory=list)
    most_reviewed_companies: list[dict] = Field(default_factory=list)
    low_rated_recruiters: list[dict] = Field(default_factory=list)
    recent_company_reviews: list[dict] = Field(default_factory=list)
    recent_recruiter_reviews: list[dict] = Field(default_factory=list)
    hidden_reviews_count: int = 0
    flagged_reviews_count: int = 0
