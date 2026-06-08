"""CLI do pipeline ETL.

Semanas 1 (Extract), 2 (Transform) e 3 (Load) implementadas.

Uso:
    python -m src.run extract
    python -m src.run transform
    python -m src.run load
    python -m src.run all
"""

from __future__ import annotations

import argparse
import sys

from src.common.config import get_config
from src.common.logging_setup import get_logger

log = get_logger("run")


def cmd_extract() -> None:
    import duckdb

    from src.extract import ingest_dataset

    staging = ingest_dataset.run()
    cfg = get_config()
    glob = f"{staging.as_posix()}/**/*.parquet"

    if cfg.get("sources", {}).get("musicbrainz", {}).get("enabled", False):
        try:
            n = int(cfg["enrichment"].get("musicbrainz_sample_artists", 200))
            con = duckdb.connect()
            artists = [
                r[0]
                for r in con.execute(
                    f"SELECT DISTINCT artist_name FROM read_parquet('{glob}') "
                    f"WHERE artist_name IS NOT NULL LIMIT {n}"
                ).fetchall()
            ]
            con.close()
            from src.extract import musicbrainz

            musicbrainz.run(artists)
        except Exception as exc:
            log.warning("Enriquecimento MusicBrainz ignorado: %s", exc)

    if cfg.get("sources", {}).get("reccobeats", {}).get("enabled", False):
        try:
            n = int(cfg["enrichment"].get("reccobeats_sample_size", 500))
            con = duckdb.connect()
            ids = [
                r[0]
                for r in con.execute(
                    f"SELECT track_id FROM read_parquet('{glob}') "
                    f"WHERE track_id IS NOT NULL LIMIT {n}"
                ).fetchall()
            ]
            con.close()
            from src.extract import reccobeats

            reccobeats.run(ids)
        except Exception as exc:
            log.warning("Enriquecimento ReccoBeats ignorado: %s", exc)

    log.info("Extract concluido.")


def cmd_transform() -> None:
    from src.quality import report
    from src.transform import clean, match

    clean.run()
    match.run()
    report.run()
    log.info("Transform concluido.")


def cmd_load() -> None:
    from src.load import build_warehouse, validate

    build_warehouse.run()
    validate.run()
    log.info("Load concluido.")


def cmd_all() -> None:
    cmd_extract()
    cmd_transform()
    cmd_load()


COMMANDS = {
    "extract": cmd_extract,
    "transform": cmd_transform,
    "load": cmd_load,
    "all": cmd_all,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pipeline ETL — Musica & Entretenimento")
    parser.add_argument("stage", choices=COMMANDS.keys(), help="Fase do pipeline a executar")
    args = parser.parse_args(argv)
    COMMANDS[args.stage]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
