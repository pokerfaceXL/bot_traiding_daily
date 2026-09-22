# Build

> Plan startowy z przeglądu plików 2026-09-21. Dokumentacja i statyczna analiza kodu; bez uruchamiania bota, backtestów, zleceń ani eksportów do Apex.
> Identyfikatory F001–F010 to nasza robocza lista priorytetów (roadmapa), nie gotowe tickety Limen — Coordinator sam prowadzi tablicę i specyfikacje feature (patrz „Praca Coordinatora").

## TRACK

- Dążyć do dodatniego wyniku netto każdego dnia miesiąca na Bybit USDT perpetual (5 min–4 h); zmierzyć osiągalną regularność, zysk i odchylenie od celu przy uzgodnionym ryzyku.
- Kolejność dowodów: poprawna symulacja → walidacja chronologiczna → wynik portfela → kontrolowany pilotaż.
- Projekt nie ma dostępu do kluczy API giełdy — nie ma technicznej możliwości uruchomienia zleceń ani dotknięcia produkcji stąd. Dodanie kluczy i pilotaż (F009) wymaga osobnej decyzji właściciela.

## NOW

- 🔴 PLANNED — F005-validation-baseline: zamrożony protokół walidacji i wynik obecnych strategii; po F004.
- Uzgodnione: kapitał portfela 500 USD, stawka 100 USD, max DD 50%, cel 100% dni dodatnich z tolerancją, zakres 5 min–4 h; otwarte: dźwignia i szczegóły operacyjne.

## NEXT
- 🔴 F010-search-performance: profilowanie/benchmark metod wyszukiwania parametrów; po F005, przed F006.
- 🔴 F006-strategy-research: porównanie hipotez i wybór finalistów na danych rozwojowych; po F005 i F010.
- 🔴 F007-portfolio-holdout: wspólny kapitał i jednorazowy końcowy test zamrożonego kandydata; po F006.
- 🔴 F009-live-pilot: pilotaż z monitoringiem i planem wycofania po decyzji właściciela; po F007.

## PROVEN

- 2026-09 — F001-current-state-map: kontrakt sygnału/wejścia/wyjścia/ryzyka i 16 rozbieżności symulacja/live spisane w `spec/research/F001-current-state.md` (12 potwierdzonych z tej listy, 4 nowe). Który plik configu jest live nieustalone statycznie; właścicielka potwierdziła, że to nieistotne (nikt nie pracuje na produkcji) — nie dociągać.
- 2026-09 — F002-offline-boundary: `backtest_apex.py --local-csv` uruchamia backtest bez sieci (test blokuje `requests.get/post`); brak danych/wyników kończy proces kodem 1 zamiast dawnego `sys.exit(0)`. Potwierdzony brak importu `trader.py`/`rest_logs.py` w ścieżce backtestu. Dowód: `spec/research/F002-offline-boundary.md`.
- 2026-09 — F003-data-contract: `data_contract.py` — tylko zamknięte świece, wykrywanie luk, warm-up, manifest z checksumą+coverage%, `enforce_no_silent_gaps` blokuje ciche zerowanie, cache per symbol/interwał/zakres UTC z weryfikacją checksumy. Dowód: `spec/research/F003-data-contract.md`.
- 2026-09 — F004-execution-equity: `backtest_apex.py`'s domyślna ścieżka (bez `--param-optimization`) liczy przez nowy silnik `backtest_engine.py` (`costs.py`+`equity.py`+`execution.py`+`data_contract.py`) zamiast bezkosztowego `_make_trade`. Dyskryminujący test: PnL apex ściśle niższe niż stary silnik, różnica dokładnie równa sumie kosztów. Optuna (`--param-optimization`) wciąż na starym silniku — udokumentowana luka, nie cicho pominięta. 63 testy. Dowód: `spec/research/F004-execution-equity.md`.
- Brak strategii potwierdzonej w tym procesie.

## Decyzje i granice pracy

- Stawka 100 USD/wejście, przed dźwignią (nominał = 100 × leverage), bez automatycznej kapitalizacji. Kapitał portfela 500 USD (initial_equity = 500), wspólny dla wszystkich strategii/symboli.
- Max DD 50% liczone od bieżącego historycznego szczytu equity (przy 500 USD granica = 250 USD), z kosztami i otwartymi pozycjami — twarde kryterium odrzucenia, nie cel do wykorzystania.
- Cel: dodatni wynik netto każdego dnia miesiąca; dokładny kontrakt tolerancji w sekcji „Cel regularności i tolerancja" poniżej.
- interwały 5 min–4 h.
- Definicja dnia: zmiana equity między końcami dni (zrealizowany + niezrealizowany PnL, opłaty, funding), strefa Europe/Warsaw. Dni zerowe liczą się jako dni bez zysku; mianownik to wszystkie dni kalendarzowe pełnego miesiąca. Niepełne miesiące pokazywać osobno.
- Strojenie dźwigni oddzielić od strojenia sygnału; większy lewar nie liczy się jako poprawa przewagi.
- Startowy koszyk: SOLUSDT, ETHUSDT i mały koszyk wg historycznej płynności — bez doboru monet po uzyskanym PnL.
- Do ustalenia: limit straty dziennej, ryzyko/transakcja, max ekspozycja/liczba pozycji, dopuszczalny czas pozycji, trzymanie przez noc/weekend.
- Dozwolone: badania i testy offline. Wymaga osobnej zgody właściciela: uruchomienie produkcji, modyfikacja rachunku, przełączenie configu live, wysyłka do usług zewnętrznych.

## Dobór modelu i reasoning effort

- Zaczynać od najniższego sensownego poziomu reasoning effort, podnosić tylko gdy wynik jest niewystarczający — nie używać maksimum domyślnie. Cap: średni/wysoki, chyba że zadanie ma dużą niejednoznaczność lub wysoką cenę błędu.
- Niski effort: zmiany nazw, commit messages, oczywiste bugfixy, plumbing danych, uruchomienie gotowego backtestu. Wyższy effort: projekt equity/realizacji (F004), hipotezy strategii (F006), wybór optymalizatora (F010), przyczynowość sygnału Lorentzian.
- Nie zmieniać poziomu w połowie zadania (unieważnia cache promptu). Coordinator dobiera effort osobno dla każdego Workera w danej fali, nie jeden poziom na cały feature.
- Coordinator ma do dyspozycji dwa backendy modeli, uruchamiane komendą `pi` (dokumentacja: pi.dev):
  1. **Anthropic Claude** przez pi-claude-bridge: `pi --model claude-bridge/<nazwa-modelu>`, np. `pi --model claude-bridge/claude-sonnet-5` — `<nazwa-modelu>` podmieniać na faktycznie potrzebny (np. `claude-opus-5`, `claude-haiku-4-5`, `claude-fable-5-1`).
  2. **ChatGPT/Codex**: `pi --provider openai-codex --model <nazwa-modelu> --thinking <poziom>`, np. `pi --provider openai-codex --model gpt-6-astra --thinking xhigh` — `<nazwa-modelu>` i `<poziom>` podmieniać wg potrzeby zadania.
- Poziom myślenia dla claude-bridge: ogólny mechanizm resolvera modeli w pi obsługuje sufiks `:poziom` po nazwie modelu (`model:thinkingLevel`), więc dla Claude powinno działać `pi --model claude-bridge/claude-sonnet-5:high` (dozwolone poziomy: off/minimal/low/medium/high/xhigh/max).
- Jeśli backend zatrzyma pracę z powodu limitu tokenów/rate limitu, Worker/Coordinator ma odczytać z treści błędu czas, kiedy limit się resetuje, poczekać do tego momentu i wznowić przerwane zadanie — nie kończyć zadania jako porażkę ani nie zgłaszać braku wyniku tylko z powodu chwilowego limitu.


## Cel regularności i tolerancja

- TARGET_POSITIVE_DAY_PCT = 100 (dzień dodatni = PnL netto > 0). DAILY_NONPROFIT_TOLERANCE_PCT = 20, czyli min. 80% dni dodatnich w pełnym miesiącu — to tolerancja częstości, nie dopuszczalna strata dzienna.
- Wzór: N = dni kalendarzowe miesiąca; positive_day_pct = 100 × N_plus/N; deviation_pct = 100 × (N_minus + N_zero)/N. Cel spełniony, gdy deviation_pct ≤ 20 (np. min. 24/30 lub 25/31 dni dodatnich). Brakujące dane unieważniają ocenę miesiąca, nie liczą się jako zero.
- Kryteria promocji: dodatni PnL netto w każdym ocenianym miesiącu i w całym okresie, DD ≤ 50%, spełniona tolerancja miesięczna, wiarygodne dane/koszty. Raportować każdy miesiąc osobno (bez maskowania średnią) — najgorszy miesiąc, najgorszy dzień, najdłuższą serię strat.
- Nie wymuszać transakcji, nie zwiększać stawki po stracie, nie odkładać realizacji strat dla poprawy statystyki. Nie zmieniać tolerancji/strefy/definicji zysku/koszyka po zobaczeniu holdoutu, żeby uzyskać PASS.
- Brak przewagi jest dopuszczalnym wynikiem badania — wymaga pokazania najlepszego przybliżenia celu i propozycji kolejnego eksperymentu, nie tylko stwierdzenia że cel jest nierealny.

## Zachowanie rynku i samodzielne badania

- Cel 100% dni dodatnich z tolerancją 20% to miara wyniku, nie polecenie handlu każdego dnia. Brak pozycji przy braku przewagi jest poprawną decyzją; raportować taką rozbieżność, nie wymuszać wejść.
- Coordinator samodzielnie dobiera eksperymenty, przeszukuje internet, tworzy generatory sygnałów/filtry/reguły adaptacji i odrzuca nieskuteczne pomysły w ramach budżetu — bez pytania o rutynowy eksperyment offline. Zmiana celu, tolerancji, kapitału, limitów ryzyka lub wdrożenia live to decyzja właścicielki.
- Pętla badawcza: obserwacja → hipoteza i przewidywany efekt → najprostszy eksperyment → wynik na train/validation → wniosek i kolejny krok. Wynik negatywny aktualizuje hipotezę, nie uzasadnia ukrywania strat.
- Warunki rynku (trend/zmienność/płynność/pora dnia) rozpoznawać wyłącznie z danych dostępnych w chwili decyzji — etykiety post-factum tylko do diagnostyki. Sprawdzać powtarzalność obserwacji poza okresem jej odkrycia.
- Adaptacja/przełączanie musi mieć zapisane przed walidacją progi i częstotliwość, porównanie z wariantem bez adaptacji, test ablacyjny i koszt przełączeń; zakaz zmiany strategii po pojedynczej stracie, martingale i zwiększania dźwigni na odrobienie straty.
- Internet: preferować dokumentację/kod źródłowy/publikacje, zapisywać źródło i datę; traktować jako hipotezy do niezależnego testu. Notatki badawcze w spec/research/: obserwacja, hipoteza, źródła, warunek obalenia, run_id, wynik, decyzja. Finalny holdout nigdy nie służy do wymyślania kolejnych poprawek.


## Lokalne wyniki i Apex

- Wysyłka badań do Apex zawieszona; wyniki tylko lokalnie na dysku (Markdown/CSV/JSON), czytelne dla Coordinatora i człowieka. backtest_apex.py zapisuje run w output/backtests/<run_id>/: report.json, trades.csv, candidate.yaml — bez importu funkcji wysyłających do Apex.
- Obecny eksport to surowy baseline: brak jeszcze dziennego equity i tolerancji miesięcznej. W F002–F005 dodać equity.csv, daily.csv, monthly.csv, manifest danych i rejestr prób.
- Nie przywracać eksportu Apex automatycznie — ewentualny przyszły eksport dla człowieka to osobna, jawna operacja.

## Ustalenia z kodu — punkt startowy

| Obszar | Co istnieje | Znaczenie dla planu |
| --- | --- | --- |
| main.py | WebSocket zamkniętych świec, kolejka, TraderBot, okresowe update_tsl | Istniejąca pętla live; zachować i opisać |
| trader.py | Zlecenia limit/aggressive_limit/market, fallback, SL, bot-managed TSL, cooldown, circuit breaker | Import inicjalizuje połączenie produkcyjne; nie importować w audycie offline |
| strategy.py | 79 wariantów sygnałów, wskaźniki, OHLCV, backtest_trailing | Baza do testów zgodności, ale łączy obliczenia z configiem i logowaniem |
| backtest_apex.py | Ranking, Optuna, lokalny eksport raportu/transakcji/YAML | Brak rozdzielenia okresu strojenia i niezależnej oceny |
| run_backtest_apex.py | Wiele symboli/interwałów, instrumenty starsze niż rok | Ryzyko survivorship bias; różne okresy danych na różnych interwałach |
| configuration/, configuration prod/ | Różne strategie, stawki, dźwignie, SL, ENTRY_ON_OPEN | Nazwa folderu nie dowodzi wdrożenia na produkcji |
| rest_logs.py, logger_config.py | Zewnętrzne raportowanie/logowanie Apex | Lokalny eksperyment musi działać bez tych zapisów |

Potwierdzone ograniczenia backtestu: brak prowizji/spreadu/poślizgu/fundingu w `_make_trade`; `_compute_metrics` pomija equity początkowe w szeregu szczytów i niezrealizowane obsunięcia; `calmar` to total_pnl/max_dd_usd bez annualizacji; SL jest procentowy mimo opisów ATR-based (ATR zakomentowany); brak jawnego odrzucenia bieżącej niezamkniętej świecy; Bar Magnifier nie ma dowodu poprawnej kolejności zdarzeń w subświecy; live używa MarkPrice, backtest OHLC — rozbieżność źródła ceny; brak modelu wspólnego kapitału/margin/likwidacji; Optuna stroi i ocenia na tym samym df (błąd `suggest_int(4, 3)` dla max_leverage=3); `BACKTEST_MAX_DD_LIMIT`/`BACKTEST_WORST_LOSS_LIMIT` z YAML nieużywane; interwał 5 min odrzucany (brak wpisu w `_SUB_INTERVAL_MAP`); puste wyniki/błędy mogą kończyć się kodem 0. To punkty audytu w F002–F004, nie dowód awarii produkcji.

## Zakres i dowód zakończenia etapów

### F001 — Mapa obecnego zachowania i kontrakt live

- Opisać pętlę main.py, logikę wejść/wyjść/SL/TSL (trader.py, strategy.py) i różnice symulacja/live; zidentyfikować realne pliki YAML na produkcji.
- Dowód: kontrakt sygnału/wejścia/wyjścia/ryzyka i lista rozbieżności w spec/. Bez zmian w konfiguracji i bez zleceń.

### F002 — Badania offline

- Oddzielić import obliczeń od klienta produkcyjnego/CLI/logowania zewnętrznego; rozwinąć lokalny eksport do pełnego raportu badania.
- Dowód: backtest na fixture działa bez sieci i bez kluczy API; błędy i brak wyniku rozróżnione od sukcesu.

### F003 — Dane i instrumenty

- Jawne start/end UTC, cache i manifest danych, tylko zamknięte świece, kontrola luk i warm-up; zdefiniować dobór instrumentów i pokrycie danych; nie zastępować brakujących kosztów zerami bez oznaczenia.
- Dowód: manifest z checksumami i raportem jakości; brak wymaganych danych wyklucza wynik z rankingu.

### F004 — Realistyczna symulacja i equity

- Spójny zegar (sygnał po zamknięciu świecy → najwcześniejsze wykonanie); rozdzielić cenę triggera od wykonania; uwzględnić prowizje/spread/poślizg/funding/partial fill.
- Rozdzielić initial_equity = 500 USD, stawkę 100 USD, margin, notional i ryzyko; księgować equity z otwartymi pozycjami; blokować pozycje przy braku środków.
- Dowód: ręcznie policzone scenariusze (long/short, pierwsza strata, funding, gap, TSL w barze, koniec okresu) + testy regresji sygnałów i ryzyka.

### F005 — Protokół i baseline

- Przed rankingiem zapisać train/validation/final holdout, koszyk, hipotezy, limity prób i kryteria odrzucenia — holdout nie uczestniczy w doborze.
- Propozycja: kroczące 12 mies. treningu / 3 mies. walidacji, min. 4 okna walidacyjne, ostatnie 6 mies. jako holdout (krótsza historia = jawne ograniczenie wniosków).
- Dowód: odtwarzalny raport baseline i zamrożony protokół (stawka, DD, cel, tolerancja, initial_equity, budżet poszukiwania).

### F010 — Wydajność i wybór metody optymalizacji

- Optuna nie jest wymaganiem architektonicznym — zmienić sampler/silnik/narzędzie, jeśli pomiary uzasadnią. Najpierw profilować osobno dane/sygnały/symulację/metryki/sampler; brak jeszcze dowodu, że TPE jest wąskim gardłem.
- Dwa osobne eksperymenty: (A) przyspieszenie tego samego backtestu (cache, wektoryzacja, Numba/njit, równoległość) bez zmiany wyniku; (B) lepsze parametry przy tym samym czasie (TPE vs Random Search/Sobol, ew. GP/CMA-ES/DE) — porównanie na tym samym sprzęcie/danych/seedach.
- Trwały rejestr prób i cache ocen (klucz: kod+dane+parametry+seed); pruning/Hyperband dopiero po wiarygodnych ocenach pośrednich, finaliści zawsze pełna ocena.
- Dowód: benchmark.csv, test zgodności przyspieszonego silnika, decyzja o domyślnej metodzie (z uzasadnieniem, nawet jeśli to „bez zmian").

### F006 — Poszukiwanie strategii

- Każda iteracja wg sekcji „Zachowanie rynku…": diagnoza baseline → hipoteza → eksperyment → wniosek. Priorytet: Lorentzian Classification z advanced-ta (0.1.8) — odtworzyć wariant referencyjny z dokumentacji, dodać adapter do wspólnego silnika (jawne mapowanie sygnałów, osobno generator vs. useDynamicExits).
- Przed rankingiem zbadać przyczynowość (sygnał z prefiksu danych vs. wsadowo na tej samej świecy, warm-up, maxBarsBack, filtry kernel/regime/volatility). Stroić tylko cechy RSI/WT/CCI/ADX/neighborsCount na train; porównać z domyślnym i prostymi strategiami przy kapitale 500 USD/stawce 100 USD.
- Równolegle: rodziny EMA/RSI/MACD/ADX, BB breakout/squeeze, RSI/BB mean reversion, potem Donchian/pullback/filtr reżimu — każda z uzasadnieniem i limitem prób. Porównać 5m–4h, long/short i brak pozycji; optymalizacja tylko na train, walidacja do wyboru finalistów.
- Dowód: porównanie netto OOS, wynik per okno/miesiąc, ranking odległości od celu, krótka lista lub odrzucenie wszystkich z najlepszym przybliżeniem. Dla >1 finalisty: wstępne uzasadnienie kombinacji (dywersyfikacja instrumentów/interwałów/warunków) jako hipoteza do F007.

### F007 — Portfel i finalny holdout

- Wspólna oś czasu/kapitał z limitami margin/ekspozycji/korelacji. Dla >1 strategii: zakodowana reguła doboru/alokacji (stały podział albo przełączanie wg warunków rynku) — traktowana jak osobna hipoteza (progi zapisane przed walidacją, porównanie z wariantem statycznym i najlepszą pojedynczą strategią, koszt przełączeń); żadna ręczna decyzja.
- Zamrozić strategię(-e), regułę doboru, parametry, instrumenty, sizing — dopiero wtedy otworzyć holdout.
- Dowód: dodatni PnL netto, DD ≤ 50%, spełniona tolerancja miesięczna, poprawa wobec baseline i wobec najlepszej pojedynczej strategii. Porażka nie uprawnia do dostrojenia tego samego holdoutu.

### F009 — Pilotaż live

- Po decyzji właściciela: mały budżet, limity, kryteria stop/rollback. Porównać faktyczne fille/prowizje/funding/PnL z modelem; kontrolować łączną ekspozycję konta.
- Dowód: raport wykonania i ryzyka + decyzja utrzymać/wycofać/skalować (nieautomatyczna).

## Standard raportu eksperymentu

- run_id, commit, konfiguracja, seed, wersje zależności, manifest danych, daty UTC, instrumenty, etykiety train/validation/holdout.
- Transakcje i equity w czasie; PnL netto, max DD z otwartymi pozycjami, profit factor, expectancy, liczba transakcji.
- Miesięcznie: dni dodatnie/ujemne/zerowe, positive_day_pct, deviation_pct, spełnienie tolerancji. Wyniki per okno/symbol/kierunek/reżim, wrażliwość parametrów i kosztów.
- Decyzja: odrzucony / wymaga więcej danych / kandydat do następnego etapu — z powodem i ograniczeniami.



## Źródła techniczne

- [dobór reasoning effort](https://mega.dev/reasoning-effort) — sprawdzono 2026-09-21.
- [advanced-ta — Lorentzian Classification](https://pypi.org/project/advanced-ta/) — sprawdzono 2026-09-21.
- Narzędzie `pi` (uruchamiane pod Limen): [pi.dev — providers](https://pi.dev/docs/latest/providers), [pi.dev — settings](https://pi.dev/docs/latest/settings), [pi-claude-bridge — README](https://github.com/elidickinson/pi-claude-bridge/blob/main/README.md) (poziomy thinking: off/minimal/low/medium/high/xhigh), [pi-subagents — spawnowanie workerów z innym modelem](https://github.com/tintinweb/pi-subagents) — sprawdzono 2026-09-21.
- [Bybit OHLCV](https://bybit-exchange.github.io/docs/v5/market/kline), [Bybit funding history](https://bybit-exchange.github.io/docs/v5/market/history-fund-rate).
- Optymalizacja (do F010): [Optuna — pruning](https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/003_efficient_optimization_algorithms.html), [Optuna QMCSampler](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.QMCSampler.html), [SciPy Differential Evolution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html), [Numba jit](https://numba.readthedocs.io/en/stable/user/jit.html).
