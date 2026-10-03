"""
scripts/f006_noncandle_oi_fade.py -- H-NONCANDLE-SLEEVE-01 T0
(spec/research/F006-hypothesis-noncandle-sleeve.md, ticket
spec/features/active/F006-noncandle-sleeve-01/ticket.md).

One rule, number_of_trials = 1. Position for hour t is the opposite sign of
the prior hour's cached Bybit linear open-interest change:
  -1 if OI[t-1] > OI[t-2], +1 if OI[t-1] < OI[t-2], 0 if equal or missing.

backtest_engine queues an entry on bar i's signal and fills it at bar i+1's
open, and closes on an opposite signal at bar i's close. So the signal on the
bar opening at s is -sign(OI[s] - OI[s-1]): it fills/rebalances at the open
of t = s + 1h with exactly OI[t-1], OI[t-2]. OI[s] is the snapshot stamped
s, known by that bar's close. Candles only supply prices to the engine.

The engine has no "go flat" command (signal 0 keeps an open position), so the
script refuses to score if a flat hour occurs while the rule would already be
in a position. With the cache (no ties, no gaps) flat hours are only the
first two bars, before any position exists.

Before any score: control (empty mask) is flat; entries change when OI is
shuffled or zeroed with candles fixed; a run without OI refuses.

Runtime catalog registration only; strategy.py is not edited.
"""
from __future__ import annotations

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
import f006_family_runner as fr  # noqa: E402
import regularity  # noqa: E402

STRATEGY_NAME = "OI_FADE_PREV_HOUR"
INTERVAL = "60"
OI_DIR = "data_cache/open_interest"
OI_MANIFEST = f"{OI_DIR}/manifest.json"
OUTPUT_DIR = "output/f006_noncandle_oi_fade"
HYPOTHESIS_NOTE = "spec/research/F006-hypothesis-noncandle-sleeve.md"
SHARED_LOSING_MONTHS = {(2024, 3), (2024, 4), (2024, 5), (2024, 8), (2024, 9), (2024, 12)}
SHUFFLE_SEED = 20261004

_CURRENT_SIGNAL: dict = {}


class OIMissing(Exception):
    pass


