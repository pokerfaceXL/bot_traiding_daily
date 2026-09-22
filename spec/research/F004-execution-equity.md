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
