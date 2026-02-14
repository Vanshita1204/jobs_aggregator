from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.api.v1.api import api_router
from app.db.session import engine

app = FastAPI(title="Jobs Aggregator")

# CORS for local development: allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup():
    # Import all models so SQLModel metadata includes every table before creating them
    # Import inside startup to avoid import-time side effects.
    import app.models.designation
    import app.models.job
    import app.models.user
    import app.models.userdesignation

    # Create database tables (SQLite file will be created if missing)
    SQLModel.metadata.create_all(engine)
