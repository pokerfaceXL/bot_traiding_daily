"""Safety and aggregation checks without network or large disk writes."""
import csv
import fcntl
import gzip
import io
import json
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from forced_flow_lab import reduce_trades_5m as r

DAY = date(2024, 1, 26)
EPOCH = 1706227200


def archive(symbol="BTCUSDT", rows=None):
    if rows is None:
        rows = [(EPOCH, "Buy", 2), (EPOCH + 299.9999, "Sell", 1),
                (EPOCH + 300, "Sell", 4), (EPOCH + 86399.9999, "Buy", 3)]
    text = "timestamp,symbol,side,size,price\n" + "".join(
        f"{ts},{symbol},{side},{size},100\n" for ts, side, size in rows)
    return gzip.compress(text.encode())


class Session:
    def __init__(self, chunks, callback=lambda: None):
        self.chunks = chunks
        self.calls = []
        self.callback = callback

    def get(self, url, **kwargs):
        self.calls.append(url)
        self.callback()
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        for chunk in self.chunks:
            if isinstance(chunk, Exception):
                raise chunk
            yield chunk


def run(root, session, end=DAY + timedelta(days=1), symbols=("BTCUSDT",)):
    events = []
    r.run(root, symbols, DAY, end, session, events.append)
    return [json.loads(event) for event in events]


@pytest.fixture(autouse=True)
def ample_disk(monkeypatch):
    # Unit tests must not depend on the host actually having 10 GiB free.
    monkeypatch.setattr(r.shutil, "disk_usage", lambda _: SimpleNamespace(free=100 * 1024**3))


def test_guard_stops_before_any_network_or_raw_write(tmp_path, monkeypatch):
    monkeypatch.setattr(r.shutil, "disk_usage", lambda _: SimpleNamespace(free=r.MIN_FREE_BYTES - 1))
    session = Session([archive()])
    with pytest.raises(r.LowDiskSpace):
        run(tmp_path, session)
    assert session.calls == []
    assert not list(tmp_path.glob("*.csv"))
    assert not (tmp_path / ".raw-day.csv.gz").exists()


def test_guard_checks_chunks_and_cleans_partial_raw(tmp_path, monkeypatch):
    calls = []

    def usage(_):
        calls.append(1)
        # pre-day, pre-chunk, post-chunk, then reject the second chunk
        if len(calls) == 4:
            assert (tmp_path / ".raw-day.csv.gz").read_bytes() == b"first"
            return SimpleNamespace(free=r.MIN_FREE_BYTES + r.WRITE_HEADROOM + 1)
        return SimpleNamespace(free=100 * 1024**3)

    monkeypatch.setattr(r.shutil, "disk_usage", usage)
    with pytest.raises(r.LowDiskSpace):
        run(tmp_path, Session([b"first", b"second"]))
    assert len(calls) == 4
    assert not (tmp_path / ".raw-day.csv.gz").exists()
    assert not list(tmp_path.glob("*.manifest.json"))


def test_boundary_flow_gaps_and_checksum_resume(tmp_path):
    source = archive()
    session = Session([source])
    assert run(tmp_path, session)[0]["status"] == "written"
    output, manifest = r.day_paths(tmp_path, "BTCUSDT", DAY)
    rows = list(csv.DictReader(io.StringIO(output.read_text())))
    assert len(rows) == 288
    assert rows[0]["timestamp"] == "2024-01-26T00:00:00+00:00"
    assert rows[0]["available_at"] == "2024-01-26T00:05:00+00:00"
    assert float(rows[0]["ofi"]) == pytest.approx(1 / 3)
    assert int(rows[0]["trade_count"]) == 2
    assert float(rows[1]["delta_cvd"]) == -4
    assert float(rows[1]["cvd_day"]) == -3
    assert float(rows[-1]["cvd_day"]) == 0
    assert rows[-1]["available_at"] == "2024-01-27T00:00:00+00:00"
    assert rows[2]["trade_count"] == "0"
    assert rows[2]["ofi"] == "0.0"
    meta = json.loads(manifest.read_text())
    assert len(meta["empty_buckets"]) == 285
    assert meta["trade_count"] == 4
    assert meta["source_sha256"] == r.hashlib.sha256(source).hexdigest()
    assert meta["minimum_observed_free_bytes"] >= r.MIN_FREE_BYTES
    assert run(tmp_path, session)[0]["status"] == "verified-skip"
    assert len(session.calls) == 1
    output.write_text("corrupt")
    assert run(tmp_path, session)[0]["status"] == "written"
    assert len(session.calls) == 2
    assert r.verified(tmp_path, "BTCUSDT", DAY)
    assert not (tmp_path / ".raw-day.csv.gz").exists()


