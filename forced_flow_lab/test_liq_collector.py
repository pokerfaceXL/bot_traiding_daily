"""
F011 · Offline tests for the liquidation collector: parsing, record format, UTC day rotation,
heartbeat. No network: uses recorded Bybit allLiquidation / subscribe-ack / pong frames.
"""

import json

from forced_flow_lab.liq_collector import (
    CONTROL_DIR,
    Collector,
    DailyJsonlWriter,
    classify_message,
    count_events,
    make_record,
    next_backoff,
    utc_day,
)

# Recorded shape of a Bybit v5 allLiquidation push (prices/sizes are strings).
SAMPLE_LIQ = (
    '{"topic":"allLiquidation.BTCUSDT","type":"snapshot","ts":1739502303204,'
    '"data":[{"T":1739502302929,"s":"BTCUSDT","S":"Sell","v":"0.003","p":"96500.10"},'
    '{"T":1739502302950,"s":"BTCUSDT","S":"Buy","v":"0.120","p":"96510.00"}]}'
)
SAMPLE_ACK = ('{"success":true,"ret_msg":"","conn_id":"abc-123","req_id":"f011-sub-1",'
              '"op":"subscribe"}')
SAMPLE_PONG = '{"success":true,"ret_msg":"pong","conn_id":"abc-123","req_id":"","op":"ping"}'

# 2025-02-13T23:59:59.900Z and 2025-02-14T00:00:00.100Z
TS_BEFORE_MIDNIGHT = 1739491199900
TS_AFTER_MIDNIGHT = 1739491200100


def test_classify_messages():
    kind, sym, msg = classify_message(SAMPLE_LIQ)
    assert kind == "liquidation" and sym == "BTCUSDT"
    assert count_events(msg) == 2
    assert msg["data"][0]["S"] == "Sell" and msg["data"][0]["p"] == "96500.10"
    assert classify_message(SAMPLE_ACK)[0] == "subscribe"
    assert classify_message(SAMPLE_PONG)[0] == "pong"
    assert classify_message("not json")[0] == "invalid"
    assert classify_message('{"foo":1}')[0] == "other"


def test_record_is_lossless():
    rec = make_record(SAMPLE_LIQ, TS_BEFORE_MIDNIGHT)
    assert rec["recv_ts_ms"] == TS_BEFORE_MIDNIGHT
    assert rec["recv_ts"] == "2025-02-13T23:59:59.900Z"
    assert rec["msg"] == json.loads(SAMPLE_LIQ)
    assert make_record("garbage", 0)["raw_text"] == "garbage"


def test_utc_day_rotation(tmp_path):
    assert utc_day(TS_BEFORE_MIDNIGHT) == "2025-02-13"
    assert utc_day(TS_AFTER_MIDNIGHT) == "2025-02-14"
    w = DailyJsonlWriter(tmp_path)
    p1 = w.write("BTCUSDT", make_record(SAMPLE_LIQ, TS_BEFORE_MIDNIGHT))
    p2 = w.write("BTCUSDT", make_record(SAMPLE_LIQ, TS_AFTER_MIDNIGHT))
    p3 = w.write("BTCUSDT", make_record(SAMPLE_LIQ, TS_AFTER_MIDNIGHT + 5))
    assert p1 == tmp_path / "BTCUSDT" / "2025-02-13.jsonl"
    assert p2 == p3 == tmp_path / "BTCUSDT" / "2025-02-14.jsonl"
    # flushed per line: readable before close
    assert len(p1.read_text().splitlines()) == 1
    assert len(p2.read_text().splitlines()) == 2
    w.close()
    # append mode: a restarted writer keeps existing lines
    w2 = DailyJsonlWriter(tmp_path)
    w2.write("BTCUSDT", make_record(SAMPLE_LIQ, TS_AFTER_MIDNIGHT + 10))
    w2.close()
    lines = p2.read_text().splitlines()
    assert len(lines) == 3
    assert json.loads(lines[-1])["msg"]["topic"] == "allLiquidation.BTCUSDT"


def test_collector_handle_frame_and_heartbeat(tmp_path):
    col = Collector(tmp_path, symbols=["BTCUSDT", "ETHUSDT"])
    assert col.handle_frame(SAMPLE_ACK, TS_BEFORE_MIDNIGHT) == "subscribe"
    assert col.handle_frame(SAMPLE_PONG, TS_BEFORE_MIDNIGHT) == "pong"
    assert col.handle_frame(SAMPLE_LIQ, TS_AFTER_MIDNIGHT) == "liquidation"
    col.writer.close()
    assert (tmp_path / CONTROL_DIR / "2025-02-13.jsonl").exists()
    assert (tmp_path / "BTCUSDT" / "2025-02-14.jsonl").exists()
    assert not (tmp_path / "ETHUSDT").exists()
    assert col.event_count == {"BTCUSDT": 2, "ETHUSDT": 0}
    col.heartbeat(force=True)
    hb = json.loads((tmp_path / "heartbeat.json").read_text())
    assert hb["symbols"]["BTCUSDT"]["events_since_start"] == 2
    assert hb["symbols"]["BTCUSDT"]["last_message_at"] == "2025-02-14T00:00:00.100Z"
    assert hb["symbols"]["ETHUSDT"]["last_message_at"] is None
    assert hb["last_subscribe_ack"]["success"] is True


def test_backoff_caps():
    b = 1.0
    seen = []
    for _ in range(10):
        b = next_backoff(b)
        seen.append(b)
    assert seen[0] == 2.0 and max(seen) == 60.0
