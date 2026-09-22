# F005 — Zamrożony protokół walidacji (fala 1)

> Ten dokument jest zamrożony PRZED jakimkolwiek pomiarem baseline. Napisany po zakończeniu audytu realnej dostępności danych Bybit (sekcja 1), ale przed jakimkolwiek wywołaniem `backtest_engine.run_backtest` na realnych danych SOLUSDT/ETHUSDT/BTCUSDT/XRPUSDT/DOGEUSDT — żaden sygnał ani PnL na tych danych nie został policzony w tej fali. Jedyne wywołania `backtest_engine.run_backtest` w tej fali dotyczyły `tests/fixtures/ohlcv_sample.csv` (istniejący fixture testowy, sztucznie powielony do większego rozmiaru wyłącznie do pomiaru czasu wykonania — patrz sekcja 5), nigdy realnych danych rynkowych koszyka.
>
> Zgodnie z `spec/build.md`, „Cel regularności i tolerancja": *„Nie zmieniać tolerancji/strefy/definicji zysku/koszyka po zobaczeniu holdoutu, żeby uzyskać PASS."* Ten dokument jest tym zamrożonym punktem odniesienia — okna, koszyk, budżet i kryteria odrzucenia poniżej nie zmieniają się po zobaczeniu wyniku fali 2 (baseline).
>
> Data audytu: 2026-09-22. `strategy.py`/`main.py`/`trader.py`/`configuration/` nie zostały zmienione w tej fali.

## 1. Audyt realnej dostępności danych Bybit

Metoda: `strategy.get_bybit_ohlcv(symbol, interval, limit=200_000)` — limit celowo dużo większy niż jakakolwiek realna historia, żeby pętla pobierania sama zatrzymała się na początku listingu instrumentu (Bybit zwraca pustą listę, gdy nie ma więcej starszych świec). Każdy wynik przepuszczony przez `data_contract.build_dataset(...)` (F003) — manifest z checksumą SHA-256, wykrywaniem luk i `coverage_pct` (bez `allow_gaps` domyślnego ukrycia luk; audyt jawnie akceptuje istnienie/brak luk i raportuje liczbę). Skrypt: `scripts/f005_fetch_audit_data.py`. Surowy wynik: `data_cache/f005_audit_summary.json`.

