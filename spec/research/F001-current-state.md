# F001 — Mapa obecnego zachowania bota (live) i kontrakt sygnału/ryzyka

> Statyczny przegląd kodu, bez uruchamiania botów/backtestów/zleceń, bez importu `trader.py` w Pythonie. Przegląd main.py, trader.py, strategy.py, backtest_apex.py, run_backtest_apex.py, configuration/, logs/configuration/, logs/*.log, config.py, rest_logs.py, logger_config.py. Data przeglądu: 2026-09-21.

## 1. Pętla main.py

- Źródło świec: WebSocket Bybit `kline.{interval}.{symbol}` (`main.py:68-73`), nasłuch bez pollingu. Callback `_on_kline` (`main.py:57-64`) filtruje tylko potwierdzone świece (`candle.get("confirm")`) i wrzuca je do kolejki `_candle_queue` (`maxsize=20`, `main.py:33`) przez `put_nowait`; gdy kolejka pełna, świeca jest cicho pomijana (`main.py:63-64` — komentarz: „duplikat i tak zostanie pominięty”).
- Główna pętla `main()` (`main.py:111-158`) blokuje się na `_candle_queue.get(timeout=GAP_CHECK_INTERVAL_SEC)` (`main.py:130`, domyślnie 30 s z configa, `main.py:119`).
  - Gdy przyjdzie potwierdzona świeca: aktualizacja cache (`update_candle_cache`, `main.py:133` → `trader.py:180-193`), log, `report_bot_alive`, i wywołanie `TraderBot(config)` (`main.py:142`) — to jest jedyne miejsce, gdzie generowany jest sygnał i podejmowana decyzja wejścia/wyjścia.
  - Gdy timeout (`queue.Empty`, `main.py:144-151`): brak nowej świecy — bot loguje keepalive i wywołuje `update_tsl()` (`main.py:149`), czyli **bot-managed TSL i gap protection są odpytywane co `GAP_CHECK_INTERVAL_SEC` (nie co świecę)**, niezależnie od zamknięcia świecy.
  - Każdy inny wyjątek w pętli: log błędu, `send_error_to_apex`, `time.sleep(5)` (`main.py:153-155`) — pętla się nie zatrzymuje.
- `TraderBot` jest wywoływany raz na potwierdzoną świecę, `update_tsl` — co `GAP_CHECK_INTERVAL_SEC` niezależnie od świec. To dwa osobne rytmy decyzyjne w tym samym procesie.
- Config wczytywany raz przy starcie z `sys.argv[1]` lub domyślnie `configuration/default.yaml` (`main.py:44`); przeładowanie tylko przez `SIGHUP` (`main.py:94-103`).

## 2. Kontrakt wejścia/wyjścia/SL/TSL/cooldown/circuit breaker

### 2.1 Sygnał (strategy.py)

- `run_strategy(df, strategy_name)` (`strategy.py:818-846`) liczy wskaźniki (`add_indicators`, `strategy.py:103-181`) i generuje kolumnę `signal` z `STRATEGY_CATALOG[strategy_name](df)` (`strategy.py:369-467`, katalog 79 gotowych wariantów sygnałów EMA/RSI/MACD/BB/ADX/Stochastic/Triple-Screen, konwencja +1/-1/0).
- Gdy `df=None` (tryb bez cache), `run_strategy` sam pobiera dane HTTP i odrzuca ostatnią (niezamkniętą) świecę: `df = df.iloc[:-1]` (`strategy.py:836`). W trybie live tego wywołania z `df=None` bot nie używa — dostaje gotowy `df_cache`.

### 2.2 Cache i decyzja (trader.py, TraderBot)

- `TraderBot` (`trader.py:658-720`):
  1. `check_for_new_closed_positions()` (`trader.py:660`) synchronicznie aktualizuje `count_profit` z Bybit **przed** circuit breakerem, celowo (`trader.py:658-660` komentarz) — inaczej bot mógłby otworzyć nową pozycję zanim dowie się o stracie z serwerowego TSL/SL.
  2. `_check_circuit_breaker()` (`trader.py:224-263`) — jeśli aktywny, `return` bez dalszej logiki.
  3. Wymaga `df_cache` ≥ 50 świec (`trader.py:667-669`), inaczej pomija iterację.
  4. `run_strategy(df=df_cache.copy(), strategy_name=...)` (`trader.py:673`) liczy sygnał na kopii cache (rolling 600 świec, `trader.py:82-83`, aktualizowany inkrementalnie w `update_candle_cache`, `trader.py:180-193`, bez zapytań HTTP poza startem).
  5. `_update_tsl_bot_managed(position)` wywoływane też tutaj, jeśli jest otwarta pozycja (`trader.py:701-702`) — czyli TSL jest liczony i na każdej świecy (w `TraderBot`), i co `GAP_CHECK_INTERVAL_SEC` (w `update_tsl()` z main.py).
  6. `_cooldown_ok()` (`trader.py:268-283`) sprawdzany przed otwarciem nowej pozycji.
  7. Logika wejścia/wyjścia na sygnale (`trader.py:706-720`): sygnał 1 (long) zamyka ewentualną krótką i otwiera long jeśli `can_open`; sygnał -1 analogicznie dla short; sygnał 0 — nic.

### 2.3 Realizacja zlecenia (`open_position`, `trader.py:330-402`)

- SL liczony przez `_calc_sl` (`trader.py:295-300`): **czysto procentowy** `dist = price * MAX_SL_PCT`; linia z ATR (`ATR_MULTIPLIER * atr_value`) jest zakomentowana (`trader.py:296`) — potwierdza ustalenie z build.md.
- `ORDER_TYPE` z configa (`trader.py:344-401`):
  - `"market"` — `place_order` typu Market ze stałym `stopLoss` (`slTriggerBy="MarkPrice"`, `slOrderType="Limit"`, `tpslMode="Full"`, `trader.py:344-351`).
  - `"limit"` / `"aggressive_limit"` — limit na best ask/bid (`limit`) albo z przesunięciem `LIMIT_OFFSET_PCT` za rynkiem (`aggressive_limit`, `trader.py:357-373`); zlecenie z `tpslMode="Partial"`, `slSize=qty`. Czeka na fill przez `_wait_for_fill` (poll co 0.5 s przez `FILL_TIMEOUT_SEC`, `trader.py:309-322`). Po timeoucie: `cancel_order` + fallback na Market z tym samym SL (`trader.py:383-401`).
- SL i TSL zawsze wysyłane do Bybit z `slTriggerBy="MarkPrice"` (`trader.py:348,369,397,508`) — **live używa MarkPrice do triggerowania SL**, w przeciwieństwie do backtestu opartego na OHLC (patrz sekcja 4).

### 2.4 Bot-managed TSL (`_update_tsl_bot_managed`, `trader.py:416-521`)

- Najpierw gap protection (jeśli `GAP_PROTECTION_ENABLED`): gdy `markPrice` przeskoczył `stopLoss` o więcej niż `GAP_PROTECTION_THRESHOLD_PCT`, bot natychmiast zamyka pozycję Market (`trader.py:432-450`), niezależnie od TSL.
- TSL: śledzi watermark peak `markPrice` od aktywacji (`ACTIVATE_PCT` zysku od entry), przesuwa `stopLoss` o `TRAIL_PCT` od watermarku, nigdy go nie cofa (`trader.py:452-484`). Aktualizacja wysyłana do Bybit tylko gdy poprawa ≥ `MIN_TSL_STEP_PCT` (`trader.py:487-490`). To **zastępuje** natywny server-side trailing stop Bybit (komentarz `trader.py:417-423`: server-side trailingStop wykonuje się jako Market, tu bot robi to sam limitem).
- `update_tsl()` (`trader.py:530-537`) to publiczny wrapper wywoływany z `main.py:149`; pobiera aktualną pozycję i deleguje do `_update_tsl_bot_managed`.

### 2.5 Cooldown (`_cooldown_ok`, `trader.py:268-283`)

- Dotyczy wyłącznie zamknięć przez SL (`_last_close_reason in {"initial_sl", "StopLoss"}`, `trader.py:270`) — **nie** dotyczy zamknięć przez `trailing_sl`, `signal_close` ani `gap_protection`. Blokuje nowe wejście przez `COOLDOWN_CANDLES` świec liczonych w `_candle_counter` (inkrementowany w `update_candle_cache`, `trader.py:193`).

### 2.6 Circuit breaker (`_check_circuit_breaker`, `trader.py:224-263`)

- Liczy skumulowany `count_profit` **tylko z transakcji tego bota** (nie equity całego portfela — komentarz `trader.py:226-228` i wprost w build.md), próg = `_loss_limit` = surowy `POSITION_SIZE_USDT` z configa (bez dźwigni, `trader.py:151`).
- Po przekroczeniu: halt do północy (`datetime.now()+1 dzień o 00:00`, `trader.py:239-241`), alert async do Apex (`_executor.submit(send_equity_halt_to_apex...)`, `trader.py:250`).
- Wyłączalny przez `CIRCUIT_BREAKER_ENABLED: false` w configu (`trader.py:229-230`) — **w plikach configuration/ obserwowanych w repo jest wyłączony wszędzie** (patrz sekcja 3).

## 3. Realny config produkcyjny

Pliki:
- `configuration/default.yaml` — zawiera `SYMBOL: PIPPINUSDT`, `STRATEGY: RSI14_trend50`, `CIRCUIT_BREAKER_ENABLED: false`, format z komentarzami i sekcjami opisowymi (nie alfabetyczny dump maszynowy).
- `configuration/ENJUSDT_240.yaml`, `LDOUSDT_240.yaml` — format alfabetyczny bez komentarzy, identyczny z `yaml.dump(cfg)` używanym w `run_backtest_apex.py:prepare_config` (`run_backtest_apex.py:135-144`, zapisywane do `configuration/backtest/<symbol>_<interval>.yaml`, nie do `configuration/`). To sugeruje, że te dwa pliki **nie są** produktem `run_backtest_apex.py` w bieżącym stanie repo (docelowy katalog to `configuration/backtest/`, którego nie ma — `find configuration/backtest/*` nic nie zwrócił), lecz zostały umieszczone ręcznie w `configuration/` w tym samym stylu zapisu.
- `configuration/JELLYJELLYUSDT_240.yaml`, `PIPPINUSDT_240.yaml` — ten sam alfabetyczny format.
- `logs/configuration/default.yaml`, `JELLYJELLYUSDT_240.yaml`, `PIPPINUSDT_240.yaml` — format z komentarzami i sekcjami (`# ─── Symbol i timeframe ───`), różny od plików w `configuration/` o tych samych nazwach: np. `logs/configuration/PIPPINUSDT_240.yaml` ma `POSITION_SIZE_USDT: 20`, `MAX_SL_PCT: 0.06`, `CIRCUIT_BREAKER_ENABLED` nieustawiony (brak), a `configuration/PIPPINUSDT_240.yaml` ma `POSITION_SIZE_USDT: 3`, `MAX_SL_PCT: 0.06`, brak `CIRCUIT_BREAKER_ENABLED`. Te dwa zestawy różnią się parametrami dla tych samych symboli — to **dwie różne wersje w czasie**, nie jeden spójny stan.
- `logs/ETHUSDT_240.log`, `logs/JELLYJELLYUSDT_240.log` — istnieją logi dla ETHUSDT, mimo braku pliku `ETHUSDT*.yaml` w `configuration/` ani `logs/configuration/`. Treść `logs/ETHUSDT_240.log` to wyłącznie ranking ~79 strategii w formacie `[strategy] PnL=... WR=... DD=... N=...` — dokładnie format linii logowanej przez `backtest_apex.py` (`backtest_apex.py:263-266` — linia `logger.info(f"[{strategy_name:<25}] PnL=...")`), **nie** zawiera śladów startu live (`main.py:125` „Bot uruchomiony”, `trader.py:176` „Trader gotowy”, WebSocket) — sprawdzone grepem, brak trafień. Wniosek: ten plik pochodzi z uruchomienia backtestu, nie z live tradingu, mimo nazwy pliku pasującej do wzorca `{SYMBOL}_{INTERVAL}.log` używanego też przez `main.py`/`trader.py` (`main.py:44`, `trader.py:145`).

**Nie da się statycznie ustalić, który plik jest faktycznie podawany jako `sys.argv[1]` przy uruchomieniu `main.py` na produkcji** — nie ma w repo pliku procesu (systemd/pm2/cron/Procfile — sprawdzone, brak), a `.env` z kluczami Bybit też nie istnieje w tym repo (sprawdzone: brak `.env*`), co jest spójne z `spec/build.md`/`spec/vision.md`: „Projekt nie ma dostępu do kluczy API giełdy”.

Korekta cytowanych linii: fallback na `configuration/default.yaml` jest w `initialize_config()` (`main.py:43`), analogicznie `trader.py:188`, `strategy.py:24-27`, `config.py:6` — nie w liniach 117-118 (tam jest inny fragment `main()`). Ważniejsze: `main()` sam wymaga jawnego argumentu i przerywa proces, jeśli go brak (`main.py:112-114`: `if len(sys.argv) < 2: print(...); sys.exit(1)`), więc fallback na `default.yaml` w `initialize_config()` jest w praktyce martwym kodem przy uruchomieniu przez `main()` — bota nie da się odpalić bez jawnej ścieżki configu. To osłabia, a nie wzmacnia, domysł „default.yaml = produkcja z braku argumentu”: skoro argument jest zawsze wymagany, o realnej ścieżce produkcyjnej świadczy tylko to, co operator faktycznie podał przy starcie procesu — czego nie da się ustalić statycznie z tego repo. `configuration/default.yaml` pozostaje najbardziej prawdopodobnym kandydatem tylko dlatego, że jako jedyny ma format ręcznie utrzymywanego szablonu (komentarze sekcyjne) — to nadal poszlaka, nie dowód — patrz „Otwarte pytania”.

We wszystkich odczytanych plikach `configuration/*.yaml` i `logs/configuration/*.yaml`, tam gdzie pole występuje, `CIRCUIT_BREAKER_ENABLED` jest `false`, poza `logs/configuration/JELLYJELLYUSDT_240.yaml`, gdzie jest `true`. Circuit breaker więc nie jest jednolicie wyłączony — zależy od pliku.

## 4. Rozbieżności symulacja/live

Potwierdzone z listy w `spec/build.md` („Ustalenia z kodu — punkt startowy”), z lokalizacją w kodzie:

1. **Brak prowizji/spreadu/poślizgu/fundingu w `_make_trade`** — potwierdzone: `_make_trade` (`strategy.py:750-767`) liczy `pnl_usd = raw_pnl_pct * leverage * stake` bez żadnego odjęcia kosztów; `backtest_apex.py` sam to przyznaje w raporcie (`backtest_apex.py:471`: „Legacy backtest: fees, slippage and funding are not included.”).
2. **`_compute_metrics` a equity początkowe** — sprecyzowane: `_compute_metrics(trades_df, stake)` jest wołane z `stake` jako `initial_equity` (`strategy.py:736`), czyli krzywa equity/peak/DD w backteście liczona jest od **stawki pojedynczego wejścia** (np. 100 USD), a nie od `initial_equity=500` całego portfela z `vision.md`. To nie jest literalnie „equity początkowe pominięte” — equity startowe jest uwzględnione (`strategy.py:785`: `equity = initial_equity + np.cumsum(pnl)`), ale to inne equity niż portfelowe z vision.md. Backtest nie modeluje też pozycji niezrealizowanych/otwartych w szeregu equity — DD liczone tylko po zamkniętych transakcjach (`closed = trades_df[~trades_df["type"].str.contains("Open")]`, `strategy.py:780`).
3. **`calmar` bez annualizacji** — potwierdzone: `calmar = total_pnl / (max_dd_usd + 1e-9)` (`strategy.py:797`), żadnej normalizacji do okresu rocznego.
4. **SL procentowy mimo opisów ATR-based, ATR zakomentowany** — potwierdzone w dwóch miejscach: live `trader.py:295-297`, backtest `strategy.py:491-493` — identyczny wzorzec komentarza `# dist = min(atr_multiplier * atr_value, price * max_sl_pct)` z aktywną tylko drugą częścią.
5. **Brak jawnego odrzucenia bieżącej niezamkniętej świecy w backteście** — potwierdzone: `backtest_apex.py:291` (`df_raw = get_bybit_ohlcv(...)`) i `backtest_apex.py:294` (`add_indicators`) nie zawierają żadnego `.iloc[:-1]` ani filtra na `confirm`/zamknięcie świecy, w przeciwieństwie do live (`trader.py:174`: `df_cache = raw.iloc[:-1].copy()` i `strategy.py:836`: `df = df.iloc[:-1]` w trybie bez cache).
6. **Bar Magnifier bez dowodu poprawnej kolejności zdarzeń w subświecy** — potwierdzone jako brak dowodu: `backtest_trailing` iteruje sub-świece i sprawdza SL/aktywację TSL sekwencyjnie (`strategy.py:614-655`), ale nie ma w kodzie ani testu, ani komentarza potwierdzającego, że kolejność OHLC-w-sub-świecy odzwierciedla rzeczywistą kolejność cen wewnątrz świecy głównej — sam kod to przyznaje przez `ambiguous_count`/`ambiguous_pct` (`strategy.py:619-621, 628-630`), czyli świadomie mierzy przypadki niepewne, nie eliminuje ich.
7. **Live używa MarkPrice, backtest OHLC** — potwierdzone: live SL/TSL trigger zawsze `slTriggerBy="MarkPrice"` (`trader.py:348,369,397,508`); backtest sprawdza SL względem `high`/`low` świecy/sub-świecy z OHLC (`strategy.py:614-655, 657-680`) — innego źródła ceny.
8. **Brak modelu wspólnego kapitału/margin/likwidacji** — potwierdzone: `backtest_trailing` traktuje każdą strategię i symbol niezależnie, `stake` jest stałe per wywołanie (`strategy.py:498-511`), nigdzie nie ma agregacji wielu jednoczesnych pozycji na wspólnym koncie ani liczenia marginu/likwidacji.
9. **Optuna stroi i ocenia na tym samym df; błąd `suggest_int(4, 3)`** — potwierdzone: `_run_optuna_strategy` (`backtest_apex.py:112-234`) dostaje ten sam `df` do `objective` co późniejsza ocena `best_trial` — nie ma podziału train/eval. `trial.suggest_int("leverage", 4, max_leverage)` (`backtest_apex.py:130`) — `_compute_max_leverage` (`backtest_apex.py:98-116`) może zwrócić `max_lev=3` przy wysokiej zmienności (`atr_pct >= 6.0`, `backtest_apex.py:113-114`), co przy dolnej granicy `4` daje niespójny zakres Optuny (low > high) — kod to jednak dopuszcza bez walidacji.
10. **`BACKTEST_MAX_DD_LIMIT`/`BACKTEST_WORST_LOSS_LIMIT` z YAML nieużywane** — potwierdzone: grep po tych nazwach w `backtest_apex.py` i `strategy.py` nie zwraca żadnych wystąpień poza samą nazwą pól w configu (nie są odczytywane nigdzie w kodzie odczytanym w tym przeglądzie).
11. **Interwał 5 min odrzucany (brak wpisu w `_SUB_INTERVAL_MAP`)** — potwierdzone: `_SUB_INTERVAL_MAP` (`strategy.py:474-481`) ma klucze `"1440","240","120","60","30","15"` — brak `"5"`; `backtest_apex.py:296-299` rzuca `ValueError` gdy `_SUB_INTERVAL_MAP.get(INTERVAL)` zwraca `None`. Interwał 5 min z zakresu 5 min–4 h uzgodnionego w `vision.md` jest więc obecnie niedostępny dla Bar Magnifiera w backteście.
12. **Puste wyniki/błędy mogą kończyć się kodem 0** — potwierdzone: `backtest_apex.py:309` (`sys.exit(0)` gdy za mało danych) i `backtest_apex.py:380` (`sys.exit(0)` gdy `not results`) — oba przypadki błędu/braku wyniku kończą proces kodem sukcesu, nieodróżnialnym od poprawnego przebiegu bez błędów w automatyzacji.

Nowe obserwacje (nieobjęte listą w build.md):

13. **`TraderBot` liczy sygnał na każdej potwierdzonej świecy niezależnie od interwału configu vs. rzeczywistego strumienia WebSocket** — `main.py` subskrybuje tylko jeden interwał z configa (`main.py:124`, `_start_websocket(SYMBOL, INTERVAL)`), więc jeśli `INTERVAL` w configu i `INTERVAL` użyte przy starcie WebSocketu się rozjadą (np. po SIGHUP z innym plikiem configu bez restartu WebSocketu), `TraderBot` dalej liczy strategię na starym interwale danych z cache. `reload_config_handler` (`main.py:94-103`) przeładowuje config i trader, ale **nie** wywołuje ponownie `_start_websocket` — WebSocket zostaje na starym symbolu/interwale.
14. **Rozjazd wersji configu w `configuration/` vs `logs/configuration/` dla tych samych symboli** (opisane w sekcji 3, punkt 3) — te same nazwy plików (`default.yaml`, `JELLYJELLYUSDT_240.yaml`, `PIPPINUSDT_240.yaml`) mają różne wartości parametrów ryzyka (`POSITION_SIZE_USDT`, `MAX_SL_PCT`, `CIRCUIT_BREAKER_ENABLED`) w obu katalogach — źródło rozbieżności nieznane statycznie (patrz „Otwarte pytania”).
15. **`update_tsl()` w `main.py:149` łapie wyjątki lokalnie i loguje ostrzeżenie** (`main.py:150-151`), ale nie inkrementuje żadnego licznika błędów ani nie eskaluje do circuit breakera — powtarzające się awarie sieci mogłyby ciągle blokować aktualizację TSL bez twardego stopu bota.
16. **`_cooldown_ok` odwołuje się do `_last_close_reason` ustawianego przez dwie różne ścieżki raportowania** (`check_for_new_closed_positions`, `trader.py:585-627` i `_report_closed_pnl_async`, `trader.py:547-582`) z osobną logiką przypisania powodu (`"trailing_sl"` vs `"StopLoss"` vs wstrzyknięty `reason`) — potencjalne źródło niespójności między tym, co faktycznie zamknęło pozycję na Bybit, a tym, co bot zapisze jako `_last_close_reason` do celów cooldownu.

## Otwarte pytania

1. Który plik configu jest faktycznie podawany jako argument `main.py` na serwerze produkcyjnym (`sys.argv[1]`)? W repo nie ma pliku uruchomieniowego (systemd/cron/pm2/Procfile) ani `.env` z kluczami — to poza zasięgiem statycznej analizy tego repo.
2. Dlaczego `configuration/JELLYJELLYUSDT_240.yaml` i `logs/configuration/JELLYJELLYUSDT_240.yaml` (analogicznie dla PIPPINUSDT, default) mają różne wartości `POSITION_SIZE_USDT`/`MAX_SL_PCT`/`CIRCUIT_BREAKER_ENABLED`? Czy `logs/configuration/` to zrzut configu z momentu startu bota (a więc historyczny „dowód” realnej konfiguracji live w danym momencie), czy osobny szablon niezwiązany z produkcją?
3. Skąd pochodzi `logs/ETHUSDT_240.log` (treść pasuje do formatu `backtest_apex.py`, ale ten skrypt domyślnie pisze do `logs/backtest/{symbol}_{interval}_backtest.log`, nie do `logs/{symbol}_{interval}.log`) — czy to ślad starszej wersji skryptu/loggera, ręcznego uruchomienia z inną nazwą, czy czegoś innego?
4. Czy `ENJUSDT_240.yaml`/`LDOUSDT_240.yaml` w `configuration/` (format zgodny z automatycznym `yaml.dump` z `run_backtest_apex.py:prepare_config`, ale w niewłaściwym katalogu — `configuration/`, nie `configuration/backtest/`) są efektem ręcznego skopiowania wyniku eksperymentu do „prod”, czy artefaktem nieudokumentowanej zmiany w skrypcie, która później została cofnięta?
5. Czy `CIRCUIT_BREAKER_ENABLED: true` w `logs/configuration/JELLYJELLYUSDT_240.yaml` (jedyny plik z tą wartością) odzwierciedla świadomą decyzję dla tego symbolu, czy błąd/przypadek przy tworzeniu configu?
6. Czy istnieje gdzieś (poza tym repo — np. na serwerze produkcyjnym) proces/skrypt startowy, który mógłby ujawnić faktyczny argument `sys.argv[1]` i potwierdzić właściciela configu live? To pytanie do właściciela, nie do dalszej analizy kodu.

> Odpowiedź właścicielki (2026-09-21): nikt obecnie nie pracuje na produkcji, kwestia nie jest istotna — nie śledzić dalej, który plik configu jest live (pytania 1, 2, 4, 5 pozostają nierozwiązane celowo).
