from fastapi import FastAPI
from api.v1.api import api_router
from sqlmodel import SQLModel

from db.session import engine


app = FastAPI(title="Jobs Aggregator")

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup():
	# Import all models so SQLModel metadata includes every table before creating them
	# Import inside startup to avoid import-time side effects.
	import models.user
	import models.job
	import models.userdesignation

	# Create database tables (SQLite file will be created if missing)
	SQLModel.metadata.create_all(engine)
