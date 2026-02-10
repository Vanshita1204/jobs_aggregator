from typing import Generator

from sqlmodel import Session, create_engine

# SQLite file-based DB for local development. Change to env var/DSN in production.
DATABASE_URL = "sqlite:///./jobs.db"

# echo=True will print SQL statements; keep False for quieter output
engine = create_engine(DATABASE_URL, echo=False)


def get_session() -> Generator[Session, None, None]:
	with Session(engine) as session:
		yield session
