# Szybki check techniczny strony

Ten plik czytasz w kroku 5, jeśli znasz adres strony firmy albo jeśli pobranie strony w kroku 1 się nie udało. To lekki przegląd 6 elementów (w raporcie 8 wierszy, bo boty AI są w trzech), które realnie wpływają na to, czy asystenci AI mogą przeczytać i zrozumieć stronę. Nie udawaj pełnego audytu SEO.

Zasada uczciwości: jeśli narzędzie nie pozwoliło czegoś zobaczyć (np. pobieranie strony zwraca tylko tekst bez kodu HTML, więc nie widać danych strukturalnych), napisz „nie udało się sprawdzić”, a nie „brak”. Fałszywe „brak” prowadzi właściciela firmy do niepotrzebnej pracy.

Stany do tabeli w raporcie: **w porządku**, **do poprawy**, **problem**, **pośredni sygnał blokady** (widać objaw, ale nie przyczynę), **do sprawdzenia**, **nie udało się sprawdzić**. Jeśli ustalenie nie pasuje do żadnego wiersza szablonu (np. ochrona Cloudflare), dodaj osobny wiersz.

## Jak pobierać

Limit: do 4 pobrań w tym kroku (zwykle robots.txt, strona główna, oferta lub cennik, llms.txt), liczonych osobno od budżetu kroku 3. Jeśli stronę główną przeczytałeś już w kroku 1, nie pobieraj jej drugi raz.

- **Claude Code / Cowork / terminal:** `curl -sL -A "Mozilla/5.0" https://domena.pl/robots.txt` oraz to samo dla strony głównej. Surowy HTML pokazuje dane strukturalne i tagi. W części środowisk ruch wychodzący idzie przez serwer pośredniczący, który blokuje część domen; wtedy curl się nie połączy i to nie mówi nic o stronie firmy.
- **Claude.ai:** narzędzie do pobierania stron (web fetch) dla `/robots.txt` i strony głównej. Wynik bywa przerobiony na tekst, więc dane strukturalne mogą być niewidoczne. Jeśli kod ma dostęp do sieci, możesz spróbować pobrać surowy HTML przez Pythona (`urllib.request`).

## Jak czytać błędy narzędzia pobierania

- **`ROBOTS_DISALLOWED` (albo podobny komunikat, że robots.txt nie pozwala) od narzędzia Claude:** to mocny sygnał, że robots.txt strony blokuje boty Anthropic (Claude-User działa na prośbę użytkownika) i prawdopodobnie także inne boty AI, bo takie blokady zwykle obejmują je razem. Wpisz w raporcie jako **ważne ustalenie**, stan „problem” jeśli widzisz treść robots.txt z blokadą, a „pośredni sygnał blokady”, jeśli robots.txt też nie dało się pobrać. Co zrobić: osoba od strony powinna otworzyć `https://domena/robots.txt` w przeglądarce, poszukać reguł `Disallow` dla `*`, `ClaudeBot`, `Claude-User`, `Claude-SearchBot`, `GPTBot`, `OAI-SearchBot`, `PerplexityBot` i zdecydować, które boty wpuścić. Częstą przyczyną jest wtyczka SEO lub bezpieczeństwa albo ustawienie hostingu.
- **Ekran „potwierdź, że nie jesteś robotem”, kod 403 lub 503 ze stroną Cloudflare** (albo innej usługi ochrony): stan **do sprawdzenia**. Taka ochrona może zatrzymywać także boty AI, ale z Twojego środowiska nie da się tego ustalić. Nie testuj botów przez podszywanie się pod ich nazwy (user-agent): odpowiedź dla Twojego adresu IP nie mówi nic o tym, co dostaną prawdziwe boty z serwerów OpenAI czy Anthropic. W raporcie napisz, że osoba z dostępem do Cloudflare powinna sprawdzić sekcję **AI Crawl Control** (zakładka z listą botów i akcją Allow/Block) oraz ustawienia ochrony przed botami dla domeny. Nazwy w panelu Cloudflare się zmieniają, więc formułuj to ostrożnie. Źródło: https://developers.cloudflare.com/ai-crawl-control/get-started/
- **`SITE_BLOCKED` lub podobny komunikat dla archiwów i stron trzecich:** to ograniczenie narzędzia, nie strony firmy. Nie wyciągaj z tego wniosków.
- **Timeout, błąd sieci:** spróbuj raz ponownie w ramach budżetu, potem „nie udało się sprawdzić”.

