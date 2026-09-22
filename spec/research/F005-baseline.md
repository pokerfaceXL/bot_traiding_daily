# F005 — Moduł regularności dzienna/miesięczna (fala 2)

> Ta fala buduje i testuje TYLKO standalone moduł liczący positive_day_pct/deviation_pct
> na equity curve. Nie uruchamia baseline na realnych danych koszyka (fala 3, osobne
> zadanie, później). Żadne wywołanie `strategy.get_bybit_ohlcv`/`backtest_engine.run_backtest`
> na danych SOLUSDT/ETHUSDT/BTCUSDT/XRPUSDT/DOGEUSDT z zamrożonego protokołu
> (`spec/research/F005-validation-protocol.md`) nie miało miejsca w tej fali. Ten dokument
> celowo nie zawiera żadnych liczb baseline — fala 3 je dopisze osobno, po zmierzeniu.

## Co powstało

- `regularity.py` — standalone moduł (ten sam wzorzec co `costs.py`/`equity.py`/`execution.py`
  z F004): bierze gotową mark-to-market equity curve (jak `backtest_engine.BacktestResult.equity_curve`
  — DataFrame indeksowany znacznikiem czasu, kolumna `equity`) i:
  - `daily_equity_snapshots` — agreguje do end-of-day equity per kalendarzowy dzień
    strefy Europe/Warsaw (ostatni dostępny znacznik w danym dniu), konwersja przez
    `zoneinfo.ZoneInfo("Europe/Warsaw")` (nie stały offset UTC — Polska ma DST).
  - `classify_days` — pełna kalendarzowa seria dni od pierwszego do ostatniego dnia
    krzywej, każdy dzień sklasyfikowany `positive` / `non_positive` (PnL <= 0, w tym
    dokładne zero) / `missing` (brak znacznika equity w tym dniu; PnL liczony względem
    ostatniego znanego znacznika sprzed ewentualnej luki, nie względem kalendarzowo
    poprzedniego dnia).
  - `monthly_regularity` — grupuje po pełnym miesiącu kalendarzowym, liczy
    `positive_day_pct`/`deviation_pct`/`target_met` wg wzoru z `spec/build.md`
    („Cel regularności i tolerancja”: `positive_day_pct = 100×N_plus/N`,
    `deviation_pct = 100×(N_minus+N_zero)/N`, cel spełniony gdy `deviation_pct <= 20`).
    Miesiąc z choć jednym dniem `missing` dostaje `is_valid=False` i
    `positive_day_pct`/`deviation_pct`/`target_met = None` (nieoceniany, missing NIE
    liczy się jako zero). Niepełny (brzegowy) miesiąc dostaje `is_partial=True`, z
    `N` = faktyczna liczba dni pokrytych przez krzywą w tym miesiącu (nie pełna
    długość kalendarzowa) — osobna flaga, żeby nigdy nie porównać go po cichu z
    tolerancją 20% pełnego miesiąca.
  - `compute_regularity` — orkiestrator (`classify_days` + `monthly_regularity`).

  Zero połączeń sieciowych, zero importu `strategy.py`/`backtest_apex.py`/
  `backtest_engine.py`/`main.py`/`trader.py`/`configuration/`. Żaden z tych plików nie
  został zmieniony w tej fali (`git status` w worktree potwierdza tylko dwa nowe pliki:
  `regularity.py`, `tests/test_regularity.py`).

