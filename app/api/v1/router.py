from fastapi import APIRouter
from app.api.v1.endpoints import halakhot, processing

api_router = APIRouter()

# Inclure les routes des endpoints
api_router.include_router(halakhot.router, prefix="/halakhot", tags=["halakhot"])
api_router.include_router(processing.router, prefix="/actions", tags=["actions"])
