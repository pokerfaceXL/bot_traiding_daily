"""
main.py  - live trading main loop z WebSocket kline stream.

Zamiast polling/sleep: nasluchujemy zamkniecia swiece przez WebSocket Bybit
(pole confirm=True). Potwierdzone swiece trafiaja do kolejki; glowny watek
przetwarza je sekwencyjnie  - jedno zdarzenie na raz, bez race conditions.
"""

import sys
import time
import queue
import signal
import yaml

from pybit.unified_trading import WebSocket

from trader import (
    TraderBot, get_current_position, close_position,
    reload_trader_config, update_candle_cache, update_tsl,
)
from logger_config import setup_logger
from rest_logs import report_bot_alive, send_bot_config_to_apex, send_error_to_apex
from config import bot_id, bot_name

# ──────────────────────────────────────────────────────────────
# GLOBALNE
# ──────────────────────────────────────────────────────────────

config        = None
config_path   = None
logger        = None
ws            = None
_candle_queue: queue.Queue = queue.Queue(maxsize=20)


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def initialize_config():
    global config, config_path, logger
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configuration/default.yaml"
    config      = load_config(config_path)
    SYMBOL      = config.get("SYMBOL",   "BTCUSDT")
    INTERVAL    = config.get("INTERVAL", "240")
    logger      = setup_logger(log_file=f"{SYMBOL}_{INTERVAL}.log")
    return config


# ──────────────────────────────────────────────────────────────
# WEBSOCKET
# ──────────────────────────────────────────────────────────────

def _on_kline(msg):
    """
    Callback wywolywany z watku WebSocket.
    Tylko potwierdzone swiece (confirm=True) trafiaja do kolejki.
    """
    for candle in msg.get("data", []):
        if candle.get("confirm"):
            try:
                _candle_queue.put_nowait(candle)
            except queue.Full:
                pass  # glowny watek opoznil sie; duplikat i tak zostanie pominiety


def _start_websocket(symbol: str, interval: str):
    global ws
    ws = WebSocket(testnet=False, channel_type="linear")
    ws.kline_stream(interval=int(interval), symbol=symbol, callback=_on_kline)
    logger.info(f"WebSocket kline.{interval}.{symbol} uruchomiony")


# ──────────────────────────────────────────────────────────────
# SIGNAL HANDLERS
# ──────────────────────────────────────────────────────────────

def graceful_exit(signum, frame):
    logger.info(f"Signal {signum}  - zamykam bota...")
    pos = get_current_position()
    if pos:
        close_position(pos)
    if ws:
        ws.exit()
    sys.exit(0)


def reload_config_handler(signum, frame):
    global config
    logger.info(f"SIGHUP  - przeladowanie konfiguracji {config_path}...")
    try:
        config = load_config(config_path)
        reload_trader_config(config_path)
        send_bot_config_to_apex(bot_id, bot_name, config)
        logger.info("Konfiguracja przeladowana.")
    except Exception as e:
        logger.error(f"Blad przeladowania: {e}")


signal.signal(signal.SIGINT,  graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)
if hasattr(signal, "SIGHUP"):
    signal.signal(signal.SIGHUP, reload_config_handler)


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Podaj sciezke do pliku konfiguracyjnego YAML")
        sys.exit(1)

    config   = initialize_config()
    SYMBOL                 = config.get("SYMBOL",              "BTCUSDT")
    INTERVAL               = config.get("INTERVAL",            "240")
    GAP_CHECK_INTERVAL_SEC = float(config.get("GAP_CHECK_INTERVAL_SEC", 30.0))

    report_bot_alive(bot_id, bot_name, 1)
    send_bot_config_to_apex(bot_id, bot_name, config)

    _start_websocket(SYMBOL, INTERVAL)
    logger.info(f"Bot uruchomiony  - czekam na zamkniecie swiece [{SYMBOL} {INTERVAL}m]...")

    while True:
        try:
            # Blokuje az WebSocket doniesie o zamknietej swiece (timeout = GAP_CHECK_INTERVAL_SEC)
            candle = _candle_queue.get(timeout=GAP_CHECK_INTERVAL_SEC)

            # Inkrementalna aktualizacja cache (bez HTTP)
            update_candle_cache(candle)

            report_bot_alive(bot_id, bot_name, 2)
            logger.info(
                f"Swieca zamknieta | start={candle.get('start')}  "
                f"O={candle['open']} H={candle['high']} "
                f"L={candle['low']} C={candle['close']} V={candle.get('volume','?')}"
            )

            TraderBot(config)

        except queue.Empty:
            # WebSocket zyje ale swieca jeszcze nie zamknieta  - keepalive
            logger.debug(f"Brak swiece w {GAP_CHECK_INTERVAL_SEC:.0f}s  - keepalive")
            report_bot_alive(bot_id, bot_name, 2)
            try:
                update_tsl()   # gap protection + bot-managed TSL co GAP_CHECK_INTERVAL_SEC
            except Exception as tsl_err:
                logger.warning(f"update_tsl() nieudany (problem z siecia?): {tsl_err}")

        except Exception as e:
            logger.error(f"Blad w petli: {e}", exc_info=True)
            send_error_to_apex(bot_id, bot_name, str(e))
            time.sleep(5)


if __name__ == "__main__":
    main()
