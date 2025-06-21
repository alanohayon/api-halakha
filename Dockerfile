FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Installation de Poetry
RUN pip install poetry

# Copie des fichiers de configuration
COPY pyproject.toml poetry.lock ./

# Installation des dépendances Python
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copie du code source
COPY . .

# Exposition du port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]