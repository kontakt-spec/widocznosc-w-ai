# Jak ułożyć zestaw pytań

Ten plik czytasz w kroku 2, zanim napiszesz pytania. Od jakości pytań zależy cały audyt: jeśli pytania brzmią jak zapytania do Google albo jak tekst marketingowy, wynik powie niewiele o tym, co widzi prawdziwy klient.

## Spis treści

1. Zasady pisania pytań
2. Kategorie i proporcje
3. Lokalizacja i zasięg
4. Pytania o markę
5. Przykłady dla kilku branż
6. Kontrola przed startem

## 1. Zasady pisania pytań

Pisz tak, jak właściciel małej firmy albo klient indywidualny pisze do ChatGPT na telefonie:

- **Po polsku, potocznie.** „polecisz kogoś do…”, „ogarnie mi ktoś…”, „szukam…”, „jaka firma…”, „gdzie znajdę…”. Literówki i brak polskich znaków są dopuszczalne w 1-2 pytaniach, bo tak ludzie piszą.
- **Różna długość.** Część krótka (5-8 słów), część średnia, 3-5 pytań długich z kontekstem: „mam małą firmę budowlaną w Gdańsku, 6 osób, i księgowa mi odchodzi. kogo polecasz?”.
- **Z perspektywy klienta, nie firmy.** Klient nie zna branżowych nazw usług. Nie pisze „outsourcing procesów kadrowo-płacowych”, pisze „kto mi będzie robił wypłaty dla pracowników”.
- **Bez nazwy sprawdzanej firmy** w pytaniach niebrandowych. To twarda zasada: pytanie z nazwą firmy zawsze ją „znajdzie”, więc zawyżyłoby wynik. Skrypt sam wykrywa takie pytania i przenosi je do pytań o markę.
- **Wyjątek: nazwa opisowa.** Gdy firma nazywa się zwykłymi słowami usługi i miasta („Fizjoterapia Lublin”, „Remonty Gdańsk”, „Biuro Rachunkowe Poznań”), naturalne pytania klientów muszą zawierać te słowa. Ustaw wtedy `firma.nazwa_opisowa: true` i pisz pytania normalnie, unikając tylko wyróżniającej części nazwy (np. „Plus”, nazwiska, wymyślonego słowa). Skrypt takich pytań nie przeniesie, tylko ostrzeże. Przy takiej nazwie firmę na liście w wynikach wpisuj tylko wtedy, gdy to naprawdę ona (ta sama strona lub adres), a nie dowolny wynik z tymi słowami.
- **Nazwa z wyróżniającym członem i słowami usługowymi** (np. „RUDEK Gabinety Rehabilitacji Medycznej”): to nie jest nazwa opisowa. Zostaw `nazwa_opisowa: false`, aliasy oprzyj na wyróżniającym członie („Rudek”), a w pytaniach swobodnie używaj słów usługowych („gabinety rehabilitacji w Rzeszowie”), byle bez członu „Rudek”. Skrypt rozpoznaje firmę po pełnej nazwie i aliasach, więc samo „gabinety rehabilitacji” nie liczy się jako wzmianka o firmie. Jeśli takie pytanie zwraca głównie profile tej firmy, napisz o tym w raporcie jako o możliwym zawyżeniu.
- **Jedna intencja na pytanie.** Nie łącz „polecisz biuro i ile to kosztuje i czy warto” w jedno.
- **Realne, nie wymyślone potrzeby.** Opieraj się na usługach i klientach, które firma faktycznie obsługuje (ze strony lub z rozmowy). Pytanie o usługę, której firma nie świadczy, mierzy szum.
- **Nie powtarzaj tego samego pytania innymi słowami** więcej niż 2 razy. Lepiej pokryć więcej potrzeb niż mierzyć jedną potrzebę pięć razy.

Dlaczego to ważne: badanie SparkToro pokazało, że prompty pisane przez prawdziwych ludzi na ten sam temat są do siebie bardzo mało podobne (średnie podobieństwo semantyczne 0,081). Zestaw pytań ma więc odwzorować tę różnorodność, a nie jedno „idealne” zapytanie.

## 2. Kategorie i proporcje

