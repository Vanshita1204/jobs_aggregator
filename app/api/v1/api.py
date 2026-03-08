"""
API endpoints.
"""

from fastapi import APIRouter

from app.api.v1 import auth, designation, job, userdesignation, userjob, userjobpreference

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(designation.router)
api_router.include_router(job.router)
api_router.include_router(userdesignation.router)
api_router.include_router(userjob.router)
api_router.include_router(userjobpreference.router)
