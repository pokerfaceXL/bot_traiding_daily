"""Offline recovery checks: no exchange connection or real sleeps."""

import json
import sys
from types import SimpleNamespace

import pytest

from forced_flow_lab import liq_collector as m


class Clock:
    def __init__(self):
        self.t = 0.0

    def monotonic(self):
        return self.t

    def sleep(self, seconds):
        self.t += seconds
        assert self.t < 100, "collector ignored duration deadline"


class SocketTimeout(Exception):
    pass


class Socket:
    def __init__(self, clock, frames):
        self.clock = clock
        self.frames = list(frames)
        self.sent = []
        self.closed = False

    def send(self, frame):
        self.sent.append(json.loads(frame))

    def settimeout(self, seconds):
        pass

    def close(self):
        self.closed = True

    def recv(self):
        self.clock.sleep(1)
        if self.frames:
            return json.dumps(self.frames.pop(0))
        raise SocketTimeout()


@pytest.fixture
def clock(monkeypatch):
    clock = Clock()
    monkeypatch.setattr(m.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(m.time, "sleep", clock.sleep)
    return clock


def install_socket(monkeypatch, connect):
    monkeypatch.setitem(sys.modules, "websocket", SimpleNamespace(
        create_connection=connect, WebSocketTimeoutException=SocketTimeout))


def test_nack_reconnects_and_resubscribes_despite_pongs(tmp_path, monkeypatch, clock):
    nack = {"op": "subscribe", "success": False, "ret_msg": "temporary failure"}
    ack = {"op": "subscribe", "success": True}
    sockets = [Socket(clock, [nack] + [{"op": "pong"}] * 90), Socket(clock, [ack])]
    attempts = []

    def connect(*args, **kwargs):
        attempts.append(clock.t)
        return sockets[len(attempts) - 1]

    install_socket(monkeypatch, connect)
    col = m.Collector(tmp_path)
    col.run(duration=30)
    assert attempts == [0, 2]
    assert col.disconnect_count == 1
    assert all(ws.closed for ws in sockets)
    for ws in sockets:
        subscriptions = [frame for frame in ws.sent if frame["op"] == "subscribe"]
        assert len(subscriptions) == 1
        assert subscriptions[0]["args"] == ["allLiquidation.BTCUSDT", "allLiquidation.ETHUSDT"]
    assert any(frame["op"] == "ping" for frame in sockets[1].sent)
    records = [json.loads(line)["msg"] for p in (tmp_path / m.CONTROL_DIR).glob("*.jsonl")
               for line in p.read_text().splitlines()]
    assert records == [nack, ack]
    hb = json.loads((tmp_path / "heartbeat.json").read_text())
    assert hb["connected"] is False
    assert hb["last_subscribe_ack"] == ack


@pytest.mark.parametrize("duration, expected_attempts", [(0, []), (2, [0, 1]), (5, [0, 1, 3])])
def test_duration_bounds_failed_connections_and_backoff(tmp_path, monkeypatch, clock, duration, expected_attempts):
    attempts = []

    def connect(*args, **kwargs):
        attempts.append(clock.t)
        assert 0 < kwargs["timeout"] <= duration - clock.t
        raise ConnectionError("offline outage")

    install_socket(monkeypatch, connect)
    col = m.Collector(tmp_path)
    col.run(duration=duration)
    assert attempts == pytest.approx(expected_attempts)
    assert clock.t == pytest.approx(duration)
    assert col.stop_requested
    assert json.loads((tmp_path / "heartbeat.json").read_text())["connected"] is False


def test_connection_timeout_cannot_trigger_retry_after_deadline(tmp_path, monkeypatch, clock):
    attempts = []

    def connect(*args, **kwargs):
        attempts.append(clock.t)
        clock.sleep(kwargs["timeout"])
        raise SocketTimeout()

    install_socket(monkeypatch, connect)
    col = m.Collector(tmp_path)
    col.run(duration=2)
    assert attempts == [0]
    assert clock.t == 2
