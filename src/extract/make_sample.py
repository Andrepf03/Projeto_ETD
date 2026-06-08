"""Cria uma amostra do dataset real (primeiras N linhas) para data/samples/.

Uso: python -m src.extract.make_sample [N]
Util para evaluadores correrem o pipeline sem o ficheiro completo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

from src.common.config import get_config
from src.common.logging_setup import get_logger

log = get_logger("extract.make_sample")


def run(n: int = 1000) -> Path:
    cfg = get_config()
    src = cfg["datasets"]["primary"]["path"]
    out = Path(cfg["paths"]["samples"]) / "spotify_sample.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(
        f"COPY (SELECT * FROM read_csv_auto('{src}', header=true) LIMIT {n}) "
        f"TO '{out.as_posix()}' (FORMAT CSV, HEADER);"
    )
    con.close()
    log.info("Amostra de %d linhas escrita em %s", n, out)
    return out


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 1000)
