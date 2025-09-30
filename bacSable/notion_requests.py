import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_client import Client, APIResponseError

# Configuration du logging (optionnel)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotionAPIError(Exception):
    """Exception personnalisée pour les erreurs liées à l'API Notion."""
    pass

class NotionRequests:
    def __init__(self):
        """
        Initialise la classe en récupérant les variables d'environnement et en définissant quelques attributs.
        """
        load_dotenv()

        self.api_token = os.getenv("NOTION_API_TOKEN")
        self.database_id = os.getenv("NOTION_DATABASE_ID_POST_HALAKHA")
        self.image_directory = "/Users/alanohayon/Library/Mobile Documents/com~apple~CloudDocs/post_halakhot/post"

        if not self.api_token:
            raise ValueError("La variable d'environnement NOTION_API_TOKEN n'est pas définie.")
        if not self.database_id:
            raise ValueError("La variable d'environnement NOTION_DATABASE_ID_POST_HALAKHA n'est pas définie.")

        self.notion = Client(auth=self.api_token)

    def get_last_image_file(self) -> Path:
        """
        Récupère le fichier image le plus récent dans le dossier self.image_directory.
        Seuls les fichiers avec extension .jpg, .jpeg, .png ou .gif sont considérés.
        """
        try:
            path = Path(self.image_directory)
            if not path.exists() or not path.is_dir():
                raise NotionAPIError(f"Le dossier d'images n'a pas été trouvé : {self.image_directory}")

            image_files = [
                f for f in path.iterdir()
                if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif"]
            ]
            if not image_files:
                raise NotionAPIError("Aucun fichier image n'a été trouvé dans le dossier spécifié.")

            last_image = max(image_files, key=lambda f: f.stat().st_mtime)
            logger.info(f"Dernière image trouvée : {last_image}")
            return last_image
        except Exception as e:
            raise NotionAPIError(f"Erreur lors de la récupération de la dernière image : {e}")

    def build_image_property(self) -> dict:
        """
        Construit la propriété Notion pour le champ 'Image' en utilisant le dernier fichier image trouvé.
        Note : Notion attend un URL accessible publiquement. Ici, on utilise un URL de type file://.
        """
        try:
            image_file = self.get_last_image_file().name
            file_url = f"file://{str(image_file)}"
            image_property = {
                "files": [
                    {
                        "name": image_file,
                        "external": {
                            "url": file_url
                        }
                    }
                ]
            }
            return image_property
        except Exception as e:
            raise NotionAPIError(f"Erreur lors de la construction de la propriété image : {e}")

    def build_page_properties(self, add_day:int, result_ai: dict) -> dict:
        """
        Construit l'objet des propriétés Notion pour une nouvelle page à partir du dictionnaire result_ai.
        Le dictionnaire result_ai doit contenir les clés :
        - question, text_post, promptDallE, legend, date_post, content, status
        """
        try:
            properties = {}

            # Ajout du champ Image
            # properties["Image"] = self.build_image_property()

            if "question" in result_ai:
                properties["question"] = {
                    "title": [
                        {
                            "text": {
                                "content": result_ai["question"]
                            }
                        }
                    ]
                }
            else:
                raise ValueError("Champ requis manquant dans result_ai : question")

            # if "image_url" in result_ai:
            #     properties["image"] = {
            #         "files": [
            #             {
            #                 "name": "image",
            #                 "external": {
            #                     "url": result_ai["image_url"]
            #                 }
            #             }
            #         ]
            #     }
            #
            # else:
            #     raise ValueError("Champ requis manquant dans result_ai : image_url")

            # Pour les autres champs texte, on construit un objet rich_text.
            for key in ["text_post", "legend", "content"]:
                if len(result_ai[key]) < 1980:
                    if key in result_ai:
                        properties[key] = {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": result_ai[key]
                                    }
                                }
                            ]
                        }
                    else:
                        raise ValueError(f"Champ requis manquant dans result_ai : {key}")
                else:
                    logger.warning(f"Le champ {key} est trop long pour être ajouté à Notion.")

            # Gestion du champ date_post (de type date)
            date_value = datetime.now() + timedelta(days=add_day)
            date_iso = date_value.isoformat()
            properties["date_post"] = {
                "date": {
                    "start": date_iso
                }
            }

            # Gestion du champ status (de type État, via select)
            # properties["status"] = {
            #     "select": {
            #         "name": result_ai.get("status", "En cours")
            #     }
            # }

            return properties

        except Exception as e:
            raise NotionAPIError(f"Erreur lors de la construction des propriétés de la page : {e}")

    def query_database(self) -> dict:
        """
        Interroge la base de données Notion (table 'PostHalakha') et retourne la réponse JSON complète.
        """
        try:
            response = self.notion.databases.query(database_id=self.database_id)
            return response
        except APIResponseError as e:
            raise NotionAPIError(f"Erreur de l'API Notion lors de l'interrogation de la base de données : {e.code} - {e.body}")
        except Exception as e:
            raise NotionAPIError(f"Erreur lors de l'interrogation de la base de données : {e}")

    def create_page(self, add_day:int, result_ai: dict) -> dict:
        """
        Crée une nouvelle page dans la base de données Notion en utilisant les données contenues dans result_ai.
        Retourne la réponse JSON complète de Notion.
        """
        try:
            properties = self.build_page_properties(add_day, result_ai)
            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            print("## Page créée :", response)
            return response
        except APIResponseError as e:
            raise NotionAPIError(f"Erreur de l'API Notion lors de la création de la page : {e.code} - {e.body}")
        except Exception as e:
            raise NotionAPIError(f"Erreur lors de la création de la page : {e}")
