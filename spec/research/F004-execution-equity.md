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

---

# F004 — Dowód: equity/margin portfela (fala 2)

> Zakres tej fali: `equity.py`, standalone, bez sieci, buduje na `costs.py` (fala 1, sekcja wyżej). Zastępuje rozbieżność #7/#8 z `spec/research/F001-current-state.md`: brak modelu wspólnego kapitału/margin i pominięcie equity początkowego/niezrealizowanego DD w `_compute_metrics`. Nie podłącza się jeszcze do `strategy.py`/`backtest_apex.py`/`main.py`/`trader.py`/`configuration/` — te pliki nie zostały zmienione.

## Co zostało zbudowane

`equity.py` — `Portfolio` (dataclass) jako ledger equity/margin, plus `Position`, `ClosedTrade`, `InsufficientMarginError`:

- **Kontrakt stawki/dźwigni/marginu** (`spec/build.md`, "Decyzje i granice pracy"): `stake` domyślnie 100 USD/wejście PRZED dźwignią, `notional = stake * leverage`, `margin = notional / leverage` — co algebraicznie zawsze daje `margin == stake`: margin to kwota faktycznie zablokowana jako zabezpieczenie, leverage tylko mnoży ekspozycję (notional), nie kwotę marginu.
- **Wspólne equity** (`initial_equity=500.0` domyślnie): jeden `Portfolio` trzyma `positions: Dict[position_id, Position]` — dowolna liczba pozycji i symboli dzieli tę samą pulę, `committed_margin` to suma marginów wszystkich aktualnie otwartych pozycji niezależnie od symbolu.
- **Mark-to-market equity** (`Portfolio.equity(mark_prices)`): `initial_equity + realized_pnl + suma(unrealized_pnl otwartych pozycji przy podanych cenach)`. Wywoływane w dowolnym momencie, nie tylko po zamknięciu transakcji — pozycja bez podanej ceny w `mark_prices` domyślnie liczy zerowy niezrealizowany PnL (fallback na `entry_price`).
- **Blokada braku środków** (`Portfolio.open_position`): liczy `available_margin = equity(mark_prices) - committed_margin - fee_buffer` i podnosi `InsufficientMarginError` (nie ciche pominięcie/ucięcie), jeśli `available_margin < margin` nowej pozycji. Pozycja odrzucona nie trafia do `self.positions` ani nie zmienia `committed_margin`.
  - **Decyzja projektowa** (odnotowana w docstringu modułu): dostępny margin liczy się z **bieżącego equity mark-to-market**, nie z literalnej stałej `initial_equity`, mimo że tekst tickieta F004b używa skrótu "available equity (initial_equity - margin - buffer)". Powód: wymóg (2) każe wliczać niezrealizowany PnL do equity w każdej chwili, a wymóg (3) blokować wejścia bez pokrycia — użycie stałej `initial_equity` pozwoliłoby otworzyć drugą pozycję za pieniądze, których już nie ma po stracie na pierwszej. Scenariusz stałej `initial_equity` jest szczególnym przypadkiem formuły z bieżącym equity, gdy PnL=0. Pokryte testem `test_open_loss_reduces_available_margin_for_next_position_via_mark_to_market`.
- **Realizacja PnL przy zamknięciu** (`Portfolio.close_position`): woła `costs.py` — `commission` i `spread_cost` na obu nogach (entry notional + exit notional), `slippage_cost` na notional wejścia, `funding_pnl` za cały okres trzymania pozycji (ta sama konwencja znaków/nóg co w scenariuszach fali 1, `tests/test_costs.py`). `net_pnl = gross_pnl - total_costs + funding_pnl` trafia do `realized_pnl`, margin pozycji wraca do puli (`committed_margin -= margin`), pozycja usuwana z `positions`.
- **Peak equity i drawdown mark-to-market** (`Portfolio.mark_to_market(mark_prices)`): aktualizuje `peak_equity` (tylko w górę) i zwraca `(equity, drawdown_pct)`, gdzie `drawdown_pct = 100 * (peak_equity - equity) / peak_equity`. Liczone z otwartymi pozycjami wliczonymi (mark-to-market), gotowe do porównania z limitem 50% max DD z `build.md` w kolejnej fali/integracji — sam limit nie jest tu egzekwowany, tylko śledzony.

## Scenariusze z ręcznie policzoną arytmetyką