- `tests/test_regularity.py` — 8 testów, ręcznie skonstruowane scenariusze (equity curve
  zbudowana wprost w teście, oczekiwane `positive_day_pct`/`deviation_pct` wyliczone
  ręcznie w komentarzu, potem `assert`):
  1. `test_full_month_all_positive_zero_deviation` — pełny miesiąc, każdy dzień dodatni
     → `deviation_pct=0.0`, `target_met=True`.
  2. `test_full_month_exactly_20pct_nonpositive_boundary_pass` — pełny miesiąc, dokładnie
     20% dni niedodatnich (6/30) → `deviation_pct=20.0`, `target_met=True` (granica `<=20`,
     nie `<20`).
  3. `test_full_month_just_over_20pct_nonpositive_fails` — 7/30 dni niedodatnich
     (`deviation_pct≈23.33`) → `target_met=False`.
  4. `test_exact_zero_pnl_day_is_nonpositive_not_positive_not_missing` — dzień z PnL
     dokładnie zero → `status="non_positive"`, nie `"positive"`, nie `"missing"`.
  5. `test_month_with_missing_interior_day_is_invalid_not_scored` — pełny miesiąc (31 dni)
     z jedną wewnętrzną luką w danych (15. dnia brak jakiegokolwiek znacznika equity) →
     `is_valid=False`, `positive_day_pct`/`deviation_pct`/`target_met=None` (nie policzone
     z luką jako zerem).
  6. `test_partial_month_flagged_with_actual_day_count_not_full_month_length` — krzywa
     zaczyna/kończy się w środku miesiąca (11 z 28 dni lutego) → `is_partial=True`,
     `N=11` (nie 28).
  7–8. `test_dst_spring_transition_boundary_timestamps_map_to_correct_local_day` i
     `test_dst_spring_transition_no_day_lost_or_duplicated_across_range` — przejście DST
     2026-03-29 (Europe/Warsaw, CET→CEST): znaczniki czasu w okolicy chwili przejścia
     mapowane na poprawny dzień lokalny (test na przygotowanym ręcznie oczekiwanym zbiorze
     dat, niezależnie od implementacji, przez bezpośrednie użycie `zoneinfo` w teście), oraz
     ciągła seria godzinowych barów przez przejście DST daje dokładnie 5 kolejnych dni
     kalendarzowych, bez żadnego zgubionego lub podwojonego dnia.

  Dyskryminujący test (uruchomiony ręcznie, nie wchodzi w skład commitu): tymczasowe
  zepsucie reguły unieważniania miesiąca z brakującymi danymi (`is_valid` na sztywno
  `True`) w `regularity.py` powoduje realne, natychmiastowe niepowodzenie testu 5
  (`assert august.is_valid is False` → `AssertionError: assert True is False`) — test faktycznie
  wykrywa regresję tej reguły, nie tylko przechodzi przy nietkniętym kodzie. Plik przywrócony
  do stanu sprzed sabotażu przed uruchomieniem pełnego zestawu i commitem (`diff` potwierdził
  identyczność z kopią zapasową).

## Wynik uruchomienia pełnego zestawu testów

`/home/limen/bot_traiding_daily/.venv_test/bin/python -m pytest tests/ -v` (wspólne
`.venv_test`, Python 3.9.25, pytest 8.4.2):

```
71 passed in 2.55s
```

63 istniejące testy sprzed tej fali (potwierdzone przed zmianami — `git status` czysty,
uruchomienie `pytest tests/ -q` na nietkniętym repo dało `63 passed in 2.28s`) + 8 nowych
z `tests/test_regularity.py` = 71. Zero regresji, zero zmian w istniejących plikach testowych
ani produkcyjnych.

## Decyzje projektowe warte odnotowania dla fali 3

- **Pierwszy dzień całej krzywej equity jest zawsze `missing`.** Definicja dnia z
  `spec/build.md` to „zmiana equity między końcami dni” — dla pierwszego dnia jakiejkolwiek
  historii nie istnieje dzień poprzedni, więc PnL jest z definicji nieznany, nie zero. Jeśli
  ten dzień wypada w pełnym miesiącu, miesiąc poprawnie staje się nieoceniany (zgodnie z
  „brakujące dane unieważniają ocenę miesiąca”). W fali 3, gdy equity curve zacznie się
  dokładnie na `Train1_start` (2024-03-01, po pominięciu warm-up), pierwszy dzień marca 2024
  będzie z tego powodu `missing`, a cały marzec 2024 (jeśli w ogóle raportowany jako pełny
  miesiąc, nie jako część okna Train) — nieoceniany. To nie błąd modułu, tylko nieunikniona
  konsekwencja definicji PnL opartej na delcie; fala 3 powinna to jawnie opisać w raporcie,
  a nie traktować jako usterkę.
- **Luka wewnątrz zakresu (brak znacznika equity danego dnia) unieważnia tylko ten jeden
  dzień**, nie łańcuchowo kolejne dni — kolejny dzień z realnymi danymi liczy PnL względem
  ostatniego znanego znacznika sprzed luki (dosłowna „zmiana między kolejnymi end-of-day
  snapshotami”, gdzie „kolejne” to kolejne istniejące snapshoty, nie kolejne kalendarzowo dni).
