"""Qualidade: relatorio curto sobre o silver (verificacoes SQL + Pydantic).

Escreve docs/quality_report.md com contagens, nulos, violacoes de dominio e cobertura
de integracao. Faz tambem uma verificacao-gate basica.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb

from src.common.config import get_config
from src.common.logging_setup import get_logger
from src.quality.rules import validate_sample

log = get_logger("quality.report")


def run() -> Path:
    cfg = get_config()
    matched = Path(cfg["paths"]["staging"]) / "silver" / "tracks_matched.parquet"
    glob = matched.as_posix()
    out = Path("docs") / "quality_report.md"

    con = duckdb.connect()
    total = con.execute(f"SELECT COUNT(*) FROM read_parquet('{glob}')").fetchone()[0]
    dup = con.execute(
        f"SELECT COUNT(*) - COUNT(DISTINCT track_id) FROM read_parquet('{glob}')"
    ).fetchone()[0]
    n_tid, n_pop, n_genre, n_year = con.execute(
        f"""SELECT
              SUM(CASE WHEN track_id IS NULL THEN 1 ELSE 0 END),
              SUM(CASE WHEN popularity IS NULL THEN 1 ELSE 0 END),
              SUM(CASE WHEN genre IS NULL THEN 1 ELSE 0 END),
              SUM(CASE WHEN year IS NULL THEN 1 ELSE 0 END)
            FROM read_parquet('{glob}')"""
    ).fetchone()
    bad_pop = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{glob}') WHERE popularity < 0 OR popularity > 100"
    ).fetchone()[0]
    bad_feat = con.execute(
        f"""SELECT COUNT(*) FROM read_parquet('{glob}')
            WHERE danceability < 0 OR danceability > 1 OR energy < 0 OR energy > 1
               OR valence < 0 OR valence > 1 OR acousticness < 0 OR acousticness > 1"""
    ).fetchone()[0]
    country_cov = con.execute(
        f"SELECT COUNT(*) FILTER (WHERE country IS NOT NULL) FROM read_parquet('{glob}')"
    ).fetchone()[0]
    n_genres = con.execute(
        f"SELECT COUNT(DISTINCT genre) FROM read_parquet('{glob}')"
    ).fetchone()[0]
    y_min, y_max = con.execute(
        f"SELECT MIN(year), MAX(year) FROM read_parquet('{glob}')"
    ).fetchone()
    con.close()

    errors = validate_sample(matched)
    cov_pct = (country_cov / total * 100) if total else 0.0

    # Gate basico: track_id nunca pode ser nulo nem duplicado no silver.
    if n_tid and n_tid > 0:
        raise ValueError(f"GATE FALHOU: {n_tid} track_id nulos no silver.")
    if dup and dup > 0:
        raise ValueError(f"GATE FALHOU: {dup} track_id duplicados no silver.")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        f"""# Relatorio de Qualidade de Dados (Semana 2)

Gerado automaticamente em {date.today().isoformat()} sobre `{glob}`.

## Visao geral
- Linhas (silver): {total:,}
- Anos: {y_min} a {y_max}
- Generos distintos: {n_genres}
- Duplicados por track_id (apos dedupe): {dup}

## Valores em falta (nulos)
- track_id: {n_tid}
- popularity: {n_pop}
- genre: {n_genre}
- year: {n_year}

## Violacoes de dominio
- popularity fora de [0,100]: {bad_pop}
- audio features fora de [0,1]: {bad_feat}

## Cobertura de integracao (cruzamento)
- Faixas com pais de origem (MusicBrainz): {country_cov:,} ({cov_pct:.1f}%)
  - NOTA: a cobertura e limitada pela amostra de artistas enriquecidos; subir
    `musicbrainz_sample_artists` no config melhora a cobertura (a 1 req/s).

## Validacao de schema (Pydantic, amostra)
- Linhas invalidas na amostra: {errors}

## Decisoes tomadas
- Coluna de indice do CSV removida no clean.
- Deduplicacao por `track_id` (mantida a faixa de maior popularity).
- `artist_key` normalizado (minusculas, sem acentos, so alfanumerico) para a juncao.
- Gate: aborta se houver track_id nulos ou duplicados no silver.
""",
        encoding="utf-8",
    )
    log.info("Relatorio de qualidade escrito em %s", out)
    return out


if __name__ == "__main__":
    run()
