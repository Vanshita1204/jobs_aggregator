"""
UserJobPreference model represents the preference of a user for a job.
"""

from datetime import datetime, timezone

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class UserJobPreference(SQLModel, table=True):
    """
    UserJobPreference model represents the preference of a user for a job.
    """

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    keyword: str = Field(index=True)
    is_excluded: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserJobPreferenceCreate(BaseModel):
    """
    UserJobPreferenceCreate model is used to create a user job preference.
    """

    keyword: str
    is_excluded: bool
