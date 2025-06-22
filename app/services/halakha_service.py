# Potentiellement dans app/services/halakha_service.py

from sqlalchemy.orm import Session
from app.models.tag import Tag
from app.models.halakha import Halakha

def get_or_create_tags(db_session: Session, tag_names: list[str]) -> list[Tag]:
    """
    Pour chaque nom de tag dans la liste, récupère le tag existant 
    ou le crée s'il n'existe pas.

    Retourne la liste complète des objets Tag prêts à être associés.
    """
    final_tag_objects = []
    for name in tag_names:
        # On peut standardiser le nom pour éviter les doublons (ex: " Shabbat " -> "Shabbat")
        normalized_name = name.strip().capitalize()
        if not normalized_name:
            continue

        # 1. Vérifier si le tag existe déjà en base
        tag = db_session.query(Tag).filter(Tag.name == normalized_name).first()

        if not tag:
            # 2. S'il n'existe pas, on crée un nouvel objet Tag
            tag = Tag(name=normalized_name)
            db_session.add(tag)

        final_tag_objects.append(tag)

    return final_tag_objects

# --- Exemple d'utilisation lors de la création d'une Halakha ---

def create_halakha_from_ai(db: Session, title: str, content: str, ai_tags: list[str]):
    
    # On utilise notre fonction pour traiter les tags suggérés par l'IA
    tag_models = get_or_create_tags(db, ai_tags)
    
    # Créez votre objet Halakha
    new_halakha = Halakha(
        title=title,
        content=content,
        tags=tag_models,  # SQLAlchemy s'occupe de la magie ici !
        # ... autres champs comme source_id, question_id etc.
    )

    db.add(new_halakha)
    db.commit() # Sauvegarde toutes les modifications (nouvelle halakha et nouveaux tags) en une seule fois
    db.refresh(new_halakha)

    return new_halakha
