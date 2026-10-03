"""
scripts/f006_funding_carry.py -- H-FUNDING-CARRY-01 T0
(spec/research/F006-hypothesis-funding-carry.md, ticket
spec/features/active/F006-funding-carry-01/ticket.md).

One rule, number_of_trials = 1: for every cached Bybit linear settlement T_k,
decide on the 60m bar opening at T_k - 2h (closes T_k - 1h). r_prev is the
latest cached settlement strictly before that close. r_prev > 0 -> short,
r_prev < 0 -> long, 0 or missing -> flat. Enter at the next bar open (T_k - 1h).
Exit by signal reversal on the bar opening at T_k + 1h. backtest_engine books
a signal_reverse exit with exit_time = that bar's index, and costs.funding_pnl
counts entry_time <= ts < exit_time, so exactly T_k is inside the hold and
T_{k+1} is not (checked below, not assumed).

Funding is the mechanism, so every run here passes the cached settlements as
`funding_events` into backtest_engine.run_backtest. A run with no events is
refused, not scored.

Modes:
  --fetch   download public /v5/market/funding/history (category linear) into
            data_cache/funding/ and write the checksum manifest. The only
            network call in this script; no OHLCV is fetched.
  (default) verify the funding checksums, run control -> carry ->
            reconciliation -> score, write output/f006_funding_carry/.

Runtime catalog registration only; strategy.py is not edited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine  # noqa: E402
import costs  # noqa: E402
import f006_family_runner as fr  # noqa: E402
import regularity  # noqa: E402
import strategy  # noqa: E402

STRATEGY_NAME = "FUNDING_CARRY_PREV_SIGN"
INTERVAL = "60"
BAR = pd.Timedelta(hours=1)
FUNDING_START = pd.Timestamp(fr.WARMUP_START)
FUNDING_END = fr.TRAIN1_END  # exclusive: last settlement strictly before
FUNDING_DIR = "data_cache/funding"
FUNDING_MANIFEST = f"{FUNDING_DIR}/manifest.json"
OUTPUT_DIR = "output/f006_funding_carry"
HYPOTHESIS_NOTE = "spec/research/F006-hypothesis-funding-carry.md"
BYBIT_URL = "https://api.bybit.com/v5/market/funding/history"
RECON_TOL = 1e-9

_CURRENT_SIGNAL: dict = {}


def _funding_path(symbol: str) -> str:
    return f"{FUNDING_DIR}/{symbol}_funding_20240126T000000Z_20250301T000000Z.csv"


def _sha256(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ---------------------------------------------------------------- fetch
def fetch_funding(symbol: str) -> pd.DataFrame:
    import requests

    start_ms = int(FUNDING_START.timestamp() * 1000)
    end_ms = int(FUNDING_END.timestamp() * 1000) - 1
    rows = {}
    while True:
        resp = requests.get(BYBIT_URL, params={
            "category": "linear", "symbol": symbol, "startTime": start_ms,
            "endTime": end_ms, "limit": 200,
        }, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("retCode") != 0:
            raise SystemExit(f"STOP: Bybit funding history error for {symbol}: {payload}")
        page = payload["result"]["list"]
        if not page:
            break
        for item in page:
            if item["symbol"] != symbol:
                raise SystemExit(f"STOP: Bybit returned {item['symbol']} for {symbol}")
            rows[int(item["fundingRateTimestamp"])] = item["fundingRate"]
        oldest = min(int(item["fundingRateTimestamp"]) for item in page)
        if oldest <= start_ms or len(page) < 200:
            break
        end_ms = oldest - 1
        time.sleep(0.2)
    df = pd.DataFrame(sorted(rows.items()), columns=["timestamp_ms", "funding_rate"])
    df = df[(df["timestamp_ms"] >= int(FUNDING_START.timestamp() * 1000))
            & (df["timestamp_ms"] < int(FUNDING_END.timestamp() * 1000))]
    df.insert(0, "timestamp", pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True))
    return df.drop(columns=["timestamp_ms"]).reset_index(drop=True)


def write_funding_cache() -> None:
    os.makedirs(FUNDING_DIR, exist_ok=True)
    manifest = {
        "source": f"{BYBIT_URL} (category=linear, public)",
        "window_start_inclusive": FUNDING_START.isoformat(),
        "window_end_exclusive": FUNDING_END.isoformat(),
        "fetched_utc": datetime.now(timezone.utc).isoformat(),
        "rate_units": "decimal settled rate per settlement (0.0001 = 1 bp), as costs.funding_payment",
        "files": {},
    }
    for symbol in fr.SYMBOLS:
        df = fetch_funding(symbol)
        path = _funding_path(symbol)
        df.to_csv(path, index=False)
        manifest["files"][symbol] = {
            "path": path, "rows": int(len(df)),
            "first": df["timestamp"].iloc[0].isoformat(),
            "last": df["timestamp"].iloc[-1].isoformat(),
            "sha256": _sha256(path),
        }
        print(f"{symbol}: {len(df)} settlements {df['timestamp'].iloc[0]} .. {df['timestamp'].iloc[-1]}")
    with open(FUNDING_MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)


def load_funding(symbol: str, manifest: dict) -> pd.DataFrame:
    entry = manifest["files"][symbol]
    path = entry["path"]
    if _sha256(path) != entry["sha256"]:
        raise SystemExit(f"STOP: funding checksum mismatch for {path}.")
    df = pd.read_csv(path, dtype={"funding_rate": str})
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["funding_rate"] = df["funding_rate"].astype(float)
    if df.empty:
        raise SystemExit(f"STOP: empty funding cache for {symbol} -- INVALID.")
    if not df["timestamp"].is_monotonic_increasing or df["timestamp"].duplicated().any():
        raise SystemExit(f"STOP: funding cache for {symbol} not strictly increasing.")
    if df["timestamp"].iloc[0] < FUNDING_START or df["timestamp"].iloc[-1] >= FUNDING_END:
        raise SystemExit(f"STOP: funding cache for {symbol} outside the Train-1 window.")
    return df


# ---------------------------------------------------------------- rule
def build_rule(bars: pd.DataFrame, funding: pd.DataFrame):
    """Signal/mask on the bar index plus the per-settlement plan (one row per T_k)."""
    idx = pd.DatetimeIndex(bars.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    present = set(idx)
    signal = pd.Series(0, index=bars.index, dtype=int)
    mask = pd.Series(False, index=bars.index, dtype=bool)
    ts = funding["timestamp"].tolist()
    rates = funding["funding_rate"].tolist()
    gaps = np.diff(np.array([t.value for t in ts])) / 3.6e12
    if len(gaps) and gaps.min() < 3:
        raise SystemExit(f"STOP: settlement spacing {gaps.min()}h < 3h; one-settlement holds would overlap.")
    plan = []
    for k, t_k in enumerate(ts):
        decision, entry, exit_bar = t_k - 2 * BAR, t_k - BAR, t_k + BAR
        decision_close = decision + BAR
        prev = [j for j in range(k + 1) if ts[j] < decision_close]
        r_prev = rates[prev[-1]] if prev else None
        direction = 0 if (r_prev is None or r_prev == 0) else (-1 if r_prev > 0 else 1)
        bars_ok = decision in present and entry in present and exit_bar in present
        plan.append({"settlement": t_k, "rate": rates[k], "r_prev": r_prev,
                     "r_prev_ts": ts[prev[-1]] if prev else None,
                     "direction": direction, "bars_ok": bars_ok})
        if direction == 0 or not bars_ok:
            continue
        pos = idx.get_loc(decision)
        signal.iloc[pos] = direction
        mask.iloc[pos] = True
        signal.iloc[idx.get_loc(exit_bar)] = -direction
    return signal, mask, pd.DataFrame(plan)


def _carry_signal(df: pd.DataFrame) -> pd.Series:
    return _CURRENT_SIGNAL["signal"].reindex(df.index).fillna(0).astype(int)


def run_arm(bars, signal, mask, symbol, funding_events):
    if not funding_events:
        raise SystemExit("STOP: funding_events empty -- a carry backtest without funding is INVALID.")
    _CURRENT_SIGNAL["signal"] = signal
    return backtest_engine.run_backtest(
        bars, STRATEGY_NAME, interval=INTERVAL, now=fr.NOW, symbol=symbol,
        initial_equity=fr.INITIAL_EQUITY, stake=fr.STAKE, max_sl_pct=fr.MAX_SL_PCT,
        activate_pct=fr.ACTIVATE_PCT, trail_pct=fr.TRAIL_PCT, cooldown_candles=fr.COOLDOWN,
        entry_regime_mask=mask, funding_events=funding_events, **fr.FIXED_PARAMS,
    )


# ---------------------------------------------------------------- checks
def reconcile(trades: pd.DataFrame, funding: pd.DataFrame) -> dict:
    """Card's 'Invalid unless funding is applied' check, on every carry hold."""
    ts = funding["timestamp"]
    n_one, n_zero_inside, n_multi, max_err, max_net_err = 0, 0, 0, 0.0, 0.0
    failures = []
    for _, t in trades.iterrows():
        entry, exit_ = pd.Timestamp(t["entry_time"]), pd.Timestamp(t["exit_time"])
        inside = funding[(ts >= entry) & (ts < exit_)]
        net_err = abs(t["net_pnl"] - (t["gross_pnl"] - t["total_costs"] + t["funding_pnl"]))
        max_net_err = max(max_net_err, net_err)
        if net_err > RECON_TOL:
            failures.append({"position_id": t["position_id"], "why": "net != gross - costs + funding"})
        if len(inside) > 1:
            n_multi += 1
            failures.append({"position_id": t["position_id"], "why": f"{len(inside)} settlements in one hold"})
        elif len(inside) == 1:
            rate = float(inside["funding_rate"].iloc[0])
            expected = costs.funding_payment(int(t["direction"]), float(t["notional"]), rate)
            err = abs(float(t["funding_pnl"]) - expected)
            max_err = max(max_err, err)
            n_one += 1
            if err > RECON_TOL:
                failures.append({"position_id": t["position_id"], "why": f"funding err {err}"})
            if rate != 0 and t["funding_pnl"] == 0:
                failures.append({"position_id": t["position_id"], "why": "non-zero settlement booked 0"})
        else:
            n_zero_inside += 1
            if t["exit_reason"] == "signal_reverse":
                failures.append({"position_id": t["position_id"], "why": "planned exit with no settlement inside"})
            if t["funding_pnl"] != 0:
                failures.append({"position_id": t["position_id"], "why": "funding booked with no settlement inside"})
    return {"holds_with_one_settlement": n_one, "holds_with_no_settlement": n_zero_inside,
            "holds_with_multiple_settlements": n_multi, "max_funding_abs_err": max_err,
            "max_net_identity_abs_err": max_net_err, "failures": failures,
            "ok": n_one > 0 and not failures}


