from typing import Generator

from sqlmodel import Session, create_engine

from app.core.config import settings

# echo=True will print SQL statements; keep False for quieter output
engine = create_engine(settings.DATABASE_URL, echo=False)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
