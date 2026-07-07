# chodzkos-detection

Uniwersalne, **stdlib-only** sondy środowiska: narzędzia CLI i usługi HTTP.
Pakiet instaluje się **bez Qt i bez torcha** — nadaje się do CLI, serwera czy
dowolnej aplikacji, która chce sprawdzić dostępność zewnętrznych narzędzi bez
ciągnięcia ciężkich zależności.

> Detekcja GPU/sprzętu (torch, CUDA, nvidia-smi) **nie jest** częścią tego pakietu —
> każda aplikacja trzyma własną warstwę torchową. Tu zostaje czysta warstwa
> narzędzi i usług.

## API

### `chodzkos_detection.tools`
- `probe_tool(name, version_args=None, version_parser=None) -> dict` — generyczna sonda
  binarki w PATH (`shutil.which` + opcjonalny odczyt wersji przez subprocess); odporna na
  wyjątki (`{"available": bool, "version": str}`).
- `check_tesseract() -> dict` — `{available, version, languages}`.
- `check_poppler() -> bool`, `check_pandoc() -> bool`.
- `check_tools() -> dict` — zbiorczy raport powyższych.

### `chodzkos_detection.services`
- `probe_http_service(url, timeout=2) -> dict` — generyczna sonda usługi HTTP zwracającej
  JSON (`{"available": bool, "data": Any | None}`); odporna na wyjątki.
- `check_ollama() -> dict` — `{available, models}` (serwer Ollama na `localhost:11434`).

## Przykład

```python
from chodzkos_detection import probe_tool, check_ollama

print(probe_tool("pandoc", ["--version"]))   # {"available": True, "version": "3.1.11"}
print(check_ollama())                          # {"available": False, "models": []}
```

## Rozwój

```bash
uv run --extra dev pytest
uv run --extra dev ruff check .
uv run --extra dev mypy src/
```

`uv.lock` jest **śledzony w repo** (spójnie z `gui-kit`): pre-commit i CI wołają
`uv run --extra dev`, więc zablokowany toolchain daje reprodukowalne środowisko
dev/CI. `uv sync --extra dev` odtwarza je dokładnie; aktualizacje zależności idą
przez Dependabota (ekosystem `pip`).
