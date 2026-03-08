"""
Designation model represents a designation.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Designation(SQLModel, table=True):
    """
    represents a designation.
    """

    id: int | None = Field(default=None, primary_key=True)

    title: str = Field(index=True)
    created_by: int | None = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DesignationCreate(SQLModel):
    """
    DesignationCreate model is used to create a new designation.
    """

    title: str


class DesignationRead(SQLModel):
    """
    DesignationRead model is used to read a designation.
    """

    id: Optional[int]
    title: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
