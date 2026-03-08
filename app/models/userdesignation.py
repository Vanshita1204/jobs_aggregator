"""
UserDesignation represents the relationship between
a user and a designation.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class UserDesignation(SQLModel, table=True):
    """
    represents the relationship between a user and a designation.
    """

    __table_args__ = (UniqueConstraint("user_id", "designation_id"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    designation_id: int = Field(foreign_key="designation.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserDesignationCreate(SQLModel):
    """
    UserDesignationCreate model is used to create a new user designation.
    """

    designation_id: int


class UserDesignationRead(SQLModel):
    """
    UserDesignationRead model is used to read a user designation.
    """

    id: Optional[int]
    user_id: int
    designation_id: int
    created_at: datetime
    updated_at: datetime
