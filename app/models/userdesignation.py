from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class UserDesignation(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "designation_id"),)

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="user.id", index=True)
    designation_id: int = Field(foreign_key="designation.id", index=True)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
