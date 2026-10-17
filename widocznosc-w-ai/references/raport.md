# Szablon raportu

Ten plik czytasz w kroku 6, zanim napiszesz raport. Raport czyta właściciel małej firmy, zwykle na telefonie, między jednym klientem a drugim. Dlatego:

- najważniejsze na górze, szczegóły w załączniku,
- zwykły język; jeśli musisz użyć terminu (share of voice, robots.txt), wyjaśnij go w jednym zdaniu przy pierwszym użyciu,
- każde stwierdzenie oparte na danych z tego audytu, z liczbą („w 6 z 20 odpowiedzi”), a nie ogólnik,
- bez długich myślników (pauzy i półpauzy; zamiast nich przecinek, dwukropek albo kropka), bez emoji, bez marketingowego tonu, bez obietnic „pozycji w ChatGPT”,
- część główna (do „Metodologii”) mieści się w około 2 ekranach tekstu.

Liczby bierz z wyniku skryptu `licz_wynik.py` (albo z liczenia ręcznego według `metodologia.md`). Nie zaokrąglaj ich inaczej niż skrypt.

## Szablon

Teksty w [nawiasach kwadratowych] zastąp danymi. Sekcje oznaczone „(jeśli…)” pomiń, gdy warunek nie zachodzi.

```markdown
# Widoczność w AI: [nazwa firmy]

[data badania] · [liczba] pytań klientów + [liczba] o markę · sprawdzone przez: [tryby, np. Claude z wyszukiwaniem w sieci, Claude bez internetu]

## Wynik

**Pojawiasz się w [X] z [N] odpowiedzi ([Y]%).**

[Jeśli użytkownik zadał pytanie tak/nie, np. „czy AI poleca X?”: jedno zdanie bezpośredniej odpowiedzi, np. „Krótko: tak, AI poleca Cię w większości pytań o księgowość online, ale prawie zawsze obok ifirmy i wFirmy.”]

[Jeśli wynik główny nie pochodzi z trybu z wyszukiwaniem: od razu, skąd pochodzi, np. „To wynik Claude bez internetu, czyli tylko pamięć modelu, bez sprawdzania sieci.”]

[Jedno zdanie interpretacji. Dla małej firmy lokalnej odnieś się do progów. Dla dużej marki ogólnopolskiej porównaj z liderami z tabeli konkurentów (np. „Jesteś w 9 z 10, ifirma w 6, wFirma w 5”) i wskaż przegrane kategorie, bo sam próg „mocno” mówi wtedy niewiele.]

Ocena robocza: [niewidoczny / słabo / średnio / mocno]. (Progi to heurystyka autora skilla, nie standard branżowy: 0% niewidoczny, poniżej 15% słabo, 15-40% średnio, powyżej 40% mocno.)

[Jeśli był tryb bez internetu, jedno zdanie: „Bez dostępu do internetu Claude wymienił Cię w [X2] z [N2] odpowiedzi ([Y2]%). To orientacyjnie pokazuje, czy firma zapisała się w pamięci modelu.” Dla małej firmy dopisz, że 0% jest tu normą.]

[Jeśli jest porównanie z poprzednim badaniem, jedno zdanie: „Miesiąc temu: [X0] z [N0], teraz [X] z [N], czyli o [k] pytań [więcej/mniej].” Przy 20 pytaniach zmiana o najwyżej 4 pytania (około 20 p.p.) może być zwykłą zmiennością; powiedz to.]

[Jeśli skrypt zgłosił zależność od pojedynczych źródeł: jedno zdanie zastrzeżenia, np. „Uwaga: 4 z Twoich 6 trafień opierają się na jednym rankingu (rankingi-xyz.pl). Jeśli ten ranking się zmieni, wynik może wyraźnie spaść.”]

## Kto pojawia się zamiast Ciebie

| Firma | W ilu odpowiedziach |
|---|---|
| [firma 1] | [n] z [N] |
| ... (5-10 firm, w kolejności malejącej) | |
| **Ty** (w miejscu wynikającym z liczby) | [X] z [N] |

[1-3 zdania: co łączy firmy z góry listy, na podstawie źródeł. Np. „Trzy pierwsze firmy mają dużo opinii w Mapach Google i są w rankingu na rankingi-xyz.pl, który AI cytował najczęściej.” Jeśli konkurentów wskazał Claude, a nie użytkownik, napisz to.]

Udział w odpowiedziach (share of voice, czyli jaka część wszystkich poleceń firm przypada na Ciebie): [S]%.

## Gdzie AI szuka informacji

| Źródło | Typ | W ilu odpowiedziach | Jesteś tam? |
|---|---|---|---|
| [domena] | [katalog firm / Mapy Google / portal z opiniami / ranking lub artykuł / portal branżowy / social media / strona konkurenta / marketplace] | [n] z [N] | [tak / nie / nie wiem] |
| ... (5-8 źródeł) | | | |

[1-2 zdania: co to znaczy. Np. „AI nie wymyśla poleceń, tylko streszcza to, co znajdzie. Jeśli nie ma Cię w źródłach z tej tabeli, nie masz jak trafić do odpowiedzi.”]

Twoja strona była źródłem w [k] z [N] odpowiedzi.

[„Jesteś tam?” wypełniaj tylko na podstawie tego, co widziałeś w wynikach lub na otwartej stronie. Jeśli nie sprawdzałeś, wpisz „nie wiem”.]

## Co AI wie o Twojej firmie

[Na podstawie pytań o markę. Krótkie listy.]

- Poprawnie: [fakty]
- Błędnie: [fakty i skąd prawdopodobnie pochodzi błąd; tu możesz też wpisać błędne dane o firmie zauważone w innych źródłach, np. stare ceny w rankingu, z zaznaczeniem, skąd są]
- Brakuje: [ważne rzeczy, których AI nie podał, a które są na stronie]

[Jeśli AI pomylił firmę z inną o podobnej nazwie, napisz to wprost, to ważne.]

## Szybki check techniczny strony (jeśli znany jest adres strony)

| Element | Stan | Co to znaczy |
|---|---|---|
| Boty wyszukiwania (Googlebot, OAI-SearchBot, Claude-SearchBot, PerplexityBot) | [w porządku / problem / pośredni sygnał blokady / nie udało się sprawdzić] | [1 zdanie] |
| Google-Extended | [wpuszczony / zablokowany / nie udało się sprawdzić] | Wpływa na trening Gemini i odpowiedzi w aplikacji Gemini, nie na wyszukiwarkę Google. |
| Boty treningowe (GPTBot, ClaudeBot, Applebot-Extended) | [wpuszczone / zablokowane (świadomy wybór) / nie udało się sprawdzić] | [1 zdanie] |
| Treść widoczna bez JavaScriptu (strona główna i oferta lub cennik) | [...] | [...] |
| Czy strona jasno mówi: co, dla kogo, gdzie | [...] | [...] |
| Dane strukturalne (Organization / LocalBusiness) | [...] | [...] |
| Spójność nazwy, adresu i telefonu w sieci | [...] | [...] |
| llms.txt | [jest / nie ma] | Brak potwierdzonego wpływu na polecenia AI, niski priorytet. |
| [Dodatkowe ustalenie, np. ochrona Cloudflare] | [do sprawdzenia] | [1 zdanie i co sprawdzić] |

To nie jest pełny audyt SEO, tylko kilka rzeczy, które najczęściej blokują AI.

## 5 rzeczy do zrobienia (od największego wpływu)

1. **[Działanie w trybie rozkazującym, konkretne.]** [Dlaczego, z liczbą z audytu: „AI cytował [źródło] w [n] z [N] odpowiedzi, a Ciebie tam nie ma.”] Pierwszy krok: [co zrobić dziś, w 15-30 minut].
2. ...
3. ...
4. ...
5. ...

## Metodologia i ograniczenia

- To symulacja: Claude z wyszukiwaniem w sieci odpowiadał na pytania tak, jak zrobiłby to asystent AI. To przybliżenie ChatGPT, Perplexity czy Google AI Mode, a nie ich odpowiedzi; nikt nie zmierzył, jak bardzo są zgodne.
- Odpowiedzi AI zmieniają się prawie przy każdym pytaniu. W badaniu SparkToro (2026, prawie 3000 promptów) ta sama lista marek powtarzała się w mniej niż 1% przypadków. Dlatego liczymy, jak często pojawiasz się w wielu różnych pytaniach, a pozycję na liście pokazujemy tylko informacyjnie.
- [N] pytań to mała próba: jedno pytanie to [100/N] punktów procentowych.
- Wyszukiwarka Claude nie widzi Map Google tak jak Gemini i Google AI, więc znaczenie profilu w Mapach może być tu niedoszacowane.
- Prawdziwe asystenty uwzględniają lokalizację, historię i ustawienia użytkownika. Tu tego nie ma.
- [Inne ograniczenia tego badania, np. pominięte pytania, brak wyszukiwania, liczenie ręczne, strona niedostępna dla narzędzia.]

[Jeśli były założenia (praca bez odpowiedzi użytkownika, niejasna nazwa, wywnioskowani konkurenci): krótka lista „Przyjęte założenia”.]

## Załącznik: pytanie po pytaniu

| # | Pytanie | Jesteś na liście? | Kogo wymieniono | Źródła |
|---|---|---|---|---|
| P01 | [treść] | [tak (poz. 2) / nie] | [firmy] | [domeny] |
| ... | | | | |

## Sprawdź sam w ChatGPT, Gemini i Perplexity

Skopiuj kilka pytań i wklej je do ChatGPT, Gemini i Perplexity (najlepiej w trybie bez historii, np. czat tymczasowy). Jeśli wkleisz mi odpowiedzi, dopiszę je do wyników jako prawdziwe dane z tych narzędzi.

[Lista wszystkich pytań niebrandowych, numerowana z id, każde w osobnej linii, bez komentarzy.]

## Za miesiąc

Zapisz pliki [nazwy plików]. Za miesiąc wgraj plik wyników i napisz „powtórz test widoczności”. Sprawdzę te same pytania i pokażę, co się zmieniło.
```

