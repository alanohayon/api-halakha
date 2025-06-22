from fastapi import APIRouter
from app.api.v1.endpoints import halakhot

api_router = APIRouter()

# Inclure les routes des endpoints
api_router.include_router(halakhot.router, prefix="/halakhot", tags=["halakhot"])
