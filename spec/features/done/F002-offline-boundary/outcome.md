# Outcome

`backtest_apex.py` przyjmuje `--local-csv` i uruchamia backtest z lokalnego fixture bez żadnego wywołania sieciowego (potwierdzone testem, który blokuje `requests.get`/`post`); domyślne zachowanie CLI (pobieranie z Bybit) niezmienione. Brak danych lub brak wyników kończy proces kodem różnym od zera zamiast dawnego `sys.exit(0)`, więc automatyzacja odróżni błąd od sukcesu. Dowód (komendy, wynik testów, potwierdzenie braku importu `trader.py`/`rest_logs.py`) zapisany w `spec/research/F002-offline-boundary.md`. Produkcyjne pliki (main.py, trader.py, configuration/) niezmienione.