def _sha256(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_oi(symbol: str, manifest: dict) -> pd.Series:
    entry = manifest["files"][symbol]
    path = entry["path"]
    if _sha256(path) != entry["sha256"]:
        raise SystemExit(f"STOP: OI checksum mismatch for {path}.")
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    if df.empty:
        raise SystemExit(f"STOP: empty OI cache for {symbol} -- INVALID.")
    if not df["timestamp"].is_monotonic_increasing or df["timestamp"].duplicated().any():
        raise SystemExit(f"STOP: OI cache for {symbol} not strictly increasing.")
    if df["timestamp"].iloc[0] < pd.Timestamp(fr.WARMUP_START) or df["timestamp"].iloc[-1] >= fr.TRAIN1_END:
        raise SystemExit(f"STOP: OI cache for {symbol} outside the Train-1 window.")
    return df.set_index("timestamp")["open_interest"].astype(float)


# ---------------------------------------------------------------- rule
def build_signal(bars: pd.DataFrame, oi) -> pd.Series:
    """Signal on the bar opening at s = position held over hour s + 1h."""
    if oi is None or len(oi) == 0 or not np.isfinite(np.asarray(oi, dtype=float)).any():
        raise OIMissing("no OI series -- refusing to build a signal (INVALID, not scored)")
    idx = pd.DatetimeIndex(bars.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    hours = pd.date_range(idx[0], idx[-1], freq="1h")
    o = oi.reindex(hours)  # OI at every hour stamp; missing -> NaN -> flat
    d = (o - o.shift(1)).to_numpy()
    sig = np.where(np.isnan(d), 0, -np.sign(d)).astype(int)
    out = pd.Series(sig, index=hours).reindex(idx).fillna(0).astype(int)
    out.index = bars.index
    return out


def _signal_fn(df: pd.DataFrame) -> pd.Series:
    return _CURRENT_SIGNAL["signal"].reindex(df.index).fillna(0).astype(int)


def run_arm(bars, signal, mask, symbol):
    _CURRENT_SIGNAL["signal"] = signal
    return backtest_engine.run_backtest(
        bars, STRATEGY_NAME, interval=INTERVAL, now=fr.NOW, symbol=symbol,
        initial_equity=fr.INITIAL_EQUITY, stake=fr.STAKE, max_sl_pct=fr.MAX_SL_PCT,
        activate_pct=fr.ACTIVATE_PCT, trail_pct=fr.TRAIL_PCT, cooldown_candles=fr.COOLDOWN,
        entry_regime_mask=mask, **fr.FIXED_PARAMS,
    )


def flat_inside_hold(signal: pd.Series) -> int:
    """Zero signals after the first non-zero one: hours the rule says flat but
    the engine would keep holding."""
    nz = np.flatnonzero(signal.to_numpy() != 0)
    if not len(nz):
        return 0
    return int((signal.to_numpy()[nz[0]:] == 0).sum())


def entries(trades: pd.DataFrame) -> list:
    if trades.empty:
        return []
    return list(zip(trades["entry_time"].astype(str), trades["direction"].astype(int)))


def warsaw_month(ts) -> tuple:
    t = pd.Timestamp(ts)
    if t.tz is None:
        t = t.tz_localize("UTC")
    t = t.tz_convert(regularity.WARSAW_TZ)
    return (t.year, t.month)


# ---------------------------------------------------------------- main
def main() -> None:
    t0 = time.time()
    with open(OI_MANIFEST) as f:
        oi_manifest = json.load(f)
    fr.register_catalog_entries({STRATEGY_NAME: _signal_fn})
    os.makedirs(f"{OUTPUT_DIR}/summary", exist_ok=True)
    os.makedirs(f"{OUTPUT_DIR}/raw", exist_ok=True)

    loaded = {}
    for symbol in fr.SYMBOLS:
        bars, manifest = fr.load_train1(symbol, INTERVAL)
        oi = load_oi(symbol, oi_manifest)
        loaded[symbol] = (bars, manifest, oi)

    # 1. control arm: empty entry mask -> 0 trades, net 0
    control = {}
    for symbol, (bars, _m, oi) in loaded.items():
        signal = build_signal(bars, oi)
        res = run_arm(bars, signal, pd.Series(False, index=bars.index, dtype=bool), symbol)
        n = int(len(res.trades))
        control[symbol] = {"n_trades": n, "total_costs": 0.0 if n == 0 else float(res.trades["total_costs"].sum()),
                           "total_net_pnl": res.metrics["total_net_pnl"],
                           "final_equity": res.metrics["final_equity"]}
        if n != 0 or res.metrics["total_net_pnl"] != 0 or res.metrics["final_equity"] != fr.INITIAL_EQUITY:
            raise SystemExit(f"STOP: control arm not flat for {symbol}: {control[symbol]}")

    # 2. OI-consumption checks (candles fixed) before any score
    consumption, results = {}, {}
    rng = np.random.default_rng(SHUFFLE_SEED)
    for symbol, (bars, _m, oi) in loaded.items():
        signal = build_signal(bars, oi)
        mask = pd.Series(True, index=bars.index, dtype=bool)
        flat_in = flat_inside_hold(signal)
        if flat_in:
            raise SystemExit(f"STOP: {symbol} has {flat_in} flat hours after the first position; "
                             "the engine cannot go flat on signal 0, so this run would not be the frozen rule.")
        res = run_arm(bars, signal, mask, symbol)
        real = entries(res.trades)

        shuffled = pd.Series(rng.permutation(oi.to_numpy()), index=oi.index)
        sig_sh = build_signal(bars, shuffled)
        ent_sh = entries(run_arm(bars, sig_sh, mask, symbol).trades)
        sig_zero = build_signal(bars, oi * 0.0)
        ent_zero = entries(run_arm(bars, sig_zero, mask, symbol).trades)
        try:
            build_signal(bars, None)
            omitted = "SCORED"
        except OIMissing as exc:
            omitted = f"refused: {exc}"
        try:
            build_signal(bars, oi.iloc[0:0])
            emptied = "SCORED"
        except OIMissing as exc:
            emptied = f"refused: {exc}"

        c = {
            "n_entries_real": len(real),
            "n_entries_shuffled": len(ent_sh),
            "shuffled_entries_differ": ent_sh != real,
            "shuffled_signal_bars_changed": int((sig_sh != signal).sum()),
            "n_entries_zeroed": len(ent_zero),
            "zeroed_entries_differ": ent_zero != real,
            "zeroed_signal_bars_changed": int((sig_zero != signal).sum()),
            "omitted_oi": omitted,
            "empty_oi": emptied,
            "n_signal_long": int((signal == 1).sum()),
            "n_signal_short": int((signal == -1).sum()),
            "n_signal_flat": int((signal == 0).sum()),
        }
        c["ok"] = (c["shuffled_entries_differ"] and c["zeroed_entries_differ"]
                   and omitted.startswith("refused") and emptied.startswith("refused") and len(real) > 0)
        consumption[symbol] = c
        results[symbol] = (signal, res)
    if not all(c["ok"] for c in consumption.values()):
        with open(f"{OUTPUT_DIR}/summary/manifest.json", "w") as f:
            json.dump({"result": "INVALID", "oi_consumption": consumption}, f, indent=2, default=str)
        raise SystemExit(f"INVALID: OI not consumed: {consumption}")

    # 3. score: Warsaw exit-month attribution
    rows, month_rows = [], []
    for symbol, (signal, res) in results.items():
        bars, manifest, _oi = loaded[symbol]
        trades = res.trades.copy()
        trades["exit_month"] = [warsaw_month(t) for t in trades["exit_time"]]
        tr = trades[trades["exit_month"].isin(fr.TRAIN1_MONTHS_SET)]
        wu = trades[trades["exit_month"].isin(fr.WARMUP_MONTHS_SET)]
        other = trades[~trades["exit_month"].isin(fr.TRAIN1_MONTHS_SET | fr.WARMUP_MONTHS_SET)]
        exits = tr["exit_reason"].value_counts().to_dict()
        for (y, mth) in fr.TRAIN1_MONTHS:
            sel = tr[tr["exit_month"] == (y, mth)]
            month_rows.append({"symbol": symbol, "month": f"{y}-{mth:02d}", "n_trades": int(len(sel)),
                               "net_pnl": round(float(sel["net_pnl"].sum()), 6),
                               "shared_losing": (y, mth) in SHARED_LOSING_MONTHS})
        rows.append({
            "symbol": symbol, "interval": INTERVAL, "strategy": STRATEGY_NAME,
            "n_trades_all": int(len(trades)),
            "n_trades_train1": int(len(tr)),
            "n_skipped_margin": int(len(res.skipped_signals)),
            "first_skipped_margin": str(res.skipped_signals[0]["time"]) if res.skipped_signals else "",
            "min_equity": round(float(res.equity_curve["equity"].min()), 6),
            "final_equity": round(float(res.metrics["final_equity"]), 6),
            "exit_signal_reverse": int(exits.get("signal_reverse", 0)),
            "exit_initial_sl": int(exits.get("initial_sl", 0)),
            "exit_other": int(sum(v for k, v in exits.items() if k not in ("signal_reverse", "initial_sl"))),
            "gross_pnl": round(float(tr["gross_pnl"].sum()), 6),
            "total_costs": round(float(tr["total_costs"].sum()), 6),
            "net_pnl": round(float(tr["net_pnl"].sum()), 6),
            "shared_losing_net": round(float(tr.loc[tr["exit_month"].isin(SHARED_LOSING_MONTHS), "net_pnl"].sum()), 6),
            "warmup_net_pnl": round(float(wu["net_pnl"].sum()), 6),
            "boundary_net_pnl": round(float(other["net_pnl"].sum()), 6),
            "data_checksum": manifest.checksum_sha256,
        })
        trades.drop(columns=["exit_month"]).to_csv(f"{OUTPUT_DIR}/raw/{symbol}_{INTERVAL}_trades.csv", index=False)
        signal.rename("signal").to_csv(f"{OUTPUT_DIR}/raw/{symbol}_{INTERVAL}_signal.csv")

    summary = pd.DataFrame(rows)
    summary.to_csv(f"{OUTPUT_DIR}/summary/results.csv", index=False)
    pd.DataFrame(month_rows).to_csv(f"{OUTPUT_DIR}/summary/monthly.csv", index=False)
    mean_net = float(summary["net_pnl"].mean())
    b_sum = float(summary["shared_losing_net"].sum())
    fired = [x for x, f in (("a", mean_net <= 0), ("b", b_sum <= 0)) if f]

    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None
    out = {
        "experiment_id": "H-NONCANDLE-SLEEVE-01",
        "script": "scripts/f006_noncandle_oi_fade.py",
        "git_commit": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis_note": HYPOTHESIS_NOTE,
        "number_of_trials": 1,
        "interval": INTERVAL,
        "params": {"max_sl_pct": fr.MAX_SL_PCT, "activate_pct": fr.ACTIVATE_PCT,
                   "trail_pct": fr.TRAIL_PCT, "cooldown_candles": fr.COOLDOWN,
                   "initial_equity": fr.INITIAL_EQUITY, "stake": fr.STAKE, **fr.FIXED_PARAMS},
        "timing": {"signal_bar_open": "s", "signal": "-sign(OI[s] - OI[s-1])",
                   "fill": "open of t = s + 1h (position for hour t uses OI[t-1], OI[t-2])",
                   "reverse_exit": "close of bar s (engine signal_reverse)"},
        "oi_manifest": OI_MANIFEST,
        "oi_checksums": {s: e["sha256"] for s, e in oi_manifest["files"].items()},
        "control_arm": control,
        "oi_consumption": consumption,
        "shuffle_seed": SHUFFLE_SEED,
        "per_series": rows,
        "mean_net_pnl": round(mean_net, 6),
        "baseline": 0.0,
        "falsifier_b": {"months": sorted(f"{y}-{m:02d}" for y, m in SHARED_LOSING_MONTHS),
                        "sum_net_pnl": round(b_sum, 6)},
        "fired": fired,
        "result": "FALSIFIED " + "+".join(f"({x})" for x in fired) if fired else "PASS (a),(b) not fired",
        "elapsed_seconds": round(time.time() - t0, 1),
    }
    with open(f"{OUTPUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(summary.drop(columns=["data_checksum"]).to_string(index=False))
    print(json.dumps({k: out[k] for k in ("control_arm", "oi_consumption", "mean_net_pnl", "falsifier_b", "result")},
                     indent=2, default=str))


if __name__ == "__main__":
    main()
