"""
F006 -- trailing-geometry boundary + no-trail control, TRAIN 1 ONLY.

Tests the hypothesis in spec/research/F006-hypothesis-trailing-boundary.md: continuing
spec/research/F006-hypothesis-trailing-sweep.md's max(activate_pct, trail_pct) collapse
outward from its grid corner (0.06/0.04), and comparing every finite cell against a
NO_TRAIL control (activate_pct set so high the trail can never arm).

H1: extending max(a, t) from 0.06 to 0.20 keeps improving pooled breakeven_win_rate_pct,
    with diminishing (concave) marginal gains -- not a turn.
H2: NO_TRAIL's pooled breakeven_win_rate_pct is <= the best finite cell's -- i.e. no
    finite trailing setting beats having no trail at all, within measurement noise.

Grid: 8 finite cells (activate_pct in {0.06, 0.10, 0.15, 0.20} x trail_pct in
{0.04, 0.08}) + 1 NO_TRAIL cell (activate_pct=10.0) = 9 cells x 8 signal names x
5 symbols x 2 intervals = 720 runs. Same sample, mask (one-shot), max_sl_pct=0.03 and
data slice as scripts/f006_trailing_sweep_experiment.py.

TWO PASSES, ONE SCHEMA, same split as every other F006 script:

    .venv_test/bin/python        scripts/f006_trailing_boundary_experiment.py --catalog
    .venv_lorentzian/bin/python  scripts/f006_trailing_boundary_experiment.py --lorentzian
    <either>/bin/python          scripts/f006_trailing_boundary_experiment.py --merge

HARNESS CONTROL: the a=0.06/t=0.04 cell (this grid's baseline, the prior note's best cell)
is re-run from scratch and diffed row by row against the stored rows of
output/f006_trailing_sweep/summary/results.csv.

Scope discipline, same as every F006 script: the frozen protocol-scoped cache is
checksum-verified against spec/research/F005-validation-protocol.md section 6 and
sliced to [2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z) -- warm-up + Train 1 only --
before run_backtest ever sees it. Validation 1-4 and Holdout are never loaded.

Reads strategy.py/backtest_engine.py/data_contract.py/entry_masks.py/donchian.py/
lorentzian.py/trade_stats.py and changes none of them. Writes only
output/f006_trailing_boundary/. Zero network connections.
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

ACTIVATE_SWEEP = [0.06, 0.10, 0.15, 0.20]
TRAIL_SWEEP = [0.04, 0.08]
NO_TRAIL_ACTIVATE = 10.0  # +1000% -- unreachable in Train 1, so trail never arms
FINITE_CELLS = [(a, t) for a in ACTIVATE_SWEEP for t in TRAIL_SWEEP]
CELLS = FINITE_CELLS + [(NO_TRAIL_ACTIVATE, None)]
BASELINE_CELL = (0.06, 0.04)  # the prior note's best cell -- this grid's harness control

FIXED_PARAMS = dict(
    leverage=1.0,
    atr_multiplier=1.5,
    commission_rate_bps=10.0,
    half_spread_bps=5.0,
    slippage_bps=2.0,
)
MAX_SL_PCT = 0.03
COOLDOWN = 0
INITIAL_EQUITY = 500.0
STAKE = 100.0
REENTRY_FLOOR = 100.0

OUT_DIR = "output/f006_trailing_boundary/summary"
PRIOR_RESULTS = "output/f006_trailing_sweep/summary/results.csv"

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


def _cell_key(activate_pct: float, trail_pct) -> str:
    if trail_pct is None:
        return "no_trail"
    return f"a{activate_pct:g}_t{trail_pct:g}"


def _run_one(df, mask, symbol, interval, strategy_name, activate_pct, trail_pct, n_calls) -> dict:
    t0 = time.time()
    no_trail = trail_pct is None
    effective_trail = 0.04 if no_trail else trail_pct  # unreachable arming makes trail_pct moot
    result = backtest_engine.run_backtest(
        df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE, max_sl_pct=MAX_SL_PCT,
        activate_pct=activate_pct, trail_pct=effective_trail,
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
        "activate_pct": activate_pct, "trail_pct": (None if no_trail else trail_pct),
        "no_trail": no_trail,
        "cell": _cell_key(activate_pct, None if no_trail else trail_pct),
        "is_baseline_cell": (not no_trail) and (activate_pct, trail_pct) == BASELINE_CELL,
        "max_sl_pct": MAX_SL_PCT, "cooldown_candles": COOLDOWN, "mask_mode": "one_shot",
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
                for activate_pct, trail_pct in CELLS:
                    rows.append(_run_one(train1_df, mask, symbol, interval, name,
                                         activate_pct, trail_pct, n_calls))
            print(f"done {symbol}/{interval} ({len(rows)} runs, {time.time() - t_start:.1f}s elapsed)")
    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT_DIR}/results_{tag}.csv", index=False)
    with open(f"{OUT_DIR}/manifest_{tag}.json", "w") as f:
        json.dump(_manifest(df, t_start, {"pass": tag, "names": names}), f, indent=2)
    print(f"\n[{tag}] {len(df)} runs in {time.time() - t_start:.1f}s -> {OUT_DIR}/results_{tag}.csv")
    return df


# ---------------------------------------------------------------- checks

def verify_baseline_cell(results: pd.DataFrame) -> dict:
    """The a=0.06/t=0.04 rows must reproduce the prior note's stored rows exactly."""
    mine = results[results["is_baseline_cell"]].copy()
    mine["interval"] = mine["interval"].astype(str)
    if not os.path.exists(PRIOR_RESULTS):
        return {"rows_compared": 0, "n_mismatches": 0, "mismatches": [],
                "source": f"{PRIOR_RESULTS} MISSING -- not compared"}
    stored = pd.read_csv(PRIOR_RESULTS)
    stored["interval"] = stored["interval"].astype(str)
    stored = stored[(stored["activate_pct"] == BASELINE_CELL[0])
                    & (stored["trail_pct"] == BASELINE_CELL[1])
                    & (stored["mask_mode"] == "one_shot")
                    & (stored["cooldown_candles"] == COOLDOWN)]
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
    """NO_TRAIL cell must never produce a trailing_sl exit."""
    sub = results[results["no_trail"]]
    bad = sub[sub["exit_trailing_sl"] > 0]
    return {"runs": int(len(sub)), "runs_with_a_trailing_exit": int(len(bad)),
            "total_trailing_exits": int(sub["exit_trailing_sl"].sum())}