- Moduł nie wymusza konkretnego źródła equity curve — działa na dowolnym DataFrame z kolumną
  `equity` i indeksem czasowym (tz-aware UTC lub naive traktowane jako UTC, ten sam wzorzec co
  `data_contract.py`). Fala 3 może podać `backtest_engine.run_backtest(...).equity_curve`
  bezpośrednio, bez konwersji pośredniej.

---

# Fala 3 (final) — zmierzony baseline na realnych danych Bybit

> Ta fala wykonała faktyczny pomiar: 790 wywołań `backtest_engine.run_backtest`
> (5 symboli × 2 interwały × 79 strategii z `strategy.STRATEGY_CATALOG`, bez podzbioru),
> na dokładnie tym zbiorze danych, który zamroził `spec/research/F005-validation-protocol.md`
> (sekcja 6). Żaden plik z listy w wymaganiu 5 tickieta (`main.py`/`trader.py`/`configuration/`/
> `backtest_apex.py`/`backtest_engine.py`/`costs.py`/`equity.py`/`execution.py`/
> `data_contract.py`/`regularity.py`/protokół) nie został zmieniony — potwierdzone `git status`
> przed commitem tej fali.

## Metodologia wykonania

- Skrypt: `scripts/f005_run_baseline.py`. Uruchomienie: `790 runs in 364.9s` (≈6.1 min,
  mieści się w budżecie z sekcji 5 protokołu — ~255-510s szacowanych).
- Dane: `data_contract.load_dataset("data_cache", symbol, interval, "2024-01-26T00:00:00Z", "2026-09-01T00:00:00Z")`
  dla wszystkich 10 kombinacji (symbol, interwał) — **checksuma każdej z 10 zweryfikowana
  programowo w skrypcie przeciwko dokładnym wartościom z sekcji 6 protokołu przed użyciem**
  (wszystkie 10 zgodne, brak rozbieżności). Uwaga dla przyszłych uruchomień: pliki
  `data_cache/*.csv` nie są dzielone między git worktree (są w `.gitignore`, nie w git) —
  ten worktree miał tylko manifesty JSON, same CSV zostały skopiowane z głównego checkout
  (`/home/limen/bot_traiding_daily/data_cache/`), gdzie manifesty były bajt-identyczne
  (zweryfikowane `md5sum` przed kopiowaniem) — nie było żadnego ponownego pobrania z sieci.
- **Cały loaded range** (`warmup_start` → `holdout_end`, 2024-01-26 → 2026-09-01) przekazany
  do `run_backtest` w jednym ciągłym przebiegu per (symbol, interwał, strategia) — zgodnie
  z sekcją 5 protokołu, bez osobnych przebiegów per okno. `now` przekazane jawnie jako stała
  `2026-09-01T00:00:00Z` (nie zegar ścienny), żeby `data_contract.filter_closed_candles`
  zachowywało się deterministycznie niezależnie od tego, kiedy skrypt jest uruchamiany.
- **Parametry** — te same dla wszystkich 79 strategii, dokładnie ścieżka nie-optymalizacyjna
  `backtest_apex.py` (linie 64-72) czytana z `configuration/default.yaml`:
  `leverage=10, atr_multiplier=2.5, max_sl_pct=0.03, activate_pct=0.03, trail_pct=0.015,
  cooldown_candles=0`, plus `initial_equity=500.0, stake=100.0` (z tickieta). Koszty
  (`commission_rate_bps=10, half_spread_bps=5, slippage_bps=2`) pozostawione na domyślnych
  wartościach `backtest_engine.run_backtest` — tickiet nie prosił o ich nadpisanie.
- Surowy wynik per (symbol, interwał, strategia): `output/f005_baseline/raw/{symbol}_{interval}_{strategy}.json`
  (790 plików, parametry/metryki/pełna lista trades/dzienna equity+pnl+status/miesięczna
  tabela regularności z tagami przynależności do okien). **86 MB łącznie — NIE dodane do
  gita** (ten sam wzorzec co `data_cache/*.csv`, protokół sekcja 7a), tylko lokalnie na dysku;
  `.gitignore` rozszerzony o `output/f005_baseline/raw/*.json`. Zagregowane tabele
  (`output/f005_baseline/summary/`, 128 KB) **są** w gicie — od razu przeglądalne bez
  ponownego uruchamiania skryptu.
