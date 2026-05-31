"""Ingestao do dataset de grande volume: CSV -> Parquet particionado por decada.

Usa DuckDB, que le o CSV de forma streaming (sem carregar tudo em memoria) e escreve
Parquet particionado. Responde ao requisito de cuidados de engenharia para grande
volume: particionamento + processamento out-of-core num laptop.

Saida (camada bronze): data/staging/bronze/dataset/decade=YYYY/*.parquet
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from src.common.config import get_config
from src.common.logging_setup import get_logger

log = get_logger("extract.ingest")


def run(csv_path: str | None = None, out_dir: str | None = None) -> Path:
    cfg = get_config()
    primary = cfg["datasets"]["primary"]
    csv_path = csv_path or primary["path"]
    staging = Path(out_dir or cfg["paths"]["staging"]) / "bronze" / "dataset"
    staging.mkdir(parents=True, exist_ok=True)

    if not Path(csv_path).exists():
        raise FileNotFoundError(
            f"Dataset nao encontrado em '{csv_path}'. Descarrega-o do Kaggle "
            "(amitanshjoshi/spotify-1million-tracks) e coloca-o em data/raw/."
        )

    log.info("A ingerir %s -> %s (Parquet particionado por decada)", csv_path, staging)
    con = duckdb.connect()
    con.execute(
        f"""
        COPY (
            SELECT *,
                   CAST(FLOOR(TRY_CAST(year AS INTEGER) / 10) * 10 AS INTEGER) AS decade
            FROM read_csv_auto('{csv_path}', header=true, sample_size=-1)
        )
        TO '{staging.as_posix()}'
        (FORMAT PARQUET, PARTITION_BY (decade), OVERWRITE_OR_IGNORE);
        """
    )
    n = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{staging.as_posix()}/**/*.parquet')"
    ).fetchone()[0]
    con.close()
    log.info("Ingestao concluida: %s linhas.", f"{n:,}")
    return staging


if __name__ == "__main__":
    run()
