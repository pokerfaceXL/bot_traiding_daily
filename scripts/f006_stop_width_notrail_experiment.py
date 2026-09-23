"""
F006 -- stop-width re-test at NO_TRAIL, TRAIN 1 ONLY.

Tests the hypothesis in spec/research/F006-hypothesis-stop-width-notrail.md: re-running
spec/research/F006-hypothesis-stop-width.md's max_sl_pct sweep ({0.03, 0.05, 0.08, 0.12}) at the
NO_TRAIL exit setting (activate_pct=10.0, trail never arms) from
spec/research/F006-hypothesis-trailing-boundary.md, instead of the original 0.03/0.02 corner --
to see whether the original "nothing at any width" result was a geometry artefact of a trail
that was clipping losers before max_sl_pct ever bound.

Grid: max_sl_pct in {0.03, 0.05, 0.08, 0.12} x 8 signal names x 5 symbols x 2 intervals = 320
runs, all at activate_pct=10.0 (NO_TRAIL). Same sample, mask (one-shot), cooldown=0, leverage=1
and data slice as scripts/f006_trailing_boundary_experiment.py.

TWO PASSES, ONE SCHEMA, same split as every other F006 script:

    .venv_test/bin/python        scripts/f006_stop_width_notrail_experiment.py --catalog
    .venv_lorentzian/bin/python  scripts/f006_stop_width_notrail_experiment.py --lorentzian
    <either>/bin/python          scripts/f006_stop_width_notrail_experiment.py --merge

HARNESS CONTROL: the max_sl_pct=0.03 cell (identical parameters to
F006-hypothesis-trailing-boundary.md's no_trail cell) is diffed row by row against the stored
rows of output/f006_trailing_boundary/summary/results.csv.

Scope discipline, same as every F006 script: the frozen protocol-scoped cache is
checksum-verified against spec/research/F005-validation-protocol.md section 6 and sliced to
[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z) -- warm-up + Train 1 only -- before run_backtest
ever sees it. Validation 1-4 and Holdout are never loaded.

Reads strategy.py/backtest_engine.py/data_contract.py/entry_masks.py/donchian.py/lorentzian.py/
trade_stats.py and changes none of them. Writes only output/f006_stop_width_notrail/. Zero
network connections.
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
import entry_masks  # noqa: E402
import strategy  # noqa: E402
import trade_stats  # noqa: E402

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]

WARMUP_START = "2024-01-26T00:00:00Z"
HOLDOUT_END = "2026-09-01T00:00:00Z"
TRAIN1_END = pd.Timestamp("2025-03-01T00:00:00Z")
NOW = TRAIN1_END

# spec/research/F005-validation-protocol.md section 6, duplicated not imported --
# same table as every other F006 script, verified independently here too.
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

CATALOG_SAMPLE = ["EMA_8_21", "MACD_12_26_hist", "RSI14_7030", "BB_20_25_breakout", "ADX14_DI_20"]
DONCHIAN_SAMPLE = ["DONCHIAN_55", "DONCHIAN_PULLBACK_55"]
LORENTZIAN_SAMPLE = ["LORENTZIAN_default"]
ALL_NAMES = CATALOG_SAMPLE + DONCHIAN_SAMPLE + LORENTZIAN_SAMPLE

MAX_SL_PCT_SWEEP = [0.03, 0.05, 0.08, 0.12]
NO_TRAIL_ACTIVATE = 10.0  # +1000% -- unreachable in Train 1, so trail never arms
NO_TRAIL_TRAIL = 0.04  # moot -- trail never arms, recorded as None per the trailing-boundary convention

FIXED_PARAMS = dict(
    leverage=1.0,
    atr_multiplier=1.5,
    activate_pct=NO_TRAIL_ACTIVATE,
    trail_pct=NO_TRAIL_TRAIL,
    commission_rate_bps=10.0,
    half_spread_bps=5.0,
    slippage_bps=2.0,
)
COOLDOWN = 0
INITIAL_EQUITY = 500.0
STAKE = 100.0
REENTRY_FLOOR = 100.0

OUT_DIR = "output/f006_stop_width_notrail/summary"
PRIOR_RESULTS = "output/f006_trailing_boundary/summary/results.csv"

DECOMP_COLUMNS = ["n_wins", "n_losses", "sum_wins", "sum_losses",
                  "avg_winner", "avg_loser", "breakeven_win_rate_pct"]


def load_train1(symbol: str, interval: str) -> pd.DataFrame:
    try:
        full_df, manifest = data_contract.load_dataset(
            "data_cache", symbol, interval, WARMUP_START, HOLDOUT_END
        )
    except data_contract.DataContractError as exc:
        raise SystemExit(
            f"STOP: cannot load frozen dataset for {symbol}/{interval} from data_cache -- {exc}."
        ) from exc
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
    return train1_df


def _mean_bars_held(trades: pd.DataFrame, interval: str) -> float:
    if not len(trades):
        return 0.0
    span = pd.to_datetime(trades["exit_time"]) - pd.to_datetime(trades["entry_time"])
    return round(float((span.dt.total_seconds() / 60.0 / int(interval)).mean()), 2)


def _run_one(df, mask, symbol, interval, strategy_name, max_sl_pct, n_calls) -> dict:
    t0 = time.time()
    result = backtest_engine.run_backtest(
        df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE, max_sl_pct=max_sl_pct,
        cooldown_candles=COOLDOWN,
        entry_regime_mask=mask,
        **FIXED_PARAMS,
    )
    m = result.metrics
    trades = result.trades
    d = trade_stats.win_loss_decomposition(trades)
    exit_mix = trades["exit_reason"].value_counts().to_dict() if len(trades) else {}
    return {
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "max_sl_pct": max_sl_pct,
        "activate_pct": NO_TRAIL_ACTIVATE, "trail_pct": None, "no_trail": True,
        "cooldown_candles": COOLDOWN, "mask_mode": "one_shot",
        "n_calls": n_calls,
        "net_pnl": m["total_net_pnl"],
        "gross_pnl": round(float(trades["gross_pnl"].sum()) if len(trades) else 0.0, 6),
        "total_costs": round(float(trades["total_costs"].sum()) if len(trades) else 0.0, 6),
        "win_rate": m["win_rate"],
        "n_trades": int(len(trades)),
        "n_wins": d["n_wins"], "n_losses": d["n_losses"],
        "sum_wins": round(d["sum_wins"], 6), "sum_losses": round(d["sum_losses"], 6),
        "avg_winner": round(d["avg_winner"], 6),
        "avg_loser": round(d["avg_loser"], 6),
        "breakeven_win_rate_pct": (round(d["breakeven_win_rate_pct"], 4)
                                   if d["breakeven_win_rate_pct"] is not None else None),
        "mean_bars_held": _mean_bars_held(trades, interval),
        "exit_initial_sl": int(exit_mix.get("initial_sl", 0)),
        "exit_trailing_sl": int(exit_mix.get("trailing_sl", 0)),
        "exit_signal_reverse": int(exit_mix.get("signal_reverse", 0)),
        "exit_end_of_data": int(exit_mix.get("end_of_data", 0)),
        "max_drawdown_pct": m["max_drawdown_pct"],
        "final_equity": m["final_equity"],
        "survived": bool(m["final_equity"] >= REENTRY_FLOOR),
        "seconds": round(time.time() - t0, 2),
    }


def run_pass(names: list, tag: str) -> pd.DataFrame:
    for name in names:
        assert name in strategy.STRATEGY_CATALOG, f"strategy {name!r} not in strategy.STRATEGY_CATALOG"
    t_start = time.time()
    rows = []
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            train1_df = load_train1(symbol, interval)
            for name in names:
                sig = entry_masks.strategy_signal_series(train1_df, name, interval=interval, now=NOW)
                mask = entry_masks.one_shot_entry_mask(sig)
                n_calls = int(mask.sum())
                for max_sl_pct in MAX_SL_PCT_SWEEP:
                    rows.append(_run_one(train1_df, mask, symbol, interval, name,
                                         max_sl_pct, n_calls))
            print(f"done {symbol}/{interval} ({len(rows)} runs, {time.time() - t_start:.1f}s elapsed)")
    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT_DIR}/results_{tag}.csv", index=False)
    with open(f"{OUT_DIR}/manifest_{tag}.json", "w") as f:
        json.dump(_manifest(df, t_start, {"pass": tag, "names": names}), f, indent=2)
    print(f"\n[{tag}] {len(df)} runs in {time.time() - t_start:.1f}s -> {OUT_DIR}/results_{tag}.csv")
    return df


# ---------------------------------------------------------------- checks

def verify_no_trail_cell(results: pd.DataFrame) -> dict:
    """The max_sl_pct=0.03 rows must reproduce the trailing-boundary note's no_trail rows exactly."""
    mine = results[results["max_sl_pct"] == 0.03].copy()
    mine["interval"] = mine["interval"].astype(str)
    if not os.path.exists(PRIOR_RESULTS):
        return {"rows_compared": 0, "n_mismatches": 0, "mismatches": [],
                "source": f"{PRIOR_RESULTS} MISSING -- not compared"}
    stored = pd.read_csv(PRIOR_RESULTS)
    stored["interval"] = stored["interval"].astype(str)
    stored = stored[(stored["no_trail"] == True) & (stored["mask_mode"] == "one_shot")  # noqa: E712
                    & (stored["cooldown_candles"] == COOLDOWN) & (stored["max_sl_pct"] == 0.03)]
    merged = mine.merge(stored, on=["symbol", "interval", "strategy"], suffixes=("_new", "_stored"))
    mismatches = []
    for col in ("net_pnl", "win_rate", "n_trades", "max_drawdown_pct", "final_equity"):
        bad = merged[merged[f"{col}_new"] != merged[f"{col}_stored"]]
        for _, row in bad.iterrows():
            mismatches.append({"symbol": row["symbol"], "interval": row["interval"],
                               "strategy": row["strategy"], "column": col,
                               "new": row[f"{col}_new"], "stored": row[f"{col}_stored"]})
    return {"rows_compared": int(len(merged)), "n_mismatches": len(mismatches),
            "mismatches": mismatches[:20], "source": f"{len(merged)} rows vs {PRIOR_RESULTS}"}


