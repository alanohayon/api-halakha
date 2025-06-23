# api-halakha

``` bash
halakha-api/
├── README.md
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py                 # Point d'entrée FastAPI
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration centralisée
│   │   ├── database.py         # Connexion DB async
│   │   ├── logging.py          # Configuration logging
│   │   └── exceptions.py       # Exceptions personnalisées
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # Modèle de base SQLAlchemy
│   │   ├── halakha.py          # Modèle Halakha
│   │   └── processing_job.py   # Modèle Job de traitement
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── base.py             # Schémas Pydantic de base
│   │   ├── halakha.py          # Schémas Halakha
│   │   ├── openai.py           # Schémas OpenAI
│   │   └── notion.py           # Schémas Notion
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Dépendances communes
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # Router principal v1
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── halakhot.py # CRUD Halakhot
│   │           ├── processing.py # Endpoints de traitement
│   │           └── health.py   # Health check
│   ├── services/
│   │   ├── __init__.py
│   │   ├── halakha_service.py  # Logique métier Halakha
│   │   ├── openai_service.py   # Service OpenAI
│   │   ├── notion_service.py   # Service Notion│ 
├── │   ├── supabase_service.py   # Service Supabase
│   │   └── processing_service.py # Orchestration des services
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py             # Repository de base
│   │   └── halakha_repository.py # Repository Halakha
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── json_loader.py      # Chargement des données JSON
│   │   └── validators.py       # Validateurs personnalisés
│   └── data/
│       └── halakhot.json       # Données source
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_services/
│   │   └── test_repositories/
│   ├── integration/
│   │   └── test_api/
│   └── fixtures/
│       └── sample_data.json
└── scripts/
    ├── test_supabase_connection.py
    └── migrate_to_supabase.py
```

``` Mermaid
sources
-
id PK int
name string

questions
-
id PK int
question text

answers
-
id PK int
answer text

tags
-
id PK int
name string UNIQUE

themes
-
id PK int
name string UNIQUE

halakhot
-
id PK int
title string INDEX
content text
source_id int FK >- sources.id
question_id int FK >- questions.id
answer_id int FK >- answers.id

halakha_tags
----
halakha_id int PK FK >- halakhot.id
tag_id int PK FK >- tags.id

halakha_themes
----
halakha_id int PK FK >- halakhot.id
theme_id int PK FK >- themes.id
``` 


