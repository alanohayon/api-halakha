import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from typing import List, Dict, Any, Optional
import uuid
from supabase import Client
import os
from datetime import datetime
from app.core.config import Settings, get_settings
from app.core.database import get_db, get_supabase
from app.services.processing_service import ProcessingService
from app.services.openai_service import OpenAIService
from app.services.notion_service import NotionService
from app.services.supabase_service import SupabaseService
from app.schemas.halakha import (
    HalakhaInputBrut,
    HalakhaNotionPost,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Stockage des jobs en mémoire (en production, utiliser Redis/DB)
job_status_store = {}

class JobStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobResponse:
    def __init__(self, job_id: str, status: str, message: str, result: Any = None, error: str = None):
        self.job_id = job_id
        self.status = status
        self.message = message
        self.result = result
        self.error = error
        self.created_at = datetime.now().isoformat()

def get_openai_service(settings: Settings = Depends(get_settings)) -> OpenAIService:
    """Dependency pour obtenir le service OpenAI"""
    return OpenAIService()

async def process_halakha_background(job_id: str, halakha_content: str, add_day: int = 0):
    """Tâche de fond pour traiter une halakha"""
    
    # Mettre à jour le statut du job
    job_status_store[job_id] = JobResponse(
        job_id=job_id,
        status=JobStatus.PROCESSING,
        message="Traitement de la halakha en cours..."
    ).__dict__
    
    try:
        logger.info(f"🚀 Démarrage du job {job_id}")
        
        # Nettoyer le contenu textuel
        from app.utils.validators import sanitize_json_text
        halakha_content = sanitize_json_text(halakha_content)
        
        settings = get_settings()
        processing_service = ProcessingService()
        
        # Utiliser le service de traitement pour le processus complet
        notion_page_url = await processing_service.process_halakha_for_notion(
            halakha_content=halakha_content,
            add_day_for_notion=add_day
        )
        
        # Succès
        job_status_store[job_id] = JobResponse(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            message="Halakha traitée et page Notion créée avec succès",
            result={"notion_page_url": notion_page_url}
        ).__dict__
        
        logger.info(f"✅ Job {job_id} terminé avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement du job {job_id}: {e}")
        
        # Échec
        job_status_store[job_id] = JobResponse(
            job_id=job_id,
            status=JobStatus.FAILED,
            message="Erreur lors du traitement de la halakha",
            error=str(e)
        ).__dict__

@router.post("/process/start")
async def start_halakha_processing(
    background_tasks: BackgroundTasks,
    halakha_content: str,
    add_day: int = 0
):
    """
    Démarre le traitement d'une halakha en arrière-plan
    Retourne immédiatement un job_id pour suivre le progrès
    """
    
    # Générer un ID unique pour le job
    job_id = str(uuid.uuid4())
    
    # Initialiser le statut du job
    job_status_store[job_id] = JobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Job en attente de traitement..."
    ).__dict__
    
    # Lancer la tâche en arrière-plan
    background_tasks.add_task(
        process_halakha_background,
        job_id,
        halakha_content,
        add_day
    )
    
    logger.info(f"🚀 Job {job_id} créé et ajouté à la queue")
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": "Traitement démarré en arrière-plan",
        "polling_url": f"/api/v1/process/status/{job_id}"
    }

@router.get("/process/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Récupère le statut d'un job de traitement
    Utilisé pour le polling côté client
    """
    
    if job_id not in job_status_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} non trouvé"
        )
    
    return job_status_store[job_id]

@router.get("/process/jobs")
async def list_all_jobs():
    """
    Liste tous les jobs (pour debug/monitoring)
    """
    return {
        "jobs": list(job_status_store.values()),
        "total": len(job_status_store)
    }

@router.delete("/process/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Annule/supprime un job
    Note: L'annulation de tâches en cours nécessiterait une logique plus complexe
    """
    
    if job_id not in job_status_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} non trouvé"
        )
    
    # Supprimer du store
    del job_status_store[job_id]
    
    return {
        "message": f"Job {job_id} supprimé",
        "status": "cancelled"
    }

# ============== ANCIEN ENDPOINT (DÉPRÉCIÉ) ==============