def verify_trade_count_invariance(results: pd.DataFrame) -> dict:
    g = results.groupby(["strategy", "symbol", "interval"])["n_trades"]
    spread = (g.max() - g.min())
    rel = (spread / g.mean().replace(0, pd.NA)).dropna()
    per_cell = results.groupby("cell")["n_trades"].sum()
    base_total = int(per_cell.get(_cell_key(*BASELINE_CELL), 0))
    return {
        "series": int(len(spread)),
        "series_with_identical_n_trades_across_cells": int((spread == 0).sum()),
        "max_relative_spread_pct": round(float(rel.max() * 100), 3),
        "mean_relative_spread_pct": round(float(rel.mean() * 100), 3),
        "pooled_n_trades_by_cell": {c: int(v) for c, v in per_cell.items()},
        "pooled_n_trades_vs_baseline_pct": {
            c: (round(100.0 * (int(v) - base_total) / base_total, 3) if base_total else None)
            for c, v in per_cell.items()},
    }


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
    for a, t in FINITE_CELLS:
        key = _cell_key(a, t)
        out[key] = {"activate_pct": a, "trail_pct": t,
                    "max_a_t": round(max(a, t), 6),
                    **_pooled(results[(results["activate_pct"] == a) & (results["trail_pct"] == t)])}
    out["no_trail"] = {"activate_pct": NO_TRAIL_ACTIVATE, "trail_pct": None, "max_a_t": None,
                       **_pooled(results[results["no_trail"]])}
    return out


