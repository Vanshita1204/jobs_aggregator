from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from app.models.enums import JobStatus


class UserJob(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    job_id: int = Field(foreign_key="job.id", index=True)
    status: str = Field(
        default="saved",
        index=True,
        description="saved | applied | interviewed | rejected | irrelevant",
    )
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserJobCreateUpdate(BaseModel):
    job_id: int
    status: JobStatus


class UserJobResponse(BaseModel):
    job_id: int
    status: JobStatus

    class Config:
        from_attributes = True