| Kategoria (`kategoria` w JSON) | Co sprawdza | Szybki (10) | Domyślny (20) | Pełny (30) |
|---|---|---|---|---|
| `polecenie`: polecenie wprost | Klient wie, czego szuka, i prosi o rekomendację | 3 | 5 | 7 |
| `problem`: problem bez nazwy usługi | Klient opisuje kłopot, nie zna nazwy usługi | 3 | 5 | 7 |
| `ranking`: ranking, porównanie | „Najlepsze…”, „top…”, „porównaj…” | 1 | 3 | 4 |
| `kryteria`: budżet, specjalizacja, branża klienta | Doprecyzowana potrzeba: cena, branża, wielkość firmy, termin | 2 | 5 | 8 |
| `alternatywy`: alternatywy dla konkurenta | „Kto zamiast X?”, „coś jak X, ale taniej” | 1 | 2 | 4 |
| `marka`: pytania o markę | Co AI wie o firmie (liczone osobno) | +2 | +3 | +3 |

Liczba trybu (10, 20, 30) to liczba pytań **niebrandowych**, czyli mianownik wskaźnika widoczności. Pytania o markę dochodzą ponad tę liczbę.

Uzasadnienie proporcji:

- **`polecenie` i `problem` po równo, najwięcej.** To dwa najczęstsze sposoby, w jakie ludzie zaczynają rozmowę z asystentem. Pytania problemowe są ważne, bo właśnie w nich AI „decyduje” za klienta, jakiej usługi potrzebuje i kogo polecić, a firmy rzadko są na nie przygotowane.
- **`kryteria` mocno reprezentowane.** Rozmowy z AI są dłuższe i bardziej szczegółowe niż wpisy w Google. To tu wychodzi specjalizacja: firma, która jasno pisze „obsługujemy e-commerce”, wygrywa pytania o e-commerce.
- **`ranking` mniej.** Pytania rankingowe dają podobne wyniki (te same artykuły „top 10”), więc 3 z 20 wystarczą, żeby sprawdzić, czy firma jest w tych zestawieniach.
- **`alternatywy` tylko gdy znamy konkurentów.** Konkurenci podani przez użytkownika albo, przy oczywistych przypadkach (zwykle duże marki), wskazani przez Ciebie w `konkurenci_wywnioskowani`. Bez konkurentów rozdziel te pytania na `polecenie` i `kryteria`. W pytaniu wpisz nazwę konkurenta, nigdy sprawdzanej firmy; konkurenta, o którego pytano, nie wpisujesz potem na listę firm w odpowiedzi.
- **`marka` osobno.** Pytanie z nazwą firmy nie mówi nic o tym, czy klient ją znajdzie, ale mówi dużo o tym, czy AI opisuje ją poprawnie.

Gdy firma ma kilka wyraźnie różnych usług (np. biuro rachunkowe z księgowością i kadrami), rozłóż pytania mniej więcej proporcjonalnie do tego, co jest dla firmy najważniejsze. Jeśli nie wiesz, co jest najważniejsze, zapytaj jednym zdaniem albo przyjmij kolejność ze strony.

## 3. Lokalizacja i zasięg

- **Firma lokalna** (fryzjer, gabinet, biuro rachunkowe, firma budowlana): w około 80% pytań podaj miasto lub region, bo tak ludzie piszą do AI, a symulacja nie zna lokalizacji użytkownika. Mieszaj formy: „w Poznaniu”, „Poznań”, „pod Poznaniem”, „w Wielkopolsce”, dzielnica („na Jeżycach”). Pozostałe pytania bez miasta pokażą, czy firma przebija się szerzej (zwykle nie, i to normalne).
- **Firma ogólnopolska lub online** (agencja, software house, szkolenia online): większość pytań bez miasta, 2-4 pytania z dużymi miastami („w Warszawie”, „w Krakowie”), bo klienci i tak często dopisują miasto.
- **Firma działająca w kilku miastach:** rozłóż pytania między 2-3 najważniejsze lokalizacje.

## 4. Pytania o markę

2-3 pytania, np.:

- „co wiesz o firmie [nazwa] z [miasto]?”
- „[nazwa] opinie”
- „czy [nazwa] zajmuje się [główna usługa]?” albo „ile kosztuje [usługa] w [nazwa]?”

Przy każdej odpowiedzi zapisz w JSON listy `poprawne`, `bledne` i `brakujace`, porównując z tym, co jest na stronie firmy lub co podał użytkownik. Błędne fakty (zły adres, zła oferta, stary telefon, firma pomylona z inną o podobnej nazwie) to jedne z najcenniejszych ustaleń audytu.

