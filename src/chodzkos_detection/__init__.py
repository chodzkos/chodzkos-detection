"""chodzkos-detection — uniwersalne, stdlib-only sondy narzędzi CLI i usług HTTP.

Publiczne API składa się z dwóch warstw:
- :mod:`chodzkos_detection.tools` — sondy narzędzi CLI (probe_tool + tesseract/poppler/pandoc),
- :mod:`chodzkos_detection.services` — sondy usług HTTP (probe_http_service + check_ollama).

Pakiet jest czysto stdlib — bez Qt i bez torcha. Detekcja GPU/sprzętu NIE jest tu częścią
(każda aplikacja trzyma własną warstwę torchową).
"""

from __future__ import annotations

from chodzkos_detection.services import check_ollama, probe_http_service
from chodzkos_detection.tools import (
    check_pandoc,
    check_poppler,
    check_tesseract,
    check_tools,
    find_tool,
    probe_tool,
)

__version__ = "0.1.2"

__all__ = [
    "__version__",
    "check_ollama",
    "check_pandoc",
    "check_poppler",
    "check_tesseract",
    "check_tools",
    "find_tool",
    "probe_http_service",
    "probe_tool",
]
