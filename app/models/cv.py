from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class UserCV(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    gcs_path: str
    extracted_text: str = Field(default="")
    user_job_id: int | None = Field(default=None, foreign_key="userjob.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserCVRead(BaseModel):
    id: int
    name: str
    gcs_path: str
    user_job_id: Optional[int]
    job_title: Optional[str] = None
    job_company: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCVCreate(BaseModel):
    name: str
    gcs_path: str
    user_job_id: Optional[int] = None
