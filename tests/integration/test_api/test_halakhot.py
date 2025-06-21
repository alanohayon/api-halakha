import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_halakha(client: AsyncClient):
    halakha_data = {
        "question": "Test question",
        "content": "Test content"
    }
    response = await client.post("/api/v1/halakhot/", json=halakha_data)
    assert response.status_code == 201
    data = response.json()
    assert data["question"] == halakha_data["question"]
    assert data["content"] == halakha_data["content"]
    assert "id" in data

@pytest.mark.asyncio
async def test_get_halakha(client: AsyncClient):
    # Créer d'abord une halakha
    halakha_data = {
        "question": "Test question",
        "content": "Test content"
    }
    create_response = await client.post("/api/v1/halakhot/", json=halakha_data)
    halakha_id = create_response.json()["id"]
    
    # La récupérer
    response = await client.get(f"/api/v1/halakhot/{halakha_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == halakha_id