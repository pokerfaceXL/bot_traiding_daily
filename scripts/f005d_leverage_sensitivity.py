"""
F005 addendum (not a new numbered feature) -- leverage/cooldown sensitivity
diagnostic, built on the frozen wave 3 baseline
(spec/research/F005-baseline.md): 0/24885 valid months met the regularity
target, 790/790 combos exceeded 50% max DD, root cause was leverage=10 +
margin=stake=$100 burning the $500 shared portfolio below the $100
re-entry floor within 1-3 months, for every strategy in the catalog.

Purpose: pure measurement for an open owner decision (spec/build.md flags
leverage as undecided -- "otwarte: dzwignia i szczegoly operacyjne"). Does
NOT touch configuration/default.yaml, backtest_apex.py's defaults, the
frozen protocol (spec/research/F005-validation-protocol.md), or any of the
wave 1-3 baseline files/outputs (spec/research/F005-baseline.md,
output/f005_baseline/, scripts/f005_run_baseline.py) -- this is a new,
separate, read-only-of-those-files diagnostic run.

Same methodology as scripts/f005_run_baseline.py: same frozen dataset via
data_contract.load_dataset with the same checksums from
spec/research/F005-validation-protocol.md section 6, same 5 symbols x
2 intervals, one continuous warmup_start->holdout_end run per
(symbol, interval, strategy, leverage, cooldown_candles), same costs
(backtest_engine.run_backtest defaults), same regularity.py classification.

Reduced scope vs wave 3, to keep runtime bounded for a diagnostic:

- 10 representative strategies (see STRATEGY_SAMPLE below), not all 79.
- leverage in {1, 2, 3, 5} swept at cooldown_candles=0 (wave 3's value).
  leverage=10 is NOT rerun -- reused from output/f005_baseline/summary/
  (validation_summary.csv + dd_flags.csv), restricted to the 10 sampled
  strategies, per the ticket's explicit instruction not to rerun it.
- cooldown_candles in {5, 20} swept at leverage=10 (wave 3's value), to
  isolate whether cooldown alone (immediate re-entry after every stop was
  named as a contributing factor in F005-baseline.md) restores
  survivability independent of leverage.

Output: output/f005d_leverage_sensitivity/summary/sweep_results.csv (one
row per (symbol, interval, strategy, leverage, cooldown_candles) --
including the reused leverage=10/cooldown=0 rows, so the full grid is in
one table) and .../summary/manifest.json. No per-run raw trade/equity dump
is written -- unlike wave 3's 86 MB raw/*.json, this diagnostic's per-run
detail (final_equity, min_equity, max_drawdown_pct, validation deviations)
is fully captured in the summary row, and the reduced grid (610 rows) is
small enough to commit directly, so there is no raw/ directory needing a
.gitignore entry this time.
"""
from __future__ import annotations

import itertools
import json
import statistics
import subprocess
import time
from datetime import datetime, timezone

import pandas as pd

import backtest_engine
import data_contract
import regularity
import strategy

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]
WARMUP_START = "2024-01-26T00:00:00Z"
HOLDOUT_END = "2026-09-01T00:00:00Z"
NOW = pd.Timestamp(HOLDOUT_END)

# Protocol section 6 checksums -- duplicated here (not imported), same
# convention scripts/f005_run_baseline.py itself uses: this script does not
# import from or modify that frozen file, it re-verifies independently
# against the same protocol table before using cached data.
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

# Non-swept params, identical to wave 3 (F005-baseline.md / f005_run_baseline.py).
BASE_PARAMS = dict(
    atr_multiplier=2.5,
    max_sl_pct=0.03,
    activate_pct=0.03,
    trail_pct=0.015,
)
INITIAL_EQUITY = 500.0
STAKE = 100.0
REENTRY_FLOOR = 100.0  # margin = stake at leverage>=1 per equity.py's contract; below this the engine can never open another position

