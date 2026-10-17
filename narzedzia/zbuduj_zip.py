#!/usr/bin/env python3
"""Buduje dist/widocznosc-w-ai.zip do wgrania w Claude.ai.

Układ zgodny z pomocą Anthropic ("How to create custom Skills"): w głównym
katalogu ZIP-a jest folder skilla, a w nim SKILL.md. Folder ma tę samą nazwę
co pole `name` w SKILL.md.

    widocznosc-w-ai.zip
      widocznosc-w-ai/
        SKILL.md
        references/...
        scripts/...
        assets/...

Pomija pliki tymczasowe (__pycache__, *.pyc, .DS_Store). Daty plików w archiwum
są stałe, więc ten sam stan repozytorium daje identyczny ZIP.

Użycie (z głównego folderu repozytorium):
    python3 narzedzia/zbuduj_zip.py
"""

import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "widocznosc-w-ai"
DIST = REPO / "dist"
POMIJANE_FOLDERY = {"__pycache__", ".git", "node_modules"}
POMIJANE_PLIKI = {".DS_Store", "Thumbs.db"}
STALA_DATA = (2026, 1, 1, 0, 0, 0)


def pliki_skilla() -> list[Path]:
    wynik = []
    for sciezka in sorted(SKILL.rglob("*")):
        if not sciezka.is_file():
            continue
        czesci = sciezka.relative_to(SKILL).parts
        if any(c in POMIJANE_FOLDERY for c in czesci):
            continue
        if sciezka.name in POMIJANE_PLIKI or sciezka.suffix == ".pyc":
            continue
        wynik.append(sciezka)
    return wynik


def main() -> int:
    if not (SKILL / "SKILL.md").exists():
        print(f"Nie znaleziono {SKILL / 'SKILL.md'}", file=sys.stderr)
        return 1
    DIST.mkdir(exist_ok=True)
    cel = DIST / f"{SKILL.name}.zip"
    with zipfile.ZipFile(cel, "w", zipfile.ZIP_DEFLATED) as archiwum:
        for plik in pliki_skilla():
            nazwa = plik.relative_to(SKILL.parent).as_posix()
            info = zipfile.ZipInfo(nazwa, date_time=STALA_DATA)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if plik.suffix == ".py" else 0o644) << 16
            archiwum.writestr(info, plik.read_bytes())
            print(f"  dodano: {nazwa}")
    print(f"Gotowe: {cel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
