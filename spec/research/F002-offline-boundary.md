# F002 — Dowód granicy offline

> Zakres: `backtest_apex.py` uruchamialny na lokalnym fixture bez sieci i bez kluczy; błąd/brak wyniku odróżnialny od sukcesu kodem wyjścia.

## Zmiany w kodzie

- `backtest_apex.py`: nowa flaga `--local-csv <ścieżka>` — wczytuje OHLCV z lokalnego CSV (`timestamp,open,high,low,close,volume`) zamiast wołać `get_bybit_ohlcv`. Bez flagi zachowanie CLI niezmienione (nadal pobiera z Bybit). W trybie `--local-csv` Bar Magnifier działa w wariancie zdegenerowanym (sub-świece = świece główne z CSV), bo nie ma drugiego źródła danych o wyższej rozdzielczości offline.
- `backtest_apex.py:309` i `:380` (przed zmianą): `sys.exit(0)` przy braku danych (`len(df_ind) < 500`) i przy braku wyników (`not results`) — zmienione na `sys.exit(1)`. Sukces i błąd/brak-wyniku mają teraz różne kody wyjścia.
- `tests/fixtures/ohlcv_sample.csv`: 600 świec syntetycznych (4h), wystarczające do przejścia progu `len(df_ind) >= 500`.
- `tests/test_offline_backtest.py`: dwa testy pytest —
  1. `test_offline_backtest_runs_without_network` — blokuje `requests.get`/`requests.post` (rzucają `AssertionError` przy próbie połączenia), uruchamia `backtest_apex.py` przez `runpy.run_path` z `--local-csv` na fixture, sprawdza że powstał `output/backtests/*/report.json`.
  2. `test_offline_backtest_exits_nonzero_when_too_few_candles` — fixture ucięty do 10 świec, sprawdza `SystemExit.code != 0`.

## Wynik uruchomienia

```
$ .venv_test/bin/python -m pytest tests/test_offline_backtest.py -v
tests/test_offline_backtest.py::test_offline_backtest_runs_without_network PASSED
tests/test_offline_backtest.py::test_offline_backtest_exits_nonzero_when_too_few_candles PASSED
2 passed in 0.80s
```

Test 1 przechodzi tylko dlatego, że `requests.get`/`requests.post` są podmienione na funkcję rzucającą wyjątek — gdyby backtest offline próbował się połączyć z siecią, test failowałby natychmiast zamiast przejść.

## Import boundary (dowód dla F001/F002)

```
$ git grep -n "import trader\|import rest_logs" backtest_apex.py run_backtest_apex.py strategy.py
(brak trafień)
```

Potwierdza ustalenie z F001: żaden z modułów obliczeniowych backtestu nie importuje `trader.py` (klient produkcyjny) ani `rest_logs.py` (wysyłka do Apex).

## Ograniczenia tego kroku

- Fixture jest syntetyczny (wygenerowany, nie prawdziwe dane Bybit) — wystarcza do dowodu "działa offline", nie do żadnego wniosku o strategii. Prawdziwe dane historyczne i ich manifest to F003.
- Tryb `--local-csv` nie ma prawdziwego Bar Magnifiera (brak sub-świec z wyższej rozdzielczości) — to świadome uproszczenie dla dowodu offline, nie docelowy kontrakt danych.
- `.venv_test/` to lokalny scratch venv na potrzeby tego zadania, dodany do `.gitignore`, nie commitowany.