# 10 strategies covering every family present in strategy.STRATEGY_CATALOG
# (checked against strategy.py naming: ADX*, BB_*, EMA*/EMA3_*/EMA_BB_ADX_*,
# MACD_*, RSI*, STOCH*, TS_* -- 7 families total). Ticket requires EMA, RSI,
# MACD, Bollinger Bands, ADX explicitly, plus at least one from each other
# family present (STOCH, TS). Picks below cover all 7, with a mix of
# single-indicator and multi-indicator-combo strategies within a family
# where budget allowed, and reuse two strategies wave 3 already singled out
# (STOCH14_cross = worst-ever combo, 949-day non-positive streak;
# TS_13_34_200_14 = least-catastrophic for DOGEUSDT/240) so this diagnostic's
# numbers are directly cross-referenceable against F005-baseline.md.
STRATEGY_SAMPLE = [
    "EMA_8_21",              # EMA family, plain crossover
    "EMA_13_34_RSI14_55",    # EMA family, EMA+RSI combo variant
    "RSI14_7030",            # RSI family, plain
    "MACD_12_26_hist",       # MACD family, plain
    "MACD_RSI14_50",         # MACD family, MACD+RSI combo variant
    "BB_20_25_breakout",     # Bollinger Bands family, breakout variant
    "BB_20_2_RSI14",         # Bollinger Bands family, BB+RSI combo variant
    "ADX14_DI_20",           # ADX family
    "STOCH14_cross",         # Stochastic family -- wave 3's worst-ever combo
    "TS_13_34_200_14",       # Triple Screen family -- wave 3's least-catastrophic for DOGEUSDT/240
]

# Sweep grid: (leverage, cooldown_candles). leverage=10/cooldown=0 (wave 3's
# defaults) intentionally excluded here -- reused from output/f005_baseline/
# summary/ instead of rerun (see _reused_leverage10_rows below).
LEVERAGE_SWEEP = [1, 2, 3, 5]  # at cooldown_candles=0
COOLDOWN_SWEEP = [5, 20]       # at leverage=10


def _month_range(y1: int, m1: int, y2: int, m2: int) -> list:
    out = []
    y, m = y1, m1
    while (y, m) <= (y2, m2):
        out.append((y, m))
        m += 1
        if m == 13:
            m = 1
            y += 1
    return out


# Protocol section 3.2, validation windows only (this diagnostic reuses
# wave 3's holdout/train numbers as-is where needed; it does not re-derive
# them -- only VALIDATION_MONTHS is needed for the per-run deviation stats
# requested in the ticket).
VALIDATION_MONTHS = sorted(set(
    m
    for w in (
        _month_range(2025, 3, 2025, 5),
        _month_range(2025, 6, 2025, 8),
        _month_range(2025, 9, 2025, 11),
        _month_range(2025, 12, 2026, 2),
    )
    for m in w
))
VALIDATION_MONTHS_SET = set(VALIDATION_MONTHS)


def _net_pnl_for_months(days, months_set) -> float:
    total = 0.0
    for d in days:
        if (d.day.year, d.day.month) in months_set and d.status != "missing":
            total += d.pnl
    return total


def _max_drawdown_for_months(equity_curve: pd.DataFrame, months_set) -> float:
    if equity_curve.empty:
        return 0.0
    idx = pd.DatetimeIndex(equity_curve.index).tz_convert(regularity.WARSAW_TZ)
    mask = [(ts.year, ts.month) in months_set for ts in idx]
    subset = equity_curve.loc[mask]
    if subset.empty:
        return 0.0
    return float(subset["drawdown_pct"].max())


