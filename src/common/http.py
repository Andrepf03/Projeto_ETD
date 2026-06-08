"""Cliente HTTP com timeouts e retry/backoff exponencial (tenacity).

Faz retry em respostas 429 (rate limit) e 5xx (erros transitorios do servidor).
"""

from __future__ import annotations

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.common.config import get_config

_cfg = get_config().get("rate_limits", {})
MAX_RETRIES = int(_cfg.get("http_max_retries", 5))
BACKOFF = float(_cfg.get("http_backoff_seconds", 2))


class RetryableHTTPError(Exception):
    """Erro que justifica nova tentativa (429 ou 5xx)."""


def build_client(timeout: float = 20.0, headers: dict | None = None) -> httpx.Client:
    return httpx.Client(timeout=timeout, headers=headers or {})


@retry(
    retry=retry_if_exception_type(RetryableHTTPError),
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=BACKOFF, min=BACKOFF, max=60),
    reraise=True,
)
def get_json(client: httpx.Client, url: str, params: dict | None = None) -> dict | list:
    resp = client.get(url, params=params)
    if resp.status_code == 429 or resp.status_code >= 500:
        raise RetryableHTTPError(f"HTTP {resp.status_code} em {url}")
    resp.raise_for_status()
    return resp.json()
