"""F013 per-event metrics on the discovery sample (reads data_cache/f013/events/*).

One row per event: latency-ladder entries (Gate B), primary trade (P + 5 m → min(entry + 72 h,
eff - 1 h)), eligibility (Gate C), funding (E), fixed horizons (F), beta / abnormal (G),
spot leg (H), liquidity (K), pre-trend (Q). Nothing here selects or optimises anything.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from delisting_lab import f013_core as C
from delisting_lab.catalog import parse_datetimes
from delisting_lab.f013_data import EV, btc_1m, load

RAW = Path("data_cache/f013/raw")
M = pd.Timedelta(minutes=1)
HR = pd.Timedelta(hours=1)
TICK_LAT = {"10s": 10, "30s": 30, "60s": 60}
BAR_LAT = {"1m": 1, "5m": 5, "15m": 15}
FIXED_H = (1, 4, 12, 24, 72)


def article_texts() -> dict:
    out = {}
    b = RAW / "binance_detail.json"
    if b.exists():
        out.update({k: v.get("text", "") for k, v in json.loads(b.read_text()).items()})
    y = RAW / "bybit_pages.json"
    if y.exists():
        out.update({k: (v.get("description") or "") + "\n" + (v.get("text") or "")
                    for k, v in json.loads(y.read_text()).items()})
    return out


def _trade(bars, fund, entry_ts, entry_px, eff, target=None):
    """Exit per primary rule (or a fixed target); returns gross/funding bp and exit ts."""
    tgt = C.exit_target(entry_ts, eff) if target is None else target
    xt, xp = C.bar_open_at(bars, tgt)
    return {"exit_ts": xt, "gross": C.short_bp(entry_px, xp),
            "fund": C.funding_bp(fund, entry_ts, xt) if xt is not None else np.nan}


def bar_has_trade(bars, t) -> bool:
    if bars is None or t not in bars.index:
        return False
    r = bars.loc[t]
    c = r.get("count", np.nan)
    return bool(r.quote_volume > 0) if not np.isfinite(c) else bool(c > 0)


def event_row(ev, btc: pd.DataFrame, texts: dict) -> dict:
    eid, P, eff = ev.event_id, ev.P, ev.effective_ts
    r = {"event_id": eid}
    bars, ticks, fund = load(eid, "perp_1m"), load(eid, "ticks"), load(eid, "funding")
    h1, spot = load(eid, "perp_1h"), load(eid, "spot_1m")
    if bars is not None:
        bars = bars[bars.index < eff]  # nothing at/after settlement
    r["has_perp_1m"] = bars is not None and len(bars) > 0
    r["has_ticks"] = ticks is not None and len(ticks) > 0
    r["has_funding"] = fund is not None and len(fund) > 0
    r["has_spot"] = spot is not None and len(spot) > 0
    info = EV / eid / "done.json"
    r["spot_venue"] = json.loads(info.read_text()).get("spot_venue") if info.exists() else None
    r["notice_h"] = (eff - P).total_seconds() / 3600
    r["notice_bin"] = C.notice_bin(r["notice_h"])

    # ---- latency ladder (Gate B); primary = 5m
    for k, s in TICK_LAT.items():
        et, ep = C.first_tick_at(ticks, P + pd.Timedelta(seconds=s))
        r[f"entry_lag_s_{k}"] = (et - P).total_seconds() if et is not None else np.nan
        t = _trade(bars, fund, et, ep, eff) if et is not None else {"gross": np.nan, "fund": np.nan}
        r[f"gross_{k}"], r[f"fund_{k}"] = t["gross"], t["fund"]
    for k, mins in BAR_LAT.items():
        et, ep = C.bar_open_at(bars, P + mins * M)
        r[f"entry_lag_s_{k}"] = (et - P).total_seconds() if et is not None else np.nan
        if et is None:
            r[f"gross_{k}"] = r[f"fund_{k}"] = np.nan
            continue
        t = _trade(bars, fund, et, ep, eff)
        r[f"gross_{k}"], r[f"fund_{k}"] = t["gross"], t["fund"]
        if k == "5m":
            r.update(entry_ts=et, entry_px=ep, exit_ts=t["exit_ts"],
                     exit_px=C.bar_open_at(bars, t["exit_ts"])[1] if t["exit_ts"] is not None else np.nan)
    et = r.get("entry_ts")
    r["insufficient_notice"] = et is None or (eff - HR - et) < HR
    if et is None:
        return r
    xt = r["exit_ts"]
    r["hold_h"] = (xt - et).total_seconds() / 3600 if xt is not None else np.nan
    r["gross"], r["fund"] = r["gross_5m"], r["fund_5m"]

    # ---- Gate C eligibility
    traded = bar_has_trade(bars, et)
    if not traded and ticks is not None and len(ticks):
        traded = bool(((ticks.ts >= et) & (ticks.ts < et + M)).any())
    key = ev.source_url if ev.exchange == "bybit" else ev.source_id
    rt = C.restriction_times(texts.get(key, ""), parse_datetimes)
    restricted = any(t <= et.value // 10**6 for t in rt)
    r.update(trade_in_entry_minute=traded, restricted_before_entry=restricted,
             restriction_times=";".join(str(pd.Timestamp(t, unit="ms", tz="UTC")) for t in rt),
             eligible=bool(traded and not restricted))

    # ---- Gate F fixed horizons
    for h in FIXED_H:
        tgt = et + h * HR
        if tgt > eff - HR:
            r[f"gross_h{h}"] = r[f"fund_h{h}"] = np.nan
            continue
        t = _trade(bars, fund, et, r["entry_px"], eff, target=tgt)
        r[f"gross_h{h}"], r[f"fund_h{h}"] = t["gross"], t["fund"]
    t = _trade(bars, fund, et, r["entry_px"], eff, target=eff - HR)
    r["gross_heff"], r["fund_heff"] = t["gross"], t["fund"]

    # ---- Gate G beta + abnormal
    beta, nb = 1.0, 0
    if h1 is not None and len(h1):
        c = h1.close[(h1.index >= P - pd.Timedelta(days=20)) & (h1.index < P - pd.Timedelta(hours=24))]
        bh = btc.close.resample("1h").last()
        j = pd.concat([np.log(c).diff().rename("y"), np.log(bh).diff().rename("x")], axis=1, join="inner").dropna()
        beta, nb = C.ols_beta(j.y.values, j.x.values)
    r["beta"], r["beta_n"] = beta, nb
    if xt is not None:
        _, b0 = C.bar_open_at(btc, et)
        _, b1 = C.bar_open_at(btc, xt)
        r["btc_ret_bp"] = (b1 / b0 - 1) * 1e4
        r["abn_gross"] = r["gross"] + beta * r["btc_ret_bp"]  # -(r_perp - beta r_btc)

    # ---- Gate H spot leg over the identical window
    if spot is not None and xt is not None:
        s0t, s0 = C.bar_open_at(spot, et, max_wait=pd.Timedelta(minutes=5))
        s1t, s1 = C.bar_open_at(spot, xt, max_wait=pd.Timedelta(minutes=5))
        r["spot_gross"] = C.short_bp(s0, s1)

    # ---- Gate K liquidity over [P - 24h, P)
    w = bars[(bars.index >= P - 24 * HR) & (bars.index < P.floor("1min"))] if bars is not None else None
    if w is not None:
        r["turnover_24h"] = float(w.quote_volume.sum())
        r["zero_vol_share_24h"] = 1.0 - float((w.quote_volume > 0).sum()) / 1440.0

    # ---- Gate Q pre-trend (raw returns, causal closes)
    def ret(a, b):
        pa, pb = C.close_before(bars, a), C.close_before(bars, b)
        return (pb / pa - 1) * 1e4 if np.isfinite(pa) and np.isfinite(pb) else np.nan
    r["pre_72h_5m"] = ret(P - 72 * HR, P - 5 * M)
    r["pre_24h_5m"] = ret(P - 24 * HR, P - 5 * M)
    r["pre_1h_0"] = ret(P - HR, P)
    return r


EVENT_COLS = ["event_id", "exchange", "symbol", "base", "delist_type", "primary_type", "in_primary_universe",
              "gate_a_status", "P", "effective_ts", "announcement_cluster_id", "day_batch_cluster_id",
              "token_cluster_id", "follower_event"]


def build_table(events: pd.DataFrame) -> pd.DataFrame:
    btc = btc_1m()
    texts = article_texts()
    rows = [event_row(ev, btc, texts) for ev in events.itertuples(index=False)]
    return events[EVENT_COLS].merge(pd.DataFrame(rows), on="event_id", how="left")
