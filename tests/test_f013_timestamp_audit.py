"""F013 Gate A: timestamp-audit classification rules (frozen in prereg §Gate A). No network."""
import json

import numpy as np
import pandas as pd

from delisting_lab import f013_timestamp_audit as G

H = 3600 * 1000
D = 1_720_000_000_000  # arbitrary dateTimestamp (ms)


def _ok(**kw):
    r = dict(S_ms=D, P_ms=D, eff_ms=D + 72 * H, raw_anchor_diff_ms=0.0, push_class="within_gap",
             cons_obs_ms=D, eff_reparse_diff_ms=0.0, eff_vs_instrument_min=0.0, effective_revised=False,
             body_past_dt=False)
    r.update(kw)
    return r


def test_bybit_push_classes():
    eff = D + 100 * H
    assert G.bybit_push_class(D, None, eff) == "none"
    assert G.bybit_push_class(D, D + 6 * H, eff) == "within_gap"
    assert G.bybit_push_class(D, D - 7 * H, eff) == "early_push"
    assert G.bybit_push_class(D, D + 20 * H, eff) == "ambiguous_late_push"
    assert G.bybit_push_class(D, eff, eff) == "post_event_edit"      # edit at/after delisting


def test_conservative_observable_takes_late_push_only_when_plausible():
    eff = D + 100 * H
    assert G.conservative_observable_ms(D, D + 20 * H, eff) == D + 20 * H
    assert G.conservative_observable_ms(D, D + 200 * H, eff) == D          # post-event edit ignored
    assert G.conservative_observable_ms(D, D - 7 * H, eff) == D
    assert G.conservative_observable_ms(D, D + 300_000, eff) == D + 300_000


def test_classify_pass_and_each_fail_rule():
    assert G.classify(_ok()) == ("PASS", [])
    assert G.classify(_ok(P_ms=D - 1))[0] == "FAIL"                         # F1 P before S
    assert G.classify(_ok(P_ms=np.nan))[0] == "FAIL"
    st, why = G.classify(_ok(raw_anchor_diff_ms=61_000.0))                  # F2
    assert st == "FAIL" and "F2_raw_anchor_mismatch" in why
    st, why = G.classify(_ok(push_class="ambiguous_late_push", cons_obs_ms=D + 20 * H))  # F3
    assert st == "FAIL" and "F3_ambiguous_late_push" in why
    st, why = G.classify(_ok(eff_ms=D))                                     # F4 no notice
    assert st == "FAIL" and "F4_no_positive_notice" in why


def test_f3_not_triggered_when_primary_already_at_late_push():
    st, why = G.classify(_ok(P_ms=D + 20 * H, push_class="ambiguous_late_push", cons_obs_ms=D + 20 * H))
    assert "F3_ambiguous_late_push" not in why and st != "FAIL"


def test_classify_warn_rules():
    assert G.classify(_ok(raw_anchor_diff_ms=np.nan))[1] == ["W6_raw_source_unavailable"]
    assert "W1_body_effective_mismatch" in G.classify(_ok(eff_reparse_diff_ms=120_000.0))[1]
    assert "W1_body_effective_unparsed" in G.classify(_ok(eff_reparse_diff_ms=np.nan))[1]
    assert "W2_instrument_delivery_mismatch" in G.classify(_ok(eff_vs_instrument_min=5.0))[1]
    assert "W3_effective_revised" in G.classify(_ok(effective_revised=True))[1]
    assert "W4_publishTime_post_event_edit" in G.classify(_ok(push_class="post_event_edit"))[1]
    st, why = G.classify(_ok(P_ms=D + 16 * 60_000))
    assert st == "WARN" and why == ["W5_observability_lag_gt_15m"]
    assert G.classify(_ok(P_ms=D + 15 * 60_000))[0] == "PASS"               # boundary: 15 min is fine
    assert "W8_body_datetime_before_announcement" in G.classify(_ok(body_past_dt=True))[1]


