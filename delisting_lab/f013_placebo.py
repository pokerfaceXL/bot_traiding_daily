"""F013 Gate P — placebos (KILL), prereg §6.

(1) Time-scrambled: per event 200 pseudo-P ~ U[P − 90 d, P − 10 d] (seed 13), excluding ±10 d
    around any delisting announcement of the same base on either venue. Same entry (P' + 5 m bar
    open), exit min(entry + 72 h, eff' − 1 h) with eff' = P' + (eff − P), funding, 34 bp cost.
    p = share of the 200 placebo sample means ≥ the actual net@34 mean.
(2) Matched controls: per event, 3 same-venue USDT perps (listed ≥ 30 d before P, not in the
    delisting catalog within ±90 d, trading at P), nearest on (pre-P 30 d return rank, pre-P 24 h
    turnover rank) among candidates ∪ event (daily bars). Control short return over the identical
    window. Event − mean(control) with day-batch cluster CI.
Survivorship caveat: candidates come from today's instrument lists (names alive today).
Pass iff p < 0.05 and event − control mean > 0 with CI lower > 0.
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from delisting_lab import f013_core as C
from delisting_lab.f013_data import (EV, ROOT, _get, _ms, binance_perp, bybit_rest_klines, funding)
from delisting_lab.f013_gates import GateResult, net, row
from delisting_lab.f013_sample import CATALOG

N_PLACEBO = 200
CTRL = ROOT / "controls"
DAY = pd.Timedelta(days=1)


def draw_pseudo_p(P: pd.Timestamp, blocked: list[pd.Timestamp], rng: np.random.Generator, n=N_PLACEBO):
    """n pseudo-P uniform in [P-90d, P-10d], rejecting draws within ±10 d of a blocked time."""
    lo, hi = (P - 90 * DAY).value, (P - 10 * DAY).value
    out = []
    for _ in range(n * 50):
        x = pd.Timestamp(int(rng.uniform(lo, hi)), tz="UTC").floor("s")
        if all(abs(x - b) > 10 * DAY for b in blocked):
            out.append(x)
            if len(out) == n:
                break
    return out


def placebo_bars(ev) -> pd.DataFrame | None:
    p = EV / ev.event_id / "placebo_1m.pkl.gz"
    if p.exists():
        return pd.read_pickle(p)
    lo, hi = ev.P - 91 * DAY, ev.P - 10 * DAY + pd.Timedelta(hours=75)
    k = binance_perp(ev.symbol, lo, hi) if ev.exchange == "binance" else bybit_rest_klines(ev.symbol, lo, hi)
    if k is None:
        return None
    k = k[["open"]].astype("float32")
    k.to_pickle(p, compression="gzip")
    return k


def placebo_funding(ev):
    p = EV / ev.event_id / "placebo_funding.pkl.gz"
    if p.exists():
        return pd.read_pickle(p)
    f = funding(ev.exchange, ev.symbol, ev.P - 91 * DAY, ev.P)
    if f is not None:
        f.to_pickle(p, compression="gzip")
    return f


def time_scrambled(s: pd.DataFrame, ev_all: pd.DataFrame) -> pd.DataFrame:
    cat = pd.read_csv(CATALOG, usecols=["base", "announcement_ts"])
    cat["announcement_ts"] = pd.to_datetime(cat.announcement_ts, utc=True, format="ISO8601")
    rng = np.random.default_rng(C.SEED)
    evs = ev_all.set_index("event_id")
    mat = np.full((len(s), N_PLACEBO), np.nan)
    for i, eid in enumerate(s.event_id):
        ev = evs.loc[eid]
        ev = ev.copy()
        ev["event_id"] = eid
        blocked = [t for t in cat.loc[cat.base == ev.base, "announcement_ts"] if t != ev.announcement_ts] + [ev.P]
        pp = draw_pseudo_p(ev.P, blocked, rng)
        bars, fund = placebo_bars(ev), placebo_funding(ev)
        notice = ev.effective_ts - ev.P
        for j, p0 in enumerate(pp):
            et, ep = C.bar_open_at(bars, p0 + pd.Timedelta(minutes=5))
            if et is None:
                continue
            xt, xp = C.bar_open_at(bars, C.exit_target(et, p0 + notice))
            if xt is None:
                continue
            fb = C.funding_bp(fund, et, xt)
            mat[i, j] = C.short_bp(ep, xp) + (0.0 if not np.isfinite(fb) else fb) - C.DECISION_BP
        print(f"placebo {eid} {np.isfinite(mat[i]).sum()}/{N_PLACEBO}", flush=True)
    return pd.DataFrame(mat, index=s.event_id)


# ------------------------------------------------------------------ matched controls
def candidates(venue: str) -> pd.DataFrame:
    p = CTRL / f"{venue}_instruments.json"
    if not p.exists():
        CTRL.mkdir(parents=True, exist_ok=True)
        if venue == "binance":
            d = _get("https://fapi.binance.com/fapi/v1/exchangeInfo").json()["symbols"]
            rows = [{"symbol": x["symbol"], "base": x["baseAsset"], "onboard_ms": x["onboardDate"]} for x in d
                    if x["contractType"] == "PERPETUAL" and x["quoteAsset"] == "USDT"]
        else:
            rows, cur = [], None
            while True:
                q = {"category": "linear", "limit": 1000, **({"cursor": cur} if cur else {})}
                r = _get("https://api.bybit.com/v5/market/instruments-info", q).json()["result"]
                rows += [{"symbol": x["symbol"], "base": x["baseCoin"], "onboard_ms": int(x["launchTime"])}
                         for x in r["list"] if x["contractType"] == "LinearPerpetual" and x["quoteCoin"] == "USDT"]
                cur = r.get("nextPageCursor")
                if not cur:
                    break
        p.write_text(json.dumps(rows))
    return pd.DataFrame(json.loads(p.read_text()))


def daily(venue: str, sym: str) -> pd.DataFrame | None:
    p = CTRL / "daily" / f"{venue}_{sym}.pkl.gz"
    if p.exists():
        return pd.read_pickle(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    lo, hi = pd.Timestamp("2023-12-01", tz="UTC"), pd.Timestamp("2025-03-10", tz="UTC")
    rows = []
    if venue == "binance":
        r = _get("https://fapi.binance.com/fapi/v1/klines", {"symbol": sym, "interval": "1d", "startTime": _ms(lo),
                                                            "endTime": _ms(hi), "limit": 1000})
        rows = [(x[0], float(x[4]), float(x[7])) for x in (r.json() if r is not None else [])]
    else:
        r = _get("https://api.bybit.com/v5/market/kline", {"category": "linear", "symbol": sym, "interval": "D",
                                                           "start": _ms(lo), "end": _ms(hi), "limit": 1000})
        lst = (r.json().get("result") or {}).get("list", []) if r is not None else []
        rows = [(int(x[0]), float(x[4]), float(x[6])) for x in lst]
    time.sleep(0.08)
    df = pd.DataFrame(rows, columns=["t", "close", "turnover"])
    df.index = pd.to_datetime(df.t, unit="ms", utc=True)
    df = df.sort_index()[["close", "turnover"]]
    df.to_pickle(p, compression="gzip")
    return df


def rank_features(d: pd.DataFrame | None, P: pd.Timestamp) -> tuple[float, float]:
    """(30 d return, 24 h turnover) from daily bars fully closed before P's day."""
    if d is None or not len(d):
        return np.nan, np.nan
    day = P.floor("D")
    prev = d[d.index < day]
    if len(prev) < 31 or prev.index[-1] < day - DAY:
        return np.nan, np.nan
    return float(prev.close.iloc[-1] / prev.close.iloc[-31] - 1), float(prev.turnover.iloc[-1])