- Manifest reprodukowalności: `output/f005_baseline/summary/manifest.json` (parametry,
  checksumy, `git_commit_parent = 2d05caee8a7c303a1083a532111ad59d00723e82` — commit HEAD
  w momencie uruchomienia skryptu, poprzedzający commit tej fali; `run_timestamp_utc`,
  `elapsed_seconds`).

## Wynik główny — 0 z 24 885 ocenianych miesięcy spełnia cel

**Żadna z 790 kombinacji (symbol, interwał, strategia) nie osiąga `deviation_pct ≤ 20%`
w ŻADNYM ważnym miesiącu, w żadnym oknie, nigdzie na całej planszy pomiaru** —
`target_met == True` dla **0 z 24 885** ważnych (`is_valid=True`) rekordów miesięcznych
(pełne wyliczenie: `output/f005_baseline/raw/*.json`, pole `monthly_regularity`).
Najniższa (najlepsza) `deviation_pct` zaobserwowana kiedykolwiek, gdziekolwiek w całym
zbiorze: **34.48%** (kilka strategii EMA na ETHUSDT/240, luty 2024) — to i tak ponad
1.7× gorsze niż wymagany próg 20%.

**Mechaniczna przyczyna, zweryfikowana bezpośrednio na próbkach** (nie jest to błąd
skryptu — zweryfikowano ręcznie na losowej próbce 12 kombinacji plus dodatkowe testy
punktowe): przy `initial_equity=500`, `stake=100`, `leverage=10` i `equity.py`'s
udokumentowanym kontraktem `margin = notional / leverage = stake` (margin **nie** maleje
wraz z dźwignią — dźwignia zwiększa tylko nominał ekspozycji, nie zmniejsza wymaganego
marginu), typowa strata na stopie (`max_sl_pct=0.03` × notional $1000 ≈ $30 + koszty)
wystarcza, by po ok. 12-15 przegranych transakcjach equity spadło poniżej $100 — progu,
poniżej którego silnik z pojedynczą pozycją **nigdy więcej nie może otworzyć nowej
pozycji** (brak dostępnego marginu $100, bez względu na resztę historii). W **każdej**
z 790 zmierzonych kombinacji dzieje się to w ciągu pierwszych 1-3 miesięcy (styczeń-kwiecień
2024, czyli w oknie warm-up/Train1, długo przed Validation 1). Dowód liczbowy:

- 93.5% (23 266/24 885) wszystkich ważnych miesięcy ma `deviation_pct` dokładnie **100.0**
  (equity płaskie, zero dni dodatnich).
- Aktywnych (nie-płaskich) miesięcy jest tylko 1619, skoncentrowanych niemal wyłącznie
  w pierwszych miesiącach: 777 w lutym 2024, 444 w marcu, 168 w kwietniu, malejąco do
  pojedynczych sztuk po połowie 2024 i **zera od marca 2025** (czyli od Validation 1) —
  potwierdza to, że do Validation 1 praktycznie wszystkie 790 kont są już matematycznie
  „zbankrutowane" (equity < $100, bez możliwości nowego wejścia).
- Końcowe equity (`final_equity`, cały ciągły przebieg) mieści się dla **wszystkich 790**
  kombinacji w wąskim paśmie **$66.86 – $99.96** (najlepszy wynik: XRPUSDT/60/`EMA_8_21_RSI14_55`,
  $99.96, wciąż poniżej progu $100 potrzebnego na jedno kolejne wejście) — pasmo tak wąskie,
  że wyklucza przypadkowość, potwierdza systemowy mechanizm.
- **790/790 (100%)** kombinacji przekracza twarde kryterium odrzucenia DD>50% z `spec/build.md`
  (`max_drawdown_pct` liczone z całego ciągłego przebiegu, mark-to-market): min 80.01%,
  średnia 83.6%, max 90.19% — pełna lista: `output/f005_baseline/summary/dd_flags.csv`.

### Konsekwencja dla wymaganej tabeli „najbliżej celu" (punkt 1 zadania)

