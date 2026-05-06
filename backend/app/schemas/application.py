from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ApplicationAdminStatus, ApplicationStatus
from app.schemas.job import JobRead


class ApplicationCreate(BaseModel):
    job_id: int
    resume_pdf_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=255)


class ApplicationRead(BaseModel):
    id: int
    job_seeker_id: int
    job_id: int
    resume_pdf_url: str | None = None
    github_url: str | None = None
    status: ApplicationStatus
    admin_status: ApplicationAdminStatus = ApplicationAdminStatus.ACTIVE
    admin_note: str | None = None
    chat_thread_id: int | None = None
    chat_status: str | None = None
    created_at: datetime
    updated_at: datetime
    job: JobRead | None = None

    model_config = ConfigDict(from_attributes=True)


class RecruiterApplicationRead(ApplicationRead):
    applicant_name: str
    applicant_email: str
    applicant_github_url: str | None = None
    applicant_resume_pdf_url: str | None = None
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