@router.post("/process/post")
async def process_halakha_post(
    halakha_content: str,
    add_day: int = 0,
    settings: Settings = Depends(get_settings)
):
    """
    ⚠️ DÉPRÉCIÉ : Traitement synchrone qui peut prendre très longtemps
    Utilisez /process/start à la place pour les traitements longs
    """
    
    logger.warning("⚠️ Endpoint déprécié utilisé - recommandation: utiliser /process/start")
    
    # Pour les traitements rapides seulement
    try:
        # Nettoyer le contenu textuel
        from app.utils.validators import sanitize_json_text
        halakha_content = sanitize_json_text(halakha_content)
        
        processing_service = ProcessingService()
        
        # Utiliser le service de traitement pour le processus complet
        notion_page_url = await processing_service.process_halakha_for_notion(
            halakha_content=halakha_content,
            add_day_for_notion=add_day
        )
        
        return {
            "status": "success",
            "message": "Halakha traitée et page Notion créée avec succès",
            "notion_page_url": notion_page_url,
            "warning": "Cet endpoint est déprécié pour les traitements longs. Utilisez /process/start"
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la halakha : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement de la halakha : {str(e)}"
        )


        
# @router.post("/halakha/analyze", response_model=ProcessHalakhaResponse, tags=["AI Processing"])
# async def analyze_halakha(
#     request: ProcessHalakhaRequest,
#     openai_service: OpenAIService = Depends(get_openai_service)
# ):
#     """
#     Analyser une halakha et extraire les données structurées (question, réponse, sources, etc.)
    
#     Cette route utilise OpenAI pour traiter le contenu d'une halakha et en extraire
#     les informations structurées comme la question, la réponse, les sources et les thèmes.
#     """
#     try:
#         logger.info("Début de l'analyse de la halakha...")
        
#         # Nettoyer le contenu textuel
#         sanitized_data = validate_and_sanitize_request(request, ['content'])
#         request.content = sanitized_data['content']
        
#         # Traitement avec OpenAI pour extraire les données structurées
#         processed_data = openai_service.queries_halakha(request.content)
        
#         logger.info("Analyse de la halakha terminée avec succès")
        
#         return ProcessHalakhaResponse(
#             success=True,
#             message="Halakha analysée avec succès",
#             **processed_data
#         )
        
#     except Exception as e:
#         logger.error(f"Erreur lors de l'analyse de la halakha : {e}")
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Erreur lors de l'analyse de la halakha : {str(e)}"
#         )

# @router.post("/halakha/complete", response_model=ProcessCompleteHalakhaResponse, tags=["AI Processing"])
# async def process_complete_halakha(
#     request: ProcessHalakhaRequest,
#     openai_service: OpenAIService = Depends(get_openai_service)
# ):
#     """
#     Traitement complet d'une halakha : analyse + génération de contenu pour post
    
#     Cette route effectue un traitement complet d'une halakha :
#     1. Analyse et extraction des données structurées (question, réponse, sources, etc.)
#     2. Génération du texte pour le post Instagram
#     3. Génération de la légende pour le post
    
#     Tout est traité et retourné dans une seule réponse JSON.
#     """
#     try:
#         logger.info("Début du traitement complet de la halakha...")
        
#         # Nettoyer le contenu textuel
#         sanitized_data = validate_and_sanitize_request(request, ['content'])
#         request.content = sanitized_data['content']
        
#         # Étape 1: Analyser la halakha pour extraire les données structurées
#         logger.info("Analyse de la halakha...")
#         processed_data = openai_service.queries_halakha(request.content)
        
#         # Étape 2: Générer le contenu pour le post et la légende
#         logger.info("Génération du contenu pour le post...")
#         text_post, legend = openai_service.queries_post_legende(
#             request.content, 
#             processed_data["answer"]
#         )
        
#         # Combiner toutes les données
#         complete_data = {
#             **processed_data,
#             "text_post": text_post,
#             "legend": legend
#         }
        
#         logger.info("Traitement complet de la halakha terminé avec succès")
        
#         return ProcessCompleteHalakhaResponse(
#             success=True,
#             message="Halakha traitée complètement avec succès",
#             **complete_data
#         )
        
#     except Exception as e:
#         logger.error(f"Erreur lors du traitement complet de la halakha : {e}")
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Erreur lors du traitement complet de la halakha : {str(e)}"
#         ) 

# @router.post("/halakhot/batch")
# async def process_batch_halakhot(
#     *,
#     background_tasks: BackgroundTasks,
#     supabase: Client = Depends(get_supabase),
#     settings: Settings = Depends(get_settings),
#     halakhot_inputs: List[HalakhaTextInput]
# ):
#     """
#     Traite plusieurs halakhot en arrière-plan.
#     Retourne immédiatement un ID de job pour suivre le progrès.
#     """
#     logger.info(f"Requête reçue pour traiter {len(halakhot_inputs)} halakhot en lot.")
    