Dla **każdej** z 10 kombinacji (symbol, interwał) wszystkie 79 strategii są **remisowane
dokładnie** na `avg_deviation_pct = 100.0` i `net_pnl_validation = $0.00` w oknach
Validation 1-4 łącznie (`output/f005_baseline/summary/validation_summary.csv`,
790 wierszy — `avg_deviation_pct.describe()`: min=max=mean=100.0, std=0.0). **Nie istnieje
żadna sensowna różnica** między strategiami wg pierwotnej metryki tickieta (najniższa
średnia `deviation_pct` w ważnych miesiącach Validation) — wszystkie remisują na najgorszej
możliwej wartości, ponieważ wszystkie konta są już płaskie/zbankrutowane zanim Validation 1
się zaczyna. Uczciwy wynik: **żadna strategia nie jest „bliżej" celu niż jakakolwiek inna —
cała plansza remisuje na 100% deviation / $0 PnL w Validation, i żadna nie spełnia progu
≤20%, ani razu.**

Jako informacja dodatkowa (NIE odpowiedź na pytanie tickieta o „najbliżej celu" — to jest
inna metryka, „najmniej katastrofalna" wg PnL całego ciągłego przebiegu, nie wg regularności
w Validation, ponieważ ta ostatnia nie różnicuje wcale) — strategia z najmniejszą stratą
netto całego przebiegu per (symbol, interwał):

| Symbol | Interwał | Strategia (najmniej katastrofalna) | Net PnL (cały przebieg) | Final equity | Max DD (cały przebieg) |
| --- | --- | --- | ---: | ---: | ---: |
| BTCUSDT | 240 | EMA_21_50_RSI14_55 | -$400.13 | $99.87 | 82.27% |
| BTCUSDT | 60 | BB_20_2_VOL12 | -$400.92 | $99.08 | 81.01% |
| DOGEUSDT | 240 | TS_13_34_200_14 | -$400.34 | $99.66 | 80.31% |
| DOGEUSDT | 60 | BB_20_25_EMA50 | -$400.53 | $99.47 | 80.11% |
| ETHUSDT | 240 | BB_10_2_RSI14 | -$400.23 | $99.77 | 82.81% |
| ETHUSDT | 60 | BB_20_25_EMA50 | -$400.04 | $99.96 | 81.64% |
| SOLUSDT | 240 | RSI14_7030 | -$400.85 | $99.15 | 80.70% |
| SOLUSDT | 60 | EMA_8_21_VOL12 | -$400.13 | $99.87 | 81.65% |
| XRPUSDT | 240 | EMA3_8_21_100 | -$400.62 | $99.38 | 80.12% |
| XRPUSDT | 60 | EMA_8_21_RSI14_55 | -$400.04 | $99.96 | 81.19% |

Każda z tych strategii **też** ma `avg_deviation_pct=100.0`/`net_pnl_validation=$0.00` w
Validation, identycznie jak pozostałe 78 w swojej kolumnie — ta tabela nie niesie żadnej
informacji o jakości sygnału, pokazuje tylko, która strategia spaliła budżet stopów odrobinę
wolniej przed uderzeniem w tę samą ścianę.

## Najgorszy miesiąc / dzień / seria strat (punkt 2 zadania)

- **Najgorszy miesiąc** (najwyższa `deviation_pct` wśród ważnych miesięcy): remis
  wielokrotny na `deviation_pct=100.0` (23 266 miesięcy remisuje na tej wartości —
  patrz wyżej). Zarejestrowana/zaatrybuowana pierwsza znaleziona instancja (kolejność
  przetwarzania plików w skrypcie): **SOLUSDT / 240 / ADX14_DI_20 / marzec 2024**
  (`positive_day_pct=0.0`). Pełne dane: `output/f005_baseline/raw/SOLUSDT_240_ADX14_DI_20.json`.
- **Najgorszy pojedynczy dzień** (największa jednodniowa strata): **DOGEUSDT / 60 /
  EMA_50_200 / 2024-02-29**, PnL dnia = **-$254.10** (equity spadło z ok. $500 startu do
  ujemnego wyniku w ciągu jednego dnia po dużym ruchu DOGE, mark-to-market z otwartą
  pozycją). Pełne dane: `output/f005_baseline/raw/DOGEUSDT_60_EMA_50_200.json`, pole `daily`.