def _falsify_h1(cells: dict) -> dict:
    base = cells[_cell_key(*BASELINE_CELL)]["breakeven_win_rate_pct"]
    widest = cells[_cell_key(0.20, 0.08)]["breakeven_win_rate_pct"]
    # marginal gain per step of max(a,t): pool over the two trail values per activate level
    by_max = {}
    for a in ACTIVATE_SWEEP:
        rows = [cells[_cell_key(a, t)] for t in TRAIL_SWEEP]
        n = sum(r["n_trades"] for r in rows)
        be = sum(r["breakeven_win_rate_pct"] * r["n_trades"] for r in rows) / n if n else None
        by_max[a] = be
    gain_06_10 = by_max[0.06] - by_max[0.10]
    gain_10_20 = by_max[0.10] - by_max[0.20]
    widened = (base - widest) >= 0.5
    concave = gain_06_10 >= gain_10_20  # bigger early gain than late gain
    return {
        "baseline_breakeven": round(base, 4), "widest_breakeven": round(widest, 4),
        "improvement_pp": round(base - widest, 4), "improved_by_at_least_0_5pp": widened,
        "breakeven_by_activate_level": {k: round(v, 4) for k, v in by_max.items()},
        "gain_0.06_to_0.10": round(gain_06_10, 4), "gain_0.10_to_0.20": round(gain_10_20, 4),
        "concave_diminishing_returns": concave,
        "falsified": not (widened and concave),
    }


def _falsify_h2(cells: dict) -> dict:
    finite = {k: v for k, v in cells.items() if k != "no_trail"}
    best_key = min(finite.items(), key=lambda kv: kv[1]["breakeven_win_rate_pct"])[0]
    best_be = finite[best_key]["breakeven_win_rate_pct"]
    no_trail_be = cells["no_trail"]["breakeven_win_rate_pct"]
    margin = no_trail_be - best_be  # positive means a finite cell beats no_trail
    falsified = margin > 1.0
    return {
        "best_finite_cell": best_key, "best_finite_breakeven": round(best_be, 4),
        "no_trail_breakeven": round(no_trail_be, 4),
        "finite_advantage_pp": round(margin, 4),
        "falsified": falsified,
    }


