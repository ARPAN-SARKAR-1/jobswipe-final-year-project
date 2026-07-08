from datetime import datetime

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ApplicationAdminStatus, ApplicationStatus
from app.schemas.job import JobRead
from app.services.screening import load_screening_answers


class ApplicationCreate(BaseModel):
    job_id: int
    resume_pdf_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=255)
    screening_answers: list[str] | None = None

    @field_validator("screening_answers", mode="before")
    @classmethod
    def normalize_screening_answers(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        if not isinstance(value, list):
            raise ValueError("Screening answers must be a list")
        answers = [str(item or "").strip() for item in value]
        if any(len(answer) > 1200 for answer in answers):
            raise ValueError("Screening answers must be 1200 characters or less")
        return answers


class ScreeningAnswerRead(BaseModel):
    question: str
    answer: str


class ApplicationRead(BaseModel):
    id: int
    job_seeker_id: int
    job_id: int
    resume_pdf_url: str | None = None
    github_url: str | None = None
    screening_answers: list[ScreeningAnswerRead] = Field(default_factory=list)
    status: ApplicationStatus
    admin_status: ApplicationAdminStatus = ApplicationAdminStatus.ACTIVE
    admin_note: str | None = None
    chat_thread_id: int | None = None
    chat_status: str | None = None
    created_at: datetime
    updated_at: datetime
    job: JobRead | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("screening_answers", mode="before")
    @classmethod
    def parse_screening_answers(cls, value: Any) -> list[dict[str, str]]:
        if isinstance(value, str) or value is None:
            return load_screening_answers(value)
        return value


class RecruiterApplicationRead(ApplicationRead):
    applicant_name: str
    applicant_email: str
    applicant_github_url: str | None = None
    applicant_resume_pdf_url: str | None = None
    applicant_skills: str | None = None
    applicant_job_seeker_category: str | None = None
    applicant_student_verification_status: str | None = None
    applicant_graduation_verification_status: str | None = None
    applicant_experience_verification_status: str | None = None
    applicant_passing_year: int | None = None
    applicant_total_experience_years: float | None = None
    applicant_has_accessibility_needs: bool | None = None
    applicant_accessibility_needs: str | None = None
    applicant_accessibility_notes: str | None = None
    applicant_accessibility_visibility: str | None = None
    job_title: str


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationTimelineRead(BaseModel):
    id: int
    application_id: int
    action: str
    old_status: str | None = None
    new_status: str | None = None
    note: str | None = None
    created_by_user_id: int | None = None
    created_by_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