def verify_no_trail_mechanism(results: pd.DataFrame) -> dict:
    """No cell in this grid may ever produce a trailing_sl exit."""
    bad = results[results["exit_trailing_sl"] > 0]
    return {"runs": int(len(results)), "runs_with_a_trailing_exit": int(len(bad)),
            "total_trailing_exits": int(results["exit_trailing_sl"].sum())}


def verify_one_shot_rule(results: pd.DataFrame) -> dict:
    violations = results[results["n_trades"] > results["n_calls"]]
    return {"runs": int(len(results)), "violations": int(len(violations))}


# ---------------------------------------------------------------- aggregation

def _pooled(sub: pd.DataFrame) -> dict:
    d = trade_stats.pool_decompositions(sub[["n_trades"] + DECOMP_COLUMNS].to_dict("records"))
    n = max(int(sub["n_trades"].sum()), 1)
    be_rate = d["breakeven_win_rate_pct"]
    win_rate = d["win_rate_pct"]
    return {
        "n_runs": int(len(sub)),
        "n_trades": int(sub["n_trades"].sum()),
        "avg_winner": round(d["avg_winner"], 4),
        "avg_loser": round(d["avg_loser"], 4),
        "reward_risk": round(d["avg_winner"] / abs(d["avg_loser"]), 4) if d["avg_loser"] else None,
        "breakeven_win_rate_pct": round(be_rate, 4) if be_rate is not None else None,
        "win_rate_pct": round(win_rate, 4) if win_rate is not None else None,
        "gap_pp": (round(be_rate - win_rate, 4)
                   if be_rate is not None and win_rate is not None else None),
        "net_per_trade": round(float(sub["net_pnl"].sum()) / n, 4),
        "gross_per_trade": round(float(sub["gross_pnl"].sum()) / n, 4),
        "mean_net_pnl": round(float(sub["net_pnl"].mean()), 2),
        "mean_max_drawdown_pct": round(float(sub["max_drawdown_pct"].mean()), 2),
        "survived": int(sub["survived"].sum()),
        "positive_net_pnl": int((sub["net_pnl"] > 0).sum()),
    }


