from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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
