import pytest
import json
import time
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from openai import OpenAI, OpenAIError, APITimeoutError, RateLimitError, APIConnectionError

# Ajouter le chemin racine du projet pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

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

    

# ... existing code ...


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
    """Test DIRECT avec appel réel à l'API OpenAI - process_halakha"""
    print("🔥 Test avec VRAIE API OpenAI (sera facturé) 🔥")
    
    # Importer et créer le service avec les vraies settings
    from app.core.config import get_settings
    
    # Créer le service réel (sans mocks)
    settings = get_settings()
    service = OpenAIService(settings)
    
    # Contenu de test
    test_content = """
Peut on shabbat secouer un habit de sa rosée/poussiere si il n'est pas noir et neuf mais qu'on est dérangé de le porter ainsi ?

•⁠  ⁠Le Talmud shabbat 146b,147a enseigne qu'il est interdit de secouer un habit (rosée d'après le Choulhan Aroukh et meme poussiere d'après le Rama),  seulement si l'habit est noir seulement si il est neuf et si on est soucieux (=on est soucieux de ne pas porter l'habit si ce n'est apres avoir retirer la rosée/poussiere).

•⁠  ⁠Mais est ce que les paramètres "noir", "neuf" sont des causes de l'interdit ou des signes révélateurs qu'on est "soucieux"?
En d'autres termes, si l'habit est noir/vieux ou rouge/neuf et que je suis soucieux de ne pas le porter ainsi, est ce interdit de le secouer?

=> Le Beour halakha עליה prouve du Rabbenou hananel que le critère essentiel est d'etre soucieux (suffit a lui seul pour interdire) et les autres signes ne sont que des revelateurs par défaut.
=> Selon d'autres ( Ben ich hay, Graz), les critères sont des causes et ainsi meme si l'on est soucieux, des lors que l'habit n'est pas noir ou noir mais vieux, ce sera permis de secouer. 

•⁠  ⁠En pratique, il conviendra d'être rigoureux des qu'on est soucieux, a priori car il s'agit d'un doute d'ordre toraique.    """
    
    print("📝 Contenu envoyé à OpenAI:")
    # print(test_content)
    print("\n⏳ Appel en cours...")
    
    try:
        # VRAI appel à l'API OpenAI
        result = service.process_halakha(test_content)
        
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
        
        print("✅ Test réussi - La fonction process_halakha fonctionne correctement!")
        return result
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        raise


# Pour exécuter directement comme un script
if __name__ == "__main__":
    test_real_process_halakha_direct()