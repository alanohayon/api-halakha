import time
import json
import logging
from openai import OpenAI, OpenAIError, APITimeoutError, RateLimitError, APIConnectionError
from app.core.config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ValueError("La clé API OpenAI n'est pas configurée.")
        
        self.settings = settings
        try:
            self.client = OpenAI(
                api_key=self.settings.openai_api_key,
                organization=self.settings.openai_organization_id,
                project=self.settings.openai_project_id
            )
        except OpenAIError as e:
            logger.error(f"Erreur OpenAI lors de l'initialisation du client : {e}")
            raise RuntimeError(f"Erreur OpenAI lors de l'initialisation du client : {e}") from e
        except Exception as e:
            logger.error("Erreur inattendue lors de l'initialisation du client", error=str(e))
            raise

    def _create_thread_and_run(self, input_msg: str, asst_id: str):
        """ Le _ au début est une convention en Python pour dire que c'est une méthode "privée", destinée à être utilisée uniquement à l'intérieur de cette classe (HalakhaRepository)."""
        logger.info("Création d'un nouveau thread OpenAI...")
        try:
            thread = self.client.beta.threads.create()
            logger.info("Thread créé")
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=asst_id,
                messages=[{"role": "user", "content": input_msg}]
            )
            logger.info(f"Thread {thread.id} et Run {run.id} créés.")
            return thread, run
        except RateLimitError as e:
            raise RuntimeError(f"Erreur de limite de taux : {e}")
        except APITimeoutError as e:
            raise RuntimeError(f"Erreur de délai d'attente : {e}")
        except APIConnectionError as e:
            raise RuntimeError(f"Erreur de connexion lors de la génération de l'image : {e}")
        except OpenAIError as e:
            logger.error(f"Erreur OpenAI lors de la création du thread/run : {e}")
            raise RuntimeError(f"Erreur OpenAI lors de la création du thread/run : {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue lors de la création du thread : {e}")
        
    def _wait_on_run(self, run_id: str, thread_id: str):
        logger.info(f"En attente de la complétion du Run... {run_id}...")
        try:
            while True:
                run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
                if run.status in ["completed", "failed", "cancelled", "requires_action"]:
                    logger.info(f"Run {run.id} terminé avec le statut : {run.status}")
                    return run
                time.sleep(1.5)
        except APITimeoutError as e:
            logger.error(f"Erreur de délai d'attente : {e}")
            raise RuntimeError(f"Erreur de délai d'attente : {e}")   
        except OpenAIError as e:
            logger.error(f"Erreur OpenAI en attendant le run : {e}")
            raise RuntimeError(f"Erreur OpenAI en attendant le run : {e}")
        except Exception as e:
            print(f"Erreur inattendue lors de la récupération du run : {e}")
            return None

    def _get_assistant_response(self, run, thread_id: str) -> str:
        if run.status == "completed":
            messages = self.client.beta.threads.messages.list(thread_id=thread_id)
            return messages.data[0].content[0].text.value
        elif run.status == "requires_action":
            tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
            arguments = tool_call.function.arguments
            logger.info("✅ Success Run !")
            
            return arguments
        else:
            logger.error(f"Le Run s'est terminé avec un statut inattendu : {run.status}")
            raise RuntimeError(f"Le Run s'est terminé avec un statut inattendu : {run.status}")

    def _query_assistant(self, input_msg: str, asst_id: str) -> str:
        try:
            thread, run = self._create_thread_and_run(input_msg, asst_id)
            completed_run = self._wait_on_run(run.id, thread.id)
            response = self._get_assistant_response(completed_run, thread.id)
            return response
        except Exception as e:
            logger.error(f"Erreur lors de l'interrogation de l'assistant {asst_id}: {e}")
            raise
        
    def process_halakha(self, halakha_content: str) -> dict:
        """
        Orchestre les appels à OpenAI pour traiter une halakha.
        """
        logger.info("Début du traitement de la halakha avec OpenAI...")
        try:
            # 1. Extraire les données structurées
            logger.info("Extraction des données structurées (question, réponse, etc.)...")
            json_str_response = self._query_assistant(halakha_content, self.settings.asst_halakha)
            processed_data = json.loads(json_str_response)
            
            # 2. Générer le texte pour le post
            logger.info("Génération du texte du post Instagram...")
            processed_data["text_post"] = self._query_assistant(processed_data["answer"], self.settings.asst_insta_post)
            
            # 3. Générer la légende
            logger.info("Génération de la légende du post...")
            processed_data["legend"] = self._query_assistant(halakha_content, self.settings.asst_legend_post)
            
            logger.info("Traitement OpenAI de la halakha terminé avec succès.")
            return processed_data
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON de la réponse OpenAI : {e}")
            raise RuntimeError(f"Réponse invalide de l'assistant de structuration : {e}")
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la halakha par OpenAI : {e}")
            raise

    

    # def generate_image_url(self, prompt: str) -> str:
    #     """
    #     Génère une image avec DALL-E et retourne son URL publique.
    #     """
    #     logger.info("Génération d'une image avec DALL-E 3...")
    #     try:
    #         response = self.client.images.generate(
    #             model="dall-e-3",
    #             prompt=prompt,
    #             n=1,
    #             size="1024x1024",
    #             quality="standard"
    #         )
    #         image_url = response.data[0].url
    #         logger.info(f"Image générée avec succès. URL: {image_url}")
    #         return image_url
    #     except OpenAIError as e:
    #         logger.error(f"Erreur OpenAI lors de la génération de l'image : {e}")
    #         raise RuntimeError(f"Erreur OpenAI lors de la génération de l'image : {e}")
