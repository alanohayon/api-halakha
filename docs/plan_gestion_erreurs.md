# Gestion Robuste des Erreurs

Mise en place d'un système homogène de gestion des exceptions afin de sécuriser l'API, de fournir des réponses HTTP claires et d'améliorer la maintenabilité.

## Tâches Complétées

- [x] Définition d'une base `CustomException` et d'exceptions spécialisées dans `app/core/exceptions.py`
- [x] Middleware/outil de logging centralisé existant dans `app/core/logging.py`

## Tâches en Cours

- [x] Cartographie uniforme des exceptions → réponses HTTP via des `exception_handlers` FastAPI
- [x] Gestion des erreurs fines dans les services externes
  - [x] NotionService : lever `NotionServiceError` au lieu de `RuntimeError`
  - [x] OpenAIService : lever `OpenAIServiceError` au lieu d'exceptions génériques
  - [x] SupabaseService : utiliser `map_supabase_error` et lever des exceptions custom
  - [x] Harmonisation de la structure des services et injection de dépendances
  - [x] Création des dépendances injectées dans `app/api/deps.py` (OpenAIServiceDep, NotionServiceDep, SupabaseServiceDep, ProcessingServiceDep)
  - [x] Refactorisation de `ProcessingService` pour accepter les services en paramètres optionnels
  - [x] Harmonisation de tous les endpoints SupabaseService (halakhot, sources, tags, themes)
  - [x] Remplacement des instanciations directes par des dépendances injectées

## Tâches Futures

- [ ] Refactorisation des endpoints pour lever uniquement des exceptions custom (pas de `HTTPException` brute)
- [ ] Mise en place de jeux de tests (unitaires et intégration) couvrant les erreurs typiques
- [ ] Documentation OpenAPI/Swagger détaillant les codes d'erreur et leurs significations

## Plan d'Implémentation

### Phase 1 : Gestion d'Erreurs (✅ Terminée)
1. **Audit des Exceptions Existantes** ✅
   - Recensement de toutes les `raise HTTPException`, `ValueError`, etc. dans le projet.
   - Association de chaque cas à une exception custom claire.
2. **Extension des Exceptions Custom** ✅
   - Ajout de classes (`NotionServiceError`, `OpenAIServiceError`, `DatabaseError`, `ValidationError`) héritant de `HalakhaAPIException` avec attributs `status_code`, `code`, `details`.
3. **Exception Handlers Globaux** ✅
   - Définition dans `app/main.py` d'un handler FastAPI pour `HalakhaAPIException` générant une réponse JSON standardisée.
4. **Refactorisation des Services** ✅
   - Remplacement des `raise RuntimeError`/`return None` par le lancement d'exceptions custom avec informations contextuelles.
   - Mapping des erreurs Supabase via `map_supabase_error`.

### Phase 2 : Harmonisation de l'Architecture (✅ Terminée)
5. **Système de Dépendances Injectées** ✅
   - Création des dépendances dans `app/api/deps.py` avec cache LRU :
     - `OpenAIServiceDep`
     - `NotionServiceDep` 
     - `SupabaseServiceDep`
     - `ProcessingServiceDep`
6. **Refactorisation de ProcessingService** ✅
   - Modification du constructeur pour accepter les services en paramètres optionnels
   - Fallback intelligent : `service or Service()`
7. **Harmonisation des Endpoints** ✅
   - Remplacement de `SupabaseService(supabase)` par `SupabaseServiceDep` dans tous les endpoints
   - Cohérence des signatures de méthodes

### Phase 3 : Optimisations Futures
8. **Mise à Jour des Endpoints** (À faire)
   - Retirer les blocs `try/except` inutiles, compter sur les handlers globaux.
9. **Tests et Observabilité** (À faire)
   - Créer des tests paramétrés pour vérifier le code HTTP et le payload d'erreur de chaque endpoint.
   - Ajouter des logs structurés (niveau `error`) dans les handlers.
10. **Documentation** (À faire)
    - Utiliser `responses` de FastAPI pour documenter chaque code d'erreur.

### Fichiers Pertinents

- `app/core/exceptions.py` – Définitions des exceptions custom
- `app/core/logging.py` – Configuration du logging
- `app/main.py` – Enregistrement des handlers globaux
- `app/api/v1/router.py` – Inclusion de routers / application du middleware
- `app/api/v1/endpoints/*/*.py` – Endpoints à refactoriser pour lever des exceptions custom
- `app/services/*_service.py` – Services externes où encapsuler les erreurs spécifiques
- `tests/` – Tests unitaires & intégration couvrant les scénarios d'erreur
