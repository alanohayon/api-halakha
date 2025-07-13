import logging
import tempfile
from fastapi import APIRouter, Depends, File, HTTPException, BackgroundTasks, UploadFile, status, Form
from typing import List, Dict, Any, Optional
import uuid
from supabase import Client
import os
from datetime import datetime

# Imports core
from app.core.config import Settings, get_settings
from app.core.database import get_supabase

# Imports services
from app.services.processing_service import ProcessingService
from app.services.supabase_service import SupabaseService

# Imports schemas
from app.schemas.halakha import (
    HalakhaInputBrut,
    HalakhaNotionPost,
)

# Imports utilitaires
from app.utils.validators import sanitize_json_text

# Imports schemas additionnels
from app.schemas.halakha import HalakhaNotionPost

# ============================================================================
# DÉPENDANCES OPTIMISÉES POUR LA PRODUCTION
# ============================================================================

def get_supabase_service() -> SupabaseService:
    """Dépendance pour SupabaseService optimisée"""
    return SupabaseService()

def get_processing_service() -> ProcessingService:
    """Dépendance pour ProcessingService optimisée"""
    return ProcessingService()

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/halakhot/post", response_model=HalakhaNotionPost)
async def process_halakha_to_notion(
    content: str = Form(..., min_length=10, max_length=10000, description="Contenu de la halakha à traiter"),
    schedule_days: int = Form(
        default=0, 
        ge=0, 
        le=100, 
        description="Nombre de jours de report pour la programmation (0-100 uniquement)",
        example=7
    ),
    last_img: bool = Form(
        default=False,
        description="Si True, sauvegarde la dernière image dans Supabase puis dans notion"
    ),
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    Traite une halakha avec OpenAI et la publie sur Notion.
    
    Args:
        content: Le texte complet de la halakha à analyser
        schedule_days: Nombre de jours à ajouter pour la date de publication (0-100)
        
    Returns:
        HalakhaNotionPost: Réponse contenant l'URL de la page Notion créée
        
    Raises:
        HTTPException: Si erreur lors du traitement
    """
    logger.info(f"🔄 Requête reçue pour traiter une halakha vers Notion")
    
    # Validation stricte du contenu
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le contenu de la halakha ne peut pas être vide"
        )
    
    if schedule_days < 0 or schedule_days > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="schedule_days doit être entre 0 et 100 inclus"
        )
    
    logger.info(f"✅ Paramètres validés - Contenu: {len(content.strip())} caractères, Jours: {schedule_days}")
    
    try:
        # Nettoyer le contenu textuel
        sanitized_content = sanitize_json_text(content.strip())
        
        # Lancer le processus complet via ProcessingService (avec sauvegarde Supabase)
        notion_url = await processing_service.process_halakha_complete(
            halakha_content=sanitized_content,
            add_day_for_notion=schedule_days,
            last_image=last_img  # Save la derniere image dans supabase puis dans notion
        )
        
        logger.info(f"✅ Halakha traitée avec succès. URL Notion: {notion_url}")
        
        return HalakhaNotionPost(notion_page_url=notion_url)

    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement halakha vers Notion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur interne est survenue: {str(e)}"
        )
        
        
@router.post("/batch/halakhot", status_code=status.HTTP_201_CREATED)
async def process_halakhot_from_json(
    start_index: int = Form(
        default=0, 
        ge=0, 
        description="Index de départ dans le fichier JSON des halakhot (commence à 0)",
        example=0
    ),
    limit_halakhot: int = Form(
        default=10, 
        ge=1, 
        le=50, 
        description="Nombre maximum d'halakhot à traiter (1-50)",
        example=10
    ),
    schedule_days: int = Form(
        default=0, 
        ge=0, 
        le=365, 
        description="Nombre de jours de décalage pour la première halakha (0-365)",
        example=0
    ),
    max_retries: int = Form(
        default=3, 
        ge=0, 
        le=10, 
        description="Nombre maximum de tentatives par halakha (0-10)",
        example=3
    ),
    fail_fast_on_max_retries: bool = Form(
        default=True, 
        description="Si True, arrête le batch en cas d'échec définitif d'une halakha"
    ),
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    🚀 Traite plusieurs halakhot en lot depuis le fichier JSON vers Notion
    
    Args:
        start_index: Index de départ dans le fichier JSON (0-based)
        limit_halakhot: Nombre maximum d'halakhot à traiter (1-50)
        schedule_days: Jours de décalage pour la première halakha (auto-incrémenté)
        max_retries: Nombre maximum de tentatives par halakha
        fail_fast_on_max_retries: Arrêt du batch si échec définitif
        
    Returns:
        Rapport détaillé du traitement en lot avec statistiques
        
    Raises:
        HTTPException: Si erreur de validation ou traitement
    """
    logger.info(f"🚀 Démarrage batch processing - Range: {start_index}-{start_index + limit_halakhot - 1}")
    logger.info(f"📋 Paramètres: schedule_days={schedule_days}, max_retries={max_retries}, fail_fast={fail_fast_on_max_retries}")
    
    # Validation des paramètres
    if limit_halakhot > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="limit_halakhot ne peut pas dépasser 50 pour éviter les timeouts"
        )
    
    if schedule_days > 365:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="schedule_days ne peut pas dépasser 365 jours"
        )
    
    try:
        # Lancer le traitement en lot via ProcessingService
        batch_result = await processing_service.process_halakhot_from_json(
            start_index=start_index,
            schedule_days=schedule_days,
            limit_halakhot=limit_halakhot,
            max_retries=max_retries,
            fail_fast_on_max_retries=fail_fast_on_max_retries
        )
    # Déterminer le statut HTTP selon le résultat
        if batch_result["status"] == "failed_fast":
            # Fail-fast déclenché - retourner 207 Multi-Status
            status_code = status.HTTP_207_MULTI_STATUS
            message = f"Batch arrêté en fail-fast à la halakha #{batch_result.get('fail_fast_triggered_at_index', 'N/A')}"
        elif batch_result["failed_count"] > 0:
            # Succès partiel - retourner 207 Multi-Status  
            status_code = status.HTTP_207_MULTI_STATUS
            message = f"Batch complété avec {batch_result['failed_count']} échec(s) sur {batch_result['processed_count']}"
        else:
            # Succès complet - retourner 200 OK
            status_code = status.HTTP_200_OK
            message = f"Batch complété avec succès - {batch_result['success_count']} halakhot traitées"
        
        logger.info(f"✅ {message}")
        
        # Retourner la réponse enrichie
        return {
            "status": "success" if batch_result["failed_count"] == 0 else "partial_success",
            "message": message,
            "data": batch_result,
            "summary": {
                "total_processed": batch_result["processed_count"],
                "successful": batch_result["success_count"],
                "failed": batch_result["failed_count"],
                "skipped": batch_result.get("skipped_count", 0),
                "success_rate": batch_result["success_rate"],
                "range": f"{batch_result['start_index']}-{batch_result.get('end_index', 'N/A')}",
                "fail_fast_triggered": batch_result["status"] == "failed_fast"
            }
        }
        
    except RuntimeError as e:
        # Erreur fail-fast ou critique
        if "fail-fast" in str(e):
            logger.error(f"🚨 Fail-fast déclenché: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Traitement arrêté en mode fail-fast: {str(e)}"
            )
        else:
            logger.error(f"❌ Erreur critique du batch: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur critique lors du traitement: {str(e)}"
            )
    
    except ValueError as e:
        # Erreur de validation ou paramètres invalides
        logger.error(f"❌ Erreur de validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Paramètres invalides: {str(e)}"
        )
    
    except Exception as e:
        # Erreur inattendue
        logger.error(f"❌ Erreur inattendue lors du batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur inattendue est survenue: {str(e)}"
        )

