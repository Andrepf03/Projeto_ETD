"""Transform: integracao entre fontes (cruzamento dataset <-> MusicBrainz).

Liga cada faixa a origem do artista (pais/area) por `artist_key` — a MESMA chave
normalizada criada no clean. Regista `match_method` por linha. Resiliente: se o
ficheiro da MusicBrainz nao existir, country/area ficam nulos e o pipeline continua.

Saida: data/staging/silver/tracks_matched.parquet
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from src.common.config import get_config
from src.common.logging_setup import get_logger
from src.transform.clean import ARTIST_KEY_SQL

log = get_logger("transform.match")


def run() -> Path:
    cfg = get_config()
    staging = Path(cfg["paths"]["staging"])
    silver = staging / "silver"
    tracks = silver / "tracks.parquet"
    mb_path = Path(cfg["paths"]["raw"]) / "musicbrainz" / "artists.jsonl"
    out = silver / "tracks_matched.parquet"

    con = duckdb.connect()
    if mb_path.exists() and mb_path.stat().st_size > 0:
        con.execute(
            f"""
            CREATE VIEW mb AS
            SELECT {ARTIST_KEY_SQL} AS artist_key,
                   any_value(country) AS country,
                   any_value(mb_artist_mbid) AS mb_artist_mbid,
                   any_value(area) AS area
            FROM read_json_auto('{mb_path.as_posix()}')
            WHERE artist_name IS NOT NULL
            GROUP BY 1
            """
        )
    else:
        con.execute(
            "CREATE VIEW mb AS SELECT NULL::VARCHAR AS artist_key, NULL::VARCHAR AS country, "
            "NULL::VARCHAR AS mb_artist_mbid, NULL::VARCHAR AS area WHERE 1=0"
        )
        log.warning("MusicBrainz ausente (%s); country/area ficam nulos.", mb_path)

    con.execute(
        f"""
        COPY (
          SELECT t.*, mb.country, mb.mb_artist_mbid, mb.area,
                 CASE WHEN mb.country IS NOT NULL OR mb.area IS NOT NULL
                      THEN 'mb_artist_key' ELSE 'no_match' END AS match_method
          FROM read_parquet('{tracks.as_posix()}') t
          LEFT JOIN mb USING (artist_key)
        ) TO '{out.as_posix()}' (FORMAT PARQUET, OVERWRITE_OR_IGNORE);
        """
    )
    total, matched = con.execute(
        f"""SELECT COUNT(*), COUNT(*) FILTER (WHERE match_method = 'mb_artist_key')
            FROM read_parquet('{out.as_posix()}')"""
    ).fetchone()
    con.close()
    pct = (matched / total * 100) if total else 0.0
    log.info("Matched: %s/%s faixas com origem (%.1f%%) -> %s", f"{matched:,}", f"{total:,}", pct, out)
    return out


if __name__ == "__main__":
    run()
