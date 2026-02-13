from datetime import datetime
from sqlmodel import SQLModel, Field

class Job(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    title: str = Field(index=True)
    company: str = Field(index=True)
    location: str | None = Field(default=None, index=True)

    description: str
    source: str = Field(index=True)
    source_url: str = Field(unique=True)

    designation_id: int = Field(index=True)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