def px_at(venue: str, sym: str, t: pd.Timestamp) -> float:
    if venue == "binance":
        r = _get("https://fapi.binance.com/fapi/v1/klines", {"symbol": sym, "interval": "1m", "startTime": _ms(t),
                                                            "limit": 1})
        lst = r.json() if r is not None else []
        return float(lst[0][1]) if lst and lst[0][0] - _ms(t) <= 30 * 60_000 else np.nan
    r = _get("https://api.bybit.com/v5/market/kline", {"category": "linear", "symbol": sym, "interval": "1",
                                                       "start": _ms(t), "end": _ms(t) + 30 * 60_000, "limit": 1000})
    lst = (r.json().get("result") or {}).get("list", []) if r is not None else []
    return float(sorted(lst, key=lambda x: int(x[0]))[0][1]) if lst else np.nan


def matched_controls(s: pd.DataFrame) -> pd.DataFrame:
    p = CTRL / "matched_controls.csv"
    if p.exists():
        return pd.read_csv(p)
    cat = pd.read_csv(CATALOG, usecols=["base", "announcement_ts"])
    cat["announcement_ts"] = pd.to_datetime(cat.announcement_ts, utc=True, format="ISO8601")
    out = []
    for r in s.itertuples(index=False):
        cand = candidates(r.exchange)
        cand = cand[cand.onboard_ms < _ms(r.P - 30 * DAY)]
        bad = set(cat.loc[(cat.announcement_ts - r.P).abs() <= 90 * DAY, "base"])
        cand = cand[~cand.base.isin(bad) & (cand.symbol != r.symbol)
                    & ~cand.symbol.isin(["BTCUSDT", "ETHUSDT", "USDCUSDT", "BTCDOMUSDT", "DEFIUSDT"])]
        feats = []
        for c in cand.symbol:
            ret, to = rank_features(daily(r.exchange, c), r.P)
            if np.isfinite(ret) and np.isfinite(to) and to > 0:
                feats.append((c, ret, to))
        f = pd.DataFrame(feats, columns=["symbol", "ret30", "to24"])
        e_ret, e_to = rank_features(daily(r.exchange, r.symbol), r.P)
        f = pd.concat([f, pd.DataFrame([{"symbol": "__EVENT__", "ret30": e_ret, "to24": e_to}])], ignore_index=True)
        f["r1"], f["r2"] = f.ret30.rank(pct=True), f.to24.rank(pct=True)
        ev_row = f[f.symbol == "__EVENT__"].iloc[0]
        f = f[f.symbol != "__EVENT__"]
        f["dist"] = np.hypot(f.r1 - ev_row.r1, f.r2 - ev_row.r2) if np.isfinite(ev_row.r1 * ev_row.r2) else np.nan
        picks = []
        for c in f.sort_values("dist").symbol:
            e0, e1 = px_at(r.exchange, c, r.entry_ts), px_at(r.exchange, c, r.exit_ts)
            if np.isfinite(e0) and np.isfinite(e1):
                picks.append({"event_id": r.event_id, "control": c, "ctrl_gross": C.short_bp(e0, e1),
                              "dist": float(f.loc[f.symbol == c, "dist"].iloc[0])})
            if len(picks) == 3:
                break
        out += picks
        print(f"controls {r.event_id}: {[x['control'] for x in picks]}", flush=True)
    df = pd.DataFrame(out)
    df.to_csv(p, index=False)
    return df


