"""Testy skryptu licz_wynik.py na fikcyjnych danych z assets/wyniki_przyklad.json.

Uruchomienie z głównego folderu repozytorium:
    python -m unittest discover -s testy -v

Oczekiwane liczby zostały policzone ręcznie (opis w komentarzach przy testach).
"""

import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKRYPT = REPO / "widocznosc-w-ai" / "scripts" / "licz_wynik.py"
PRZYKLAD = REPO / "widocznosc-w-ai" / "assets" / "wyniki_przyklad.json"

_spec = importlib.util.spec_from_file_location("licz_wynik", SKRYPT)
lw = importlib.util.module_from_spec(_spec)
sys.modules["licz_wynik"] = lw
_spec.loader.exec_module(lw)


def wczytaj_przyklad():
    return json.loads(PRZYKLAD.read_text(encoding="utf-8"))


def poprzedni_miesiac(dane):
    """Wersja "sprzed miesiąca" używana w testach porównania."""
    stare = copy.deepcopy(dane)
    stare["data"] = "2026-09-17"
    q = {p["id"]: p for p in stare["pytania"]}
    q["P03"]["wyniki"]["wyszukiwanie"]["firmy"] = ["Delta Finanse", "Księgowość Gamma"]
    q["P05"]["wyniki"]["wyszukiwanie"]["firmy"] = [
        "Biuro Rachunkowe Alfa", "Delta Finanse", "Księgowość Gamma", "Omega Księgowi"]
    q["P04"]["wyniki"]["wyszukiwanie"]["firmy"].append("Kalkulus")
    q["P10"]["tresc"] = "księgowa dla spółki z o.o. z kadrami w Poznaniu"
    q["P06"]["wyniki"]["wyszukiwanie"] = {"blad": "wyszukiwanie zwróciło błąd"}
    stare["pytania"].insert(10, {
        "id": "P13", "kategoria": "polecenie", "tresc": "biuro rachunkowe Poznań Jeżyce",
        "wyniki": {"wyszukiwanie": {"firmy": ["Omega Księgowi"], "zrodla": ["https://panoramafirm.pl/x"]}}})
    return stare


