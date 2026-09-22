# F004 · Realistyczna realizacja zleceń i księgowanie equity portfela

## Outcome

Backtest liczy wynik na spójnym zegarze (sygnał po zamknięciu świecy → najwcześniejsza możliwa realizacja), z kosztami (prowizja, spread, poślizg, funding) i prawdziwym equity portfela (initial_equity=500 USD, stawka 100 USD/wejście, margin, notional rozdzielone), zamiast obecnego uproszczenia bez kosztów i bez wspólnego kapitału. To usuwa rozbieżności #1, #2, #7, #8 z F001 i jest warunkiem, zanim jakikolwiek wynik strategii (F005+) można porównywać do celu regularności.

## Scope

- Model kosztów: prowizja, spread, poślizg, funding rate — czyste funkcje, deterministyczne, bez sieci.
- Rozdzielenie ceny triggera (sygnał/SL/TSL) od ceny wykonania (najwcześniejsza dostępna po sygnale).
- Equity portfela: initial_equity=500 USD wspólne dla wszystkich pozycji, stawka=100 USD/wejście przed dźwignią, notional=stawka×leverage, margin osobno; blokada nowej pozycji przy braku środków.
- Mark-to-market equity z otwartymi pozycjami (niezrealizowany PnL wliczony do DD), nie tylko po zamkniętych transakcjach.
- Integracja z `data_contract.py` (F003) i `backtest_apex.py` — to też zamyka odłożoną integrację z F003.

## Out of scope

- Wybór strategii/parametrów, protokół walidacji (F005+).
- Wielo-symbolowy portfel z limitami korelacji (F007).
- Zmiana main.py/trader.py/configuration/ produkcyjnych.

## Acceptance

- Testy jednostkowe na ręcznie policzonych scenariuszach: long, short, pierwsza strata, funding, gap, TSL w środku bara, koniec okresu z otwartą pozycją.
- Equity portfela nigdy nie liczy dwóch pozycji tak, jakby każda miała własne 500 USD.
- Brak środków (margin) blokuje nowe wejście zamiast cichego przekroczenia.
- `backtest_apex.py` używa nowego modułu kosztów/equity zamiast `_make_trade`'s bezkosztowego liczenia (strategy.py) — stary tryb udokumentowany jako zastąpiony, nie cicho zduplikowany.
- Dowód w `spec/research/F004-execution-equity.md`; main.py/trader.py/configuration/ niezmienione.

## Notes

Effort: wysoki — najbardziej fundamentalna i najbardziej podatna na błędy część łańcucha dowodowego (vision.md: "Kolejność dowodów: poprawna symulacja → ..."). Podzielone na fale (patrz commits/badge w spec/research/F004-execution-equity.md): koszty → equity/margin → zegar wykonania → integracja z backtest_apex.py.