def gate_p(s: pd.DataFrame, ev_all: pd.DataFrame) -> GateResult:
    s = s.copy()
    s["entry_ts"] = pd.to_datetime(s.entry_ts, utc=True)
    s["exit_ts"] = pd.to_datetime(s.exit_ts, utc=True)
    actual = float(net(s, C.DECISION_BP).mean())
    mat = time_scrambled(s, ev_all)
    means = mat.mean(axis=0, skipna=True).values
    pval = float(np.mean(means >= actual))
    ctl = matched_controls(s)
    cm = ctl.groupby("event_id").ctrl_gross.mean().rename("ctrl_gross")
    j = s.merge(cm, left_on="event_id", right_index=True, how="inner")
    diff = j.gross - j.ctrl_gross
    tb = pd.DataFrame([
        {"split": "actual net@34 mean", "mean": actual, "n": len(s)},
        {"split": "time-scrambled placebo sample means", "mean": float(np.nanmean(means)),
         "p95": float(np.nanpercentile(means, 95)), "p_one_sided": pval, "n": int(np.isfinite(mat.values).sum())},
        row("matched controls: control short gross", j.ctrl_gross, j.day_batch_cluster_id),
        row("event − control (gross)", diff, j.day_batch_cluster_id),
    ])
    mat.to_csv(C_out := (EV.parent / "placebo_matrix.csv"))
    ok = pval < 0.05 and tb.loc[3, "mean"] > 0 and tb.loc[3, "ci_lo"] > 0
    notes = [f"Placebo p = {pval:.3f} (needs < 0.05); placebo cells {int(np.isfinite(mat.values).sum())}/"
             f"{mat.size} (pre-listing / no data draws are empty).",
             f"Matched controls found for {j.event_id.nunique()}/{len(s)} events; survivorship caveat: candidate "
             "lists are today's instruments.", f"Placebo matrix cached at {C_out} (git-ignored)."]
    return GateResult("P", "KILL", "Placebos", "PASS" if ok else "FAIL", tb, notes, {"placebo_p": pval})
