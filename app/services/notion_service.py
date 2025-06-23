import logging
from datetime import datetime, timedelta
from notion_client import Client, APIResponseError
from app.core.config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotionService:
    def __init__(self, settings: Settings):
        if not settings.notion_api_token or not settings.notion_database_id_post_halakha:
            raise ValueError("Les configurations Notion (token et ID de base de données) sont requises.")
        
        self.settings = settings
        self.notion = Client(auth=self.settings.notion_api_token)

    def _build_page_properties(self, processed_data: dict, add_day: int, image_url: str = None) -> dict:
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
        
        # Champ Status (Exemple, à adapter si besoin)
        # properties["Status"] = {"status": {"name": "Prêt à publier"}}
        
        logger.info(" ☑️ 📄 Propriétés de la page construites avec succès.")
        return properties
    
    def create_post_page(self, processed_data: dict, add_day: int, image_url: str = None) -> dict:
        """
        Crée une nouvelle page dans la base de données Notion des posts.
        """
        logger.info(f"Création d'une nouvelle page Notion dans la base de données: {self.settings.notion_database_id_post_halakha}")
        try:
            properties = self._build_page_properties(processed_data, add_day, image_url)
            
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
