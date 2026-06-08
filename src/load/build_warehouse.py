"""Load: construcao do data warehouse analitico (star schema) em DuckDB.

Le data/staging/silver/tracks_matched.parquet e cria, em data/curated/curated.duckdb:
- dimensoes: dim_genre, dim_time, dim_region, dim_artist
- factos: fact_track (audio features), fact_track_popularity (popularidade)

Modelo: medallion (bronze/silver/gold) + star schema na camada gold (consultas do dashboard).
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from src.common.config import get_config
from src.common.logging_setup import get_logger

log = get_logger("load.warehouse")

_TABLES = ["dim_artist", "dim_genre", "dim_time", "dim_region", "fact_track", "fact_track_popularity"]


def run() -> Path:
    cfg = get_config()
    silver = Path(cfg["paths"]["staging"]) / "silver" / "tracks_matched.parquet"
    db_path = Path(cfg["paths"]["duckdb"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not silver.exists():
        raise FileNotFoundError(f"Silver nao encontrado: {silver}. Corre 'transform' primeiro.")

    con = duckdb.connect(str(db_path))
    con.execute(f"CREATE OR REPLACE VIEW silver AS SELECT * FROM read_parquet('{silver.as_posix()}')")

    con.execute(
        """
        CREATE OR REPLACE TABLE dim_genre AS
        SELECT row_number() OVER (ORDER BY genre) AS genre_sk, genre AS genre_name
        FROM (SELECT DISTINCT genre FROM silver WHERE genre IS NOT NULL)
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE dim_time AS
        SELECT row_number() OVER (ORDER BY year) AS time_sk, year, decade
        FROM (SELECT DISTINCT year, decade FROM silver WHERE year IS NOT NULL)
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE dim_region AS
        SELECT row_number() OVER (ORDER BY country_code, area_name) AS region_sk,
               country_code, area_name
        FROM (SELECT DISTINCT country AS country_code, area AS area_name FROM silver
              WHERE country IS NOT NULL OR area IS NOT NULL)
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE dim_artist AS
        SELECT row_number() OVER (ORDER BY a.artist_key) AS artist_sk,
               a.artist_key, a.artist_name, a.mb_artist_mbid, r.region_sk
        FROM (SELECT artist_key,
                     any_value(artist_name)   AS artist_name,
                     any_value(mb_artist_mbid) AS mb_artist_mbid,
                     any_value(country)        AS country,
                     any_value(area)           AS area
              FROM silver WHERE artist_key IS NOT NULL GROUP BY artist_key) a
        LEFT JOIN dim_region r
               ON r.country_code IS NOT DISTINCT FROM a.country
              AND r.area_name    IS NOT DISTINCT FROM a.area
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE fact_track AS
        SELECT s.track_id AS track_sk, s.track_id AS spotify_track_id, s.track_name AS title,
               da.artist_sk, dg.genre_sk, dt.time_sk,
               s.danceability, s.energy, s.valence, s.acousticness, s.loudness, s.tempo,
               s.duration_ms, s.match_method
        FROM silver s
        LEFT JOIN dim_artist da ON da.artist_key = s.artist_key
        LEFT JOIN dim_genre  dg ON dg.genre_name = s.genre
        LEFT JOIN dim_time   dt ON dt.year       = s.year
        """
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE fact_track_popularity AS
        SELECT track_id AS track_sk, popularity AS spotify_popularity,
               CAST(NULL AS INTEGER) AS lastfm_listeners,
               CAST(NULL AS INTEGER) AS lastfm_playcount,
               CURRENT_DATE          AS snapshot_date
        FROM silver
        """
    )

    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in _TABLES}
    con.close()
    log.info("Warehouse criado em %s | %s", db_path, counts)
    return db_path


if __name__ == "__main__":
    run()
