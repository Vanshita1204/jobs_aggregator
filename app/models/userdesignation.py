from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint
from datetime import datetime

class UserDesignation(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "designation"),
    )

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="user.id", index=True)
    designation: str = Field(index=True)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
