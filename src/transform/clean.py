"""Transform: limpeza e normalizacao (bronze -> silver).

- Remove a coluna de indice (sem nome) do CSV original.
- Garante tipos (TRY_CAST) e remove duplicados por track_id (mantem a de maior popularity).
- Cria a chave de juncao normalizada do artista (artist_key) de forma CONSISTENTE
  com o matching (mesma expressao SQL exportada em ARTIST_KEY_SQL).

Saida: data/staging/silver/tracks.parquet
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from src.common.config import get_config
from src.common.logging_setup import get_logger

log = get_logger("transform.clean")

# Chave do artista, reutilizada no matching: minusculas, sem acentos, so alfanumerico.
ARTIST_KEY_SQL = (
    "trim(regexp_replace(regexp_replace("
    "lower(strip_accents(CAST(artist_name AS VARCHAR))), '[([].*?[)\\]]', ' ', 'g'), "
    "'[^a-z0-9]+', ' ', 'g'))"
)


def run() -> Path:
    cfg = get_config()
    staging = Path(cfg["paths"]["staging"])
    bronze = staging / "bronze" / "dataset"
    silver_dir = staging / "silver"
    silver_dir.mkdir(parents=True, exist_ok=True)
    out = silver_dir / "tracks.parquet"

    con = duckdb.connect()
    con.execute(
        f"""
        COPY (
          WITH src AS (
            SELECT
              CAST(track_id AS VARCHAR)        AS track_id,
              CAST(track_name AS VARCHAR)      AS track_name,
              CAST(artist_name AS VARCHAR)     AS artist_name,
              {ARTIST_KEY_SQL}                 AS artist_key,
              TRY_CAST(popularity AS INTEGER)  AS popularity,
              TRY_CAST(year AS INTEGER)        AS year,
              CAST(decade AS INTEGER)          AS decade,
              CAST(genre AS VARCHAR)           AS genre,
              TRY_CAST(danceability AS DOUBLE) AS danceability,
              TRY_CAST(energy AS DOUBLE)       AS energy,
              TRY_CAST(valence AS DOUBLE)      AS valence,
              TRY_CAST(acousticness AS DOUBLE) AS acousticness,
              TRY_CAST(loudness AS DOUBLE)     AS loudness,
              TRY_CAST(tempo AS DOUBLE)        AS tempo,
              TRY_CAST(duration_ms AS INTEGER) AS duration_ms,
              row_number() OVER (PARTITION BY track_id ORDER BY TRY_CAST(popularity AS INTEGER) DESC) AS rn
            FROM read_parquet('{bronze.as_posix()}/**/*.parquet')
            WHERE track_id IS NOT NULL
          )
          SELECT * EXCLUDE (rn) FROM src WHERE rn = 1
        ) TO '{out.as_posix()}' (FORMAT PARQUET, OVERWRITE_OR_IGNORE);
        """
    )
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out.as_posix()}')").fetchone()[0]
    con.close()
    log.info("Silver tracks: %s linhas (deduplicadas) -> %s", f"{n:,}", out)
    return out


if __name__ == "__main__":
    run()
