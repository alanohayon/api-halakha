import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from app.services.notion_service import NotionService, NotionStatus
from app.schemas.notion import NotionPageRequest
from app.schemas.halakha import HalakhaNotionPost, HalakhaNotionInputBrut
from app.api.deps import get_settings_dependency
from app.core.config import Settings
from app.services.processing_service import ProcessingService

router = APIRouter()
logger = logging.getLogger(__name__)

# Endpoint pour créer une page post avancée
@router.post("/post", response_model=HalakhaNotionPost)
async def process_single_halakha(halakha_input: HalakhaNotionInputBrut):
    """
        Post une halakha sur Notion : analyse avec OpenAI et publication sur Notion.
    """
    logger.info(f"Requête reçue pour poster une nouvelle halakha.")
    try:
        
        # On instancie le service d'orchestration avec le client Supabase
        processing_service = ProcessingService()

        # On lance le processus complet
        notion_url = await processing_service.process_halakha_for_notion(
            halakha_content=halakha_input.content,
            add_day_for_notion=halakha_input.schedule_days
        )

        
        return HalakhaNotionPost(notion_page_url=notion_url)

    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête /processing/halakhot: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Une erreur interne est survenue: {str(e)}"
        )

# Endpoint pour créer une page Notion
# @router.post("/page")
# async def create_notion_page(
#     request: NotionPageRequest,
#     settings: Settings = Depends(get_settings_dependency)
# ):
#     """Créer une page dans Notion"""
#     notion_service = NotionService(settings)
#     try:
#         result = await notion_service.create_page(request)
#         return {"page_id": result, "status": "success"}
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur lors de la création de la page: {str(e)}"
#         )

# Endpoint pour récupérer une page Notion
# @router.get("/pages/{page_id}")
# async def get_notion_page(
#     page_id: str,
#     settings: Settings = Depends(get_settings_dependency)
# ):
#     """Récupérer une page Notion par ID"""
#     notion_service = NotionService(settings)
#     try:
#         result = await notion_service.get_page(page_id)
#         return {"page": result, "status": "success"}
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Page non trouvée: {str(e)}"
#         )

# Endpoint pour synchroniser les halakhot vers Notion
# @router.post("/sync/halakhot")
# async def sync_halakhot_to_notion(
#     halakha_ids: List[int],
#     settings: Settings = Depends(get_settings_dependency)
# ):
#     """Synchroniser des halakhot vers Notion"""
#     service = NotionService(settings)
#     try:
#         results = await service.sync_halakhot(halakha_ids)
#         return {"synced_pages": results, "status": "success"}
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur lors de la synchronisation: {str(e)}"
#         )

