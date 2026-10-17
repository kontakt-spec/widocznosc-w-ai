# Metodologia, ograniczenia i powtarzanie testu

Ten plik czytasz, gdy: liczysz wyniki ręcznie (bez wykonywania kodu), piszesz sekcję o metodologii w raporcie, użytkownik pyta „skąd te liczby?” albo „czy to wiarygodne?”, albo przygotowujesz powtórkę testu.

## Spis treści

1. Co mierzymy, a czego nie
2. Dlaczego nie pozycja: badanie SparkToro
3. Definicje metryk
4. Progi interpretacji (robocze)
5. Liczenie ręczne
6. Schemat pliku wyników
7. Ograniczenia
8. Powtarzanie testu co miesiąc

## 1. Co mierzymy, a czego nie

Mierzymy, jak często firma pojawia się w odpowiedziach na **wiele różnych pytań**, które mógłby zadać jej potencjalny klient. Robimy to na trzy sposoby, zawsze liczone osobno:

- **Claude z wyszukiwaniem** (tryb `wyszukiwanie`, główny): Claude wyszukuje w sieci tak, jak robi to asystent AI, i układa odpowiedź z wyników. To przybliżenie zachowania ChatGPT Search, Perplexity czy Google AI Mode, które też budują odpowiedzi na wynikach wyszukiwania. To nie jest odpowiedź ChatGPT.
- **Claude bez internetu** (tryb `pamiec`): co Claude wie z treningu. Pokazuje, czy firma „zapisała się” w pamięci modeli. Żeby ograniczyć mieszanie z wiedzą z rozmowy, Claude przed użyciem jakiegokolwiek narzędzia zapisuje „migawkę pamięci marki” (`migawka_pamieci`): czy zna firmę i co o niej wie. W odpowiedziach z pamięci sprawdzana firma może paść tylko wtedy, gdy migawka mówi, że Claude ją zna. Tryb i tak jest orientacyjny.
- **Sprawdzenie ręczne** (tryby `chatgpt`, `gemini`, `perplexity`, `google_ai`, `copilot`): odpowiedzi, które użytkownik sam skopiował z tych narzędzi. To jedyne prawdziwe dane z ChatGPT i spółki, jakie ten skill może mieć.

Nie mierzymy: ruchu ze strony, liczby zapytań w ChatGPT, „pozycji w ChatGPT” ani pozycji w Google. Nie robimy pełnego audytu SEO.

## 2. Dlaczego nie pozycja: badanie SparkToro

W styczniu 2026 Rand Fishkin (SparkToro) razem z Patrickiem O'Donnellem (Gumshoe.ai) opublikował badanie, w którym setki ochotników wpisały 2961 promptów do ChatGPT, Claude i Google (AI Overviews, a gdy ich nie było, AI Mode). 12 promptów z prośbą o polecenie marki powtarzano po 60-100 razy na każdej platformie. Wyniki:

- ta sama lista marek pojawiała się w mniej niż 1 na 100 powtórzeń tego samego promptu,
- ta sama lista w tej samej kolejności w mniej niż 1 na 1000 powtórzeń,
- natomiast to, **jak często** dana marka pojawiała się w wielu odpowiedziach, było dużo stabilniejsze. 142 uczestników napisało własne, bardzo różne prompty o słuchawki, a najpopularniejsze marki (Bose, Sony, Sennheiser, Apple) pojawiły się w 55-77% z 994 odpowiedzi.

Wniosek dla nas: pozycja w pojedynczej odpowiedzi AI jest niewiarygodną metryką (pokazujemy ją tylko informacyjnie), a sensowną metryką jest częstotliwość pojawiania się w wielu różnych pytaniach (visibility rate) i udział w odpowiedziach (share of voice).

Uczciwe zastrzeżenia, o których warto wiedzieć: badanie powstało we współpracy z firmą sprzedającą narzędzia do śledzenia AI (autor to ujawnił), nie było recenzowane naukowo i autor sam wzywa do większych badań.

Źródło: Search Engine Journal, 30.01.2026, „AI Recommendations Change With Nearly Every Query: SparkToro”, https://www.searchenginejournal.com/ai-recommendations-change-with-nearly-every-query-sparktoro/566242

## 3. Definicje metryk

Wszystkie metryki liczymy osobno dla każdego trybu i tylko z pytań niebrandowych (bez kategorii `marka`). Wyniki z polem `blad` pomijamy.

