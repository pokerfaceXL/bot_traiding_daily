"""
F011 · Live liquidation collector (Bybit allLiquidation, non-trading).

Subscribes to the Bybit public linear WebSocket (``allLiquidation.<SYMBOL>``) and persists
every raw message, plus the local receive timestamp, as one JSON line per message:

    <out_dir>/<SYMBOL>/<YYYY-MM-DD>.jsonl      (UTC day of local receive time, append, flush/line)
    <out_dir>/collector.log                    (connects / disconnects / gaps / acks / errors)
    <out_dir>/heartbeat.json                   (rewritten atomically every minute)

Bybit serves no liquidation history, so this builds our own history from "now". It never
places orders and needs no API key. See forced_flow_lab/LIQ_COLLECTOR.md for operations.

Stdlib only, except the ``websocket-client`` package (``import websocket``), imported lazily
so the parsing/rotation helpers are testable offline.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Any, Dict, Optional, Tuple

WS_URL = "wss://stream.bybit.com/v5/public/linear"
DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT")
TOPIC_PREFIX = "allLiquidation."
PING_INTERVAL_S = 20.0  # Bybit recommends a ping every 20s
HEARTBEAT_INTERVAL_S = 60.0
STALE_TIMEOUT_S = 75.0  # no frame at all (incl. pong) for this long -> reconnect
BACKOFF_INITIAL_S = 1.0
BACKOFF_MAX_S = 60.0
CONTROL_DIR = "_control"  # non-topic messages (subscribe acks) are kept here too

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = _REPO_ROOT / "data_cache" / "liquidations" / "bybit"

log = logging.getLogger("f011.liq_collector")


# --------------------------------------------------------------------------- pure helpers
def utc_day(ts_ms: int) -> str:
    """UTC calendar day (YYYY-MM-DD) for an epoch-milliseconds timestamp."""
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


def iso_utc(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%f"
    )[:-3] + "Z"


def classify_message(raw: str) -> Tuple[str, Optional[str], Any]:
    """Classify one raw WS text frame.

    Returns (kind, symbol, parsed) where kind is one of
      'liquidation' (topic allLiquidation.<SYMBOL>; symbol set),
      'subscribe'   (subscription ack/nack),
      'pong'        (reply to our ping),
      'other'       (valid JSON, anything else),
      'invalid'     (not JSON; parsed is None).
    """
    try:
        msg = json.loads(raw)
    except (TypeError, ValueError):
        return "invalid", None, None
    if not isinstance(msg, dict):
        return "other", None, msg
    topic = msg.get("topic")
    if isinstance(topic, str) and topic.startswith(TOPIC_PREFIX):
        return "liquidation", topic[len(TOPIC_PREFIX):], msg
    op = msg.get("op")
    if op == "subscribe":
        return "subscribe", None, msg
    if op in ("ping", "pong") or msg.get("ret_msg") == "pong":
        return "pong", None, msg
    return "other", None, msg


def make_record(raw: str, recv_ts_ms: int) -> Dict[str, Any]:
    """One output JSON line: local receive time + the raw message (parsed if JSON, else text).

    Bybit sends prices/sizes as strings, so parsing is lossless; non-JSON frames are kept
    verbatim under 'raw_text'.
    """
    rec: Dict[str, Any] = {"recv_ts_ms": recv_ts_ms, "recv_ts": iso_utc(recv_ts_ms)}
    try:
        rec["msg"] = json.loads(raw)
    except (TypeError, ValueError):
        rec["raw_text"] = raw
    return rec


def count_events(msg: Any) -> int:
    """Number of liquidation events in an allLiquidation message (data is a list)."""
    if isinstance(msg, dict):
        data = msg.get("data")
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            return 1
    return 0


class DailyJsonlWriter:
    """Append-only JSONL writer keyed by (stream, UTC day). Flushes (and fsyncs) every line."""

    def __init__(self, out_dir: Path, fsync: bool = False):
        self.out_dir = Path(out_dir)
        self.fsync = fsync
        self._open: Dict[str, Tuple[str, IO[str]]] = {}  # stream -> (day, handle)

    def path_for(self, stream: str, ts_ms: int) -> Path:
        return self.out_dir / stream / f"{utc_day(ts_ms)}.jsonl"

    def write(self, stream: str, record: Dict[str, Any]) -> Path:
        ts_ms = int(record["recv_ts_ms"])
        day = utc_day(ts_ms)
        cur = self._open.get(stream)
        if cur is None or cur[0] != day:
            if cur is not None:
                cur[1].close()
            path = self.path_for(stream, ts_ms)
            path.parent.mkdir(parents=True, exist_ok=True)
            fh = open(path, "a", encoding="utf-8")
            self._open[stream] = (day, fh)
            cur = self._open[stream]
        fh = cur[1]
        fh.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")
        fh.flush()
        if self.fsync:
            os.fsync(fh.fileno())
        return self.path_for(stream, ts_ms)

    def close(self) -> None:
        for _, fh in self._open.values():
            try:
                fh.close()
            except OSError:
                pass
        self._open.clear()


def write_json_atomic(path: Path, obj: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def next_backoff(current: float) -> float:
    return min(BACKOFF_MAX_S, max(BACKOFF_INITIAL_S, current * 2.0))


# --------------------------------------------------------------------------- collector
class Collector:
    def __init__(
        self,
        out_dir: Path,
        symbols=DEFAULT_SYMBOLS,
        url: str = WS_URL,
        ping_interval: float = PING_INTERVAL_S,
        heartbeat_interval: float = HEARTBEAT_INTERVAL_S,
        stale_timeout: float = STALE_TIMEOUT_S,
    ):
        self.out_dir = Path(out_dir)
        self.symbols = [s.upper() for s in symbols]
        self.url = url
        self.ping_interval = ping_interval
        self.heartbeat_interval = heartbeat_interval
        self.stale_timeout = stale_timeout
        self.writer = DailyJsonlWriter(self.out_dir)
        self.stop_requested = False
        self.started_at_ms = now_ms()
        self.connected = False
        self.connect_count = 0
        self.disconnect_count = 0
        self.last_disconnect_ms: Optional[int] = None
        self.last_frame_ms: Optional[int] = None
        self.last_pong_ms: Optional[int] = None
        self.last_ack: Optional[Dict[str, Any]] = None
        self.last_msg_ms: Dict[str, Optional[int]] = {s: None for s in self.symbols}
        self.msg_count: Dict[str, int] = {s: 0 for s in self.symbols}
        self.event_count: Dict[str, int] = {s: 0 for s in self.symbols}
        self._last_hb = 0.0

    # -- bookkeeping ---------------------------------------------------------------
    def heartbeat(self, force: bool = False) -> None:
        mono = time.monotonic()
        if not force and mono - self._last_hb < self.heartbeat_interval:
            return
        self._last_hb = mono
        ts = now_ms()
        hb = {
            "updated_at": iso_utc(ts),
            "updated_at_ms": ts,
            "pid": os.getpid(),
            "url": self.url,
            "connected": self.connected,
            "connect_count": self.connect_count,
            "disconnect_count": self.disconnect_count,
            "started_at": iso_utc(self.started_at_ms),
            "last_frame_at": iso_utc(self.last_frame_ms) if self.last_frame_ms else None,
            "last_pong_at": iso_utc(self.last_pong_ms) if self.last_pong_ms else None,
            "last_subscribe_ack": self.last_ack,
            "symbols": {
                s: {
                    "last_message_at": iso_utc(self.last_msg_ms[s]) if self.last_msg_ms[s] else None,
                    "messages_since_start": self.msg_count[s],
                    "events_since_start": self.event_count[s],
                }
                for s in self.symbols
            },
        }
        try:
            self.out_dir.mkdir(parents=True, exist_ok=True)
            write_json_atomic(self.out_dir / "heartbeat.json", hb)
        except OSError as exc:  # never die because of the heartbeat
            log.error("heartbeat write failed: %s", exc)

    def handle_frame(self, raw: str, recv_ts_ms: int) -> str:
        """Persist/account one frame. Returns its kind. Pure enough to unit test."""
        self.last_frame_ms = recv_ts_ms
        kind, symbol, msg = classify_message(raw)
        if kind == "liquidation":
            sym = symbol or "UNKNOWN"
            self.writer.write(sym, make_record(raw, recv_ts_ms))
            self.last_msg_ms[sym] = recv_ts_ms
            self.msg_count[sym] = self.msg_count.get(sym, 0) + 1
            self.event_count[sym] = self.event_count.get(sym, 0) + count_events(msg)
        elif kind == "pong":
            self.last_pong_ms = recv_ts_ms
        elif kind == "subscribe":
            self.last_ack = msg
            self.writer.write(CONTROL_DIR, make_record(raw, recv_ts_ms))
            if msg.get("success"):
                log.info("subscribe ACK success=%s conn_id=%s req_id=%s ret_msg=%r",
                         msg.get("success"), msg.get("conn_id"), msg.get("req_id"), msg.get("ret_msg"))
            else:
                log.error("subscribe NACK: %s", raw[:500])
        else:
            self.writer.write(CONTROL_DIR, make_record(raw, recv_ts_ms))
            log.warning("unexpected %s frame: %s", kind, str(raw)[:300])
        return kind

    # -- network -------------------------------------------------------------------
    def _session(self, deadline: Optional[float]) -> None:
        import websocket  # websocket-client

        remaining = deadline - time.monotonic() if deadline is not None else 10.0
        if remaining <= 0:
            self.stop_requested = True
            return
        ws = websocket.create_connection(self.url, timeout=min(10.0, remaining), enable_multithread=False)
        try:
            self.connected = True
            self.connect_count += 1
            now = now_ms()
            gap = ""
            if self.last_disconnect_ms is not None:
                gap = " (gap since disconnect: %.1fs)" % ((now - self.last_disconnect_ms) / 1000.0)
            log.info("connected #%d to %s%s", self.connect_count, self.url, gap)
            topics = [TOPIC_PREFIX + s for s in self.symbols]
            ws.send(json.dumps({"req_id": "f011-sub-%d" % self.connect_count,
                                "op": "subscribe", "args": topics}))
            log.info("subscribe sent: %s", topics)
            self.heartbeat(force=True)
            ws.settimeout(1.0)
            last_ping = time.monotonic()
            last_rx = time.monotonic()
            while not self.stop_requested:
                mono = time.monotonic()
                if deadline is not None and mono >= deadline:
                    log.info("duration reached, stopping")
                    self.stop_requested = True
                    break
                if mono - last_ping >= self.ping_interval:
                    ws.send(json.dumps({"op": "ping"}))
                    last_ping = mono
                if mono - last_rx >= self.stale_timeout:
                    raise TimeoutError("no frames for %.0fs" % (mono - last_rx))
                self.heartbeat()
                try:
                    raw = ws.recv()
                except websocket.WebSocketTimeoutException:
                    continue
                if raw is None or raw == "":
                    raise ConnectionError("empty frame / connection closed")
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8", errors="replace")
                last_rx = time.monotonic()
                kind = self.handle_frame(raw, now_ms())
                if kind == "subscribe" and not self.last_ack.get("success"):
                    # Pongs do not prove that the liquidation topics are subscribed.
                    # Reconnect with backoff and subscribe again rather than staying idle.
                    raise ConnectionError("subscription rejected")
        finally:
            self.connected = False
            try:
                ws.close()
            except Exception:  # noqa: BLE001
                pass

    def run(self, duration: Optional[float] = None) -> None:
        deadline = time.monotonic() + duration if duration is not None else None
        backoff = BACKOFF_INITIAL_S
        log.info("collector start pid=%d out_dir=%s symbols=%s", os.getpid(), self.out_dir, self.symbols)
        self.heartbeat(force=True)
        try:
            while not self.stop_requested:
                t0 = time.monotonic()
                if deadline is not None and t0 >= deadline:
                    log.info("duration reached, stopping")
                    self.stop_requested = True
                    break
                try:
                    self._session(deadline)
                except Exception as exc:  # noqa: BLE001 - any failure -> reconnect
                    self.disconnect_count += 1
                    self.last_disconnect_ms = now_ms()
                    log.warning("disconnected (%s: %s)", type(exc).__name__, exc)
                if self.stop_requested:
                    break
                if time.monotonic() - t0 > 60:  # session was healthy for a while
                    backoff = BACKOFF_INITIAL_S
                if self.last_disconnect_ms is None:
                    self.last_disconnect_ms = now_ms()
                log.info("reconnecting in %.0fs", backoff)
                self.heartbeat(force=True)
                end = time.monotonic() + backoff
                if deadline is not None:
                    end = min(end, deadline)
                while time.monotonic() < end and not self.stop_requested:
                    time.sleep(max(0.0, min(0.2, end - time.monotonic())))
                backoff = next_backoff(backoff)
        finally:
            self.heartbeat(force=True)
            self.writer.close()
            log.info("collector stop (connects=%d disconnects=%d events=%s)",
                     self.connect_count, self.disconnect_count, self.event_count)


def now_ms() -> int:
    return int(time.time() * 1000)


def setup_logging(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)sZ %(levelname)s %(message)s", "%Y-%m-%dT%H:%M:%S")
    fmt.converter = time.gmtime
    log.setLevel(logging.INFO)
    log.handlers.clear()
    fh = logging.FileHandler(out_dir / "collector.log", encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    log.addHandler(fh)
    log.addHandler(sh)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR),
                    help="output root (default: <repo>/data_cache/liquidations/bybit)")
    ap.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    ap.add_argument("--url", default=WS_URL)
    ap.add_argument("--duration", type=float, default=None,
                    help="stop after N seconds (smoke tests); default: run forever")
    args = ap.parse_args(argv)
    out_dir = Path(args.out_dir).expanduser().resolve()
    setup_logging(out_dir)
    col = Collector(out_dir, symbols=[s for s in args.symbols.split(",") if s], url=args.url)

    def _stop(signum, _frame):
        log.info("signal %d received, stopping", signum)
        col.stop_requested = True

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    col.run(duration=args.duration)
    return 0


if __name__ == "__main__":
    sys.exit(main())