#     if not halakhot_inputs:
#         raise HTTPException(
#             status_code=400,
#             detail="La liste des halakhot ne peut pas être vide"
#         )
    
#     if len(halakhot_inputs) > 50:  # Limite raisonnable
#         raise HTTPException(
#             status_code=400,
#             detail="Trop de halakhot à traiter en une fois (maximum 50)"
#         )
    
#     try:
#         # Nettoyer tous les champs textuels dans la liste
#         for i, halakha_input in enumerate(halakhot_inputs):
#             sanitized_data = validate_and_sanitize_request(halakha_input, ['content'])
#             halakhot_inputs[i].content = sanitized_data['content']
        
#         # Générer un ID unique pour ce job
#         job_id = str(uuid.uuid4())
        
#         # Initialiser le statut du job
#         job_status_store[job_id] = {
#             "job_id": job_id,
#             "status": "pending",
#             "total": len(halakhot_inputs),
#             "processed": 0,
#             "errors": [],
#             "created_at": "2024-01-01T00:00:00Z",  # En production, utiliser datetime.utcnow()
#             "started_at": None,
#             "completed_at": None
#         }
        
#         # Ajouter la tâche en arrière-plan
#         background_tasks.add_task(
#             _process_batch_background,
#             job_id=job_id,
#             halakhot_inputs=halakhot_inputs,
#             supabase=supabase,
#             settings=settings
#         )
        
#         return {
#             "status": "accepted",
#             "message": f"Traitement de {len(halakhot_inputs)} halakhot démarré en arrière-plan",
#             "job_id": job_id,
#             "total_items": len(halakhot_inputs),
#             "status_url": f"/api/v1/processing/jobs/{job_id}"
#         }
        
#     except Exception as e:
#         logger.error(f"Erreur lors de l'initialisation du traitement batch: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail=f"Impossible de démarrer le traitement en lot: {str(e)}"
#         )


# @router.get("/jobs/{job_id}")
# async def get_job_status(job_id: str):
#     """
#     Récupère le statut d'un job de traitement asynchrone.
    
#     Statuts possibles :
#     - pending: Job créé mais pas encore démarré
#     - running: Job en cours d'exécution
#     - completed: Job terminé avec succès
#     - failed: Job échoué
#     - partial: Job terminé avec quelques erreurs
#     """
#     if job_id not in job_status_store:
#         raise HTTPException(
#             status_code=404,
#             detail="Job not found"
#         )
    
#     job_status = job_status_store[job_id]
    
#     # Calculer le pourcentage de progression
#     if job_status["total"] > 0:
#         progress_percentage = (job_status["processed"] / job_status["total"]) * 100
#     else:
#         progress_percentage = 0
    
#     return {
#         **job_status,
#         "progress_percentage": round(progress_percentage, 2)
#     }

# @router.delete("/jobs/{job_id}")
# async def cancel_job(job_id: str):
#     """
#     Annule un job en cours (si possible).
#     Note: L'annulation n'est pas toujours possible selon l'état du job.
#     """
#     if job_id not in job_status_store:
#         raise HTTPException(
#             status_code=404,
#             detail="Job not found"
#         )
    
#     job_status = job_status_store[job_id]
    
#     if job_status["status"] in ["completed", "failed"]:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Cannot cancel job with status: {job_status['status']}"
#         )
    
#     # Marquer comme annulé
#     job_status_store[job_id]["status"] = "cancelled"
#     job_status_store[job_id]["completed_at"] = "2024-01-01T00:00:00Z"  # En production, utiliser datetime.utcnow()
    
#     return {
#         "message": "Job cancelled successfully",
#         "job_id": job_id
#     }

# async def _process_batch_background(
#     job_id: str,
#     halakhot_inputs: List[HalakhaTextInput],
#     supabase: Client,
#     settings: Settings
# ):
#     """
#     Fonction privée pour traiter les halakhot en arrière-plan.
#     """
#     logger.info(f"Démarrage du traitement batch {job_id}")
    
#     # Mettre à jour le statut
#     job_status_store[job_id]["status"] = "running"
#     job_status_store[job_id]["started_at"] = "2024-01-01T00:00:00Z"  # En production, utiliser datetime.utcnow()
    