- **Widoczność (visibility rate)** = liczba pytań, w których firma się pojawiła ÷ liczba sprawdzonych pytań niebrandowych. Przykład: firma pojawiła się w 4 z 10 odpowiedzi = 40%.
- **Udział w odpowiedziach (share of voice)** = liczba wzmianek o firmie ÷ liczba wszystkich wzmianek o firmach w tych samych odpowiedziach. W jednej odpowiedzi każda firma liczy się raz. Przykład: w 10 odpowiedziach było łącznie 28 wzmianek o firmach, w tym 4 o naszej = 14,3%. Ta metryka mówi, jaki kawałek „tortu poleceń” zjada firma.
- **Ranking firm**: dla każdej innej firmy liczba pytań, w których się pojawiła.
- **Domeny źródłowe**: dla każdej domeny liczba pytań, w których była źródłem odpowiedzi. Linki do Map Google liczymy jako jedno źródło `google.com/maps`.
- **Cytowanie strony firmy**: w ilu pytaniach niebrandowych źródłem była domena firmy (lub jej subdomena). Jeśli „strona” firmy to profil na platformie (Facebook, Instagram, Booksy, ZnanyLekarz itp.), liczy się adres profilu, a nie cała platforma.
- **Zależność od pojedynczych źródeł**: jeśli firma ma co najmniej 3 trafienia, a ponad 1/3 z nich opiera się na jednej domenie (bez własnej strony firmy), skrypt to zgłasza. W raporcie trzeba to napisać jako zastrzeżenie, bo zmiana jednego rankingu może mocno przesunąć wynik.
- **Pozycja (informacyjnie)**: miejsce firmy na liście firm w odpowiedzi (1 = pierwsza). Średnia pozycja jest liczona tylko z pytań, w których firma się pojawiła.

Zaokrąglenia: do 0,1 punktu procentowego, połówki w górę. Polski zapis dziesiętny (przecinek).

Normalizacja nazw (żeby „Delta Finanse sp. z o.o.” i „DELTA FINANSE” liczyły się jako jedna firma): małe litery, bez formy prawnej (sp. z o.o., S.A., sp.k., sp.j., sp.p., s.c., S.K.A., P.S.A., „spółka…”), bez „www.” i końcówki domeny („iFirma.pl” to „ifirma”), bez cudzysłowów i interpunkcji, porównanie także w wersji bez polskich znaków. Wszystkie warianty sprawdzanej firmy liczą się jako jedna firma, więc dwa zapisy w jednej odpowiedzi to jedna wzmianka. Przy konflikcie (ten sam wariant przypisany Tobie i konkurentowi) wygrywa sprawdzana firma, a skrypt to zgłasza.

Odmiany nie są normalizowane: „Biura Rachunkowego Kalkulus” i „Kalkulusa” skrypt uzna za inne firmy. Dlatego nazwy zapisuj zawsze w mianowniku i w formie, w jakiej firma sama się nazywa. Warianty, których nie da się złapać normalizacją (np. „BR Alfa” i „Biuro Rachunkowe Alfa”), zapisuj w `aliasy_firm`, a warianty sprawdzanej firmy w `firma.aliasy`.

## 4. Progi interpretacji (robocze)

| Widoczność | Ocena | Co to znaczy w praktyce |
|---|---|---|
| 0% | niewidoczny | AI nie poleca firmy w żadnym z badanych pytań |
| powyżej 0%, poniżej 15% | słabo | pojedyncze przypadki, mogą być przypadkowe |
| 15-40% | średnio | firma jest w grze, ale w większości odpowiedzi wygrywają inni |
| powyżej 40% | mocno | firma pojawia się regularnie w różnych pytaniach |

To heurystyka autora skilla, nie standard branżowy. Uzasadnienie:

- **15%** to około 3 z 20 pytań. Poniżej tego jedno-dwa trafienia mogą wynikać z przypadku albo z jednego konkretnego pytania, które pasuje do firmy.
- **40%** to poziom, przy którym firma pojawia się w wyraźnej części różnie sformułowanych pytań. Dla porównania: w badaniu SparkToro najpopularniejsze marki słuchawek pojawiały się w 55-77% odpowiedzi na różnie sformułowane prompty. To inna skala niż mała firma lokalna, więc wynik powyżej 40% traktuj po prostu jako wyraźną obecność, nie jako „poziom lidera”.
- Progi dotyczą trybu z wyszukiwaniem. W trybie bez internetu małe firmy prawie zawsze mają 0% i to jest normalne, bo modele zapamiętują głównie duże, często opisywane marki.
- Dla dużych marek ogólnopolskich progi mówią mało (lider rynku łatwo ma ponad 40%). Wtedy ważniejsze jest porównanie z 2-3 największymi konkurentami z tabeli i przegrane kategorie pytań.