## 5. Przykłady dla kilku branż

Przykłady pokazują ton i różnorodność. Nie kopiuj ich, dopasuj do konkretnej firmy.

### Biuro rachunkowe, lokalne (Poznań)

- polecenie: „polecisz dobre biuro rachunkowe w Poznaniu dla jdg?”
- polecenie: „szukam księgowej w Poznaniu, kogoś ogarniętego i nie za drogiego”
- problem: „toniemy w fakturach i nie ogarniamy ZUS-ów, kto w Poznaniu może to wziąć na siebie?”
- problem: „zaczynam działalność w przyszłym miesiącu i nie wiem kompletnie nic o podatkach, do kogo się zgłosić w Poznaniu”
- ranking: „najlepsze biura rachunkowe w Poznaniu ranking”
- kryteria: „biuro rachunkowe Poznań dla sklepu internetowego, sprzedaję na Allegro i Amazonie”
- kryteria: „ile kosztuje księgowość dla małej spółki z o.o. w Poznaniu i kogo polecasz”
- alternatywy: „jakie są alternatywy dla [konkurent] w Poznaniu?”

### Agencja marketingowa B2B, ogólnopolska

- polecenie: „polecisz agencję, która robi kampanie na LinkedIn dla firm B2B?”
- problem: „mamy dobry produkt dla firm, ale nikt o nas nie wie, a sprzedawcy dzwonią na zimno bez efektu. komu to zlecić?”
- problem: „nasza strona nie daje żadnych zapytań od klientów, kto w Polsce może to naprawić?”
- ranking: „top agencje marketingu B2B w Polsce”
- kryteria: „agencja marketingowa dla firmy produkcyjnej, budżet około 10 tys. zł miesięcznie”
- kryteria: „szukam agencji, która zna branżę IT i robi content po angielsku”
- alternatywy: „coś jak [konkurent], ale dla mniejszych firm”

### Firma remontowo-budowlana, lokalna (Gdańsk)

- polecenie: „kto robi dobre remonty mieszkań w Gdańsku?”
- problem: „kupiłem mieszkanie w stanie deweloperskim w Gdańsku i nie wiem od czego zacząć, kogo polecasz do wykończenia”
- problem: „zalało mi łazienkę, trzeba skuć płytki i zrobić od nowa, ktoś z Trójmiasta?”
- ranking: „najlepsze firmy wykończeniowe Trójmiasto”
- kryteria: „ekipa do remontu kuchni w Gdańsku, termin w ciągu miesiąca”
- kryteria: „firma remontowa Gdańsk z gwarancją i fakturą VAT, mieszkanie 50 m2”

### Szkolenia i doradztwo dla firm (online)

- polecenie: „polecisz szkolenie z AI dla pracowników małej firmy, po polsku?”
- problem: „pracownicy marnują mnóstwo czasu na maile i raporty, słyszałem że AI może pomóc, kto nas tego nauczy?”
- ranking: „najlepsze kursy ChatGPT dla firm w Polsce”
- kryteria: „szkolenie z AI dla biura rachunkowego, 10 osób, zdalnie”
- kryteria: „kurs AI dla właściciela firmy usługowej, bez programowania”

### Gabinet usługowy (fizjoterapia, Lublin)

- polecenie: „dobry fizjoterapeuta w Lublinie od kręgosłupa?”
- problem: „od tygodnia boli mnie szyja po pracy przy komputerze, do kogo w Lublinie się wybrać”
- kryteria: „fizjoterapia Lublin na NFZ czy prywatnie, gdzie szybko przyjmą”
- kryteria: „fizjoterapeuta dla biegacza Lublin, kontuzja kolana”

## 6. Kontrola przed startem

Zanim zaczniesz sprawdzanie, przejrzyj listę i upewnij się, że:

- żadne pytanie niebrandowe nie zawiera nazwy firmy ani jej aliasu (przy `nazwa_opisowa: true`: ani wyróżniającej części nazwy),
- proporcje kategorii mniej więcej zgadzają się z tabelą,
- pytania pokrywają główne usługi i głównych klientów firmy,
- są pytania krótkie i długie, potoczne i rzeczowe,
- każde pytanie ma `id` (P01, P02…), które zostanie na stałe. Za miesiąc te same `id` i ta sama treść pozwolą porównać wyniki.
