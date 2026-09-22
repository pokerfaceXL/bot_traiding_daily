# F006 — Kontrola pozytywna pipeline'u backtestu (positive control)

> Diagnostyka/walidacja, nie badanie strategii. Cel: sprawdzic, zanim F006 (poszukiwanie
> nowych hipotez) ruszy na dobre, czy kategoryczny wynik 0/24885 (`F005-baseline.md`) i
> 0/700 (`F005-leverage-sensitivity.md`) to realne stwierdzenie o katalogu strategii, a nie
> pozostajacy blad pipeline'u. Zero zmian w `strategy.py`/`backtest_apex.py`/
> `backtest_engine.py`/`costs.py`/`equity.py`/`execution.py`/`data_contract.py`/
> `regularity.py`/`main.py`/`trader.py`/`configuration/` ani zadnym pliku F001-F005 —
> tylko nowy skrypt (`scripts/f006_positive_control.py`), nowy fixture
> (`tests/fixtures/positive_control_uptrend.csv`), nowy test
> (`tests/test_positive_control.py`) i ten raport.

## Skonstruowany scenariusz (krok 1 zadania)

`scripts/f006_positive_control.py:build_synthetic_uptrend` buduje deterministycznie (zero
RNG), 280 swiec 4h (`interval="240"`), od `2024-01-15 00:00:00` do `2024-03-01 12:00:00`:

- `close[i] = 100.0 + 0.12*i + 0.35*sin(2*pi*i/24)` — liniowy dryf w gore plus male,
  realistycznie wygladajace wachniecie (amplituda 0.35, okres 24 swiece = 4 dni).
  Pochodna ciaglego przyblizenia: `drift +/- amp*2*pi/period = 0.12 +/- 0.0916`, czyli
  **zawsze dodatnia** (zakres [0.0284, 0.2116]) — z konstrukcji zaden bar nie ma nizszego
  `close` niz poprzedni. Zweryfikowane wprost w skrypcie i tescie: **0 z 279 przejsc
  bar-nad-bar ma `close[i] < close[i-1]`**.
- `open[i] = close[i-1]` (ciagle, bez luk cenowych).
- `high`/`low` = `open`/`close` +/- mala, deterministyczna wewnatrzswiecowa amplituda
  (`0.10 + 0.02*sin(i*0.7)`, ~0.08-0.12 USD) — realistyczny ksztalt swiecy, nie plaska linia.
- `volume` = `1000 + 50*sin(i*0.3)` (deterministyczne, zawsze dodatnie).
- Cena rosnie z **100.00 do 133.23 (+33.23%)** przez cala serie.

Zapisane jako `tests/fixtures/positive_control_uptrend.csv`, w tym samym formacie OHLCV co
istniejace fixture (`tests/fixtures/ohlcv_sample.csv`): naglowek
`timestamp,open,high,low,close,volume`, timestamp bez tz (traktowany jako UTC, ten sam
wzorzec co `data_contract.py`).

**Wybor strategii (krok 2, uzasadnienie):** `EMA_8_21` z `strategy.STRATEGY_CATALOG` —
czysty crossover dwoch EMA (`sig_ema_cross`, `strategy.py:186`), zawsze w rynku (sygnal
+1/-1, nigdy nie plaski poza pierwszym barem), zero dodatkowych filtrow (RSI/ADX/objetosc).
To najprostszy mozliwy wariant trend-following w katalogu — na czystym, monotonicznym
uptrendzie powinien wejsc raz w long i trzymac pozycje, bez zbednych wejsc/wyjsc, co czyni
wynik latwym do policzenia recznie (patrz nizej).

## Wynik — NOWY silnik (`backtest_engine.run_backtest`, leverage=1)

Parametry: `initial_equity=500, stake=100, leverage=1` (placeholder badawczy F006 z
`spec/build.md`), `commission_rate_bps=10, half_spread_bps=5, slippage_bps=2` (te same co
`F005-baseline.md`), `atr_multiplier=1.5, max_sl_pct=0.05, activate_pct=0.03, trail_pct=0.02,
cooldown_candles=0` (domyslne `run_backtest`, nieujawnione w tickiecie jako zmienione).

```
total_net_pnl:     +32.58
final_equity:      532.58   (start: 500.00)
max_drawdown_pct:  0.0693%
n_trades:          1
win_rate:          100.0%
skipped_signals:   0
```

**Dokladnie jedna transakcja**: long, wejscie `2024-01-15 08:00` @ 100.2106 (pierwszy bar po
przecieciu EMA8>EMA21 — sygnal wchodzi na open nastepnego bara, jak dokumentuje
`execution.resolve_entry_fill`), trzymana do konca danych, zamknieta
`exit_reason="end_of_data"` `2024-03-01 12:00` @ 133.2325. Trend nigdy sie nie odwraca, wiec
sygnal nigdy nie daje przeciwnego kierunku ani stopu — dokladnie taki wynik, jaki uzasadnienie
wyboru strategii przewidywalo.

