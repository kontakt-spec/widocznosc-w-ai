#!/usr/bin/env python3
"""Liczy metryki widoczności firmy w odpowiedziach AI z pliku wyników JSON.

Skrypt jest częścią skilla "widocznosc-w-ai". Nie łączy się z internetem i nie
wymaga żadnych bibliotek poza standardową biblioteką Pythona 3.

Użycie:
    python licz_wynik.py wyniki.json
    python licz_wynik.py wyniki.json --poprzedni stary.json
    python licz_wynik.py wyniki.json --md raport_metryki.md --top 10

Bez --md pełny raport trafia na standardowe wyjście. Z --md raport trafia do
pliku, a na wyjściu jest tylko krótkie podsumowanie (oszczędza miejsce w rozmowie).

Co liczy (osobno dla każdego trybu sprawdzania, np. "wyszukiwanie", "pamiec"):
    * widoczność (visibility rate): w ilu pytaniach niebrandowych firma się pojawiła,
      podzielone przez liczbę sprawdzonych pytań niebrandowych; także per kategoria,
    * udział w odpowiedziach (share of voice): wzmianki o firmie podzielone przez
      wszystkie wzmianki o firmach w odpowiedziach na pytania niebrandowe,
    * ranking firm, które pojawiały się w odpowiedziach (liczba pytań),
    * najczęściej cytowane domeny źródłowe i to, czy cytowana była strona firmy,
    * zależność trafień firmy od jednego źródła,
    * wyniki pytań o markę (liczone osobno, nie wchodzą do widoczności),
    * zmianę względem poprzedniego pliku (punkty procentowe), jeśli go podano.

Pozycja firmy w odpowiedzi jest pokazywana wyłącznie informacyjnie: odpowiedzi
AI zmieniają kolejność niemal przy każdym powtórzeniu tego samego pytania.

Minimalny schemat pliku wyników (pełny opis: references/metodologia.md):

    {
      "wersja_schematu": 1,
      "data": "2026-10-17",
      "firma": {"nazwa": "...", "aliasy": ["..."], "strona": "https://...",
                "nazwa_opisowa": false,
                "konkurenci": ["..."], "konkurenci_wywnioskowani": ["..."]},
      "aliasy_firm": {"Nazwa kanoniczna": ["wariant 1", "wariant 2"]},
      "pytania": [
        {"id": "P01", "kategoria": "polecenie", "tresc": "...",
         "wyniki": {
            "wyszukiwanie": {"zapytania": ["..."], "firmy": ["A", "B"],
                             "zrodla": ["https://..."], "notatka": "..."},
            "pamiec": {"firmy": ["A"]}
         }}
      ]
    }

Kategoria "marka" oznacza pytanie o markę (branded). Wynik z polem "blad"
(np. {"blad": "wyszukiwanie nie zadziałało"}) jest pomijany w liczeniu.

Kody wyjścia: 0 sukces, 1 błąd danych wejściowych, 2 błędne argumenty.
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

# ---------------------------------------------------------------------------
# Stałe
# ---------------------------------------------------------------------------

KATEGORIE = {
    "polecenie": "Polecenie wprost",
    "problem": "Problem bez nazwy usługi",
    "ranking": "Ranking i porównanie",
    "kryteria": "Kryteria (budżet, specjalizacja, branża)",
    "alternatywy": "Alternatywy dla konkurenta",
    "marka": "Pytania o markę",
}
KATEGORIA_MARKA = "marka"

TRYBY = {
    "wyszukiwanie": "Claude z wyszukiwaniem",
    "pamiec": "Claude bez internetu (pamięć modelu)",
    "chatgpt": "ChatGPT (sprawdzone ręcznie)",
    "perplexity": "Perplexity (sprawdzone ręcznie)",
    "gemini": "Gemini (sprawdzone ręcznie)",
    "google_ai": "Google AI Overviews / AI Mode (sprawdzone ręcznie)",
    "copilot": "Copilot (sprawdzone ręcznie)",
}
TRYB_GLOWNY = "wyszukiwanie"
TRYBY_RECZNE = ["chatgpt", "perplexity", "gemini", "google_ai", "copilot"]

# Najwięcej firm na jedno pytanie zgodnie z zasadami skilla.
MAKS_FIRM = 7

# Platformy, na których firma może mieć tylko profil. Gdy "strona" firmy leży
# na takiej platformie, cytowanie liczymy po adresie profilu, a nie po domenie.
PLATFORMY = {
    "facebook.com", "instagram.com", "linkedin.com", "tiktok.com", "youtube.com",
    "x.com", "twitter.com", "google.com", "g.page", "booksy.com", "znanylekarz.pl",
    "olx.pl", "allegro.pl", "oferteo.pl", "useme.com", "fixly.pl", "pinterest.com",
    "linktr.ee", "wix.com", "wixsite.com", "blogspot.com", "wordpress.com",
}

# Formy prawne usuwane z nazw. Kolejność ma znaczenie: dłuższe wzorce najpierw.
_FORMY_PRAWNE = [
    r"sp[oó]łka\s+z\s+ograniczon[aą]\s+odpowiedzialno[sś]ci[aą]",
    r"prosta\s+sp[oó]łka\s+akcyjna",
    r"sp[oó]łka\s+komandytowo[\s-]+akcyjna",
    r"sp[oó]łka\s+komandytowa",
    r"sp[oó]łka\s+akcyjna",
    r"sp[oó]łka\s+jawna",
    r"sp[oó]łka\s+cywilna",
    r"sp[oó]łka\s+partnerska",
    r"sp\.?\s*z\s*o\.?\s*o\.?",
    r"p\.\s?s\.\s?a\.?",
    r"s\.\s?k\.\s?a\.?",
    r"sp\.\s?k\.?",
    r"sp\.\s?j\.?",
    r"sp\.\s?p\.?",
    r"s\.\s?a\.?",
    r"s\.\s?c\.?",
    r"sp[oó]łka",
]
_FORMY_RE = re.compile(
    r"(?<!\w)(?:" + "|".join(_FORMY_PRAWNE) + r")(?!\w)", re.IGNORECASE
)
# Skróty bez kropek rozpoznajemy tylko pisane wielkimi literami na końcu nazwy,
# żeby nie wyciąć np. słowa "sa" z nazwy własnej.
_FORMY_KONCOWE_RE = re.compile(r"(?<!\w)(?:SA|SC|SKA|PSA|SPZOO|SP\.?\s?ZOO)\s*$")
_ZNAKI_DO_USUNIECIA = re.compile(r"[\"'„”“«»‚‘’`()\[\]{}]")
# "https://www." na początku nazwy i końcówki domen ("iFirma.pl" = "iFirma").
_PREFIKS_URL = re.compile(r"(?<!\w)(?:https?://)?www\.", re.IGNORECASE)
_KONCOWKA_DOMENY = re.compile(
    r"(?<=\w)\.(?:com\.pl|net\.pl|org\.pl|pl|com|eu|io|net|org|app|ai|co|biz|info|online|shop|store)"
    r"(?=$|[\s/,;:)!?])",
    re.IGNORECASE,
)
_INTERPUNKCJA = re.compile(r"[^\w\s]")
_SPACJE = re.compile(r"\s+")


class BladDanych(Exception):
    """Błąd w danych wejściowych. Zawiera listę czytelnych komunikatów."""

    def __init__(self, komunikaty: list[str]):
        super().__init__("\n".join(komunikaty))
        self.komunikaty = komunikaty


# ---------------------------------------------------------------------------
# Normalizacja nazw i domen
# ---------------------------------------------------------------------------


def usun_diakrytyki(tekst: str) -> str:
    """Zamienia polskie (i inne) znaki diakrytyczne na podstawowe litery."""
    tekst = tekst.replace("ł", "l").replace("Ł", "L")
    rozlozony = unicodedata.normalize("NFKD", tekst)
    return "".join(z for z in rozlozony if not unicodedata.combining(z))


def usun_forme_prawna(nazwa: str) -> str:
    """Usuwa formę prawną i cudzysłowy, zachowując wielkość liter i diakrytyki."""
    wynik = _ZNAKI_DO_USUNIECIA.sub(" ", nazwa)
    wynik = _FORMY_RE.sub(" ", wynik)
    wynik = _FORMY_KONCOWE_RE.sub(" ", wynik.strip())
    wynik = _SPACJE.sub(" ", wynik).strip(" ,.-;:/&")
    return wynik.strip()


def klucz_nazwy(nazwa: str) -> str:
    """Klucz do porównywania nazw firm.

    Małe litery, bez formy prawnej, bez "www." i końcówki domeny, bez
    interpunkcji i bez znaków diakrytycznych. Dzięki temu "Księgowość Gamma s.c."
    i "KSIEGOWOSC GAMMA" dają ten sam klucz, podobnie "iFirma.pl" i "ifirma".
    """
    wynik = usun_forme_prawna(nazwa)
    wynik = _PREFIKS_URL.sub(" ", wynik)
    wynik = _KONCOWKA_DOMENY.sub("", wynik).casefold()
    wynik = _INTERPUNKCJA.sub(" ", wynik)
    wynik = usun_diakrytyki(wynik)
    return _SPACJE.sub(" ", wynik).strip()


def adres_zrodla(zrodlo: str) -> tuple[str, str] | None:
    """Zwraca (domena, ścieżka) dla adresu URL lub domeny.

    Usuwa "www." i "m.". Linki do Map Google sprowadza do "google.com/maps",
    bo to osobne, ważne źródło dla firm lokalnych. Ścieżka jest małymi literami,
    bez ukośników na początku i końcu; dla facebook.com/profile.php zawiera też
    parametr id ("profile.php?id=123"), bo tylko on wskazuje konkretny profil.
    """
    tekst = zrodlo.strip()
    if not tekst:
        return None
    if tekst.casefold() in ("google maps", "mapy google", "google mapy", "mapy"):
        return ("google.com/maps", "")
    if "://" not in tekst:
        tekst = "//" + tekst
    try:
        czesci = urlsplit(tekst)
        host = (czesci.hostname or "").strip(".")
    except ValueError:
        return None
    if not host or " " in host or "." not in host:
        return None
    for prefiks in ("www.", "m."):
        if host.startswith(prefiks):
            host = host[len(prefiks):]
            break
    sciezka = (czesci.path or "").lower()
    if (
        host.startswith("maps.google.")
        or host == "maps.app.goo.gl"
        or (host == "goo.gl" and sciezka.startswith("/maps"))
        or (host.startswith("google.") and sciezka.startswith("/maps"))
    ):
        return ("google.com/maps", "")
    sciezka = sciezka.strip("/")
    if (host == "facebook.com" or host.endswith(".facebook.com")) and sciezka == "profile.php":
        identyfikator = (parse_qs(czesci.query).get("id") or [""])[0].strip()
        sciezka = f"profile.php?id={identyfikator}" if identyfikator else sciezka
    return (host, sciezka)


def domena_z_zrodla(zrodlo: str) -> str | None:
    """Znormalizowana domena źródła albo None, gdy to nie wygląda na adres."""
    adres = adres_zrodla(zrodlo)
    return adres[0] if adres else None


def _czy_platforma(domena: str) -> bool:
    return any(domena == p or domena.endswith("." + p) for p in PLATFORMY)


def czy_zawiera_fraze(tekst_klucz: str, fraza_klucz: str) -> bool:
    """Czy znormalizowany tekst zawiera frazę jako całe słowa."""
    if not fraza_klucz:
        return False
    return re.search(r"(?<!\w)" + re.escape(fraza_klucz) + r"(?!\w)", tekst_klucz) is not None


# ---------------------------------------------------------------------------
# Wczytywanie i walidacja
# ---------------------------------------------------------------------------


def wczytaj_json(sciezka: Path) -> object:
    """Wczytuje plik JSON z czytelnym komunikatem po polsku przy błędzie."""
    if not sciezka.exists():
        raise BladDanych([f"Nie znaleziono pliku: {sciezka}"])
    if sciezka.is_dir():
        raise BladDanych([f"To jest folder, a nie plik: {sciezka}"])
    try:
        tekst = sciezka.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise BladDanych([f"Plik {sciezka} nie jest zapisany w kodowaniu UTF-8."])
    except OSError as blad:
        raise BladDanych([f"Nie udało się odczytać pliku {sciezka}: {blad}"])
    try:
        return json.loads(tekst)
    except json.JSONDecodeError as blad:
        raise BladDanych(
            [
                f"Plik {sciezka} nie jest poprawnym JSON-em: {blad.msg} "
                f"(linia {blad.lineno}, kolumna {blad.colno}). "
                "Najczęstsze przyczyny: brak przecinka między elementami, przecinek "
                "po ostatnim elemencie albo cudzysłowy typu „ ” zamiast \" \"."
            ]
        )


def _lista_napisow(wartosc: object, sciezka: str, bledy: list[str]) -> list[str]:
    if wartosc is None:
        return []
    if not isinstance(wartosc, list) or not all(isinstance(x, str) for x in wartosc):
        bledy.append(f"Pole {sciezka} musi być listą napisów, np. [\"A\", \"B\"].")
        return []
    return wartosc


def waliduj(dane: object) -> list[str]:
    """Sprawdza strukturę danych. Zwraca listę błędów (pusta = w porządku)."""
    bledy: list[str] = []
    if not isinstance(dane, dict):
        return ["Główny element pliku musi być obiektem JSON w nawiasach { }."]

    firma = dane.get("firma")
    if not isinstance(firma, dict):
        bledy.append("Brak pola \"firma\" (obiekt z co najmniej polem \"nazwa\").")
    else:
        if not isinstance(firma.get("nazwa"), str) or not firma["nazwa"].strip():
            bledy.append("Brak pola firma.nazwa (nazwa sprawdzanej firmy).")
        for pole in ("aliasy", "konkurenci", "konkurenci_wywnioskowani"):
            _lista_napisow(firma.get(pole), f"firma.{pole}", bledy)
        for pole in ("strona", "domena"):
            if pole in firma and firma[pole] is not None and not isinstance(firma[pole], str):
                bledy.append(f"Pole firma.{pole} musi być napisem.")
        if "nazwa_opisowa" in firma and not isinstance(firma["nazwa_opisowa"], bool):
            bledy.append("Pole firma.nazwa_opisowa musi mieć wartość true albo false.")

    aliasy_firm = dane.get("aliasy_firm")
    if aliasy_firm is not None:
        if not isinstance(aliasy_firm, dict):
            bledy.append("Pole aliasy_firm musi być obiektem: {\"Nazwa\": [\"wariant\"]}.")
        else:
            for nazwa, warianty in aliasy_firm.items():
                _lista_napisow(warianty, f"aliasy_firm[\"{nazwa}\"]", bledy)

    pytania = dane.get("pytania")
    if not isinstance(pytania, list) or not pytania:
        bledy.append("Brak pola \"pytania\" albo lista pytań jest pusta.")
        return bledy

    widziane_id: set[str] = set()
    for i, pytanie in enumerate(pytania):
        miejsce = f"pytania[{i}]"
        if not isinstance(pytanie, dict):
            bledy.append(f"{miejsce} musi być obiektem.")
            continue
        pid = pytanie.get("id")
        if not isinstance(pid, (str, int)) or isinstance(pid, bool) or str(pid).strip() == "":
            bledy.append(f"{miejsce}: brak pola \"id\" (np. \"P01\").")
        else:
            miejsce = f"pytania[{i}] (id {pid})"
            if str(pid) in widziane_id:
                bledy.append(f"{miejsce}: id się powtarza. Każde pytanie musi mieć inne id.")
            widziane_id.add(str(pid))
        if not isinstance(pytanie.get("tresc"), str) or not pytanie["tresc"].strip():
            bledy.append(f"{miejsce}: brak pola \"tresc\" (treść pytania).")
        if not isinstance(pytanie.get("kategoria"), str) or not pytanie["kategoria"].strip():
            bledy.append(f"{miejsce}: brak pola \"kategoria\".")
        wyniki = pytanie.get("wyniki")
        if wyniki is None:
            continue
        if not isinstance(wyniki, dict):
            bledy.append(f"{miejsce}: pole \"wyniki\" musi być obiektem, np. {{\"wyszukiwanie\": {{...}}}}.")
            continue
        for tryb, wynik in wyniki.items():
            m = f"{miejsce}.wyniki.{tryb}"
            if not isinstance(wynik, dict):
                bledy.append(f"{m} musi być obiektem.")
                continue
            if "blad" in wynik:
                continue
            if "firmy" not in wynik:
                bledy.append(
                    f"{m}: brak pola \"firmy\" (lista firm z odpowiedzi; pusta lista [] "
                    "jeśli nie wymieniono żadnej firmy)."
                )
            _lista_napisow(wynik.get("firmy"), f"{m}.firmy", bledy)
            for pole in ("zrodla", "zapytania", "poprawne", "bledne", "brakujace"):
                _lista_napisow(wynik.get(pole), f"{m}.{pole}", bledy)
    return bledy


# ---------------------------------------------------------------------------
# Rozpoznawanie firm
# ---------------------------------------------------------------------------


class Rozpoznawacz:
    """Mapuje nazwy firm na wspólne klucze, z uwzględnieniem aliasów.

    Wszystkie warianty sprawdzanej firmy dostają jeden klucz (`klucz_nasz`),
    więc dwa zapisy tej samej firmy w jednej odpowiedzi liczą się raz.
    Przy konflikcie aliasów sprawdzana firma ma pierwszeństwo przed konkurentem.
    """

    def __init__(self, firma: dict, aliasy_firm: dict[str, list[str]]):
        self.ostrzezenia: list[str] = []
        self.nazwa_firmy = usun_forme_prawna(firma["nazwa"]) or firma["nazwa"].strip()
        self.nazwa_opisowa = bool(firma.get("nazwa_opisowa"))
        self.klucz_nasz = klucz_nazwy(firma["nazwa"])
        self.klucze_naszej = {self.klucz_nasz}
        for alias in firma.get("aliasy") or []:
            if klucz_nazwy(alias):
                self.klucze_naszej.add(klucz_nazwy(alias))
        self.klucze_naszej.discard("")

        self.mapa_aliasow: dict[str, str] = {}
        self.nazwy_kanoniczne: dict[str, str] = {}
        for kanoniczna, warianty in (aliasy_firm or {}).items():
            k = klucz_nazwy(kanoniczna)
            if not k:
                continue
            if k in self.klucze_naszej:
                self.ostrzezenia.append(
                    f"W aliasy_firm jest \"{kanoniczna}\", a to nazwa Twojej firmy. Pomijam tę grupę "
                    "aliasów. Warianty swojej firmy wpisuj w firma.aliasy."
                )
                continue
            self.nazwy_kanoniczne[k] = usun_forme_prawna(kanoniczna) or kanoniczna
            for wariant in warianty or []:
                kw = klucz_nazwy(wariant)
                if not kw:
                    continue
                if kw in self.klucze_naszej:
                    self.ostrzezenia.append(
                        f"Wariant \"{wariant}\" jest jednocześnie aliasem Twojej firmy i konkurenta "
                        f"\"{kanoniczna}\". Liczę go jako Twoją firmę. Sprawdź, czy to poprawne."
                    )
                    continue
                self.mapa_aliasow[kw] = k

        # Konkurenci: klucz -> (nazwa do wyświetlenia, "podany" albo "wywnioskowany").
        self.konkurenci: dict[str, tuple[str, str]] = {}
        for pole, zrodlo in (("konkurenci", "podany"), ("konkurenci_wywnioskowani", "wywnioskowany")):
            for nazwa in firma.get(pole) or []:
                k = self.klucz(nazwa)
                if not k or self.czy_nasza(k) or k in self.konkurenci:
                    continue
                self.konkurenci[k] = (self.nazwy_kanoniczne.get(k, usun_forme_prawna(nazwa) or nazwa), zrodlo)

        # Frazy, które oznaczają konkurenta w treści pytania (do rozpoznawania pytań o markę).
        self.frazy_konkurentow = set(self.mapa_aliasow) | set(self.nazwy_kanoniczne) | set(self.konkurenci)

        self._formy: dict[str, Counter] = {}

    def klucz(self, nazwa: str) -> str:
        k = klucz_nazwy(nazwa)
        if k in self.klucze_naszej:
            return self.klucz_nasz
        return self.mapa_aliasow.get(k, k)

    def czy_nasza(self, klucz: str) -> bool:
        return klucz in self.klucze_naszej

    def zapamietaj_forme(self, klucz: str, nazwa: str) -> None:
        forma = usun_forme_prawna(nazwa) or nazwa.strip()
        self._formy.setdefault(klucz, Counter())[forma] += 1

    def nazwa_wyswietlana(self, klucz: str) -> str:
        if self.czy_nasza(klucz):
            return self.nazwa_firmy
        if klucz in self.nazwy_kanoniczne:
            return self.nazwy_kanoniczne[klucz]
        if klucz in self.konkurenci:
            return self.konkurenci[klucz][0]
        formy = self._formy.get(klucz)
        if not formy:
            return klucz
        # Najczęstsza forma; przy remisie ta z większą liczbą polskich znaków
        # (czyli najpewniej zapis poprawny), a potem pierwsza zapisana.
        kolejnosc = list(formy)
        return max(
            kolejnosc,
            key=lambda f: (formy[f], sum(1 for z in f if ord(z) > 127), -kolejnosc.index(f)),
        )

    def nazwa_w_pytaniu(self, tresc: str) -> list[str]:
        """Warianty nazwy naszej firmy obecne w treści pytania.

        Pomija trafienia, które są częścią nazwy konkurenta obecnej w tym samym
        pytaniu (np. alias "Alfa" w pytaniu o "Alfa Plus", gdy Alfa Plus to konkurent).
        """
        tekst = klucz_nazwy(tresc)
        trafienia = [k for k in self.klucze_naszej if czy_zawiera_fraze(tekst, k)]
        konkurenci_w_pytaniu = [c for c in self.frazy_konkurentow if czy_zawiera_fraze(tekst, c)]
        return sorted(
            k for k in trafienia
            if not any(c != k and czy_zawiera_fraze(c, k) for c in konkurenci_w_pytaniu)
        )

    def podobna_do_naszej(self, klucz: str) -> bool:
        """Heurystyka do ostrzeżeń: nazwa wygląda jak wariant naszej firmy."""
        for nasza in self.klucze_naszej:
            if len(nasza) >= 4 and czy_zawiera_fraze(klucz, nasza):
                return True
            if len(klucz) >= 4 and czy_zawiera_fraze(nasza, klucz):
                return True
            if difflib.SequenceMatcher(None, klucz, nasza).ratio() >= 0.85:
                return True
        return False


# ---------------------------------------------------------------------------
# Liczenie
# ---------------------------------------------------------------------------


@dataclass
class WierszPytania:
    pid: str
    kategoria: str
    tresc: str
    nasza: bool
    pozycja: int | None
    firmy: list[str]
    domeny: list[str]
    nasza_domena: bool
    poprawne: list[str] = field(default_factory=list)
    bledne: list[str] = field(default_factory=list)
    brakujace: list[str] = field(default_factory=list)
    notatka: str = ""


@dataclass
class MetrykiTrybu:
    tryb: str
    etykieta: str
    wiersze: list[WierszPytania] = field(default_factory=list)
    wiersze_marka: list[WierszPytania] = field(default_factory=list)
    pominiete: list[tuple[str, str]] = field(default_factory=list)
    kategorie: dict[str, list[int]] = field(default_factory=dict)
    wzmianki_suma: int = 0
    firmy: dict[str, set[str]] = field(default_factory=dict)
    domeny: dict[str, set[str]] = field(default_factory=dict)
    hosty_profilu: set[str] = field(default_factory=set)

    @property
    def liczba_pytan(self) -> int:
        return len(self.wiersze)

    @property
    def trafienia(self) -> list[WierszPytania]:
        return [w for w in self.wiersze if w.nasza]

    @property
    def widocznosc(self) -> Fraction | None:
        if not self.wiersze:
            return None
        return Fraction(len(self.trafienia), len(self.wiersze))

    @property
    def share_of_voice(self) -> Fraction | None:
        if self.wzmianki_suma == 0:
            return None
        return Fraction(len(self.trafienia), self.wzmianki_suma)

    @property
    def nasza_domena_pytania(self) -> list[str]:
        return [w.pid for w in self.wiersze if w.nasza_domena]

    def zaleznosc_od_zrodel(self, pomin: set[str] | None = None) -> list[tuple[str, int, int]]:
        """Domeny, na których opiera się ponad 1/3 trafień firmy (min. 3 trafienia).

        Zwraca listę (domena, trafienia z tą domeną, wszystkie trafienia).
        Domeny z `pomin` (np. własna strona firmy) nie są brane pod uwagę.
        """
        trafienia = self.trafienia
        if len(trafienia) < 3:
            return []
        licznik: Counter = Counter()
        for w in trafienia:
            for d in w.domeny:
                if d not in (pomin or set()):
                    licznik[d] += 1
        wynik = [
            (d, ile, len(trafienia)) for d, ile in licznik.items()
            if Fraction(ile, len(trafienia)) > Fraction(1, 3)
        ]
        return sorted(wynik, key=lambda x: (-x[1], x[0]))


@dataclass
class Wynik:
    nazwa_firmy: str
    data: str
    domena_firmy: str | None
    profil_firmy: bool
    tryby: dict[str, MetrykiTrybu]
    liczba_pytan: int
    liczba_niebrandowych: int
    liczba_brandowych: int
    ostrzezenia: list[str]
    tresci: dict[str, str]
    rozpoznawacz: Rozpoznawacz
    pytania_niebrandowe: list[str] = field(default_factory=list)
    pytania_marka: list[str] = field(default_factory=list)
    wpisy: dict[str, set[str]] = field(default_factory=dict)
    technika: list[dict[str, str]] = field(default_factory=list)
    technika_data: str = ""

    @property
    def tryb_glowny(self) -> MetrykiTrybu | None:
        """Tryb wyniku głównego.

        Kolejność: wyszukiwanie; potem tryb z odpowiedziami wklejonymi przez
        użytkownika (prawdziwe dane z ChatGPT itd.) z największą liczbą
        sprawdzonych pytań; potem inne tryby; pamięć modelu na końcu.
        """
        z_danymi = [m for m in self.tryby.values() if m.wiersze]
        if not z_danymi:
            return None
        for m in z_danymi:
            if m.tryb == TRYB_GLOWNY:
                return m
        reczne = [m for m in z_danymi if m.tryb in TRYBY_RECZNE]
        if reczne:
            return max(reczne, key=lambda m: (m.liczba_pytan, -TRYBY_RECZNE.index(m.tryb)))
        inne = [m for m in z_danymi if m.tryb != "pamiec"]
        return inne[0] if inne else z_danymi[0]

    def niekompletne(self) -> tuple[list[str], list[str]]:
        """Pytania (niebrandowe, o markę) bez żadnego wpisu w trybie głównym."""
        glowny = self.tryb_glowny
        if glowny is None:
            return (list(self.pytania_niebrandowe), [])
        brak_n = [p for p in self.pytania_niebrandowe if glowny.tryb not in self.wpisy.get(p, set())]
        brak_m = [p for p in self.pytania_marka if glowny.tryb not in self.wpisy.get(p, set())]
        return (brak_n, brak_m)


def adres_firmy(firma: dict) -> tuple[str, str] | None:
    """(domena, ścieżka profilu) strony firmy. Ścieżka tylko dla platform."""
    for pole in ("domena", "strona"):
        if isinstance(firma.get(pole), str) and firma[pole].strip():
            adres = adres_zrodla(firma[pole])
            if adres is None:
                return None
            domena, sciezka = adres
            return (domena, sciezka if _czy_platforma(domena) else "")
    return None


def domena_firmy(firma: dict) -> str | None:
    adres = adres_firmy(firma)
    return adres[0] if adres else None


def _czy_zrodlo_firmy(zrodlo: tuple[str, str], firma: tuple[str, str]) -> bool:
    """Czy źródło to strona firmy (albo jej profil, gdy firma ma tylko profil na platformie).

    Profil porównujemy po pełnej ścieżce: źródło musi być tym samym profilem albo
    jego podstroną, np. "booksy.com/pl-pl/123_salon" i ".../123_salon/opinie".
    """
    domena, sciezka = zrodlo
    nasza, nasza_sciezka = firma
    if nasza == "google.com/maps":
        return False  # profilu w Mapach nie da się wiarygodnie dopasować po adresie
    if not (domena == nasza or domena.endswith("." + nasza)):
        return False
    if nasza_sciezka:
        return sciezka == nasza_sciezka or sciezka.startswith(nasza_sciezka + "/")
    return True


def _kolejnosc_trybow(tryby: list[str]) -> list[str]:
    znane = [t for t in TRYBY if t in tryby]
    inne = [t for t in tryby if t not in TRYBY]
    return znane + inne


def zbuduj_rozpoznawacz(*zbiory_danych: dict) -> Rozpoznawacz:
    """Rozpoznawacz z połączonymi aliasami (ważne przy porównaniu dwóch plików).

    Pierwszy zbiór danych ma pierwszeństwo przy konfliktach.
    """
    glowny = zbiory_danych[0]
    firma = dict(glowny["firma"])
    aliasy: list[str] = []
    konkurenci: list[str] = []
    wywnioskowani: list[str] = []
    aliasy_firm: dict[str, list[str]] = {}
    for dane in reversed(zbiory_danych):
        aliasy.extend(dane["firma"].get("aliasy") or [])
        konkurenci.extend(dane["firma"].get("konkurenci") or [])
        wywnioskowani.extend(dane["firma"].get("konkurenci_wywnioskowani") or [])
        for nazwa, warianty in (dane.get("aliasy_firm") or {}).items():
            aliasy_firm[nazwa] = list(warianty or [])
        if dane is not glowny:
            aliasy.append(dane["firma"]["nazwa"])
    firma["aliasy"] = aliasy
    firma["konkurenci"] = list(dict.fromkeys(konkurenci))
    firma["konkurenci_wywnioskowani"] = list(dict.fromkeys(wywnioskowani))
    return Rozpoznawacz(firma, aliasy_firm)


def policz(dane: dict, rozpoznawacz: Rozpoznawacz | None = None) -> Wynik:
    """Liczy wszystkie metryki z poprawnych (zwalidowanych) danych."""
    firma = dane["firma"]
    rozp = rozpoznawacz or zbuduj_rozpoznawacz(dane)
    nasz_adres = adres_firmy(firma)
    profil = bool(nasz_adres and nasz_adres[1])
    ostrzezenia: list[str] = list(rozp.ostrzezenia)
    tryby: dict[str, MetrykiTrybu] = {}
    tresci: dict[str, str] = {}
    niebrandowe = brandowe = 0
    podejrzane_nazwy: dict[str, set[str]] = {}
    dziwne_zrodla: set[str] = set()
    za_dlugie: list[str] = []
    pytania_niebrandowe: list[str] = []
    pytania_marka: list[str] = []
    wpisy: dict[str, set[str]] = {}

    wszystkie_tryby: list[str] = []
    for pytanie in dane["pytania"]:
        for tryb in (pytanie.get("wyniki") or {}):
            if tryb not in wszystkie_tryby:
                wszystkie_tryby.append(tryb)
    for tryb in _kolejnosc_trybow(wszystkie_tryby):
        tryby[tryb] = MetrykiTrybu(tryb, TRYBY.get(tryb, tryb))

    for pytanie in dane["pytania"]:
        pid = str(pytanie["id"])
        tresc = pytanie["tresc"].strip()
        tresci[pid] = tresc
        kategoria = pytanie["kategoria"].strip().lower()
        if kategoria not in KATEGORIE:
            ostrzezenia.append(
                f"Pytanie {pid}: nieznana kategoria \"{kategoria}\". Liczę ją pod tą nazwą. "
                f"Znane kategorie: {', '.join(KATEGORIE)}."
            )
        marka = kategoria == KATEGORIA_MARKA
        if not marka and rozp.nazwa_w_pytaniu(tresc):
            if rozp.nazwa_opisowa:
                ostrzezenia.append(
                    f"Pytanie {pid} zawiera opisową nazwę Twojej firmy (firma.nazwa_opisowa = true), "
                    "więc zostawiam je wśród pytań niebrandowych. Sprawdź, czy nie faworyzuje Twojej firmy."
                )
            else:
                ostrzezenia.append(
                    f"Pytanie {pid} zawiera nazwę Twojej firmy, więc liczę je jako pytanie o markę "
                    "(nie wchodzi do wskaźnika widoczności). Pytania niebrandowe nie powinny "
                    "zawierać nazwy firmy. Jeśli nazwa firmy to zwykłe słowa (np. \"Fizjoterapia "
                    "Lublin\"), ustaw firma.nazwa_opisowa na true."
                )
                marka = True
        if marka:
            brandowe += 1
            pytania_marka.append(pid)
        else:
            niebrandowe += 1
            pytania_niebrandowe.append(pid)

        wyniki = pytanie.get("wyniki") or {}
        wpisy[pid] = set(wyniki)
        if not wyniki:
            ostrzezenia.append(f"Pytanie {pid} nie ma żadnych wyników, więc nie jest liczone.")

        for tryb, wynik in wyniki.items():
            m = tryby[tryb]
            if "blad" in wynik:
                if not marka:
                    m.pominiete.append((pid, str(wynik.get("blad") or "bez opisu")))
                continue

            klucze: list[str] = []
            for nazwa in wynik.get("firmy") or []:
                if not nazwa.strip():
                    continue
                k = rozp.klucz(nazwa)
                if not k:
                    continue
                rozp.zapamietaj_forme(k, nazwa)
                if k not in klucze:
                    klucze.append(k)
                if not rozp.czy_nasza(k) and rozp.podobna_do_naszej(k):
                    podejrzane_nazwy.setdefault(nazwa.strip(), set()).add(pid)
            if len(klucze) > MAKS_FIRM:
                za_dlugie.append(f"{pid} ({m.etykieta}: {ile_slownie(len(klucze), 'firma', 'firmy', 'firm')})")

            domeny: list[str] = []
            nasze_zrodlo = False
            for zrodlo in wynik.get("zrodla") or []:
                adres = adres_zrodla(zrodlo)
                if adres is None:
                    if zrodlo.strip():
                        dziwne_zrodla.add(zrodlo.strip())
                    continue
                if nasz_adres and _czy_zrodlo_firmy(adres, nasz_adres):
                    nasze_zrodlo = True
                    if profil:
                        m.hosty_profilu.add(adres[0])
                if adres[0] not in domeny:
                    domeny.append(adres[0])

            pozycja = None
            for indeks, k in enumerate(klucze, start=1):
                if rozp.czy_nasza(k):
                    pozycja = indeks
                    break
            wiersz = WierszPytania(
                pid=pid,
                kategoria=kategoria,
                tresc=tresc,
                nasza=pozycja is not None,
                pozycja=pozycja,
                firmy=klucze,
                domeny=domeny,
                nasza_domena=nasze_zrodlo,
                poprawne=list(wynik.get("poprawne") or []),
                bledne=list(wynik.get("bledne") or []),
                brakujace=list(wynik.get("brakujace") or []),
                notatka=str(wynik.get("notatka") or ""),
            )
            if marka:
                m.wiersze_marka.append(wiersz)
                continue

            m.wiersze.append(wiersz)
            licznik = m.kategorie.setdefault(kategoria, [0, 0])
            licznik[0] += 1
            if wiersz.nasza:
                licznik[1] += 1
            m.wzmianki_suma += len(klucze)
            for k in klucze:
                if not rozp.czy_nasza(k):
                    m.firmy.setdefault(k, set()).add(pid)
            for d in domeny:
                m.domeny.setdefault(d, set()).add(pid)

    for m in tryby.values():
        if m.pominiete and not m.wiersze:
            ostrzezenia.append(
                f"Wszystkie wyniki pytań niebrandowych w trybie \"{m.etykieta}\" to błędy, więc dla "
                "tego trybu nie da się policzyć widoczności. Powody są w sekcji \"Pytanie po pytaniu\"."
            )
    for nazwa, pids in sorted(podejrzane_nazwy.items()):
        ostrzezenia.append(
            f"Nazwa \"{nazwa}\" (pytania: {', '.join(sorted(pids))}) wygląda podobnie do Twojej "
            "firmy, ale nie jest liczona jako Ty. Jeśli to Twoja firma (np. odmieniona nazwa), "
            "dopisz ją do firma.aliasy albo zapisz w mianowniku i uruchom skrypt ponownie."
        )
    if za_dlugie:
        ostrzezenia.append(
            f"Więcej niż {MAKS_FIRM} firm w odpowiedzi: {', '.join(za_dlugie)}. Zasada skilla to najwyżej "
            f"{MAKS_FIRM} firm na pytanie, bo dłuższe listy sztucznie zaniżają udział w odpowiedziach."
        )
    if dziwne_zrodla:
        przyklady = ", ".join(sorted(dziwne_zrodla)[:5])
        ostrzezenia.append(
            f"Niektóre źródła nie wyglądają na adres strony i są pominięte w rankingu domen: {przyklady}. "
            "Zapisuj źródła jako pełne adresy URL albo domeny."
        )
    if not nasz_adres:
        ostrzezenia.append(
            "Brak firma.strona, więc nie da się sprawdzić, czy AI cytował stronę firmy."
        )
    elif nasz_adres[0] == "google.com/maps":
        ostrzezenia.append(
            "Strona firmy to wizytówka w Mapach Google. Cytowania profilu w Mapach nie da się "
            "wiarygodnie sprawdzić po adresie, więc nie liczę go."
        )
    elif profil:
        ostrzezenia.append(
            f"Strona firmy to profil na platformie ({nasz_adres[0]}), więc cytowanie liczę po adresie "
            "profilu, a nie po całej domenie."
        )

    technika, technika_data = _technika(dane.get("technika"), ostrzezenia)

    return Wynik(
        nazwa_firmy=rozp.nazwa_firmy,
        data=str(dane.get("data") or "brak daty"),
        domena_firmy=nasz_adres[0] if nasz_adres else None,
        profil_firmy=profil,
        tryby=tryby,
        liczba_pytan=len(dane["pytania"]),
        liczba_niebrandowych=niebrandowe,
        liczba_brandowych=brandowe,
        ostrzezenia=ostrzezenia,
        tresci=tresci,
        rozpoznawacz=rozp,
        pytania_niebrandowe=pytania_niebrandowe,
        pytania_marka=pytania_marka,
        wpisy=wpisy,
        technika=technika,
        technika_data=technika_data,
    )


def _technika(wartosc: object, ostrzezenia: list[str]) -> tuple[list[dict[str, str]], str]:
    """Odczytuje opcjonalne pole "technika" (wyniki checku technicznego).

    Format: {"data": "RRRR-MM-DD", "elementy": [{"element": "...", "stan": "...",
    "opis": "..."}]}. Pole nie wpływa na metryki; jest tylko wypisywane.
    """
    if wartosc is None:
        return ([], "")
    elementy = wartosc.get("elementy") if isinstance(wartosc, dict) else None
    if not isinstance(elementy, list) or not all(
            isinstance(e, dict) and isinstance(e.get("element"), str) for e in elementy):
        ostrzezenia.append(
            "Pole \"technika\" ma nieznany format, więc go nie wypisuję. Oczekiwany format: "
            "{\"data\": \"RRRR-MM-DD\", \"elementy\": [{\"element\": \"...\", \"stan\": \"...\", \"opis\": \"...\"}]}."
        )
        return ([], "")
    wynik = [{k: str(e.get(k) or "") for k in ("element", "stan", "opis")} for e in elementy]
    return (wynik, str(wartosc.get("data") or ""))


# ---------------------------------------------------------------------------
# Formatowanie
# ---------------------------------------------------------------------------


def _zaokraglij(wartosc: Fraction) -> Decimal:
    return (Decimal(wartosc.numerator) / Decimal(wartosc.denominator)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )


def liczba_pl(wartosc: Decimal) -> str:
    if wartosc == wartosc.to_integral_value():
        return str(int(wartosc))
    return str(wartosc).replace(".", ",")


def odmiana(liczba: int, jeden: str, kilka: str, wiele: str) -> str:
    """Polska odmiana rzeczownika po liczebniku: 1 pytanie, 2 pytania, 5 pytań, 22 pytania."""
    if liczba == 1:
        return jeden
    if liczba % 10 in (2, 3, 4) and liczba % 100 not in (12, 13, 14):
        return kilka
    return wiele


def ile_slownie(liczba: int, jeden: str, kilka: str, wiele: str) -> str:
    """Np. ile_slownie(5, "pytanie", "pytania", "pytań") -> "5 pytań"."""
    return f"{liczba} {odmiana(liczba, jeden, kilka, wiele)}"


def ile_pytan(liczba: int) -> str:
    return ile_slownie(liczba, "pytanie", "pytania", "pytań")


def ile_razy(liczba: int) -> str:
    return f"{liczba} {'raz' if liczba == 1 else 'razy'}"


def procent(ulamek: Fraction | None) -> str:
    """Np. Fraction(1, 7) -> "14,3%". Brak danych -> "-"."""
    if ulamek is None:
        return "-"
    return liczba_pl(_zaokraglij(ulamek * 100)) + "%"


def srednia_pozycja(pozycje: list[int]) -> str:
    """Średnia z jednym miejscem po przecinku, np. "1,0" albo "2,8"."""
    if not pozycje:
        return "-"
    return str(_zaokraglij(Fraction(sum(pozycje), len(pozycje)))).replace(".", ",")


def zmiana_pp(nowa: Fraction | None, stara: Fraction | None) -> str:
    """Różnica w punktach procentowych, np. "+10 p.p.", "-3,3 p.p.", "bez zmian"."""
    if nowa is None or stara is None:
        return "brak danych do porównania"
    roznica = _zaokraglij((nowa - stara) * 100)
    if roznica == 0:
        return "bez zmian"
    znak = "+" if roznica > 0 else "-"
    return f"{znak}{liczba_pl(abs(roznica))} p.p."


def ocena(ulamek: Fraction | None) -> str:
    """Robocza interpretacja wskaźnika widoczności (heurystyka, nie standard)."""
    if ulamek is None:
        return "brak danych"
    if ulamek == 0:
        return "niewidoczny"
    if ulamek < Fraction(15, 100):
        return "słabo"
    if ulamek <= Fraction(40, 100):
        return "średnio"
    return "mocno"


def prog_zmiennosci(liczba_pytan: int) -> int:
    """Ile pytań to około 20 p.p., czyli zmiana, którą traktujemy jako możliwą zmienność."""
    return max(1, math.ceil(liczba_pytan * 0.2))


def komorka(tekst: str) -> str:
    """Zabezpiecza tekst do komórki tabeli Markdown."""
    return _SPACJE.sub(" ", str(tekst)).replace("|", "\\|").strip() or "-"


def etykieta_kategorii(kategoria: str) -> str:
    return KATEGORIE.get(kategoria, kategoria)


def _ranking(slownik: dict[str, set[str]]) -> list[tuple[str, int]]:
    return sorted(((k, len(v)) for k, v in slownik.items()), key=lambda x: (-x[1], x[0]))


def _remisy(ranking: list[tuple[str, int]], top: int) -> list[tuple[str, int]]:
    """Pozycje spoza top-N z takim samym wynikiem jak ostatnia pokazana."""
    if len(ranking) <= top:
        return []
    granica = ranking[top - 1][1]
    return [(k, ile) for k, ile in ranking[top:] if ile == granica]


def _linia_remisow(remisy: list[tuple[str, int]], nazwa, ile_razem: int) -> str:
    nazwy = [nazwa(k) for k, _ in remisy]
    pokazane = ", ".join(nazwy[:10])
    reszta = len(nazwy) - 10
    dopisek = f" i {reszta} innych" if reszta > 0 else ""
    return (f"Z tym samym wynikiem co ostatnia pozycja ({remisy[0][1]}): {pokazane}{dopisek}. "
            f"Wszystkich pozycji: {ile_razem}.")


def renderuj(wynik: Wynik, top: int, porownanie: list[str] | None = None) -> str:
    """Składa raport z metrykami w Markdown."""
    rozp = wynik.rozpoznawacz
    nazwa = rozp.nazwa_wyswietlana
    linie: list[str] = []
    dodaj = linie.append

    dodaj(f"# Metryki widoczności w AI: {wynik.nazwa_firmy}")
    dodaj("")
    glowny = wynik.tryb_glowny
    naglowek = f"Data badania: {wynik.data}. Pytania niebrandowe: {wynik.liczba_niebrandowych}"
    if glowny is not None:
        bez_wyniku = wynik.liczba_niebrandowych - glowny.liczba_pytan - len(glowny.pominiete)
        naglowek += (f" (w trybie głównym sprawdzone: {glowny.liczba_pytan}, z błędem: "
                     f"{len(glowny.pominiete)}, bez wyniku: {max(0, bez_wyniku)})")
    dodaj(naglowek + f". Pytania o markę: {wynik.liczba_brandowych}.")
    dodaj("")
    ostrzezenie = ostrzezenie_niekompletny(wynik)
    if ostrzezenie:
        dodaj(f"> **{ostrzezenie}**")
        dodaj("")

    dodaj("## Wynik główny")
    dodaj("")
    if glowny is None:
        dodaj("Brak wyników dla pytań niebrandowych, więc nie da się policzyć widoczności.")
    else:
        w = glowny.widocznosc
        dodaj(f"**Pojawiasz się w {len(glowny.trafienia)} z {glowny.liczba_pytan} odpowiedzi "
              f"({procent(w)}).** Tryb: {glowny.etykieta}.")
        dodaj("")
        dodaj(f"Ocena robocza: **{ocena(w)}**. Progi to heurystyka autora skilla, nie standard branżowy: "
              "0% niewidoczny, poniżej 15% słabo, 15-40% średnio, powyżej 40% mocno.")
    dodaj("")

    dodaj("## Widoczność według trybu")
    dodaj("")
    dodaj("Tryby liczymy osobno, bo mierzą różne rzeczy. Nie sumuj ich w jedną liczbę.")
    dodaj("")
    dodaj("| Tryb | Pytania | Pojawiasz się | Widoczność | Udział w odpowiedziach | Średnia pozycja (informacyjnie) | Pominięte |")
    dodaj("|---|---|---|---|---|---|---|")
    for m in wynik.tryby.values():
        pozycje = [w.pozycja for w in m.trafienia if w.pozycja]
        dodaj(f"| {komorka(m.etykieta)} | {m.liczba_pytan} | {len(m.trafienia)} | "
              f"{procent(m.widocznosc)} | {procent(m.share_of_voice)} | {srednia_pozycja(pozycje)} | "
              f"{len(m.pominiete)} |")
    dodaj("")
    dodaj("Udział w odpowiedziach (share of voice): jaki procent wszystkich wzmianek o firmach "
          "w odpowiedziach przypada na Ciebie.")
    dodaj("")

    kategorie: list[str] = []
    for m in wynik.tryby.values():
        for k in m.kategorie:
            if k not in kategorie:
                kategorie.append(k)
    kategorie.sort(key=lambda k: (list(KATEGORIE).index(k) if k in KATEGORIE else 99, k))
    tryby_z_danymi = [m for m in wynik.tryby.values() if m.wiersze]
    if kategorie:
        dodaj("## Widoczność według kategorii pytań")
        dodaj("")
        dodaj("| Kategoria | " + " | ".join(komorka(m.etykieta) for m in tryby_z_danymi) + " |")
        dodaj("|---|" + "---|" * len(tryby_z_danymi))
        for k in kategorie:
            komorki = []
            for m in tryby_z_danymi:
                if k in m.kategorie:
                    n, t = m.kategorie[k]
                    komorki.append(f"{t} z {n} ({procent(Fraction(t, n))})")
                else:
                    komorki.append("-")
            dodaj(f"| {komorka(etykieta_kategorii(k))} | " + " | ".join(komorki) + " |")
        dodaj("")

    for m in tryby_z_danymi:
        dodaj(f"## Kto pojawia się w odpowiedziach: {m.etykieta}")
        dodaj("")
        ranking = _ranking(m.firmy)
        dodaj("| # | Firma | W ilu pytaniach | % pytań |")
        dodaj("|---|---|---|---|")
        nasze = len(m.trafienia)
        wstawiono_nas = False
        for lp, (k, ile) in enumerate(ranking[:top], start=1):
            if not wstawiono_nas and nasze >= ile and nasze > 0:
                dodaj(f"| - | **{komorka(wynik.nazwa_firmy)} (Ty)** | {nasze} | "
                      f"{procent(Fraction(nasze, m.liczba_pytan))} |")
                wstawiono_nas = True
            dopisek = ""
            if k in rozp.konkurenci:
                dopisek = (" (konkurent podany przez Ciebie)" if rozp.konkurenci[k][1] == "podany"
                           else " (konkurent wskazany przez Claude)")
            dodaj(f"| {lp} | {komorka(nazwa(k))}{dopisek} | {ile} | "
                  f"{procent(Fraction(ile, m.liczba_pytan))} |")
        if not wstawiono_nas:
            dodaj(f"| - | **{komorka(wynik.nazwa_firmy)} (Ty)** | {nasze} | "
                  f"{procent(Fraction(nasze, m.liczba_pytan))} |")
        if not ranking:
            dodaj("")
            dodaj("W odpowiedziach nie wymieniono żadnej innej firmy.")
        elif len(ranking) > top:
            dodaj("")
            remisy = _remisy(ranking, top)
            if remisy:
                dodaj(_linia_remisow(remisy, nazwa, len(ranking)))
            else:
                dodaj(f"Pokazano {top} z {len(ranking)} firm.")
        nieobecni = [n for k, (n, _) in rozp.konkurenci.items() if k not in m.firmy]
        if nieobecni:
            dodaj("")
            dodaj("Konkurenci z listy, którzy nie pojawili się ani razu w tym trybie: "
                  + ", ".join(sorted(nieobecni)) + ".")
        dodaj("")

    for m in wynik.tryby.values():
        if not m.domeny:
            continue
        dodaj(f"## Skąd AI brał informacje: {m.etykieta}")
        dodaj("")
        dodaj("Liczba pytań niebrandowych, w których dana domena była źródłem.")
        dodaj("")
        dodaj("| # | Domena | W ilu pytaniach | % pytań |")
        dodaj("|---|---|---|---|")
        ranking_domen = _ranking(m.domeny)
        for lp, (d, ile) in enumerate(ranking_domen[:top], start=1):
            dopisek = ""
            if wynik.domena_firmy and not wynik.profil_firmy and (
                    d == wynik.domena_firmy or d.endswith("." + wynik.domena_firmy)):
                dopisek = " **(Twoja strona)**"
            elif d in m.hosty_profilu:
                dopisek = " (w tym Twój profil)"
            dodaj(f"| {lp} | {komorka(d)}{dopisek} | {ile} | {procent(Fraction(ile, m.liczba_pytan))} |")
        remisy = _remisy(ranking_domen, top)
        if remisy:
            dodaj("")
            dodaj(_linia_remisow(remisy, lambda d: d, len(ranking_domen)))
        dodaj("")
        if wynik.domena_firmy:
            ile_nasza = len(m.nasza_domena_pytania)
            rodzaj = "był Twój profil" if wynik.profil_firmy else "była Twoja strona"
            dodaj(f"Pytania niebrandowe, w których wśród źródeł {rodzaj} "
                  f"({wynik.domena_firmy}): {ile_nasza} z {m.liczba_pytan} "
                  f"({procent(Fraction(ile_nasza, m.liczba_pytan))}).")
            dodaj("")
        pomin = set() if (wynik.profil_firmy or not wynik.domena_firmy) else {
            d for d in m.domeny if d == wynik.domena_firmy or d.endswith("." + wynik.domena_firmy)}
        zaleznosci = m.zaleznosc_od_zrodel(pomin)
        if zaleznosci:
            razem = zaleznosci[0][2]
            opis = ", ".join(f"{d} ({ile} z {razem})" for d, ile, _ in zaleznosci)
            dodaj(f"Zależność od pojedynczych źródeł: ponad 1/3 z {razem} Twoich trafień w tym trybie "
                  f"opiera się na: {opis}. Jeśli takie źródło się zmieni albo zniknie, wynik może "
                  "wyraźnie spaść.")
            dodaj("")

    if any(m.wiersze_marka for m in wynik.tryby.values()):
        dodaj("## Pytania o Twoją markę (liczone osobno)")
        dodaj("")
        dodaj("Te pytania zawierają nazwę firmy, więc nie wchodzą do wskaźnika widoczności. "
              "Sprawdzają, czy AI wie o Tobie poprawne rzeczy.")
        dodaj("")
        for pid, tresc in wynik.tresci.items():
            wiersze = [(m, w) for m in wynik.tryby.values() for w in m.wiersze_marka if w.pid == pid]
            if not wiersze:
                continue
            dodaj(f"### {pid}. {tresc}")
            dodaj("")
            for m, w in wiersze:
                if not wynik.domena_firmy:
                    cytowana = "nie sprawdzono (brak adresu strony)"
                elif not w.domeny:
                    cytowana = "brak źródeł w tym trybie"
                else:
                    cytowana = "tak" if w.nasza_domena else "nie"
                dodaj(f"{m.etykieta}:")
                dodaj("")
                dodaj(f"- AI wymienił Twoją firmę: {'tak' if w.nasza else 'nie'}. "
                      f"Twoja strona wśród źródeł: {cytowana}.")
                if w.poprawne:
                    dodaj("- Poprawne: " + "; ".join(w.poprawne))
                if w.bledne:
                    dodaj("- Błędne: " + "; ".join(w.bledne))
                if w.brakujace:
                    dodaj("- Brakuje: " + "; ".join(w.brakujace))
                if w.notatka:
                    dodaj("- Notatka: " + w.notatka)
                dodaj("")

    for m in wynik.tryby.values():
        if not m.wiersze and not m.pominiete:
            continue
        dodaj(f"## Pytanie po pytaniu: {m.etykieta}")
        dodaj("")
        if m.wiersze:
            dodaj("| # | Kategoria | Pytanie | Jesteś na liście? | Poz. | Kogo wymieniono | Źródła |")
            dodaj("|---|---|---|---|---|---|---|")
            for w in m.wiersze:
                firmy = ", ".join(f"**{wynik.nazwa_firmy}**" if rozp.czy_nasza(k) else nazwa(k)
                                  for k in w.firmy) or "nikt"
                dodaj(f"| {w.pid} | {komorka(etykieta_kategorii(w.kategoria))} | {komorka(w.tresc)} | "
                      f"{'tak' if w.nasza else 'nie'} | {w.pozycja or '-'} | {komorka(firmy)} | "
                      f"{komorka(', '.join(w.domeny) or '-')} |")
        else:
            dodaj("Brak sprawdzonych pytań niebrandowych w tym trybie.")
        if m.pominiete:
            dodaj("")
            dodaj("Pominięte (nie liczone): " + "; ".join(f"{pid}: {powod}" for pid, powod in m.pominiete))
        dodaj("")

    if wynik.technika:
        dodaj("## Check techniczny (zapisany w pliku wyników)" + (f", {wynik.technika_data}" if wynik.technika_data else ""))
        dodaj("")
        dodaj("| Element | Stan | Co to znaczy |")
        dodaj("|---|---|---|")
        for e in wynik.technika:
            dodaj(f"| {komorka(e['element'])} | {komorka(e['stan'])} | {komorka(e['opis'])} |")
        dodaj("")

    if porownanie:
        linie.extend(porownanie)

    if wynik.ostrzezenia:
        dodaj("## Uwagi do danych")
        dodaj("")
        for o in wynik.ostrzezenia:
            dodaj(f"- {o}")
        dodaj("")

    return "\n".join(linie).rstrip() + "\n"


def ostrzezenie_niekompletny(wynik: Wynik) -> str:
    """Ostrzeżenie, gdy w trybie głównym brakuje wyników części pytań."""
    brak_n, brak_m = wynik.niekompletne()
    if not brak_n and not brak_m:
        return ""
    glowny = wynik.tryb_glowny
    etykieta = glowny.etykieta if glowny else "żadnym"
    czesci = []
    if brak_n:
        przymiotnik = odmiana(len(brak_n), "niebrandowe", "niebrandowe", "niebrandowych")
        czesci.append(f"{ile_pytan(len(brak_n))} {przymiotnik} bez wyniku ({', '.join(brak_n)})")
    if brak_m:
        czesci.append(f"{ile_pytan(len(brak_m))} o markę bez wyniku ({', '.join(brak_m)})")
    return (f"Test niekompletny: {' oraz '.join(czesci)} w trybie \"{etykieta}\". "
            "Dokończ test (ścieżka Kontynuacja), zanim napiszesz raport.")


def podsumowanie(wynik: Wynik, sciezka_md: str, porownanie: bool) -> str:
    """Krótki tekst na standardowe wyjście, gdy pełny raport poszedł do pliku."""
    linie = [f"Metryki widoczności w AI: {wynik.nazwa_firmy} ({wynik.data})"]
    ostrzezenie = ostrzezenie_niekompletny(wynik)
    if ostrzezenie:
        linie.append(f"UWAGA. {ostrzezenie}")
    for m in wynik.tryby.values():
        if m.wiersze:
            linie.append(f"- {m.etykieta}: {len(m.trafienia)} z {m.liczba_pytan} "
                         f"({procent(m.widocznosc)}), udział w odpowiedziach {procent(m.share_of_voice)}, "
                         f"ocena robocza: {ocena(m.widocznosc)}")
        elif m.pominiete:
            linie.append(f"- {m.etykieta}: brak sprawdzonych pytań ({len(m.pominiete)} z błędem)")
    if porownanie:
        linie.append("- Porównanie z poprzednim badaniem: w pliku raportu.")
    if wynik.ostrzezenia:
        linie.append(f"- Uwagi do danych: {len(wynik.ostrzezenia)} (przeczytaj je w pliku raportu).")
    linie.append(f"Pełny raport z metrykami: {sciezka_md}")
    return "\n".join(linie) + "\n"


# ---------------------------------------------------------------------------
# Porównanie z poprzednim plikiem
# ---------------------------------------------------------------------------


def _klucz_tresci(tresc: str) -> str:
    return _SPACJE.sub(" ", tresc.casefold()).strip()


def porownaj(nowy: Wynik, stary: Wynik, top: int) -> list[str]:
    """Sekcja Markdown z porównaniem dwóch badań."""
    linie: list[str] = []
    dodaj = linie.append
    rozp = nowy.rozpoznawacz
    dodaj(f"## Porównanie z poprzednim badaniem ({stary.data})")
    dodaj("")

    tylko_nowe = sorted(set(nowy.tresci) - set(stary.tresci))
    tylko_stare = sorted(set(stary.tresci) - set(nowy.tresci))
    zmienione = sorted(
        pid for pid in set(nowy.tresci) & set(stary.tresci)
        if _klucz_tresci(nowy.tresci[pid]) != _klucz_tresci(stary.tresci[pid])
    )
    if tylko_nowe or tylko_stare or zmienione:
        dodaj("Zestawy pytań się różnią, więc porównanie całościowe jest mniej wiarygodne. "
              "Patrz kolumna \"Na tych samych pytaniach\".")
        if tylko_nowe:
            dodaj(f"- Nowe pytania: {', '.join(tylko_nowe)}")
        if tylko_stare:
            dodaj(f"- Pytania usunięte: {', '.join(tylko_stare)}")
        if zmienione:
            dodaj(f"- Pytania o zmienionej treści (nie porównujemy ich): {', '.join(zmienione)}")
        dodaj("")
    else:
        dodaj("Te same pytania w obu badaniach.")
        dodaj("")

    dodaj("| Tryb | Widoczność wcześniej | Widoczność teraz | Zmiana | Na tych samych pytaniach | Udział w odpowiedziach: zmiana |")
    dodaj("|---|---|---|---|---|---|")
    liczba_wspolnych = 0
    for tryb, m in nowy.tryby.items():
        s = stary.tryby.get(tryb)
        if s is None or not m.wiersze or not s.wiersze:
            continue
        nowe_w = {w.pid: w for w in m.wiersze}
        stare_w = {w.pid: w for w in s.wiersze}
        wspolne = [pid for pid in nowe_w if pid in stare_w and pid not in zmienione]
        if wspolne:
            a = sum(1 for p in wspolne if stare_w[p].nasza)
            b = sum(1 for p in wspolne if nowe_w[p].nasza)
            n = len(wspolne)
            liczba_wspolnych = max(liczba_wspolnych, n)
            wspolne_txt = f"{a} z {n} → {b} z {n} ({zmiana_pp(Fraction(b, n), Fraction(a, n))})"
        else:
            wspolne_txt = "brak wspólnych pytań"
        dodaj(f"| {komorka(m.etykieta)} | {len(s.trafienia)} z {s.liczba_pytan} ({procent(s.widocznosc)}) | "
              f"{len(m.trafienia)} z {m.liczba_pytan} ({procent(m.widocznosc)}) | "
              f"{zmiana_pp(m.widocznosc, s.widocznosc)} | {wspolne_txt} | "
              f"{procent(s.share_of_voice)} → {procent(m.share_of_voice)} "
              f"({zmiana_pp(m.share_of_voice, s.share_of_voice)}) |")
    dodaj("")

    glowny = nowy.tryb_glowny
    if glowny and glowny.tryb in stary.tryby and stary.tryby[glowny.tryb].wiersze:
        s = stary.tryby[glowny.tryb]
        nowe_w = {w.pid: w for w in glowny.wiersze}
        stare_w = {w.pid: w for w in s.wiersze}
        wspolne = [pid for pid in nowe_w if pid in stare_w and pid not in zmienione]
        zyskane = [p for p in wspolne if nowe_w[p].nasza and not stare_w[p].nasza]
        stracone = [p for p in wspolne if stare_w[p].nasza and not nowe_w[p].nasza]
        dodaj(f"### Zmiany pytanie po pytaniu: {glowny.etykieta}")
        dodaj("")
        dodaj("- Pytania, w których teraz się pojawiasz, a wcześniej nie: "
              + (", ".join(zyskane) if zyskane else "brak"))
        dodaj("- Pytania, w których wcześniej się pojawiałeś, a teraz nie: "
              + (", ".join(stracone) if stracone else "brak"))
        if nowy.domena_firmy:
            dodaj(f"- Pytania, w których źródłem była Twoja strona: wcześniej {len(s.nasza_domena_pytania)}, "
                  f"teraz {len(glowny.nasza_domena_pytania)}")
        dodaj("")

        klucze = [k for k, _ in _ranking(glowny.firmy)[:top]]
        for k, _ in _ranking(s.firmy)[:top]:
            if k not in klucze:
                klucze.append(k)
        if klucze:
            dodaj(f"### Firmy w odpowiedziach: wcześniej i teraz ({glowny.etykieta})")
            dodaj("")
            dodaj("| Firma | Wcześniej (pytania) | Teraz (pytania) | Zmiana |")
            dodaj("|---|---|---|---|")
            for k in sorted(klucze, key=lambda k: (-len(glowny.firmy.get(k, ())), k)):
                a = len(s.firmy.get(k, ()))
                b = len(glowny.firmy.get(k, ()))
                roznica = b - a
                znak = f"+{roznica}" if roznica > 0 else str(roznica) if roznica < 0 else "0"
                dodaj(f"| {komorka(rozp.nazwa_wyswietlana(k))} | {a} | {b} | {znak} |")
            dodaj("")

    n = liczba_wspolnych or (glowny.liczba_pytan if glowny else 0)
    if n:
        dodaj(f"Pamiętaj: przy {n} {'pytaniu' if n == 1 else 'pytaniach'} jedno pytanie to "
              f"{liczba_pl(_zaokraglij(Fraction(100, n)))} p.p. "
              f"Zmiana o najwyżej {ile_pytan(prog_zmiennosci(n))} (około 20 p.p.) może być zwykłą "
              "zmiennością odpowiedzi AI, a nie efektem Twoich działań. Patrz na trend z kilku miesięcy "
              "i na konkretne pytania, które się zmieniły.")
        dodaj("")
    return linie


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _spolszcz_argparse() -> None:
    """Tłumaczy najczęstsze komunikaty argparse na polski (bez wpływu na logikę)."""
    tlumaczenia = {
        "usage: ": "użycie: ",
        "positional arguments": "argumenty",
        "options": "opcje",
        "optional arguments": "opcje",
        "show this help message and exit": "pokaż tę pomoc i zakończ",
    }
    oryginal = getattr(argparse, "_", None)
    if callable(oryginal) and not getattr(oryginal, "_spolszczone", False):
        def tlumacz(tekst: str) -> str:
            return tlumaczenia.get(tekst, oryginal(tekst))
        tlumacz._spolszczone = True  # type: ignore[attr-defined]
        argparse._ = tlumacz  # type: ignore[attr-defined]


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        self.print_usage(sys.stderr)
        komunikat = (message.replace("the following arguments are required", "brakuje argumentów")
                     .replace("unrecognized arguments", "nieznane argumenty")
                     .replace("expected one argument", "oczekiwano jednej wartości")
                     .replace("invalid int value", "to nie jest liczba całkowita"))
        sys.stderr.write(f"Błąd: {komunikat}\n")
        sys.exit(2)


def zbuduj_parser() -> argparse.ArgumentParser:
    _spolszcz_argparse()
    parser = _Parser(
        prog="licz_wynik.py",
        description="Liczy metryki widoczności firmy w odpowiedziach AI z pliku wyników JSON "
                    "i wypisuje raport w Markdown.",
    )
    parser.add_argument("wyniki", help="plik wyników JSON z bieżącego badania")
    parser.add_argument("--poprzedni", metavar="STARY.json",
                        help="plik wyników z poprzedniego badania, do porównania")
    parser.add_argument("--md", metavar="PLIK.md",
                        help="zapisz pełny raport do pliku; na ekranie tylko krótkie podsumowanie")
    parser.add_argument("--top", type=int, default=10, metavar="N",
                        help="ile firm i domen pokazać w rankingach (domyślnie 10)")
    return parser


def _wczytaj_i_sprawdz(sciezka: Path, etykieta: str) -> dict:
    dane = wczytaj_json(sciezka)
    bledy = waliduj(dane)
    if bledy:
        raise BladDanych([f"{etykieta} ({sciezka}) zawiera błędy:"] + [f"  - {b}" for b in bledy[:25]]
                         + ([f"  ... i {len(bledy) - 25} więcej."] if len(bledy) > 25 else []))
    return dane  # type: ignore[return-value]


def main(argv: list[str] | None = None) -> int:
    for strumien in (sys.stdout, sys.stderr):
        try:
            strumien.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass

    args = zbuduj_parser().parse_args(argv)
    if args.top < 1:
        sys.stderr.write("Błąd: --top musi być liczbą większą od zera.\n")
        return 2
    try:
        dane = _wczytaj_i_sprawdz(Path(args.wyniki), "Plik wyników")
        porownanie = None
        if args.poprzedni:
            stare = _wczytaj_i_sprawdz(Path(args.poprzedni), "Plik poprzedni")
            rozp = zbuduj_rozpoznawacz(dane, stare)
            wynik = policz(dane, rozp)
            wynik_stary = policz(stare, rozp)
            nazwy_teraz = {klucz_nazwy(n) for n in [dane["firma"]["nazwa"], *(dane["firma"].get("aliasy") or [])]}
            if klucz_nazwy(stare["firma"]["nazwa"]) not in nazwy_teraz:
                wynik.ostrzezenia.append("Plik poprzedni dotyczy firmy o innej nazwie. Sprawdź, czy to właściwy plik.")
            porownanie = porownaj(wynik, wynik_stary, args.top)
        else:
            wynik = policz(dane)
    except BladDanych as blad:
        sys.stderr.write("\n".join(blad.komunikaty) + "\n")
        return 1

    raport = renderuj(wynik, args.top, porownanie)
    if args.md:
        try:
            Path(args.md).write_text(raport, encoding="utf-8")
        except OSError as blad:
            sys.stderr.write(f"Nie udało się zapisać pliku {args.md}: {blad}\n")
            return 1
        sys.stdout.write(podsumowanie(wynik, args.md, porownanie is not None))
    else:
        sys.stdout.write(raport)
    return 0


if __name__ == "__main__":
    sys.exit(main())
