import logging
import os
import queue
import threading
import requests
from datetime import datetime

_APEX_LOG_URL = (
    "https://g6005f98fc66f55-boty.adb.eu-frankfurt-1.oraclecloudapps.com/ords/boty/lorenzian/bot_log/"
)


class ApexLogHandler(logging.Handler):
    """
    Non-blocking handler: kolejkuje rekordy i wysyla REST w tle (daemon thread).
    Nie blokuje watku tradingowego  - drop gdy kolejka pelna (maxsize=500).
    Domyslnie tylko WARNING+  - INFO/DEBUG zostaja tylko w pliku.
    """

    def __init__(self, bot_id, bot_name, symbol, level=logging.WARNING):
        super().__init__(level)
        self._bot_id   = str(bot_id)
        self._bot_name = bot_name
        self._symbol   = symbol
        self._queue    = queue.Queue(maxsize=500)
        self._thread   = threading.Thread(
            target=self._worker, daemon=True, name="apex-log"
        )
        self._thread.start()

    def emit(self, record):
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            pass  # drop  - nie blokujemy watku tradingowego

    def _worker(self):
        while True:
            try:
                record = self._queue.get(timeout=5)
                self._send(record)
            except queue.Empty:
                continue
            except Exception:
                pass  # worker nie moze sie crashowac

    def _send(self, record):
        try:
            msg = self.format(record)
            raw = {
                "p_bot_id":   self._bot_id,
                "p_bot_name": self._bot_name,
                "p_symbol":   self._symbol,
                "p_level":    record.levelname,
                "p_message":  msg.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")[:4000],
                "p_log_time": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
            }
            # HTTP headers akceptuja tylko Latin-1  - zastepujemy nieobslugiwane znaki
            headers = {k: v.encode("latin-1", errors="replace").decode("latin-1") for k, v in raw.items()}
            resp = requests.post(_APEX_LOG_URL, headers=headers, timeout=5)
            if not resp.ok:
                import sys
                print(f"[apex-log] HTTP {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
        except Exception as e:
            import sys
            print(f"[apex-log] send error: {e}", file=sys.stderr)


def setup_logger(
    name="bot_logger",
    log_file="bot.log",
    level=logging.INFO,
    bot_id=None,
    bot_name=None,
    symbol=None,
    apex_level=logging.WARNING,
):
    log_path = os.path.join("logs", log_file)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    if not logger.handlers:
        fh = logging.FileHandler(log_path, mode="a", delay=True)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # Apex handler  - dodajemy tylko gdy znamy kontekst bota i jeszcze go nie ma
    has_apex = any(isinstance(h, ApexLogHandler) for h in logger.handlers)
    if not has_apex and bot_id is not None and bot_name and symbol:
        ah = ApexLogHandler(bot_id, bot_name, symbol, level=apex_level)
        ah.setFormatter(formatter)
        logger.addHandler(ah)

    logger.propagate = False
    return logger
