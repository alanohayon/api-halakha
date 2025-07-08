from typing import Dict, Any
import structlog
from app.core.config import Settings
from app.services.openai_service import OpenAIService
from app.services.notion_service import NotionService
from app.services.supabase_service import SupabaseService
from app.core.config import get_settings

from app.utils.performance import measure_execution_time, measure_with_metadata
from ..schemas.notion import NotionStatus

logger = structlog.get_logger()

class ProcessingService:
    def __init__(self):
        settings = get_settings()
            
        self.supabase_service = SupabaseService()
        self.settings = settings
        self.openai_service = OpenAIService()
        self.notion_service = NotionService()

    @measure_execution_time("process_and_publish_halakha")
    async def process_and_publish_halakha(self, halakha_content: str, add_day_for_notion: int = 0) -> str:
        logger.info("🚀 Démarrage du processus de traitement complet de la halakha.")
        try:
            # 1. Traitement par OpenAI
            logger.info("Étape 1/3 : Traitement du contenu par OpenAI...")
            processed_data = await self.openai_service.queries_halakha(halakha_content)
            logger.info("Génération du contenu pour le post...")
            post_result = await self.openai_service.queries_post_legende(
                halakha_content, 
                processed_data["answer"]
            )
            # Combiner toutes les données
            complete_data = {
                **processed_data,
                "text_post": post_result["post_text"],
                "legend": post_result["legende_text"],  # ✅ Utilise legende_text
                "content": halakha_content  # Assure que 'content' est le texte initial
            }
            logger.info("✅ Données traitées par OpenAI.")

            # 2. Sauvegarde dans Supabase
            logger.info("Étape 2/3 : Sauvegarde des données dans Supabase...")
            await self.supabase_service.create_halakha(complete_data)
            logger.info("✅ Données sauvegardées avec succès dans Supabase.")

            # 3. Création de la page sur Notion
            logger.info("Étape 3/3 : Création de la page sur Notion...")
            notion_page = await self.notion_service.create_halakha_page(
                complete_data,
                add_day=add_day_for_notion,
            )
            logger.info(f"✅ Page Notion créée avec succès.")

            logger.info("🎉 Processus complet terminé avec succès !")
            return notion_page.get("url", "URL non disponible")
        except Exception as e:
            logger.error(f"❌ Échec du processus de traitement : {e}", exc_info=True)
            raise

    @measure_with_metadata(service="processing", operation_type="json_processing", source="json_file")
    async def process_halakha_from_json(self, json_index: int, schedule_days: int = 0) -> Dict[str, Any]:
        try:
            from ..utils.json_loader import load_halakha_by_index
            halakha_data = await load_halakha_by_index(json_index)
            # Appel direct à process_and_publish_halakha avec halakha_data comme contenu
            notion_url = await self.process_and_publish_halakha(halakha_content=halakha_data, add_day_for_notion=schedule_days)
            return {"notion_page_url": notion_url, "status": "completed"}
        except Exception as e:
            logger.error("Processing failed", error=str(e), json_index=json_index)
            raise

    @measure_with_metadata(service="processing", operation_type="ai_processing", provider="openai")
    async def _process_with_openai(self, halakha_id: int) -> None:
        halakha = await self.supabase_service.get_halakha_by_id(halakha_id)
        if not halakha:
            raise ValueError(f"Halakha {halakha_id} not found")
        # Marquer comme en cours (si méthode update existe)
        await self.supabase_service.update_halakha_partial(halakha_id, {"status": NotionStatus.IN_PROGRESS})
        try:
            # 1. Analyse de la halakha
            ai_result = await self.openai_service.queries_halakha(halakha['content'])
            
            # 2. Génération du contenu Instagram
            post_result = await self.openai_service.queries_post_legende(
                halakha['content'], 
                ai_result["answer"]
            )
            
            await self.supabase_service.update_halakha_partial(halakha_id, {
                "answer": ai_result.get("answer"),
                "text_post": post_result["post_text"],
                "legend": post_result["legende_text"],  # ✅ Utilise legende_text
                "status": NotionStatus.COMPLETED
            })
        except Exception as e:
            await self.supabase_service.update_halakha_partial(halakha_id, {"status": NotionStatus.FAILED})
            raise

    @measure_with_metadata(service="processing", operation_type="publication", provider="notion")
    async def _publish_to_notion(self, halakha_id: int, schedule_days: int) -> None:
        halakha = await self.supabase_service.get_halakha_by_id(halakha_id)
        if not halakha:
            raise ValueError(f"Halakha {halakha_id} not found")
        await self.supabase_service.update_halakha_partial(halakha_id, {"status": NotionStatus.IN_PROGRESS})
        try:
            await self.notion_service.create_halakha_page(
                halakha,
                add_day=schedule_days
            )
            await self.supabase_service.update_halakha_partial(halakha_id, {"status": NotionStatus.COMPLETED})
        except Exception as e:
            await self.supabase_service.update_halakha_partial(halakha_id, {"status": NotionStatus.FAILED})
            raise
    
    @measure_execution_time("process_halakha_for_notion")
    async def process_halakha_for_notion(self, halakha_content: str, add_day_for_notion: int = 0) -> str:
        logger.info("🚀 Démarrage du processus de traitement complet de la halakha.")
        try:
            # 1. Traitement par OpenAI
            logger.info("Étape 1/2 : Traitement du contenu par OpenAI...")
            processed_data = await self.openai_service.queries_halakha(halakha_content)
            logger.info("Génération du contenu pour le post...")
            post_result = await self.openai_service.queries_post_legende(halakha_content, processed_data["answer"])
            
            # Combiner toutes les données
            complete_data = {
                **processed_data,
                "text_post": post_result["post_text"],
                "legend": post_result["legende_text"],  # ✅ Utilise legende_text
                "content": halakha_content  # Assure que 'content' est le texte initial
            }
            logger.info("✅ Données traitées par OpenAI.")
            
            # 2. Création de la page sur Notion
            logger.info("Étape 2/2 : Création de la page sur Notion...")
            notion_page = await self.notion_service.create_halakha_page(
                complete_data,
                add_day=add_day_for_notion,
            )
            logger.info(f"✅ Page Notion créée avec succès.")
            
            logger.info("🎉 Processus complet terminé avec succès !")
            return notion_page.get("url", "URL non disponible")
        except Exception as e:
            logger.error(f"❌ Échec du processus de traitement : {e}", exc_info=True)
            raise