class TestNormalizacji(unittest.TestCase):
    def test_formy_prawne_i_diakrytyki(self):
        self.assertEqual(lw.klucz_nazwy("Delta Finanse sp. z o.o."), "delta finanse")
        self.assertEqual(lw.klucz_nazwy("DELTA FINANSE SP Z O O"), "delta finanse")
        self.assertEqual(lw.klucz_nazwy("Księgowość Gamma s.c."), "ksiegowosc gamma")
        self.assertEqual(lw.klucz_nazwy("Ksiegowosc Gamma"), "ksiegowosc gamma")
        self.assertEqual(lw.klucz_nazwy("Studio Łódź Projekt S.A."), "studio lodz projekt")
        self.assertEqual(lw.klucz_nazwy("Studio Lodz Projekt SA"), "studio lodz projekt")
        self.assertEqual(lw.klucz_nazwy("„Kowalski i Wspólnicy” sp.k."), "kowalski i wspolnicy")
        self.assertEqual(lw.klucz_nazwy("Nowak Spółka Jawna"), "nowak")
        # Końcówki domen i "www." w nazwach firm.
        self.assertEqual(lw.klucz_nazwy("iFirma.pl"), "ifirma")
        self.assertEqual(lw.klucz_nazwy("www.inFakt.pl"), "infakt")
        self.assertEqual(lw.klucz_nazwy("Fakturownia.pl sp. z o.o."), "fakturownia")
        self.assertEqual(lw.klucz_nazwy("Booksy.com"), "booksy")

    def test_wyswietlanie_zachowuje_diakrytyki(self):
        self.assertEqual(lw.usun_forme_prawna("Księgowość Gamma s.c."), "Księgowość Gamma")

    def test_domeny(self):
        self.assertEqual(lw.domena_z_zrodla("https://www.panoramafirm.pl/a/b"), "panoramafirm.pl")
        self.assertEqual(lw.domena_z_zrodla("oferteo.pl"), "oferteo.pl")
        self.assertEqual(lw.domena_z_zrodla("https://m.facebook.com/x"), "facebook.com")
        self.assertEqual(lw.domena_z_zrodla("https://www.google.com/maps/place/x"), "google.com/maps")
        self.assertEqual(lw.domena_z_zrodla("https://maps.google.pl/?q=x"), "google.com/maps")
        self.assertEqual(lw.domena_z_zrodla("https://maps.app.goo.gl/abc"), "google.com/maps")
        self.assertEqual(lw.domena_z_zrodla("Google Maps"), "google.com/maps")
        self.assertEqual(lw.domena_z_zrodla("https://www.google.com/search?q=x"), "google.com")
        self.assertIsNone(lw.domena_z_zrodla("jakiś artykuł"))

    def test_formatowanie(self):
        self.assertEqual(lw.procent(Fraction(4, 28)), "14,3%")
        self.assertEqual(lw.procent(Fraction(2, 5)), "40%")
        self.assertEqual(lw.procent(None), "-")
        self.assertEqual(lw.zmiana_pp(Fraction(4, 10), Fraction(3, 10)), "+10 p.p.")
        self.assertEqual(lw.zmiana_pp(Fraction(1, 3), Fraction(2, 3)), "-33,3 p.p.")
        self.assertEqual(lw.zmiana_pp(Fraction(1, 2), Fraction(1, 2)), "bez zmian")
        self.assertEqual(lw.srednia_pozycja([1]), "1,0")
        self.assertEqual(lw.srednia_pozycja([3, 2, 5, 1]), "2,8")
        self.assertEqual(lw.srednia_pozycja([]), "-")
        self.assertEqual(lw.prog_zmiennosci(20), 4)
        self.assertEqual(lw.prog_zmiennosci(10), 2)

    def test_progi_interpretacji(self):
        self.assertEqual(lw.ocena(Fraction(0)), "niewidoczny")
        self.assertEqual(lw.ocena(Fraction(1, 10)), "słabo")
        self.assertEqual(lw.ocena(Fraction(15, 100)), "średnio")
        self.assertEqual(lw.ocena(Fraction(40, 100)), "średnio")
        self.assertEqual(lw.ocena(Fraction(41, 100)), "mocno")


class TestPrzykladu(unittest.TestCase):
    """Liczby dla assets/wyniki_przyklad.json, przeliczone ręcznie."""

    @classmethod
    def setUpClass(cls):
        dane = wczytaj_przyklad()
        assert lw.waliduj(dane) == []
        cls.wynik = lw.policz(dane)
        cls.szuk = cls.wynik.tryby["wyszukiwanie"]
        cls.pam = cls.wynik.tryby["pamiec"]

    def test_widocznosc(self):
        # Kalkulus pada w P01 (poz. 3), P03 (2), P05 (5), P07 (1): 4 z 10.
        self.assertEqual(self.szuk.liczba_pytan, 10)
        self.assertEqual([w.pid for w in self.szuk.trafienia], ["P01", "P03", "P05", "P07"])
        self.assertEqual(self.szuk.widocznosc, Fraction(4, 10))
        self.assertEqual([w.pozycja for w in self.szuk.trafienia], [3, 2, 5, 1])

    def test_share_of_voice(self):
        # Unikalne firmy na pytanie: 3+3+3+2+5+3+2+2+3+2 = 28, nasze wzmianki: 4.
        self.assertEqual(self.szuk.wzmianki_suma, 28)
        self.assertEqual(self.szuk.share_of_voice, Fraction(4, 28))

    def test_kategorie(self):
        self.assertEqual(self.szuk.kategorie, {
            "polecenie": [2, 1], "problem": [2, 1], "ranking": [2, 1],
            "kryteria": [3, 1], "alternatywy": [1, 0]})

    def test_konkurenci(self):
        liczby = {k: len(v) for k, v in self.szuk.firmy.items()}
        self.assertEqual(liczby, {
            "delta finanse": 7, "biuro rachunkowe alfa": 6, "omega ksiegowi": 5,
            "ksiegowosc gamma": 4, "sigma rachunkowosc": 2})
        rozp = self.wynik.rozpoznawacz
        self.assertEqual(rozp.nazwa_wyswietlana("ksiegowosc gamma"), "Księgowość Gamma")
        self.assertEqual(rozp.nazwa_wyswietlana("delta finanse"), "Delta Finanse")

    def test_domeny(self):
        liczby = {k: len(v) for k, v in self.szuk.domeny.items()}
        self.assertEqual(liczby["panoramafirm.pl"], 4)
        self.assertEqual(liczby["google.com/maps"], 4)
        self.assertEqual(liczby["oferteo.pl"], 3)
        self.assertEqual(liczby["rankingi-przyklad.pl"], 3)
        self.assertEqual(liczby["kalkulus-przyklad.pl"], 2)
        self.assertEqual(self.szuk.nasza_domena_pytania, ["P01", "P07"])

    def test_tryb_pamieci(self):
        # Sprawdzono 6 pytań niebrandowych, firma nie pada ani razu, 7 wzmianek.
        self.assertEqual(self.pam.liczba_pytan, 6)
        self.assertEqual(self.pam.widocznosc, Fraction(0))
        self.assertEqual(self.pam.wzmianki_suma, 7)

    def test_marka_osobno(self):
        self.assertEqual([w.pid for w in self.szuk.wiersze_marka], ["P11", "P12"])
        self.assertTrue(all(w.nasza for w in self.szuk.wiersze_marka))
        self.assertEqual(self.wynik.liczba_brandowych, 2)
        self.assertEqual(self.wynik.ostrzezenia, [])


