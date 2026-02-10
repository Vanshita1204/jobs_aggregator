from sqlmodel import SQLModel, Field
from datetime import datetime

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