## 1. robots.txt a boty AI

Pobierz `/robots.txt`. Sprawdź reguły dla poniższych botów i dla `User-agent: *`. Bot podlega najbardziej szczegółowej grupie, która go wymienia z nazwy; jeśli żadna go nie wymienia, obowiązuje grupa `*`.

| Bot (token w robots.txt) | Firma | Do czego służy | Co oznacza blokada |
|---|---|---|---|
| `Googlebot` | Google | Wyszukiwarka Google, w tym AI Overviews i AI Mode | **Poważny problem:** strona znika z Google i z jego odpowiedzi AI. Treść w AI Overviews ograniczają też tagi `nosnippet` i `max-snippet` |
| `OAI-SearchBot` | OpenAI | Pokazywanie stron w wynikach wyszukiwania ChatGPT | **Poważny problem:** strona może nie pojawiać się jako źródło w ChatGPT Search |
| `Claude-SearchBot` | Anthropic | Poprawa wyników wyszukiwania w Claude | **Poważny problem** dla widoczności w wyszukiwaniu Claude |
| `PerplexityBot` | Perplexity | Pokazywanie i linkowanie stron w wynikach Perplexity (według Perplexity nie służy do trenowania modeli) | **Poważny problem** dla widoczności w Perplexity |
| `Google-Extended` | Google | Token (nie osobny robot): czy treści mogą trenować modele Gemini i służyć do „ugruntowania” odpowiedzi w aplikacji Gemini | Według Google nie wpływa na wyszukiwarkę Google ani na pozycje, ale **może ograniczyć użycie strony w odpowiedziach aplikacji Gemini**. Wpływu na AI Overviews Google jednoznacznie nie opisuje |
| `ChatGPT-User` | OpenAI | Wejście na stronę, gdy użytkownik ChatGPT o coś pyta | Według OpenAI reguły robots.txt mogą tu nie mieć zastosowania, bo wejście inicjuje użytkownik. Ograniczony efekt |
| `Claude-User` | Anthropic | Wejście na stronę na prośbę użytkownika Claude | Claude nie przeczyta strony na prośbę użytkownika (tak działa `ROBOTS_DISALLOWED`) |
| `Perplexity-User` | Perplexity | Wejście na stronę na prośbę użytkownika (według Perplexity zwykle nie stosuje się do robots.txt) | Ograniczony efekt |
| `GPTBot` | OpenAI | Zbieranie treści do trenowania modeli | Rezygnacja z treningu. Świadomy wybór; mniejszy wpływ na wyszukiwanie, ale model „zapamięta” o firmie mniej |
| `ClaudeBot` | Anthropic | Zbieranie treści do trenowania modeli | Jak przy GPTBot |
| `Applebot-Extended` | Apple | Token (nie robot): czy treści zebrane przez Applebota mogą trenować modele Apple | Strona dalej może być w wynikach wyszukiwania Apple |

Jak to opisać w raporcie:

- Blokada `Googlebot`, `OAI-SearchBot`, `Claude-SearchBot` lub `PerplexityBot` (wprost albo przez `User-agent: *` z `Disallow: /`) to najważniejsze ustalenie techniczne. Napisz, że to prawdopodobnie ustawienie wtyczki, hostingu lub firewalla (np. opcja „blokuj boty AI”) i że warto je zmienić, jeśli firma chce być polecana.
- Blokada samych `GPTBot`, `ClaudeBot` lub `Applebot-Extended` to legalny wybór właściciela. Nie strasz, napisz krótko, co zyskuje i co traci. `Google-Extended` opisz osobno, bo wpływa też na odpowiedzi w aplikacji Gemini.
- Brak pliku robots.txt (błąd 404) oznacza, że nic nie jest blokowane. To nie jest problem.
- Robots.txt nie jest jedyną blokadą. Hostingi i usługi typu Cloudflare mogą blokować boty na poziomie serwera (patrz wyżej).

Źródła (sprawdzone październik 2026; nazwy botów się zmieniają, więc jeśli masz wyszukiwanie, szybko zweryfikuj):

- OpenAI: https://developers.openai.com/api/docs/bots
- Anthropic: https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
- Perplexity: https://docs.perplexity.ai/docs/resources/perplexity-crawlers
- Google: https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers
- Apple: https://support.apple.com/en-us/119829 (strona „About Applebot”)

## 2. Treść widoczna bez JavaScriptu