class TestPorownania(unittest.TestCase):
    def test_porownanie(self):
        dane = wczytaj_przyklad()
        stare = poprzedni_miesiac(dane)
        rozp = lw.zbuduj_rozpoznawacz(dane, stare)
        nowy = lw.policz(dane, rozp)
        stary = lw.policz(stare, rozp)
        self.assertEqual(stary.tryby["wyszukiwanie"].widocznosc, Fraction(3, 10))
        self.assertEqual(stary.tryby["wyszukiwanie"].share_of_voice, Fraction(3, 25))
        tekst = "\n".join(lw.porownaj(nowy, stary, 10))
        self.assertIn("| Claude z wyszukiwaniem | 3 z 10 (30%) | 4 z 10 (40%) | +10 p.p. |", tekst)
        self.assertIn("3 z 8 → 4 z 8 (+12,5 p.p.)", tekst)
        self.assertIn("12% → 14,3% (+2,3 p.p.)", tekst)
        self.assertIn("teraz się pojawiasz, a wcześniej nie: P03, P05", tekst)
        self.assertIn("a teraz nie: P04", tekst)
        self.assertIn("Pytania usunięte: P13", tekst)
        self.assertIn("(nie porównujemy ich): P10", tekst)
        self.assertIn("| Omega Księgowi | 6 | 5 | -1 |", tekst)


