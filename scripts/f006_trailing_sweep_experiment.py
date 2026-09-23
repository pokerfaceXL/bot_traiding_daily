"""
F006 -- activate_pct x trail_pct sweep (the exit geometry), TRAIN 1 ONLY.

Tests the hypothesis in spec/research/F006-hypothesis-trailing-sweep.md: that the
1 : 1.75 reward:risk ratio spec/research/F006-hypothesis-donchian.md decomposed
(avg winner $1.46 vs avg loser -$2.55, ~63% breakeven win rate, no name above 44%) is
a property of the two win-side exit parameters -- which no F006 slice has ever varied,
since every prior script inherited run_backtest's own defaults of 0.03/0.02 -- rather
than of this basket's price action.

Outcome variable is NOT net PnL. It is pooled breakeven_win_rate_pct
(= |avg_loser| / (avg_winner + |avg_loser|) * 100, trade_stats.py), with net and gross
per-trade expectancy alongside so a reviewer can see whether any improvement is a
reward:risk story or a cost-drag story.

Grid: 9 cells (activate_pct in {0.01, 0.03, 0.06} x trail_pct in {0.01, 0.02, 0.04})
x 8 signal names x 5 symbols x 2 intervals = 720 runs, ALL with the one-shot
entry_regime_mask on (per the board's recorded decision), cooldown_candles=0,
max_sl_pct=0.03 fixed -- the initial stop was spec/research/F006-hypothesis-stop-width.md's
job and is deliberately not swept here.

TWO PASSES, ONE SCHEMA -- same split as scripts/f006_one_shot_experiment.py, because
advanced-ta (lorentzian.py) needs Python >=3.10:

    .venv_test/bin/python        scripts/f006_trailing_sweep_experiment.py --catalog
    .venv_lorentzian/bin/python  scripts/f006_trailing_sweep_experiment.py --lorentzian
    <either>/bin/python          scripts/f006_trailing_sweep_experiment.py --merge

HARNESS CONTROL: the 0.03/0.02 cell is re-run from scratch, then diffed row by row
against the stored rows of output/f006_one_shot/summary/results.csv (one-shot, cd=0)
and output/f006_donchian/summary/results.csv (one-shot) -- 80 rows, six columns each.
Every "improves versus baseline" claim in the note rests on that diff being empty.

Scope discipline, same as every F006 script: the frozen protocol-scoped cache is
checksum-verified against spec/research/F005-validation-protocol.md section 6 and
sliced to [2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z) -- warm-up + Train 1 only --
before run_backtest ever sees it. Validation 1-4 and Holdout are never loaded.

Reads strategy.py/backtest_engine.py/data_contract.py/entry_masks.py/donchian.py/
lorentzian.py/trade_stats.py and changes none of them. Writes only
output/f006_trailing_sweep/. Zero network connections.
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
NOW = TRAIN1_END  # fixed, not wall-clock -- filter_closed_candles stays deterministic

# spec/research/F005-validation-protocol.md section 6 -- same table as every other
# F006 script, duplicated (not imported) so this script verifies independently.
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

# The 8-name sample, justified name by name in the research note's "Sample" section.
CATALOG_SAMPLE = ["EMA_8_21", "MACD_12_26_hist", "RSI14_7030", "BB_20_25_breakout", "ADX14_DI_20"]
DONCHIAN_SAMPLE = ["DONCHIAN_55", "DONCHIAN_PULLBACK_55"]
LORENTZIAN_SAMPLE = ["LORENTZIAN_default"]
ALL_NAMES = CATALOG_SAMPLE + DONCHIAN_SAMPLE + LORENTZIAN_SAMPLE

ACTIVATE_SWEEP = [0.01, 0.03, 0.06]
TRAIL_SWEEP = [0.01, 0.02, 0.04]
CELLS = [(a, t) for a in ACTIVATE_SWEEP for t in TRAIL_SWEEP]
BASELINE_CELL = (0.03, 0.02)  # run_backtest's own defaults, inherited by all 7 prior F006 slices

# Identical fixed block to scripts/f006_donchian_experiment.py minus the two swept
# parameters. max_sl_pct stays at 0.03: this slice isolates the TRAILING parameters.
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

OUT_DIR = "output/f006_trailing_sweep/summary"
ONE_SHOT_RESULTS = "output/f006_one_shot/summary/results.csv"
DONCHIAN_RESULTS = "output/f006_donchian/summary/results.csv"

DECOMP_COLUMNS = ["n_wins", "n_losses", "sum_wins", "sum_losses",
                  "avg_winner", "avg_loser", "breakeven_win_rate_pct"]


def load_train1(symbol: str, interval: str) -> pd.DataFrame:
    """Checksum-verified protocol cache, sliced to warm-up + Train 1 only."""
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


def _run_one(df, mask, symbol, interval, strategy_name, activate_pct, trail_pct, n_calls) -> dict:
    t0 = time.time()
    result = backtest_engine.run_backtest(
        df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE, max_sl_pct=MAX_SL_PCT,
        activate_pct=activate_pct, trail_pct=trail_pct,
        cooldown_candles=COOLDOWN,
        entry_regime_mask=mask,  # one-shot mask ON for every run in this slice
        **FIXED_PARAMS,
    )
    m = result.metrics
    trades = result.trades
    # The outcome variable. trade_stats reuses result.trades["net_pnl"] and the
    # engine's own win convention; tests/test_trade_stats.py pins both.
    d = trade_stats.win_loss_decomposition(trades)
    exit_mix = trades["exit_reason"].value_counts().to_dict() if len(trades) else {}
    return {
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "activate_pct": activate_pct, "trail_pct": trail_pct,
        "cell": f"a{activate_pct:g}_t{trail_pct:g}",
        "is_baseline_cell": (activate_pct, trail_pct) == BASELINE_CELL,
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
                # The mask is a pure function of the signal, so it is computed ONCE per
                # (name, symbol, interval) and shared by all 9 cells. That is also why
                # n_trades is expected to be near-invariant across cells: the exit
                # parameters cannot create or remove an entry opportunity.
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
    """The 0.03/0.02 rows must reproduce the stored prior notes exactly.

    Same engine, same fixed params, same data slice, same mask helper -- so any
    difference means this script's harness drifted and every "improves versus the
    baseline" statement in the note would be comparing against the wrong number.
    """
    mine = results[results["is_baseline_cell"]].copy()
    mine["interval"] = mine["interval"].astype(str)
    mismatches, compared, sources = [], 0, {}
    for path, names in ((ONE_SHOT_RESULTS, CATALOG_SAMPLE + LORENTZIAN_SAMPLE),
                        (DONCHIAN_RESULTS, DONCHIAN_SAMPLE)):
        if not os.path.exists(path):
            sources[path] = "MISSING -- not compared"
            continue
        stored = pd.read_csv(path)
        stored = stored[(stored["strategy"].isin(names))
                        & (stored["mask_mode"] == "one_shot")
                        & (stored["cooldown_candles"] == COOLDOWN)].copy()
        stored["interval"] = stored["interval"].astype(str)  # CSV reads "240" back as int64
        merged = mine[mine["strategy"].isin(names)].merge(
            stored, on=["symbol", "interval", "strategy"], suffixes=("_new", "_stored"))
        compared += len(merged)
        sources[path] = f"{len(merged)} rows"
        for col in ("net_pnl", "win_rate", "n_trades", "max_drawdown_pct", "final_equity", "n_calls"):
            bad = merged[merged[f"{col}_new"] != merged[f"{col}_stored"]]
            for _, row in bad.iterrows():
                mismatches.append({"symbol": row["symbol"], "interval": row["interval"],
                                   "strategy": row["strategy"], "column": col,
                                   "new": row[f"{col}_new"], "stored": row[f"{col}_stored"]})
    return {"rows_compared": int(compared), "sources": sources,
            "n_mismatches": len(mismatches), "mismatches": mismatches[:20]}


def verify_trade_count_invariance(results: pd.DataFrame) -> dict:
    """Is the 'it only traded less' confound live? Pre-registered as structurally absent.

    Under the one-shot mask an entry is queued only on a call's first bar, so the exit
    parameters should not move n_trades. Measured per (name, symbol, interval) as the
    spread of n_trades over the 9 cells.
    """
    g = results.groupby(["strategy", "symbol", "interval"])["n_trades"]
    spread = (g.max() - g.min())
    rel = (spread / g.mean().replace(0, pd.NA)).dropna()
    per_cell = results.groupby("cell")["n_trades"].sum()
    base_total = int(per_cell.get(_cell_key(*BASELINE_CELL), 0))
    return {
        "series": int(len(spread)),
        "series_with_identical_n_trades_across_cells": int((spread == 0).sum()),
        "max_absolute_spread": int(spread.max()),
        "max_relative_spread_pct": round(float(rel.max() * 100), 3),
        "mean_relative_spread_pct": round(float(rel.mean() * 100), 3),
        "pooled_n_trades_by_cell": {c: int(v) for c, v in per_cell.items()},
        "pooled_n_trades_vs_baseline_pct": {
            c: (round(100.0 * (int(v) - base_total) / base_total, 3) if base_total else None)
            for c, v in per_cell.items()},
    }


def verify_one_shot_rule(results: pd.DataFrame) -> dict:
    violations = results[results["n_trades"] > results["n_calls"]]
    return {"runs": int(len(results)), "violations": int(len(violations)),
            "violating_rows": violations[["symbol", "interval", "strategy", "cell",
                                          "n_trades", "n_calls"]].head(10).to_dict("records")}


# ---------------------------------------------------------------- aggregation

def _cell_key(activate_pct: float, trail_pct: float) -> str:
    return f"a{activate_pct:g}_t{trail_pct:g}"


def _pooled(sub: pd.DataFrame) -> dict:
    """Pooled over every trade in `sub` -- never a mean of per-series ratios."""
    d = trade_stats.pool_decompositions(sub[["n_trades"] + DECOMP_COLUMNS].to_dict("records"))
    n = max(int(sub["n_trades"].sum()), 1)
    be_rate = d["breakeven_win_rate_pct"]
    win_rate = d["win_rate_pct"]
    return {
        "n_runs": int(len(sub)),
        "n_trades": int(sub["n_trades"].sum()),
        "mean_n_trades": round(float(sub["n_trades"].mean()), 1),
        "avg_winner": round(d["avg_winner"], 4),
        "avg_loser": round(d["avg_loser"], 4),
        "reward_risk": round(d["avg_winner"] / abs(d["avg_loser"]), 4) if d["avg_loser"] else None,
        "breakeven_win_rate_pct": round(be_rate, 4) if be_rate is not None else None,
        "win_rate_pct": round(win_rate, 4) if win_rate is not None else None,
        "gap_pp": (round(be_rate - win_rate, 4)
                   if be_rate is not None and win_rate is not None else None),
        "net_per_trade": round(float(sub["net_pnl"].sum()) / n, 4),
        "gross_per_trade": round(float(sub["gross_pnl"].sum()) / n, 4),
        "cost_per_trade": round(float(sub["total_costs"].sum()) / n, 4),
        "mean_net_pnl": round(float(sub["net_pnl"].mean()), 2),
        "mean_max_drawdown_pct": round(float(sub["max_drawdown_pct"].mean()), 2),
        "mean_bars_held": round(float(sub["mean_bars_held"].mean()), 2),
        "exit_mix_pct": {reason: round(100.0 * int(sub[f"exit_{reason}"].sum()) / n, 2)
                         for reason in ("initial_sl", "trailing_sl", "signal_reverse", "end_of_data")},
        "survived": int(sub["survived"].sum()),
        "positive_net_pnl": int((sub["net_pnl"] > 0).sum()),
        "best_net_pnl": round(float(sub["net_pnl"].max()), 2),
    }


def _cell_table(results: pd.DataFrame) -> dict:
    return {_cell_key(a, t): {"activate_pct": a, "trail_pct": t,
                              "lock_in_at_arming": round((1 + a) * (1 - t), 6),
                              **_pooled(results[(results["activate_pct"] == a)
                                                & (results["trail_pct"] == t)])}
            for a, t in CELLS}


def _falsification_verdict(results: pd.DataFrame, cells: dict) -> dict:
    """The condition as pre-registered in the research note, evaluated mechanically."""
    base = cells[_cell_key(*BASELINE_CELL)]
    improvement_bar_pp = 2.0
    trade_drop_bar_pct = 10.0
    candidates = {}
    for key, c in cells.items():
        if key == _cell_key(*BASELINE_CELL):
            continue
        delta_be = c["breakeven_win_rate_pct"] - base["breakeven_win_rate_pct"]
        trade_drop_pct = 100.0 * (base["n_trades"] - c["n_trades"]) / max(base["n_trades"], 1)
        clears_a = delta_be <= -improvement_bar_pp
        fails_b = (trade_drop_pct > trade_drop_bar_pct
                   or c["net_per_trade"] <= base["net_per_trade"]
                   or c["gross_per_trade"] <= base["gross_per_trade"])
        candidates[key] = {
            "delta_breakeven_pp": round(delta_be, 4),
            "clears_clause_a_bar": bool(clears_a),
            "trade_drop_vs_baseline_pct": round(trade_drop_pct, 3),
            "net_per_trade": c["net_per_trade"], "baseline_net_per_trade": base["net_per_trade"],
            "gross_per_trade": c["gross_per_trade"], "baseline_gross_per_trade": base["gross_per_trade"],
            "fails_clause_b": bool(fails_b),
            "survives_both_clauses": bool(clears_a and not fails_b),
        }
    clearing = [k for k, v in candidates.items() if v["clears_clause_a_bar"]]
    surviving = [k for k, v in candidates.items() if v["survives_both_clauses"]]
    best = min(cells.items(), key=lambda kv: kv[1]["breakeven_win_rate_pct"])
    return {
        "baseline_cell": _cell_key(*BASELINE_CELL),
        "baseline_breakeven_win_rate_pct": base["breakeven_win_rate_pct"],
        "baseline_avg_winner": base["avg_winner"], "baseline_avg_loser": base["avg_loser"],
        "improvement_bar_pp": improvement_bar_pp,
        "max_trade_drop_bar_pct": trade_drop_bar_pct,
        "per_cell": candidates,
        "best_cell_by_breakeven": best[0],
        "best_cell_breakeven_win_rate_pct": best[1]["breakeven_win_rate_pct"],
        "clause_a_no_cell_clears_the_bar": len(clearing) == 0,
        "cells_clearing_clause_a": clearing,
        "clause_b_every_clearing_cell_fails": len(clearing) > 0 and len(surviving) == 0,
        "cells_surviving_both": surviving,
        "falsified": len(surviving) == 0,
        # with n_trades > 0 everywhere, "profitable" and "positive per-trade expectancy"
        # are the same condition -- one number, not two dressed up as two
        "profitable_runs_anywhere": int((results["net_pnl"] > 0).sum()),
        "runs_with_zero_trades": int((results["n_trades"] == 0).sum()),
    }


def _monotonicity(cells: dict) -> dict:
    """P1 (raise activate at fixed trail) and P2 (raise trail at fixed activate)."""
    out = {"P1_raise_activate_at_fixed_trail": {}, "P2_raise_trail_at_fixed_activate": {}}
    for t in TRAIL_SWEEP:
        seq = [cells[_cell_key(a, t)] for a in ACTIVATE_SWEEP]
        out["P1_raise_activate_at_fixed_trail"][f"t{t:g}"] = _seq_stats(seq, ACTIVATE_SWEEP)
    for a in ACTIVATE_SWEEP:
        seq = [cells[_cell_key(a, t)] for t in TRAIL_SWEEP]
        out["P2_raise_trail_at_fixed_activate"][f"a{a:g}"] = _seq_stats(seq, TRAIL_SWEEP)
    return out


def _seq_stats(seq: list, xs: list) -> dict:
    aw = [c["avg_winner"] for c in seq]
    al = [c["avg_loser"] for c in seq]
    be = [c["breakeven_win_rate_pct"] for c in seq]
    return {
        "x": xs, "avg_winner": aw, "avg_loser": al, "breakeven_win_rate_pct": be,
        "avg_winner_rises_monotonically": all(b > a for a, b in zip(aw, aw[1:])),
        "breakeven_falls_monotonically": all(b < a for a, b in zip(be, be[1:])),
        "breakeven_net_change_pp": round(be[-1] - be[0], 4),
    }


def _per_name_table(results: pd.DataFrame, cell_key: str) -> dict:
    sub = results[results["cell"] == cell_key]
    return {name: _pooled(sub[sub["strategy"] == name]) for name in ALL_NAMES
            if not sub[sub["strategy"] == name].empty}


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
        "activate_sweep": ACTIVATE_SWEEP,
        "trail_sweep": TRAIL_SWEEP,
        "baseline_cell": _cell_key(*BASELINE_CELL),
        "mask_mode": "one_shot (entry_masks.one_shot_entry_mask, on for every run)",
        "symbols": SYMBOLS,
        "intervals": INTERVALS,
        "fixed_params": {**FIXED_PARAMS, "max_sl_pct": MAX_SL_PCT, "cooldown_candles": COOLDOWN,
                         "initial_equity": INITIAL_EQUITY, "stake": STAKE},
        "warmup_start": WARMUP_START,
        "train1_end": str(TRAIN1_END),
        "now_fixed": str(NOW),
        "data_checksums_verified": {f"{s}_{i}": c for (s, i), c in EXPECTED_CHECKSUMS.items()},
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
        "trade_count_invariance": verify_trade_count_invariance(results),
        "one_shot_rule": verify_one_shot_rule(results),
    }
    verdict = _falsification_verdict(results, cells)
    best_key = verdict["best_cell_by_breakeven"]
    manifest = _manifest(results, t_start, {
        "pass": "merged",
        **checks,
        "means_by_cell": cells,
        "means_by_cell_4h": _cell_table(results[results["interval"] == "240"]),
        "means_by_cell_1h": _cell_table(results[results["interval"] == "60"]),
        "monotonicity": _monotonicity(cells),
        "per_name_baseline_cell": _per_name_table(results, _cell_key(*BASELINE_CELL)),
        "per_name_best_cell": _per_name_table(results, best_key),
        "falsification": verdict,
    })
    with open(f"{OUT_DIR}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    _print_report(manifest, cells, verdict, checks)
    return results


def _print_report(manifest, cells, verdict, checks) -> None:
    b = checks["baseline_cell_vs_stored_notes"]
    print(f"\nbaseline cell vs stored notes: {b['rows_compared']} rows compared, "
          f"{b['n_mismatches']} mismatches  {b['sources']}")
    inv = checks["trade_count_invariance"]
    print(f"trade-count invariance: {inv['series_with_identical_n_trades_across_cells']}/{inv['series']} "
          f"series identical across all 9 cells; max relative spread "
          f"{inv['max_relative_spread_pct']}%, mean {inv['mean_relative_spread_pct']}%")
    print(f"one-shot rule: {checks['one_shot_rule']['violations']}/{checks['one_shot_rule']['runs']} "
          f"runs violate n_trades<=n_calls")

    print(f"\n{'cell':>12} {'lockin':>7} {'avgWin':>7} {'avgLoss':>8} {'R:R':>6} {'breakeven%':>11} "
          f"{'win%':>6} {'gap pp':>7} {'net/tr':>7} {'gross/tr':>9} {'trades':>7} {'pos':>5}")
    for key, c in cells.items():
        flag = "  <= baseline" if key == verdict["baseline_cell"] else ""
        print(f"{key:>12} {c['lock_in_at_arming']:7.4f} {c['avg_winner']:7.3f} {c['avg_loser']:8.3f} "
              f"{c['reward_risk']:6.3f} {c['breakeven_win_rate_pct']:11.2f} {c['win_rate_pct']:6.2f} "
              f"{c['gap_pp']:7.2f} {c['net_per_trade']:7.3f} {c['gross_per_trade']:9.3f} "
              f"{c['n_trades']:7d} {c['positive_net_pnl']:>2}/{c['n_runs']:<3}{flag}")

    print("\n-- monotonicity --")
    for claim, groups in manifest["monotonicity"].items():
        for k, s in groups.items():
            print(f"  {claim} [{k}]: avg_winner {s['avg_winner']} rises={s['avg_winner_rises_monotonically']}  "
                  f"breakeven {s['breakeven_win_rate_pct']} falls={s['breakeven_falls_monotonically']} "
                  f"({s['breakeven_net_change_pp']:+.2f} pp)")

    print("\n-- falsification condition (as pre-registered) --")
    print(f"  baseline {verdict['baseline_cell']}: breakeven={verdict['baseline_breakeven_win_rate_pct']:.2f}%  "
          f"avg_winner={verdict['baseline_avg_winner']}  avg_loser={verdict['baseline_avg_loser']}")
    print(f"  best cell by breakeven: {verdict['best_cell_by_breakeven']} "
          f"({verdict['best_cell_breakeven_win_rate_pct']:.2f}%)")
    print(f"  clause (a) no cell improves breakeven by >= 2.0 pp : {verdict['clause_a_no_cell_clears_the_bar']} "
          f"(clearing: {verdict['cells_clearing_clause_a']})")
    print(f"  clause (b) every clearing cell fails the quality test : {verdict['clause_b_every_clearing_cell_fails']} "
          f"(surviving: {verdict['cells_surviving_both']})")
    print(f"  profitable runs anywhere in the 720: {verdict['profitable_runs_anywhere']}")
    print(f"  => FALSIFIED: {verdict['falsified']}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--catalog":
        run_pass(CATALOG_SAMPLE + DONCHIAN_SAMPLE, "catalog")
    elif mode == "--lorentzian":
        run_pass(LORENTZIAN_SAMPLE, "lorentzian")
    elif mode == "--merge":
        merge()
    else:
        raise SystemExit("usage: f006_trailing_sweep_experiment.py --catalog | --lorentzian | --merge")
