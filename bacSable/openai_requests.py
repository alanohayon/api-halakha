import time
import os
import json
import requests
import base64
from dotenv import load_dotenv
import openai
from openai import OpenAIError, OpenAI, APITimeoutError, RateLimitError, APIConnectionError


class OpenaiRequests:

    def __init__(self):
        load_dotenv()

        # Load environment variables
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.project_id = os.getenv("OPENAI_PROJECT_AI")
        self.organization_id = os.getenv("OPENAI_ORGANIZATION_ID")

        # keys for the different assistants
        self.asst_halakha = os.getenv("ASST_HALAKHA")
        self.asst_prompt_dallE = os.getenv("ASST_PROMPT_DALLE")
        self.asst_text_post = os.getenv("ASST_INSTA_POST")
        self.asst_legend_post = os.getenv("ASST_LEGEND_POST")

        if not self.api_key:
            raise EnvironmentError("Clé API OpenAI non définie dans les variables d'environnement.")

        openai.api_key = self.api_key
        try:
            self.client = OpenAI(
                organization=self.organization_id,
                project=self.project_id
            )
        except OpenAIError as e:
            print(f"Erreur OpenAI lors de l'initialisation du client : {e}")
            self.client = None
        except Exception as e:
            print(f"Erreur inattendue lors de l'initialisation du client : {e}")
            self.client = None

    def create_thread_and_run(self, input_msg, asst_id):
        try:
            thread = self.client.beta.threads.create()
            print("#1 Thread créé.")
        except OpenAIError as e:
            raise RuntimeError(f"Erreur OpenAI lors de la création du thread : {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue lors de la création du thread : {e}")

        run = self.submit_message(asst_id, thread, input_msg)
        if not run:
            raise RuntimeError("Impossible de soumettre le message à l'assistant.")
        return thread, run

    def submit_message(self, asst_id, thread, user_message):
        try:
            self.client.beta.threads.messages.create(
                thread_id=thread.id, role="user", content=user_message
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=asst_id,
            )
            print("#2 Message crée et soumis à l'assistant.")
            return run
        except RateLimitError as e:
            raise RuntimeError(f"Erreur de limite de taux : {e}")
        except APITimeoutError as e:
            raise RuntimeError(f"Erreur de délai d'attente : {e}")
        except APIConnectionError as e:
            raise RuntimeError(f"Erreur de connexion lors de la génération de l'image : {e}")
        except OpenAIError as e:
            raise RuntimeError(f"Erreur OpenAI : {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue : {e}")

    def wait_on_run(self, run, thread):
        print("#3 Exécution du RUN...")
        try:
            count_time = 0
            while run.status == "queued" or run.status == "in_progress":
                count_time += 1
                print(run.status)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                time.sleep(1.5)
                if count_time > 20:
                    self.client.beta.threads.runs.cancel(
                        thread_id=thread.id,
                        run_id=run.id)
                    return None
            print(run.status)
            return run
        except APITimeoutError as e:
            print(f"Erreur de délai d'attente : {e}")
            return None
        except OpenAIError as e:
            print(f"Erreur OpenAI : {e}")
            return None
        except Exception as e:
            print(f"Erreur inattendue lors de la récupération du run : {e}")
            return None

    def query_assistant_json(self, input_msg):
        try:
            thread, run = self.create_thread_and_run(input_msg, self.asst_halakha)
            if not run:
                raise RuntimeError("Le run n'a pas été correctement créé.")

            run = self.wait_on_run(run, thread)
            if not run:
                raise RuntimeError("Le run n'a pas pu être complété.")

            tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
            arguments = tool_call.function.arguments
            print("#4 Argument récupéré.")
            print("## Success of OpenAI !")

            json_response = json.loads(arguments)
            return json_response
        except Exception as e:
            raise RuntimeError(f"Erreur dans query_assistant_json : {e}")

    def query_assistant(self, input_msg, asst_id):
        try:
            thread, run = self.create_thread_and_run(input_msg, asst_id)
            if not run:
                raise RuntimeError("Le run n'a pas été correctement créé.")

            run = self.wait_on_run(run, thread)
            if not run:
                raise RuntimeError("Le run n'a pas pu être complété.")

            response = self.client.beta.threads.messages.list(thread.id).data[0].content[0].text.value

            print("#4 Argument récupéré.")
            print("## Success of OpenAI !")
            return response
        except Exception as e:
            raise RuntimeError(f"Erreur dans query_assistant_json : {e}")

    def generate_text_post(self, halakha_content):
        try:
            response = self.query_assistant(halakha_content, self.asst_text_post)
            print(response)
            return response
        except OpenAIError as e:
            raise RuntimeError(f"Erreur OpenAI lors de la génération du texte : {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue lors de la génération du texte : {e}")

    def generate_legend_post(self, halakha_content):
        try:
            response = self.query_assistant(halakha_content, self.asst_legend_post)
            print(response)
            return response
        except OpenAIError as e:
            raise RuntimeError(f"Erreur OpenAI lors de la génération du texte : {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue lors de la génération du texte : {e}")

    # def generate_all_post(self):

    def generate_prompt_dallE(self, question_hlk):
        # pre_prompt = f"""
        # Adapte ce prompt au text ci dessous:
        #
        # prompt: Crée une illustration 1024x1024 au style moderne, réaliste et détaillé qui représente le concept suivant : [Insérer une brève description du concept ou de l'idée principale du texte]. L'image doit capturer un moment précis où [décrire l'action ou la situation principale du texte]. Inclue des éléments visuels détaillés comme [mentionner les objets ou éléments contextuels pertinents] pour ajouter du réalisme à la scène. Utilisez une lumière qui correspond au thème du texte et des couleurs qui s'adaptent à la situation ou à la représentation des idées. Le style vestimentaire doit être moderne avec des couleurs sobre et moderne, ** je ne veux pas de colorful ou de color vibrant**. Les visages et les vêtements doivent être réalisés avec un souci du détail et du réalisme. Évitez les références directes à la spiritualité ou aux croyances religieuses, en mettant l'accent sur l'aspect humain et réaliste de la scène et de la situation. - Important : ** dans la description je ne veux pas d'adjectif Colorful et Vibrant !**
        # text:{question_hlk}
        # """

        pre_prompt = f"""
        Rédige un prompt en français pour DALL·E qui illustre visuellement la question suivante : {question_hlk}.

        Instructions :
        La représentation doit être réaliste et moderne.
        L’image doit être sobre, avec des couleurs naturelles et un éclairage réaliste.
        Interdiction : Ne pas mettre les couleurs vives et les styles trop artistiques ou exagérés.*Pas de *Colorful* ou de *Vibrant*"*
        """

        try:
            prompt = self.query_assistant(pre_prompt, self.asst_prompt_dallE)
            print(prompt)
            return prompt
        except OpenAIError as e:
            raise RuntimeError(f"Erreur OpenAI lors de la génération de l'image : {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue : {e}")

    def generate_image(self, text_img):

        prompt = f"""
          Le rendu que tu vois ici est basé sur un style graphique flat design moderne et minimaliste, souvent utilisé dans l’illustration éditoriale, les applications mobiles et les interfaces web contemporaines. Voici les détails du style utilisé :

🎨 Style graphique :
	•	Flat design : Sans effets de textures, d’ombres réalistes ou de dégradés complexes. Tout est en aplats de couleurs.
	•	Palette douce et chaleureuse : Des tons beige, crème, bleu nuit, et blanc cassé pour créer une ambiance calme et respectueuse.
	•	Contours simples et lisses : Pas de détails superflus, des lignes nettes et épurées, avec un tracé uniforme.
	•	Silhouettes stylisées : Les personnages sont simplifiés, sans traits de visage complexes (yeux, bouche très discrets), mais conservant assez d’expression corporelle pour transmettre une émotion.
	•	Proportions réalistes, mais adoucies : Le corps est proche de la réalité mais légèrement arrondi pour un effet plus doux et apaisant.

🖌️ Style d’illustration :
	•	Inspiré du style vectoriel : Comme ce qu’on trouve dans les outils comme Adobe Illustrator ou Figma.
	•	Ambiance “editorial illustration” : Un style souvent vu dans les magazines, journaux ou blogs pour représenter des scènes de vie de façon élégante et non intrusive.
	•	Statique mais narratif : L’image capture un moment figé mais chargé de sens, dans un cadre domestique familier.
	
	Text:
        {text_img}
        
                 """

        try:

            print("Génération de l'image (20sec)...")
            img = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )

            image_url = img.data[0].url # ✅ URL de l’image
            download_response = requests.get(image_url)

            if download_response.status_code == 200:
                downloads_folder = os.path.expanduser("~/Downloads")
                filename = "image_dalle3.png"
                filepath = os.path.join(downloads_folder, filename)
                with open(filepath, "wb") as f:
                    f.write(download_response.content)
                print(f"✅ Image téléchargée dans : {filepath}")
            else:
                print(f"❌ Échec du téléchargement (code {download_response.status_code})")


            print("Connard")

        except OpenAIError as e:
            raise RuntimeError(f"Erreur OpenAI lors de la génération de l'image : {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur inattendue lors de la génération de l'image : {e}")