#     processing_service = ProcessingService(supabase_client=supabase, settings=settings)
    
#     processed = 0
#     errors = []
    
#     for i, halakha_input in enumerate(halakhot_inputs):
#         # Vérifier si le job a été annulé
#         if job_status_store[job_id]["status"] == "cancelled":
#             logger.info(f"Job {job_id} cancelled, stopping processing")
#             break
            
#         try:
#             logger.info(f"Traitement de la halakha {i+1}/{len(halakhot_inputs)} (job {job_id})")
            
#             await processing_service.process_and_publish_halakha(
#                 halakha_content=halakha_input.content,
#                 add_day_for_notion=halakha_input.schedule_days + i  # Étaler les dates de publication
#             )
            
#             processed += 1
#             logger.info(f"Halakha {i+1} traitée avec succès")
            
#             # Mettre à jour le progrès
#             job_status_store[job_id]["processed"] = processed
            
#         except Exception as e:
#             error_msg = f"Erreur lors du traitement de la halakha {i+1}: {str(e)}"
#             logger.error(error_msg, exc_info=True)
#             errors.append({
#                 "halakha_index": i + 1,
#                 "error": error_msg
#             })
#             job_status_store[job_id]["errors"] = errors
    
#     # Finaliser le statut du job
#     if job_status_store[job_id]["status"] != "cancelled":
#         if len(errors) == 0:
#             job_status_store[job_id]["status"] = "completed"
#         elif processed > 0:
#             job_status_store[job_id]["status"] = "partial"  # Succès partiel
#         else:
#             job_status_store[job_id]["status"] = "failed"
    
#     job_status_store[job_id]["completed_at"] = "2024-01-01T00:00:00Z"  # En production, utiliser datetime.utcnow()
    
#     logger.info(f"Traitement job {job_id} terminé: {processed}/{len(halakhot_inputs)} réussies, {len(errors)} erreurs")

# @router.post("/upload-latest-image")
# async def upload_latest_image(
#     supabase_client=Depends(get_supabase)
# ) -> Dict[str, Any]:
#     """
#     Upload la dernière image du dossier Downloads vers Supabase Storage
#     et retourne l'URL publique
#     """
#     try:
#         logger.info("🖼️ Recherche de la dernière image dans Downloads...")
        
#         # Récupérer la dernière image avec nom nettoyé
#         latest_image_path, clean_filename = get_latest_image_with_clean_name()
        
#         if not latest_image_path or not clean_filename:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Aucune image trouvée dans le dossier Downloads"
#             )
        
#         logger.info(f"📁 Image trouvée: {latest_image_path}")
        
#         # Upload vers Supabase
#         supabase_service = SupabaseService(supabase_client)
#         image_url = await supabase_service.upload_img_to_supabase(latest_image_path, clean_filename)
        
#         if not image_url:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Échec de l'upload de l'image"
#             )
        
#         logger.info(f"✅ Image uploadée avec succès: {image_url}")
        
#         return {
#             "success": True,
#             "message": "Image uploadée avec succès",
#             "data": {
#                 "image_url": image_url,
#                 "file_name": clean_filename,
#                 "original_file_name": latest_image_path.split("/")[-1],
#                 "bucket": "notion-images"
#             }
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ Erreur lors de l'upload de l'image: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur interne: {str(e)}"
#         )

# @router.get("/latest-image-info")
# async def get_latest_image_info() -> Dict[str, Any]:
#     """
#     Récupère les informations sur la dernière image dans Downloads
#     sans l'uploader
#     """
#     try:
#         latest_image_path, clean_filename = get_latest_image_with_clean_name()
        
#         if not latest_image_path or not clean_filename:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Aucune image trouvée dans le dossier Downloads"
#             )
        
#         file_stats = os.stat(latest_image_path)
#         file_size = file_stats.st_size
#         modified_time = datetime.fromtimestamp(file_stats.st_mtime)
        
#         return {
#             "success": True,
#             "data": {
#                 "file_path": latest_image_path,
#                 "original_file_name": os.path.basename(latest_image_path),
#                 "clean_file_name": clean_filename,
#                 "file_size_bytes": file_size,
#                 "file_size_mb": round(file_size / (1024 * 1024), 2),
#                 "modified_time": modified_time.isoformat(),
#                 "ready_for_upload": True
#             }
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ Erreur lors de la récupération des infos de l'image: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur interne: {str(e)}"
#         )