- **Najdłuższa seria dni bez zysku** (kolejne `non_positive`, dzień `missing` lub `positive`
  przerywa serię — patrz definicja niżej): **SOLUSDT / 60 / STOCH14_cross**, **949 kolejnych
  dni** non-positive, 2024-01-27 → 2026-09-01 — to **cała historia po pierwszym dniu**: ta
  konkretna kombinacja nie miała ani jednego dnia dodatniego w całym zmierzonym zakresie.
  Pełne dane: `output/f005_baseline/raw/SOLUSDT_60_STOCH14_cross.json`.

  Uwaga terminologiczna (jawna decyzja projektowa tej fali, nie ukryta): `regularity.py`
  rozróżnia tylko `positive`/`non_positive`/`missing` (zero dnia = `non_positive`, zgodnie
  z definicją dnia z build.md), nie ma osobnej kategorii „strata" (ściśle ujemne PnL) vs
  „bez zysku" (PnL=0). „Seria strat" w tym raporcie = seria `non_positive`, spójnie z
  resztą słownictwa protokołu — nie licząc oddzielnie ściśle ujemnych dni.

## Sprawdzenie max drawdown (punkt 3 zadania) — flaga twardego kryterium odrzucenia

**790 z 790 (100%)** kombinacji (symbol, interwał, strategia) przekracza `max_drawdown_pct > 50%`
w którymś momencie całego ciągłego przebiegu — twarde kryterium odrzucenia z `spec/build.md`,
uruchamiane bez wyjątku dla całego katalogu pod tymi parametrami. Zakres: min **80.01%**
(np. `XRPUSDT/60/BB_20_25_EMA50`), średnia **83.63%**, max **90.19%**. Pełna lista wszystkich
790 wierszy z dokładną wartością: `output/f005_baseline/summary/dd_flags.csv` (w gicie,
26 KB). Żadna kombinacja nie została pominięta w tej fladze.

## Okno Holdout — POMIAR WYŁĄCZNIE, nie do wyboru/strojenia niczego w tej fali

> Zgodnie z wiążącą regułą „holdout nietykalny" z sekcji 7 protokołu: poniższe liczby
> to **wyłącznie pomiar obecnego stanu** istniejącego, niemodyfikowanego katalogu
> (`STRATEGY_CATALOG`, gotowe parametry). **Nie zostały i nie mogą zostać użyte** do
> wyboru, promocji ani strojenia żadnej strategii w tej ani żadnej przyszłej fali —
> patrz protokół sekcja 7, punkty 2(a)-(d).

Okno Holdout (2026-03-01 … 2026-09-01, wszystkie 5 symboli, oba interwały):
`output/f005_baseline/summary/holdout_summary.csv`, 790 wierszy — dokładnie ten sam
wzorzec jak Validation: `avg_deviation_pct` = 100.0 i `net_pnl_holdout` = $0.00 dla
**wszystkich 790** kombinacji (min=max=mean, std=0.0). Powód jest identyczny jak dla
Validation: konta były już matematycznie zbankrutowane (equity < $100, niezdolne otworzyć
nową pozycję) od pierwszych miesięcy 2024 — długo przed startem Holdoutu — więc pomiar
Holdoutu w tej fali **nie mówi nic o zachowaniu sygnału w tym oknie**, mówi wyłącznie,
że stan „equity płaskie od 2024" trwał nadal we wrześniu 2026. To osobno raportowany,
nie wymieszany z rankingiem Validation powyżej, zgodnie z wymaganiem tickieta.

## Ważność miesięcy — ile danych stoi za tym baseline (punkt 5 zadania)

Łącznie **25 675** rekordów miesięcznych (790 uruchomień × ~32.5 miesiąca/uruchomienie
średnio) w `output/f005_baseline/raw/*.json`:

| Kategoria | Liczba | % |
| --- | ---: | ---: |
| `is_valid=True`, pełny miesiąc | 24 490 | 95.38% |
| `is_valid=True`, `is_partial=True` | 395 | 1.54% |
| `is_valid=False`, `is_partial=True` | 790 | 3.08% |
| `is_valid=False`, pełny miesiąc | 0 | 0.00% |

- **395 „valid+partial"** = dokładnie 5 symboli × 79 strategii (wszystkie 395 uruchomień
  interwału 60) — ostatni bar zakresu 1h ląduje dokładnie na granicy `2026-09-01T00:00:00Z`,
  co tworzy jednodniowy, ważny (dane realne, nie brakujące), ale brzegowo-niepełny miesiąc
  „wrzesień 2026". Interwał 240 nie ma tego artefaktu (ostatni pełny miesiąc to sierpień
  2026). Nie wpływa na żadne z wymaganych okien (Train/Validation/Holdout kończą się na
  sierpniu 2026) — czysto informacyjna ciekawostka brzegowa danych, nie problem jakości.
