from datetime import datetime

from sqlmodel import Field, SQLModel


class Designation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    title: str = Field(index=True)
    created_by: int | None = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