Wynik (cała dostępna historia per symbol/interwał, do „teraz" = 2026-09-22):

| Symbol | Interwał | Najwcześniejsza świeca (UTC) | Najpóźniejsza świeca (UTC) | Miesięcy historii | Wiersze | Luki | Pokrycie |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SOLUSDT | 240 (4h) | 2021-10-15T00:00:00Z | 2026-09-22T00:00:00Z | 59.24 | 10819 | 0 | 100.00% |
| SOLUSDT | 60 (1h) | 2021-10-15T00:00:00Z | 2026-09-22T05:00:00Z | 59.24 | 43278 | 0 | 100.00% |
| ETHUSDT | 240 (4h) | 2021-03-15T00:00:00Z | 2026-09-22T00:00:00Z | 66.27 | 12103 | 0 | 100.00% |
| ETHUSDT | 60 (1h) | 2021-03-15T00:00:00Z | 2026-09-22T05:00:00Z | 66.27 | 48414 | 0 | 100.00% |
| BTCUSDT | 240 (4h) | 2020-03-25T08:00:00Z | 2026-09-22T00:00:00Z | 77.92 | 14231 | 0 | 100.00% |
| BTCUSDT | 60 (1h) | 2020-03-25T10:00:00Z | 2026-09-22T05:00:00Z | 77.92 | 56924 | 0 | 100.00% |
| XRPUSDT | 240 (4h) | 2021-05-13T08:00:00Z | 2026-09-22T00:00:00Z | 64.32 | 11747 | 0 | 100.00% |
| XRPUSDT | 60 (1h) | 2021-05-13T09:00:00Z | 2026-09-22T05:00:00Z | 64.32 | 46989 | 0 | 100.00% |
| DOGEUSDT | 240 (4h) | 2021-06-02T08:00:00Z | 2026-09-22T00:00:00Z | 63.66 | 11627 | 0 | 100.00% |
| DOGEUSDT | 60 (1h) | 2021-06-02T10:00:00Z | 2026-09-22T05:00:00Z | 63.66 | 46508 | 0 | 100.00% |

**Wniosek dla kształtu okien (sekcja 3)**: najkrótsza historia w koszyku to SOLUSDT — 59.24 miesiąca, ciągła, bez luk, przy 4h i 1h. To ponad dwukrotność wymaganych 30 miesięcy (12+4×3+6, z `spec/build.md`/tickieta). **Żaden symbol nie wymaga skrócenia domyślnego kształtu okien** — propozycja z build.md (kroczące 12mies./3mies., min. 4 okna walidacyjne, ostatnie 6mies. holdout) jest użyta bez modyfikacji, z jawnie udokumentowanym marginesem (patrz sekcja 3.3).

## 2. Koszyk instrumentów

Wymagane przez `spec/build.md` („Decyzje i granice pracy"): SOLUSDT, ETHUSDT + „mały koszyk wg historycznej płynności — bez doboru monet po uzyskanym PnL". SOLUSDT i ETHUSDT są ustalone przez ticket/build.md wprost, nie przez ranking płynności.

**Metoda doboru pozostałych 3**: `GET https://api.bybit.com/v5/market/tickers?category=linear` (publiczny endpoint, bez klucza), filtr do symboli kwotowanych w USDT, sortowanie malejąco po `turnover24h` (obrót 24h w USDT — miara płynności, nie miara wyniku strategii). Migawka: `data_cache/f005_liquidity_snapshot.json`, 2026-09-22T07:09:17Z. Top 20:

| # | Symbol | turnover24h (USDT) |
| --- | --- | --- |
| 1 | BTCUSDT | 9,981,908,880 |
| 2 | ETHUSDT | 4,375,758,419 |
| 3 | SOLUSDT | 1,431,507,570 |
| 4 | XRPUSDT | 959,247,937 |
| 5 | ZECUSDT | 628,192,447 |
| 6 | DOGEUSDT | 523,229,764 |
| 7 | NEARUSDT | 431,065,262 |
| 8 | 1000PEPEUSDT | 422,995,511 |
| 9 | SUIUSDT | 311,861,078 |
| 10 | HYPEUSDT | 289,468,671 |
| 11 | SOXLUSDT | 228,471,768 |
| ... | | |

ETHUSDT (#2) i SOLUSDT (#3) już są w koszyku (ustalone wprost, nie przez ranking). Wybrane 3 dodatkowe (kryterium: najwyższy `turnover24h` wśród standardowych, dobrze znanych par USDT perpetual, z wykluczeniem instrumentów, które nie są zwykłym crypto-perpem):

- **BTCUSDT** (#1 obrotu) — najbardziej płynny instrument na Bybit, naturalny punkt odniesienia.
- **XRPUSDT** (#4 obrotu) — kolejny wg płynności po BTC/ETH/SOL, standardowy USDT perpetual.
- **DOGEUSDT** (#6 obrotu) — wybrany zamiast #5 ZECUSDT (mniej znany, bardziej spekulacyjny instrument o niższej rozpoznawalności rynkowej) i zamiast #8 1000PEPEUSDT (kontrakt ze sztucznym mnożnikiem `1000×` w nazwie — utrudnia porównywalność notional/sizing bez dodatkowej konwersji).

Wykluczone z rozważań mimo wysokiego obrotu: **SOXLUSDT** (#11), **XAUUSDT** (#15, złoto), **AAPLUSDT** (#17, akcja) — to tokenizowane instrumenty spoza zakresu „Bybit USDT perpetual, kryptowaluty" z `spec/vision.md`, nie standardowe crypto-perpy.

**Finalny koszyk (5 symboli)**: SOLUSDT, ETHUSDT, BTCUSDT, XRPUSDT, DOGEUSDT. Dobór nie użył żadnego wyniku PnL/backtestu — wyłącznie obrót 24h w chwili audytu i jawnie opisane wykluczenie instrumentów spoza zakresu.

## 3. Okna train / validation / holdout (UTC, zamrożone)

### 3.1 Kształt

Domyślna propozycja `spec/build.md`: kroczące 12 mies. treningu / 3 mies. walidacji, min. 4 okna walidacyjne, ostatnie 6 mies. jako holdout. Użyta bez skrócenia (sekcja 1 — margines ×2 nawet dla najkrótszej historii w koszyku).

„Teraz" przyjęte jako 2026-09-22 (data audytu). Holdout kończy się na ostatnim **pełnym** miesiącu kalendarzowym przed „teraz" (2026-09 jest niepełny — zgodnie z `spec/build.md`, „Definicja dnia": *„Niepełne miesiące pokazywać osobno"*), więc holdout = 2026-03-01 … 2026-09-01 (marzec–sierpień 2026 włącznie, 6 pełnych miesięcy).

### 3.2 Dokładne granice (UTC, `[start, end)`)

| Okno | Start (UTC) | Koniec (UTC) | Zakres kalendarzowy | Długość |
| --- | --- | --- | --- | --- |
| Train 1 | 2024-03-01T00:00:00Z | 2025-03-01T00:00:00Z | 2024-03 … 2025-02 | 12 mies. |
| Validation 1 | 2025-03-01T00:00:00Z | 2025-06-01T00:00:00Z | 2025-03 … 2025-05 | 3 mies. |
| Train 2 | 2024-06-01T00:00:00Z | 2025-06-01T00:00:00Z | 2024-06 … 2025-05 | 12 mies. |
| Validation 2 | 2025-06-01T00:00:00Z | 2025-09-01T00:00:00Z | 2025-06 … 2025-08 | 3 mies. |
| Train 3 | 2024-09-01T00:00:00Z | 2025-09-01T00:00:00Z | 2024-09 … 2025-08 | 12 mies. |
| Validation 3 | 2025-09-01T00:00:00Z | 2025-12-01T00:00:00Z | 2025-09 … 2025-11 | 3 mies. |
| Train 4 | 2024-12-01T00:00:00Z | 2025-12-01T00:00:00Z | 2024-12 … 2025-11 | 12 mies. |
| Validation 4 | 2025-12-01T00:00:00Z | 2026-03-01T00:00:00Z | 2025-12 … 2026-02 | 3 mies. |
| **Holdout** | **2026-03-01T00:00:00Z** | **2026-09-01T00:00:00Z** | 2026-03 … 2026-08 | 6 mies. |

Każde okno treningowe kończy się dokładnie tam, gdzie zaczyna się jego okno walidacyjne (bez zakładki między train i validation); okna treningowe między sobą nachodzą (kroczące o 3 mies.) — to zamierzone, zgodne z propozycją build.md, nie błąd.

Łączny zakres Train1_start → Holdout_end = 2024-03-01 → 2026-09-01 = **dokładnie 30 miesięcy** (12+4×3+6).

Warm-up wskaźników (potrzebny przed Train1, żeby np. `ema200`/`BB_20_25_EMA200` miały pełne dane od pierwszego bara Train1, nie NaN): największe okno w `strategy.add_indicators` to EMA o `span=200` (200 barów). Bufor: **35 dni kalendarzowych przed Train1_start** = od **2024-01-26T00:00:00Z** (210 barów przy 4h, 840 barów przy 1h — z zapasem ponad wymagane 200). Dane warm-up służą wyłącznie do liczenia wskaźników, nie generują sygnałów/wejść (`data_contract.split_warmup`).

### 3.3 Margines wobec realnej historii

Najkrótsza historia w koszyku (SOLUSDT) zaczyna się 2021-10-15 — **ponad 2 lata wcześniej** niż wymagany początek warm-up (2024-01-26). Cały koszyk ma więc **znaczny margines niewykorzystanej historii** (SOLUSDT: ~27 dodatkowych miesięcy przed warm-up startem; BTCUSDT: ~46 dodatkowych miesięcy). Ten protokół celowo **nie** rozszerza liczby okien walidacyjnych powyżej minimum 4 zdefiniowanego w build.md — to trzyma się dosłownie zamrożonej propozycji z tickieta, nie jest próbą maksymalizacji wykorzystania danych w tej fali. Wykorzystanie dodatkowej wcześniejszej historii (więcej okien walk-forward, dłuższy train) jest możliwą przyszłą decyzją (F006+), ale wymagałaby osobnego, jawnego uzasadnienia — nie jest tu domyślnie zakładana.

## 4. Kapitał, ryzyko, cel regularności (z `spec/build.md`, cytowane dosłownie)

- `initial_equity = 500` USD — kapitał portfela, wspólny dla wszystkich strategii/symboli.
- `stake = 100` USD/wejście, **przed dźwignią** (nominał = 100 × leverage, bez automatycznej kapitalizacji).
- Max DD = 50% liczone od bieżącego historycznego szczytu equity (przy 500 USD granica = 250 USD), z kosztami i otwartymi pozycjami (mark-to-market, `equity.Portfolio.mark_to_market`) — twarde kryterium odrzucenia, nie cel do wykorzystania.
- Dźwignia: strojenie dźwigni oddzielić od strojenia sygnału (build.md); większy lewar nie liczy się jako poprawa przewagi. Wartość dźwigni per strategia w wave 2 pozostaje wartością z istniejących presetów `STRATEGY_CATALOG`/configu (nie jest przedmiotem tej fali).

**Cel regularności i tolerancja** (`spec/build.md`, sekcja „Cel regularności i tolerancja", cytat dosłowny):

> TARGET_POSITIVE_DAY_PCT = 100 (dzień dodatni = PnL netto > 0). DAILY_NONPROFIT_TOLERANCE_PCT = 20, czyli min. 80% dni dodatnich w pełnym miesiącu — to tolerancja częstości, nie dopuszczalna strata dzienna.
>
> Wzór: N = dni kalendarzowe miesiąca; positive_day_pct = 100 × N_plus/N; deviation_pct = 100 × (N_minus + N_zero)/N. Cel spełniony, gdy deviation_pct ≤ 20 (np. min. 24/30 lub 25/31 dni dodatnich). Brakujące dane unieważniają ocenę miesiąca, nie liczą się jako zero.

Definicja dnia (build.md, „Decyzje i granice pracy", cytat): *„zmiana equity między końcami dni (zrealizowany + niezrealizowany PnL, opłaty, funding), strefa Europe/Warsaw. Dni zerowe liczą się jako dni bez zysku; mianownik to wszystkie dni kalendarzowe pełnego miesiąca. Niepełne miesiące pokazywać osobno."*

## 5. Budżet strategii dla fali 2 (baseline)

**Decyzja: pełny `STRATEGY_CATALOG` (79 strategii), bez podzbioru.**

`len(strategy.STRATEGY_CATALOG) == 79` (zweryfikowane: `python -c "import strategy; print(len(strategy.STRATEGY_CATALOG))"`).

### Pomiar kosztu per-bar `backtest_engine.run_backtest` (WYŁĄCZNIE na danych syntetycznych/testowych — nie na realnych danych koszyka, zgodnie z ograniczeniem tej fali)

Dane: `tests/fixtures/ohlcv_sample.csv` (istniejący fixture testowy F004, 600 barów), sztucznie powielony 40× i przeindeksowany na ciągłą godzinową siatkę czasu (24000 „barów") wyłącznie do pomiaru czasu wykonania — nie reprezentuje żadnego realnego instrumentu i nie był użyty do żadnego wniosku o strategii.

- Pojedyncza strategia (`RSI14_7030`), 6000 barów: 0.251s. 24000 barów: 0.843s → koszt krańcowy ≈ 3.29×10⁻⁵ s/bar, narzut stały na wywołanie ≈ 0.054s (regresja liniowa z dwóch punktów).
- **Cały katalog (79 strategii) na 24000 barach**: łącznie 42.996s, średnio 0.544s/strategię, najwolniejsza `ADX14_DI_20` — 1.116s. Wynik zapisuje `sorted(strategy.STRATEGY_CATALOG.keys())`, więc obejmuje cały katalog, nie próbkę.

### Ekstrapolacja na pełny budżet fali 2

Projekt wykonania (patrz sekcja 6): **jeden ciągły przebieg `run_backtest` per (symbol, interwał, strategia)** obejmujący `warmup_start → holdout_end` (2024-01-26 → 2026-09-01), z podziałem wyniku (equity curve/trades) na okna Train/Validation/Holdout przy raportowaniu — nie osobny przebieg per okno. To poprawne, bo strategie z `STRATEGY_CATALOG` mają stałe, gotowe parametry — fala 5 (F005) nie dopasowuje niczego do okna treningowego (dopasowanie parametrów to F006/F010); pojedynczy ciągły przebieg daje identyczny wynik jak nowe przebiegi per okno, bez ryzyka przecieku (nic nie jest dopasowywane).

Liczba barów per (symbol, interwał) w tym zakresie (patrz sekcja 6, tabela manifestu): 5695 (4h, z warm-up) / 22777 (1h, z warm-up).

- 1h: 0.544s × (22777/24000) ≈ 0.516s/strategię/symbol → × 5 symboli × 79 strategii ≈ **204s**.
- 4h: 0.544s × (5695/24000) ≈ 0.129s/strategię/symbol → × 5 symboli × 79 strategii ≈ **51s**.
- **Razem (oba interwały, cały koszyk, cały katalog): ≈ 255s (≈4.3 min)**, przypadek pesymistyczny (wszystkie strategie tak wolne jak najwolniejsza `ADX14_DI_20`): ≈510s (≈8.5 min).

Liczba wywołań `run_backtest` łącznie: 5 symboli × 2 interwały × 79 strategii = **790**.

Wniosek: pełny katalog mieści się wygodnie w pojedynczej sesji fali 2 (rząd minut, nie godzin) — **nie ma potrzeby dokumentowanego podzbioru**, cały `STRATEGY_CATALOG` wchodzi do baseline.

## 6. Manifest danych (dowód reprodukowalności dla fali 2)

Dwa poziomy cache, oba pod `data_cache/` (format `data_contract.py`: CSV + `.manifest.json`, nazwa deterministyczna `{symbol}_{interval}_{startUTC}_{endUTC}`, checksuma SHA-256 weryfikowana przy `load_dataset`):

1. **Pełna dostępna historia per symbol/interwał** (sekcja 1) — 10 plików, zakresy jak w tabeli sekcji 1. Skrypt: `scripts/f005_fetch_audit_data.py`. Zbiorczy plik: `data_cache/f005_audit_summary.json`.
2. **Zakres dokładnie zgodny z protokołem** (`warmup_start=2024-01-26T00:00:00Z` → `holdout_end=2026-09-01T00:00:00Z`), zbudowany z (1) przez ponowne wycięcie zakresu przez `data_contract.build_dataset` — **bez żadnego nowego zapytania sieciowego** (dowód: `scripts/f005_build_protocol_cache.py` czyta z `data_cache/`, nie importuje `strategy.get_bybit_ohlcv`). To dokładny zbiór, na którym fala 2 ma liczyć baseline.

Tabela (2) — dokładny zbiór danych fali 2, z checksumami:

| Symbol | Interwał | Zakres (UTC, wraz z warm-up) | Wiersze (z warm-up) | Warm-up barów | Wiersze użyteczne | Luki | Checksuma SHA-256 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SOLUSDT | 240 | 2024-01-26T00:00:00Z … 2026-09-01T00:00:00Z | 5695 | 210 | 5485 | 0 | `72a6947ba3607e4326cf8a3d655dbc0953103cc66e5f1dd74aa8eb83e45fb731` |
| SOLUSDT | 60 | 2024-01-26T00:00:00Z … 2026-09-01T00:00:00Z | 22777 | 840 | 21937 | 0 | `25323c766de58648b624435237e47994b0a3ae1cda5cbcf7e091689b4e74c213` |
| ETHUSDT | 240 | 2024-01-26T00:00:00Z … 2026-09-01T00:00:00Z | 5695 | 210 | 5485 | 0 | `4e856f13e3da0afa5d8b5d1d102e04a133788f49122694bdba222f90fbe13176` |
| ETHUSDT | 60 | 2024-01-26T00:00:00Z … 2026-09-01T00:00:00Z | 22777 | 840 | 21937 | 0 | `239b32b3348bd11978fdbb43e2d7220f4113625be9e558c4e533e096a312645e` |
| BTCUSDT | 240 | 2024-01-26T00:00:00Z … 2026-09-01T00:00:00Z | 5695 | 210 | 5485 | 0 | `d690423a3bae1a53f73728a3b178ab14cbf970855163bed32fe6b727b8e6c467` |
| BTCUSDT | 60 | 2024-01-26T00:00:00Z … 2026-09-01T00:00:00Z | 22777 | 840 | 21937 | 0 | `cfb39aec9eadb660460f9e0f180184b67690a35c92af8a16e66398ea548e8d69` |
| XRPUSDT | 240 | 2024-01-26T00:00:00Z … 2026-09-01T00:00:00Z | 5695 | 210 | 5485 | 0 | `11c203e30f687508833530daa913e133eb42239699ed52339f4f8e3fbd5a89b3` |
| XRPUSDT | 60 | 2024-01-26T00:00:00Z … 2026-09-01T00:00:00Z | 22777 | 840 | 21937 | 0 | `cdd81edbe415f3d583bc365ca1e786afa09956a4aa3bf82e739ecf9b0475b4a5` |
| DOGEUSDT | 240 | 2024-01-26T00:00:00Z … 2026-09-01T00:00:00Z | 5695 | 210 | 5485 | 0 | `5a05355dd929a844a262cf9a15950974b1cdf18000b7e44c71ff89ebf567abde` |
| DOGEUSDT | 60 | 2024-01-26T00:00:00Z … 2026-09-01T00:00:00Z | 22777 | 840 | 21937 | 0 | `748590acb70eed66878380a7ba4890f498ac458038cd7feec20c3ec3fa16e8ff` |

Zbiorczy plik: `data_cache/f005_protocol_scoped_manifest.json`. Wszystkie 10 kombinacji: **100% pokrycia, 0 luk** — żaden symbol nie potrzebował `allow_gaps=True`.

**Jak fala 2 ma wczytać dokładnie te dane** (bez ponownego pobierania z sieci):

```python
import data_contract
df, manifest = data_contract.load_dataset(
    "data_cache", "SOLUSDT", "240",
    "2024-01-26T00:00:00Z", "2026-09-01T00:00:00Z",
)
assert manifest.checksum_sha256 == "72a6947ba3607e4326cf8a3d655dbc0953103cc66e5f1dd74aa8eb83e45fb731"
```

`load_dataset` rzuca `DataContractError`, jeśli plik na dysku nie zgadza się z zapisaną checksumą — cichy dryf danych między falą 1 a falą 2 jest błędem twardym, nie zostanie niezauważony.

## 7. Kryteria odrzucenia i reguła holdoutu (wiążąca dla F005 i wszystkich przyszłych feature'ów, F006+)

- Holdout = **2026-03-01T00:00:00Z … 2026-09-01T00:00:00Z**, wszystkie 5 symboli koszyka, oba interwały (4h/1h). To okno jest zdefiniowane raz, tutaj, i nie zmienia się po zobaczeniu jakiegokolwiek wyniku.
- **Twarde kryteria odrzucenia** (z `spec/build.md`): DD > 50% w dowolnym momencie (liczone mark-to-market, z otwartymi pozycjami) → odrzucenie natychmiastowe, niezależnie od pozostałych metryk. `deviation_pct > 20` w danym pełnym miesiącu → cel regularności nieosiągnięty dla tego miesiąca (raportować, nie ukrywać uśrednieniem). Ujemny PnL netto w dowolnym ocenianym miesiącu lub w całym okresie → brak promocji, niezależnie od regularności (build.md: „Regularność zysku nie usprawiedliwia ujemnego wyniku netto").
- **Zasada „holdout nietykalny" (wiążąca dla F005 i każdego kolejnego feature'a)**:
  1. Fala 2 (F005-baseline) **może** policzyć i zaraportować metryki na holdoucie dla **istniejącego, niemodyfikowanego** katalogu strategii (`STRATEGY_CATALOG`, gotowe parametry — nic nie jest tu dopasowywane) — to czysty pomiar obecnego stanu, zgodnie z zakresem tickieta F005 („jeśli baseline go dotknie, to tylko dla zmierzenia obecnego stanu, nie do poprawek").
  2. Wynik holdoutu z fali 2 **nie może** być użyty do: (a) wyboru, którą istniejącą strategię z katalogu uznać za lepszą/promować, (b) strojenia parametrów żadnej strategii, (c) inspirowania nowych hipotez sygnału w F006, (d) ponownego przeliczenia po zmianie protokołu (okien/koszyka/tolerancji/kosztów), żeby wynik „zaliczył" próg PASS.
  3. F006 (poszukiwanie nowych strategii) prowadzi całą selekcję/porównanie **wyłącznie** na train+validation. Holdout pozostaje zamknięty dla F006 — F006 nie wolno go otwierać nawet do diagnostyki.
  4. F007 otwiera to samo, niezmienione okno holdoutu **raz**, dla już zamrożonego finalisty (strategia/e, parametry, koszyk, sizing zamrożone PRZED otwarciem holdoutu) — zgodnie z `spec/build.md`, F007: „Zamrozić strategię(-e)... dopiero wtedy otworzyć holdout." Porażka na holdoucie w F007 nie uprawnia do donastrajania tego samego holdoutu (build.md, F007: „Porażka nie uprawnia do dostrojenia tego samego holdoutu").
  5. Jeśli po 2026-09-01 pojawią się nowe dane (przyszłe miesiące), mogą zasilić przyszłe, osobno uzasadnione okna — ale **to konkretne okno holdoutu** (2026-03 … 2026-08) zachowuje swoją rolę zamrożonego testu końcowego dla obecnego katalogu (F005) i dla kandydata z F007; nie jest przesuwane ani rozszerzane, żeby poprawić wynik.

## 7a. Uwaga Coordinatora: `data_cache/*.csv` nie jest w git

Surowe pliki CSV (~28 MB, ~446 tys. wierszy) nie są śledzone w git (`.gitignore: data_cache/*.csv`) — bloatowałyby historię repo bezterminowo i tylko rosłyby z każdą kolejną falą/symbolem (F006+). Reprodukowalność zapewniają checksumy SHA-256 w `.manifest.json` (śledzone w git) i w tabeli sekcji 6 — nie literalna obecność bajtów w repo. Same CSV zostają lokalnie na dysku serwera projektu (zgodnie z build.md: „wyniki tylko lokalnie na dysku”); jeśli znikną, `scripts/f005_fetch_audit_data.py` + `scripts/f005_build_protocol_cache.py` je odtworzą identycznie (ten sam publiczny endpoint, te same zakresy dat), a `load_dataset` zweryfikuje checksumę przy odczycie.

## 8. Skrypty i pochodzenie danych

- `scripts/f005_fetch_audit_data.py` — audyt sekcji 1 (sieć: `strategy.get_bybit_ohlcv`, publiczny endpoint kline).
- `scripts/f005_build_protocol_cache.py` — budowa dokładnego zakresu fali 2 (sekcja 6) z już pobranego cache, bez sieci.
- `data_cache/f005_liquidity_snapshot.json` — migawka obrotu 24h użyta do doboru koszyka (sekcja 2), jedno zapytanie `GET /v5/market/tickers`.
- Żadne z powyższych nie importuje `trader.py`/`main.py`/`configuration/`; brak zleceń, brak kluczy API.
