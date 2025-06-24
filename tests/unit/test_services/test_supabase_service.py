import json
import pytest
import sys
import os

from app.services.supabase_service import SupabaseService
from app.core.database import get_supabase

@pytest.fixture
def supabase_client():
    """Fixture pour obtenir le vrai client Supabase"""
    return get_supabase()

@pytest.fixture
def supabase_service(supabase_client):
    """Fixture pour obtenir le vrai service Supabase"""
    return SupabaseService(supabase_client)

@pytest.mark.asyncio
async def test_create_and_delete_halakha_with_openai_response(supabase_service):
    """Test d'intégration : création puis suppression d'une halakha avec la réponse d'OpenAI"""
    # Utiliser le fichier halakha_ai_ex.json qui a la bonne structure
    halakha_ai_ex_path = os.path.join(os.path.dirname(__file__), '../../../app/data/halakha_ai_ex.json')
    with open(halakha_ai_ex_path, encoding='utf-8') as f:
        halakha_data = json.load(f)

    print("📝 Données à insérer:")
    print(json.dumps(halakha_data, indent=2, ensure_ascii=False)[:500] + "...")

    # Création réelle dans Supabase
    created = await supabase_service.create_halakha(halakha_data)
    print("✅ Résultat de l'insertion :", created)

    # Vérifications simples
    assert created is not None, "Aucune réponse de Supabase"
    assert "title" in created, "Le champ 'title' est manquant"
    assert created["title"] == halakha_data["title"], "Le titre n'est pas correct"
    assert "answer" in created, "Le champ 'answer' est manquant"
    assert created["answer"] == halakha_data["answer"], "La réponse n'est pas correcte"
    assert "id" in created, "L'ID de la halakha créée est manquant"
    assert "question" in created, "Le champ 'question' est manquant"
    assert created["question"] == halakha_data["question"], "La question n'est pas correcte"

    # Vérifier les sources, themes et tags
    assert "sources" in created, "Le champ 'sources' est manquant"
    assert len(created["sources"]) == len(halakha_data["sources"]), "Le nombre de sources ne correspond pas"
    
    assert "themes" in created, "Le champ 'themes' est manquant"
    assert len(created["themes"]) == len(halakha_data["themes"]), "Le nombre de thèmes ne correspond pas"
    
    assert "tags" in created, "Le champ 'tags' est manquant"
    assert len(created["tags"]) == len(halakha_data["tags"]), "Le nombre de tags ne correspond pas"

    # Nettoyage : suppression de la halakha créée
    halakha_id = created["id"]
    deleted = await supabase_service.delete_halakha(halakha_id)
    assert deleted, f"La halakha avec l'ID {halakha_id} n'a pas été supprimée correctement"
    print(f"🗑️ Halakha {halakha_id} supprimée avec succès.") 