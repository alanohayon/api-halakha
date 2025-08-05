import asyncio
from typing import Dict, Any, List
import structlog
from app.core.config import Settings
from app.services.openai_service import OpenAIService
from app.services.notion_service import NotionService
from app.services.supabase_service import SupabaseService
from ..utils.json_loader import get_halakhot_count, get_halakhot_range, load_halakha_by_index
from app.core.config import get_settings
from app.utils.performance import measure_execution_time, measure_with_metadata
from typing import Optional
from ..schemas.notion import NotionStatus

logger = structlog.get_logger()

class ProcessingService:
    def __init__(self, 
                 supabase_service: Optional[SupabaseService] = None,
                 openai_service: Optional[OpenAIService] = None,
                 notion_service: Optional[NotionService] = None):
        settings = get_settings()
        self.settings = settings
        self.supabase_service = supabase_service or SupabaseService()
        self.openai_service = openai_service or OpenAIService()
        self.notion_service = notion_service or NotionService()

    # ===========================================
    # 🚀 MÉTHODES PRINCIPALES (API PUBLIQUE)
    # ===========================================

    @measure_execution_time("process_halakha_complete")
    async def process_halakha_complete(
        self, 
        halakha_content: str, 
        add_day_for_notion: int = 0, 
        last_image: bool = False
    ) -> str:
        """
        🎯 MÉTHODE UNIFIÉE : Traite une halakha complètement (OpenAI + Notion + optionnellement Supabase)
        
        Args:
            halakha_content: Contenu de la halakha à traiter
            add_day_for_notion: Jours de décalage pour la publication Notion
            last_image: Si True, sauvegarde la dernière image dans Supabase puis dans notion
            
        Returns:
            URL de la page Notion créée
        """
        logger.info("🚀 Démarrage du traitement complet de la halakha")
        
        try:
            # 1. Traitement IA (OpenAI)
            complete_data = await self._process_with_ai(halakha_content)
            
            # 2. Sauvegarde optionnelle Supabase
            image_url = None
            if last_image:
                result = await self.supabase_service.get_last_img_supabase()
                logger.info(f"🔍 Résultat de la récupération de l'image: {result}")
                if result and isinstance(result, tuple):
                    image_url = result[0]  # Récupérer uniquement l'URL, pas le nom
                else:
                    image_url = result
            
            # 3. Publication Notion
            notion_url = await self._publish_to_notion_platform(complete_data, add_day_for_notion, image_url)
            
            logger.info("🎉 Traitement complet terminé avec succès !")
            return notion_url
            
        except Exception as e:
            logger.error(f"❌ Échec du traitement complet : {e}", exc_info=True)
            raise

    @measure_with_metadata(service="processing", operation_type="json_processing", source="json_file")
    async def process_halakha_from_json(self, json_index: int, schedule_days: int = 0) -> Dict[str, Any]:
        """
        Traite une halakha unique depuis le fichier JSON
        
        Args:
            json_index: Index de la halakha dans le fichier JSON
            schedule_days: Nombre de jours à ajouter pour programmer la publication
            
        Returns:
            Dictionnaire avec l'URL Notion et le statut
        """
        try:
            logger.info(f"🎯 Traitement de la halakha unique #{json_index} (programmée dans {schedule_days} jours)")
            
            # Charger la halakha depuis le JSON
            halakha_content = await load_halakha_by_index(json_index)
            
            # Traiter avec la méthode unifiée (sans Supabase pour le JSON)
            notion_url = await self.process_halakha_complete(
                halakha_content=halakha_content, 
                add_day_for_notion=schedule_days,
                save_to_supabase=False  # 🎯 Pas de sauvegarde DB pour JSON
            )
            
            result = {
                "index": json_index,
                "notion_page_url": notion_url,
                "scheduled_days": schedule_days,
                "status": "completed",
                "content_length": len(halakha_content)
            }
            
            logger.info(f"✅ Halakha #{json_index} traitée avec succès")
            return result
            
        except Exception as e:
            error_msg = f"Échec du traitement de la halakha #{json_index}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    @measure_with_metadata(service="processing", operation_type="batch_processing", source="json_file") 
    async def process_halakhot_from_json(
        self, 
        start_index: int = 0, 
        schedule_days: int = 0, 
        limit_halakhot: int = 10, 
        max_retries: int = 3, 
        fail_fast_on_max_retries: bool = True
    ) -> Dict[str, Any]:
        """
        Orchestre le traitement en lot d'halakhot depuis le fichier JSON
        
        Args:
            start_index: Index de départ dans le fichier JSON
            schedule_days: Nombre de jours de décalage pour la première halakha
            limit_halakhot: Nombre maximum d'halakhot à traiter
            max_retries: Nombre maximum de tentatives par halakha
            fail_fast_on_max_retries: Si True, arrête le batch en cas d'échec définitif
            
        Returns:
            Dictionnaire détaillé avec les résultats du traitement en lot
        """
        logger.info(f"🚀 Démarrage du traitement en lot - Index: {start_index}, Limite: {limit_halakhot}")
        
        try:
            # Charger la plage d'halakhot à traiter
            halakhot_to_process = await get_halakhot_range(start_index, limit_halakhot)
            actual_count = len(halakhot_to_process)
            
            logger.info(f"📋 {actual_count} halakhot à traiter")
            if max_retries > 0:
                logger.info(f"🔄 Mode retry activé: {max_retries} tentatives max")
            if fail_fast_on_max_retries:
                logger.info(f"🚨 Mode fail-fast activé")
            
            # Initialiser les résultats
            results = self._init_batch_results(start_index, limit_halakhot, actual_count, schedule_days, max_retries)
            
            # Traiter chaque halakha avec retry et fail-fast
            for i, halakha_data in enumerate(halakhot_to_process):
                current_index = halakha_data["index"]
                current_schedule_days = schedule_days + i
                
                logger.info(f"📖 Traitement halakha #{current_index} ({i+1}/{actual_count})")
                
                # Traitement avec retry
                processing_result = await self._process_single_halakha_with_retry(
                    halakha_data, current_index, current_schedule_days, max_retries
                )
                
                # Mettre à jour les résultats
                self._update_batch_results(results, processing_result)
                
                # 🚨 FAIL-FAST : Arrêt en cas d'échec après tous les retries
                if (processing_result["status"] == "failed" and 
                    processing_result.get("retries_exhausted", False) and 
                    fail_fast_on_max_retries):
                    
                    logger.error(f"🚨 FAIL-FAST déclenché à la halakha #{current_index}")
                    
                    # Marquer les halakhot restantes comme sautées
                    remaining_halakhot = halakhot_to_process[i+1:]
                    self._add_skipped_halakhot_to_results(results, remaining_halakhot, "skipped_due_to_fail_fast")
                    
                    results["status"] = "failed_fast"
                    results["fail_fast_triggered_at_index"] = current_index
                    
                    error_msg = f"Batch arrêté en fail-fast à la halakha #{current_index}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                # Pause entre les traitements
                if i < len(halakhot_to_process) - 1:
                    await asyncio.sleep(2)
            
            return self._finalize_batch_results(results)
            
        except Exception as e:
            if isinstance(e, RuntimeError) and "fail-fast" in str(e):
                raise  # Ne pas wrapper les erreurs fail-fast
            
            error_msg = f"❌ Échec critique du traitement en lot: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    @measure_execution_time("upload_image_to_storage")
    async def upload_image_to_storage(self, file_content: bytes, filename: str, clean_filename: str = None) -> Dict[str, Any]:
        """
        Orchestre l'upload d'une image vers Supabase Storage
        
        🚨 NOTE: Cette méthode devrait être dans un ImageService séparé
        """
        logger.info(f"🖼️ Upload d'image : {filename}")
        
        try:
            import tempfile
            import uuid
            import os
            
            # Générer un nom unique si non fourni
            if not clean_filename:
                file_extension = os.path.splitext(filename)[1]
                clean_filename = f"{uuid.uuid4()}{file_extension}"
            elif not clean_filename.endswith(os.path.splitext(filename)[1]):
                clean_filename = f"{clean_filename}{os.path.splitext(filename)[1]}"
            
            # Créer un fichier temporaire
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload vers Supabase
                image_url = await self.supabase_service.upload_img_to_supabase(
                    image_path=temp_file_path,
                    clean_filename=clean_filename
                )
                
                if not image_url:
                    raise RuntimeError("Échec de l'upload vers Supabase Storage")
                
                logger.info(f"✅ Image uploadée avec succès : {clean_filename}")
                
                return {
                    "image_url": image_url,
                    "filename": clean_filename,
                    "original_filename": filename,
                    "file_size": len(file_content)
                }
                
            finally:
                # Nettoyer le fichier temporaire
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'upload d'image : {e}", exc_info=True)
            raise

    # ===========================================
    # 🔧 MÉTHODES PRIVÉES (LOGIQUE INTERNE)
    # ===========================================

    async def _process_with_ai(self, halakha_content: str) -> Dict[str, Any]:
        """
        Traite le contenu avec OpenAI (analyse + génération post/légende)
        
        Returns:
            Dictionnaire avec toutes les données traitées
        """
        logger.info("🤖 Traitement du contenu par OpenAI...")
        
        # 1. Analyse de la halakha
        processed_data = await self.openai_service.queries_halakha(halakha_content)
        
        # 2. Génération du contenu pour les réseaux sociaux
        post_result = await self.openai_service.queries_post_legende(
            halakha_content, 
            processed_data["answer"]
        )
        
        # 3. Combiner toutes les données
        complete_data = {
            **processed_data,
            "text_post": post_result["post_text"],
            "legend": post_result["legende_text"],
            "content": halakha_content
        }
        
        logger.info("✅ Traitement IA terminé")
        return complete_data

    async def _save_to_database(self, complete_data: Dict[str, Any]) -> None:
        """Sauvegarde les données dans Supabase"""
        logger.info("💾 Sauvegarde dans Supabase...")
        await self.supabase_service.create_halakha(complete_data)
        logger.info("✅ Sauvegarde terminée")

    async def _publish_to_notion_platform(self, complete_data: Dict[str, Any], add_day: int, image_url: str) -> str:
        """
        Publie sur Notion et retourne l'URL de la page
        
        Returns:
            URL de la page Notion créée
        """
        logger.info("📝 Publication sur Notion...")
        notion_page = await self.notion_service.create_halakha_page(complete_data, add_day=add_day, image_url=image_url)
        logger.info("✅ Publication Notion terminée")
        return notion_page.get("url", "URL non disponible")

    async def _process_single_halakha_with_retry(
        self, 
        halakha_data: Dict[str, Any], 
        index: int, 
        schedule_days: int, 
        max_retries: int
    ) -> Dict[str, Any]:
        """Traite une halakha avec système de retry et délai exponentiel"""
        
        halakha_content = halakha_data["halakha"]
        retry_delays = [1, 2, 4, 8, 16]
        last_exception = None
        retry_details = []
        
        for attempt in range(max_retries + 1):
            try:
                if attempt == 0:
                    logger.info(f"🎯 Tentative initiale pour halakha #{index}")
                else:
                    logger.warning(f"🔄 Retry {attempt}/{max_retries} pour halakha #{index}")
                
                # Validation du contenu
                if not halakha_content.strip():
                    raise ValueError(f"Contenu vide pour la halakha #{index}")
                
                # Traitement avec la méthode unifiée
                notion_url = await self.process_halakha_complete(
                    halakha_content=halakha_content,
                    add_day_for_notion=schedule_days,
                    last_image=False  # On ne sauvegarde pas l'image dans Supabase pour les JSON
                )
                # 🎉 Succès !
                success_msg = f"✅ Halakha #{index} traitée avec succès"
                if attempt > 0:
                    success_msg += f" après {attempt} retry(s)"
                logger.info(success_msg)
                
                return {
                    "status": "success",
                    "index": index,
                    "notion_url": notion_url,
                    "scheduled_days": schedule_days,
                    "content_length": halakha_data.get("character_count", len(halakha_content)),
                    "attempts_made": attempt + 1,
                    "retry_details": retry_details
                }
                
            except Exception as e:
                last_exception = e
                
                retry_details.append({
                    "attempt": attempt + 1,
                    "error": str(e),
                    "exception_type": type(e).__name__
                })
                
                if attempt >= max_retries:
                    logger.error(f"❌ Halakha #{index} échouée après {attempt + 1} tentatives")
                    break
                
                # Délai exponentiel avant retry
                delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                logger.warning(f"⏳ Attente de {delay}s avant retry pour halakha #{index}")
                await asyncio.sleep(delay)
        
        # 🚨 Échec après tous les retries
        return {
            "status": "failed",
            "index": index,
            "error": f"Échec après {max_retries + 1} tentatives: {str(last_exception)}",
            "exception_type": type(last_exception).__name__ if last_exception else "Unknown",
            "scheduled_days": schedule_days,
            "attempts_made": max_retries + 1,
            "retry_details": retry_details,
            "retries_exhausted": True
        }

    def _init_batch_results(
        self, 
        start_index: int, 
        requested_limit: int, 
        actual_count: int, 
        schedule_days: int,
        max_retries: int
    ) -> Dict[str, Any]:
        """Initialise la structure des résultats du batch"""
        return {
            "processed_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "notion_urls": [],
            "errors": [],
            "skipped_items": [],
            "processing_details": [],
            "start_index": start_index,
            "requested_limit": requested_limit,
            "actual_count": actual_count,
            "schedule_days_start": schedule_days,
            "max_retries": max_retries,
            "status": "in_progress"
        }

    def _update_batch_results(self, results: Dict[str, Any], processing_result: Dict[str, Any]) -> None:
        """Met à jour les résultats globaux avec le résultat d'une halakha"""
        results["processed_count"] += 1
        
        if processing_result["status"] == "success":
            results["success_count"] += 1
            results["notion_urls"].append({
                "index": processing_result["index"],
                "url": processing_result["notion_url"],
                "scheduled_days": processing_result["scheduled_days"]
            })
        else:
            results["failed_count"] += 1
            results["errors"].append({
                "index": processing_result["index"],
                "error": processing_result["error"],
                "exception_type": processing_result.get("exception_type", "Unknown")
            })
        
        results["processing_details"].append(processing_result)

    def _add_skipped_halakhot_to_results(
        self, 
        results: Dict[str, Any], 
        skipped_halakhot: List[Dict[str, Any]], 
        reason: str
    ) -> None:
        """Ajoute les halakhot sautées aux résultats en cas de fail-fast"""
        for halakha_data in skipped_halakhot:
            skipped_item = {
                "index": halakha_data["index"],
                "reason": reason,
                "content_length": halakha_data.get("character_count", 0)
            }
            
            results["skipped_items"].append(skipped_item)
            results["skipped_count"] += 1
            
            results["processing_details"].append({
                "status": "skipped",
                "index": halakha_data["index"],
                "reason": reason
            })

    def _finalize_batch_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Finalise les résultats du traitement en lot"""
        # Calculer le taux de succès
        treated_count = results["processed_count"] - results["skipped_count"]
        success_rate = (results["success_count"] / treated_count * 100) if treated_count > 0 else 0
        
        # Calculer les statistiques de retry
        retry_stats = self._calculate_retry_stats(results["processing_details"])
        
        # Finaliser les résultats
        results.update({
            "success_rate": round(success_rate, 1),
            "end_index": results["start_index"] + results["actual_count"] - 1,
            "retry_statistics": retry_stats,
            "status": "completed" if results["status"] != "failed_fast" else results["status"]
        })
        
        # Logs finaux
        logger.info(f"🎉 Traitement en lot terminé !")
        logger.info(f"📊 Résumé: {results['success_count']} succès, {results['failed_count']} échecs, {results['skipped_count']} sautées")
        logger.info(f"📈 Taux de succès: {success_rate:.1f}%")
        
        if retry_stats["total_retries_used"] > 0:
            logger.info(f"🔄 Retries utilisés: {retry_stats['total_retries_used']}")
        
        return results

    def _calculate_retry_stats(self, processing_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule les statistiques des retries"""
        total_retries = 0
        items_with_retries = 0
        
        for detail in processing_details:
            if detail.get("status") in ["success", "failed"] and "attempts_made" in detail:
                attempts = detail["attempts_made"]
                if attempts > 1:
                    total_retries += (attempts - 1)
                    items_with_retries += 1
        
        return {
            "total_retries_used": total_retries,
            "items_with_retries": items_with_retries,
            "avg_retries_per_item": total_retries / len(processing_details) if processing_details else 0
        }