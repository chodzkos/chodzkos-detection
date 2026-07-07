"""Wykrywanie usług sieciowych (Ollama).

Wszystkie funkcje są odporne na brak usługi — zwracają pusty dict,
nie rzucają wyjątków.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

# Dozwolone schematy URL. urlopen samo w sobie akceptuje też file://, ftp:// itd.,
# co przy publicznym API jest wektorem SSRF / odczytu lokalnych plików — dopuszczamy
# wyłącznie ruch HTTP(S).
_ALLOWED_SCHEMES = frozenset({"http", "https"})

# Górny limit odczytu odpowiedzi (bajty). Chroni przed DoS pamięci przy ogromnej
# odpowiedzi — czytamy o 1 bajt więcej i odrzucamy, jeśli przekroczono limit.
MAX_BYTES = 1_000_000


def probe_http_service(url: str, timeout: int = 2) -> dict[str, Any]:
    """Generyczna sonda usługi HTTP zwracającej JSON.

    Args:
        url: adres endpointu zwracającego JSON (dozwolone schematy: http, https).
        timeout: limit czasu połączenia w sekundach.

    Returns:
        Słownik ``{"available": bool, "data": Any | None}``. Odporny na wyjątki —
        przy braku usługi/błędzie/niedozwolonym schemacie/zbyt dużej odpowiedzi
        zwraca ``available=False`` zamiast rzucać.
    """
    result: dict[str, Any] = {"available": False, "data": None}

    # Walidacja schematu przed jakimkolwiek połączeniem — file://, ftp:// itd. są
    # odrzucane bez otwierania zasobu (kontrakt: available=False, bez rzucania).
    if urllib.parse.urlparse(url).scheme not in _ALLOWED_SCHEMES:
        logger.debug("probe_http_service: odrzucono niedozwolony schemat URL: %r", url)
        return result

    try:
        # Schemat zwalidowany powyżej do http/https, więc S310 tu nie dotyczy.
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            body = resp.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            logger.debug("probe_http_service: odpowiedź %r przekroczyła limit %d B", url, MAX_BYTES)
            return result
        result["data"] = json.loads(body)
        result["available"] = True
    except Exception as exc:
        logger.debug("probe_http_service(%r) nieudane: %s", url, exc)
    return result


def check_ollama() -> dict[str, Any]:
    """Sprawdza czy serwer Ollama działa i zwraca listę dostępnych modeli.

    Returns:
        Słownik z kluczami: available (bool), models (list[str]).
    """
    result: dict[str, Any] = {"available": False, "models": []}
    try:
        probe = probe_http_service("http://localhost:11434/api/tags")
        if probe["available"]:
            data = probe["data"] or {}
            result["models"] = [m["name"] for m in data.get("models", [])]
            result["available"] = True
    except Exception as exc:
        logger.debug("check_ollama nieudane: %s", exc)
    return result
