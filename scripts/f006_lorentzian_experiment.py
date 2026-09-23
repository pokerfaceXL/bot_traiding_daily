"""
F006 -- Lorentzian Classification vs. the existing catalog, TRAIN 1 ONLY.

First comparison run for spec/research/F006-lorentzian-causality.md: the causal
Lorentzian adapter (lorentzian.py, advanced-ta 0.1.8 at its library defaults, no
tuning) run through backtest_engine.run_backtest exactly like any catalog entry,
next to the same 10-strategy sample and the same fixed parameters as
scripts/f006_stop_width_experiment.py's max_sl_pct=0.03 rows.

The 10 existing strategies are re-run here rather than quoted from
output/f006_stop_width/summary/results.csv, and then checked against those stored
numbers row by row (see `verify_against_stop_width`): that both gives one
self-contained comparison table and proves the new catalog entries did not perturb
any existing strategy's result.

Scope discipline, identical to scripts/f006_stop_width_experiment.py: the frozen
protocol-scoped cache is loaded and checksum-verified against
spec/research/F005-validation-protocol.md section 6, then sliced to
[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z) -- warm-up + Train 1 only -- before
run_backtest ever sees it. Validation 1-4 and Holdout are never loaded into a run.

Needs Python >= 3.10 (advanced-ta's Requires-Python). Zero network connections.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine  # noqa: E402
import data_contract  # noqa: E402
import lorentzian  # noqa: E402
import strategy  # noqa: E402

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]

WARMUP_START = "2024-01-26T00:00:00Z"
HOLDOUT_END = "2026-09-01T00:00:00Z"
TRAIN1_END = pd.Timestamp("2025-03-01T00:00:00Z")
NOW = TRAIN1_END

# spec/research/F005-validation-protocol.md section 6 -- same table as
# scripts/f006_stop_width_experiment.py, duplicated rather than imported.
EXPECTED_CHECKSUMS = {
    ("SOLUSDT", "240"): "72a6947ba3607e4326cf8a3d655dbc0953103cc66e5f1dd74aa8eb83e45fb731",
    ("SOLUSDT", "60"): "25323c766de58648b624435237e47994b0a3ae1cda5cbcf7e091689b4e74c213",
    ("ETHUSDT", "240"): "4e856f13e3da0afa5d8b5d1d102e04a133788f49122694bdba222f90fbe13176",
    ("ETHUSDT", "60"): "239b32b3348bd11978fdbb43e2d7220f4113625be9e558c4e533e096a312645e",
    ("BTCUSDT", "240"): "d690423a3bae1a53f73728a3b178ab14cbf970855163bed32fe6b727b8e6c467",
    ("BTCUSDT", "60"): "cfb39aec9eadb660460f9e0f180184b67690a35c92af8a16e66398ea548e8d69",
    ("XRPUSDT", "240"): "11c203e30f687508833530daa913e133eb42239699ed52339f4f8e3fbd5a89b3",
    ("XRPUSDT", "60"): "cdd81edbe415f3d583bc365ca1e786afa09956a4aa3bf82e739ecf9b0475b4a5",
    ("DOGEUSDT", "240"): "5a05355dd929a844a262cf9a15950974b1cdf18000b7e44c71ff89ebf567abde",
    ("DOGEUSDT", "60"): "748590acb70eed66878380a7ba4890f498ac458038cd7feec20c3ec3fa16e8ff",
}

# The 10-strategy sample of spec/research/F006-hypothesis-stop-width.md, verbatim.
STRATEGY_SAMPLE = [
    "EMA_8_21", "EMA_13_34_RSI14_55", "RSI14_7030", "MACD_12_26_hist", "MACD_RSI14_50",
    "BB_20_25_breakout", "BB_20_2_RSI14", "ADX14_DI_20", "STOCH14_cross", "TS_13_34_200_14",
]
LORENTZIAN_SAMPLE = ["LORENTZIAN_default", "LORENTZIAN_raw"]

# Identical to the stop-width experiment's fixed block, at its max_sl_pct=0.03 row.
FIXED_PARAMS = dict(
    leverage=1.0,
    cooldown_candles=0,
    atr_multiplier=1.5,
    activate_pct=0.03,
    trail_pct=0.02,
    commission_rate_bps=10.0,
    half_spread_bps=5.0,
    slippage_bps=2.0,
)
MAX_SL_PCT = 0.03
INITIAL_EQUITY = 500.0
STAKE = 100.0
REENTRY_FLOOR = 100.0

OUT_DIR = "output/f006_lorentzian/summary"
STOP_WIDTH_RESULTS = "output/f006_stop_width/summary/results.csv"


def _run_one(df, symbol, interval, strategy_name) -> dict:
    t0 = time.time()
    result = backtest_engine.run_backtest(
        df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE, max_sl_pct=MAX_SL_PCT,
        **FIXED_PARAMS,
    )
    m = result.metrics
    return {
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "max_sl_pct": MAX_SL_PCT,
        "net_pnl": m["total_net_pnl"],
        "win_rate": m["win_rate"],
        "n_trades": int(len(result.trades)),
        "max_drawdown_pct": m["max_drawdown_pct"],
        "final_equity": m["final_equity"],
        "survived": bool(m["final_equity"] >= REENTRY_FLOOR),
        "seconds": round(time.time() - t0, 2),
    }


def signal_shape(df: pd.DataFrame, symbol: str, interval: str) -> dict:
    """
    How the Lorentzian entry signal is shaped, independently of PnL: the engine
    treats a catalog entry as a PERSISTENT state (+1/-1/0 per bar) and re-enters
    whenever the state is non-zero and no position is open, so state flips -- not
    the library's own one-shot startLongTrade/startShortTrade -- drive trade count.
    Recorded so the next slice can reason about entry frequency from measured
    numbers rather than from the trade count alone.
    """
    closed, _ = data_contract.filter_closed_candles(df, interval, now=NOW)
    frame = lorentzian.lorentzian_frame(closed)
    out = {"bars": int(len(frame))}
    for col in ("signal", "raw_signal"):
        s = frame[col].to_numpy()
        out[col] = {
            "pct_bars_long": round(100.0 * float((s > 0).mean()), 1),
            "pct_bars_short": round(100.0 * float((s < 0).mean()), 1),
            "pct_bars_flat": round(100.0 * float((s == 0).mean()), 1),
            "n_state_flips": int((s[1:] != s[:-1]).sum()),
        }
    out["pct_bars_filter_allows"] = round(100.0 * float(frame["filter_all"].mean()), 1)
    return out


def verify_against_stop_width(results: pd.DataFrame) -> dict:
    """Existing strategies must reproduce the stored max_sl_pct=0.03 numbers exactly."""
    if not os.path.exists(STOP_WIDTH_RESULTS):
        return {"checked": False, "reason": f"{STOP_WIDTH_RESULTS} not found"}
    stored = pd.read_csv(STOP_WIDTH_RESULTS)
    stored = stored[stored["max_sl_pct"] == MAX_SL_PCT].copy()
    stored["interval"] = stored["interval"].astype(str)  # CSV reads "240" back as int64
    keys = ["symbol", "interval", "strategy"]
    merged = results[results["strategy"].isin(STRATEGY_SAMPLE)].merge(
        stored, on=keys, suffixes=("_new", "_stored")
    )
    mismatches = []
    for col in ("net_pnl", "win_rate", "n_trades", "max_drawdown_pct", "final_equity"):
        bad = merged[merged[f"{col}_new"] != merged[f"{col}_stored"]]
        for _, row in bad.iterrows():
            mismatches.append({
                "symbol": row["symbol"], "interval": int(row["interval"]), "strategy": row["strategy"],
                "column": col, "new": row[f"{col}_new"], "stored": row[f"{col}_stored"],
            })
    return {"checked": True, "rows_compared": int(len(merged)), "mismatches": mismatches}


def main():
    t_start = time.time()
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None

    all_names = STRATEGY_SAMPLE + LORENTZIAN_SAMPLE
    for name in all_names:
        assert name in strategy.STRATEGY_CATALOG, f"strategy {name!r} not in strategy.STRATEGY_CATALOG"

    rows = []
    diagnostics: dict = {}
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            try:
                full_df, manifest = data_contract.load_dataset(
                    "data_cache", symbol, interval, WARMUP_START, HOLDOUT_END
                )
            except data_contract.DataContractError as exc:
                raise SystemExit(f"STOP: cannot load frozen dataset for {symbol}/{interval} -- {exc}.") from exc
            expected = EXPECTED_CHECKSUMS[(symbol, interval)]
            if manifest.checksum_sha256 != expected:
                raise SystemExit(
                    f"STOP: checksum mismatch for {symbol}/{interval}: cache has "
                    f"{manifest.checksum_sha256}, protocol section 6 expects {expected}."
                )

            idx = pd.DatetimeIndex(full_df.index)
            if idx.tz is None:
                idx = idx.tz_localize("UTC")
            train1_df = full_df.loc[(idx >= pd.Timestamp(WARMUP_START)) & (idx < TRAIN1_END)]
            assert not train1_df.empty, f"empty Train 1 slice for {symbol}/{interval}"
            assert pd.DatetimeIndex(train1_df.index).max() < TRAIN1_END

            diagnostics[f"{symbol}_{interval}"] = signal_shape(train1_df, symbol, interval)
            for name in all_names:
                row = _run_one(train1_df, symbol, interval, name)
                rows.append(row)
                if name.startswith("LORENTZIAN"):
                    print(f"  {symbol}/{interval} {name}: net_pnl={row['net_pnl']:.2f} "
                          f"win={row['win_rate']:.2f}% n={row['n_trades']} dd={row['max_drawdown_pct']:.2f}% "
                          f"({row['seconds']}s)")
            print(f"done {symbol}/{interval} ({len(rows)} runs, {time.time() - t_start:.1f}s elapsed)")

    os.makedirs(OUT_DIR, exist_ok=True)
    results_df = pd.DataFrame(rows)
    results_df.to_csv(f"{OUT_DIR}/results.csv", index=False)

    verification = verify_against_stop_width(results_df)
    with open(f"{OUT_DIR}/manifest.json", "w") as f:
        json.dump({
            "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit_parent": commit_sha,
            "python_version": sys.version.split()[0],
            "advanced_ta_version": "0.1.8",
            "n_runs": len(rows),
            "strategy_sample": STRATEGY_SAMPLE,
            "lorentzian_sample": LORENTZIAN_SAMPLE,
            "symbols": SYMBOLS,
            "intervals": INTERVALS,
            "fixed_params": {**FIXED_PARAMS, "max_sl_pct": MAX_SL_PCT,
                             "initial_equity": INITIAL_EQUITY, "stake": STAKE},
            "lorentzian_params": "advanced-ta 0.1.8 library defaults, untuned (see lorentzian.py)",
            "warmup_start": WARMUP_START,
            "train1_end": str(TRAIN1_END),
            "now_fixed": str(NOW),
            "data_checksums_verified": {f"{s}_{i}": c for (s, i), c in EXPECTED_CHECKSUMS.items()},
            "stop_width_cross_check": verification,
            "lorentzian_signal_shape": diagnostics,
            "elapsed_seconds": round(time.time() - t_start, 1),
        }, f, indent=2)

    print(f"\ncross-check vs {STOP_WIDTH_RESULTS}: {verification}")
    for name in LORENTZIAN_SAMPLE:
        sub = results_df[results_df["strategy"] == name]
        print(f"{name}: mean net_pnl={sub['net_pnl'].mean():.2f} mean win_rate={sub['win_rate'].mean():.2f} "
              f"mean n_trades={sub['n_trades'].mean():.1f} positive={int((sub['net_pnl'] > 0).sum())}/{len(sub)}")
    base = results_df[results_df["strategy"].isin(STRATEGY_SAMPLE)]
    print(f"existing 10-strategy sample: mean net_pnl={base['net_pnl'].mean():.2f} "
          f"mean win_rate={base['win_rate'].mean():.2f} mean n_trades={base['n_trades'].mean():.1f} "
          f"positive={int((base['net_pnl'] > 0).sum())}/{len(base)}")
    print(f"ALL DONE: {len(rows)} runs in {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
