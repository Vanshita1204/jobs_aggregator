from fastapi import APIRouter

from . import auth, designation, job, userdesignation

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(designation.router)
api_router.include_router(job.router)
api_router.include_router(userdesignation.router)
