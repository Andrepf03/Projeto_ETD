"""Teste minimo para manter a CI verde no scaffold."""

import src


def test_version() -> None:
    assert src.__version__ == "0.1.0"


def test_run_module_imports() -> None:
    import src.run  # noqa: F401