def _cell_table(results: pd.DataFrame) -> dict:
    out = {}
    for w in MAX_SL_PCT_SWEEP:
        out[f"max_sl_pct_{w:g}"] = {"max_sl_pct": w,
                                    **_pooled(results[results["max_sl_pct"] == w])}
    return out


def _falsify(cells: dict) -> dict:
    ordered = [cells[f"max_sl_pct_{w:g}"]["net_per_trade"] for w in MAX_SL_PCT_SWEEP]
    diffs = [ordered[i + 1] - ordered[i] for i in range(len(ordered) - 1)]
    monotonic = all(d >= 0 for d in diffs) or all(d <= 0 for d in diffs)
    span = max(ordered) - min(ordered)
    base_abs = abs(ordered[0])
    span_pct_of_base = (100.0 * span / base_abs) if base_abs else None
    meaningful = (span_pct_of_base is not None) and (span_pct_of_base >= 10.0)
    return {
        "net_per_trade_by_width": {f"{w:g}": v for w, v in zip(MAX_SL_PCT_SWEEP, ordered)},
        "step_diffs": diffs,
        "monotonic": monotonic,
        "span": round(span, 4),
        "base_abs_net_per_trade_at_0.03": round(base_abs, 4),
        "span_pct_of_base": round(span_pct_of_base, 2) if span_pct_of_base is not None else None,
        "meaningful_span_ge_10pct": meaningful,
        "falsified": not (monotonic and meaningful),
    }


