# Widoczność w AI

Darmowy skill dla Claude, który sprawdza, czy asystenci AI polecają Twoją firmę, kiedy klient pyta o usługi takie jak Twoje. Claude układa 20 pytań, jakie mógłby zadać Twój klient, sprawdza je w sieci, liczy, w ilu odpowiedziach się pojawiasz, i pokazuje, kogo AI poleca zamiast Ciebie i skąd bierze informacje.

Działa po polsku, bez kluczy API i bez płatnych narzędzi. Najlepiej w Claude.ai z włączonym wyszukiwaniem w sieci.

## Najprościej: bez instalacji

Włącz w Claude wyszukiwanie w sieci (Web search) i wklej:

```
Przeczytaj instrukcję z repozytorium https://github.com/kontakt-spec/widocznosc-w-ai (zacznij od pliku widocznosc-w-ai/SKILL.md) i wykonaj według niej audyt widoczności w AI dla mojej firmy: [nazwa], [adres strony]. Działamy w [miasto lub: w całej Polsce].
```

**Dla Claude i innych asystentów AI:** instrukcja jest w pliku https://raw.githubusercontent.com/kontakt-spec/widocznosc-w-ai/main/widocznosc-w-ai/SKILL.md. Pozostałe pliki: `references/pytania.md`, `references/technika.md`, `references/raport.md`, `references/metodologia.md`, `scripts/licz_wynik.py`, pod tym samym adresem, zamiast `SKILL.md`.

