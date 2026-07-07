"""Testy sond usług HTTP (probe_http_service, Ollama)."""

from __future__ import annotations

import pytest

from chodzkos_detection import services


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, amt: int | None = None) -> bytes:
        # Odwzorowuje kontrakt http.client.HTTPResponse.read(amt): przy podanym
        # limicie zwraca co najwyżej `amt` bajtów (produkcja czyta MAX_BYTES + 1).
        if amt is None or amt < 0:
            return self._payload
        return self._payload[:amt]


def test_probe_http_service_returns_parsed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(url: str, *, timeout: int) -> _FakeResponse:
        assert url == "http://example/api"
        assert timeout == 3
        return _FakeResponse(b'{"hello": "world"}')

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert services.probe_http_service("http://example/api", timeout=3) == {
        "available": True,
        "data": {"hello": "world"},
    }


def test_probe_http_service_false_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(*_args: object, **_kwargs: object) -> object:
        raise OSError("server down")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert services.probe_http_service("http://example/api") == {
        "available": False,
        "data": None,
    }


def test_probe_http_service_rejects_non_http_scheme(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fake_urlopen(*_args: object, **_kwargs: object) -> object:
        nonlocal called
        called = True
        raise AssertionError("urlopen nie powinno być wołane dla schematu file://")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert services.probe_http_service("file:///etc/passwd") == {
        "available": False,
        "data": None,
    }
    # Kluczowe: odrzucenie następuje przed otwarciem zasobu (brak SSRF/odczytu pliku).
    assert called is False


def test_probe_http_service_rejects_oversized_response(monkeypatch: pytest.MonkeyPatch) -> None:
    oversized = b"[" + b"0," * services.MAX_BYTES  # > MAX_BYTES bajtów

    def fake_urlopen(url: str, *, timeout: int) -> _FakeResponse:
        return _FakeResponse(oversized)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert services.probe_http_service("http://example/api") == {
        "available": False,
        "data": None,
    }


def test_check_ollama_returns_models(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(url: str, *, timeout: int) -> _FakeResponse:
        assert url == "http://localhost:11434/api/tags"
        assert timeout == 2
        return _FakeResponse(b'{"models": [{"name": "qwen2.5:14b"}, {"name": "llama3"}]}')

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = services.check_ollama()

    assert result == {"available": True, "models": ["qwen2.5:14b", "llama3"]}


def test_check_ollama_false_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(*_args: object, **_kwargs: object) -> object:
        raise OSError("server down")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert services.check_ollama() == {"available": False, "models": []}
