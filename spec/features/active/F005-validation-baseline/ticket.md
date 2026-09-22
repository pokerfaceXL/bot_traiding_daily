# F005 · Zamrożony protokół walidacji i zmierzony baseline obecnych strategii

## Outcome

Przed jakimkolwiek poszukiwaniem nowej strategii (F006+) istnieje zapisany, zamrożony protokół (okna train/validation/holdout, koszyk instrumentów, budżet prób, kryteria odrzucenia) i jeden odtwarzalny raport pokazujący, jak obecny katalog strategii radzi sobie wobec celu 100% dni dodatnich z tolerancją 20%, na realnych danych historycznych. To baseline, do którego porównuje się każdy przyszły kandydat.

## Scope

- Audyt realnie dostępnej historii Bybit (linear perpetual, 1h/4h) dla koszyka: SOLUSDT, ETHUSDT + mały koszyk wg płynności (build.md, „Decyzje i granice pracy”) — ile miesięcy danych faktycznie istnieje, przez `strategy.get_bybit_ohlcv`.
- Zapisać protokół PRZED jakimkolwiek pomiarem: okna train/validation/holdout (propozycja z build.md: kroczące 12mies./3mies., min. 4 okna walidacyjne, ostatnie 6mies. holdout — dostosować do realnej głębi danych, jawnie opisać skrócenie jeśli historia jest krótsza), initial_equity=500, stake=100, max DD 50%, cel/tolerancja z sekcji „Cel regularności i tolerancja".
- Zbudować moduł liczący dzienną/miesięczną regularność (positive_day_pct, deviation_pct, spełnienie tolerancji) z equity curve `backtest_engine.py` (F004) — strefa Europe/Warsaw, dni zerowe liczą się jako bez zysku, per build.md „Definicja dnia”.
- Uruchomić baseline: obecny katalog strategii (`STRATEGY_CATALOG`) na koszyku/oknach z zamrożonego protokołu, przez `backtest_engine.py` (kosztowy silnik z F004, nie stary bezkosztowy).
- Raport per miesiąc osobno (bez maskowania średnią): najgorszy miesiąc, najgorszy dzień, najdłuższa seria strat, DD, deviation_pct — zgodnie ze „Standard raportu eksperymentu” w build.md.

## Out of scope

- Nowe strategie/hipotezy, strojenie parametrów (F006+).
- Metoda optymalizacji/Optuna (F010).
- Holdout nie służy do wyboru w tej fazie — jeśli baseline go dotknie, to tylko dla zmierzenia obecnego stanu, nie do poprawek.

## Acceptance

- `spec/research/F005-validation-protocol.md`: zamrożony protokół (daty UTC okien, koszyk, initial_equity/stake/DD/cel/tolerancja/budżet prób) zapisany PRZED raportem baseline, nie po.
- `spec/research/F005-baseline.md` (lub podobnie): raport per strategia/okno/miesiąc z positive_day_pct/deviation_pct/DD, najgorszy miesiąc i dzień, bez uśredniania które maskuje porażkę.
- Dowód odtwarzalności: run_id/commit/manifest danych (F003) dla każdego pomiaru.
- Brak zmian w main.py/trader.py/configuration/.

## Notes

Effort: wysoki dla protokołu (jednoznaczność okien/koszyka ma trwałe konsekwencje — nie zmieniać po zobaczeniu wyników), średni dla samego uruchomienia baseline (mechaniczne, silnik już zbudowany w F004).