## Jak dobrać 5 działań

Wybieraj z danych, nie z listy ogólnych porad. Kolejność według wpływu:

1. **Blokada techniczna** (boty wyszukiwania zablokowane, `ROBOTS_DISALLOWED`, pusta strona bez JavaScriptu) albo **strona nieobecna w wyszukiwaniu** (nie pojawia się nawet na pytania o własną nazwę; to „do sprawdzenia”, nie pewnik). Jeśli jest, zawsze pierwsza, bo bez tego reszta nie zadziała.
2. **Brak w najczęściej cytowanych źródłach.** Weź 2-3 domeny z góry tabeli źródeł, w których firmy nie ma. Podaj, w ilu odpowiedziach były cytowane. Konkretnie: „dodaj firmę do [katalog]”, „zgłoś się do autora rankingu [domena]”, „uzupełnij profil w Mapach Google”.
3. **Opinie i profil w Mapach Google**, jeśli Mapy lub portale z opiniami są wysoko w źródłach, a firma ma tam mało opinii lub niepełny profil (tylko jeśli to widziałeś).
4. **Luka w treści strony** powiązana z przegraną kategorią pytań. Np. „Przegrałeś wszystkie 3 pytania o e-commerce, a na stronie nie ma słowa o e-commerce: dodaj podstronę o obsłudze sklepów internetowych.”
5. **Błędne fakty** w odpowiedziach o marce lub w cudzych źródłach. Wskaż, gdzie poprawić (strona, katalog, profil, autor rankingu), jeśli widać źródło błędu.
6. **Treść odpowiadająca na pytania problemowe**, jeśli firma przegrywa właśnie te: krótkie artykuły lub FAQ pisane słowami klienta („co zrobić, gdy…”). Jeśli konkurenci wygrywają poradnikami, napisz to wprost.
7. **Dane strukturalne i spójność danych kontaktowych**, jeśli są braki.

