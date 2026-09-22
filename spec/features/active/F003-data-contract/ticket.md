# F003 · Powtarzalny kontrakt danych OHLCV z manifestem i kontrolą jakości

## Outcome

Każdy backtest deklaruje jawny zakres UTC i symbole, pobiera dane raz do lokalnego cache, i zostawia manifest (checksumy, luki, pokrycie, warm-up) który mówi wprost, czy dane są wystarczające do zaufania wynikowi. Bez tego F004/F005 nie mają wspólnej, odtwarzalnej podstawy danych do porównywania kandydatów.

## Scope

- Cache OHLCV per symbol/interwał/zakres UTC na dysku (Parquet/CSV), z jawnym start/end zamiast dorozumianego `limit=N świec wstecz od teraz`.
- Filtr tylko zamkniętych świec (już częściowo w `strategy.py:836`/`trader.py:174` — ujednolicić dla ścieżki backtestu, patrz F001 rozbieżność #5).
- Wykrywanie luk (brakujące świece w oczekiwanej siatce czasowej) i warm-up (ile świec trzeba przed pierwszym ocenianym punktem dla wskaźników).
- Manifest per uruchomienie: symbole, zakres, checksuma danych, liczba luk, ocena pokrycia — zapisany obok raportu backtestu (`output/backtests/<run_id>/`).
- Reguła: brakujące dane/koszty nie mogą być cicho zerowane — muszą być oznaczone w manifeście i wykluczać dany wynik z rankingu.
- Startowy koszyk instrumentów z build.md (SOLUSDT, ETHUSDT + mały koszyk wg płynności) — zdefiniować listę i uzasadnienie doboru, bez selekcji po wynikach PnL.

## Out of scope

- Equity, margin, koszty realizacji, likwidacja — F004.
- Wybór protokołu walidacji train/validation/holdout — F005.
- Zmiana main.py/trader.py/configuration/ produkcyjnych.

## Acceptance

- Backtest offline (bazując na F002) potrafi wskazać jawny start/end UTC i wygenerować manifest z checksumą i raportem luk dla co najmniej jednego symbolu/interwału.
- Test pokazuje, że sztucznie wprowadzona luka w danych jest wykryta i oznaczona w manifeście, nie zignorowana.
- Manifest jednoznacznie odróżnia „dane wystarczające” od „dane niewystarczające — wynik wykluczony z rankingu”.
- `git diff` poza nowymi plikami manifestu/cache/testów jest pusty w main.py/trader.py/configuration/.

## Notes

Effort: medium-high — więcej niejednoznaczności niż F001/F002 (definicja „wystarczających” danych, siatka czasowa per interwał), ale to jeszcze nie equity/margin (F004, wyższy effort).
