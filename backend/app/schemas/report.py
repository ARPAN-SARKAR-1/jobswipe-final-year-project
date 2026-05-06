from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReportStatus, ReportType


class ReportCreate(BaseModel):
    report_type: ReportType
    description: str = Field(min_length=10, max_length=1000)


class ReportStatusUpdate(BaseModel):
    status: ReportStatus
    admin_note: str | None = Field(default=None, max_length=1000)


class ReportRead(BaseModel):
    id: int
    reporter_id: int
    job_id: int | None = None
    recruiter_id: int | None = None
    report_type: ReportType
    description: str
    status: ReportStatus
    admin_note: str | None = None
    reporter_name: str | None = None
    reporter_email: str | None = None
    recruiter_name: str | None = None
    recruiter_email: str | None = None
    job_title: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
