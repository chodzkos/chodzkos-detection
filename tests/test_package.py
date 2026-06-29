"""Test publicznego API pakietu (re-eksport z __init__)."""

from __future__ import annotations

import chodzkos_detection


def test_public_api_is_exported() -> None:
    expected = {
        "probe_tool",
        "check_tesseract",
        "check_poppler",
        "check_pandoc",
        "check_tools",
        "probe_http_service",
        "check_ollama",
    }
    assert expected <= set(chodzkos_detection.__all__)
    for name in expected:
        assert callable(getattr(chodzkos_detection, name))


def test_version_is_string() -> None:
    assert isinstance(chodzkos_detection.__version__, str)
    assert chodzkos_detection.__version__