def test_gate_a_verdict_thresholds():
    def df(x_pass, x_fail, y_pass, y_fail):
        return pd.DataFrame({"exchange": ["x"] * (x_pass + x_fail) + ["y"] * (y_pass + y_fail),
                             "gate_a_status": ["PASS"] * x_pass + ["FAIL"] * x_fail
                             + ["WARN"] * y_pass + ["FAIL"] * y_fail})
    assert G.gate_a_verdict(df(16, 2, 10, 0))[0] == "PASS"                # 92.9% usable, worst venue 11%
    assert G.gate_a_verdict(df(17, 0, 0, 3))[0] == "FAIL"                 # 85% usable but venue y 100% FAIL
    assert G.gate_a_verdict(df(8, 2, 8, 2))[0] == "FAIL"                  # 80% usable < 85%
    assert G.gate_a_verdict(df(17, 3, 3, 0))[0] == "PASS"                 # exactly 85% / 15% boundary


def _tiny_catalog():
    """Two-event catalog in the C02 column layout (one Binance perp, one Bybit perp with late push)."""
    base = dict(contract_type="linear_perp", category="perp_delist", effective_revised=False,
                eff_vs_instrument_min=0.0, day_batch_cluster_id="B1")
    bn = dict(base, event_id="BINANCE-1-AAAUSDT", exchange="binance", symbol="AAAUSDT", base="AAA",
              announcement_cluster_id="BINANCE-1", source_id="code1", source_url="u1",
              announcement_ts="2024-06-03 03:00:00+00:00", first_publicly_observable_ts="2024-06-03 03:00:00+00:00",
              effective_ts="2024-06-10 09:00:00+00:00", effective_ts_announced="2024-06-10 09:00:00+00:00",
              ts_flag=np.nan, bybit_dateTimestamp=np.nan, bybit_publishTime=np.nan)
    d = pd.Timestamp("2024-08-08 05:59:00", tz="UTC").value // 10**6
    by = dict(base, event_id="BYBIT-1-BBBUSDT", exchange="bybit", symbol="BBBUSDT", base="BBB",
              announcement_cluster_id="BYBIT-art1", source_id="BYBIT-art1", source_url="https://x/bbb-art1/",
              announcement_ts="2024-08-08 05:59:00+00:00", first_publicly_observable_ts="2024-08-08 05:59:00+00:00",
              effective_ts="2024-08-15 08:00:00+00:00", effective_ts_announced="2024-08-15 08:00:00+00:00",
              ts_flag="publishTime_gap_26.0h_ignored", bybit_dateTimestamp=float(d),
              bybit_publishTime=float(d + 26 * H))
    return pd.DataFrame([bn, by])


def test_build_audit_offline_fixture(tmp_path):
    rel = pd.Timestamp("2024-06-03 03:00", tz="UTC").value // 10**6
    (tmp_path / "binance_detail.json").write_text(json.dumps({"code1": {
        "title": "Binance Futures Will Delist USDⓈ-M AAAUSDT Perpetual Contract", "publishDate": rel,
        "text": "Binance Futures will close all positions and conduct an automatic settlement on the "
                "USDⓈ-M AAAUSDT Perpetual Contract at 2024-06-10 09:00 (UTC). Thereafter"}}))
    (tmp_path / "bybit_pages.json").write_text(json.dumps({"https://x/bbb-art1/": {
        "title": "Delisting of BBBUSDT Perpetual Contract", "date": "2024-08-08T05:59:00Z",
        "description": "Bybit will delist the BBBUSDT Perpetual Contract at 8AM UTC on Aug 15, 2024.",
        "text": "Bybit will delist the BBBUSDT Perpetual Contract at 8AM UTC on Aug 15, 2024."}}))
    a = G.build_audit(_tiny_catalog(), raw_dir=tmp_path).set_index("event_id")
    assert a.loc["BINANCE-1-AAAUSDT", "gate_a_status"] == "PASS"
    assert a.loc["BINANCE-1-AAAUSDT", "eff_reparse_diff_ms"] == 0
    b = a.loc["BYBIT-1-BBBUSDT"]
    assert b.gate_a_status == "FAIL" and b.gate_a_reasons.startswith("F3_ambiguous_late_push")
    assert b.raw_anchor_diff_ms == 0 and b.eff_reparse_diff_ms == 0
    assert np.isnan(b.raw_bybit_api_dateTimestamp)                         # no API file → NaN, not a crash
