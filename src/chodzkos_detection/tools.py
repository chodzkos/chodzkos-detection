"""Wykrywanie narzędzi CLI (Tesseract, Poppler, Pandoc).

Wszystkie funkcje są odporne na brak narzędzia — zwracają False/pusty dict,
nie rzucają wyjątków.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# CREATE_NO_WINDOW tłumi mignięcie okna konsoli przy subprocess na Windows (widoczne, gdy
# wołający jest gui-scriptem bez własnej konsoli). Poza Windows = 0, więc przekazujemy
# bezwarunkowo. `if`-instrukcja (nie wyrażenie) — tak mypy zawęża sys.platform i sprawdza
# CREATE_NO_WINDOW tylko pod win32, gdzie atrybut istnieje.
if sys.platform == "win32":  # pragma: no cover - gałąź platformowa (CI jest na Linuksie)
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW
else:
    _SUBPROCESS_FLAGS = 0


def find_tool(name: str, extra_paths: Sequence[str | Path] = ()) -> str | None:
    """Znajduje pełną ścieżkę narzędzia: najpierw PATH (``shutil.which``), potem ``extra_paths``.

    Zwraca pełną ścieżkę pierwszego istniejącego pliku albo ``None``. Przydatne dla narzędzi
    instalowanych poza PATH (np. Calibre w ``C:\\Calibre2``) — wołający dokłada kandydatów
    (z rejestru / znanych katalogów), a kolejność „PATH-first" zachowuje priorytet instalacji
    widocznej w środowisku.

    Args:
        name: nazwa binarki szukanej najpierw przez ``shutil.which``.
        extra_paths: dodatkowi kandydaci (pełne ścieżki), sprawdzani po PATH w podanej kolejności.

    Returns:
        Pełna ścieżka do istniejącego pliku albo ``None``, gdy nie znaleziono nigdzie.
    """
    in_path = shutil.which(name)
    if in_path is not None:
        return in_path
    for candidate in extra_paths:
        path = Path(candidate)
        if path.is_file():
            return str(path)
    return None


def _default_version_parser(output: str) -> str:
    """Domyślny parser wersji: ostatni token pierwszej niepustej linii (np. ``tool 1.2.3``)."""
    for line in output.splitlines():
        if line.strip():
            return line.split()[-1]
    return ""


def probe_tool(
    name: str,
    version_args: list[str] | None = None,
    version_parser: Callable[[str], str] | None = None,
    *,
    executable: str | None = None,
) -> dict[str, Any]:
    """Generyczna sonda narzędzia CLI dostępnego w PATH.

    Args:
        name: nazwa binarki szukanej przez ``shutil.which`` (gdy nie podano ``executable``).
        version_args: argumenty wywołania zwracającego wersję (np. ``["--version"]``).
            Gdy ``None`` — sprawdzamy tylko obecność, bez subprocessu.
        version_parser: opcjonalny parser wyjścia (stdout/stderr) na łańcuch wersji;
            domyślnie ostatni token pierwszej niepustej linii.
        executable: pełna ścieżka do binarki zamiast szukania po nazwie w PATH (np. wynik
            :func:`find_tool` dla narzędzia zainstalowanego poza PATH). Gdy podana, pomijamy
            ``shutil.which`` i ufamy wołającemu, że ścieżka istnieje.

    Returns:
        Słownik ``{"available": bool, "version": str}``. Odporny na wyjątki — gdy binarka
        jest dostępna, lecz wywołanie wersji zawiedzie (timeout/OSError/parsowanie), zwraca
        ``available=False`` zamiast rzucać (jak reszta modułu).
    """
    result: dict[str, Any] = {"available": False, "version": ""}
    resolved = executable if executable is not None else shutil.which(name)
    if resolved is None:
        return result
    if not version_args:
        result["available"] = True
        return result
    parser = version_parser or _default_version_parser
    try:
        # Uruchamiamy rozwiązaną ścieżkę (z which albo jawnie podaną), nie gołą nazwę —
        # brak ponownego przeszukiwania PATH i mniejsze ryzyko podmiany binarki.
        proc = subprocess.run(
            [resolved, *version_args],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=_SUBPROCESS_FLAGS,
        )
        # Niezerowy kod = wywołanie wersji zawiodło, choć binarka jest w PATH.
        # Kontrakt (jak reszta modułu) obiecuje wtedy available=False, version="".
        if proc.returncode != 0:
            logger.debug("probe_tool(%r): niezerowy kod wyjścia %d", name, proc.returncode)
            return result
        result["version"] = parser(proc.stdout or proc.stderr)
        result["available"] = True
    except Exception as exc:
        logger.debug("probe_tool(%r) nieudane: %s", name, exc)
    return result


def check_tesseract() -> dict[str, Any]:
    """Sprawdza czy Tesseract OCR jest zainstalowany i zwraca jego wersję oraz języki.

    Returns:
        Słownik z kluczami: available (bool), version (str), languages (list[str]).
    """
    probe = probe_tool("tesseract", ["--version"])
    result: dict[str, Any] = {
        "available": probe["available"],
        "version": probe["version"],
        "languages": [],
    }
    if not probe["available"]:
        return result
    # probe.available=True gwarantuje obecność w PATH; which zwraca tę samą
    # rozwiązaną ścieżkę, którą przekazujemy do subprocessu (spójnie z probe_tool).
    tesseract = shutil.which("tesseract")
    if tesseract is None:
        return result
    # --list-langs to rozszerzenie ponad generyczną sondę (sonda „bogatsza").
    try:
        lang_proc = subprocess.run(
            [tesseract, "--list-langs"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=_SUBPROCESS_FLAGS,
        )
        # Niezerowy kod = nie ufamy wyjściu; zostawiamy languages=[] zamiast parsować błąd.
        if lang_proc.returncode != 0:
            logger.debug(
                "check_tesseract --list-langs: niezerowy kod wyjścia %d", lang_proc.returncode
            )
            return result
        result["languages"] = [
            ln.strip()
            for ln in (lang_proc.stdout or lang_proc.stderr).splitlines()
            if ln.strip() and not ln.startswith("List")
        ]
    except Exception as exc:
        logger.debug("check_tesseract --list-langs nieudane: %s", exc)
    return result


def check_poppler() -> bool:
    """Sprawdza czy pdftotext (część Poppler) jest dostępny w PATH."""
    return bool(probe_tool("pdftotext")["available"])


def check_pandoc() -> bool:
    """Sprawdza czy Pandoc jest dostępny w PATH."""
    return bool(probe_tool("pandoc")["available"])


def check_tools() -> dict[str, Any]:
    """Zbiorczy raport sond narzędzi CLI (tesseract/poppler/pandoc)."""
    return {
        "tesseract": check_tesseract(),
        "poppler": check_poppler(),
        "pandoc": check_pandoc(),
    }
