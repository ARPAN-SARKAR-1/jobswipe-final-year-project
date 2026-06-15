from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import (
    SupportTicketCategory,
    SupportTicketPriority,
    SupportTicketRoleType,
    SupportTicketStatus,
)


class SupportTicketCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    role_type: SupportTicketRoleType
    category: SupportTicketCategory
    priority: SupportTicketPriority = SupportTicketPriority.MEDIUM
    subject: str = Field(min_length=5, max_length=150)
    message: str = Field(min_length=10, max_length=2000)
    captcha_challenge_id: str | None = None
    captcha_answer: str | None = None


class SupportTicketResponse(BaseModel):
    id: int
    ticket_code: str
    name: str
    email: EmailStr
    role_type: SupportTicketRoleType
    category: SupportTicketCategory
    priority: SupportTicketPriority
    subject: str
    message: str
    status: SupportTicketStatus
    user_id: int | None = None
    assigned_admin_id: int | None = None
    admin_note: str | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    source: str
    email_warning: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SupportTicketListItem(BaseModel):
    id: int
    ticket_code: str
    name: str
    email: EmailStr
    role_type: SupportTicketRoleType
    category: SupportTicketCategory
    priority: SupportTicketPriority
    subject: str
    status: SupportTicketStatus
    user_id: int | None = None
    assigned_admin_id: int | None = None
    admin_note: str | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    source: str

    model_config = ConfigDict(from_attributes=True)


class SupportTicketAdminUpdate(BaseModel):
    status: SupportTicketStatus | None = None
    priority: SupportTicketPriority | None = None
    assigned_admin_id: int | None = None
    admin_note: str | None = Field(default=None, max_length=1000)


class SupportTicketAdminPage(BaseModel):
    items: list[SupportTicketListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class SupportTicketSummary(BaseModel):
    open: int
    in_progress: int
    resolved: int
    closed: int
