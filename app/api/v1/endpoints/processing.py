import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.services.processing_service import ProcessingService
from app.services.openai_service import OpenAIService
from app.schemas.halakha import (
    HalakhaTextInput, 
    HalakhaProcessResponse,
    ProcessHalakhaRequest,
    ProcessHalakhaResponse,
    ProcessCompleteHalakhaResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

def get_openai_service(settings: Settings = Depends(get_settings)) -> OpenAIService:
    """Dependency pour obtenir le service OpenAI"""
    return OpenAIService(settings)

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

@router.post("/halakha/analyze", response_model=ProcessHalakhaResponse, tags=["AI Processing"])
async def analyze_halakha(
    request: ProcessHalakhaRequest,
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    Analyser une halakha et extraire les données structurées (question, réponse, sources, etc.)
    
    Cette route utilise OpenAI pour traiter le contenu d'une halakha et en extraire
    les informations structurées comme la question, la réponse, les sources et les thèmes.
    """
    try:
        logger.info("Début de l'analyse de la halakha...")
        
        # Traitement avec OpenAI pour extraire les données structurées
        processed_data = openai_service.process_halakha(request.content)
        
        logger.info("Analyse de la halakha terminée avec succès")
        
        return ProcessHalakhaResponse(
            success=True,
            message="Halakha analysée avec succès",
            **processed_data
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de la halakha : {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de l'analyse de la halakha : {str(e)}"
        )

@router.post("/halakha/complete", response_model=ProcessCompleteHalakhaResponse, tags=["AI Processing"])
async def process_complete_halakha(
    request: ProcessHalakhaRequest,
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    Traitement complet d'une halakha : analyse + génération de contenu pour post
    
    Cette route effectue un traitement complet d'une halakha :
    1. Analyse et extraction des données structurées (question, réponse, sources, etc.)
    2. Génération du texte pour le post Instagram
    3. Génération de la légende pour le post
    
    Tout est traité et retourné dans une seule réponse JSON.
    """
    try:
        logger.info("Début du traitement complet de la halakha...")
        
        # Étape 1: Analyser la halakha pour extraire les données structurées
        logger.info("Analyse de la halakha...")
        processed_data = openai_service.process_halakha(request.content)
        
        # Étape 2: Générer le contenu pour le post et la légende
        logger.info("Génération du contenu pour le post...")
        text_post, legend = openai_service.process_post_legent(
            request.content, 
            processed_data["answer"]
        )
        
        # Combiner toutes les données
        complete_data = {
            **processed_data,
            "text_post": text_post,
            "legend": legend
        }
        
        logger.info("Traitement complet de la halakha terminé avec succès")
        
        return ProcessCompleteHalakhaResponse(
            success=True,
            message="Halakha traitée complètement avec succès",
            **complete_data
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement complet de la halakha : {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors du traitement complet de la halakha : {str(e)}"
        ) 