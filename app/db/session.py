from typing import Generator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from app.core.config import settings

# echo=True will print SQL statements; keep False for quieter output
engine = create_engine(settings.DATABASE_URL, echo=False)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Turn on FK enforcement for every new SQLite connection (any engine).

    SQLite ships this off by default per-connection, so declared
    `Field(foreign_key=...)` constraints (Designation.created_by,
    UserDesignation.*, UserJob.*, UserCV.*, Job.designation_id) were
    previously advisory only. Registered on the generic `Engine` class
    (not just the module-level `engine` above) so it also covers the
    per-test SQLite engines created in `tests/conftest.py`.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
