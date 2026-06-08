"""Enriquecimento via MusicBrainz: pais/origem do artista a partir do nome.

Usa musicbrainzngs, que define o User-Agent obrigatorio e respeita ~1 pedido/segundo.
Passo OPCIONAL e resiliente: se falhar (rede, etc.) nao quebra o pipeline.
Saida: data/raw/musicbrainz/artists.jsonl
"""

from __future__ import annotations

import json
from pathlib import Path

import musicbrainzngs

from src.common.config import get_config, get_settings
from src.common.logging_setup import get_logger

log = get_logger("extract.musicbrainz")


def _setup() -> None:
    s = get_settings()
    musicbrainzngs.set_useragent(
        s.musicbrainz_app_name, s.musicbrainz_app_version, s.musicbrainz_contact
    )


def fetch_artist_country(artist_name: str) -> dict | None:
    try:
        res = musicbrainzngs.search_artists(artist=artist_name, limit=1)
        artists = res.get("artist-list", [])
        if not artists:
            return None
        a = artists[0]
        return {
            "artist_name": artist_name,
            "mb_artist_mbid": a.get("id"),
            "mb_name": a.get("name"),
            "country": a.get("country"),
            "area": (a.get("area") or {}).get("name"),
            "begin_area": (a.get("begin-area") or {}).get("name"),
            "type": a.get("type"),
        }
    except Exception as exc:  # resiliente
        log.warning("MusicBrainz falhou para '%s': %s", artist_name, exc)
        return None


def run(artist_names: list[str]) -> Path:
    _setup()
    out = Path(get_config()["paths"]["raw"]) / "musicbrainz"
    out.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    for i, name in enumerate(artist_names, 1):
        rec = fetch_artist_country(name)
        if rec:
            results.append(rec)
        if i % 25 == 0:
            log.info("MusicBrainz: %d/%d artistas processados", i, len(artist_names))
    path = out / "artists.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    log.info("MusicBrainz: %d artistas com dados guardados em %s", len(results), path)
    return path
