"""Qualidade: contrato de schema com Pydantic.

`SilverTrack` define tipos e dominios esperados; `validate_sample` valida uma amostra
(as verificacoes sobre os dados todos sao feitas em SQL no report, que escala melhor).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import duckdb
from pydantic import BaseModel, field_validator

from src.common.logging_setup import get_logger

log = get_logger("quality.rules")


class SilverTrack(BaseModel):
    track_id: str
    artist_name: Optional[str] = None
    artist_key: Optional[str] = None
    popularity: Optional[int] = None
    year: Optional[int] = None
    decade: Optional[int] = None
    genre: Optional[str] = None
    danceability: Optional[float] = None
    energy: Optional[float] = None
    valence: Optional[float] = None
    acousticness: Optional[float] = None
    loudness: Optional[float] = None
    tempo: Optional[float] = None
    duration_ms: Optional[int] = None

    @field_validator("popularity")
    @classmethod
    def _pop_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("popularity fora de [0,100]")
        return v

    @field_validator("danceability", "energy", "valence", "acousticness")
    @classmethod
    def _unit_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("feature fora de [0,1]")
        return v


def validate_sample(path: Path, n: int = 500) -> int:
    con = duckdb.connect()
    res = con.execute(f"SELECT * FROM read_parquet('{path.as_posix()}') LIMIT {n}")
    cols = [d[0] for d in res.description]
    rows = [dict(zip(cols, r)) for r in res.fetchall()]
    con.close()

    errors = 0
    for r in rows:
        data = {k: r.get(k) for k in SilverTrack.model_fields}
        try:
            SilverTrack(**data)
        except Exception as exc:
            errors += 1
            if errors <= 5:
                log.warning("Validacao Pydantic falhou numa linha: %s", exc)
    log.info("Pydantic: %d/%d linhas validas na amostra", len(rows) - errors, len(rows))
    return errors
