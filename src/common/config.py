"""Carregamento de configuracao.

- Segredos / variaveis de ambiente via .env (pydantic-settings).
- Parametros nao-sensiveis via config/config.yaml.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


class Settings(BaseSettings):
    """Segredos e variaveis de ambiente (.env). Tudo com defaults seguros."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    # Spotify (OPCIONAL)
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    # ReccoBeats
    reccobeats_base_url: str = "https://api.reccobeats.com/v1"
    # MusicBrainz (o contacto e obrigatorio no User-Agent)
    musicbrainz_app_name: str = "ProjetoETD"
    musicbrainz_app_version: str = "0.1.0"
    musicbrainz_contact: str = "exemplo@exemplo.pt"
    # Last.fm (opcional)
    lastfm_api_key: str = ""
    # Execucao
    data_dir: str = "./data"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_config() -> dict[str, Any]:
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)