def _run_one(df, symbol, interval, strategy_name, leverage, cooldown_candles) -> dict:
    result = backtest_engine.run_backtest(
        df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE,
        leverage=leverage, cooldown_candles=cooldown_candles, **BASE_PARAMS,
    )
    days, months = regularity.compute_regularity(result.equity_curve)

    val_months = [m for m in months if (m.year, m.month) in VALIDATION_MONTHS_SET and m.is_valid]
    val_deviations = [m.deviation_pct for m in val_months if m.deviation_pct is not None]
    n_val_target_met = sum(1 for m in val_months if m.target_met)

    final_equity = result.metrics["final_equity"]
    min_equity = float(result.equity_curve["equity"].min()) if not result.equity_curve.empty else INITIAL_EQUITY
    last_trade_exit = result.trades["exit_time"].max() if not result.trades.empty else None

    return {
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "leverage": leverage, "cooldown_candles": cooldown_candles,
        "n_trades": int(len(result.trades)),
        "final_equity": final_equity,
        "min_equity_full_run": min_equity,
        "survives_to_holdout_end": bool(final_equity >= REENTRY_FLOOR),
        "net_pnl_full_run": result.metrics["total_net_pnl"],
        "max_drawdown_pct_full_run": result.metrics["max_drawdown_pct"],
        "n_valid_validation_months": len(val_months),
        "n_validation_months_target_met": n_val_target_met,
        "frac_validation_target_met": (n_val_target_met / len(val_months)) if val_months else None,
        "best_deviation_pct_validation": min(val_deviations) if val_deviations else None,
        "median_deviation_pct_validation": statistics.median(val_deviations) if val_deviations else None,
        "worst_deviation_pct_validation": max(val_deviations) if val_deviations else None,
        "net_pnl_validation": _net_pnl_for_months(days, VALIDATION_MONTHS_SET),
        "max_drawdown_pct_validation": _max_drawdown_for_months(result.equity_curve, VALIDATION_MONTHS_SET),
        "last_trade_exit_time": str(last_trade_exit) if last_trade_exit is not None else None,
        "source": "measured",
    }


def _reused_leverage10_rows() -> list:
    """
    leverage=10, cooldown_candles=0 rows for the 10 sampled strategies,
    reused from output/f005_baseline/summary/ (wave 3), not rerun -- per
    the ticket's explicit instruction. validation_summary.csv and
    dd_flags.csv don't carry final_equity/min_equity directly, but
    F005-baseline.md's wave 3 prose establishes, for ALL 790 combos
    (so including these 10): final_equity in [$66.86, $99.96] (always
    < $100 -> never survives) and avg_deviation_pct == 100.0 with std==0.0
    across the whole 790-row table, which is only possible if every single
    valid Validation month has deviation_pct == 100.0 exactly (a mean of
    100.0 over values bounded in [0, 100] forces every value to be 100.0)
    -- i.e. frac_validation_target_met == 0.0 for every one of these rows,
    without needing to reopen the (gitignored, not present in this
    worktree) raw/*.json files to recompute it.
    """
    val_df = pd.read_csv("output/f005_baseline/summary/validation_summary.csv")
    dd_df = pd.read_csv("output/f005_baseline/summary/dd_flags.csv")
    rows = []
    for strat in STRATEGY_SAMPLE:
        for symbol in SYMBOLS:
            for interval in INTERVALS:
                interval_i = int(interval)
                v = val_df[(val_df.symbol == symbol) & (val_df.interval == interval_i) & (val_df.strategy == strat)]
                d = dd_df[(dd_df.symbol == symbol) & (dd_df.interval == interval_i) & (dd_df.strategy == strat)]
                assert len(v) == 1, f"expected exactly 1 wave-3 validation row for {symbol}/{interval}/{strat}, found {len(v)}"
                assert len(d) == 1, f"expected exactly 1 wave-3 dd_flags row for {symbol}/{interval}/{strat}, found {len(d)}"
                v = v.iloc[0]
                d = d.iloc[0]
                n_valid = int(v.n_valid_validation_months)
                avg_dev = v.avg_deviation_pct
                assert avg_dev is None or pd.isna(avg_dev) or avg_dev == 100.0, (
                    f"wave-3 assumption violated for {symbol}/{interval}/{strat}: "
                    f"avg_deviation_pct={avg_dev} != 100.0 -- cannot safely infer "
                    f"frac_validation_target_met==0.0 for this row, reuse logic needs revisiting"
                )
                rows.append({
                    "symbol": symbol, "interval": interval, "strategy": strat,
                    "leverage": 10, "cooldown_candles": 0,
                    "n_trades": None,
                    "final_equity": None,
                    "min_equity_full_run": None,
                    "survives_to_holdout_end": False,  # F005-baseline.md: final_equity band $66.86-$99.96 for all 790, always < $100
                    "net_pnl_full_run": None,
                    "max_drawdown_pct_full_run": float(d.max_drawdown_pct_full_run),
                    "n_valid_validation_months": n_valid,
                    "n_validation_months_target_met": 0,
                    "frac_validation_target_met": 0.0 if n_valid else None,
                    "best_deviation_pct_validation": 100.0 if n_valid else None,
                    "median_deviation_pct_validation": 100.0 if n_valid else None,
                    "worst_deviation_pct_validation": 100.0 if n_valid else None,
                    "net_pnl_validation": float(v.net_pnl_validation),
                    "max_drawdown_pct_validation": float(v.max_drawdown_pct_validation),
                    "last_trade_exit_time": None,
                    "source": "reused_wave3_output/f005_baseline/summary",
                })
    return rows