Wszystkie w `tests/test_equity.py`, arytmetyka w komentarzu nad każdym scenariuszem.

1. **Dwie jednoczesne pozycje dzielące jedną pulę 500 USD** (`test_two_simultaneous_positions_share_one_500_usd_pool`):
   `initial_equity=500`. Dwie pozycje, każda `stake=100, leverage=5 → margin=100`. Po otwarciu obu: `committed_margin=200`, `equity()=500` (brak PnL), `available_margin()=500-200-0=300`. Trzecia pozycja `margin=100` nadal się mieści (`300>=100`) → `committed_margin=300`, `available_margin=200`.

2. **Pozycja odrzucona z braku marginu** (`test_new_position_rejected_when_margin_insufficient`):
   4 pozycje `margin=100` każda → `committed_margin=400`, `available=100`. Piąta pozycja `margin=100` dokładnie się mieści (`100>=100`) → przechodzi, `committed_margin=500`, `available=0`. Szósta pozycja `margin=100` przy `available=0` → `InsufficientMarginError`, nie trafia do `positions`, `committed_margin` bez zmian.

3. **Odrzucenie przez bufor na koszty** (`test_new_position_rejected_by_fee_buffer_even_with_nominal_room`):
   `available_margin` bez bufora = `500-450=50`, dokładnie starcza na pozycję `margin=50` — ale `fee_buffer=10` zarezerwowany na koszty wyjścia sprawia, że wymagane pokrycie to `50+10=60 > 50` dostępne → `InsufficientMarginError`.

4. **Mark-to-market equity i DD z otwartą, przegrywającą pozycją, PRZED jej zamknięciem** (`test_mark_to_market_includes_unrealized_pnl_of_open_position`, `test_mark_to_market_drawdown_while_losing_position_still_open`):
   long SOLUSDT `entry=20, stake=100, leverage=5 → notional=500, qty=25`. Cena spada do 18: `unrealized = 1*(18-20)*25 = -50` → `equity = 500+0-50 = 450`, `dd = 100*(500-450)/500 = 10.0%`. Cena spada dalej do 16: `unrealized = 1*(16-20)*25 = -100` → `equity=400`, `dd=20.0%`. Pozycja przez cały czas otwarta (`realized_pnl==0`, `"p1" in positions`) — DD liczone wyłącznie mark-to-market, nie po zamknięciu.

5. **Peak equity aktualizuje się w górę przy odbiciu** (`test_peak_equity_updates_when_equity_recovers_above_prior_peak`):
   po spadku do `equity=450` (dd=10%), cena odbija do 22: `unrealized = 1*(22-20)*25 = +50` → `equity=550`, nowy `peak_equity=550`, `dd=0.0%`.

6. **Zamknięcie pozycji realizuje PnL po kosztach i zwalnia margin** (`test_close_position_realizes_net_pnl_and_frees_margin`):
   long SOLUSDT `entry=20, exit=22, stake=100, leverage=5 → notional=500, qty=25`. `gross_pnl = 1*(22-20)*25 = 50.00`. `exit_notional=22*25=550`. Prowizja 10bps: entry `500*0.0010=0.50`, exit `550*0.0010=0.55`, suma `1.05`. Spread 5bps: entry `500*0.0005=0.25`, exit `550*0.0005=0.275`, suma `0.525`. Poślizg: `500*0.0002+0.10=0.20`. `total_costs=1.05+0.525+0.20=1.775`. Brak fundingu. `net_pnl=50-1.775+0=48.225`. Po zamknięciu: `realized_pnl=48.225`, `committed_margin=0`, `"p1" not in positions`, `equity()=548.225`.

7. **Sekwencja otwarcie→zamknięcie zgodna z ręczną arytmetyką narastającego equity** (`test_sequence_of_open_close_matches_manual_running_equity`):
   Trade 1: long SOLUSDT `entry=20, exit=22, stake=100, leverage=5`, bez kosztów → `net=+50`, `equity=500+50=550`. Trade 2: short ETHUSDT `entry=2000, exit=1980, stake=100, leverage=2 → notional=200, qty=0.1`. `gross = -1*(1980-2000)*0.1 = -1*(-20)*0.1 = +2.0` (short zarabia na spadku ceny). Bez kosztów → `net=+2.0`, `equity=550+2=552.0`, `realized_pnl=52.0`, `committed_margin=0`.

