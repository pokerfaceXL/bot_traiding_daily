"""
run_backtest_apex.py — uruchamia backtest_apex.py rownolegle dla wielu symboli.

Filtrowanie symboli:
  - tylko pary USDT na linear perpetuals
  - symbol musi istniec na gieldzie co najmniej 1 rok

Przykladowe uzycie:
    # wszystkie strategie, wszystkie symbole USDT >= 1 rok
    python run_backtest_apex.py

    # tylko wybrane strategie
    python run_backtest_apex.py --strategies BB_20_25_SQ BB_20_2_SQ

    # tylko wybrane symbole
    python run_backtest_apex.py --symbols BTCUSDT ETHUSDT

    # konkretny interval (minuty: 60, 240, 30 itd.)
    python run_backtest_apex.py --intervals 240 60

    # lista dostepnych strategii
    python run_backtest_apex.py --list-strategies
"""

import argparse
import os
import subprocess
import sys
import time
import yaml
import requests
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

from strategy import STRATEGY_CATALOG

# ──────────────────────────────────────────────────────────────
# ARGUMENTY
# ──────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="Multi-symbol backtest runner")
parser.add_argument("--strategies", nargs="*", default=None,
                    help="Strategie do przetestowania (domyslnie: wszystkie)")
parser.add_argument("--symbols", nargs="*", default=None,
                    help="Symbole do przetestowania (domyslnie: wszystkie USDT >= 1 rok)")
parser.add_argument("--intervals", nargs="*", default=["240", "60"],
                    help="Timeframe'y w minutach (domyslnie: 240 60)")
parser.add_argument("--workers", type=int, default=2,
                    help="Maksymalna liczba rownoleglych procesow (domyslnie: 6)")
parser.add_argument("--candles", type=int, default=8000,
                    help="Minimalna liczba swiec do backtestow (domyslnie: 8000)")
parser.add_argument("--config-template", default="configuration/default.yaml",
                    help="Sciezka do szablonu konfiguracji")
parser.add_argument("--list-strategies", action="store_true",
                    help="Wyswietl dostepne strategie i zakoncz")
parser.add_argument("--param-optimization", action="store_true",
                    help="Optuna optimization po leverage/max_sl_pct/trail_pct/activate_pct")
parser.add_argument("--cooldown", type=int, default=0,
                    help="Ile swiec przerwy po initial SL przed kolejnym wejsciem (domyslnie: 0 = wylaczone)")
parser.add_argument("--optuna-trials", type=int, default=None,
                    help="Liczba prob Optuna (nadpisuje YAML OPTUNA_TRIALS; domyslnie 150)")
args = parser.parse_args()

if args.list_strategies:
    print("Dostepne strategie:")
    for name in sorted(STRATEGY_CATALOG.keys()):
        print(f"  {name}")
    sys.exit(0)

CONFIG_TEMPLATE = Path(args.config_template)
BACKTEST_SCRIPT = Path(__file__).parent / "backtest_apex.py"
MIN_LISTING_AGE_DAYS = 365   # symbol musi byc starszy niz 1 rok

# ──────────────────────────────────────────────────────────────
# WALIDACJA STRATEGII
# ──────────────────────────────────────────────────────────────

if args.strategies:
    unknown = [s for s in args.strategies if s not in STRATEGY_CATALOG]
    if unknown:
        print(f"[BLAD] Nieznane strategie: {unknown}")
        print(f"Uzyj --list-strategies zeby zobaczyc dostepne.")
        sys.exit(1)
    strategy_names = args.strategies
else:
    strategy_names = list(STRATEGY_CATALOG.keys())

print(f"Strategii do przetestowania: {len(strategy_names)}")

# ──────────────────────────────────────────────────────────────
# POBIERANIE SYMBOLI Z BYBIT
# ──────────────────────────────────────────────────────────────