Każde działanie: jedno zdanie co, jedno zdanie dlaczego (z liczbą z audytu), jeden pierwszy krok. Jeśli danych wystarcza tylko na 3 sensowne działania, daj 3 i napisz, dlaczego reszta to byłyby ogólniki. Lepiej 3 trafne niż 5 wymyślonych.

## Nazwy i format plików

Gdy masz system plików, zapisz trzy pliki. `[firma]` to nazwa firmy małymi literami, bez polskich znaków, ze spacjami zamienionymi na myślniki (np. `biuro-rachunkowe-kalkulus`), `[RRRR-MM-DD]` to data badania:

- `raport-widocznosc-ai-[firma]-[RRRR-MM-DD].md`: raport według szablonu,
- `wyniki-[firma]-[RRRR-MM-DD].json`: plik wyników (potrzebny do powtórki i kontynuacji),
- `pytania-[firma].txt`: pytania gotowe do kopiowania, dokładnie w tym formacie:

```text
Pytania do testu widoczności w AI: [nazwa firmy], [RRRR-MM-DD]

P01 [treść pytania]
P02 [treść pytania]
...

Pytania o markę
P21 [treść pytania]
P22 [treść pytania]
```

Bez innych dodatków (bez kategorii, komentarzy i wyników). Id zostają, bo przy powtórce pozwalają dopasować pytania.

W Claude.ai zapisuj pliki w folderze wyjściowym, który środowisko udostępnia do pobierania (jeśli jest), i powiedz użytkownikowi, które pliki ma pobrać. Bez systemu plików: raport w czacie, a pod nim pełny plik wyników w bloku kodu `json` z prośbą o skopiowanie i zapisanie.
