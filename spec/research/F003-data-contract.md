# F003 — kontrakt danych OHLCV: dowod

> Uwaga Coordinatora przy scalaniu: worker dostal worktree odgalezione przed
> commitami F001/F002 (Coordinator nie scommitowal ich do gita przed spawn) -
> stad opisana ponizej "blokada" i samodzielny modul zamiast integracji z
> F002. F001/F002 sa teraz scommitowane; integracja z `tests/test_offline_backtest.py`
> i `strategy.get_bybit_ohlcv` pozostaje otwartym krokiem opisanym na koncu.
> Fixture przemianowany na `ohlcv_sample_gap.csv`, zeby nie kolidowac z F002.

## Blokada w hando­ffie (do zgloszenia Coordinatorowi)

Wskazane w zadaniu sciezki nie istnieja w tym worktree:

- `spec/features/active/F003-data-contract/ticket.md` — brak.
- `spec/research/F001-current-state.md` — brak (F001 wg `spec/build.md` ma status 🔴 PLANNED, nie zrobione).
- `tests/fixtures/ohlcv_sample.csv`, `tests/test_offline_backtest.py` — brak (F002 tez nie zostalo jeszcze zrealizowane).

Zamiast czekac na ticket/F001/F002, zaimplementowano kontrakt danych jako
samodzielny modul zbudowany na tym, co realnie istnieje w repo
(`strategy.get_bybit_ohlcv`, `spec/build.md` sekcja "Ustalenia z kodu" —
rozbieznosc: "brak jawnego odrzucenia biezacej niezamknietej swiecy"), z
wlasnym fixture i testami. Gdy F001/F002 powstana, `data_contract.py` moze
zostac podlaczony do ich fixture/testow bez zmiany API.

Main.py, trader.py i configuration/ nie zostaly zmienione.

## Co zbudowano

`data_contract.py` — kontrakt danych OHLCV, bez polaczen sieciowych (przyjmuje
juz pobrany DataFrame, np. z `strategy.get_bybit_ohlcv`):

- **Tylko zamkniete swiece**: `filter_closed_candles(df, interval, now)` odrzuca
  bar, jesli `open_time + interval > now` — usuwa dokladnie rozbieznosc #5 z
  audytu F001 wskazana w `spec/build.md` ("brak jawnego odrzucenia biezacej
  niezamknietej swiecy").
- **Wykrywanie luk**: `detect_gaps(df, interval)` znajduje kazda przerwe w
  regularnej siatce czasowej i zwraca liste `Gap(after, before, missing_bars)`.
- **Warm-up**: `split_warmup(df, warmup_bars)` oddziela pierwsze N barow
  (tylko do liczenia wskaznikow) od zbioru uzywalnego do sygnalow/wejsc.
- **Manifest**: `build_manifest(...)` — symbol, interwal, zakres zadany vs.
  rzeczywisty, liczba barow, oczekiwana liczba barow, `coverage_pct`, lista
  luk, liczba odrzuconych niezamknietych barow, checksuma SHA-256 danych.
- **Brak cichego zerowania**: `enforce_no_silent_gaps(manifest, allow_gaps=False)`
  domyslnie rzuca `DataGapError`, gdy sa luki — wynik z lukami nie moze
  wejsc do rankingu bez jawnej, swiadomej zgody (`allow_gaps=True`).
- **Cache per symbol/interwal/zakres UTC**: `save_dataset`/`load_dataset`
  zapisuja/czytaja CSV + manifest JSON pod deterministyczna nazwa
  (`{symbol}_{interval}_{startUTC}_{endUTC}`); `load_dataset` weryfikuje
  checksume — rozbiezny/uszkodzony cache to blad twardy (`DataContractError`),
  nie ciche przeliczenie.
- **Punkt wejscia**: `build_dataset(...)` laczy powyzsze — filtruje zakres i
  zamkniete swiece, buduje manifest, egzekwuje brak cichych luk, opcjonalnie
  zapisuje cache, zwraca dane po odcieciu warm-up.

## Fixture

`tests/fixtures/ohlcv_sample_gap.csv` — 20 barow 4h (interwal `"240"`), UTC,
z celowa luka miedzy indeksem 9 a 10 (16h zamiast 4h → 3 brakujace bary),
zeby test mogl wykryc luke deterministycznie.

## Testy i wynik

`tests/test_data_contract.py`, 11 testow — uruchomione w venv z
pandas/numpy/pytest (repo nie ma zainstalowanych zaleznosci; venv utworzony
tymczasowo w `/tmp/f003venv`, poza tym worktree):

```
$ /tmp/f003venv/bin/python3 -m pytest tests/test_data_contract.py -v
...
11 passed in 0.53s
```

Pokrycie: fixture ma wykrywalna luke; filtr niezamknietej swiecy usuwa/
zachowuje bar w zaleznosci od `now`; manifest liczy pokrycie i checksume;
`enforce_no_silent_gaps` rzuca domyslnie i przepuszcza po jawnym opt-in;
warm-up dzieli dane poprawnie; `build_dataset` end-to-end na czystym
wycinku (bez luk) zapisuje cache i pliki manifestu; `build_dataset` rzuca
na wycinku z luka bez opt-in; `load_dataset` wykrywa zmanipulowany plik CSV
(checksuma) i brakujacy cache.

**Dowod dyskryminujacy** (najbardziej prawdopodobne falszywe zalozenie:
"test filtra niezamknietej swiecy faktycznie cos sprawdza, a nie zawsze
przechodzi"): zmutowano warunek w `filter_closed_candles` tak, by nigdy nie
odrzucal barow (`keep = close_time <= now + 100h`) i potwierdzono, ze
`test_filter_closed_candles_drops_currently_forming_bar` wtedy pada
(`assert 0 == 1`); po przywroceniu oryginalnego kodu wszystkie 11 testow
znow przechodzi. Test nie jest samospelniajacym sie potwierdzeniem.

## Czego brakuje / nastepny krok

- F001 (mapa obecnego zachowania) i F002 (offline backtest boundary +
  `tests/fixtures/ohlcv_sample.csv`/`tests/test_offline_backtest.py`) nie
  zostaly jeszcze zrealizowane w tym repo — Coordinator powinien albo
  dokonczyc F001/F002 wedlug `spec/build.md`, albo potwierdzic, ze F003
  dostarczony jako samodzielny modul jest wystarczajacy na tym etapie.
- `data_contract.py` nie laczy sie jeszcze z `strategy.get_bybit_ohlcv` ani
  z `backtest_trailing` — integracja (przekazanie danych z kontraktu do
  silnika backtestu) to osobny krok po ustaleniu ksztaltu F002.
- Dobor instrumentow/koszyka i polityka warm-up per strategia (ile barow)
  nie zostaly ustalone — `warmup_bars` jest parametrem wywolujacego.
