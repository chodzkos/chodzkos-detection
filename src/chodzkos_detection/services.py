"""Wykrywanie usług sieciowych (Ollama).

Wszystkie funkcje są odporne na brak usługi — zwracają pusty dict,
nie rzucają wyjątków.
"""

from __future__ import annotations

from typing import Any


def probe_http_service(url: str, timeout: int = 2) -> dict[str, Any]:
    """Generyczna sonda usługi HTTP zwracającej JSON.

    Args:
        url: adres endpointu zwracającego JSON.
        timeout: limit czasu połączenia w sekundach.

    Returns:
        Słownik ``{"available": bool, "data": Any | None}``. Odporny na wyjątki —
        przy braku usługi/błędzie zwraca ``available=False`` zamiast rzucać.
    """
    result: dict[str, Any] = {"available": False, "data": None}
    try:
        import json
        import urllib.request

        with urllib.request.urlopen(url, timeout=timeout) as resp:
            result["data"] = json.loads(resp.read())
            result["available"] = True
    except Exception:
        pass
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
    except Exception:
        pass
    return result
