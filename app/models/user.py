from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    email: str = Field(unique=True, index=True)
    full_name: str
    hashed_password: str

    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    last_login: datetime | None = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserCreate(SQLModel):
    """Request model for creating a user (sent by client)."""

    email: str
    full_name: str
    password: str


class UserRead(SQLModel):
    """Response model returned to clients (omits hashed password)."""

    id: Optional[int]
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
