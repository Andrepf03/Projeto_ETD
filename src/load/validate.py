"""Load: validacao pos-carga do star schema (integridade referencial + gate).

Escreve docs/load_validation.md e aborta se houver chaves orfas ou duplicadas.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb

from src.common.config import get_config
from src.common.logging_setup import get_logger

log = get_logger("load.validate")

_TABLES = ["dim_artist", "dim_genre", "dim_time", "dim_region", "fact_track", "fact_track_popularity"]


def run() -> Path:
    cfg = get_config()
    db_path = Path(cfg["paths"]["duckdb"])
    out = Path("docs") / "load_validation.md"

    con = duckdb.connect(str(db_path))
    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in _TABLES}
    dup_pk = con.execute(
        "SELECT COUNT(*) - COUNT(DISTINCT track_sk) FROM fact_track"
    ).fetchone()[0]
    orphan_artist = con.execute(
        "SELECT COUNT(*) FROM fact_track f LEFT JOIN dim_artist d USING (artist_sk) "
        "WHERE f.artist_sk IS NOT NULL AND d.artist_sk IS NULL"
    ).fetchone()[0]
    orphan_genre = con.execute(
        "SELECT COUNT(*) FROM fact_track f LEFT JOIN dim_genre d USING (genre_sk) "
        "WHERE f.genre_sk IS NOT NULL AND d.genre_sk IS NULL"
    ).fetchone()[0]
    orphan_time = con.execute(
        "SELECT COUNT(*) FROM fact_track f LEFT JOIN dim_time d USING (time_sk) "
        "WHERE f.time_sk IS NOT NULL AND d.time_sk IS NULL"
    ).fetchone()[0]
    null_genre_sk = con.execute(
        "SELECT COUNT(*) FILTER (WHERE genre_sk IS NULL) FROM fact_track"
    ).fetchone()[0]
    con.close()

    problems = []
    if dup_pk:
        problems.append(f"{dup_pk} track_sk duplicados em fact_track")
    if orphan_artist:
        problems.append(f"{orphan_artist} FKs de artista orfas")
    if orphan_genre:
        problems.append(f"{orphan_genre} FKs de genero orfas")
    if orphan_time:
        problems.append(f"{orphan_time} FKs de tempo orfas")
    status = "OK" if not problems else "PROBLEMAS: " + "; ".join(problems)

    out.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"- {t}: {c:,}" for t, c in counts.items())
    out.write_text(
        f"""# Validacao Pos-Load (Semana 3)

Gerado em {date.today().isoformat()} sobre `{db_path.as_posix()}`.

## Contagens das tabelas
{body}

## Integridade referencial
- track_sk duplicados em fact_track: {dup_pk}
- FKs de artista orfas: {orphan_artist}
- FKs de genero orfas: {orphan_genre}
- FKs de tempo orfas: {orphan_time}
- fact_track sem genre_sk (genero nulo na origem): {null_genre_sk}

## Estado: {status}
""",
        encoding="utf-8",
    )
    log.info("Validacao pos-load: %s | relatorio em %s", status, out)
    if problems:
        raise ValueError("GATE pos-load falhou: " + status)
    return out


if __name__ == "__main__":
    run()
