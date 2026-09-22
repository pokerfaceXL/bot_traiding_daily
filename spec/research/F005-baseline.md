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
