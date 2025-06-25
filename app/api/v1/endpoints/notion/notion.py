import json
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from app.services.notion_service import NotionService, NotionStatus
from app.schemas.notion import NotionPageRequest
from app.schemas.halakha import ProcessCompleteHalakhaResponse
from app.api.deps import get_settings_dependency
from app.core.config import Settings

router = APIRouter()

# Endpoint pour créer une page Notion
@router.post("/page")
async def create_notion_page(
    request: NotionPageRequest,
    settings: Settings = Depends(get_settings_dependency)
):
    """Créer une page dans Notion"""
    notion_service = NotionService(settings)
    try:
        result = await notion_service.create_page(request)
        return {"page_id": result, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la page: {str(e)}"
        )

# Endpoint pour récupérer une page Notion
@router.get("/pages/{page_id}")
async def get_notion_page(
    page_id: str,
    settings: Settings = Depends(get_settings_dependency)
):
    """Récupérer une page Notion par ID"""
    notion_service = NotionService(settings)
    try:
        result = await notion_service.get_page(page_id)
        return {"page": result, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page non trouvée: {str(e)}"
        )

# Endpoint pour synchroniser les halakhot vers Notion
@router.post("/sync/halakhot")
async def sync_halakhot_to_notion(
    halakha_ids: List[int],
    settings: Settings = Depends(get_settings_dependency)
):
    """Synchroniser des halakhot vers Notion"""
    service = NotionService(settings)
    try:
        results = await service.sync_halakhot(halakha_ids)
        return {"synced_pages": results, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la synchronisation: {str(e)}"
        )

# Endpoint pour créer une page post avancée
@router.post("/post")
async def create_notion_post(
    schema_halakha_complet: ProcessCompleteHalakhaResponse,
    add_day: int = 0,
    image_url: str = None,
    settings: Settings = Depends(get_settings_dependency)
):
    """Créer une page post Notion avec données traitées"""
    service = NotionService(settings)
    
    halakha_complet_dict = schema_halakha_complet.model_dump()
    try:
        result = service.create_halakha_page(
            processed_data=halakha_complet_dict,
            add_day=add_day,
            image_url=image_url
        )
        return {"page": result, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du post: {str(e)}"
        ) 