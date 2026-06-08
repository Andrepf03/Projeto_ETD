"""Flow Prefect — orquestracao do pipeline.

Fase 0: esqueleto. Na Fase 1+ cada @task chama as mesmas funcoes de src/ usadas pelo
CLI (src/run.py), garantindo que o pipeline corre tanto via `make all` como via Prefect.
"""

from __future__ import annotations

# from prefect import flow, task
#
# @task(retries=3, retry_delay_seconds=10)
# def extract() -> None:
#     ...
#
# @flow(name="etl-musica")
# def etl_flow() -> None:
#     extract()
#     # transform(); load()
#
# if __name__ == "__main__":
#     etl_flow()
