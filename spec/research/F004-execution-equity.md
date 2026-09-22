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

---

# F004 — Dowód: zegar wykonania (fala 3)

> Zakres tej fali: `execution.py`, standalone, bez sieci, buduje na `costs.py` (fala 1) i `equity.py` (fala 2) — nie importuje ich, ale jest projektowany do współpracy z ich konwencją cen/kierunku. Nie podłącza się jeszcze do `strategy.py`/`backtest_apex.py`/`main.py`/`trader.py`/`configuration/` — te pliki nie zostały zmienione (integracja to F004d, kolejna i ostatnia fala).

## Co zostało zbudowane

`execution.py` — trzy czyste funkcje plus dataclassy `Bar`/`EntryFill`/`ExitTrigger` i enumy `OrderType`/`TriggerKind`:

- **`resolve_entry_fill(order_type, direction, next_bar, limit_price=None)`** — rozwiązuje cenę wejścia z OHLC świecy N+1, nigdy świecy N (patrz niżej, rozbieżność #5). `MARKET` wypełnia się zawsze po `next_bar.open`. `LIMIT` wypełnia się tylko, gdy zakres `[low, high]` świecy N+1 dotyka `limit_price` w kierunku korzystnym dla zlecenia (`direction=+1`: `low <= limit_price`; `direction=-1`: `high >= limit_price`); w przeciwnym razie `filled=False, fill_price=None` — zlecenie NIE jest cicho wypełniane po gorszej cenie. Gdy świeca otworzyła się już za limitem (gap na korzyść), wypełnienie jest po lepszej cenie `min(open, limit)`/`max(open, limit)`, nie po samym limicie.
- **`resolve_stop_take_within_bar(direction, bar, stop_loss=None, take_profit=None)`** — rozwiązuje, czy i gdzie SL/TP zostałyby dotknięte w obrębie jednej świecy OHLC. Gdy trafiony jest tylko jeden poziom, ten wygrywa. Gdy **oba** poziomy mieszczą się w `[low, high]` tej samej świecy (rozbieżność #6, Bar Magnifier), funkcja stosuje jawne, udokumentowane założenie **worst-case: SL zawsze wygrywa** — patrz sekcja niżej po pełne uzasadnienie.
- **`resolve_level_fill(direction, bar, level, kind)`** — funkcja gap handling (punkt 3 tickieta): rozstrzyga cenę wypełnienia dla poziomu, o którym już wiadomo, że został dotknięty. Jeśli świeca **otwiera się już poza poziomem** w kierunku, który by go aktywował (gap przez SL/TP), wypełnienie jest po cenie **otwarcia** świecy, NIE po samym poziomie — i oznaczone `is_gap_fill=True`, żeby odróżnić je od normalnego wypełnienia po poziomie (`is_gap_fill=False`).

### Rozbieżności z F001 adresowane przez ten moduł

- **#5 (brak jawnego odrzucenia bieżącej niezamkniętej świecy)**: moduł zakłada, że sygnał na świecy N został już policzony PO jej zamknięciu (`data_contract.py`'s `filter_closed_candles` robi to wyżej w łańcuchu — ten moduł tego nie powtarza, nie importuje `data_contract.py`). Najwcześniejsza możliwa realizacja to **otwarcie świecy N+1** — nigdy cena zamknięcia świecy N, co byłoby look-ahead (w momencie, gdy sygnał na N staje się znany, jedyna jeszcze nieustalona "z góry" cena to otwarcie kolejnej świecy).
- **#6 (Bar Magnifier — niejednoznaczna kolejność zdarzeń wewnątrz sub-świecy)**: gdy SL i TP oba mieszczą się w zakresie jednej świecy, z samego OHLC nie da się odtworzyć kolejności (kod `strategy.py` sam to przyznaje przez `ambiguous_count`/`ambiguous_pct`, `strategy.py:619-621,628-630` — mierzy niepewność, nie eliminuje jej). `resolve_stop_take_within_bar` przyjmuje zawsze, że cena poszła **najpierw w stronę SL**. To jest zamierzenie **konserwatywne (pesymistyczne)**, nie optymistyczne: odwrotne założenie (TP zawsze wygrywa) systematycznie zawyżałoby win-rate/PnL strategii bez żadnego dowodu, że tak faktycznie było w danych, których po prostu nie mamy (OHLC nie zawiera ścieżki ceny wewnątrz świecy). Wybór SL-pierwszy nigdy nie zawyży wyniku strategii przez ciche przyjęcie korzystnej dla niej kolejności.
- **#7 (live używa MarkPrice, backtest OHLC)**: moduł pracuje wyłącznie na OHLC (jak istniejący backtest) — nie próbuje symulować MarkPrice. To jest udokumentowana, akceptowana różnica źródła ceny między live a backtestem, nie błąd do naprawienia w tej fali (naprawienie wymagałoby danych tick/MarkPrice, których backtest OHLC nie ma).

## Scenariusze z ręcznie policzoną arytmetyką

Wszystkie w `tests/test_execution.py`, arytmetyka/uzasadnienie w komentarzu nad każdym scenariuszem.

1. **Market entry wypełnia się po otwarciu następnej świecy** (`test_market_entry_fills_at_next_bars_open`): `next_bar.open=101.0` → `fill_price=101.0`, `filled=True`.
2. **Limit entry nie wypełnia się, gdy cena nigdy go nie dotyka** (`test_limit_entry_does_not_fill_when_price_never_touches_it`): long limit buy=90, zakres świecy `[92, 98]` nigdy nie sięga 90 → `filled=False, fill_price=None` — zlecenie NIE jest cicho wypełnione po gorszej cenie.
3. **Limit entry wypełnia się dokładnie po cenie limitu, gdy zakres go dotyka bez gapu** (`test_limit_entry_fills_at_limit_price_when_range_touches_it`): limit=93, zakres `[92,98]`, `open=95>93` (bez gapu) → `fill_price=93.0`.
4. **Limit entry wypełnia się po lepszym `open`, gdy świeca gapuje przez limit** (`test_limit_entry_fills_at_better_open_when_bar_gaps_through_limit`): limit=90, `open=88` (już poniżej limitu) → `fill_price=88.0` (lepsza cena niż limit), nie 90.
5. **Short limit entry — symetryczny test w drugą stronę** (`test_short_limit_entry_fills_only_when_range_reaches_up_to_it`): limit=105 poza zakresem `[98,103]` → unfilled; limit=102 wewnątrz zakresu, `open=100<102` → `fill_price=102.0`.
6. **Normalny SL touch mid-bar, long** (`test_normal_stop_loss_touch_mid_bar_long`): SL=97, bar `open=100,high=102,low=95` — `low<=97` trafiony, `open=100>97` (bez gapu) → `kind=STOP_LOSS, fill_price=97.0, is_gap_fill=False`.
7. **TP touch mid-bar, long** (`test_take_profit_touch_mid_bar_long`): TP=103, bar `open=100,high=105,low=99` — `high>=103` trafiony, `open=100<103` (bez gapu) → `kind=TAKE_PROFIT, fill_price=103.0, is_gap_fill=False`.
8. **Test dyskryminujący: SL i TP oba wewnątrz tej samej świecy — konserwatywne SL wygrywa** (`test_both_sl_and_tp_inside_same_bar_conservative_stop_wins`, long, i `..._short` dla strony short): SL=97, TP=103, bar `open=100,high=105,low=95` — OBA poziomy mieszczą się w zakresie. Bez tego testu implementacja mogłaby błędnie (optymistycznie) zwrócić TP. Test wprost sprawdza, że wynikiem jest `kind=STOP_LOSS, fill_price=97.0` — nie `TAKE_PROFIT`. Wariant short: SL=103, TP=97, bar `open=100,high=105,low=95` → `kind=STOP_LOSS, fill_price=103.0`.
9. **Gap-through-stop na otwarciu, long i short** (`test_gap_through_stop_at_open_long`, `test_gap_through_stop_at_open_short`): long SL=97, bar `open=96` (już poniżej SL) → `fill_price=96.0` (cena otwarcia, NIE 97), `is_gap_fill=True` — odróżnialne od normalnego stop-fill z punktu 6 (`is_gap_fill=False`). Short SL=103, bar `open=104` (już powyżej SL) → `fill_price=104.0, is_gap_fill=True`.
10. **Brak triggera, gdy żaden poziom nie jest dotknięty** (`test_no_trigger_when_neither_level_touched`): SL=90, TP=110, bar `[99,101]` → `kind=NONE, fill_price=None, is_gap_fill=False`.

Plus testy brzegowe: `direction` spoza `{1,-1}` odrzucone (`ValueError`) w obu funkcjach kierunkowych, `resolve_level_fill` z `kind=NONE` odrzucone (`ValueError`), `LIMIT` bez `limit_price` odrzucone (`ValueError`).

## Wynik testów

Uruchomione przez `/home/limen/bot_traiding_daily/.venv_test/bin/python -m pytest tests/ -v` (ten sam współdzielony venv testowy co fale 1/2 — bez instalowania niczego nowego):

```
tests/test_costs.py (12 testów) PASSED
tests/test_data_contract.py (11 testów) PASSED
tests/test_equity.py (15 testów) PASSED
tests/test_execution.py::test_market_entry_fills_at_next_bars_open PASSED
tests/test_execution.py::test_limit_entry_does_not_fill_when_price_never_touches_it PASSED
tests/test_execution.py::test_limit_entry_fills_at_limit_price_when_range_touches_it PASSED
tests/test_execution.py::test_limit_entry_fills_at_better_open_when_bar_gaps_through_limit PASSED
tests/test_execution.py::test_short_limit_entry_fills_only_when_range_reaches_up_to_it PASSED
tests/test_execution.py::test_normal_stop_loss_touch_mid_bar_long PASSED
tests/test_execution.py::test_take_profit_touch_mid_bar_long PASSED
tests/test_execution.py::test_both_sl_and_tp_inside_same_bar_conservative_stop_wins PASSED
tests/test_execution.py::test_both_sl_and_tp_inside_same_bar_conservative_stop_wins_short PASSED
tests/test_execution.py::test_gap_through_stop_at_open_long PASSED
tests/test_execution.py::test_gap_through_stop_at_open_short PASSED
tests/test_execution.py::test_no_trigger_when_neither_level_touched PASSED
tests/test_execution.py::test_resolve_level_fill_rejects_unknown_kind PASSED
tests/test_execution.py::test_resolve_entry_fill_rejects_invalid_direction PASSED
tests/test_execution.py::test_resolve_stop_take_rejects_invalid_direction PASSED
tests/test_execution.py::test_limit_entry_requires_limit_price PASSED
tests/test_offline_backtest.py (2 testy, przedistniejące) PASSED

55 passed in 1.55s
```

Brak regresji w testach fal 1/2 (`test_costs.py`, `test_equity.py`) ani w przedistniejących `test_data_contract.py`/`test_offline_backtest.py`. `git status` po tej fali pokazuje wyłącznie dwa nowe pliki (`execution.py`, `tests/test_execution.py`) — `strategy.py`/`backtest_apex.py`/`main.py`/`trader.py`/`configuration/` niezmienione.

## Co pozostaje dla kolejnej fali (poza scope tej pracy)

- **F004d (integracja, ostatnia fala)**: podłączenie `costs.py`+`equity.py`+`execution.py` do `backtest_apex.py` zamiast bezkosztowego `_make_trade` ze `strategy.py`, z jawną dokumentacją że stary tryb jest zastąpiony (nie cicho duplikowany), egzekwowanie limitu 50% max DD, oraz podłączenie do `data_contract.py`'s `filter_closed_candles` tak, by sygnał na świecy N faktycznie napędzał `resolve_entry_fill`/`resolve_stop_take_within_bar` na świecy N+1 w pętli backtestu. Nie zrobione w tej fali — `execution.py` przyjmuje już gotowe obiekty `Bar`, nie zna źródła danych.

---

# F004 — Dowód: orkiestracja pętli backtestu (fala 4)

> Zakres tej fali: `backtest_engine.py`, standalone, bez sieci, składa cztery już scalone moduły F004/F003 (`costs.py` fala 1, `equity.py` fala 2, `execution.py` fala 3, `data_contract.py` F003) w działającą pętlę backtestu end-to-end. **To NIE jest integracja z `backtest_apex.py`** — ta jest kolejną, osobną falą (fala 5). `strategy.py`/`backtest_apex.py`/`main.py`/`trader.py`/`configuration/` są tylko czytane (import `strategy` dla `STRATEGY_CATALOG`/`add_indicators`), nie modyfikowane.

## Co zostało zbudowane

`backtest_engine.py` — `run_backtest(df, strategy_name, ...)` + `BacktestResult` (dataclass: `trades`, `equity_curve`, `metrics`, `skipped_signals`):

- **Generacja sygnału**: `data_contract.filter_closed_candles` → `strategy.add_indicators` → `strategy.STRATEGY_CATALOG[strategy_name](df)`. Czysta matematyka wskaźników/sygnałów ze `strategy.py` jest użyta jak jest, nie przepisana.
- **Kontrakt initial-SL/trailing-SL replikowany 1:1 ze `strategy.backtest_trailing` (entry_on_open=True, `strategy.py:498`)**: `_calc_initial_sl` w `backtest_engine.py` to ta sama formuła co `strategy.py`'s `_calc_initial_sl` (`strategy.py:491`) — `dist = price * max_sl_pct`, `atr_multiplier` jest przyjmowany jako parametr (kontrakt z tickieta), ale **celowo NIE jest używany do liczenia dystansu SL**, dokładnie jak w obecnym `strategy.py`, gdzie komponent ATR jest zakomentowany (`strategy.py:495`) — replikujemy istniejące (mylące nazwą, ale realne) zachowanie, nie cichą naprawę. Trailing SL: `activate_pct`/`trail_pct` liczone tą samą formułą, `best_price`/`trailing_sl` aktualizowane HIGH/LOW bieżącego bara PRZED sprawdzeniem dotknięcia SL na tym barze (ta sama kolejność co gałąź `sub_lookup=None` w `strategy.py`, bo ten moduł nie ma danych sub-świec Bar Magnifier). Ten sam `cooldown_candles` gate po wyjściu przez `initial_sl`. To samo wyjście przez odwrócenie sygnału (zamknięcie po `close` bieżącego bara) i to samo zamknięcie na końcu danych (`close` ostatniego bara).
- **Co NIE jest wzięte ze `strategy.py`**: samo rozstrzygnięcie dotknięcia bara. Zamiast surowych porównań `low <= active_sl`/`high >= active_sl` ze `strategy.py`, każdy bar z otwartą pozycją przechodzi przez `execution.resolve_stop_take_within_bar` (konserwatywne, gap-aware; `take_profit=None`, bo `backtest_trailing` nie ma TP — tylko SL/trailing SL), a wypełnienie idzie przez `execution.resolve_level_fill` (wbudowane w `resolve_stop_take_within_bar`). Wejścia wypełniają się przez `execution.resolve_entry_fill(OrderType.MARKET, ...)` na otwarciu NASTĘPNEGO bara (zamiast `strategy.py`'s własnego `open_a[i]`) — dokładnie semantyka `entry_on_open=True`.
- **Equity/margin/koszty**: jeden współdzielony `equity.Portfolio` (`initial_equity=500` domyślnie, `stake=100` domyślnie per `spec/build.md`) — `costs.py`'s prowizja/spread/poślizg/funding aplikowane przy KAŻDYM zamknięciu przez `Portfolio.close_position`. W danym momencie otwarta jest tylko JEDNA pozycja (ta sama maszyna stanów co `strategy.backtest_trailing` — ten moduł nie dodaje współbieżności wielopozycyjnej).
- **Decyzja o `equity.InsufficientMarginError`** (udokumentowana w docstringu modułu, NIE pozostawiona niezdefiniowana): gdy `Portfolio.open_position` podniosłoby ten wyjątek, sygnał jest POMINIĘTY — pozycja po prostu nie zostaje otwarta, pętla kontynuuje, pominięcie trafia do zwracanej listy `skipped_signals`. Wyjątek nie propaguje się i nie przerywa backtestu.
- **Krzywa equity mark-to-market per-bar**: `Portfolio.mark_to_market` wołane na KAŻDYM barze (nie tylko po zamkniętych transakcjach) z ceną `close` bieżącego bara jako mark price otwartej pozycji (jeśli jest) — `equity_curve` zawiera niezrealizowany PnL otwartych pozycji w każdym momencie.
- **Metryki**: `total_net_pnl` (suma `net_pnl` transakcji), `win_rate`, `max_drawdown_pct` (z `equity_curve`), `n_trades`, `final_equity`.

## Wybór strategii testowej

`RSI14_7030` (`sig_rsi_extreme` ze `strategy.py`) — wybrana zamiast np. zawsze-w-rynku `EMA_8_21`, bo jest czystą funkcją JEDNEJ już przetestowanej kolumny wskaźnika (`rsi14`) i generuje rzadkie sygnały (0 prawie wszędzie, ±1 tylko na ekstremach RSI). Dzięki temu liczba transakcji na fixture (17 na 600 barach) jest na tyle mała, że pojedyncza transakcja daje się ręcznie prześledzić i zweryfikować end-to-end, a test braku nakładania się pozycji (punkt b niżej) jest sensowny (nie trywialny "zawsze w pozycji").

## Scenariusze testowe (`tests/test_backtest_engine.py`)

Dane: `tests/fixtures/ohlcv_sample.csv` (600 barów 4H, bez luk — wybrana zamiast `ohlcv_sample_gap.csv`, bo ta fala nie testuje obsługi luk, to już pokryte przez `data_contract.py`/F003; pełny przebieg end-to-end nie potrzebuje dodatkowej zmiennej luki w danych) dla testów (a)/(b)/(d), plus mała ręcznie skonstruowana 6-barowa ramka dla testu (c).

1. **(a) Pierwsza transakcja zweryfikowana ręcznie end-to-end** (`test_first_short_trade_matches_hand_calculated_entry_sl_and_costs`): RSI14 przekracza 70 na barze `2024-01-04 00:00` → sygnał short. Wejście market na OTWARCIU następnego bara `2024-01-04 04:00`, `open=103.4276` — zweryfikowane, że `entry_price == 103.4276`, nie cena zamknięcia sygnałowego bara (co byłoby look-ahead). `initial_sl = 103.4276 + 103.4276*0.05 = 108.598980` (formuła `_calc_initial_sl`, dystans tylko z `max_sl_pct`, bez ATR — zweryfikowane wprost). Pozycja przeżywa (SL nigdy nie dotknięty, cena spada w stronę ~101, trailing nigdy się nie aktywuje bo cena nigdy nie spadła 3% na korzyść short przed wyjściem) do odwrócenia sygnału na `2024-01-08 20:00`, zamknięcie po `close=101.0948` tego bara (`exit_reason="signal_reverse"`, `is_gap_fill=False`). Koszty policzone NIEZALEŻNIE przez bezpośrednie wywołania `costs.commission`/`costs.spread_cost`/`costs.slippage_cost` w teście (nie przez zaufanie własnemu wynikowi silnika): `quantity=1000/103.4276=9.668599`, `gross_pnl=22.554908`, `total_costs=3.166168` (prowizja+spread na obu nogach + poślizg wejścia, domyślne stawki silnika 10/5/2 bps), `net_pnl=19.388740`, `equity_curve` po tej transakcji `== 500 + 19.388740 = 519.388740` — wszystko zweryfikowane `pytest.approx` przeciw niezależnie policzonym liczbom.
2. **(b) Krzywa equity nigdy nie sugeruje więcej niż jednej pozycji marginu na raz** (`test_full_run_never_implies_more_than_one_positions_margin_committed`): dla KAŻDEGO znacznika czasu w `equity_curve` policzone ile transakcji z `trades` ma `entry_time <= ts < exit_time` — zawsze `<= 1`. Dodatkowo (nadmiarowo, jako krzyżowa kontrola) posortowane transakcje nie nakładają się czasowo (`exit_time[i] <= entry_time[i+1]`). To bezpośredni dowód, że nigdy nie jest zaangażowany margin dwóch pozycji (2×`stake`=200) naraz.
3. **(c) `InsufficientMarginError` → pominięcie sygnału, nie wyjątek** (`test_insufficient_margin_skips_signal_leaves_position_unopened_and_equity_flat`): mała 6-barowa rosnąca ramka, `EMA_8_21` (szybko daje sygnał long), `initial_equity=50 < stake=100` — margin nigdy nie może być pokryty. Zweryfikowane: `res.trades` puste, `res.skipped_signals` ma >=1 wpis, ŻADEN wyjątek nie propaguje się z `run_backtest`, `equity_curve["equity"]` pozostaje płaskie na 50.0 przez cały przebieg (żadna pozycja nigdy nie została otwarta), `res.metrics["n_trades"]==0`. Dodatkowo test wprost odtwarza to samo wywołanie `equity.Portfolio.open_position` bezpośrednio i potwierdza `pytest.raises(equity.InsufficientMarginError)` — dowód, że silnik faktycznie łapie TEN SAM wyjątek, a nie po prostu nigdy nie wchodzi w tę ścieżkę.
4. **(d) Metryki podsumowujące spójne z `trades`/`equity_curve`** (`test_metrics_summary_matches_trades_and_equity_curve`): `n_trades`, `total_net_pnl`, `win_rate`, `max_drawdown_pct`, `final_equity` przeliczone niezależnie z `trades`/`equity_curve` i porównane z `res.metrics`.

## Znana pułapka uruchamiania testów (nowa w tej fali — WAŻNE dla fali 5)

`strategy.py`'s `_resolve_config_path()` (`strategy.py:23-26`, kod istniejący, nie zmieniony) czyta `sys.argv[1]` i próbuje otworzyć go jako plik YAML configu, jeśli nie zaczyna się od `-`. Żadna wcześniejsza fala nie importowała `strategy.py` bezpośrednio w testach, więc to nigdy nie miało znaczenia. `backtest_engine.py` importuje `strategy` na poziomie modułu (żeby użyć `STRATEGY_CATALOG`/`add_indicators`), więc odtąd **jakiekolwiek wywołanie pytest z argumentem ścieżki** (np. `pytest tests/ -v` — dokładnie komenda użyta w falach 1-3 tego dowodu) **rozbija się** przy kolekcji `tests/test_backtest_engine.py`: `sys.argv[1]` staje się `"tests/"`, co `strategy.py` próbuje otworzyć jako plik configu → `IsADirectoryError`. Zweryfikowane wprost (`pytest tests/ -v` faktycznie rzuca `IsADirectoryError`, `pytest tests/test_backtest_engine.py -v` faktycznie rzuca `yaml.parser.ParserError` próbując sparsować kod Pythona jako YAML). To pre-istniejący błąd w `strategy.py` (poza scope tej fali — nie wolno zmieniać `strategy.py`), tylko teraz ujawniony przez nowy import. **Działające wywołanie: `python -m pytest -v` BEZ argumentu ścieżki** (pytest samo odkrywa `tests/` po rootdir) — użyte do wyniku testów niżej. Fala 5 (integracja z `backtest_apex.py`) i każdy kolejny worker powinni używać tej formy, nie `pytest tests/ -v`.

## Wynik testów

Uruchomione przez `/home/limen/bot_traiding_daily/.venv_test/bin/python -m pytest -v` (ten sam współdzielony venv testowy co fale 1-3, BEZ argumentu ścieżki — patrz pułapka wyżej — bez instalowania niczego nowego):

```
tests/test_backtest_engine.py::test_first_short_trade_matches_hand_calculated_entry_sl_and_costs PASSED
tests/test_backtest_engine.py::test_full_run_never_implies_more_than_one_positions_margin_committed PASSED
tests/test_backtest_engine.py::test_insufficient_margin_skips_signal_leaves_position_unopened_and_equity_flat PASSED
tests/test_backtest_engine.py::test_metrics_summary_matches_trades_and_equity_curve PASSED
tests/test_costs.py (12 testów) PASSED
tests/test_data_contract.py (11 testów) PASSED
tests/test_equity.py (15 testów) PASSED
tests/test_execution.py (17 testów) PASSED
tests/test_offline_backtest.py (2 testy, przedistniejące) PASSED

59 passed in 2.06s
```

Brak regresji w testach fal 1-3 (`test_costs.py`, `test_equity.py`, `test_execution.py`) ani w przedistniejących `test_data_contract.py`/`test_offline_backtest.py`. `git status` po tej fali pokazuje wyłącznie dwa nowe pliki (`backtest_engine.py`, `tests/test_backtest_engine.py`) — `strategy.py`/`backtest_apex.py`/`main.py`/`trader.py`/`configuration/` niezmienione.

## Co pozostaje dla ostatniej fali (poza scope tej pracy)

- **F004, fala 5 (integracja, ostatnia fala)**: podłączenie `backtest_engine.run_backtest` do `backtest_apex.py` zamiast bezkosztowego `_make_trade`/`backtest_trailing` ze `strategy.py`, z jawną dokumentacją że stary tryb jest zastąpiony (nie cicho duplikowany), egzekwowanie limitu 50% max DD (na razie tylko śledzony przez `equity.Portfolio.mark_to_market`, nie wymuszany — `backtest_engine.py` też go nie wymusza, tylko przekazuje dalej w `metrics["max_drawdown_pct"]`). Uwaga na pułapkę `sys.argv`/`strategy._resolve_config_path` opisaną wyżej przy pisaniu/uruchamianiu testów integracyjnych.
- Nie zrobione w tej fali — `backtest_engine.py` jest samodzielny, nie wie o `backtest_apex.py`.

---

# F004 — Dowód: integracja z `backtest_apex.py` (fala 5, ostatnia)

> Zakres tej fali: `backtest_apex.py`'s domyślna (nie `--param-optimization`) ścieżka wykonania przestaje liczyć bezkosztowo przez `strategy.backtest_trailing` i zamiast tego woła `backtest_engine.run_backtest` (fala 4, złożenie `costs.py`/`equity.py`/`execution.py`/`data_contract.py`). `strategy.py`/`main.py`/`trader.py`/`configuration/` NIE zostały zmienione — tylko `backtest_apex.py` (adapter/wiring) i testy.

## Co zostało zbudowane

### 1. Rozszerzenie metryk `backtest_engine.py` (`_compute_metrics`)

Dodano do istniejącego słownika metryk (`total_net_pnl`, `win_rate`, `max_drawdown_pct`, `n_trades`, `final_equity` — bez zmiany nazw, superset, nie przemianowanie) pięć nowych kluczy, semantyka dopasowana do `strategy.py`'s `_compute_metrics` (`strategy.py:779-826`), nie tylko nazwa pola:

- **`profit_factor`** = suma zyskownych `net_pnl` / `abs(suma stratnych net_pnl)`, **`0.0` gdy brak strat** — jawnie INNE niż sentinel `9999.0` w `strategy.py:822`, bo tak nakazał tickiet wprost (nie "naprawa" starego zachowania, świadome odejście udokumentowane w kodzie i teście `test_compute_metrics_profit_factor_is_zero_when_no_losing_trades`).
- **`max_drawdown_usd`** = szczyt-do-dołka equity curve w dolarach: `max(running_peak(equity) - equity)`, liczone niezależnie od `drawdown_pct` (osobna funkcja `_max_drawdown_usd`).
- **`max_drawdown_abs_pct`** = dokładnie ta sama wartość co `max_drawdown_pct` — zweryfikowane w `strategy.py:816-820`, że `max_drawdown` i `max_drawdown_abs_pct` tam też są literalnie tym samym `round(max_dd_pct, 1)`, nie dwoma różnymi liczbami; ten sam alias odtworzony tutaj.
- **`calmar`** = `total_net_pnl / (max_drawdown_usd + 1e-9)` — dokładnie ta sama formuła co `strategy.py:816` (`calmar = total_pnl / (max_dd_usd + 1e-9)`), bez annualizacji — dopasowane 1:1, nie "naprawione".
- **`ambiguous_pct`** = `0.0` na stałe, z komentarzem w kodzie: `execution.py` rozstrzyga niejednoznaczność SL/TP wewnątrz bara deterministycznie (SL zawsze wygrywa, `execution.resolve_stop_take_within_bar`), więc miara "jak często było niejednoznacznie" nie ma już tego samego zastosowania — pole zostaje obecne (nie usunięte), żeby nie rozbić dostępu do klucza w `backtest_apex.py`.

Testy (`tests/test_backtest_engine.py`, dodane do istniejącego pliku fali 4):

1. `test_new_metrics_fields_on_full_fixture_run_recomputed_independently` — dla pełnego przebiegu na fixture (`RSI14_7030`, 17 transakcji), każde z pięciu nowych pól przeliczone NIEZALEŻNIE z `res.trades`/`res.equity_curve` (nie przez zaufanie własnemu kodowi silnika) i porównane `pytest.approx`.
2. `test_compute_metrics_new_fields_hand_calculated` — w pełni ręcznie skonstruowane `trades_df`/`equity_curve` (3 transakcje: +10, −4, +20; 6-wierszowa krzywa equity 500→510→508→506→515→526) wywołane bezpośrednio przez `be._compute_metrics(...)`, z arytmetyką w komentarzu nad testem: `profit_factor=30/4=7.5`, `max_drawdown_usd=4.0` (peak 510 w indeksie 3, equity 506), `max_drawdown_pct=max_drawdown_abs_pct=78.4314%` (`400/510*100`), `calmar=26/(4+1e-9)≈6.499999998`.
3. `test_compute_metrics_profit_factor_is_zero_when_no_losing_trades` — 2 transakcje, obie zyskowne (`+5`, `+10`) → `profit_factor==0.0` dokładnie (nie `9999.0`), zgodnie z jawnym wymogiem tickieta.

### 2. `backtest_apex.py`: podłączenie domyślnej ścieżki do `backtest_engine.run_backtest`

- Dodany import `backtest_engine` (obok istniejącego `from strategy import ...`, który zostaje — `backtest_trailing` nadal potrzebny dla gałęzi `--param-optimization`).
- Nowa funkcja `_adapt_backtest_result(bt_result)` mapuje `BacktestResult.metrics` (nazwy pól `backtest_engine.py`: `total_net_pnl`, `max_drawdown_pct`, ...) na dokładnie te klucze, których oczekuje reszta pliku (`total_pnl`, `max_drawdown`, `max_drawdown_usd`, `max_drawdown_abs_pct`, `profit_factor`, `n_trades`, `calmar`, `ambiguous_pct` — te same nazwy co `strategy.backtest_trailing`'s metryki wcześniej, `strategy.py:816-825`) — samo przemianowanie, nie przeliczenie.
- W pętli `for strategy_name in strategy_names:`, gałąź `else:` (nie-`OPTIMIZATION`) zamieniona z wywołania `backtest_trailing(df, ...)` na:
  ```python
  bt_result = backtest_engine.run_backtest(
      df_ind, strategy_name, interval=INTERVAL,
      initial_equity=500.0, stake=POSITION_SIZE_USDT, leverage=LEVERAGE,
      atr_multiplier=ATR_MULT, max_sl_pct=MAX_SL_PCT,
      activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT,
      cooldown_candles=COOLDOWN_CANDLES,
  )
  trades_df, metrics = _adapt_backtest_result(bt_result)
  ```
  `df_ind` to zmienna modułowa sprzed dodania kolumny `"signal"` (kolumna `signal` jest dodawana tylko do lokalnej kopii `df = df_ind.copy()` używanej przez gałąź `OPTIMIZATION`) — celowo, bo `backtest_engine.run_backtest` sam woła `strategy.add_indicators` i sam generuje kolumnę `signal` wewnętrznie (`data_contract.filter_closed_candles` → `strategy.add_indicators` → `STRATEGY_CATALOG[strategy_name]`). Podwójne wywołanie `add_indicators` (raz na poziomie modułu dla `df_ind`, raz wewnątrz `run_backtest`) jest nieszkodliwe — `add_indicators` przelicza wszystkie kolumny wyłącznie z `close`/`high`/`low`/`volume` i nadpisuje te same nazwy kolumn deterministycznie, zweryfikowane przez faktyczne uruchomienie (zobacz sekcja "Dowód" niżej — wynik identyczny niezależnie od tego, czy `df_ind` ma już policzone wskaźniki).
- Gałąź `if OPTIMIZATION:` NIE została zmieniona funkcjonalnie — nadal woła `_run_optuna_strategy` → `backtest_trailing` (stary, bezkosztowy silnik). Dodano jawny komentarz na początku tej gałęzi w kodzie (`backtest_apex.py`, tuż po `if OPTIMIZATION:`):
  > "KNOWN FOLLOW-UP GAP (F004 wave 5): the Optuna search path still calls the old cost-free strategy.backtest_trailing ... Re-wiring Optuna to the new cost/equity-aware engine is out of scope for this wave and is future work"

  To jest świadomie udokumentowana luka, nie cicho porzucona integracja — `--param-optimization` pozostaje na starym, bezkosztowym silniku do kolejnej pracy (poza scope F004).

### 3. Nietknięte pliki

`strategy.py`, `main.py`, `trader.py`, `configuration/` — bez zmian (`git diff --stat` po tej fali pokazuje wyłącznie `backtest_apex.py`, `backtest_engine.py`, `tests/test_backtest_engine.py` (zmienione) i `tests/test_apex_uses_new_engine.py` (nowy)). Tryb `--local-csv` (F002, offline) działa nadal — `tests/test_offline_backtest.py` (przedistniejące, bez zmian) przechodzi bez modyfikacji.

## Test dyskryminujący: `tests/test_apex_uses_new_engine.py`

Uruchamia `backtest_apex.py` jak samodzielny skrypt CLI (ten sam wzorzec `runpy.run_path(..., run_name="__main__")` co `tests/test_offline_backtest.py`, offline `--local-csv` na fixture, sieć zablokowana przez `monkeypatch`) w trybie DOMYŚLNYM (bez `--param-optimization`), strategia `RSI14_7030`, i weryfikuje trzema niezależnymi odniesieniami, że wynik faktycznie pochodzi z nowego, kosztowego silnika — nie jest tylko "inny", tylko **weryfikowalnie niższy o policzalną kwotę kosztów**:

1. **Referencja 1 (parytet wywołania)**: bezpośrednie wywołanie `backtest_engine.run_backtest` z dokładnie tymi samymi parametrami, które teraz przekazuje `backtest_apex.py` (te same `df_ind`, `strategy_name`, `interval`, `initial_equity=500.0`, `stake=100.0`, `leverage=10`, `atr_multiplier=2.5`, `max_sl_pct=0.03`, `activate_pct=0.03`, `trail_pct=0.015`, `cooldown_candles=0` — wartości z `configuration/default.yaml`). Zweryfikowane: `n_trades` i `total_net_pnl` z raportu `report.json`'s `summary["best_pnl"]`/`summary["best_n_trades"]` (`21` transakcji, `$197.651764`) zgadzają się z bezpośrednim wywołaniem `pytest.approx(..., abs=0.01)` — nie "w tym samym przedziale", tylko ten sam kod, te same liczby.
2. **Referencja 2 (rekoncyliacja kosztów co do grosza)**: to samo wywołanie z `commission_rate_bps=half_spread_bps=slippage_bps=slippage_fixed=0.0`. Ponieważ decyzje o czasie/cenie wejścia i wyjścia w `run_backtest` NIE zależą od parametrów kosztowych (koszty są aplikowane dopiero w `Portfolio.close_position`, po ustaleniu fill price/timing), sekwencja transakcji (czasy wejścia/wyjścia) jest IDENTYCZNA między przebiegiem z kosztami i bez — zweryfikowane wprost (`entry_time`/`exit_time` tablice równe element-po-elemencie). Przy zerowym funding (`funding_pnl==0.0` dla każdej transakcji) różnica `total_net_pnl` (bez kosztów) − `total_net_pnl` (z kosztami) = **dokładnie** suma `total_costs` z transakcji z kosztami (`$67.037209` na tym przebiegu, `pytest.approx(rel=1e-6)`) — nie przybliżenie, tylko rekoncyliacja co do grosza. To jest właściwy dowód "niższy o weryfikowalną, niezerową kwotę kosztów, nie tylko inny".
3. **Referencja 3 (dosłowne porównanie z tickieta)**: bezpośrednie wywołanie starego, bezkosztowego `strategy.backtest_trailing` z tymi samymi parametrami config-owymi, jakich `backtest_apex.py` używał PRZED tą falą (w tym `entry_on_open=ENTRY_ON_OPEN` z `configuration/default.yaml`, tu `False` — inny mechanizm timing wejścia niż `run_backtest`'s zawsze-`entry_on_open=True`, patrz "Znana luka" niżej) i tym samym zdegenerowanym `sub_lookup` (główne świece jako własne sub-świece, offline), jak w kodzie `backtest_apex.py`. Wynik: stary bezkosztowy silnik dałby `total_pnl=$289.38` (20 transakcji) na tych samych danych/strategii, wobec `$197.65` (21 transakcji) z nowego, kosztowego wywołania przez `backtest_apex.py` — różnica `$91.73`, zweryfikowana `assert apex_pnl < legacy_free_pnl` i `assert (legacy_free_pnl - apex_pnl) > 1.0` (nie szum zaokrągleń). Liczba transakcji różni się (20 vs 21) z powodu innego mechanizmu wejścia (`entry_on_open` semantyka, patrz niżej) — dlatego ta referencja jest nierówną (ale silną) nierównością, nie dokładną rekoncyliacją jak Referencja 2.

## Znana luka wynikająca z tej integracji (nowa, do udokumentowania — NIE naprawiona w tej fali)

`configuration/default.yaml` ma `ENTRY_ON_OPEN: false` — przed tą falą `backtest_apex.py`'s domyślna ścieżka wołała `backtest_trailing(..., entry_on_open=ENTRY_ON_OPEN, ...)`, czyli wejścia na `close` bara sygnałowego (nie na `open` kolejnego bara). `backtest_engine.run_backtest` (fala 4, kontrakt zamrożony przed tą falą) replikuje WYŁĄCZNIE `entry_on_open=True` (wejście na otwarciu następnego bara po sygnale) — nie przyjmuje parametru `entry_on_open` i tickiet fali 5 jawnie nie wymienia go w liście argumentów do przekazania. Efekt: po tej integracji domyślna ścieżka `backtest_apex.py` faktycznie zawsze wchodzi na `open` następnego bara, NIEZALEŻNIE od `ENTRY_ON_OPEN: false` w configu — realna, nie tylko kosmetyczna różnica timing (widoczna wyżej: 21 vs 20 transakcji na tym samym fixture/strategii). To jest znana, udokumentowana tu luka (nie cicho pominięta) pozostawiona na kolejną pracę — rozszerzenie `backtest_engine.run_backtest` o parametr `entry_on_open` byłoby zmianą kontraktu fali 4, poza scope fali 5 (fala 5 miała integrować, nie rozszerzać silnik). Uwaga: `entry_on_open=True` (nowe zachowanie) jest ogólnie bardziej konserwatywne/realistyczne niż `entry_on_open=False` (wejście na `close` sygnałowego bara to częściowy look-ahead — cena `close` bara, na którym liczony jest sygnał, nie jest jeszcze znana w momencie decyzji handlowej w praktyce), więc to nie jest regresja jakości symulacji, tylko rozjazd z bieżącą wartością configu.

## Wynik testów

Uruchomione przez `/home/limen/bot_traiding_daily/.venv_test/bin/python -m pytest -v` z katalogu głównego repo (ten sam współdzielony venv testowy co fale 1-4, BEZ argumentu ścieżki jako pierwszego argumentu — patrz pułapka `sys.argv`/`strategy._resolve_config_path` opisana przy fali 4):

```
tests/test_apex_uses_new_engine.py::test_apex_default_path_uses_cost_aware_engine_not_free_legacy_one PASSED
tests/test_backtest_engine.py (7 testów, w tym 3 nowe dla metryk fali 5) PASSED
tests/test_costs.py (12 testów) PASSED
tests/test_data_contract.py (11 testów) PASSED
tests/test_equity.py (15 testów) PASSED
tests/test_execution.py (17 testów) PASSED
tests/test_offline_backtest.py (2 testy, przedistniejące, bez zmian) PASSED

63 passed in 2.27s
```

Brak regresji w 59 przedistniejących testach fal 1-4 (`test_costs.py`, `test_equity.py`, `test_execution.py`, `test_backtest_engine.py`'s oryginalne 4, `test_data_contract.py`, `test_offline_backtest.py`). `git status`/`git diff --stat` po tej fali pokazuje wyłącznie: `backtest_apex.py` (zmieniony, +49/−9), `backtest_engine.py` (zmieniony, +42), `tests/test_backtest_engine.py` (zmieniony, +81), `tests/test_apex_uses_new_engine.py` (nowy plik) — `strategy.py`/`main.py`/`trader.py`/`configuration/` niezmienione, zgodnie z acceptance tickieta F004.

## Co pozostaje poza scope F004 (dla przyszłych ticketów)

- **Re-wiring Optuna (`--param-optimization`) do `backtest_engine.run_backtest`** — udokumentowane jako known gap wprost w kodzie (`backtest_apex.py`, komentarz na początku gałęzi `if OPTIMIZATION:`) i tutaj. Gałąź optymalizacji nadal liczy bezkosztowo.
- **Egzekwowanie limitu 50% max DD** — `equity.Portfolio.mark_to_market` śledzi `peak_equity`/`drawdown_pct`, `backtest_engine.py` przekazuje to dalej w `metrics["max_drawdown_pct"]`, ale nic nie zatrzymuje backtestu ani nie blokuje nowych wejść przy przekroczeniu 50% — to osobna praca (nie było w scope żadnej z pięciu fal F004, poza samym śledzeniem).
- **Rozjazd `entry_on_open`** opisany wyżej — `backtest_engine.run_backtest` powinien dostać parametr `entry_on_open` zgodny z `configuration/default.yaml`, żeby domyślna ścieżka `backtest_apex.py` faktycznie honorowała `ENTRY_ON_OPEN: false` zamiast go cicho ignorować.
- **Wielo-symbolowy portfel / F007** — jawnie poza scope F004 od początku (patrz `ticket.md`).