def attribute(trades: pd.DataFrame, funding: pd.DataFrame) -> pd.DataFrame:
    """Per trade: value = funding_pnl - total_costs, on the Warsaw day of the
    settlement inside the hold, else (stop before settlement) the exit's day."""
    ts = funding["timestamp"]
    out = trades.copy()
    days = []
    for _, t in trades.iterrows():
        inside = ts[(ts >= pd.Timestamp(t["entry_time"])) & (ts < pd.Timestamp(t["exit_time"]))]
        anchor = inside.iloc[0] if len(inside) else pd.Timestamp(t["exit_time"])
        days.append(anchor.tz_convert(regularity.WARSAW_TZ).date())
    out["day"] = days
    out["value"] = out["funding_pnl"] - out["total_costs"]
    out["train1"] = [(d.year, d.month) in fr.TRAIN1_MONTHS_SET for d in days]
    return out


def reversal_days(funding: pd.DataFrame) -> set:
    sign = np.sign(funding["funding_rate"].to_numpy())
    rev = sign[1:] != sign[:-1]
    stamps = funding["timestamp"].iloc[1:][rev]
    return {s.tz_convert(regularity.WARSAW_TZ).date() for s in stamps}


# ---------------------------------------------------------------- main
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    if args.fetch:
        write_funding_cache()
        return

    t0 = time.time()
    with open(FUNDING_MANIFEST) as f:
        funding_manifest = json.load(f)
    fr.register_catalog_entries({STRATEGY_NAME: _carry_signal})
    os.makedirs(f"{OUTPUT_DIR}/summary", exist_ok=True)
    os.makedirs(f"{OUTPUT_DIR}/raw", exist_ok=True)

    loaded = {}
    for symbol in fr.SYMBOLS:
        bars, manifest = fr.load_train1(symbol, INTERVAL)
        funding = load_funding(symbol, funding_manifest)
        loaded[symbol] = (bars, manifest, funding)

    # 1. control arm: empty entry mask, funding loaded -> 0 trades, M = 0
    control = {}
    for symbol, (bars, _m, funding) in loaded.items():
        events = list(zip(funding["timestamp"], funding["funding_rate"]))
        signal, _mask, _plan = build_rule(bars, funding)
        empty = pd.Series(False, index=bars.index, dtype=bool)
        res = run_arm(bars, signal, empty, symbol, events)
        n = int(len(res.trades))
        control[symbol] = {"n_trades": n, "n_funding_events": len(events),
                           "total_net_pnl": res.metrics["total_net_pnl"],
                           "final_equity": res.metrics["final_equity"]}
        if n != 0 or res.metrics["total_net_pnl"] != 0 or res.metrics["final_equity"] != fr.INITIAL_EQUITY:
            raise SystemExit(f"STOP: control arm not flat for {symbol}: {control[symbol]}")

    # 2. carry arm + 3. reconciliation before any score
    rows, recon, all_attr = [], {}, []
    for symbol, (bars, manifest, funding) in loaded.items():
        events = list(zip(funding["timestamp"], funding["funding_rate"]))
        signal, mask, plan = build_rule(bars, funding)
        res = run_arm(bars, signal, mask, symbol, events)
        trades = res.trades
        rec = reconcile(trades, funding)
        recon[symbol] = rec
        if not rec["ok"]:
            with open(f"{OUTPUT_DIR}/summary/manifest.json", "w") as f:
                json.dump({"result": "INVALID", "reconciliation": recon}, f, indent=2, default=str)
            raise SystemExit(f"INVALID: reconciliation failed for {symbol}: {rec['failures'][:5]}")
        attr = attribute(trades, funding)
        attr.insert(0, "series", symbol)
        all_attr.append(attr)
        tr = attr[attr["train1"]]
        exits = tr["exit_reason"].value_counts().to_dict()
        rows.append({
            "symbol": symbol, "interval": INTERVAL, "strategy": STRATEGY_NAME,
            "n_settlements": int(len(funding)),
            "n_decisions_short": int((plan["direction"] == -1).sum()),
            "n_decisions_long": int((plan["direction"] == 1).sum()),
            "n_decisions_flat": int((plan["direction"] == 0).sum()),
            "n_missing_bars": int((~plan["bars_ok"] & (plan["direction"] != 0)).sum()),
            "n_trades_all": int(len(trades)),
            "n_trades_train1": int(len(tr)),
            "n_skipped_margin": int(len(res.skipped_signals)),
            "first_skipped_margin": str(res.skipped_signals[0]["time"]) if res.skipped_signals else "",
            "min_equity": round(float(res.equity_curve["equity"].min()), 6),
            "exit_signal_reverse": int(exits.get("signal_reverse", 0)),
            "exit_initial_sl": int(exits.get("initial_sl", 0)),
            "exit_other": int(sum(v for k, v in exits.items() if k not in ("signal_reverse", "initial_sl"))),
            "funding_pnl": round(float(tr["funding_pnl"].sum()), 6),
            "total_costs": round(float(tr["total_costs"].sum()), 6),
            "M": round(float(tr["value"].sum()), 6),
            "gross_pnl": round(float(tr["gross_pnl"].sum()), 6),
            "net_pnl": round(float(tr["net_pnl"].sum()), 6),
            "warmup_M": round(float(attr.loc[~attr["train1"], "value"].sum()), 6),
            "data_checksum": manifest.checksum_sha256,
        })
        trades.to_csv(f"{OUTPUT_DIR}/raw/{symbol}_{INTERVAL}_trades.csv", index=False)
        plan.to_csv(f"{OUTPUT_DIR}/raw/{symbol}_{INTERVAL}_plan.csv", index=False)

    summary = pd.DataFrame(rows)
    summary.to_csv(f"{OUTPUT_DIR}/summary/results.csv", index=False)
    mean_m = float(summary["M"].mean())

    # 4. (b): Warsaw symbol-day sums, reversal days vs green days
    attr_all = pd.concat(all_attr, ignore_index=True)
    day_vals = attr_all[attr_all["train1"]].groupby(["series", "day"])["value"].sum().reset_index()
    rev_flags = []
    for _, r in day_vals.iterrows():
        rev_flags.append(r["day"] in reversal_days(loaded[r["series"]][2]))
    day_vals["reversal_day"] = rev_flags
    day_vals.to_csv(f"{OUTPUT_DIR}/summary/day_values.csv", index=False)
    G = float(day_vals.loc[day_vals["value"] > 0, "value"].sum())
    rev_vals = day_vals.loc[day_vals["reversal_day"], "value"]
    W = float(rev_vals.min()) if len(rev_vals) else None
    worst = (day_vals.loc[rev_vals.idxmin()].to_dict() if len(rev_vals) else None)
    fired_a = mean_m <= 0
    fired_b = W is not None and W <= -G
    fired = [x for x, f in (("a", fired_a), ("b", fired_b)) if f]

    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None
    out = {
        "experiment_id": "H-FUNDING-CARRY-01",
        "script": "scripts/f006_funding_carry.py",
        "git_commit": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis_note": HYPOTHESIS_NOTE,
        "number_of_trials": 1,
        "interval": INTERVAL,
        "params": {"max_sl_pct": fr.MAX_SL_PCT, "activate_pct": fr.ACTIVATE_PCT,
                   "trail_pct": fr.TRAIL_PCT, "cooldown_candles": fr.COOLDOWN,
                   "initial_equity": fr.INITIAL_EQUITY, "stake": fr.STAKE, **fr.FIXED_PARAMS},
        "timing": {"decision_bar_open": "T_k - 2h", "entry_fill": "T_k - 1h open",
                   "exit_bar_open": "T_k + 1h (engine exit_time; fill at its close)"},
        "funding_manifest": FUNDING_MANIFEST,
        "funding_checksums": {s: e["sha256"] for s, e in funding_manifest["files"].items()},
        "control_arm": control,
        "reconciliation": recon,
        "per_series": rows,
        "mean_M": round(mean_m, 6),
        "baseline": 0.0,
        "falsifier_b": {"G_sum_positive_days": round(G, 6),
                        "W_worst_reversal_day": None if W is None else round(W, 6),
                        "worst_reversal_day": worst,
                        "n_symbol_days": int(len(day_vals)),
                        "n_reversal_symbol_days": int(day_vals["reversal_day"].sum()),
                        "n_positive_days": int((day_vals["value"] > 0).sum())},
        "fired": fired,
        "result": "FALSIFIED " + "+".join(f"({x})" for x in fired) if fired else "PASS (a),(b) not fired",
        "elapsed_seconds": round(time.time() - t0, 1),
    }
    with open(f"{OUTPUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(summary.drop(columns=["data_checksum"]).to_string(index=False))
    print(json.dumps({k: out[k] for k in ("control_arm", "mean_M", "falsifier_b", "result")}, indent=2, default=str))
    print({s: {k: v for k, v in r.items() if k != "failures"} for s, r in recon.items()})


if __name__ == "__main__":
    main()
