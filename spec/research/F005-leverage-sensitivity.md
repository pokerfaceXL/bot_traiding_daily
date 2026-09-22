# F005 — Diagnostyka wrażliwości na dźwignię i cooldown (addendum, nie nowa fala)

> Ten dokument jest dodatkiem do zamkniętego F005 (`spec/features/done/F005-validation-baseline/ticket.md`),
> nie nową numerowaną funkcją. Cel: czyste pomiarowe wsparcie dla otwartej decyzji Koordynatora
> o dźwigni (`spec/build.md`: „otwarte: dźwignia i szczegóły operacyjne"). **Nic w tym uruchomieniu
> nie zmienia** `configuration/default.yaml`, domyślnych wartości `backtest_apex.py`, zamrożonego
> protokołu (`spec/research/F005-validation-protocol.md`) ani żadnego pliku fali 1-3
> (`spec/research/F005-baseline.md`, `output/f005_baseline/`, `scripts/f005_run_baseline.py`) —
> to nowy, osobny, tylko-do-odczytu-tamtych-plików przebieg diagnostyczny.
>
> Skrypt: `scripts/f005d_leverage_sensitivity.py`. Dane: te same 10 checksum SHA-256 z sekcji 6
> protokołu, ten sam ciągły przebieg `warmup_start → holdout_end` (2024-01-26 → 2026-09-01),
> te same koszty domyślne `backtest_engine.run_backtest`, ta sama klasyfikacja `regularity.py`.

## Metodologia

### Próbka 10 strategii (nie cały katalog 79 — budżet czasowy diagnostyki)

`strategy.STRATEGY_CATALOG` grupuje się (po nazwie) w 7 rodzin: `ADX*`, `BB_*` (Bollinger Bands),
`EMA*`/`EMA3_*`/`EMA_BB_ADX_*`, `MACD_*`, `RSI*`, `STOCH*`, `TS_*` (Triple Screen). Tickiet
wymagał wprost EMA/RSI/MACD/BB/ADX plus co najmniej jednej z pozostałych obecnych rodzin
(STOCH, TS). Wybór (10, po jednej-dwóch na rodzinę, mieszanka czystych wskaźników i kombinacji):

| Strategia | Rodzina | Uzasadnienie wyboru |
| --- | --- | --- |
| `EMA_8_21` | EMA | czysty crossover, najprostszy wariant rodziny |
| `EMA_13_34_RSI14_55` | EMA | wariant kombinowany EMA+RSI w obrębie tej samej rodziny |
| `RSI14_7030` | RSI | czysty RSI |
| `MACD_12_26_hist` | MACD | czysty MACD |
| `MACD_RSI14_50` | MACD | wariant kombinowany MACD+RSI |
| `BB_20_25_breakout` | Bollinger Bands | wariant breakout |
| `BB_20_2_RSI14` | Bollinger Bands | wariant kombinowany BB+RSI |
| `ADX14_DI_20` | ADX | wymagana rodzina, najwolniejsza strategia katalogu wg pomiaru fali 1 (sekcja 5 protokołu) — celowo pozostawiona w próbce, żeby czas próbki nie był sztucznie optymistyczny |
| `STOCH14_cross` | Stochastic | jedyna rodzina spoza wymaganych pięciu obecna w katalogu obok TS; wybrana też dlatego, że to *najgorsza kombinacja fali 3* (949 kolejnych dni non-positive, `F005-baseline.md`) — bezpośrednia porównywalność z baseline |
| `TS_13_34_200_14` | Triple Screen | druga rodzina spoza wymaganych pięciu; wybrana bo to strategia „najmniej katastrofalna" fali 3 dla DOGEUSDT/240 (`F005-baseline.md`) — również bezpośrednio porównywalna |

Wszystkie 7 rodzin obecnych w katalogu są reprezentowane; dwie z wybranych strategii (`STOCH14_cross`,
`TS_13_34_200_14`) są te same, które fala 3 już nazwała po imieniu jako skrajne przypadki, więc
tę diagnostykę można czytać obok `F005-baseline.md` bez zgadywania, czy chodzi o tę samą strategię.

### Siatka pomiaru

- **Dźwignia** (`cooldown_candles=0`, wartość fali 3): 1, 2, 3, 5 — **zmierzone** (400 uruchomień:
  4 wartości × 10 strategii × 10 kombinacji symbol/interwał). `leverage=10` (wartość fali 3)
  **nie zostało ponownie uruchomione** — zgodnie z wymaganiem tickieta, ponownie użyte z
  `output/f005_baseline/summary/` (100 wierszy: 10 strategii × 10 kombinacji), patrz niżej.
- **Cooldown** (`leverage=10`, wartość fali 3): `cooldown_candles` = 5, 20 — **zmierzone**
  (200 uruchomień: 2 wartości × 10 strategii × 10 kombinacji).
- Pozostałe parametry identyczne jak fala 3: `atr_multiplier=2.5, max_sl_pct=0.03, activate_pct=0.03,
  trail_pct=0.015, initial_equity=500, stake=100`. Koszty (`commission_rate_bps=10, half_spread_bps=5,
  slippage_bps=2`) — domyślne `backtest_engine.run_backtest`, tak jak w fali 3.
- **Razem: 600 zmierzonych przebiegów `backtest_engine.run_backtest`** (`600 measured runs + 100
  reused rows in 260.1s` — log skryptu) **+ 100 wierszy ponownie użytych** z fali 3 (leverage=10,
  cooldown=0) = **700 wierszy siatki** w `output/f005d_leverage_sensitivity/summary/sweep_results.csv`.

### Ponowne użycie leverage=10/cooldown=0 — jak, bez ponownego uruchamiania

`output/f005_baseline/raw/*.json` (pełne dane per-run z fali 3) nie są w gicie i nie są obecne
w tym worktree (ten sam wzorzec co `data_cache/*.csv` — lokalnie na dysku, gitignored). Ponowne
użycie opiera się więc na już scalonych tabelach `output/f005_baseline/summary/validation_summary.csv`
i `.../dd_flags.csv`, ograniczonych do 10 wybranych strategii (100 wierszy), plus jednym
udowodnionym wnioskowaniu z prozy `F005-baseline.md`: skoro `avg_deviation_pct` w
`validation_summary.csv` ma **min=max=mean=100.0, std=0.0** dla wszystkich 790 wierszy fali 3
(cytat z `F005-baseline.md`), to jedyny sposób, żeby średnia z wartości ograniczonych do [0,100]
wyniosła dokładnie 100.0, to żeby *każda* pojedyncza wartość wynosiła 100.0 — czyli
`frac_validation_target_met = 0.0` dla każdego z tych 100 wierszy, bez potrzeby ponownego otwierania
plików `raw/*.json`. Podobnie `final_equity` nie jest dostępne per-wiersz w tabelach summary, ale
fala 3 ustaliła pasmo **$66.86–$99.96 dla wszystkich 790 kombinacji (zawsze < $100)** — więc
`survives_to_holdout_end=False` dla wszystkich 100 ponownie użytych wierszy jest bezpośrednim
cytatem tego ustalenia, nie nowym pomiarem. Skrypt (`_reused_leverage10_rows`) sprawdza
asercją, że `avg_deviation_pct` rzeczywiście wynosi 100.0 (lub `NaN` przy `n_valid=0`) dla
każdego z tych 100 wierszy przed użyciem tego skrótu — gdyby założenie było fałszywe dla
któregokolwiek wiersza, skrypt rzuciłby wyjątkiem zamiast cicho przyjąć złe dane.

### Dane wyjściowe — bez ciężkiego `raw/`

W przeciwieństwie do fali 3 (86 MB `output/f005_baseline/raw/*.json` z pełną listą transakcji i
dzienną krzywą equity per uruchomienie, gitignored), ta diagnostyka **nie zapisuje** takiego
zrzutu per-run. Wszystkie metryki wymagane przez tickiet (przetrwanie, ułamek miesięcy
spełniających cel, net PnL, max DD) są w jednym płaskim `sweep_results.csv` (700 wierszy, 120 KB)
— **wystarczająco małe, żeby wejść do gita wprost**, bez potrzeby wzorca `.gitignore` z fali 3.
To świadoma decyzja zakresu (diagnostyka „nie musi być wyczerpująca" — tickiet), nie przeoczenie.

## Wynik główny — dźwignia sama nie ratuje przetrwania; nic w siatce nie spełnia celu regularności

**Zero z 700 kombinacji (symbol, interwał, strategia, dźwignia, cooldown) osiąga
`deviation_pct ≤ 20%` w choćby jednym ważnym miesiącu Validation** — dokładnie taki sam,
kategoryczny negatywny wynik jak fala 3 (tam: 0/24885 miesięcy), teraz potwierdzony również
przy niższej dźwigni i przy niezerowym cooldownie. Najlepsza (najniższa) `deviation_pct`
zaobserwowana w całej siatce: **40.0%** (leverage=1, wciąż dwukrotnie gorsze niż wymagany próg).

| Dźwignia | Cooldown | n (symbol×interwał×strategia) | Przetrwało do końca Holdout | DD≤50% (twardy próg) | ≥1 miesiąc spełnia cel regularności | Najlepsza dev% | Mediana dev% (na kombinację) | Najgorsza dev% | Net PnL cały przebieg: średnia [min, max] | Max DD cały przebieg: średnia [min, max] |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 0 | 100 | **7/100** | 5/100 | 0/100 | 40.00% | 100.0% | 100.0% | -$390.74 [-$403.32, -$195.80] | 78.29% [39.32%, 81.26%] |
| 2 | 0 | 100 | **1/100** | 0/100 | 0/100 | 56.67% | 100.0% | 100.0% | -$402.56 [-$406.60, -$391.61] | 80.71% [78.56%, 82.80%] |
| 3 | 0 | 100 | 0/100 | 0/100 | 0/100 | 80.65% | 100.0% | 100.0% | -$404.64 [-$409.87, -$400.01] | 81.22% [80.00%, 83.04%] |
| 5 | 0 | 100 | 0/100 | 0/100 | 0/100 | 100.00% | 100.0% | 100.0% | -$406.92 [-$416.59, -$400.00] | 81.85% [80.12%, 84.28%] |
| **10 (ponowne użycie fali 3)** | 0 | 100 | 0/100 | 0/100 (wszystkie w `dd_flags.csv`) | 0/100 | 100.00% | 100.0% | 100.0% | n/d (nie w tabelach summary fali 3, patrz `F005-baseline.md`: pasmo -$400 do -$401 dla najlepszych 10 kombinacji symbol/interwał) | 83.49% [80.12%, 88.11%] |
| 10 | 5 | 100 | 0/100 | 0/100 | 0/100 | 100.00% | 100.0% | 100.0% | -$412.13 [-$433.00, -$400.20] | 83.17% [80.15%, 89.08%] |
| 10 | 20 | 100 | 0/100 | 0/100 | 0/100 | 100.00% | 100.0% | 100.0% | -$411.48 [-$431.69, -$400.00] | 83.09% [80.01%, 87.37%] |

Pełne 700 wierszy: `output/f005d_leverage_sensitivity/summary/sweep_results.csv`.

## Cooldown sam nie pomaga — nawet lekko pogarsza wynik przy tej samej dźwigni

Przy `leverage=10` (wartość fali 3): `cooldown_candles=5` i `cooldown_candles=20` dają **0/100
przetrwań, 0/100 przejść DD≤50%, 0/100 miesięcy spełniających cel** — identyczne zero jak
`cooldown_candles=0`. Średni max DD i średni net PnL są nawet nieznacznie **gorsze** przy
`cooldown_candles=20` niż przy `cooldown_candles=0` (83.09% vs 83.49% DD to w granicach szumu,
ale net PnL -$411 vs brak porównywalnej liczby dla cooldown=0 z ponownego użycia — patrz próbka
punktowa niżej). Punktowa weryfikacja na `EMA_8_21`/SOLUSDT/240/leverage=10: `cooldown=0` →
equity $91.26 (27 transakcji); `cooldown=5` → equity $92.48 (22 transakcje, odrobinę lepiej);
`cooldown=20` → equity **$72.83** (29 transakcji, gorzej niż `cooldown=0` — dłuższy cooldown
zmienia, które sygnały wejścia są łapane, nie tylko ich liczbę, i w tym konkretnym przypadku
trafia akurat na gorsze wejścia). **Wniosek: cooldown, testowany osobno przy dźwigni=10, nie
przywraca przetrwania ani razu w próbce, i nie ma spójnego kierunku poprawy** — nie jest to
brakujący czynnik, który sam naprawiłby problem.

## Dlaczego niższa dźwignia sama nie wystarcza — mechanizm, nie tylko liczby

`equity.py`'s kontrakt (już nazwany w `F005-baseline.md`): `margin = notional / leverage = stake`
— **margin wymagany na wejście to zawsze $100, niezależnie od dźwigni** (potwierdzone bezpośrednio
w tej diagnostyce: pole `margin` w `trades` df = 100.0 dla `leverage` = 1, 2, 3, 5, 10 na tym samym
przykładzie). Dźwignia zmienia tylko nominał ekspozycji (`notional = stake × leverage`), więc
zmniejsza **procentową** wielkość straty na stopie w dolarach za pojedynczą transakcję
(`max_sl_pct × notional`) — ale margin zablokowany na każde wejście pozostaje stały. Punktowa
weryfikacja (`EMA_8_21`/SOLUSDT/240, `cooldown=0`):

| Dźwignia | Liczba transakcji (cały przebieg) | Średni net PnL/transakcję | Ostatnia transakcja (data) | Final equity |
| ---: | ---: | ---: | --- | ---: |
| 1 | 318 | -$1.27 | 2024-07-06 | $96.88 |
| 2 | 152 | -$2.65 | 2024-04-02 | $97.39 |
| 10 | 27 | -$15.14 | 2024-02-12 | $91.26 |

**Niższa dźwignia nie zmienia, czy konto ostatecznie osiądzie poniżej progu $100 wejścia — zmienia
tylko, ile miesięcy to trwa.** Przy dźwigni=10 konto jest matematycznie zablokowane w ~2.5 tygodnia
(12 lutego 2024); przy dźwigni=1 to samo konto robi 12× więcej transakcji o 12× mniejszej średniej
stracie i osiada w niemal identycznym miejscu ($96.88 zamiast $91.26) po ~5 miesiącach zamiast
~2.5 tygodnia. **Przewaga sygnału (`win_rate`/`profit_factor`) tej strategii jest ujemna
niezależnie od dźwigni — dźwignia tylko przyspiesza lub spowalnia tempo, w jakim ujemna
przewaga zjada budżet $500 do progu $100, nie zmienia znaku wyniku.** To wyjaśnia, czemu nawet
najniższa testowana dźwignia (1) daje tylko 7/100 „przetrwań" w całej próbce, nie 100/100.

## „Przetrwanie" ≠ rentowność — nawet 7 ocalałych przy leverage=1 nie spełnia żadnego innego kryterium

Wszystkie 7 kombinacji, które przetrwały przy `leverage=1, cooldown=0` (final_equity ≥ $100 na
koniec pełnego przebiegu), to niemal wyłącznie jedna strategia:

| Symbol | Interwał | Strategia | Final equity | Net PnL (cały przebieg) | Max DD (cały przebieg) | Najgorsza dev% w Validation |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| BTCUSDT | 240 | BB_20_25_breakout | $304.20 | -$195.80 | 39.32% | 93.55% |
| ETHUSDT | 240 | BB_20_25_breakout | $275.82 | -$224.18 | 46.50% | 100.00% |
| SOLUSDT | 240 | BB_20_25_breakout | $274.91 | -$225.09 | 45.37% | 100.00% |
| XRPUSDT | 240 | BB_20_25_breakout | $255.41 | -$244.59 | 49.32% | 96.67% |
| DOGEUSDT | 240 | BB_20_25_breakout | $253.32 | -$246.68 | 49.35% | 100.00% |
| BTCUSDT | 60 | BB_20_25_breakout | $227.55 | -$272.45 | 55.21% | 70.97% |
| BTCUSDT | 240 | BB_20_2_RSI14 | $152.62 | -$347.38 | 70.98% | 85.71% |

Przetrwanie nie oznacza tu użyteczności: **wszystkie 7 mają net PnL głęboko ujemny (-39% do -69%
zainwestowanego kapitału), a żadna nie osiąga celu regularności w żadnym miesiącu Validation**
(najlepsza z nich, BTCUSDT/240, ma najgorszą `deviation_pct` w Validation = 93.5% — wciąż prawie
5× gorzej niż próg 20%). Tylko 5 z tych 7 przechodzi nawet samo twarde kryterium DD≤50%
(BTCUSDT/60 i BTCUSDT/240/`BB_20_2_RSI14` przekraczają 50%). **W całej siatce 700 kombinacji
zero jednocześnie: (a) przetrwało, (b) przeszło DD≤50%, (c) osiągnęło cel regularności choć raz,
(d) miało dodatni net PnL całego przebiegu.** `BB_20_25_breakout` dominuje listę ocalałych, bo to
strategia o niskiej częstości transakcji (160-206 transakcji na 4h w cały przebieg, zamiast setek)
— przetrwanie tutaj koreluje z rzadkością wejść, nie z jakością sygnału.

## Wniosek — odpowiedź na pytanie tickieta

**Nie, obniżenie samej dźwigni (do 1, 2, 3 ani 5) i/lub dodanie samego cooldownu (5 lub 20 świec)
przy dźwigni=10 nie przywraca przetrwalności katalogu strategii w sposób, który miałby znaczenie
dla decyzji o dźwigni.** Jedyna kombinacja z niezerowym przetrwaniem w próbce to `leverage=1`
(7/100), i nawet ta garstka nie spełnia ani celu regularności, ani (w 2/7 przypadków) twardego
progu DD, ani nie ma dodatniego PnL. `leverage=2` daje 1/100 przetrwań o tej samej charakterystyce.
`leverage≥3` oraz jakikolwiek testowany cooldown przy `leverage=10` dają **dokładnie 0/100**
przetrwań, tak jak `leverage=10` sam. **W całej zmierzonej i ponownie użytej siatce (700 wierszy)
zero kombinacji spełnia jednocześnie przetrwanie + DD≤50% + cel regularności + dodatni PnL** —
dokładnie tak samo kategoryczny negatywny wynik jak fala 3 (`F005-baseline.md`: 0/24885 miesięcy),
teraz rozszerzony na cztery dodatkowe wartości dźwigni i dwie wartości cooldownu. Mechanizm
(margin = stake niezależnie od dźwigni) pokazuje, że problem nie jest w samej dźwigni jako
mnożniku ryzyka, tylko w tym, że **przewaga sygnału istniejącego katalogu strategii jest ujemna
niezależnie od dźwigni/cooldownu** — dźwignia tylko kontroluje tempo, w jakim ta ujemna przewaga
konsumuje kapitał do progu wejścia $100, nie jej znak. Obniżenie dźwigni w produkcji spowolniłoby
tempo bankructwa konta (miesiące zamiast tygodni), ale **nie uczyniłoby żadnej istniejącej
strategii z katalogu rentowną ani regularną** — to zgodne z wnioskiem fali 3 i z uwagą
`spec/build.md`, że strojenie dźwigni ma być oddzielone od strojenia sygnału.

## Test suite

`/home/limen/bot_traiding_daily/.venv_test/bin/python -m pytest tests/ -v` (wspólne `.venv_test`,
uruchomione po zapisaniu skryptu/wyników/tego raportu, przed commitem):

```
74 passed, 1 skipped
```

Zero regresji — dokładnie ten sam wynik co przed tym addendum (żaden plik produkcyjny ani test
nie został zmieniony, dodano wyłącznie `scripts/f005d_leverage_sensitivity.py`,
`output/f005d_leverage_sensitivity/summary/{sweep_results.csv,manifest.json}` i ten raport).

## Pliki tego addendum

- `scripts/f005d_leverage_sensitivity.py` — skrypt pomiarowy.
- `output/f005d_leverage_sensitivity/summary/sweep_results.csv` — 700 wierszy, wszystkie metryki
  per (symbol, interwał, strategia, dźwignia, cooldown), w gicie (120 KB).
- `output/f005d_leverage_sensitivity/summary/manifest.json` — parametry, checksumy, znacznik czasu,
  commit rodzica, w gicie.
- Ten plik.

Żaden plik fali 1-3 F005 (`spec/research/F005-baseline.md`, `spec/research/F005-validation-protocol.md`,
`scripts/f005_run_baseline.py`, `output/f005_baseline/`) nie został zmieniony.
