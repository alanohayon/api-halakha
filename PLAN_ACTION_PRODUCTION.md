# 🚀 PLAN D'ACTION - DÉPLOIEMENT PRODUCTION
## Roadmap technique pour Railway

---

## 📋 PHASE 1 : CORRECTIONS CRITIQUES (1-2 jours)

### 🔴 1.1 SÉCURITÉ - PRIORITÉ MAXIMALE

#### 1.1.1 Corriger CORS (30 min)
**Fichier :** `app/main.py`
```python
# ❌ Actuel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DANGEREUX
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Correction
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,  # Depuis config
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)
```

#### 1.1.2 Gérer les secrets (45 min)
**Fichier :** `app/core/config.py`
```python
# ❌ Actuel
secret_key: str = Field(
    default="your-secret-key-change-in-production",  # DANGEREUX
    description="Clé secrète pour les tokens JWT",
    min_length=32
)

# ✅ Correction
secret_key: str = Field(
    ...,  # Obligatoire
    description="Clé secrète pour les tokens JWT",
    min_length=32
)
```

**Action :** Créer `.env.example` avec toutes les variables requises

#### 1.1.3 Ajouter authentification basique (2h)
**Nouveau fichier :** `app/core/auth.py`
```python
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    settings = get_settings()
    if credentials.credentials != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials
```

### 🔴 1.2 DOCKERFILE - OPTIMISATION (1h)