def main():
    t_start = time.time()
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None

    for name in STRATEGY_SAMPLE:
        assert name in strategy.STRATEGY_CATALOG, f"strategy {name!r} not in strategy.STRATEGY_CATALOG"

    grid = [(lev, 0) for lev in LEVERAGE_SWEEP] + [(10, cd) for cd in COOLDOWN_SWEEP]

    rows = []
    n_runs = 0
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            checksum_expected = EXPECTED_CHECKSUMS[(symbol, interval)]
            try:
                df, manifest = data_contract.load_dataset(
                    "data_cache", symbol, interval, WARMUP_START, HOLDOUT_END
                )
            except data_contract.DataContractError as exc:
                raise SystemExit(
                    f"STOP: cannot load frozen dataset for {symbol}/{interval} "
                    f"from data_cache -- {exc}."
                ) from exc
            if manifest.checksum_sha256 != checksum_expected:
                raise SystemExit(
                    f"STOP: checksum mismatch for {symbol}/{interval}: "
                    f"cache has {manifest.checksum_sha256}, protocol section 6 "
                    f"expects {checksum_expected}."
                )

            for strategy_name, (leverage, cooldown_candles) in itertools.product(STRATEGY_SAMPLE, grid):
                n_runs += 1
                rows.append(_run_one(df, symbol, interval, strategy_name, leverage, cooldown_candles))

            print(f"done {symbol}/{interval} ({n_runs} runs so far, {time.time() - t_start:.1f}s elapsed)")

    rows.extend(_reused_leverage10_rows())

    results_df = pd.DataFrame(rows)
    results_df.to_csv("output/f005d_leverage_sensitivity/summary/sweep_results.csv", index=False)

    with open("output/f005d_leverage_sensitivity/summary/manifest.json", "w") as f:
        json.dump({
            "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit_parent": commit_sha,
            "n_measured_runs": n_runs,
            "n_reused_rows": len(rows) - n_runs,
            "n_total_rows": len(rows),
            "strategy_sample": STRATEGY_SAMPLE,
            "leverage_sweep_at_cooldown_0": LEVERAGE_SWEEP,
            "cooldown_sweep_at_leverage_10": COOLDOWN_SWEEP,
            "leverage_10_cooldown_0_source": "reused from output/f005_baseline/summary/ (wave 3), not rerun",
            "symbols": SYMBOLS,
            "intervals": INTERVALS,
            "base_params": {**BASE_PARAMS, "initial_equity": INITIAL_EQUITY, "stake": STAKE},
            "warmup_start": WARMUP_START,
            "holdout_end": HOLDOUT_END,
            "now_fixed": HOLDOUT_END,
            "data_checksums_verified": {f"{sym}_{intv}": chk for (sym, intv), chk in EXPECTED_CHECKSUMS.items()},
            "elapsed_seconds": time.time() - t_start,
        }, f, indent=2)

    print(f"ALL DONE: {n_runs} measured runs + {len(rows) - n_runs} reused rows in {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
