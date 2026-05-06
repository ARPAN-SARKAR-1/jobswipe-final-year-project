from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import SwipeAction
from app.schemas.job import JobRead


class SwipeCreate(BaseModel):
    job_id: int
    action: SwipeAction


class SwipeRead(BaseModel):
    id: int
    job_seeker_id: int
    job_id: int
    action: SwipeAction
    created_at: datetime
    job: JobRead | None = None

    model_config = ConfigDict(from_attributes=True)


class UndoSwipeResponse(BaseModel):
    message: str
    undone: SwipeRead | None = None