def _manifest(results_df: pd.DataFrame, t_start: float, extra: dict) -> dict:
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None
    return {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit_parent": commit_sha,
        "python_version": sys.version.split()[0],
        "pandas_version": pd.__version__,
        "n_runs": int(len(results_df)),
        "sample_names": ALL_NAMES,
        "max_sl_pct_sweep": MAX_SL_PCT_SWEEP,
        "no_trail_activate_pct": NO_TRAIL_ACTIVATE,
        "symbols": SYMBOLS, "intervals": INTERVALS,
        "fixed_params": {**FIXED_PARAMS, "cooldown_candles": COOLDOWN,
                         "initial_equity": INITIAL_EQUITY, "stake": STAKE},
        "warmup_start": WARMUP_START, "train1_end": str(TRAIN1_END),
        "elapsed_seconds": round(time.time() - t_start, 1),
        **extra,
    }


def merge() -> pd.DataFrame:
    t_start = time.time()
    parts = []
    for tag in ("catalog", "lorentzian"):
        path = f"{OUT_DIR}/results_{tag}.csv"
        if not os.path.exists(path):
            raise SystemExit(f"STOP: {path} missing -- run the --{tag} pass first.")
        parts.append(pd.read_csv(path))
    results = pd.concat(parts, ignore_index=True)
    results["interval"] = results["interval"].astype(str)
    expected = len(MAX_SL_PCT_SWEEP) * len(ALL_NAMES) * len(SYMBOLS) * len(INTERVALS)
    assert len(results) == expected, f"expected {expected} runs, merged {len(results)}"
    results.to_csv(f"{OUT_DIR}/results.csv", index=False)

    cells = _cell_table(results)
    checks = {
        "no_trail_cell_vs_stored_boundary_note": verify_no_trail_cell(results),
        "no_trail_mechanism": verify_no_trail_mechanism(results),
        "one_shot_rule": verify_one_shot_rule(results),
    }
    falsify = _falsify(cells)
    manifest = _manifest(results, t_start, {
        "pass": "merged", **checks, "cells": cells,
        "falsification": falsify,
    })
    with open(f"{OUT_DIR}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    _print_report(cells, checks, falsify)
    return results


def _print_report(cells, checks, falsify) -> None:
    b = checks["no_trail_cell_vs_stored_boundary_note"]
    print(f"\nmax_sl_pct=0.03 vs trailing-boundary no_trail cell: {b['rows_compared']} rows "
          f"compared, {b['n_mismatches']} mismatches ({b.get('source')})")
    nt = checks["no_trail_mechanism"]
    print(f"no_trail mechanism: {nt['runs']} runs, {nt['runs_with_a_trailing_exit']} with a "
          f"trailing exit, {nt['total_trailing_exits']} trailing exits total (expect 0)")
    print(f"one-shot rule violations: {checks['one_shot_rule']['violations']}/"
          f"{checks['one_shot_rule']['runs']}")

    print(f"\n{'max_sl_pct':>10} {'avgWin':>7} {'avgLoss':>8} {'R:R':>6} {'breakeven%':>11} "
          f"{'win%':>6} {'net/tr':>7} {'trades':>7} {'pos':>6}")
    for w in MAX_SL_PCT_SWEEP:
        c = cells[f"max_sl_pct_{w:g}"]
        print(f"{w:>10.2f} {c['avg_winner']:7.3f} {c['avg_loser']:8.3f} {c['reward_risk']:6.3f} "
              f"{c['breakeven_win_rate_pct']:11.2f} {c['win_rate_pct']:6.2f} "
              f"{c['net_per_trade']:7.3f} {c['n_trades']:7d} "
              f"{c['positive_net_pnl']:>3}/{c['n_runs']:<3}")

    print("\n-- falsification: net PnL/trade must move monotonically and span >= 10% of the "
          "0.03 base --")
    print(f"  by width: {falsify['net_per_trade_by_width']}")
    print(f"  step diffs: {falsify['step_diffs']}  monotonic: {falsify['monotonic']}")
    print(f"  span: {falsify['span']}  span as % of |base|: {falsify['span_pct_of_base']}  "
          f"meaningful (>=10%): {falsify['meaningful_span_ge_10pct']}")
    print(f"  => FALSIFIED: {falsify['falsified']}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--catalog":
        run_pass(CATALOG_SAMPLE + DONCHIAN_SAMPLE, "catalog")
    elif mode == "--lorentzian":
        run_pass(LORENTZIAN_SAMPLE, "lorentzian")
    elif mode == "--merge":
        merge()
    else:
        raise SystemExit("usage: f006_stop_width_notrail_experiment.py --catalog | --lorentzian | --merge")
