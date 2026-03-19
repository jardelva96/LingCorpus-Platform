"""Configurações centrais da aplicação."""

from __future__ import annotations

import secrets
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente ou .env."""

    app_name: str = "LingCorpus Platform"
    debug: bool = False

    # Banco de dados
    database_url: str = "sqlite:///./lingcorpus.db"

    # JWT
    secret_key: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # Upload
    upload_dir: Path = Path("uploads")
    max_upload_size_mb: int = 50

    # NLTK
    nltk_data_dir: Path = Path("nltk_data")

    model_config = {"env_prefix": "LINGCORPUS_", "env_file": ".env"}


settings = Settings()

# Garante que diretórios existam
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.nltk_data_dir.mkdir(parents=True, exist_ok=True)
