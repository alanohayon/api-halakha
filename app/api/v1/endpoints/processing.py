import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

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

# Stockage temporaire des jobs (en production, utiliser Redis/DB)
job_status_store = {}

def get_openai_service(settings: Settings = Depends(get_settings)) -> OpenAIService:
    """Dependency pour obtenir le service OpenAI"""
    return OpenAIService(settings)

@router.post("/halakhot", response_model=HalakhaProcessResponse)
async def process_single_halakha(
    *,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    halakha_input: HalakhaTextInput
):
    """
    Traite une halakha complète : analyse avec OpenAI, sauvegarde dans Supabase 
    et publication sur Notion.
    """
    logger.info(f"Requête reçue pour traiter une nouvelle halakha.")
    try:
        # On instancie le service d'orchestration
        processing_service = ProcessingService(db_session=db, settings=settings)

        # On lance le processus complet
        notion_url = await processing_service.process_and_publish_halakha(
            halakha_content=halakha_input.halakha_content,
            add_day_for_notion=halakha_input.schedule_days
        )
        
        return HalakhaProcessResponse(notion_page_url=notion_url)

    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête /processing/halakhot: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Une erreur interne est survenue: {str(e)}"
        )

@router.post("/halakhot/batch")
async def process_batch_halakhot(
    *,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    halakhot_inputs: List[HalakhaTextInput]
):
    """
    Traite plusieurs halakhot en arrière-plan.
    Retourne immédiatement un ID de job pour suivre le progrès.
    """
    logger.info(f"Requête reçue pour traiter {len(halakhot_inputs)} halakhot en lot.")
    
    if not halakhot_inputs:
        raise HTTPException(
            status_code=400,
            detail="La liste des halakhot ne peut pas être vide"
        )
    
    if len(halakhot_inputs) > 50:  # Limite raisonnable
        raise HTTPException(
            status_code=400,
            detail="Trop de halakhot à traiter en une fois (maximum 50)"
        )
    
    try:
        # Générer un ID unique pour ce job
        job_id = str(uuid.uuid4())
        
        # Initialiser le statut du job
        job_status_store[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "total": len(halakhot_inputs),
            "processed": 0,
            "errors": [],
            "created_at": "2024-01-01T00:00:00Z",  # En production, utiliser datetime.utcnow()
            "started_at": None,
            "completed_at": None
        }
        
        # Ajouter la tâche en arrière-plan
        background_tasks.add_task(
            _process_batch_background,
            job_id=job_id,
            halakhot_inputs=halakhot_inputs,
            db=db,
            settings=settings
        )
        
        return {
            "status": "accepted",
            "message": f"Traitement de {len(halakhot_inputs)} halakhot démarré en arrière-plan",
            "job_id": job_id,
            "total_items": len(halakhot_inputs),
            "status_url": f"/api/v1/processing/jobs/{job_id}"
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du traitement batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Impossible de démarrer le traitement en lot: {str(e)}"
        )

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Récupère le statut d'un job de traitement asynchrone.
    
    Statuts possibles :
    - pending: Job créé mais pas encore démarré
    - running: Job en cours d'exécution
    - completed: Job terminé avec succès
    - failed: Job échoué
    - partial: Job terminé avec quelques erreurs
    """
    if job_id not in job_status_store:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    job_status = job_status_store[job_id]
    
    # Calculer le pourcentage de progression
    if job_status["total"] > 0:
        progress_percentage = (job_status["processed"] / job_status["total"]) * 100
    else:
        progress_percentage = 0
    
    return {
        **job_status,
        "progress_percentage": round(progress_percentage, 2)
    }

@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Annule un job en cours (si possible).
    Note: L'annulation n'est pas toujours possible selon l'état du job.
    """
    if job_id not in job_status_store:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    job_status = job_status_store[job_id]
    
    if job_status["status"] in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job_status['status']}"
        )
    
    # Marquer comme annulé
    job_status_store[job_id]["status"] = "cancelled"
    job_status_store[job_id]["completed_at"] = "2024-01-01T00:00:00Z"  # En production, utiliser datetime.utcnow()
    
    return {
        "message": "Job cancelled successfully",
        "job_id": job_id
    }

async def _process_batch_background(
    job_id: str,
    halakhot_inputs: List[HalakhaTextInput],
    db: AsyncSession,
    settings: Settings
):
    """
    Fonction privée pour traiter les halakhot en arrière-plan.
    """
    logger.info(f"Démarrage du traitement batch {job_id}")
    
    # Mettre à jour le statut
    job_status_store[job_id]["status"] = "running"
    job_status_store[job_id]["started_at"] = "2024-01-01T00:00:00Z"  # En production, utiliser datetime.utcnow()
    
    processing_service = ProcessingService(db_session=db, settings=settings)
    
    processed = 0
    errors = []
    
    for i, halakha_input in enumerate(halakhot_inputs):
        # Vérifier si le job a été annulé
        if job_status_store[job_id]["status"] == "cancelled":
            logger.info(f"Job {job_id} cancelled, stopping processing")
            break
            
        try:
            logger.info(f"Traitement de la halakha {i+1}/{len(halakhot_inputs)} (job {job_id})")
            
            await processing_service.process_and_publish_halakha(
                halakha_content=halakha_input.halakha_content,
                add_day_for_notion=halakha_input.schedule_days + i  # Étaler les dates de publication
            )
            
            processed += 1
            logger.info(f"Halakha {i+1} traitée avec succès")
            
            # Mettre à jour le progrès
            job_status_store[job_id]["processed"] = processed
            
        except Exception as e:
            error_msg = f"Erreur lors du traitement de la halakha {i+1}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append({
                "halakha_index": i + 1,
                "error": error_msg
            })
            job_status_store[job_id]["errors"] = errors
    
    # Finaliser le statut du job
    if job_status_store[job_id]["status"] != "cancelled":
        if len(errors) == 0:
            job_status_store[job_id]["status"] = "completed"
        elif processed > 0:
            job_status_store[job_id]["status"] = "partial"  # Succès partiel
        else:
            job_status_store[job_id]["status"] = "failed"
    
    job_status_store[job_id]["completed_at"] = "2024-01-01T00:00:00Z"  # En production, utiliser datetime.utcnow()
    
    logger.info(f"Traitement job {job_id} terminé: {processed}/{len(halakhot_inputs)} réussies, {len(errors)} erreurs")

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