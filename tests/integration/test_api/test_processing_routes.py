import pytest
from unittest.mock import patch, Mock


@pytest.mark.asyncio
class TestProcessingRoutes:
    """Tests d'intégration pour les routes de traitement de halakha"""

    async def test_analyze_halakha_route(self, client):
        """Test de la route d'analyse de halakha"""
        
        # Mock de la réponse OpenAI
        mock_response = {
            "question": "Peut-on faire du vélo le Shabbat ?",
            "answer": "Il est interdit de faire du vélo le Shabbat...",
            "sources": ["Shulchan Aroukh", "Mishna Brura"],
            "themes": ["Shabbat", "Mouktse"],
            "tags": ["vélo", "shabbat", "interdit"]
        }
        
        with patch('app.services.openai_service.OpenAIService.queries_halakha') as mock_process:
            mock_process.return_value = mock_response
            
            response = await client.post(
                "/api/v1/processing/halakha/analyze",
                json={"content": "Test halakha content"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["message"] == "Halakha analysée avec succès"
            assert data["question"] == mock_response["question"]
            assert data["answer"] == mock_response["answer"]
            assert data["sources"] == mock_response["sources"]

    async def test_complete_halakha_route(self, client):
        """Test de la route de traitement complet de halakha"""
        
        # Mock de la réponse process_halakha
        mock_halakha_response = {
            "question": "Peut-on faire du vélo le Shabbat ?",
            "answer": "Il est interdit de faire du vélo le Shabbat...",
            "sources": ["Shulchan Aroukh", "Mishna Brura"]
        }
        
        # Mock de la réponse queries_post_legende
        mock_text_post = "🚲 #Shabbat Question importante sur le vélo..."
        mock_legend = "Une belle réflexion sur les lois du Shabbat..."
        
        with patch('app.services.openai_service.OpenAIService.queries_halakha') as mock_process, \
             patch('app.services.openai_service.OpenAIService.queries_post_legende') as mock_post:
            
            mock_process.return_value = mock_halakha_response
            mock_post.return_value = (mock_text_post, mock_legend)
            
            response = await client.post(
                "/api/v1/processing/halakha/complete",
                json={"content": "Test halakha content"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["message"] == "Halakha traitée complètement avec succès"
            assert data["question"] == mock_halakha_response["question"]
            assert data["answer"] == mock_halakha_response["answer"]
            assert data["text_post"] == mock_text_post
            assert data["legend"] == mock_legend
            
            # Vérifier que les méthodes ont été appelées correctement
            mock_process.assert_called_once_with("Test halakha content")
            mock_post.assert_called_once_with(
                "Test halakha content", 
                mock_halakha_response["answer"]
            )

    async def test_analyze_halakha_route_error(self, client):
        """Test de la route d'analyse avec erreur"""
        
        with patch('app.services.openai_service.OpenAIService.queries_halakha') as mock_process:
            mock_process.side_effect = Exception("OpenAI API Error")
            
            response = await client.post(
                "/api/v1/processing/halakha/analyze",
                json={"content": "Test halakha content"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Erreur lors de l'analyse de la halakha" in data["detail"]

    async def test_complete_halakha_route_error(self, client):
        """Test de la route de traitement complet avec erreur"""
        
        with patch('app.services.openai_service.OpenAIService.queries_halakha') as mock_process:
            mock_process.side_effect = Exception("OpenAI API Error")
            
            response = await client.post(
                "/api/v1/processing/halakha/complete",
                json={"content": "Test halakha content"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Erreur lors du traitement complet de la halakha" in data["detail"]

    async def test_request_validation(self, client):
        """Test de validation des requêtes"""
        
        # Test avec contenu manquant
        response = await client.post(
            "/api/v1/processing/halakha/analyze",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test avec contenu vide
        response = await client.post(
            "/api/v1/processing/halakha/analyze",
            json={"content": ""}
        )
        
        assert response.status_code == 422  # Validation error 