class TestCli(unittest.TestCase):
    def uruchom(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                kod = lw.main(list(argv))
            except SystemExit as e:
                kod = e.code
        return kod, out.getvalue(), err.getvalue()

    def test_sukces_i_zapis_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "raport.md"
            kod, out, _ = self.uruchom(str(PRZYKLAD), "--md", str(md))
            self.assertEqual(kod, 0)
            tresc = md.read_text(encoding="utf-8")
            self.assertIn("Pojawiasz się w 4 z 10 odpowiedzi (40%)", tresc)
            # Na ekranie tylko krótkie podsumowanie, a nie cały raport.
            self.assertIn("Claude z wyszukiwaniem: 4 z 10 (40%)", out)
            self.assertIn(str(md), out)
            self.assertNotIn("Pytanie po pytaniu", out)
            self.assertLess(len(out.splitlines()), 8)

    def test_bez_md_pelny_raport(self):
        kod, out, _ = self.uruchom(str(PRZYKLAD))
        self.assertEqual(kod, 0)
        self.assertIn("Pytanie po pytaniu", out)

    def test_zly_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            plik = Path(tmp) / "zly.json"
            plik.write_text('{"firma": {"nazwa": "X"}, "pytania": [}', encoding="utf-8")
            kod, _, err = self.uruchom(str(plik))
            self.assertEqual(kod, 1)
            self.assertIn("nie jest poprawnym JSON-em", err)

    def test_brakujace_pola(self):
        with tempfile.TemporaryDirectory() as tmp:
            plik = Path(tmp) / "braki.json"
            plik.write_text(json.dumps({"firma": {}, "pytania": [{"id": "P1"}]}), encoding="utf-8")
            kod, _, err = self.uruchom(str(plik))
            self.assertEqual(kod, 1)
            self.assertIn("firma.nazwa", err)
            self.assertIn("brak pola \"tresc\"", err)

    def test_brak_pliku(self):
        kod, _, err = self.uruchom("nie-ma-takiego-pliku.json")
        self.assertEqual(kod, 1)
        self.assertIn("Nie znaleziono pliku", err)

    def test_nazwa_firmy_w_pytaniu_niebrandowym(self):
        dane = wczytaj_przyklad()
        dane["pytania"][0]["tresc"] = "czy Kalkulus to dobre biuro w Poznaniu?"
        wynik = lw.policz(dane)
        self.assertEqual(wynik.tryby["wyszukiwanie"].liczba_pytan, 9)
        self.assertTrue(any("zawiera nazwę Twojej firmy" in o for o in wynik.ostrzezenia))


def minimalne(firma, pytania, **reszta):
    dane = {"firma": firma, "pytania": pytania}
    dane.update(reszta)
    assert lw.waliduj(dane) == [], lw.waliduj(dane)
    return dane


def pytanie(pid, kategoria, tresc, firmy=None, zrodla=None, tryb="wyszukiwanie", **pola):
    wynik = {"firmy": firmy or [], "zrodla": zrodla or []}
    wynik.update(pola)
    return {"id": pid, "kategoria": kategoria, "tresc": tresc, "wyniki": {tryb: wynik}}


class TestPoprawek(unittest.TestCase):
    """Poprawki po review i testach na żywo (iteracja 2)."""

    def test_aliasy_naszej_firmy_scalane(self):
        # Dwa zapisy naszej firmy w jednej odpowiedzi liczą się jako jedna wzmianka.
        dane = minimalne(
            {"nazwa": "inFakt Sp. z o.o.", "aliasy": ["inFakt.pl"]},
            [pytanie("P01", "polecenie", "księgowość online dla jdg",
                     ["inFakt.pl", "Infakt sp. z o.o.", "wFirma", "iFirma.pl", "ifirma"])])
        m = lw.policz(dane).tryby["wyszukiwanie"]
        self.assertEqual(m.wiersze[0].firmy, ["infakt", "wfirma", "ifirma"])
        self.assertEqual(m.wzmianki_suma, 3)
        self.assertEqual(m.share_of_voice, Fraction(1, 3))
        tekst = lw.renderuj(lw.policz(dane), 10)
        self.assertNotIn("**inFakt**, **inFakt**", tekst)

    def test_nazwa_opisowa_nie_przenosi_pytania(self):
        firma = {"nazwa": "Fizjoterapia Lublin", "nazwa_opisowa": True}
        dane = minimalne(firma, [
            pytanie("P01", "polecenie", "dobra fizjoterapia Lublin, kręgosłup", ["Fizjo Plus"]),
            pytanie("P02", "problem", "boli mnie kolano, gdzie w Lublinie", ["Fizjoterapia Lublin"])])
        wynik = lw.policz(dane)
        self.assertEqual(wynik.tryby["wyszukiwanie"].liczba_pytan, 2)
        self.assertTrue(any("opisową nazwę" in o for o in wynik.ostrzezenia))
        # Bez flagi pytanie trafia do pytań o markę, a ostrzeżenie podpowiada flagę.
        firma["nazwa_opisowa"] = False
        wynik = lw.policz(dane)
        self.assertEqual(wynik.tryby["wyszukiwanie"].liczba_pytan, 1)
        self.assertTrue(any("nazwa_opisowa" in o for o in wynik.ostrzezenia))

    def test_nazwa_konkurenta_zawierajaca_alias_nie_jest_marka(self):
        dane = minimalne(
            {"nazwa": "Alfa", "konkurenci": ["Alfa Plus"]},
            [pytanie("P04", "alternatywy", "coś jak Alfa Plus ale taniej", ["Beta"])])
        wynik = lw.policz(dane)
        self.assertEqual(wynik.tryby["wyszukiwanie"].liczba_pytan, 1)
        self.assertEqual(wynik.liczba_brandowych, 0)

    def test_konflikt_aliasow_wygrywa_nasza_firma(self):
        dane = minimalne(
            {"nazwa": "Biuro Rachunkowe Kalkulus", "aliasy": ["Kalkulus"]},
            [pytanie("P01", "polecenie", "biuro rachunkowe Poznań", ["Kalkulus", "BR Alfa"]),
             pytanie("P02", "marka", "Kalkulus opinie", ["Kalkulus"])],
            aliasy_firm={"Biuro Rachunkowe Alfa": ["BR Alfa", "Kalkulus"]})
        wynik = lw.policz(dane)
        m = wynik.tryby["wyszukiwanie"]
        self.assertTrue(m.wiersze[0].nasza)
        self.assertTrue(m.wiersze_marka[0].nasza)
        self.assertEqual({k: len(v) for k, v in m.firmy.items()}, {"biuro rachunkowe alfa": 1})
        self.assertTrue(any("jednocześnie aliasem" in o for o in wynik.ostrzezenia))

    def test_profil_na_platformie(self):
        dane = minimalne(
            {"nazwa": "Kalkulus", "strona": "https://www.facebook.com/kalkulus"},
            [pytanie("P01", "polecenie", "biuro rachunkowe Poznań", ["Delta"],
                     ["https://www.facebook.com/deltafinanse", "https://pl-pl.facebook.com/x"]),
             pytanie("P02", "polecenie", "księgowa Poznań", ["Kalkulus"],
                     ["https://pl-pl.facebook.com/kalkulus/posts/1"])])
        wynik = lw.policz(dane)
        m = wynik.tryby["wyszukiwanie"]
        self.assertEqual(m.nasza_domena_pytania, ["P02"])
        tekst = lw.renderuj(wynik, 10)
        self.assertNotIn("(Twoja strona)", tekst)
        self.assertIn("(w tym Twój profil)", tekst)
        self.assertTrue(any("profil na platformie" in o for o in wynik.ostrzezenia))

    def test_zwykla_strona_dalej_po_domenie(self):
        dane = minimalne(
            {"nazwa": "Kalkulus", "strona": "https://kalkulus-przyklad.pl"},
            [pytanie("P01", "polecenie", "biuro Poznań", ["Kalkulus"],
                     ["https://blog.kalkulus-przyklad.pl/a"])])
        self.assertEqual(lw.policz(dane).tryby["wyszukiwanie"].nasza_domena_pytania, ["P01"])

    def test_wyniki_null_i_same_bledy(self):
        dane = minimalne(
            {"nazwa": "X"},
            [{"id": "P01", "kategoria": "polecenie", "tresc": "a", "wyniki": None},
             pytanie("P02", "polecenie", "b"), pytanie("P03", "problem", "c")])
        dane["pytania"][1]["wyniki"]["wyszukiwanie"] = {"blad": "limit wyszukiwań"}
        dane["pytania"][2]["wyniki"]["wyszukiwanie"] = {"blad": "brak wyników"}
        wynik = lw.policz(dane)
        tekst = lw.renderuj(wynik, 10)
        self.assertIn("P02: limit wyszukiwań", tekst)
        self.assertIn("P03: brak wyników", tekst)
        self.assertTrue(any("Wszystkie wyniki" in o for o in wynik.ostrzezenia))

    def test_naglowek_rozroznia_sprawdzone_i_pominiete(self):
        dane = wczytaj_przyklad()
        dane["pytania"][3]["wyniki"]["wyszukiwanie"] = {"blad": "timeout"}
        tekst = lw.renderuj(lw.policz(dane), 10)
        self.assertIn("Pytania niebrandowe: 10 (w trybie głównym sprawdzone: 9, z błędem: 1, bez wyniku: 0)", tekst)

    def test_remisy_na_granicy_top(self):
        pytania = [pytanie(f"P{i}", "polecenie", f"pytanie {i}", ["A", "B", "C", "D"]) for i in range(1, 3)]
        tekst = lw.renderuj(lw.policz(minimalne({"nazwa": "X"}, pytania)), 2)
        self.assertIn("Z tym samym wynikiem co ostatnia pozycja (2): C, D.", tekst)

    def test_konkurenci_wywnioskowani_etykieta(self):
        dane = minimalne(
            {"nazwa": "inFakt", "konkurenci": ["wFirma"], "konkurenci_wywnioskowani": ["ifirma"]},
            [pytanie("P01", "polecenie", "księgowość online", ["wFirma", "iFirma.pl", "Fakturownia"])])
        tekst = lw.renderuj(lw.policz(dane), 10)
        self.assertIn("wFirma (konkurent podany przez Ciebie)", tekst)
        self.assertIn("ifirma (konkurent wskazany przez Claude)", tekst)

    def test_zaleznosc_od_jednego_zrodla(self):
        pytania = [
            pytanie("P01", "polecenie", "a", ["X", "A"], ["https://ranking.pl/1", "https://a.pl"]),
            pytanie("P02", "polecenie", "b", ["X"], ["https://ranking.pl/2"]),
            pytanie("P03", "polecenie", "c", ["X"], ["https://inne.pl"]),
        ]
        wynik = lw.policz(minimalne({"nazwa": "X"}, pytania))
        self.assertEqual(wynik.tryby["wyszukiwanie"].zaleznosc_od_zrodel(), [("ranking.pl", 2, 3)])
        self.assertIn("ponad 1/3 z 3 Twoich trafień w tym trybie opiera się na: ranking.pl (2 z 3)",
                      lw.renderuj(wynik, 10))
        # Przy mniej niż 3 trafieniach nie ostrzegamy (za mała próba).
        wynik = lw.policz(minimalne({"nazwa": "X"}, pytania[:2]))
        self.assertEqual(wynik.tryby["wyszukiwanie"].zaleznosc_od_zrodel(), [])

    def test_zaleznosc_pomija_wlasna_strone(self):
        pytania = [pytanie(f"P0{i}", "polecenie", str(i), ["X"], ["https://x-przyklad.pl/"]) for i in range(1, 4)]
        wynik = lw.policz(minimalne({"nazwa": "X", "strona": "x-przyklad.pl"}, pytania))
        self.assertNotIn("Zależność od pojedynczych źródeł", lw.renderuj(wynik, 10))

    def test_ostrzezenie_za_duzo_firm(self):
        firmy = [f"Firma {i}" for i in range(9)]
        wynik = lw.policz(minimalne({"nazwa": "X"}, [pytanie("P01", "polecenie", "a", firmy)]))
        self.assertTrue(any("Więcej niż 7 firm" in o for o in wynik.ostrzezenia))

    def test_prog_zmiennosci_w_porownaniu(self):
        dane = wczytaj_przyklad()
        rozp = lw.zbuduj_rozpoznawacz(dane, dane)
        tekst = "\n".join(lw.porownaj(lw.policz(dane, rozp), lw.policz(dane, rozp), 10))
        self.assertIn("Zmiana o najwyżej 2 pytania (około 20 p.p.)", tekst)


class TestIteracji3(unittest.TestCase):
    """Poprawki po review 2 i teście firmy lokalnej."""

    def profil(self, strona, zrodlo):
        dane = minimalne({"nazwa": "Kalkulus", "strona": strona},
                         [pytanie("P01", "polecenie", "biuro Poznań", ["Delta"], [zrodlo])])
        return lw.policz(dane).tryby["wyszukiwanie"].nasza_domena_pytania

    def test_profile_innych_firm_nie_sa_twoje(self):
        przypadki = [
            ("https://booksy.com/pl-pl/12345_salon-anna_fryzjer_3_warszawa",
             "https://booksy.com/pl-pl/99999_salon-inny_fryzjer_3_warszawa"),
            ("https://www.linkedin.com/company/kalkulus", "https://www.linkedin.com/company/deltafinanse"),
            ("https://www.facebook.com/profile.php?id=1000123", "https://www.facebook.com/profile.php?id=999"),
            ("https://sites.google.com/view/kalkulus", "https://sites.google.com/view/delta"),
        ]
        for nasza, cudza in przypadki:
            with self.subTest(nasza=nasza):
                self.assertEqual(self.profil(nasza, cudza), [])

    def test_wlasny_profil_i_podstrony_sa_twoje(self):
        przypadki = [
            ("https://booksy.com/pl-pl/12345_salon-anna_fryzjer_3_warszawa",
             "https://booksy.com/pl-pl/12345_salon-anna_fryzjer_3_warszawa/opinie"),
            ("https://www.linkedin.com/company/kalkulus/", "https://pl.linkedin.com/company/kalkulus"),
            ("https://www.facebook.com/profile.php?id=1000123", "https://m.facebook.com/profile.php?id=1000123&sk=about"),
            ("https://sites.google.com/view/kalkulus", "https://sites.google.com/view/kalkulus/kontakt"),
        ]
        for nasza, zrodlo in przypadki:
            with self.subTest(nasza=nasza):
                self.assertEqual(self.profil(nasza, zrodlo), ["P01"])

    def test_prefiks_sciezki_nie_myli_podobnych_profili(self):
        self.assertEqual(self.profil("https://facebook.com/kalkulus", "https://facebook.com/kalkulusplus"), [])

    def test_bez_wyszukiwania_glowny_tryb_z_danych_recznych(self):
        pytania = [
            {"id": "P01", "kategoria": "polecenie", "tresc": "a",
             "wyniki": {"pamiec": {"firmy": []}, "chatgpt": {"firmy": ["X"]}, "gemini": {"firmy": []}}},
            {"id": "P02", "kategoria": "polecenie", "tresc": "b",
             "wyniki": {"pamiec": {"firmy": []}, "chatgpt": {"firmy": ["X", "Y"]}}},
        ]
        wynik = lw.policz(minimalne({"nazwa": "X"}, pytania))
        self.assertEqual(wynik.tryb_glowny.tryb, "chatgpt")
        self.assertIn("Pojawiasz się w 2 z 2 odpowiedzi (100%).** Tryb: ChatGPT", lw.renderuj(wynik, 10))
        # Gemini ma więcej pytań: wygrywa tryb z największą liczbą sprawdzonych pytań.
        for p in pytania:
            p["wyniki"]["gemini"] = {"firmy": []}
        pytania.append({"id": "P03", "kategoria": "problem", "tresc": "c", "wyniki": {"gemini": {"firmy": []}}})
        self.assertEqual(lw.policz(minimalne({"nazwa": "X"}, pytania)).tryb_glowny.tryb, "gemini")
        # Sama pamięć: dopiero wtedy wynik główny z pamięci.
        tylko_pamiec = [pytanie("P01", "polecenie", "a", [], tryb="pamiec")]
        self.assertEqual(lw.policz(minimalne({"nazwa": "X"}, tylko_pamiec)).tryb_glowny.tryb, "pamiec")

    def test_odmiana(self):
        oczekiwane = {1: "pytanie", 2: "pytania", 5: "pytań", 6: "pytań", 12: "pytań", 22: "pytania", 25: "pytań"}
        for n, slowo in oczekiwane.items():
            self.assertEqual(lw.ile_pytan(n), f"{n} {slowo}")
        firmy = {1: "firma", 2: "firmy", 5: "firm", 6: "firm", 12: "firm", 22: "firmy", 25: "firm"}
        for n, slowo in firmy.items():
            self.assertEqual(lw.ile_slownie(n, "firma", "firmy", "firm"), f"{n} {slowo}")
        razy = {1: "raz", 2: "razy", 5: "razy", 6: "razy", 12: "razy", 22: "razy", 25: "razy"}
        for n, slowo in razy.items():
            self.assertEqual(lw.ile_razy(n), f"{n} {slowo}")

    def test_odmiana_w_komunikacie_zmiennosci(self):
        for n, fraza in ((5, "o najwyżej 1 pytanie"), (10, "o najwyżej 2 pytania"), (30, "o najwyżej 6 pytań")):
            pytania = [pytanie(f"P{i:02d}", "polecenie", f"pytanie {i}", ["A"]) for i in range(1, n + 1)]
            dane = minimalne({"nazwa": "X"}, pytania)
            rozp = lw.zbuduj_rozpoznawacz(dane, dane)
            tekst = "\n".join(lw.porownaj(lw.policz(dane, rozp), lw.policz(dane, rozp), 10))
            self.assertIn(fraza, tekst)

    def test_nowe_naglowki_tabeli(self):
        tekst = lw.renderuj(lw.policz(wczytaj_przyklad()), 10)
        self.assertIn("| Jesteś na liście? |", tekst)
        self.assertIn("| Kogo wymieniono |", tekst)
        self.assertNotIn("Padłeś", tekst)
        self.assertNotIn("padł", tekst)

    def test_test_niekompletny(self):
        dane = wczytaj_przyklad()
        for p in dane["pytania"]:
            if p["id"] in ("P09", "P10"):
                p["wyniki"].pop("wyszukiwanie")
            if p["id"] == "P12":
                p["wyniki"] = None
        wynik = lw.policz(dane)
        tekst = lw.renderuj(wynik, 10)
        self.assertIn("Test niekompletny: 2 pytania niebrandowe bez wyniku (P09, P10) oraz "
                      "1 pytanie o markę bez wyniku (P12)", tekst)
        self.assertIn("UWAGA. Test niekompletny", lw.podsumowanie(wynik, "m.md", False))
        self.assertNotIn("Test niekompletny", lw.renderuj(lw.policz(wczytaj_przyklad()), 10))

    def test_nazwa_ze_slowami_uslugowymi(self):
        # Pytanie ze słowami usługowymi nie jest pytaniem o markę, a firma o podobnej
        # nazwie nie jest liczona jako nasza (tylko ostrzeżenie).
        dane = minimalne(
            {"nazwa": "RUDEK Gabinety Rehabilitacji Medycznej Sp. z o.o.", "aliasy": ["Rudek"]},
            [pytanie("P01", "ranking", "najlepsze gabinety rehabilitacji w Rzeszowie ranking",
                     ["Gabinety Rehabilitacji Medycznej", "Rudek", "Fizjo Plus"])])
        wynik = lw.policz(dane)
        m = wynik.tryby["wyszukiwanie"]
        self.assertEqual(wynik.liczba_brandowych, 0)
        self.assertEqual(m.wiersze[0].pozycja, 2)
        self.assertIn("gabinety rehabilitacji medycznej", m.firmy)
        self.assertTrue(any("wygląda podobnie" in o for o in wynik.ostrzezenia))

    def test_pole_technika(self):
        dane = wczytaj_przyklad()
        dane["technika"] = {"data": "2026-10-17", "elementy": [
            {"element": "Boty wyszukiwania", "stan": "pośredni sygnał blokady", "opis": "ROBOTS_DISALLOWED"}]}
        tekst = lw.renderuj(lw.policz(dane), 10)
        self.assertIn("## Check techniczny (zapisany w pliku wyników), 2026-10-17", tekst)
        self.assertIn("| Boty wyszukiwania | pośredni sygnał blokady | ROBOTS_DISALLOWED |", tekst)
        dane["technika"] = "zły format"
        wynik = lw.policz(dane)
        self.assertTrue(any("technika" in o for o in wynik.ostrzezenia))


if __name__ == "__main__":
    unittest.main()
