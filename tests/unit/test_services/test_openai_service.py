import pytest
import json
import sys
import os
from unittest.mock import Mock, patch
from app.services.openai_service import OpenAIService
from app.core.config import Settings


@pytest.fixture
def mock_settings():
    """Fixture pour utiliser les vraies clés API des settings"""
    from app.core.config import get_settings
    return get_settings()


@pytest.fixture
def mock_openai_client():
    """Fixture pour créer un client OpenAI mocké"""
    with patch('app.services.openai_service.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        yield mock_client


@pytest.fixture
def openai_service(mock_settings, mock_openai_client):
    """Fixture pour créer un service OpenAI avec des mocks"""
    return OpenAIService(mock_settings)


class TestRealOpenAIIntegration:
    """Tests d'intégration avec la vraie API OpenAI"""
    
    @staticmethod
    def _has_real_openai_config():
        """Vérifie si les clés OpenAI sont configurées pour les tests réels"""
        try:
            from app.core.config import get_settings
            settings = get_settings()
            return (settings.openai_api_key and 
                    settings.asst_halakha and 
                    len(settings.openai_api_key) > 20)
        except:
            return False
    

def test_real_process_halakha_direct():
    """Test DIRECT avec appel réel à l'API OpenAI - queries_halakha"""
    print("🔥 Test avec VRAIE API OpenAI (sera facturé) 🔥")

    # Charger une halakha depuis le fichier JSON
    halakhot_path = os.path.join(os.path.dirname(__file__), '../../../app/data/halakhot.json')
    with open(halakhot_path, encoding='utf-8') as f:
        halakhot = json.load(f)
    # On prend la première halakha pour l'exemple
    test_content = halakhot[0]["halakha"]

    print("📝 Contenu envoyé à OpenAI:")
    print(test_content)
    print("\n⏳ Appel en cours...")

    try:
        # VRAI appel à l'API OpenAI
        from app.core.config import get_settings
        settings = get_settings()
        service = OpenAIService(settings)

        result = service.queries_halakha(test_content)

        # Afficher les résultats
        print("\n✅ RÉPONSE REÇUE:")
        print("=" * 50)
        print(f"Question: {result['question']}")
        print(f"Réponse: {result['answer']}")
        if "sources" in result:
            print(f"Sources: {result['sources']}")
        print("=" * 50)
        
        # Vérifications simples
        assert isinstance(result, dict), "Erreur: La réponse n'est pas un dictionnaire"
        assert "question" in result, "Erreur: Pas de question dans la réponse"
        assert "answer" in result, "Erreur: Pas de réponse dans la réponse"
        
        print("✅ Test réussi - La fonction queries_halakha fonctionne correctement!")
        return result
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        raise


# Pour exécuter directement comme un script
if __name__ == "__main__":
    test_real_process_halakha_direct()