#### 1.2.1 Multi-stage build
**Fichier :** `Dockerfile`
```dockerfile
# ✅ Nouveau Dockerfile optimisé
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim as runtime

# Créer un utilisateur non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copier les dépendances depuis builder
COPY --from=builder /root/.local /home/appuser/.local
COPY . .

# Changer de propriétaire
RUN chown -R appuser:appuser /app
USER appuser

# Variables d'environnement
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 🔴 1.3 HEALTH CHECKS (30 min)

#### 1.3.1 Endpoint de santé
**Fichier :** `app/api/v1/endpoints/health.py`
```python
from fastapi import APIRouter, Depends
from app.core.database import get_supabase
from app.core.config import get_settings

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check pour Railway et monitoring"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health/detailed")
async def detailed_health_check(supabase=Depends(get_supabase)):
    """Health check détaillé avec dépendances"""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Test Supabase
    try:
        supabase.table('halakhot').select('id').limit(1).execute()
        health_status["services"]["supabase"] = "healthy"
    except Exception as e:
        health_status["services"]["supabase"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status
```

---

## 📋 PHASE 2 : AMÉLIORATIONS IMPORTANTES (2-3 jours)

### 🟡 2.1 TESTS - AUGMENTER LA COUVERTURE (1 jour)

#### 2.1.1 Tests unitaires manquants
**Nouveau fichier :** `tests/unit/test_services/test_processing_service.py`
```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.processing_service import ProcessingService

@pytest.fixture
def processing_service():
    return ProcessingService()

@pytest.mark.asyncio
async def test_post_halakha_complete_success(processing_service):
    with patch.object(processing_service, '_process_with_ai') as mock_ai, \
         patch.object(processing_service, '_publish_to_notion_platform') as mock_notion:
        
        mock_ai.return_value = {"title": "Test", "answer": "Test answer"}
        mock_notion.return_value = "https://notion.so/test"
        
        result = await processing_service.post_halakha_complete("Test content")
        
        assert result == "https://notion.so/test"
        mock_ai.assert_called_once()
        mock_notion.assert_called_once()
```

#### 2.1.2 Tests d'intégration améliorés
**Fichier :** `tests/integration/test_api/test_processing_routes.py`
```python
@pytest.mark.asyncio
async def test_process_halakha_to_notion_success(client):
    """Test complet du workflow de traitement"""
    response = await client.post(
        "/api/v1/processing/halakhot/post",
        data={
            "content": "Test halakha content",
            "schedule_days": 0,
            "last_img": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "notion_page_url" in data
    assert data["notion_page_url"].startswith("https://")
```

#### 2.1.3 Configuration pytest
**Fichier :** `pytest.ini`
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70
    -v
```

### 🟡 2.2 CACHE REDIS (2h)

#### 2.2.1 Service de cache
**Nouveau fichier :** `app/services/cache_service.py`
```python
import redis.asyncio as redis
from app.core.config import get_settings
from typing import Optional, Any
import json

class CacheService:
    def __init__(self):
        settings = get_settings()
        if settings.redis_url:
            self.redis = redis.from_url(settings.redis_url)
        else:
            self.redis = None
    
    async def get(self, key: str) -> Optional[Any]:
        if not self.redis:
            return None
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        if not self.redis:
            return
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
        except Exception:
            pass
```

#### 2.2.2 Intégration dans les services
**Fichier :** `app/services/supabase_service.py`
```python
from app.services.cache_service import CacheService

class SupabaseService:
    def __init__(self):
        # ... existing code ...
        self.cache = CacheService()
    
    async def get_halakha_by_id(self, halakha_id: int) -> Optional[Dict]:
        # Vérifier le cache d'abord
        cached = await self.cache.get(f"halakha:{halakha_id}")
        if cached:
            return cached
        
        # ... existing database code ...
        
        # Mettre en cache le résultat
        if result:
            await self.cache.set(f"halakha:{halakha_id}", result, ttl=1800)
        
        return result
```

### 🟡 2.3 OPTIMISATION DES TIMEOUTS (1h)

#### 2.3.1 Configuration des timeouts
**Fichier :** `app/core/config.py`
```python
# Timeouts optimisés pour la production
openai_timeout: int = Field(
    default=300,  # 5 minutes au lieu de 1h
    ge=60,
    le=600,
    description="Timeout OpenAI en secondes"
)

notion_timeout: int = Field(
    default=60,  # 1 minute
    ge=30,
    le=120,
    description="Timeout Notion en secondes"
)

supabase_timeout: int = Field(
    default=30,  # 30 secondes
    ge=10,
    le=60,
    description="Timeout Supabase en secondes"
)
```

---

## 📋 PHASE 3 : AMÉLIORATIONS POST-DÉPLOIEMENT (1-2 semaines)

### 🟢 3.1 REFACTORING ET NETTOYAGE (3 jours)

#### 3.1.1 Supprimer le code mort
```bash
# Script de nettoyage
find app -name "*.py" -exec grep -l "# TODO\|# FIXME\|# XXX" {} \;
find app -name "*.py" -exec grep -l "print(" {} \;
```

#### 3.1.2 Supprimer le dossier bacSable
```bash
rm -rf bacSable/
```

#### 3.1.3 Déplacer les données
```bash
mkdir -p data/external
mv app/data/*.json data/external/
```

### 🟢 3.2 MONITORING ET OBSERVABILITÉ (2 jours)

#### 3.2.1 Métriques Prometheus
**Nouveau fichier :** `app/core/metrics.py`
```python
from prometheus_client import Counter, Histogram, Gauge
import time

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active database connections')
```

#### 3.2.2 Middleware de métriques
**Fichier :** `app/main.py`
```python
from app.core.metrics import REQUEST_COUNT, REQUEST_DURATION

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(duration)
    return response
```

### 🟢 3.3 CI/CD PIPELINE (1 jour)

#### 3.3.1 GitHub Actions
**Fichier :** `.github/workflows/ci.yml`
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: |
          # Configuration Railway
          echo "Deploying to Railway..."
```

---

## 🛠️ OUTILS RECOMMANDÉS

### Développement
- **Code formatting** : `black`, `isort`
- **Linting** : `ruff`, `mypy`
- **Testing** : `pytest`, `pytest-cov`, `pytest-asyncio`
- **Security** : `bandit`, `safety`

### Production
- **Monitoring** : Prometheus + Grafana
- **Logging** : ELK Stack ou Datadog
- **Error tracking** : Sentry
- **Performance** : APM (New Relic, DataDog)

### Déploiement
- **Container** : Docker multi-stage
- **Orchestration** : Railway (actuel)
- **Secrets** : Railway Variables
- **Database** : Supabase (actuel)

---

## 📊 TIMELINE ESTIMÉE

| Phase | Durée | Priorité | Bloquant |
|-------|-------|----------|----------|
| Phase 1 | 1-2 jours | 🔴 Critique | Oui |
| Phase 2 | 2-3 jours | 🟡 Important | Non |
| Phase 3 | 1-2 semaines | 🟢 Amélioration | Non |

**Total estimé : 1-2 semaines pour un déploiement production-ready**

---

## ✅ CHECKLIST DE DÉPLOIEMENT

### Avant Railway
- [x] CORS sécurisé
- [x] Secrets gérés
- [ ] Dockerfile optimisé
- [ ] Health checks ajoutés
- [ ] Tests > 50% de couverture
- [ ] Variables d'environnement documentées

### Après Railway
- [ ] Monitoring configuré
- [ ] Logs centralisés
- [ ] Alertes configurées
- [ ] Backup strategy
- [ ] Documentation API complète

---

## 🚨 POINTS D'ATTENTION

1. **Ne jamais commiter de secrets** dans le code
2. **Tester en local** avec les mêmes variables que Railway
3. **Monitorer les performances** après déploiement
4. **Prévoir un rollback** en cas de problème
5. **Documenter les changements** pour l'équipe

---

*Ce plan d'action est priorisé pour un déploiement rapide et sécurisé sur Railway. Suivez l'ordre des phases pour une mise en production progressive et maîtrisée.*