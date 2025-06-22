import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.services.processing_service import ProcessingService
from app.schemas.halakha import HalakhaTextInput, HalakhaProcessResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process-halakha", response_model=HalakhaProcessResponse)
async def process_single_halakha(
    *,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    halakha_input: HalakhaTextInput
):
    """
    Reçoit le texte d'une halakha, le traite avec OpenAI, le sauvegarde
    dans Supabase et le publie sur Notion.
    """
    logger.info(f"Requête reçue pour traiter une nouvelle halakha.")
    try:
        # On instancie le service d'orchestration en lui passant
        # la session de base de données et les configurations.
        processing_service = ProcessingService(db_session=db, settings=settings)

        # On lance le processus complet
        notion_url = await processing_service.process_and_publish_halakha(
            halakha_content=halakha_input.halakha_content,
            add_day_for_notion=halakha_input.schedule_days
        )
        
        return HalakhaProcessResponse(notion_page_url=notion_url)

    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête /process-halakha: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Une erreur interne est survenue: {str(e)}"
        ) 