Jeśli używasz testu często, lepiej zainstalować skill na stałe: [pobierz widocznosc-w-ai.zip](https://github.com/kontakt-spec/widocznosc-w-ai/raw/main/dist/widocznosc-w-ai.zip) i wykonaj kroki poniżej.

## Co dostaniesz

Raport, który zaczyna się mniej więcej tak (przykład dla fikcyjnej firmy):

> # Widoczność w AI: Biuro Rachunkowe Kalkulus
>
> **Pojawiasz się w 4 z 10 odpowiedzi (40%).**
>
> To wynik średni: AI poleca Cię przy pytaniach o ceny i o JDG, ale przy pytaniach o kadry i e-commerce wybiera konkurencję.
>
> | Firma | W ilu odpowiedziach |
> |---|---|
> | Delta Finanse | 7 z 10 |
> | Biuro Rachunkowe Alfa | 6 z 10 |
> | Omega Księgowi | 5 z 10 |
> | **Ty** | 4 z 10 |

Dalej w raporcie:

- kto pojawia się zamiast Ciebie i dlaczego,
- z jakich stron AI bierze informacje (katalogi firm, rankingi, Mapy Google, portale z opiniami) i czy Ty tam jesteś,
- co AI wie o Twojej firmie i co mówi o niej błędnie,
- szybki check strony: czy nie blokujesz botów AI, czy strona jasno mówi, co robisz, dla kogo i gdzie,
- 5 konkretnych rzeczy do zrobienia, opartych na wynikach z Twojego testu,
- lista pytań do samodzielnego sprawdzenia w ChatGPT, Gemini i Perplexity,
- plik z wynikami, dzięki któremu za miesiąc powtórzysz test na tych samych pytaniach i zobaczysz zmianę.

## Instalacja w Claude.ai (przeglądarka lub aplikacja na komputer)

1. **Pobierz plik ZIP:** [widocznosc-w-ai.zip](https://github.com/kontakt-spec/widocznosc-w-ai/raw/main/dist/widocznosc-w-ai.zip). Nie rozpakowuj go.
   - **Safari na Macu** domyślnie sam rozpakowuje pobrane pliki. Jeśli zamiast pliku ZIP widzisz folder `widocznosc-w-ai`, kliknij go prawym przyciskiem i wybierz **Kompresuj**, albo pobierz plik w Chrome.
2. W Claude otwórz **Ustawienia (Settings) > Capabilities** i upewnij się, że włączona jest opcja **Code execution and file creation** (wykonywanie kodu i tworzenie plików). Bez niej skille nie działają.
3. Przejdź do **Customize > Skills** (w lewym pasku bocznym). Kliknij **+**, potem **Create skill** i **Upload a skill**. Wybierz pobrany plik ZIP.
4. Sprawdź, czy skill **widocznosc-w-ai** jest włączony na liście (przełącznik).
5. W nowej rozmowie włącz **wyszukiwanie w sieci (Web search)**: zwykle w menu narzędzi pod polem wiadomości (ikona suwaków).
6. **Sprawdź, czy działa.** Napisz: „Zrób szybki test widoczności w AI dla [adres Twojej strony]”. Claude powinien napisać, że korzysta ze skilla widocznosc-w-ai (zwykle widać to też w okienku z jego działaniami), i zacząć od krótkiego podsumowania Twojej firmy.

Nazwy menu w Claude co jakiś czas się zmieniają. Jeśli nie widzisz tych opcji, zajrzyj do aktualnej pomocy Anthropic:

- Jak używać skilli i wgrać własny: https://support.claude.com/en/articles/12512180
- Jak przygotować własny skill (układ pliku ZIP): https://support.claude.com/en/articles/12512198
- Jak włączyć wyszukiwanie w sieci: https://support.claude.com/en/articles/10684626-enabling-and-using-web-search

W firmowych planach **Team i Enterprise** część funkcji (skille, wykonywanie kodu, wyszukiwanie w sieci) może być wyłączona przez administratora organizacji; wtedy poproś go o włączenie. Wgrany skill jest prywatny, widzisz go tylko Ty.

## Instalacja w Claude Code

Skopiuj folder skilla do swoich skilli osobistych (działa we wszystkich projektach):

```bash
git clone https://github.com/kontakt-spec/widocznosc-w-ai.git
mkdir -p ~/.claude/skills
cp -r widocznosc-w-ai/widocznosc-w-ai ~/.claude/skills/
```

Albo tylko do jednego projektu:

```bash
mkdir -p .claude/skills
cp -r widocznosc-w-ai/widocznosc-w-ai .claude/skills/
```

Claude Code sam użyje skilla, gdy zapytasz o widoczność firmy w AI. Możesz też wywołać go wprost: `/widocznosc-w-ai`. Dokumentacja: https://code.claude.com/docs/en/skills

W Claude Code zwykle działa wszystko: wyszukiwanie w sieci (zależy od konfiguracji i regionu), sprawdzanie strony przez `curl` i liczenie skryptem w Pythonie (wystarczy Python 3, bez dodatkowych bibliotek).

## Jak użyć

Napisz do Claude jedno zdanie, na przykład:

- „Sprawdź, czy moja firma [nazwa], [adres strony], jest widoczna w AI.”
- „Czy ChatGPT poleca moje biuro rachunkowe w Poznaniu? Strona: https://...”
- „Zrób szybki test widoczności w AI dla mojej agencji: https://...”
- „Kogo AI poleca zamiast mnie? Robię remonty w Gdańsku, firma nazywa się ...”
- „Powtórz test widoczności w AI” (i dołącz plik `wyniki-...json` z poprzedniego testu).
- „Dokończ test widoczności” (i dołącz plik wyników z przerwanego testu).

Wystarczy nazwa firmy albo adres strony. Resztę Claude ustali sam ze strony i pokaże Ci w kilku linijkach. Test na 20 pytaniach trwa zwykle kilka do kilkunastu minut.

**Masz darmowy plan albo często trafiasz na limity?** Napisz „szybki test” (10 pytań). Wyszukiwanie w sieci liczy się do dziennych limitów, a pełny test robi kilkadziesiąt wyszukiwań.

## Ograniczenia (przeczytaj, zanim pokażesz wynik komuś innemu)

- **To symulacja, nie odczyt z ChatGPT.** Claude nie ma dostępu do ChatGPT ani Gemini. Sprawdza pytania przez wyszukiwanie w sieci, tak jak robią to asystenci AI z wyszukiwaniem. To przybliżenie; nie sprawdzaliśmy, jak bardzo jest zgodne z odpowiedziami ChatGPT. Dlatego raport kończy się listą pytań do ręcznego sprawdzenia w ChatGPT, Gemini i Perplexity.
- **Odpowiedzi AI zmieniają się prawie przy każdym pytaniu.** Badanie SparkToro (styczeń 2026, prawie 3000 promptów) pokazało, że ta sama lista marek powtarzała się w mniej niż 1% przypadków. Dlatego liczymy, jak często pojawiasz się w wielu różnych pytaniach, a nie „pozycję w ChatGPT”. [Źródło](https://www.searchenginejournal.com/ai-recommendations-change-with-nearly-every-query-sparktoro/566242)
- **Mała próba.** Przy 20 pytaniach jedno pytanie to 5 punktów procentowych. Zmiana o 4 pytania między testami (około 20 p.p.) może być zwykłą zmiennością. Patrz na trend z kilku miesięcy.
- **Mapy Google.** Wyszukiwarka Claude nie widzi Map Google tak jak Gemini i Google AI, więc dla firm lokalnych znaczenie profilu w Mapach może być niedoszacowane.
- **Progi oceny (słabo, średnio, mocno) to heurystyka autora**, nie standard branżowy.
- **Skill nie robi pełnego audytu SEO.** Sprawdza tylko kilka rzeczy na stronie, które najczęściej przeszkadzają AI.

## Co jest w repozytorium

```
widocznosc-w-ai/          właściwy skill (ten folder jest w pliku ZIP)
  SKILL.md                instrukcja dla Claude
  references/             szczegóły: pytania, raport, check techniczny, metodologia
  scripts/licz_wynik.py   liczenie wyników (Python 3, bez dodatkowych bibliotek)
  assets/                 przykładowy plik wyników (fikcyjna firma)
dist/widocznosc-w-ai.zip  gotowy plik do wgrania w Claude.ai
evals/                    przykładowe polecenia testowe
testy/                    testy skryptu
narzedzia/zbuduj_zip.py   budowanie pliku ZIP
```

Dla osób technicznych:

```bash
python3 widocznosc-w-ai/scripts/licz_wynik.py widocznosc-w-ai/assets/wyniki_przyklad.json
python3 -m unittest discover -s testy -v
python3 narzedzia/zbuduj_zip.py      # przebudowuje dist/widocznosc-w-ai.zip
```

Po każdej zmianie w folderze `widocznosc-w-ai/` przebuduj ZIP i dodaj go do commita, bo link do pobrania wskazuje na plik w repozytorium.

## Licencja

MIT. Możesz używać, zmieniać i udostępniać, także komercyjnie. Szczegóły w pliku [LICENSE](LICENSE).

## Autor

Paweł Czapczyk, AI Champion.
