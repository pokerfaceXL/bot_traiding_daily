"""
F005 wave 3 (final): run the frozen baseline measurement.

Loads the exact frozen dataset (spec/research/F005-validation-protocol.md
section 6) for each of the 5 basket symbols x 2 intervals, runs every
strategy in strategy.STRATEGY_CATALOG (79, no subsetting) once as a single
continuous backtest_engine.run_backtest pass over warmup_start..holdout_end
(protocol section 5 execution design -- one continuous run per
(symbol, interval, strategy), sliced afterward for reporting, not one run
per window), classifies the resulting equity curve with
regularity.compute_regularity, and writes:

  - output/f005_baseline/raw/{symbol}_{interval}_{strategy}.json
    (complete per-run record: params, metrics, trades, daily equity/pnl/status,
    monthly regularity table with window membership tags)
  - output/f005_baseline/summary/validation_summary.csv (790 rows, one per
    (symbol, interval, strategy): avg deviation_pct across valid Validation
    1-4 months, net PnL and max drawdown_pct restricted to those months)
  - output/f005_baseline/summary/holdout_summary.csv (same shape, Holdout
    window only -- measurement only, see protocol section 7)
  - output/f005_baseline/summary/dd_flags.csv (rows where the FULL continuous
    run's max_drawdown_pct exceeded 50%)
  - output/f005_baseline/summary/global_extremes.json (worst single month,
    worst single day, longest losing streak, each with full attribution)
  - output/f005_baseline/summary/month_validity_counts.json
  - output/f005_baseline/summary/manifest.json (params used, data checksums,
    git commit, run timestamp -- reproducibility record)

Zero modification to main.py/trader.py/configuration/backtest_apex.py/
backtest_engine.py/costs.py/equity.py/execution.py/data_contract.py/
regularity.py/spec/research/F005-validation-protocol.md -- this script only
reads/calls them and writes new files under output/f005_baseline/.
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import date, datetime, timezone

import pandas as pd

import backtest_engine
import data_contract
import regularity
import strategy

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]
WARMUP_START = "2024-01-26T00:00:00Z"
HOLDOUT_END = "2026-09-01T00:00:00Z"
NOW = pd.Timestamp(HOLDOUT_END)  # fixed, not wall-clock, so filter_closed_candles is deterministic run-to-run

# Non-optimization path defaults, matched exactly to backtest_apex.py's
# LEVERAGE/ATR_MULT/MAX_SL_PCT/ACTIVATE_PCT/TRAIL_PCT/COOLDOWN_CANDLES
# (backtest_apex.py lines 64-72), which read from configuration/default.yaml.
# Same values used uniformly for all 79 strategies -- this is a baseline of
# the existing catalog's default config, not a per-strategy-tuned run.
PARAMS = dict(
    leverage=10,
    atr_multiplier=2.5,
    max_sl_pct=0.03,
    activate_pct=0.03,
    trail_pct=0.015,
    cooldown_candles=0,
)
INITIAL_EQUITY = 500.0
STAKE = 100.0

# Protocol section 6 table -- exact checksums this wave's dataset must match.
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


def _month_range(y1: int, m1: int, y2: int, m2: int) -> list:
    """Inclusive (year, month) list from (y1,m1) to (y2,m2)."""
    out = []
    y, m = y1, m1
    while (y, m) <= (y2, m2):
        out.append((y, m))
        m += 1
        if m == 13:
            m = 1
            y += 1
    return out


# Protocol section 3.2 "Zakres kalendarzowy" column, verbatim.
WINDOWS = {
    "train_1": _month_range(2024, 3, 2025, 2),
    "validation_1": _month_range(2025, 3, 2025, 5),
    "train_2": _month_range(2024, 6, 2025, 5),
    "validation_2": _month_range(2025, 6, 2025, 8),
    "train_3": _month_range(2024, 9, 2025, 8),
    "validation_3": _month_range(2025, 9, 2025, 11),
    "train_4": _month_range(2024, 12, 2025, 11),
    "validation_4": _month_range(2025, 12, 2026, 2),
    "holdout": _month_range(2026, 3, 2026, 8),
}
VALIDATION_WINDOW_NAMES = ["validation_1", "validation_2", "validation_3", "validation_4"]
VALIDATION_MONTHS = sorted(set(m for w in VALIDATION_WINDOW_NAMES for m in WINDOWS[w]))
HOLDOUT_MONTHS = WINDOWS["holdout"]


def _windows_for_month(year: int, month: int) -> list:
    return [name for name, months in WINDOWS.items() if (year, month) in months]


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


def _longest_losing_streak(days) -> tuple:
    """Returns (streak_len, start_date, end_date) for the longest run of
    consecutive non_positive days. Missing/positive days break the streak."""
    best_len, best_start, best_end = 0, None, None
    cur_len, cur_start = 0, None
    for d in days:
        if d.status == "non_positive":
            if cur_len == 0:
                cur_start = d.day
            cur_len += 1
            if cur_len > best_len:
                best_len, best_start, best_end = cur_len, cur_start, d.day
        else:
            cur_len = 0
    return best_len, best_start, best_end


def _ts(x):
    if x is None:
        return None
    return pd.Timestamp(x).isoformat()


def main():
    t_start = time.time()
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None

    strategy_names = sorted(strategy.STRATEGY_CATALOG.keys())
    assert len(strategy_names) == 79, f"expected 79 strategies, found {len(strategy_names)}"

    validation_rows = []
    holdout_rows = []
    dd_flag_rows = []

    worst_month = {"deviation_pct": -1.0}
    worst_day = {"pnl": float("inf")}
    longest_streak = {"streak_len": -1}

    n_invalid_full = 0
    n_invalid_partial = 0
    n_valid_full = 0
    n_valid_partial = 0

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
                    f"from data_cache -- {exc}. Refusing to refetch a possibly-"
                    f"different dataset. Fix the cache and re-run."
                ) from exc
            if manifest.checksum_sha256 != checksum_expected:
                raise SystemExit(
                    f"STOP: checksum mismatch for {symbol}/{interval}: "
                    f"cache has {manifest.checksum_sha256}, protocol section 6 "
                    f"expects {checksum_expected}. Data on disk has drifted from "
                    f"the frozen protocol -- refusing to proceed."
                )

            for strategy_name in strategy_names:
                n_runs += 1
                result = backtest_engine.run_backtest(
                    df, strategy_name, interval=interval, now=NOW, symbol=symbol,
                    initial_equity=INITIAL_EQUITY, stake=STAKE, **PARAMS,
                )
                days, months = regularity.compute_regularity(result.equity_curve)

                month_records = []
                for mr in months:
                    windows = _windows_for_month(mr.year, mr.month)
                    if mr.is_valid:
                        if mr.is_partial:
                            n_valid_partial += 1
                        else:
                            n_valid_full += 1
                    else:
                        if mr.is_partial:
                            n_invalid_partial += 1
                        else:
                            n_invalid_full += 1
                    month_records.append({
                        "year": mr.year, "month": mr.month, "n": mr.n,
                        "n_positive": mr.n_positive, "n_nonpositive": mr.n_nonpositive,
                        "n_missing": mr.n_missing, "is_partial": mr.is_partial,
                        "is_valid": mr.is_valid, "positive_day_pct": mr.positive_day_pct,
                        "deviation_pct": mr.deviation_pct, "target_met": mr.target_met,
                        "windows": windows,
                    })
                    if mr.is_valid and mr.deviation_pct is not None and mr.deviation_pct > worst_month["deviation_pct"]:
                        worst_month = {
                            "symbol": symbol, "interval": interval, "strategy": strategy_name,
                            "year": mr.year, "month": mr.month, "deviation_pct": mr.deviation_pct,
                            "positive_day_pct": mr.positive_day_pct,
                        }

                for d in days:
                    if d.status != "missing" and d.pnl is not None and d.pnl < worst_day["pnl"]:
                        worst_day = {
                            "symbol": symbol, "interval": interval, "strategy": strategy_name,
                            "date": d.day.isoformat(), "pnl": d.pnl,
                        }

                streak_len, streak_start, streak_end = _longest_losing_streak(days)
                if streak_len > longest_streak["streak_len"]:
                    longest_streak = {
                        "symbol": symbol, "interval": interval, "strategy": strategy_name,
                        "streak_len": streak_len,
                        "start_date": streak_start.isoformat() if streak_start else None,
                        "end_date": streak_end.isoformat() if streak_end else None,
                    }

                full_max_dd = result.metrics["max_drawdown_pct"]
                if full_max_dd > 50.0:
                    dd_flag_rows.append({
                        "symbol": symbol, "interval": interval, "strategy": strategy_name,
                        "max_drawdown_pct_full_run": full_max_dd,
                    })

                val_months = [m for m in months if (m.year, m.month) in set(VALIDATION_MONTHS) and m.is_valid]
                val_deviations = [m.deviation_pct for m in val_months]
                validation_rows.append({
                    "symbol": symbol, "interval": interval, "strategy": strategy_name,
                    "n_valid_validation_months": len(val_months),
                    "avg_deviation_pct": (sum(val_deviations) / len(val_deviations)) if val_deviations else None,
                    "net_pnl_validation": _net_pnl_for_months(days, set(VALIDATION_MONTHS)),
                    "max_drawdown_pct_validation": _max_drawdown_for_months(result.equity_curve, set(VALIDATION_MONTHS)),
                })

                hold_months = [m for m in months if (m.year, m.month) in set(HOLDOUT_MONTHS) and m.is_valid]
                hold_deviations = [m.deviation_pct for m in hold_months]
                holdout_rows.append({
                    "symbol": symbol, "interval": interval, "strategy": strategy_name,
                    "n_valid_holdout_months": len(hold_months),
                    "avg_deviation_pct": (sum(hold_deviations) / len(hold_deviations)) if hold_deviations else None,
                    "net_pnl_holdout": _net_pnl_for_months(days, set(HOLDOUT_MONTHS)),
                    "max_drawdown_pct_holdout": _max_drawdown_for_months(result.equity_curve, set(HOLDOUT_MONTHS)),
                })

                raw_record = {
                    "symbol": symbol, "interval": interval, "strategy": strategy_name,
                    "params": {**PARAMS, "initial_equity": INITIAL_EQUITY, "stake": STAKE},
                    "data_checksum_sha256": manifest.checksum_sha256,
                    "metrics": result.metrics,
                    "n_trades": int(len(result.trades)),
                    "trades": [
                        {
                            "position_id": t.get("position_id"), "direction": t.get("direction"),
                            "entry_time": _ts(t.get("entry_time")), "entry_price": t.get("entry_price"),
                            "exit_time": _ts(t.get("exit_time")), "exit_price": t.get("exit_price"),
                            "exit_reason": t.get("exit_reason"), "net_pnl": t.get("net_pnl"),
                            "gross_pnl": t.get("gross_pnl"), "total_costs": t.get("total_costs"),
                            "funding_pnl": t.get("funding_pnl"), "leverage": t.get("leverage"),
                            "notional": t.get("notional"),
                        }
                        for t in result.trades.to_dict("records")
                    ] if not result.trades.empty else [],
                    "daily": [
                        {
                            "date": d.day.isoformat(), "equity": d.equity, "pnl": d.pnl, "status": d.status,
                        }
                        for d in days
                    ],
                    "monthly_regularity": month_records,
                }
                out_path = f"output/f005_baseline/raw/{symbol}_{interval}_{strategy_name}.json"
                with open(out_path, "w") as f:
                    json.dump(raw_record, f)

            print(f"done {symbol}/{interval} ({n_runs} runs so far, {time.time() - t_start:.1f}s elapsed)")

    validation_df = pd.DataFrame(validation_rows)
    holdout_df = pd.DataFrame(holdout_rows)
    dd_flags_df = pd.DataFrame(dd_flag_rows)

    validation_df.to_csv("output/f005_baseline/summary/validation_summary.csv", index=False)
    holdout_df.to_csv("output/f005_baseline/summary/holdout_summary.csv", index=False)
    dd_flags_df.to_csv("output/f005_baseline/summary/dd_flags.csv", index=False)

    with open("output/f005_baseline/summary/global_extremes.json", "w") as f:
        json.dump({
            "worst_month": worst_month,
            "worst_day": worst_day,
            "longest_losing_streak": longest_streak,
        }, f, indent=2, default=str)

    with open("output/f005_baseline/summary/month_validity_counts.json", "w") as f:
        json.dump({
            "n_valid_full": n_valid_full,
            "n_valid_partial": n_valid_partial,
            "n_invalid_full": n_invalid_full,
            "n_invalid_partial": n_invalid_partial,
            "total_months": n_valid_full + n_valid_partial + n_invalid_full + n_invalid_partial,
        }, f, indent=2)

    with open("output/f005_baseline/summary/manifest.json", "w") as f:
        json.dump({
            "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit_parent": commit_sha,
            "n_runs": n_runs,
            "n_strategies": len(strategy_names),
            "symbols": SYMBOLS,
            "intervals": INTERVALS,
            "params": {**PARAMS, "initial_equity": INITIAL_EQUITY, "stake": STAKE},
            "warmup_start": WARMUP_START,
            "holdout_end": HOLDOUT_END,
            "now_fixed": HOLDOUT_END,
            "data_checksums_verified": {f"{sym}_{intv}": chk for (sym, intv), chk in EXPECTED_CHECKSUMS.items()},
            "elapsed_seconds": time.time() - t_start,
        }, f, indent=2)

    print(f"ALL DONE: {n_runs} runs in {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