8. **Funding wliczony przy zamknięciu** (`test_close_position_applies_funding_pnl`):
   long SOLUSDT `entry=20=exit=20` (płaska cena, `gross_pnl=0`), `notional=500`. Jedno zdarzenie funding w oknie trzymania, `rate=0.0001`: `funding_payment(long, 500, 0.0001) = -(+1)*500*0.0001 = -0.05`. Bez innych kosztów → `net_pnl = 0 - 0 + (-0.05) = -0.05`.

9. **Test dyskryminujący: strata na otwartej pozycji musi zmniejszyć dostępny margin dla kolejnej** (`test_open_loss_reduces_available_margin_for_next_position_via_mark_to_market`):
   long SOLUSDT `entry=20, stake=400, leverage=1 → notional=400, margin=400, qty=20`. Cena spada do 15: `unrealized=1*(15-20)*20=-100 → equity=500-100=400`, `available_margin=equity(400)-committed_margin(400)-0=0`. Naiwna formuła `initial_equity - committed_margin` dałaby błędnie `500-400=100` dostępne i przepuściłaby drugą pozycję `margin=100` — poprawna formuła MTM musi ją odrzucić: `InsufficientMarginError`, `"p2" not in positions`. Ten test celowo sprawdza tezę, która mogłaby być fałszywa przy literalnym odczytaniu tickieta ("available equity = initial_equity - margin - buffer").

Plus testy brzegowe: obliczenie `notional/margin/quantity` przy otwarciu, `direction` spoza `{1,-1}` odrzucone (`ValueError`), duplikat `position_id` odrzucony (`ValueError`), zamknięcie nieistniejącej pozycji (`KeyError`).

## Wynik testów

Uruchomione przez `/home/limen/bot_traiding_daily/.venv_test/bin/python -m pytest tests/ -v` (ten sam współdzielony venv testowy co w fali 1 — bez instalowania niczego nowego):

```
tests/test_costs.py (12 testów) PASSED
tests/test_data_contract.py (11 testów) PASSED
tests/test_equity.py::test_open_position_computes_notional_margin_quantity PASSED
tests/test_equity.py::test_two_simultaneous_positions_share_one_500_usd_pool PASSED
tests/test_equity.py::test_new_position_rejected_when_margin_insufficient PASSED
tests/test_equity.py::test_new_position_rejected_by_fee_buffer_even_with_nominal_room PASSED
tests/test_equity.py::test_mark_to_market_includes_unrealized_pnl_of_open_position PASSED
tests/test_equity.py::test_mark_to_market_drawdown_while_losing_position_still_open PASSED
tests/test_equity.py::test_peak_equity_updates_when_equity_recovers_above_prior_peak PASSED
tests/test_equity.py::test_close_position_realizes_net_pnl_and_frees_margin PASSED
tests/test_equity.py::test_sequence_of_open_close_matches_manual_running_equity PASSED
tests/test_equity.py::test_close_position_applies_funding_pnl PASSED
tests/test_equity.py::test_open_loss_reduces_available_margin_for_next_position_via_mark_to_market PASSED
tests/test_equity.py::test_close_unknown_position_raises_key_error PASSED
tests/test_equity.py::test_open_position_rejects_invalid_direction PASSED
tests/test_equity.py::test_open_position_duplicate_id_rejected PASSED
tests/test_offline_backtest.py (2 testy, przedistniejące) PASSED

39 passed in 1.26s
```

Brak regresji w testach fali 1 (`test_costs.py`) ani w przedistniejących `test_data_contract.py`/`test_offline_backtest.py`.

## Co pozostaje dla kolejnych fal (poza scope tej pracy)

- **F004c**: zegar wykonania (rozdzielenie ceny triggera od ceny wykonania, najwcześniejsza dostępna po sygnale) — `equity.py` przyjmuje ceny entry/exit jako dane wejściowe, nie liczy triggerów ani opóźnień.
- **Integracja**: podłączenie `equity.py`+`costs.py` do `backtest_apex.py` zamiast bezkosztowego `_make_trade` ze `strategy.py`, z jawną dokumentacją że stary tryb jest zastąpiony (nie cicho duplikowany), plus egzekwowanie limitu 50% max DD (na razie tylko śledzony przez `mark_to_market`, nie wymuszany). Nie zrobione w tej fali — `strategy.py`/`backtest_apex.py`/`main.py`/`trader.py`/`configuration/` nie zostały zmienione.
