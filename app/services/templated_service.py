import asyncio
import logging
from typing import List, Tuple, Optional, Union
import httpx
from app.core.config import get_settings
from app.core.exceptions import TemplatedServiceError

logger = logging.getLogger(__name__)


class TemplatedService:
    def __init__(self):
        settings = get_settings()

        if not settings.templated_api_key:
            raise TemplatedServiceError("Configuration Templated.io manquante (clé API)", status_code=500)
        if not settings.templated_template_id:
            raise TemplatedServiceError("Configuration Templated.io manquante (template id)", status_code=500)

        self.settings = settings
        self.api_base_url = "https://api.templated.io/v1"
        self.timeout = httpx.Timeout(settings.request_timeout)

    @staticmethod
    def _split_bullet_text(text: str) -> List[str]:
        """
        Découpe un texte en segments en prenant les parties entre des tirets '-'.
        Règle: ignorer tout avant le premier '-' et couper avant chaque '-'.

        Exemple d'entrée:

        """
        if text is None:
            return []

        # Normaliser les retours ligne et splitter par '-'
        parts = []
        current = []
        seen_first_dash = False
        for line in text.splitlines():
            # On parcourt char par char pour repérer les tirets de début de puce
            i = 0
            while i < len(line):
                ch = line[i]
                if ch == "-":
                    if not seen_first_dash:
                        # Le premier '-' active la collecte
                        seen_first_dash = True
                    else:
                        # Nouveau item -> on flush l'actuel
                        if current:
                            item = "".join(current).strip()
                            if item:
                                parts.append(item)
                            current = []
                    # Consommer le '-' et l'espace éventuel qui suit
                    i += 1
                    # Sauter espaces après '-'
                    while i < len(line) and line[i].isspace():
                        i += 1
                    # Continuer collecte de ce point
                    # et ne pas ajouter le '-'
                    # donc continue sans increment supplémentaire ici
                    # pour retomber dans l'ajout de chars
                    continue
                # Collecte si on a vu au moins un '-'
                if seen_first_dash:
                    current.append(ch)
                i += 1

            # Fin de ligne -> si on est en collecte, garder le saut de ligne
            if seen_first_dash:
                current.append("\n")

        # Dernier item
        if current:
            last = "".join(current).strip()
            if last:
                parts.append(last)

        # Nettoyage d'espaces superflus en début de deuxième puce de l'exemple
        return [p.strip() for p in parts]

    
    def _build_page_1(self, image_url: str, question = """Ceci est un texte <i>en italique</i> et <strong>en gras</strong>."""):
        """
            construction de la page_1
        """
        return {
                'page': 'page-1',
                    'layers': {
                        'image-1' : {'image_url' : image_url },
                        'txt_question' : {
                            "text": """Ceci est un texte Comment faire la Havdala  un feu 🔥 allumé avant KippourKippour. """,
                            'color' : 'rgba(9, 10, 10, 1)',
                            'font_family' : 'Radley',
                            'font_size' : '56px',
                            'width' : '748',
                            'x' : "160",
                            'y' : "760",
                            'autofit' : 'height',
                            'border_radius' : '25px',
                            'horizontal_align' : 'center',
                            'vertical_align' : 'center',
                        },

                    },
                }
        
        # Calculer le nombre de caractere avec espace

#hide
    

    async def render_two_pages(
        self,
        image_url: str,
        title: str,
        segments: List[str],
        format: str = "jpg",
        merge_pdf: bool = False,
        template_id: Optional[str] = None,
    ) -> Union[List[dict], dict]:
        """
        Crée un rendu multi‑pages (2 pages) via Templated.io en utilisant une image, un titre, et 2 segments de texte.

        Returns: la réponse JSON Templated (liste d'objets de rendu ou objet unique selon le template/config).
        """
        if not image_url:
            raise TemplatedServiceError("image_url requis")
        if not title:
            raise TemplatedServiceError("title requis")
        if not segments or len(segments) < 2:
            raise TemplatedServiceError("Au moins 2 segments de texte sont requis pour 2 pages")

        page_1 = self._build_page_1(image_url, title)

        tpl_id = template_id or self.settings.templated_template_id

        # Exemple de structure pages, à adapter aux noms de couches du template Templated.io
        payload = {
            "template": tpl_id,
            "format": format,
            # "merge": bool(merge_pdf),
            "pages": [
                page_1,
                # {
                #     'page': 'page-2',
                #     'layers': {
                #         'image-2' : {
                #         'image_url' : image_url,
                #         },
                #         'text-1-copy' : {
                #         'text' : """Manger la veille de Kippour 🍽️ est une mitsva, considérée par certains comme venant de la Torah 📜, valable pour hommes et femmes.""",
                #         'color' : 'rgba(0, 0, 0, 1)'
                #         },
                #         'text-1-copy-copy' : {
                #         'text' : """Celui qui mange est récompensé comme s'il avait jeûné 🏅, appelée Mitsva cadeau 🎁 (Yoma 81). Même pour les personnes malades 🤒, cette mitsva s'applique. """,
                #         'color' : 'rgba(0, 0, 0, 1)'
                #         }, 
                #         'text-1-copy-copy-copy' : {
                #         'text' : """Important d'avoir l'intention de réaliser la mitsva lors de chaque repas 🥘 (Choulhan Aroukh, Michna Broura). """,
                #         'color' : 'rgba(0, 0, 0, 1)'
                #         }
                #     }
                # }
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.settings.templated_api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.api_base_url}/render"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    raise TemplatedServiceError(
                        f"Échec de rendu Templated.io ({resp.status_code})",
                        status_code=resp.status_code,
                        details={"body": resp.text},
                    )
                data = resp.json()
                return data
        except httpx.TimeoutException:
            raise TemplatedServiceError("Timeout Templated.io dépassé")
        except httpx.HTTPError as e:
            raise TemplatedServiceError(f"Erreur HTTP Templated.io: {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue Templated.io: {e}")
            raise TemplatedServiceError(f"Erreur inattendue Templated.io: {e}")


