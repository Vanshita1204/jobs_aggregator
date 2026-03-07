from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Designation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    title: str = Field(index=True)
    created_by: int | None = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DesignationCreate(SQLModel):
    title: str


class DesignationRead(SQLModel):
    id: Optional[int]
    title: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


class DesignationUpdate(SQLModel):
    title: Optional[str] = None