## 5. Liczenie ręczne

Gdy nie ma wykonywania kodu, policz dokładnie tak samo jak skrypt:

1. Weź pytania niebrandowe, które mają wynik w danym trybie (bez `blad`).
2. Dla każdego pytania ustal listę unikalnych firm (po normalizacji z punktu 3).
3. Widoczność: policz pytania, w których jest nasza firma, podziel przez liczbę pytań.
4. Share of voice: zsumuj długości list z punktu 2, podziel liczbę pytań z naszą firmą przez tę sumę.
5. Ranking: dla każdej innej firmy policz pytania, w których jest. Sortuj malejąco, przy remisie alfabetycznie.
6. Domeny: dla każdej domeny policz pytania, w których jest źródłem.
7. Kategorie: powtórz punkt 3 osobno dla każdej kategorii.

Przy liczeniu ręcznym napisz w raporcie jedno zdanie: „Metryki policzone ręcznie według tych samych zasad co skrypt.” Jeśli masz choćby cień wątpliwości co do sumy, przelicz drugi raz, zanim pokażesz wynik.

## 6. Schemat pliku wyników

```json
{
  "wersja_schematu": 1,
  "data": "RRRR-MM-DD",
  "srodowisko": "np. Claude.ai z wyszukiwaniem w sieci",
  "migawka_pamieci": {"zna_firme": false, "co_wiem": ["co Claude wiedział o firmie przed użyciem narzędzi"]},
  "zalozenia": ["założenia przyjęte bez potwierdzenia użytkownika, np. zasięg ogólnopolski"],
  "firma": {
    "nazwa": "pełna nazwa firmy",
    "aliasy": ["krótsze nazwy, pod którymi firma może paść"],
    "strona": "https://adres-strony.pl",
    "nazwa_opisowa": false,
    "uslugi": ["główne usługi"],
    "dla_kogo": "główni klienci",
    "zasieg": "lokalny: miasto / ogólnopolski",
    "konkurenci": ["opcjonalnie, podani przez użytkownika"],
    "konkurenci_wywnioskowani": ["opcjonalnie, wskazani przez Claude"]
  },
  "aliasy_firm": {"Nazwa kanoniczna konkurenta": ["inny zapis tej samej firmy"]},
  "pytania": [
    {
      "id": "P01",
      "kategoria": "polecenie | problem | ranking | kryteria | alternatywy | marka",
      "tresc": "treść pytania dokładnie tak, jak zadałby je klient",
      "wyniki": {
        "wyszukiwanie": {
          "zapytania": ["co faktycznie wpisano do wyszukiwarki"],
          "firmy": ["najwyżej 7 firm, w mianowniku, w kolejności z odpowiedzi"],
          "zrodla": ["pełne adresy URL źródeł, z których wzięto firmy"],
          "notatka": "opcjonalnie, krótko",
          "poprawne": ["tylko dla kategorii marka"],
          "bledne": ["tylko dla kategorii marka"],
          "brakujace": ["tylko dla kategorii marka"]
        },
        "pamiec": {"firmy": []},
        "chatgpt": {"firmy": [], "zrodla": []}
      }
    }
  ]
}
```

Wymagane: `firma.nazwa`, `pytania[].id`, `pytania[].kategoria`, `pytania[].tresc`, a w każdym wyniku `firmy` (może być pustą listą). Pytanie bez wyników (`wyniki` puste albo `null`) oznacza „jeszcze nie sprawdzone”: tak wygląda plik do kontynuacji. `nazwa_opisowa: true` ustaw, gdy nazwa firmy to zwykłe słowa usługi i miasta; wtedy skrypt nie przenosi pytań z tymi słowami do pytań o markę, tylko ostrzega. Pola `migawka_pamieci` i `zalozenia` skrypt ignoruje, ale są potrzebne do raportu i kontynuacji. Wynik, którego nie udało się zdobyć, zapisz jako `{"blad": "krótki powód"}`, a nie jako pustą listę firm, bo pusta lista oznacza „AI nie wymienił żadnej firmy” i obniża widoczność.

Opcjonalne pole `technika` przechowuje wynik checku technicznego (krok 5), żeby kontynuacja testu nie musiała go powtarzać. Skrypt nie liczy z niego metryk, tylko wypisuje tabelę:

```json
"technika": {
  "data": "RRRR-MM-DD",
  "elementy": [
    {"element": "Boty wyszukiwania (Googlebot, OAI-SearchBot, Claude-SearchBot, PerplexityBot)", "stan": "pośredni sygnał blokady", "opis": "Narzędzie Claude zwróciło ROBOTS_DISALLOWED dla strony głównej i robots.txt."}
  ]
}
```

