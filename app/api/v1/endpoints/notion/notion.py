from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from app.services.notion_service import NotionService
from app.schemas.notion import NotionPageRequest

router = APIRouter()

# Endpoint pour créer une page Notion
@router.post("/pages")
async def create_notion_page(
    request: NotionPageRequest
):
    """Créer une page dans Notion"""
    service = NotionService()
    try:
        result = await service.create_page(
            parent_id=request.parent_id,
            title=request.title,
            content=request.content
        )
        return {"page_id": result, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la page: {str(e)}"
        )

# Endpoint pour récupérer une page Notion
@router.get("/pages/{page_id}")
async def get_notion_page(
    page_id: str
):
    """Récupérer une page Notion par ID"""
    service = NotionService()
    try:
        result = await service.get_page(page_id)
        return {"page": result, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page non trouvée: {str(e)}"
        )

# Endpoint pour synchroniser les halakhot vers Notion
@router.post("/sync/halakhot")
async def sync_halakhot_to_notion(
    halakha_ids: List[int]
):
    """Synchroniser des halakhot vers Notion"""
    service = NotionService()
    try:
        results = await service.sync_halakhot(halakha_ids)
        return {"synced_pages": results, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la synchronisation: {str(e)}"
        ) 