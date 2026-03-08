"""
Job model represents a job.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Job(SQLModel, table=True):
    """
    Job model represents a job.
    """

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    company: str = Field(index=True)
    location: Optional[str] = Field(default=None, index=True)
    description: str
    source: str = Field(index=True)
    source_url: str = Field(unique=True)
    designation_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class JobCreate(SQLModel):
    """
    JobCreate model is used to create a new job.
    """

    title: str
    company: str
    location: Optional[str] = None
    description: str
    source: str
    source_url: str
    designation_id: int


class JobRead(SQLModel):
    """
    JobRead model is used to read a job.
    """

    id: Optional[int]
    title: str
    company: str
    location: Optional[str]
    description: str
    source: str
    source_url: str
    designation_id: int
    created_at: datetime
    updated_at: datetime