def get_usdt_symbols_min_age(min_days=365):
    """
    Zwraca liste symboli USDT z linear perpetuals ktore sa notowane
    na gieldzie od co najmniej min_days dni.
    """
    url          = "https://api.bybit.com/v5/market/instruments-info"
    cutoff_ms    = (time.time() - min_days * 86400) * 1000
    params       = {"category": "linear", "limit": 1000}
    symbols      = []

    while True:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        for item in data["result"]["list"]:
            sym      = item["symbol"]
            launch   = int(item.get("launchTime", 0))
            status   = item.get("status", "")
            if (sym.endswith("USDT")
                    and status == "Trading"
                    and launch > 0
                    and launch < cutoff_ms):
                symbols.append(sym)

        cursor = data["result"].get("nextPageCursor", "")
        if not cursor:
            break
        params["cursor"] = cursor

    return sorted(symbols)


# ──────────────────────────────────────────────────────────────
# PRZYGOTOWANIE KONFIGURACJI DLA SUBPROCESU
# ──────────────────────────────────────────────────────────────

def prepare_config(symbol, interval, candles, cooldown):
    """Tworzy tymczasowy plik konfiguracyjny dla danego symbolu."""
    cfg = yaml.safe_load(CONFIG_TEMPLATE.read_text())
    cfg["SYMBOL"]           = symbol
    cfg["INTERVAL"]         = interval
    cfg["CANDLES"]          = candles
    cfg["COOLDOWN_CANDLES"] = cooldown
    backtest_dir = CONFIG_TEMPLATE.parent / "backtest"
    backtest_dir.mkdir(parents=True, exist_ok=True)
    config_path = backtest_dir / f"{symbol}_{interval}.yaml"
    config_path.write_text(yaml.dump(cfg))
    return config_path


# ──────────────────────────────────────────────────────────────
# ZADANIE BACKTESTOWE (uruchamiane w subprocesie)
# ──────────────────────────────────────────────────────────────

def run_backtest_task(symbol, interval, candles, bot_id, strategies, cooldown):
    """Uruchamia backtest_apex.py jako subprocess."""
    config_path = prepare_config(symbol, interval, candles, cooldown)
    env = os.environ.copy()
    env["BOT_ID"] = str(bot_id)

    cmd = [sys.executable, str(BACKTEST_SCRIPT), str(config_path)]
    if strategies:
        cmd += ["--strategies"] + strategies
    if args.param_optimization:
        cmd += ["--param-optimization"]
    if args.optuna_trials is not None:
        cmd += ["--optuna-trials", str(args.optuna_trials)]

    result = subprocess.run(
        cmd,
        cwd=str(Path(__file__).parent),
        env=env,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        err = result.stderr.strip()[-300:] if result.stderr else "(brak stderr)"
        print(f"ERR {symbol} @ {interval}m:\n{err}", flush=True)
        return f"ERR {symbol} @ {interval}m  (exit {result.returncode})"
    return f"OK  {symbol} @ {interval}m"


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def main():
    bot_id = int(time.time())

    # Symbole
    if args.symbols:
        symbols = args.symbols
        print(f"Uzytkownik podal {len(symbols)} symboli.")
    else:
        print(f"Pobieranie symboli USDT z Bybit (min {MIN_LISTING_AGE_DAYS} dni)...", flush=True)
        symbols = get_usdt_symbols_min_age(MIN_LISTING_AGE_DAYS)
        print(f"Znaleziono {len(symbols)} kwalifikujacych sie symboli.")

    intervals = args.intervals
    candles   = args.candles
    cooldown  = args.cooldown

    # Budowanie listy zadan
    tasks = [
        (sym, iv, candles, bot_id, strategy_names, cooldown)
        for iv  in intervals
        for sym in symbols
    ]
    print(f"Zadan do wykonania: {len(tasks)}  (workers={args.workers})")
    print(f"Strategie: {', '.join(strategy_names)}")
    print(f"Cooldown po SL: {cooldown} swiec\n")

    # Rownolegle wykonanie
    completed = failed = 0
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(run_backtest_task, sym, iv, c, bid, strats, cd): (sym, iv)
            for sym, iv, c, bid, strats, cd in tasks
        }
        for future in as_completed(futures):
            result = future.result()
            print(result)
            if result.startswith("OK"):
                completed += 1
            else:
                failed += 1

    print(f"\nGotowe — OK: {completed}  BLEDY: {failed}")


if __name__ == "__main__":
    main()
