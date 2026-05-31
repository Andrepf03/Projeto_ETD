"""Logging estruturado simples e consistente para todo o pipeline."""

from __future__ import annotations

import logging

from src.common.config import get_settings

_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    global _CONFIGURED
    if not _CONFIGURED:
        logging.basicConfig(
            level=get_settings().log_level.upper(),
            format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        _CONFIGURED = True
    return logging.getLogger(name)
