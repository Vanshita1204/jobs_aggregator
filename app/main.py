from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

import app.models  # noqa: F401
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import RateLimitMiddleware
from app.db.session import engine

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENV == "development":
        # All columns/constraints (is_external, embedding, the
        # designation.title unique index, and the job.designation_id FK)
        # are declared directly on the models now, so create_all() produces
        # the fully correct schema on a fresh DB. No ALTER TABLE/CREATE
        # INDEX patching needed — that was only ever required to retrofit
        # an already-existing jobs.db in place.
        SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(title="Jobs Aggregator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
