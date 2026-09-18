"""
JobDesignation represents the many-to-many relationship between
a job and the designations it's visible under.

`Job.designation_id` remains the single "originating" designation a job
was first scraped/added under; this table is the actual source of truth
for feed visibility, since the same real posting can legitimately match
more than one designation search (e.g. "software engineer" and "software
developer" both matching one LinkedIn job) and shouldn't need a duplicate
`Job` row per designation to be visible in each one.
"""

from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class JobDesignation(SQLModel, table=True):
    """
    Links a job to one designation it's visible under.
    """

    __table_args__ = (UniqueConstraint("job_id", "designation_id"),)

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id", index=True)
    designation_id: int = Field(foreign_key="designation.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)
