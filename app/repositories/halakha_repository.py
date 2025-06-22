import logging
from typing import List, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.halakha import Halakha
from app.models.question import Question
from app.models.answer import Answer
from app.models.source import Source
from app.models.tag import Tag
from app.models.theme import Theme
from app.core.database import Base

logger = logging.getLogger(__name__)

class HalakhaRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def _get_or_create(self, model: Type[Base], **kwargs) -> Base:
        """
        Récupère une instance de modèle si elle existe, sinon la crée.
        _get_or_create(Tag, name="Cacherout"), cette ligne fera en sorte que :
        filter_key vaudra "name".
        filter_value vaudra "Cacherout".
        """
        # Utilise le premier kwarg pour la recherche, typiquement 'name' ou 'full_src'.
        filter_key, filter_value = next(iter(kwargs.items()))
        
        result = await self.db.execute(select(model).filter(getattr(model, filter_key) == filter_value))
        instance = result.scalars().first()
        
        if instance:
            # Si l'objet a été trouvé dans la base de données
            logger.debug(f"Instance trouvée pour {model.__name__}: {filter_value}")
            return instance
        else:
            # Si instance est None (l'objet n'existe pas), on passe à la partie "Create".
            logger.debug(f"Création d'une nouvelle instance pour {model.__name__}: {filter_value}")
            # model(**kwargs) est un raccourci pour Tag(name="Cacherout").
            instance = model(**kwargs)
            self.db.add(instance)
            # Pas de commit ici, on le fera en une seule fois à la fin.
            return instance

    async def save_full_halakha(self, processed_data: Dict[str, Any], halakha_content: str) -> Halakha:
        """
        Sauvegarde une halakha complète avec ses relations (Question, Réponse, Tags, etc.).
        """
        logger.info("💿 Début de la sauvegarde de la halakha complète dans la base de données.")
        try:
            # 1. Créer ou récupérer les Tags
            tags = []
            if "tags" in processed_data:
                for tag_name in processed_data["tags"]:
                    tag = await self._get_or_create(Tag, name=tag_name.strip())
                    tags.append(tag)

            # 2. Créer ou récupérer les Thèmes
            themes = []
            if "themes" in processed_data:
                for theme_name in processed_data["themes"]:
                    theme = await self._get_or_create(Theme, name=theme_name.strip())
                    themes.append(theme)

            # 3. Créer ou récupérer les Sources
            sources = []
            if "sources" in processed_data:
                for src_data in processed_data["sources"]:
                    # On crée une nouvelle instance de Source à chaque fois
                    source = Source(
                        full_src=src_data["full_src"].strip(), 
                        name=src_data["name"], 
                        page=src_data.get("page")
                    )
                    self.db.add(source) # On l'ajoute à la session
                    sources.append(source)
            
            # 4. Créer la Question et la Réponse
            question_obj = Question(question=processed_data["question"])
            answer_obj = Answer(answer=processed_data["answer"])
            
            # 5. Créer l'objet Halakha principal
            new_halakha = Halakha(
                title=processed_data["question"],
                content=halakha_content,
                difficulty_level=processed_data.get("difficulty_level"),
                question=question_obj,
                answer=answer_obj,
                tags=tags,
                themes=themes,
                sources=sources
            )
            logger.info("➡️ Objet Halakha et ses associations créent avec succès")

            self.db.add(new_halakha)
            await self.db.commit()
            await self.db.refresh(new_halakha)
            
            logger.info(f"✅ Halakha '{new_halakha.title}' sauvegardée avec succès avec l'ID: {new_halakha.id}.")
            return new_halakha

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la halakha : {e}")
            await self.db.rollback()
            raise 