def _quality_gate(results: pd.DataFrame, cells: dict) -> dict:
    base = cells[_cell_key(*BASELINE_CELL)]
    out = {}
    for key, c in cells.items():
        trade_drop_pct = 100.0 * (base["n_trades"] - c["n_trades"]) / max(base["n_trades"], 1)
        out[key] = {
            "trade_drop_vs_baseline_pct": round(trade_drop_pct, 3),
            "net_per_trade": c["net_per_trade"], "baseline_net_per_trade": base["net_per_trade"],
            "passes_gate": bool(trade_drop_pct <= 10.0 and c["net_per_trade"] >= base["net_per_trade"]),
        }
    return out


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
        "activate_sweep": ACTIVATE_SWEEP, "trail_sweep": TRAIL_SWEEP,
        "no_trail_activate_pct": NO_TRAIL_ACTIVATE,
        "baseline_cell": _cell_key(*BASELINE_CELL),
        "symbols": SYMBOLS, "intervals": INTERVALS,
        "fixed_params": {**FIXED_PARAMS, "max_sl_pct": MAX_SL_PCT, "cooldown_candles": COOLDOWN,
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
    expected = len(CELLS) * len(ALL_NAMES) * len(SYMBOLS) * len(INTERVALS)
    assert len(results) == expected, f"expected {expected} runs, merged {len(results)}"
    results.to_csv(f"{OUT_DIR}/results.csv", index=False)

    cells = _cell_table(results)
    checks = {
        "baseline_cell_vs_stored_notes": verify_baseline_cell(results),
        "no_trail_mechanism": verify_no_trail_mechanism(results),
        "trade_count_invariance": verify_trade_count_invariance(results),
        "one_shot_rule": verify_one_shot_rule(results),
    }
    h1 = _falsify_h1(cells)
    h2 = _falsify_h2(cells)
    quality = _quality_gate(results, cells)
    manifest = _manifest(results, t_start, {
        "pass": "merged", **checks, "cells": cells,
        "h1_diminishing_returns": h1, "h2_no_trail_is_ceiling": h2,
        "quality_gate_per_cell": quality,
    })
    with open(f"{OUT_DIR}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    _print_report(cells, checks, h1, h2, quality)
    return results


def _print_report(cells, checks, h1, h2, quality) -> None:
    b = checks["baseline_cell_vs_stored_notes"]
    print(f"\nbaseline cell vs prior note: {b['rows_compared']} rows compared, "
          f"{b['n_mismatches']} mismatches ({b.get('source')})")
    nt = checks["no_trail_mechanism"]
    print(f"no_trail mechanism: {nt['runs']} runs, {nt['runs_with_a_trailing_exit']} with a "
          f"trailing exit, {nt['total_trailing_exits']} trailing exits total (expect 0)")
    inv = checks["trade_count_invariance"]
    print(f"trade-count invariance: {inv['series_with_identical_n_trades_across_cells']}/"
          f"{inv['series']} series identical; max spread {inv['max_relative_spread_pct']}%")
    print(f"one-shot rule violations: {checks['one_shot_rule']['violations']}/"
          f"{checks['one_shot_rule']['runs']}")

    print(f"\n{'cell':>12} {'max(a,t)':>9} {'avgWin':>7} {'avgLoss':>8} {'R:R':>6} "
          f"{'breakeven%':>11} {'win%':>6} {'net/tr':>7} {'trades':>7} {'pos':>6} {'gate':>5}")
    for key, c in cells.items():
        mx = f"{c['max_a_t']:.4f}" if c['max_a_t'] is not None else "  n/a"
        gate = "OK" if quality[key]["passes_gate"] else "FAIL"
        print(f"{key:>12} {mx:>9} {c['avg_winner']:7.3f} {c['avg_loser']:8.3f} "
              f"{c['reward_risk']:6.3f} {c['breakeven_win_rate_pct']:11.2f} {c['win_rate_pct']:6.2f} "
              f"{c['net_per_trade']:7.3f} {c['n_trades']:7d} "
              f"{c['positive_net_pnl']:>3}/{c['n_runs']:<3}{gate:>5}")

    print("\n-- H1: diminishing returns from 0.06 to 0.20 --")
    print(f"  baseline (0.06) breakeven={h1['baseline_breakeven']}  widest (0.20) breakeven="
          f"{h1['widest_breakeven']}  improvement={h1['improvement_pp']} pp "
          f"(bar: >= 0.5 pp) -> {h1['improved_by_at_least_0_5pp']}")
    print(f"  gain 0.06->0.10 = {h1['gain_0.06_to_0.10']} pp, gain 0.10->0.20 = "
          f"{h1['gain_0.10_to_0.20']} pp -> concave: {h1['concave_diminishing_returns']}")
    print(f"  => H1 FALSIFIED: {h1['falsified']}")

    print("\n-- H2: no_trail is the ceiling --")
    print(f"  best finite cell: {h2['best_finite_cell']} at {h2['best_finite_breakeven']}%  "
          f"no_trail at {h2['no_trail_breakeven']}%  finite advantage = {h2['finite_advantage_pp']} pp "
          f"(falsifies if > 1.0 pp)")
    print(f"  => H2 FALSIFIED: {h2['falsified']}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--catalog":
        run_pass(CATALOG_SAMPLE + DONCHIAN_SAMPLE, "catalog")
    elif mode == "--lorentzian":
        run_pass(LORENTZIAN_SAMPLE, "lorentzian")
    elif mode == "--merge":
        merge()
    else:
        raise SystemExit("usage: f006_trailing_boundary_experiment.py --catalog | --lorentzian | --merge")
