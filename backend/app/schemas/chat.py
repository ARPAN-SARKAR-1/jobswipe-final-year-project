from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ChatThreadStatus


def clean_message(value: str) -> str:
    message = value.strip()
    if not message:
        raise ValueError("Message cannot be empty")
    return message


class ChatStartRequest(BaseModel):
    application_id: int
    message_text: str = Field(min_length=1, max_length=1000)

    @field_validator("message_text")
    @classmethod
    def validate_message(cls, value: str) -> str:
        return clean_message(value)


class ChatMessageCreate(BaseModel):
    message_text: str = Field(min_length=1, max_length=1000)

    @field_validator("message_text")
    @classmethod
    def validate_message(cls, value: str) -> str:
        return clean_message(value)


class ChatMessageRead(BaseModel):
    id: int
    thread_id: int
    sender_id: int
    sender_name: str | None = None
    sender_role: str | None = None
    message_text: str
    is_read: bool
    read_at: datetime | None = None
    deleted_for_sender: bool = False
    deleted_for_receiver: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatThreadRead(BaseModel):
    id: int
    application_id: int
    recruiter_id: int
    job_seeker_id: int
    job_id: int
    status: ChatThreadStatus
    started_by_recruiter: bool
    created_at: datetime
    updated_at: datetime
    job_title: str | None = None
    company_name: str | None = None
    recruiter_name: str | None = None
    job_seeker_name: str | None = None
    application_status: str | None = None
    unread_count: int = 0
    last_message: str | None = None
    last_message_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatReadResponse(BaseModel):
    message: str