@router.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(..., description="Fichier image à uploader"),
    clean_filename: Optional[str] = Form(None, description="Nom de fichier personnalisé")
):
    """
    Upload une image vers Supabase Storage et retourne l'URL publique
    
    Args:
        file: Fichier image (.png, .jpg, .jpeg, .webp) à uploader
        clean_filename: Nom de fichier personnalisé (optionnel)
        
    Returns:
        dict: Réponse contenant l'URL de l'image uploadée
        
    Raises:
        HTTPException: Si erreur lors de l'upload ou format de fichier invalide
    """
    logger.info(f"Requête reçue pour upload d'image : {file.filename}")
    
    # Validation basique du fichier
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nom de fichier requis"
        )
    
    # Vérifier le type de fichier
    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    file_extension = os.path.splitext(file.filename.lower())[1]
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Format non supporté. Formats acceptés : {', '.join(allowed_extensions)}"
        )
    
    # Vérifier le content-type
    allowed_content_types = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Type MIME non supporté : {file.content_type}"
        )
    
    # Vérifier la taille du fichier (max 10MB)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fichier trop volumineux (max 10MB)"
        )
    
    logger.info(f"Paramètres validés - Fichier: {file.filename}, Taille: {len(file_content)} bytes")
    
    try:
        # Instancier le service d'orchestration
        processing_service = ProcessingService()
        
        # Lancer l'upload via le service d'orchestration
        result = await processing_service.upload_image_to_storage(
            file_content=file_content,
            filename=file.filename,
            clean_filename=clean_filename
        )
        
        logger.info(f"✅ Image uploadée avec succès : {result['filename']}")
        
        return {
            "status": "success", 
            "message": "Image uploadée avec succès",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'upload d'image : {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur interne est survenue : {str(e)}"
        )

@router.get("/images/latest")
async def get_latest_image():
    """
    Récupère l'URL de la dernière image uploadée dans Supabase Storage
    
    Returns:
        dict: Réponse contenant l'URL de la dernière image
        
    Raises:
        HTTPException: Si aucune image trouvée ou erreur
    """
    logger.info("Requête reçue pour récupérer la dernière image")
    
    try:
        # Instancier le service d'orchestration 
        processing_service = ProcessingService()
        
        # Récupérer la dernière image via Supabase service
        image_url, name = await processing_service.supabase_service.get_last_img_supabase()
        
        if not image_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucune image trouvée dans le storage "
            )

        
        return {
            "status": "success",
            "message": "Dernière image récupérée avec succès",
            "data": {
                "image_url": image_url,
                "name": name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la dernière image : {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur interne est survenue : {str(e)}"
        )



# # Stockage des jobs en mémoire (en production, utiliser Redis/DB)
# job_status_store = {}

# class JobStatus:
#     PENDING = "pending"
#     PROCESSING = "processing"
#     COMPLETED = "completed"
#     FAILED = "failed"

# class JobResponse:
#     def __init__(self, job_id: str, status: str, message: str, result: Any = None, error: str = None):
#         self.job_id = job_id
#         self.status = status
#         self.message = message
#         self.result = result
#         self.error = error
#         self.created_at = datetime.now().isoformat()

# def get_openai_service(settings: Settings = Depends(get_settings)) -> OpenAIService:
#     """Dependency pour obtenir le service OpenAI"""
#     return OpenAIService()

# async def process_halakha_background(job_id: str, halakha_content: str, add_day: int = 0):
#     """Tâche de fond pour traiter une halakha"""
    
#     # Mettre à jour le statut du job
#     job_status_store[job_id] = JobResponse(
#         job_id=job_id,
#         status=JobStatus.PROCESSING,
#         message="Traitement de la halakha en cours..."
#     ).__dict__
    
#     try:
#         logger.info(f"🚀 Démarrage du job {job_id}")
        
#         # Nettoyer le contenu textuel
#         from app.utils.validators import sanitize_json_text
#         halakha_content = sanitize_json_text(halakha_content)
        
#         settings = get_settings()
#         processing_service = ProcessingService()
        
#         # Utiliser le service de traitement pour le processus complet
#         notion_page_url = await processing_service.process_halakha_for_notion(
#             halakha_content=halakha_content,
#             add_day_for_notion=add_day
#         )
        
#         # Succès
#         job_status_store[job_id] = JobResponse(
#             job_id=job_id,
#             status=JobStatus.COMPLETED,
#             message="Halakha traitée et page Notion créée avec succès",
#             result={"notion_page_url": notion_page_url}
#         ).__dict__
        
#         logger.info(f"✅ Job {job_id} terminé avec succès")
        
#     except Exception as e:
#         logger.error(f"❌ Erreur lors du traitement du job {job_id}: {e}")
        
#         # Échec
#         job_status_store[job_id] = JobResponse(
#             job_id=job_id,
#             status=JobStatus.FAILED,
#             message="Erreur lors du traitement de la halakha",
#             error=str(e)
#         ).__dict__

# @router.post("/process/start")
# async def start_halakha_processing(
#     background_tasks: BackgroundTasks,
#     halakha_content: str,
#     add_day: int = 0
# ):
#     """
#     Démarre le traitement d'une halakha en arrière-plan
#     Retourne immédiatement un job_id pour suivre le progrès
#     """
    
#     # Générer un ID unique pour le job
#     job_id = str(uuid.uuid4())
    
#     # Initialiser le statut du job
#     job_status_store[job_id] = JobResponse(
#         job_id=job_id,
#         status=JobStatus.PENDING,
#         message="Job en attente de traitement..."
#     ).__dict__
    
#     # Lancer la tâche en arrière-plan
#     background_tasks.add_task(
#         process_halakha_background,
#         job_id,
#         halakha_content,
#         add_day
#     )
    
#     logger.info(f"🚀 Job {job_id} créé et ajouté à la queue")
    
#     return {
#         "job_id": job_id,
#         "status": "started",
#         "message": "Traitement démarré en arrière-plan",
#         "polling_url": f"/api/v1/process/status/{job_id}"
#     }

# @router.get("/process/status/{job_id}")
# async def get_job_status(job_id: str):
#     """
#     Récupère le statut d'un job de traitement
#     Utilisé pour le polling côté client
#     """
    
#     if job_id not in job_status_store:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Job {job_id} non trouvé"
#         )
    
#     return job_status_store[job_id]

# @router.get("/process/jobs")
# async def list_all_jobs():
#     """
#     Liste tous les jobs (pour debug/monitoring)
#     """
#     return {
#         "jobs": list(job_status_store.values()),
#         "total": len(job_status_store)
#     }

# @router.delete("/process/jobs/{job_id}")
# async def cancel_job(job_id: str):
#     """
#     Annule/supprime un job
#     Note: L'annulation de tâches en cours nécessiterait une logique plus complexe
#     """
    
#     if job_id not in job_status_store:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Job {job_id} non trouvé"
#         )
    
#     # Supprimer du store
#     del job_status_store[job_id]
    
#     return {
#         "message": f"Job {job_id} supprimé",
#         "status": "cancelled"
#     }

# ============== ANCIEN ENDPOINT (DÉPRÉCIÉ) ==============

# @router.post("/halakhot", response_model=HalakhaNotionPost)
# async def process_halakha(
#     content: str = Form(..., min_length=10, max_length=10000, description="Contenu de la halakha à traiter"),
#     schedule_days: int = Form(default=0, ge=0, le=100, description="Nombre de jours de report (0-100)"),
#     processing_service: ProcessingService = Depends(get_processing_service),
#     settings: Settings = Depends(get_settings)
# ):
#     """
#     Traitement complet d'une halakha : analyse OpenAI + sauvegarde Supabase + création page Notion
    
#     Args:
#         content: Le texte complet de la halakha à analyser
#         schedule_days: Nombre de jours à ajouter pour la date de publication (0-100)
        
#     Returns:
#         HalakhaNotionPost: Réponse contenant l'URL de la page Notion créée
        
#     Raises:
#         HTTPException: Si erreur lors du traitement
#     """
#     # Validation stricte du contenu
#     if not content or not content.strip():
#         raise HTTPException(
#             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#             detail="Le contenu de la halakha ne peut pas être vide"
#         )
    
#     if schedule_days < 0 or schedule_days > 100:
#         raise HTTPException(
#             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#             detail="schedule_days doit être entre 0 et 100 inclus"
#         )
    
#     logger.info(f"🚀 Début du traitement - Contenu: {len(content.strip())} chars, Jours: {schedule_days}")
    
#     try:
#         # Nettoyer le contenu textuel
#         sanitized_content = sanitize_json_text(content.strip())
        
#         # Traitement complet via le service d'orchestration
#         notion_url = await processing_service.process_halakha_for_notion(
#             halakha_content=sanitized_content,
#             add_day_for_notion=schedule_days
#         )
        
#         logger.info(f"✅ Traitement terminé avec succès : {notion_url}")
        
#         return HalakhaNotionPost(notion_page_url=notion_url)
        
#     except Exception as e:
#         logger.error(f"❌ Erreur lors du traitement : {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur lors du traitement : {str(e)}"
#         )

# ============================================================================
# ENDPOINT DE SANTÉ POUR MONITORING PRODUCTION
# ============================================================================

@router.get("/health")
async def health_check(
    settings: Settings = Depends(get_settings)
):
    """
    Endpoint de santé pour vérifier la configuration des services
    Essentiel pour le monitoring en production
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        # Vérification OpenAI
        if settings.openai_api_key:
            health_status["services"]["openai"] = "configured"
        else:
            health_status["services"]["openai"] = "not_configured"
        
        # Vérification Notion
        if settings.notion_api_token:
            health_status["services"]["notion"] = "configured"
        else:
            health_status["services"]["notion"] = "not_configured"
        
        # Vérification Supabase
        if settings.supabase_url and settings.supabase_anon_key:
            health_status["services"]["supabase"] = "configured"
        else:
            health_status["services"]["supabase"] = "not_configured"
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Erreur health check : {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


        
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

