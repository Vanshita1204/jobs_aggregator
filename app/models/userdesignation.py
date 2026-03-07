from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class UserDesignation(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "designation_id"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    designation_id: int = Field(foreign_key="designation.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserDesignationCreate(SQLModel):
    designation_id: int


class UserDesignationRead(SQLModel):
    id: Optional[int]
    user_id: int
    designation_id: int
    created_at: datetime
    updated_at: datetime


class UserDesignationUpdate(SQLModel):
    designation_id: Optional[int] = None
