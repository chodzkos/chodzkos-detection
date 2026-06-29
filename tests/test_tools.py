"""Testy sond narzędzi CLI (probe_tool, tesseract/poppler/pandoc)."""

from __future__ import annotations

import subprocess

import pytest

from chodzkos_detection import tools


def test_probe_tool_absent_when_not_in_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools.shutil, "which", lambda _command: None)

    assert tools.probe_tool("widget", ["--version"]) == {
        "available": False,
        "version": "",
    }


def test_probe_tool_present_without_version_args(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools.shutil, "which", lambda _command: "/usr/bin/widget")

    # Bez version_args sonda nie uruchamia subprocessu — sprawdza tylko obecność w PATH.
    def fail_run(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("subprocess nie powinien być wywołany")

    monkeypatch.setattr(tools.subprocess, "run", fail_run)

    assert tools.probe_tool("widget") == {"available": True, "version": ""}


def test_probe_tool_parses_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools.shutil, "which", lambda _command: "/usr/bin/widget")

    def fake_run(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        assert command == ["widget", "--version"]
        assert timeout == 5
        return subprocess.CompletedProcess(command, 0, stdout="widget 2.4.1\nfoo\n")

    monkeypatch.setattr(tools.subprocess, "run", fake_run)

    assert tools.probe_tool("widget", ["--version"]) == {
        "available": True,
        "version": "2.4.1",
    }


def test_probe_tool_custom_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools.shutil, "which", lambda _command: "/usr/bin/widget")
    monkeypatch.setattr(
        tools.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, stdout="ver=9.9\n"),
    )

    result = tools.probe_tool(
        "widget", ["--version"], version_parser=lambda out: out.split("=")[-1].strip()
    )

    assert result == {"available": True, "version": "9.9"}


def test_probe_tool_unavailable_when_version_call_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools.shutil, "which", lambda _command: "/usr/bin/widget")

    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise OSError("boom")

    monkeypatch.setattr(tools.subprocess, "run", fake_run)

    assert tools.probe_tool("widget", ["--version"]) == {
        "available": False,
        "version": "",
    }


def test_check_tesseract_returns_version_and_languages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools.shutil, "which", lambda command: "/usr/bin/tesseract")

    def fake_run(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        if command == ["tesseract", "--version"]:
            return subprocess.CompletedProcess(command, 0, stdout="tesseract 5.3.0\n")
        if command == ["tesseract", "--list-langs"]:
            return subprocess.CompletedProcess(
                command, 0, stdout="List of available languages\neng\npol\n"
            )
        raise AssertionError(command)

    monkeypatch.setattr(tools.subprocess, "run", fake_run)

    result = tools.check_tesseract()

    assert result == {"available": True, "version": "5.3.0", "languages": ["eng", "pol"]}


def test_check_tesseract_false_when_binary_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools.shutil, "which", lambda _command: None)

    assert tools.check_tesseract() == {
        "available": False,
        "version": "",
        "languages": [],
    }


def test_check_tesseract_false_when_command_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools.shutil, "which", lambda _command: "/usr/bin/tesseract")

    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise OSError("boom")

    monkeypatch.setattr(tools.subprocess, "run", fake_run)

    assert tools.check_tesseract()["available"] is False


def test_simple_binary_checks_use_shutil_which(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_which(command: str) -> str | None:
        return "/usr/bin/pdftotext" if command == "pdftotext" else None

    monkeypatch.setattr(tools.shutil, "which", fake_which)

    assert tools.check_poppler() is True
    assert tools.check_pandoc() is False


def test_check_tools_aggregates_probes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools, "check_tesseract", lambda: {"available": False})
    monkeypatch.setattr(tools, "check_poppler", lambda: True)
    monkeypatch.setattr(tools, "check_pandoc", lambda: False)

    assert tools.check_tools() == {
        "tesseract": {"available": False},
        "poppler": True,
        "pandoc": False,
    }
