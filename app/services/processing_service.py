from typing import Dict, Any
import asyncio
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings
from app.services.openai_service import OpenAIService
from app.services.notion_service import NotionService
from app.repositories.halakha_repository import HalakhaRepository

from ..schemas.halakha import HalakhaCreate, ProcessingStatus

logger = structlog.get_logger()

class ProcessingService:
    def __init__(self, db_session: AsyncSession, settings: Settings):
        self.db_session = db_session
        self.settings = settings
        # Les services externes sont initialisés ici
        self.openai_service = OpenAIService(settings)
        self.notion_service = NotionService(settings)
        # Le repository est initialisé avec la session de la base de données
        self.halakha_repo = HalakhaRepository(db_session)

    async def process_and_publish_halakha(self, halakha_content: str, add_day_for_notion: int = 0) -> str:
        """
        Orchestre le traitement complet d'une halakha : OpenAI -> Supabase -> Notion.
        """
        logger.info("🚀 Démarrage du processus de traitement complet de la halakha.")
        
        try:
            # 1. Traitement par OpenAI pour extraire les données et générer les textes
            logger.info("Étape 1/3 : Traitement du contenu par OpenAI...")
            processed_data = self.openai_service.process_halakha(halakha_content)
            logger.info("✅ Données traitées par OpenAI.")          
            
            # 3. Sauvegarde dans la base de données Supabase via le Repository
            logger.info("Étape 2/3 : Sauvegarde des données dans Supabase...")
            await self.halakha_repo.save_full_halakha(processed_data, halakha_content)
            logger.info("✅ Données sauvegardées avec succès dans Supabase.")

            # 4. Création de la page sur Notion
            logger.info("Étape 3/3 : Création de la page sur Notion...")
            notion_page = self.notion_service.create_post_page(
                processed_data,
                add_day=add_day_for_notion,
            )
            logger.info(f"✅ Page Notion créée avec succès.")

            logger.info("🎉 Processus complet terminé avec succès !")
            return notion_page.get("url", "URL non disponible")

        except Exception as e:
            logger.error(f"❌ Échec du processus de traitement : {e}", exc_info=True)
            # exc_info=True va logger la stack trace complète pour un meilleur débogage
            raise

    async def process_halakha_from_json(
        self, 
        json_index: int,
        schedule_days: int = 0
    ) -> Dict[str, Any]:
        """Traite une halakha depuis les données JSON"""
        try:
            # 1. Charger depuis JSON
            from ..utils.json_loader import load_halakha_by_index
            halakha_data = await load_halakha_by_index(json_index)
            
            # 2. Créer en base
            halakha = await self.halakha_repo.create(
                HalakhaCreate(**halakha_data)
            )
            
            # 3. Traiter avec OpenAI
            await self._process_with_openai(halakha.id)
            
            # 4. Publier vers Notion
            await self._publish_to_notion(halakha.id, schedule_days)
            
            return {"halakha_id": halakha.id, "status": "completed"}
            
        except Exception as e:
            logger.error("Processing failed", error=str(e), json_index=json_index)
            raise

    async def _process_with_openai(self, halakha_id: int) -> None:
        """Traitement OpenAI"""
        halakha = await self.halakha_repo.get(halakha_id)
        if not halakha:
            raise ValueError(f"Halakha {halakha_id} not found")
        
        # Marquer comme en cours
        await self.halakha_repo.update(
            halakha_id, 
            {"status": ProcessingStatus.IN_PROGRESS}
        )
        
        try:
            # Appel OpenAI
            ai_result = await self.openai_service.process_halakha(
                halakha.content
            )
            
            # Mise à jour avec les résultats
            await self.halakha_repo.update(halakha_id, {
                "answer": ai_result.get("answer"),
                "text_post": ai_result.get("text_post"),
                "legend": ai_result.get("legend"),
                "status": ProcessingStatus.COMPLETED
            })
            
        except Exception as e:
            await self.halakha_repo.update(
                halakha_id, 
                {"status": ProcessingStatus.FAILED}
            )
            raise

    async def _publish_to_notion(self, halakha_id: int, schedule_days: int) -> None:
        """Publie la halakha vers Notion"""
        halakha = await self.halakha_repo.get(halakha_id)
        if not halakha:
            raise ValueError(f"Halakha {halakha_id} not found")
        
        # Marquer comme en cours
        await self.halakha_repo.update(
            halakha_id, 
            {"status": ProcessingStatus.IN_PROGRESS}
        )
        
        try:
            # Appel Notion
            await self.notion_service.create_post_page(
                halakha.to_dict(),
                add_day=schedule_days
            )
            
            # Mise à jour avec le statut de publication
            await self.halakha_repo.update(halakha_id, {
                "status": ProcessingStatus.COMPLETED
            })
            
        except Exception as e:
            await self.halakha_repo.update(
                halakha_id, 
                {"status": ProcessingStatus.FAILED}
            )
            raise