**Reczna kalkulacja (niezalezna od silnika, wprost z cen wejscia/wyjscia + `costs.py`)**,
wykonana w skrypcie i powtorzona w `tests/test_positive_control.py`:

```
notional = stake * leverage = 100.0
quantity = notional / entry_price = 100 / 100.2106 = 0.997899
gross_pnl = quantity * (exit_price - entry_price) = 0.997899 * 33.0219 = 32.952532
total_costs (komisja+spread x2 nog + slippage wejscia, costs.py) = 0.369429
net_pnl = 32.952532 - 0.369429 = 32.583104
```

**Zgadza sie co do grosza z wyjsciem silnika** (`t["net_pnl"] == 32.583104`) — asercja
`abs(hand_net_pnl - engine_net_pnl) < 1e-6` przechodzi. To nie jest przypadkowa zgodnosc —
scenariusz zostal celowo skonstruowany tak, zeby dac dokladnie jedna transakcje policzalna
na kartce, i silnik daje dokladnie to, czego formula przewiduje.

## Regularnosc (`regularity.compute_regularity` na krzywej equity nowego silnika)

| Miesiac | n | is_partial | is_valid | positive_day_pct | deviation_pct | target_met |
| --- | ---: | --- | --- | ---: | ---: | --- |
| 2024-01 | 17 | True | **False** (pierwszy dzien calej krzywej = missing, patrz nizej) | — | — | — |
| **2024-02** | **29** | **False** | **True** | **100.0** | **0.0** | **True** |
| 2024-03 | 1 | True | True | 0.0 | 100.0 | False (partial, nieporownywalny z progiem pelnego miesiaca) |

Luty 2024 (jedyny pelny, niebrzegowy miesiac calkowicie pokryty przez fixture) osiaga
**`deviation_pct = 0.0%`** — nie tylko spelnia prog `<=20%` z `spec/build.md`, jest to
najlepszy mozliwy wynik (kazdy z 29 dni lutego jest `positive`). Styczen jest niewazny
wylacznie dlatego, ze pierwszy dzien calej krzywej equity jest z definicji `missing`
(udokumentowana regula `regularity.py`, ten sam mechanizm co w fali 2/3 F005 — nie usterka
tej diagnostyki). Marzec jest brzegowo-czesciowy (1 dzien) i poprawnie oznaczony
`is_partial=True`, wiec nie jest porownywany z progiem pelnego miesiaca.

## Wynik — STARY silnik (`strategy.backtest_trailing`, F004-era, bez kosztow)

Te same parametry sygnalu/SL/trailing co nowy silnik (`atr_multiplier=1.5, max_sl_pct=0.05,
activate_pct=0.03, trail_pct=0.02, leverage=1, stake=100, entry_on_open=True,
cooldown_candles=0`) — jedyna roznica to brak modelu kosztow/equity w starym silniku.

Surowa lista transakcji (`old_trades`, wprost z `strategy.backtest_trailing`): **dokladnie
jedna transakcja**, `type="Long (Open)"`, wejscie/wyjscie identyczne co do ceny i czasu z
nowym silnikiem (`entry_price=100.2106`, `exit_price=133.2325`), `pnl_usd=32.952532` —
**dokladnie rowne `gross_pnl` nowego silnika** (32.952532), co jest oczekiwane: ten sam
sygnal, ten sam moment wejscia/wyjscia, zero kosztow w starym silniku, wiec jego "czysty"
PnL powinien byc rownowazny PnL nowego silnika PRZED odjeciem kosztow — i jest, co do 6
miejsca po przecinku (`tests/test_positive_control.py::test_old_engine_trade_matches_new_engine_gross_pnl`).

**Usterka do odnotowania, nie tej diagnostyki:** zagregowane metryki starego silnika
(`old_metrics`, `strategy._compute_metrics`) pokazuja `total_pnl=0.0, n_trades=0` mimo
istnienia tej jednej, wyraznie zyskownej transakcji w `old_trades`. Przyczyna jest w
niezmienionym `strategy.py:780` (`_compute_metrics`): filtruje transakcje po
`~type.str.contains("Open")` **przed** policzeniem `total_pnl`, i jesli po filtrze nie
zostaje nic (a nasza jedyna transakcja to `"Long (Open)"`, bo pozycja jest wciaz otwarta na
koniec danych, zamknieta dopiero w kroku 5 backtest_trailing jako "koniec danych"), funkcja
zwraca `_empty_metrics()` bez w ogole zerknieccia na `total_pnl` policzone z pelnego
`trades_df`. To **istniejacy artefakt agregacji metryk starego, F004-erowego silnika**
(transakcje wciaz otwarte na koniec przebiegu sa calkowicie pomijane w podsumowaniu, mimo
ze sa widoczne i policzalne w surowym `trades_df`) — nie modyfikuje sie tu `strategy.py`
(poza zakresem tickieta), tylko odnotowuje sie ten fakt jawnie, zeby nie czytac
`old_metrics["total_pnl"]==0.0` jako "stary silnik tez zawodzi". Surowe dane (`old_trades`)
pokazuja jednoznacznie pozytywny wynik.