Klucze trybów rozpoznawane przez skrypt: `wyszukiwanie`, `pamiec`, `chatgpt`, `perplexity`, `gemini`, `google_ai`, `copilot`. Inny klucz też zadziała, będzie po prostu wyświetlony pod swoją nazwą. Wynik główny pochodzi z trybu `wyszukiwanie`; bez niego z trybu z odpowiedziami wklejonymi przez użytkownika, który ma najwięcej sprawdzonych pytań; pamięć modelu tylko w ostateczności. Gdy w trybie głównym brakuje wyników części pytań, skrypt na górze zgłasza „Test niekompletny”.

## 7. Ograniczenia

Do sekcji „Metodologia i ograniczenia” w raporcie wybierz te, które dotyczą danego badania, i opisz je krótko:

- **To symulacja, nie ChatGPT.** Claude z wyszukiwaniem korzysta z innej wyszukiwarki i innego modelu niż ChatGPT, Gemini czy Perplexity. Wynik pokazuje, co asystent AI z dostępem do sieci może znaleźć o firmie i jej konkurencji, a nie co dokładnie odpowie ChatGPT.
- **Odpowiedzi AI się zmieniają.** To samo pytanie zadane dwa razy daje inną listę firm (SparkToro). Dlatego liczy się wynik z wielu pytań, a nie pojedyncza odpowiedź.
- **Mała próba.** Przy 20 pytaniach jedno pytanie to 5 punktów procentowych. Wynik 40% oznacza w praktyce „gdzieś między około 20% a 60%”. Traktuj go jako orientację, nie pomiar laboratoryjny.
- **Mapy Google są niedoszacowane.** Wyszukiwarka Claude nie widzi Map Google i profili firm tak jak Gemini czy Google AI Overviews. Dla firm lokalnych profil w Mapach może więc ważyć w prawdziwych odpowiedziach więcej, niż pokazuje ten test.
- **Reguła włączenia firmy na listę.** Najbardziej wpływa na wynik decyzja, czy firma z wyników to „polecenie”. Skill stosuje stałą regułę (SKILL.md, krok 3b), ale przy granicznych źródłach (ogólny artykuł, w którym firma pada jako przykład) wynik może się przesunąć o kilka pytań. Jeśli to się zdarzyło, napisz o tym.
- **Personalizacja i lokalizacja.** Prawdziwe asystenty biorą pod uwagę lokalizację użytkownika, historię rozmów i pamięć. Symulacja tego nie robi, dlatego w pytaniach podajemy miasto wprost.
- **Tryb bez internetu jest orientacyjny.** Migawka pamięci ogranicza mieszanie wiedzy z treningu z wiedzą z rozmowy, ale nie usuwa go całkiem (dotyczy to zwłaszcza konkurentów). Czystszy test: nowa rozmowa, wyszukiwanie wyłączone, wklejone same pytania.
- **Kogo wymieniono, ocenia Claude.** Lista firm w odpowiedzi to decyzja modelu na podstawie wyników wyszukiwania. Pomaga to, że zasady są stałe (patrz SKILL.md), ale to wciąż ocena, a nie odczyt z ChatGPT.

## 8. Powtarzanie testu co miesiąc

Żeby porównanie miało sens:

- **Te same pytania.** Użyj pliku wyników z poprzedniego badania: te same `id`, ta sama treść, ta sama kategoria. Skrypt porównuje osobno „na tych samych pytaniach”, a pytania o zmienionej treści pomija.
- **To samo środowisko i te same tryby.** Najlepiej to samo narzędzie (np. Claude.ai z wyszukiwaniem) i podobna pora miesiąca.
- **Nowe pytania dodawaj jako nowe `id`**, nie podmieniaj starych. Wtedy porównanie na wspólnych pytaniach zostaje czyste.
- **Nie przesadzaj z interpretacją małych zmian.** Zmiana o najwyżej 4 pytania przy 20 (około 20 p.p.; 2 pytania przy 10) może być zwykłą zmiennością odpowiedzi, bo przy tak niestabilnych odpowiedziach AI kilka pytań potrafi się „przełączyć” w obie strony między testami. Podawaj zmianę w liczbie pytań, nie tylko w procentach. Prawdziwy efekt działań widać jako trend przez 2-3 miesiące albo jako konkretne zmiany: firma zaczęła się pojawiać w pytaniach, w których cytowany jest katalog, do którego właśnie się dodała.
- **Uruchomienie porównania:** `python scripts/licz_wynik.py wyniki-nowe.json --poprzedni wyniki-stare.json --md metryki.md`.
