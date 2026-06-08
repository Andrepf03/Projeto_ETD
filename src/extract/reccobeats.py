"""Enriquecimento via ReccoBeats: audio features para uma AMOSTRA de track ids do
Spotify, para validar/cruzar com as features historicas do dataset (cross-check de
qualidade). Passo OPCIONAL e resiliente.

NOTA: confirma os paths exatos na doc da ReccoBeats (https://reccobeats.com/docs).
O fluxo abaixo assume: 1) GET /track?ids=<spotify_ids> devolve recursos ReccoBeats
com `id`; 2) GET /track/<id>/audio-features devolve as features.
Saida: data/raw/reccobeats/audio_features.jsonl
"""

from __future__ import annotations

import json
from pathlib import Path

from src.common.config import get_config, get_settings
from src.common.http import build_client, get_json
from src.common.logging_setup import get_logger

log = get_logger("extract.reccobeats")

_BATCH = 40  # ReccoBeats aceita varios ids por pedido no multi-get


def _chunks(seq: list[str], size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def fetch_features_for_spotify_ids(spotify_ids: list[str]) -> list[dict]:
    base = get_settings().reccobeats_base_url.rstrip("/")
    client = build_client(headers={"Accept": "application/json"})
    out: list[dict] = []
    try:
        for batch in _chunks(spotify_ids, _BATCH):
            data = get_json(client, f"{base}/track", params={"ids": ",".join(batch)})
            tracks = data.get("content", data) if isinstance(data, dict) else data
            for t in tracks or []:
                recco_id = t.get("id")
                if not recco_id:
                    continue
                feats = get_json(client, f"{base}/track/{recco_id}/audio-features")
                if isinstance(feats, dict):
                    feats["reccobeats_id"] = recco_id
                    feats["spotify_href"] = t.get("href")
                    out.append(feats)
    except Exception as exc:  # resiliente
        log.warning("ReccoBeats interrompido (%d obtidos): %s", len(out), exc)
    finally:
        client.close()
    return out


def run(spotify_ids: list[str]) -> Path:
    out = Path(get_config()["paths"]["raw"]) / "reccobeats"
    out.mkdir(parents=True, exist_ok=True)
    feats = fetch_features_for_spotify_ids(spotify_ids)
    path = out / "audio_features.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for r in feats:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    log.info("ReccoBeats: %d faixas guardadas em %s", len(feats), path)
    return path
