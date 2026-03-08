"""
UserJob model represents the relationship between a user and a job.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.enums import JobStatus


class UserJob(SQLModel, table=True):
    """
    UserJob model represents the relationship between a user and a job.
    """

    __table_args__ = (UniqueConstraint("user_id", "job_id"),)
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
    """
    UserJobCreateUpdate model is used to create or update a user job.
    """

    job_id: int
    status: JobStatus


class UserJobResponse(BaseModel):
    """
    UserJobResponse model is used to return a user job.
    """

    job_id: int
    status: JobStatus

    model_config = ConfigDict(from_attributes=True)
