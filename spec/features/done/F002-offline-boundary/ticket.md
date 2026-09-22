# F002 · Backtest offline bez sieci, kluczy i eksportu do Apex

## Outcome

Coordinator i Workerzy mogą uruchomić backtest w pełni offline — na lokalnym fixture, bez kluczy handlowych, bez zapytań sieciowych i bez śladu w Apex — i odróżnić w kodzie wyjścia „błąd”/„brak wyniku” od „sukces”. To zamyka granicę badawczą z vision.md przed F003 (kontrakt danych), gdzie liczy się już powtarzalność samych danych, nie tylko brak zależności zewnętrznych.

## Scope

- Fixture: mały, zapisany lokalnie zestaw świec OHLCV (CSV/parquet) wystarczający do uruchomienia `backtest_trailing` na jednej strategii i jednym symbolu.
- Ścieżka w `backtest_apex.py`, która pozwala podać dane z fixture zamiast wołać `get_bybit_ohlcv` (np. wstrzyknięcie df zamiast pobierania) — bez zmiany domyślnego zachowania CLI dla użytkownika, który chce prawdziwe dane.
- Rozróżnienie kodów wyjścia: `backtest_apex.py:309` i `:380` (`sys.exit(0)` przy braku danych/wyników) — sukces vs błąd/brak wyniku muszą mieć różne kody, żeby automatyzacja/CI to odróżniła.
- Potwierdzenie (testem lub jawną asercją), że `backtest_apex.py`/`run_backtest_apex.py`/`strategy.py` nie importują `trader.py` ani `rest_logs.py` (już tak jest wg F001 — tu chodzi o zapisany dowód, nie zmianę architektury).

## Out of scope

- Equity/margin/koszty realizacji, manifest danych, kontrola luk — to F003/F004.
- Zmiana logiki sygnałów, ryzyka, SL/TSL.
- Dotykanie main.py/trader.py/configuration/ produkcyjnych.
- Ustalanie, który config jest live — właścicielka potwierdziła, że to nieistotne (F001).

## Acceptance

- Nowy test (np. `pytest`) uruchamia `backtest_trailing`/`backtest_apex.py` na fixture bez żadnego wywołania sieciowego — weryfikowalne np. przez brak dostępu do sieci w środowisku testu lub mock, który rzuca wyjątkiem przy próbie połączenia.
- `backtest_apex.py` zwraca kod inny niż 0, gdy nie ma danych lub wyników; test to pokrywa.
- `git grep -n "import trader\|import rest_logs" backtest_apex.py run_backtest_apex.py strategy.py` nie zwraca trafień (dowód zapisany w spec/research/).
- Produkcyjne pliki (main.py, trader.py, configuration/) niezmienione.

## Notes

Effort: medium — realna zmiana kodu (exit codes, ścieżka fixture) plus test, ale ograniczony zakres i niska cena błędu (offline, brak wpływu na produkcję).
