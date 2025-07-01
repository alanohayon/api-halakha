import logging
from datetime import datetime, timedelta
from notion_client import Client, APIResponseError
from typing import List, Dict, Any
from app.core.config import Settings
from app.utils.performance import measure_execution_time, measure_with_metadata
import os
from app.services.supabase_service import SupabaseService
from app.utils.image_utils import get_latest_image_path


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes pour les status Notion
class NotionStatus:
    TODO = "Pas commencé"
    INPROGRESS = "En cours"
    COMPLETE = "Terminé"

class NotionService:
    def __init__(self, settings: Settings):
        if not settings.notion_api_token or not settings.notion_database_id_post_halakha:
            raise ValueError("Les configurations Notion (token et ID de base de données) sont requises.")
        
        self.settings = settings
        self.notion = Client(auth=self.settings.notion_api_token)

    @measure_execution_time("Création d'une page Notion simple")
    async def create_page(self, title: str, content: str) -> str:
        """
        Crée une page Notion simple avec titre et contenu
        
        Args:
            title: Titre de la page
            content: Contenu de la page
            
        Returns:
            ID de la page créée
        """
        logger.info(f"Création d'une page Notion simple: {title}")
        try:
            properties = {
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            }
            
            children = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": content}}]
                    }
                }
            ]
            
            response = self.notion.pages.create(
                parent={"database_id": self.settings.notion_database_id_post_halakha},
                properties=properties,
                children=children
            )
            
            logger.info(f"Page Notion créée avec succès. ID: {response['id']}")
            return response['id']
            
        except APIResponseError as e:
            logger.error(f"Erreur de l'API Notion lors de la création de la page : {e.code} - {e.body}")
            raise RuntimeError(f"Erreur API Notion: {e.body}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la création de la page Notion : {e}")
            raise RuntimeError(f"Erreur inattendue lors de la création de la page Notion: {e}")

    @measure_execution_time("Récupération d'une page Notion")
    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Récupère une page Notion par son ID
        
        Args:
            page_id: ID de la page à récupérer
            
        Returns:
            Données de la page
        """
        logger.info(f"Récupération de la page Notion: {page_id}")
        try:
            response = self.notion.pages.retrieve(page_id=page_id)
            logger.info(f"Page Notion récupérée avec succès: {page_id}")
            return response
            
        except APIResponseError as e:
            logger.error(f"Erreur de l'API Notion lors de la récupération de la page : {e.code} - {e.body}")
            raise RuntimeError(f"Erreur API Notion: {e.body}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération de la page Notion : {e}")
            raise RuntimeError(f"Erreur inattendue lors de la récupération de la page Notion: {e}")

    @measure_execution_time("Synchronisation des halakhot vers Notion")
    async def sync_halakhot(self, halakha_ids: List[int]) -> List[str]:
        """
        Synchronise des halakhot vers Notion
        
        Args:
            halakha_ids: Liste des IDs des halakhot à synchroniser
            
        Returns:
            Liste des IDs des pages créées
        """
        logger.info(f"Synchronisation de {len(halakha_ids)} halakhot vers Notion")
        created_pages = []
        
        try:
            # Pour l'instant, on crée des pages simples
            # Cette méthode devrait être adaptée selon votre logique métier
            for halakha_id in halakha_ids:
                page_id = await self.create_page(
                    title=f"Halakha {halakha_id}",
                    content=f"Contenu de la halakha {halakha_id}"
                )
                created_pages.append(page_id)
                
            logger.info(f"Synchronisation terminée. {len(created_pages)} pages créées.")
            return created_pages
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des halakhot : {e}")
            raise RuntimeError(f"Erreur lors de la synchronisation des halakhot: {e}")

    def _build_page_properties(self, processed_data: dict, add_day: int, image_url: str = None, status: str = NotionStatus.INPROGRESS) -> dict:
        """
        Crée une nouvelle page dans la base de données Notion
        
        Args:
            processed_data: Données traitées par OpenAI
            schedule_days: Nombre de jours à ajouter à la date de publication
            
        Returns:
            Réponse de l'API Notion
        """
        logger.info("Construction des propriétés de la page Notion...")
        properties = {}

        # Titre de la page (Question)
        if "question" in processed_data:
            properties["question"] = {"title": [{"text": {"content": processed_data["question"]}}]}
        else:
            raise ValueError("La clé 'question' est manquante dans les données traitées.")

        # Champs texte (avec troncature si nécessaire)
        for key in ["text_post", "legend", "content"]:
            if key in processed_data and processed_data[key]:
                content = processed_data[key]
                # L'API Notion a une limite de 2000 caractères par bloc de texte riche.
                if len(content) > 2000:
                    logger.warning(f"Le contenu du champ '{key}' dépasse 2000 caractères et sera tronqué.")
                    content = content[:1997] + "..."
                    logger.warning(" ⚠️ Content du text trop long, text raccourci ! ")
                
                properties[key] = {"rich_text": [{"text": {"content": content}}]}
        # Champ Image (si une URL est fournie)
        if image_url:
            logger.info(f"Ajout de l'image depuis l'URL: {image_url}")
            properties["Image"] = {
                "files": [{"name": "image_dalle", "external": {"url": image_url}}]
            }
        # Champ Date
        date_value = datetime.now() + timedelta(days=add_day)
        properties["date_post"] = {"date": {"start": date_value.isoformat()}}
        
        # Champ Status - Configurable
        properties["status"] = {"status": {"name": status}}
        
        logger.info(" ☑️ 📄 Propriétés de la page construites avec succès.")
        return properties
    
    @measure_execution_time("Création d'une Halakha Notion")
    def create_halakha_page(self, processed_data: dict, add_day: int, status: str = NotionStatus.INPROGRESS) -> dict:
        """
        Crée une nouvelle page dans la base de données Notion des posts.
        """
        logger.info(f"Création d'une nouvelle page Notion dans la base de données: {self.settings.notion_database_id_post_halakha}")
        try:
            # 1. Trouver la dernière image
            # latest_image_path = get_latest_image_path()
            # print("lcreate halakha page latest_image_path", latest_image_path)
            # if latest_image_path:
            #     # 2. Uploader l'image sur Supabase et obtenir l'URL publique
            #     image_url = SupabaseService.upload_image(latest_image_path)
            
            # 3. Construire les propriétés de la page Notion (avec l'URL de l'image = Nonz)
            properties = self._build_page_properties(processed_data, add_day, None, status)
            # 4. Créer la page Notion
            response = self.notion.pages.create(
                    parent={"database_id": self.settings.notion_database_id_post_halakha},
                    properties=properties
                )
            logger.info(f"Page Notion créée avec succès. ID: {response['id']}")
            return response
        except APIResponseError as e:
            logger.error(f"Erreur de l'API Notion lors de la création de la page : {e.code} - {e.body}")
            raise RuntimeError(f"Erreur API Notion: {e.body}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la création de la page Notion : {e}")
            raise RuntimeError(f"Erreur inattendue lors de la création de la page Notion: {e}")
