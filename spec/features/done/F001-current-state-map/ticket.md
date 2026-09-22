# F001 · Mapa obecnego zachowania bota i kontraktu live

## Outcome

Coordinator i przyszli Workerzy mają jeden dokument opisujący, jak bot faktycznie działa dziś: pętlę główną, kontrakt sygnału/wejścia/wyjścia/ryzyka i realne pliki konfiguracyjne produkcji. To baza pod F002 (granica offline) — bez niej każda kolejna decyzja opiera się na domysłach co do obecnego zachowania.

## Scope

- Opisać pętlę main.py (WebSocket świec, kolejka, TraderBot, update_tsl) z odwołaniami plik:linia.
- Opisać kontrakt wejścia/wyjścia/SL/TSL/cooldown/circuit breaker z trader.py i generowanie sygnału ze strategy.py.
- Zidentyfikować, który plik w configuration/ (lub logs/configuration/) faktycznie odpowiada produkcji, i uzasadnić wybór.
- Rozszerzyć listę rozbieżności symulacja/live z sekcji „Ustalenia z kodu" w build.md, jeśli przegląd ujawni kolejne.

## Out of scope

- Zmiana configów, kodu, logiki bota.
- Import trader.py w sposób, który otwiera połączenie produkcyjne (analiza wyłącznie statyczna/czytanie kodu).
- Uruchamianie backtestów, botów, zleceń, eksportu do Apex (to F002+).

## Acceptance

- Istnieje dokument (spec/research/F001-current-state.md lub podobny) z kontraktem sygnału/wejścia/wyjścia/ryzyka, każdy punkt z odwołaniem plik:linia.
- Dokument wskazuje, który config uznajemy za produkcyjny i dlaczego.
- Dokument zawiera listę rozbieżności symulacja/live (co najmniej te już znane z build.md, oznaczone jako potwierdzone lub sprecyzowane).
- `git diff` poza nowym dokumentem i tym ticketem jest pusty — brak zmian w main.py/trader.py/strategy.py/configuration/.

## Notes

Effort: medium (dużo kodu do spójnego przeczytania, niska cena błędu bo praca czysto dokumentacyjna, ale trzeba uniknąć powierzchownego streszczenia).