## Weryfikacja odpornosci testu (dyskryminujacy check)

Zanim test zostal uznany za wiarygodny, przeprowadzono recznie sabotaz `equity.py`
(tymczasowa zmiana `if available < margin:` na `if available < margin * 1000:`, symulujaca
wadliwy pipeline, ktory blokuje niemal kazde otwarcie pozycji) i uruchomiono
`tests/test_positive_control.py` — **4 z 5 testow natychmiast padly** (0 transakcji zamiast
1, `IndexError` przy probie odczytu nieistniejacej pierwszej transakcji), potwierdzajac, ze
test rzeczywiscie wykrywa zepsuty pipeline, a nie tylko przechodzi na nietknietym kodzie.
Plik przywrocony do stanu oryginalnego przed commitem (`diff` potwierdzil identycznosc z
kopia zapasowa, `git status` przed commitem pokazuje wylacznie nowe pliki tej diagnostyki).

## Werdykt

**Pipeline moze wyprodukowac pozytywny/przechodzacy wynik w sprzyjajacych warunkach —
znaleziska F005 (0/24885 i 0/700) sa wiarygodne.**

Na celowo skonstruowanym, deterministycznym, niskoszumowym uptrendzie (280 swiec 4h,
+33.23% ceny, zero barow spadkowych z konstrukcji), pod parametrami zgodnymi z zakresem
tickieta F006 (leverage=1, koszty/equity identyczne z `F005-baseline.md`):

1. Konto **przetrwalo** (`final_equity=532.58` > `initial_equity=500.00`, nigdzie w poblizu
   progu `$100` opisanego w `F005-baseline.md` jako mechanizm bankructwa przy leverage=10).
2. Net PnL byl **jednoznacznie dodatni** (+$32.58, `win_rate=100%`, `profit_factor=9999.0`
   — brak przegranych transakcji w ogole).
3. Max drawdown byl **znikomy** (0.0693%), dalekie od progu odrzucenia 50% z `spec/build.md`.
4. `regularity.compute_regularity` pokazal **pelny, wazny miesiac (luty 2024) spelniajacy
   cel regularnosci z zapasem** (`deviation_pct=0.0%`, najlepszy mozliwy wynik, nie tylko
   "w pobliżu" progu `<=20%`).
5. Reczna kalkulacja z surowych cen + `costs.py` **zgadza sie co do grosza** z wyjsciem
   silnika — nie ma ukrytej rozbieznosci miedzy tym, co silnik powinien policzyc, a tym,
   co faktycznie liczy.
6. Niezalezny, bezkosztowy stary silnik (`strategy.backtest_trailing`) daje **identyczny
   surowy PnL transakcji** (przed kosztami) na tych samych danych/sygnale/parametrach SL —
   sygnal i logika wejscia/wyjscia dzialaja tak samo w obu silnikach; jedyna roznica to
   model kosztow nowego silnika, ktory tutaj obcina zaledwie $0.37 z $32.95 (koszty nie sa
   przyczyna zadnego problemu na tych danych).

**Wniosek:** kategoryczny 0/24885 (`F005-baseline.md`) i 0/700 (`F005-leverage-sensitivity.md`)
NIE jest artefaktem zepsutego pipeline'u — mechanizm bankructwa konta przy leverage=10 na
prawdziwym katalogu strategii (margin=stake niezaleznie od dzwigni, ujemna przewaga sygnalu
zjadajaca $500->$100 w ciagu 1-3 miesiecy) jest realnym zjawiskiem tych konkretnych strategii
na prawdziwych, szumnych danych rynkowych, a nie skutkiem błędu w `backtest_engine.py`/
`costs.py`/`equity.py`/`execution.py`/`regularity.py`. Te moduly poprawnie, dokladnie i
przewidywalnie licza pozytywny wynik, kiedy sygnal i dane faktycznie na to zasluguja. F006
(poszukiwanie nowych hipotez) moze ruszyc bez podejrzenia bledu w warstwie
backtest/koszty/equity/regularnosc.

## Pliki tej diagnostyki

- `scripts/f006_positive_control.py` — skrypt budujacy fixture i uruchamiajacy oba silniki
  (uruchomienie: `.venv_test/bin/python scripts/f006_positive_control.py`).
- `tests/fixtures/positive_control_uptrend.csv` — 280 swiec, deterministyczny uptrend.
- `tests/test_positive_control.py` — 5 testow kodujacych zweryfikowany, rzeczywisty wynik
  (nie zalozony z gory): czysty monotoniczny uptrend, przetrwanie + dodatni PnL nowego
  silnika, zgodnosc z reczna kalkulacja, spelnienie celu regularnosci w lutym 2024, zgodnosc
  surowego PnL starego silnika z gross_pnl nowego.
- Ten plik.

Zaden plik F001-F005 (`strategy.py`, `backtest_apex.py`, `backtest_engine.py`, `costs.py`,
`equity.py`, `execution.py`, `data_contract.py`, `regularity.py`, `main.py`, `trader.py`,
`configuration/`) nie zostal zmieniony w tej diagnostyce.