- **790 „invalid+partial"** = dokładnie jeden na uruchomienie: styczeń 2024, pierwszy
  (brzegowy) miesiąc każdej krzywej equity. Nieważny, bo pierwszy dzień CAŁEJ krzywej jest
  zawsze `missing` z definicji (`regularity.py`: brak dnia „przed" pierwszym dniem historii,
  więc PnL tego dnia jest z definicji nieznany) — udokumentowane już w notatce fali 2
  („Decyzje projektowe warte odnotowania dla fali 3"), nie jest to usterka ani luka
  w danych, tylko nieunikniona konsekwencja definicji PnL opartej na delcie zastosowanej
  do pierwszego dnia jakiejkolwiek historii.
- **0 „invalid+full"** — żaden PEŁNY (nie-brzegowy) miesiąc nigdzie w całym zbiorze nie ma
  rzeczywistej luki w danych (`n_missing>0` poza pierwszym dniem historii) — potwierdza to
  100%-owe pokrycie z audytu danych (protokół sekcja 1/6, 0 luk).

## Otwarty problem dla Koordynatora — NIE rozwiązany w tej fali, tylko zaraportowany

Zgodnie z wymaganiem 5 tickieta: protokół jest zamrożony, nie modyfikuję go ani nie
reinterpretuję samodzielnie — poniżej jest zgłoszenie problemu, nie poprawka.

**Metodologia „jeden ciągły przebieg" (protokół sekcja 5) traci swoją zakładaną
równoważność z osobnymi przebiegami per okno, gdy silnik jest stanowy (pojedyncza
pozycja, equity przenoszone między oknami) i katalog strategii ma realne ryzyko upadłości
konta.** Uzasadnienie sekcji 5 („to poprawne, bo strategie mają stałe parametry — nic nie
jest dopasowywane do okna, pojedynczy ciągły przebieg daje identyczny wynik jak nowe
przebiegi per okno") jest prawdziwe dla **generowania sygnału** (te same wskaźniki/progi
niezależnie od tego, czy Validation jest liczone w osobnym przebiegu czy jako wycinek
ciągłego), ale **nieprawdziwe dla stanu kapitału**: przebieg ciągły przenosi equity
z Train do Validation do Holdout bez resetu, więc gdy konto raz stanie się matematycznie
niewypłacalne (equity < stake, brak marginu na nowe wejście — co w tym pomiarze
zdarzyło się dla **100% z 790 kombinacji**, w ciągu pierwszych 1-3 miesięcy), ten stan
trwa do końca przebiegu niezależnie od tego, co sygnał „chciałby" zrobić w Validation/
Holdout. W efekcie **cały wynik Validation i Holdout w tej fali mierzy wyłącznie „czy
konto przetrwało pierwsze miesiące" (odpowiedź: nie, dla całego katalogu), a nie jakość
sygnału w tych oknach.** Metodologia z resetem kapitału na starcie każdego okna (lub
przynajmniej na starcie Validation, po Train) dałaby prawdopodobnie zupełnie inny,
bardziej informacyjny obraz tego, czy sygnały obecnego katalogu mają jakąkolwiek
przewagę w Validation/Holdout, niezależnie od kwestii wielkości pozycji/ryzyka
upadłości, która w tej fali zdominowała każdy pojedynczy wynik. Nie zmieniam protokołu
ani nie uruchamiam alternatywnej metodologii w tej fali — to decyzja dla Koordynatora
(dotyczy potencjalnie też metodologii F006+).

## Podsumowanie fali 3

Baseline jest **kompletny i uczciwie zaraportowany**: 790/790 uruchomień, 0 pominiętych,
checksumy zweryfikowane przed użyciem, żadna strategia nie osiąga celu regularności ani
razu, żadna nie jest bliżej niż inna w oknach Validation (remis na najgorszej możliwej
wartości), 100% przekracza twarde kryterium DD>50%, a Holdout potwierdza identyczny,
zdegenerowany wzorzec. Wynik nie jest zawyżony ani zaokrąglony w górę — to bezpośredni,
zmierzony stan obecnego katalogu strategii pod parametrami z `configuration/default.yaml`
zastosowanymi jednolicie, bez strojenia, zgodnie z zakresem tickieta.
