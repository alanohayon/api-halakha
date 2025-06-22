from typing import Dict, Any
import asyncio
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.halakha import HalakhaCreate, ProcessingStatus
from .openai_service import OpenAIService
from .notion_service import NotionService

logger = structlog.get_logger()

class ProcessingService:
    def __init__(
        self,
        db: AsyncSession,
        openai_service: OpenAIService,
        notion_service: NotionService
    ):
        self.db = db
        self.openai_service = openai_service
        self.notion_service = notion_service

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