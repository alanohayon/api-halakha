from fastapi import APIRouter
from app.api.v1.endpoints.halakhot import halakhot, sources, themes, tags
from app.api.v1.endpoints import processing
from app.api.v1.endpoints.openai import openai
from app.api.v1.endpoints.notion import notion
from app.api.v1.endpoints.meta import meta
from app.api.v1.endpoints.whatsapp import whatsapp

api_router = APIRouter()

# Routes principales selon les standards REST
api_router.include_router(halakhot.router, prefix="/halakhot", tags=["Halakhot"])
api_router.include_router(sources.router, prefix="/halakhot/sources", tags=["Sources"])
api_router.include_router(themes.router, prefix="/halakhot/themes", tags=["Themes"])
api_router.include_router(tags.router, prefix="/halakhot/tags", tags=["Tags"])
api_router.include_router(processing.router, prefix="/processing", tags=["Processing"])

# Routes des services externes
api_router.include_router(openai.router, prefix="/openai", tags=["OpenAI"])
api_router.include_router(notion.router, prefix="/notion", tags=["Notion"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["WhatsApp"])

# Routes meta
api_router.include_router(meta.router, prefix="/meta", tags=["Meta"])
