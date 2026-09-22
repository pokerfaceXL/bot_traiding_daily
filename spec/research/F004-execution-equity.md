# F004 — Dowód: model kosztów (fala 1)

> Zakres tej fali: `costs.py`, standalone, bez sieci, bez zmiany `strategy.py`/`main.py`/`trader.py`/`configuration/`. Zastępuje rozbieżność #1 z `spec/research/F001-current-state.md`: `_make_trade` (`strategy.py:750-767`) liczy `pnl_usd = raw_pnl_pct * leverage * stake` bez żadnego odjęcia prowizji/spreadu/poślizgu/fundingu — ten moduł dostarcza te funkcje, ale nie podłącza ich jeszcze do `_make_trade` (podłączenie do `backtest_apex.py` jest w scope pełnego F004, po falach equity/margin i zegara wykonania — patrz `ticket.md`).

## Co zostało zbudowane

`costs.py` — cztery czyste, deterministyczne funkcje:

- `commission(notional, rate_bps)` — prowizja (taker albo maker, zależnie tylko od podanej stawki) od notional, `notional * rate_bps / 10_000`.
- `spread_cost(notional, half_spread_bps)` — koszt połowy spreadu, zawsze przeciwko traderowi, ta sama formuła co commission.
- `slippage_cost(notional, bps=0.0, fixed=0.0)` — poślizg jako suma składnika proporcjonalnego (bps od notional) i stałej kwoty; konfigurowalne osobno albo łącznie.
- `funding_payment(direction, notional, funding_rate)` — podpisany cash flow z jednego zdarzenia funding: `-direction * notional * funding_rate`. `direction=+1` (long) płaci przy dodatniej stawce, `direction=-1` (short) otrzymuje.
- `funding_pnl(direction, notional, entry_time, exit_time, funding_events)` — sumuje `funding_payment` dla zdarzeń `(timestamp, rate)`, które zaszły w oknie `entry_time <= timestamp < exit_time` (pozycja musi być otwarta w momencie fundingu; wejście dokładnie w momencie fundingu jest liczone, wyjście dokładnie w momencie fundingu — nie, bo pozycja jest już zamknięta).

Konwencja znaków: `commission`/`spread_cost`/`slippage_cost` zwracają nieujemny koszt do odjęcia od gross pnl niezależnie od kierunku pozycji; `funding_payment`/`funding_pnl` zwracają podpisany cash flow, bo funding może iść w obie strony.

Moduł nie implementuje equity/margin (to F004b) ani zegara wykonania sygnał→realizacja (to F004c) — tylko izolowane funkcje kosztów, gotowe do użycia przez kolejne fale.

## Scenariusze z ręcznie policzoną arytmetyką

Wszystkie w `tests/test_costs.py`, arytmetyka w komentarzu nad każdym assertem (nie assert przeciwko innej formule).

1. **Profitable long minus commission+slippage** (`test_profitable_long_minus_commission_and_slippage`):
   entry=100, exit=110, qty=1. Gross pnl = (110-100)×1 = 10.00.
   Commission taker 10bps na obu nogach: entry 100×0.0010=0.10, exit 110×0.0010=0.11, suma 0.21.
   Slippage 5bps na entry notional: 100×0.0005=0.05.
   Net = 10 − 0.21 − 0.05 = **9.74**.

2. **Losing short minus commission + fixed slippage** (`test_losing_short_minus_commission_and_fixed_slippage`):
   entry=100, exit=105, qty=2. Gross pnl (short) = (100-105)×2 = −10.00.
   Commission 10bps: entry 200×0.0010=0.20, exit 210×0.0010=0.21, suma 0.41.
   Slippage stała 0.50.
   Net = −10 − 0.41 − 0.50 = **−10.91**.

3. **Funding across one timestamp, long i short** (`test_funding_pnl_long_held_across_one_funding_timestamp`, `test_funding_pnl_short_held_across_one_funding_timestamp`):
   notional=1000, funding_rate=0.0001 (1bp), jedno zdarzenie funding wewnątrz okna trzymania pozycji.
   Long: `-(+1)×1000×0.0001` = **−0.10** (płaci).
   Short: `-(-1)×1000×0.0001` = **+0.10** (otrzymuje).
   Dodatkowo pokryte: zdarzenia poza oknem trzymania są ignorowane (`test_funding_pnl_ignores_events_outside_holding_window`), zdarzenie dokładnie w momencie wejścia jest liczone (`test_funding_pnl_counts_event_exactly_at_entry`).

4. **Trade ze spread cost na wejściu i wyjściu** (`test_trade_with_spread_cost_on_entry_and_exit`):
   entry=50, exit=55, qty=10. Gross pnl = (55-50)×10 = 50.00.
   Half-spread 8bps na obu nogach: entry 500×0.0008=0.40, exit 550×0.0008=0.44, suma 0.84.
   Net = 50 − 0.84 = **49.16**.

Plus trzy testy jednostkowe na samych funkcjach kosztów (`commission`, `spread_cost`, `slippage_cost` z osobna) i dwa na znak `funding_payment` (long/short).

## Wynik testów

Uruchomione przez `/home/limen/bot_traiding_daily/.venv_test/bin/python -m pytest tests/ -v` (środowisko systemowe nie ma zainstalowanego `pandas`, więc użyto istniejącego współdzielonego venv testowego — bez instalowania niczego nowego).

```
tests/test_costs.py::test_commission_basic_rate PASSED
tests/test_costs.py::test_spread_cost_basic_rate PASSED
tests/test_costs.py::test_slippage_cost_bps_and_fixed PASSED
tests/test_costs.py::test_profitable_long_minus_commission_and_slippage PASSED
tests/test_costs.py::test_losing_short_minus_commission_and_fixed_slippage PASSED
tests/test_costs.py::test_trade_with_spread_cost_on_entry_and_exit PASSED
tests/test_costs.py::test_funding_payment_sign_long_pays_positive_rate PASSED
tests/test_costs.py::test_funding_payment_sign_short_receives_positive_rate PASSED
tests/test_costs.py::test_funding_pnl_long_held_across_one_funding_timestamp PASSED
tests/test_costs.py::test_funding_pnl_short_held_across_one_funding_timestamp PASSED
tests/test_costs.py::test_funding_pnl_ignores_events_outside_holding_window PASSED
tests/test_costs.py::test_funding_pnl_counts_event_exactly_at_entry PASSED
tests/test_data_contract.py (9 testów, przedistniejące) PASSED
tests/test_offline_backtest.py (2 testy, przedistniejące) PASSED

25 passed in 1.29s
```

Brak regresji w przedistniejących testach `test_data_contract.py` i `test_offline_backtest.py`.

## Co pozostaje dla kolejnych fal (poza scope tej pracy)

- **F004b**: equity/margin portfela (`initial_equity=500`, stawka 100 USD/wejście, notional=stawka×leverage, margin osobno), blokada braku środków.
- **F004c**: zegar wykonania (rozdzielenie ceny triggera od ceny wykonania, najwcześniejsza dostępna po sygnale), mark-to-market equity z pozycjami otwartymi.
- **Integracja**: podłączenie `costs.py` do `backtest_apex.py` zamiast bezkosztowego `_make_trade` ze `strategy.py`, z jawną dokumentacją że stary tryb jest zastąpiony (nie cicho duplikowany). Nie zrobione w tej fali — `strategy.py`/`backtest_apex.py` nie zostały zmienione.
