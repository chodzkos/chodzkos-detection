# Polityka bezpieczeństwa

## Zgłaszanie podatności

**Nie zgłaszaj podatności przez publiczne Issues ani Pull Requesty.**

- **Preferowane:** prywatne zgłoszenie przez GitHub — w tym repo zakładka
  **Security → Report a vulnerability** (Private Vulnerability Reporting).
- **Alternatywnie:** e-mail na **chodzkos@gmail.com** z prefiksem `SECURITY`
  w temacie.

W zgłoszeniu podaj: opis problemu, kroki reprodukcji lub PoC, wersję pakietu
(tag `vX.Y.Z`) oraz środowisko (OS, wersja Pythona). Pakiet jest **stdlib-only**
(bez zależności runtime) — istotne bywają sondy CLI/HTTP i obsługa wejścia
zewnętrznego.

## Czas odpowiedzi

Projekt prowadzony w modelu best-effort (po godzinach) — terminy orientacyjne:

- potwierdzenie przyjęcia zgłoszenia: **do 7 dni**,
- wstępna ocena i plan naprawy: **do 30 dni**.

Po wydaniu poprawki skoordynujemy ujawnienie (credit dla zgłaszającego, jeśli
sobie życzy).

## Wspierane wersje

Poprawki bezpieczeństwa trafiają wyłącznie do **najnowszej wydanej wersji**
(najwyższy tag `vX.Y.Z`). Wydania `0.x` nie są łatane wstecz — zaktualizuj pin
w aplikacji do najnowszego taga.

| Wersja                 | Wsparcie |
| ---------------------- | -------- |
| najnowszy tag `v0.y.z` | ✅       |
| starsze `0.x`          | ❌       |