Sprawdź **stronę główną i stronę z ofertą lub cennikiem**, jeśli istnieje. Jeśli pobrana strona jest prawie pusta (sam tytuł, menu, „włącz JavaScript”), a w przeglądarce ma dużo treści, albo gdy w pobranym kodzie nie ma kluczowych informacji (np. cen na stronie cennika), treść jest doładowywana w przeglądarce. Według analizy Vercel z grudnia 2024 roboty OpenAI, Anthropic i Perplexity nie wykonywały wtedy JavaScriptu, więc mogą jej nie widzieć (Google, w tym Gemini, renderuje JavaScript). Stan mógł się zmienić, więc pisz o tym jako o ryzyku, nie pewniku. Powiąż to z wynikami, np. gdy w pytaniach o ceny AI podawał ceny z cudzych rankingów. Źródło: https://vercel.com/blog/the-rise-of-the-ai-crawler

## 3. Czy strona jasno mówi: co, dla kogo, gdzie

Przeczytaj tytuł strony, nagłówek główny i pierwszy ekran tekstu. Asystent AI dopasowuje firmę do pytania głównie po tym, co strona wprost mówi. Sprawdź, czy w pierwszych zdaniach widać:

- **co** firma robi, nazwane słowami klienta (nie tylko hasło typu „Twój partner w rozwoju”),
- **dla kogo** (np. „dla JDG i małych spółek”, „dla firm produkcyjnych”),
- **gdzie** (miasto, region albo „w całej Polsce, zdalnie”).

Zestaw to z pytaniami, w których firmy nie było na liście. Jeśli firma przegrała wszystkie pytania o e-commerce, a na stronie słowo „e-commerce” nie pada ani razu, to konkretne działanie do raportu.

## 4. Dane strukturalne (Organization / LocalBusiness)

W surowym HTML szukaj `application/ld+json` i typów `Organization`, `LocalBusiness` lub podtypów (`AccountingService`, `ProfessionalService`, `HomeAndConstructionBusiness`, `MedicalBusiness` itd.). Sprawdź, czy zawierają nazwę, adres, telefon, adres strony i ewentualnie `sameAs` (profile w sieci).

Dane strukturalne pomagają maszynom jednoznacznie odczytać, kim jest firma i gdzie działa. Nie ma twardych dowodów, że same z siebie podnoszą widoczność w AI, więc przedstaw je jako porządek, a nie magiczny przycisk. Jeśli widziałeś tylko tekst bez HTML: „nie udało się sprawdzić”.

## 5. Spójność nazwy, adresu i telefonu

Porównaj nazwę, adres i telefon ze strony z tym, co widziałeś w wynikach wyszukiwania (Mapy Google, katalogi firm, portale z opiniami). Różnice (stary adres, inny telefon, inna nazwa) utrudniają AI połączenie wzmianek w jedną firmę. Wypisz konkretne rozbieżności i miejsca, gdzie je widać.

## 6. llms.txt

Sprawdź, czy istnieje `/llms.txt`. Jeśli adres zwraca zwykłą stronę HTML (kod 200, ale zamiast tekstu jest kod strony, np. strona główna albo „nie znaleziono”), to pliku **nie ma**: tak działają strony, które każdy nieznany adres kierują na stronę główną. Opisz uczciwie: to propozycja standardu (https://llmstxt.org), a nie wymóg. Nie ma potwierdzonego wpływu na to, czy AI poleca firmę. John Mueller z Google powiedział w podcaście Search Off the Record (relacja z czerwca 2026), że takie pliki nie pomagają systemom AI odróżnić dobrej strony od słabej, choć mogą pomóc agentowi, który już jest na stronie. Jeśli llms.txt podaje inne dane niż strona (np. ceny), to jest rozbieżność warta wpisania. Nie dawaj llms.txt jako działania z listy 5 najważniejszych, chyba że wszystko inne jest w porządku. Źródło relacji: https://letsdatascience.com/news/googles-mueller-says-llmstxt-wont-guide-llm-recommendations-8afc3fa3

## Format wyniku do raportu

Tabela z szablonu w `references/raport.md`: 6 elementów w 8 wierszach (boty AI w trzech: wyszukiwanie, Google-Extended, trening), stan i jedno zdanie, co to znaczy. Dodatkowe ustalenia (np. Cloudflare) jako osobne wiersze.

Te same wiersze zapisz w pliku wyników w polu `technika` (format w `references/metodologia.md`, sekcja 6). Skrypt wypisze je w metrykach, a przy kontynuacji testu nie trzeba będzie powtarzać tego kroku.