def test_network_failure_recovery_and_single_raw_day(tmp_path):
    with pytest.raises(r.requests.ConnectionError):
        run(tmp_path, Session([b"partial", r.requests.ConnectionError("dropped")]))
    assert not (tmp_path / ".raw-day.csv.gz").exists()
    # Simulate a killed process; stale raw and output partials cannot accumulate.
    (tmp_path / ".raw-day.csv.gz").write_bytes(b"stale")
    (tmp_path / "BTCUSDT_2024-01-26.csv.part").write_bytes(b"stale")
    checks = []

    class BothSymbols(Session):
        def get(self, url, **kwargs):
            assert not (tmp_path / ".raw-day.csv.gz").exists()
            assert not list(tmp_path.glob("*.part"))
            checks.append(url)
            self.chunks = [archive("ETHUSDT" if "ETHUSDT" in url else "BTCUSDT")]
            return super().get(url, **kwargs)

    run(tmp_path, BothSymbols([]), symbols=r.SYMBOLS)
    assert len(checks) == 2
    assert all(r.verified(tmp_path, symbol, DAY) for symbol in r.SYMBOLS)
    assert not (tmp_path / ".raw-day.csv.gz").exists()


def test_low_space_after_completed_day_preserves_resume(tmp_path, monkeypatch):
    session = Session([archive()])

    def after_first_day(_):
        monkeypatch.setattr(r.shutil, "disk_usage", lambda _: SimpleNamespace(free=r.MIN_FREE_BYTES - 1))

    with pytest.raises(r.LowDiskSpace):
        r.run(tmp_path, r.SYMBOLS, DAY, DAY + timedelta(days=1), session, after_first_day)
    assert len(session.calls) == 1
    assert r.verified(tmp_path, "BTCUSDT", DAY)
    assert not r.verified(tmp_path, "ETHUSDT", DAY)
    assert not (tmp_path / ".raw-day.csv.gz").exists()


def test_lock_blocks_competing_reducer_without_deleting_raw(tmp_path):
    with (tmp_path / ".reducer.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        raw = tmp_path / ".raw-day.csv.gz"
        raw.write_bytes(b"owned by other process")
        with pytest.raises(RuntimeError, match="Another reducer"):
            run(tmp_path, Session([archive()]))
        assert raw.read_bytes() == b"owned by other process"


@pytest.mark.parametrize("rows", [[], [(EPOCH - 0.01, "Buy", 1)],
    [(EPOCH + 86400, "Buy", 1)], [(EPOCH, "Unknown", 1)],
    [(EPOCH, "Buy", -1)], [(EPOCH, "Buy", "nan")], [("inf", "Buy", 1)]])
def test_invalid_archives_not_committed(tmp_path, rows):
    with pytest.raises(ValueError):
        run(tmp_path, Session([archive(rows=rows)]))
    assert not r.verified(tmp_path, "BTCUSDT", DAY)
    assert not (tmp_path / ".raw-day.csv.gz").exists()


def test_truncated_gzip_is_not_published(tmp_path):
    with pytest.raises(EOFError):
        run(tmp_path, Session([archive()[:-8]]))
    assert not list(tmp_path.glob("*.manifest.json"))
    assert not (tmp_path / ".raw-day.csv.gz").exists()


def test_manifest_interruption_rebuilds_day(tmp_path, monkeypatch):
    original = r.atomic_write

    def interrupted(path, payload, guard):
        if path.name.endswith(".manifest.json"):
            raise OSError("interrupted publication")
        original(path, payload, guard)

    monkeypatch.setattr(r, "atomic_write", interrupted)
    with pytest.raises(OSError):
        run(tmp_path, Session([archive()]))
    assert not r.verified(tmp_path, "BTCUSDT", DAY)
    assert not (tmp_path / ".raw-day.csv.gz").exists()
    monkeypatch.setattr(r, "atomic_write", original)
    assert run(tmp_path, Session([archive()]))[0]["status"] == "written"


def test_sub_float_precision_timestamp_stays_in_previous_bar(tmp_path):
    raw = tmp_path / "test.gz"
    raw.write_bytes(archive(rows=[("1706227499.99999999", "Buy", 1),
                                 ("1706227500", "Sell", 2)]))
    payload, _ = r.reduce_raw(raw, "BTCUSDT", DAY)
    rows = list(csv.DictReader(io.StringIO(payload.decode())))
    assert int(rows[0]["trade_count"]) == 1
    assert float(rows[0]["taker_buy_vol"]) == 1
    assert int(rows[1]["trade_count"]) == 1
    assert float(rows[1]["taker_sell_vol"]) == 2


def test_reduction_is_prefix_causal(tmp_path):
    raw = tmp_path / "test.gz"
    raw.write_bytes(archive())
    before, _ = r.reduce_raw(raw, "BTCUSDT", DAY)
    raw.write_bytes(archive(rows=[(EPOCH, "Buy", 2), (EPOCH + 299.9999, "Sell", 1),
                                  (EPOCH + 300, "Buy", 999999)]))
    after, _ = r.reduce_raw(raw, "BTCUSDT", DAY)
    assert before.splitlines()[:2] == after.splitlines()[:2]
    assert before.splitlines()[2] != after.splitlines()[2]
