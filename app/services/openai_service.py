import time
import json
import logging
import asyncio
from openai import OpenAI, OpenAIError, APITimeoutError, RateLimitError, APIConnectionError
from app.core.config import get_settings
from app.utils.performance import measure_execution_time, measure_with_metadata
from app.core.exceptions import OpenAIServiceError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        settings = get_settings()
        if not settings.openai_api_key:
            raise OpenAIServiceError("Configuration OpenAI manquante (clé API)", status_code=500)
        
        self.settings = settings
        try:
            self.client = OpenAI(
                api_key=self.settings.openai_api_key,
                organization=self.settings.openai_organization_id,
                project=self.settings.openai_project_id
            )
        except OpenAIError as e:
            logger.error(f"Erreur OpenAI lors de l'initialisation du client : {e}")
            raise OpenAIServiceError(f"Erreur OpenAI lors de l'initialisation du client : {e}") from e
        except Exception as e:
            logger.error("Erreur inattendue lors de l'initialisation du client", error=str(e))
            raise

    async def _create_thread_and_run(self, input_msg: str, asst):
        
        """ Le _ au début est une convention en Python pour dire que c'est une méthode "privée", destinée à être utilisée uniquement à l'intérieur de cette classe (HalakhaRepository)."""
        
        logger.info(f" 🤖 OpenAI: Création d'un Thread et Run ...")
    
        try:
            # thread = session (oblig) persistante de la conversation
            thread_run = self.client.beta.threads.create_and_run(
                assistant_id=asst,
                thread={
                    "messages": [
                        {"role": "user", "content": input_msg}
                    ]
                }
            )

            logger.info(f" 🤖 OpenAI: Run d'un nouveau message envoyé à l'assistant {asst} ...")
            
            return thread_run
            
        except RateLimitError as e:
            raise OpenAIServiceError(f"Erreur de limite de taux : {e}")
        except APITimeoutError as e:
            raise OpenAIServiceError(f"Erreur de délai d'attente : {e}")
        except APIConnectionError as e:
            raise OpenAIServiceError(f"Erreur de connexion lors de la génération de l'image : {e}")
        except OpenAIError as e:
            logger.error(f"Erreur OpenAI lors de la création du thread/run : {e}")
            raise OpenAIServiceError(f"Erreur OpenAI lors de la création du thread/run : {e}")
        except Exception as e:
            return e

    async def _cancel_run(self, thread_id: str, run_id: str):
        """Annule un run en cours"""
        try:
            self.client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)
            logger.info(f"Run {run_id} annulé sur le thread {thread_id}")
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation du run : {e}")
            
    async def _delete_thread(self, thread_id: str):
        """Supprime un thread en cours"""
        try:
            
            self.client.beta.threads.delete(thread_id)
            logger.info(f"Thread {thread_id} supprimé sur le thread.")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du thread : {e}")

    async def _wait_on_run(self, run, timeout: int = 3600, poll_interval: float = 4.0):
        """
        Poll le statut du run toutes les 4s, timeout à 1h pour les traitements longs.
        Retourne l'objet run final.
        """
        
        start = time.time()
 
        try:
            while True:
                run = self.client.beta.threads.runs.retrieve(thread_id=run.thread_id, run_id=run.id)
                logger.info(f" 🤖 Statut du Run {run.id}: {run.status}")
                
                # Si le run est complété ou arrêté 
                if run.status in ["completed", "failed", "cancelled", "expired"]:
                    print(run.status,run.thread_id, run.id)
                    return run
                
                # Si le run est complété ou arreté 
                if run.status == "requires_action":
                    logger.info(" 🔧 Action requise détectée, traitement des outils...")
                    run = await self._submit_tool_outputs_if_required(run)
                    # Continuer le polling après soumission des outils
                    continue
                    
                if time.time() - start > timeout:
                    logger.warning(f" ❌ ⏱️ Timeout de {timeout}s dépassé, annulation du run...")
                    await self._cancel_run(run.thread_id, run.id)
                    # On récupère le statut final après annulation
                    run = self.client.beta.threads.runs.retrieve(thread_id=run.thread_id, run_id=run.id)
                    return run
                await asyncio.sleep(poll_interval)
        except Exception as e:
            logger.error(f"Erreur lors du polling du run : {e}")
            raise
        
    async def _submit_tool_outputs(self, run, tool_outputs: list):
        try:
            logger.info(f" 🔧 Soumission des sorties d'outils pour le run {run.id}")
            formatted_outputs = [
                {
                    "tool_call_id": tool["tool_call_id"],
                    "output": json.dumps(tool["output"])
                }
                for tool in tool_outputs
            ]
            run = self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=run.thread_id,
                run_id=run.id,
                tool_outputs=formatted_outputs
            )
            logger.info(" ✅ Sorties d'outils soumises avec succès")
            return await self._wait_on_run(run)
            
        except OpenAIError as e:
            logger.error(f"Erreur OpenAI lors de la soumission des sorties : {e}")
            raise OpenAIServiceError(f"Erreur lors de la soumission des sorties : {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la soumission : {e}")
            raise

    async def _submit_tool_outputs_if_required(self, run):
        if run.status == "requires_action" and run.required_action and run.required_action.type == "submit_tool_outputs":
            outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                try:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    result = self.tool_functions[func_name](args)
                except Exception as e:
                    result = f"[Erreur: {str(e)}]"

                outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": result
                })

            return await self._submit_tool_outputs(run, outputs)
        return run

    async def _get_assistant_response(self, run) -> str:
        """
        Récupère la réponse du run si completed, sinon gère les erreurs.
        """
        if run.status == "completed":
            messages = self.client.beta.threads.messages.list(thread_id=run.thread_id)
            if not messages.data or not messages.data[0].content or not messages.data[0].content[0].text.value:
                logger.error("Réponse vide de l'assistant.")
                raise OpenAIServiceError("Réponse vide de l'assistant.")
            return messages.data[0].content[0].text.value
        elif run.status == "failed":
            logger.error(f"Le Run a échoué : {run.last_error}")
            raise OpenAIServiceError(f"Le Run a échoué : {run.last_error}")
        elif run.status == "cancelled":
            logger.error("Le Run a été annulé (timeout ou annulation manuelle).")
            raise OpenAIServiceError("Le Run a été annulé (timeout ou annulation manuelle).")
        elif run.status == "expired":
            logger.error("Le Run a expiré (OpenAI n'a pas répondu à temps).")
            raise OpenAIServiceError("Le Run a expiré (OpenAI n'a pas répondu à temps).")
        else:
            logger.error(f"Le Run s'est terminé avec un statut inattendu : {run.status}")
            raise OpenAIServiceError(f"Le Run s'est terminé avec un statut inattendu : {run.status}")

    async def _query_assistant(self, input_msg: str, asst) -> str:
        try:
            run_thread = await self._create_thread_and_run(input_msg, asst)
            run = await self._wait_on_run(run_thread)
            response = await self._get_assistant_response(run)
            await self._delete_thread(run_thread.thread_id)
            return response
        except Exception as e:
            logger.error(e)
            raise
        
    @measure_execution_time("Traitement OpenAI halakha")
    async def queries_halakha(self, halakha_content: str) -> dict:
        """
        Orchestre les appels à OpenAI pour traiter une halakha.
        """
        logger.info("Début du traitement de la halakha avec OpenAI...")
        try:
            # 1. Extraire les données structurées
            logger.info("Extraction des données structurées (question, réponse, etc.)...")
            json_str_response = await self._query_assistant(halakha_content, self.settings.asst_halakha)
            processed_data = json.loads(json_str_response)
            
            
            logger.info("Traitement OpenAI de la halakha terminé avec succès.")
            return processed_data
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON de la réponse OpenAI : {e}")
            raise OpenAIServiceError(f"Réponse invalide de l'assistant de structuration : {e}")
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la halakha par OpenAI : {e}")
            raise

    @measure_execution_time("Traitement OpenAI post_legend")
    async def queries_post_legende(self, halakha_content: str, answer: str) -> dict:
        """
        Génère le contenu Instagram (post et légende).
        Retourne un dictionnaire avec post_text et legende_text.
        """
        try:
            # 2. Générer le texte pour le post
            logger.info("Génération du texte du post Instagram...")
            text_post = await self._query_assistant(answer, self.settings.asst_insta_post)
            
            # 3. Générer la légende
            logger.info("Génération de la légende du post...")
            legend = await self._query_assistant(halakha_content, self.settings.asst_legend_post)
            
            return {
                "post_text": text_post.strip(),
                "legende_text": legend.strip()  # ✅ Changé "caption" en "legende_text"
            }
        except Exception as e:
            logger.error(f"Erreur lors de la génération du contenu Instagram : {e}")
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
    #         raise OpenAIServiceError(f"Erreur OpenAI lors de la génération de l'image : {e}")
