"""Pre-registered Train-1 HTF-direction gate for BB_20_25_EMA200.

Run: python3 scripts/f006_bb_20_25_entry_htf_direction.py
The ungated control is reproduced and the freeze record is written before the
single binary gated cell is evaluated. Validation and holdout data are never loaded.
data_cache is read relative to the process cwd; outputs go under this checkout.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import data_contract
import entry_masks
import f006_family_runner as harness

OUT = ROOT / "output/f006_bb_20_25_entry_htf_direction"
REFERENCE = ROOT / "output/f006_signal_autopsy/catalog5_ema_bb/summary/results.csv"
CONTROL_NAME = "BB_20_25_EMA200"
EXPECTED_MEAN = 82.900262
EXPECTED_COHORT_N = 512
EXPECTED_COHORT_NET = 709.8492091190283
BIG_WINNER_THRESHOLD = 29.9
HTF_BARS = 4
GATED_LABEL = "htf_4"
KEY = ["symbol", "interval", "entry_time", "direction"]


def htf_direction(bars, interval_minutes, htf_bars=HTF_BARS):
    """Direction of the prior fully closed HTF bucket for each native bar.

    Buckets are Unix-epoch floors of bar open time to htf_bars * interval. For a
    bar opening at t the bucket used opens at floor(t) - htf, so it closes at
    floor(t) <= t and never contains the bar itself. The bucket must hold all
    htf_bars native opens; incomplete buckets and flat candles give 0.
    """
    native = pd.Timedelta(minutes=int(interval_minutes))
    htf_ns = (native * htf_bars).value
    idx = pd.DatetimeIndex(bars.index)
    ns = idx.asi8
    prior_open = pd.DatetimeIndex(ns - ns % htf_ns - htf_ns, tz=idx.tz)
    opens = bars["open"]
    closes = bars["close"]
    complete = np.ones(len(idx), dtype=bool)
    for k in range(htf_bars):
        complete &= (prior_open + k * native).isin(idx)
    first_open = opens.reindex(prior_open).to_numpy(dtype=float)
    last_close = closes.reindex(prior_open + (htf_bars - 1) * native).to_numpy(dtype=float)
    direction = np.where(last_close > first_open, 1, np.where(last_close < first_open, -1, 0))
    return pd.Series(np.where(complete, direction, 0), index=bars.index, dtype=int)


def htf_direction_gate(bars, signal, interval_minutes):
    """Keep long only on prior HTF +1 and short only on prior HTF -1."""
    signal = entry_masks.normalized_signal(signal).reindex(bars.index).fillna(0).astype(int)
    direction = htf_direction(bars, interval_minutes)
    return ((signal != 0) & (signal == direction)).astype(bool)


def htf_direction_entry_mask(bars, signal, interval_minutes, gated):
    one_shot = entry_masks.one_shot_entry_mask(signal)
    if not gated:
        return one_shot
    gate = htf_direction_gate(bars.reindex(one_shot.index), signal, interval_minutes)
    return one_shot & gate.reindex(one_shot.index).fillna(False)


def entry_mask(bars, interval, gated):
    closed, _ = data_contract.filter_closed_candles(bars, interval, now=harness.NOW)
    signal = entry_masks.strategy_signal_series(
        closed, CONTROL_NAME, interval=interval, now=harness.NOW,
    )
    return htf_direction_entry_mask(closed, signal, int(interval), gated)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str) + "\n")


def run_cell(data, label, gated):
    rows, blotters = [], []
    directory = OUT / label
    for (symbol, interval), bars in data.items():
        mask = entry_mask(bars, interval, gated)
        row = harness._run_one(
            bars, mask, symbol, interval, CONTROL_NAME, int(mask.sum()),
            autopsy_dir=directory / "blotters",
        )
        if row["exit_trailing_sl"] or row["exit_take_profit"]:
            raise AssertionError("NO_TRAIL exit geometry changed")
        if row["n_trades"] > row["n_calls"]:
            raise AssertionError("one-shot invariant failed")
        row.update(cell=label, gated=gated)
        dump(directory / "raw" / f"{symbol}_{interval}.json", row)
        rows.append(row)
        blotter = pd.read_csv(directory / "blotters" / row["signal_autopsy"]["blotter"])
        blotter["interval"] = str(interval)
        blotters.append(blotter.loc[blotter.train1_entry == True])  # noqa: E712
    return rows, pd.concat(blotters, ignore_index=True)


def _monthly(cohort):
    months = cohort.entry_time.str[:7]
    return cohort.groupby(months).net_pnl.sum().reindex(
        [f"{year}-{month:02d}" for year, month in harness.TRAIN1_MONTHS], fill_value=0,
    )


def score_cell(rows, cohort, baseline, baseline_mean, baseline_sl_share, baseline_losing_months):
    winners = baseline.loc[baseline.net_pnl >= BIG_WINNER_THRESHOLD]
    matched = baseline.merge(cohort, on=KEY, suffixes=("_base", "_gate"), how="inner")
    for col in ("net_pnl", "exit_time", "exit_reason"):
        mismatches = matched[matched[f"{col}_base"] != matched[f"{col}_gate"]]
        if len(mismatches):
            raise AssertionError(f"matched trade {col} changed")
    retained = winners.merge(cohort[KEY], on=KEY, how="inner")
    winner_pnl = float(winners.net_pnl.sum())
    retained_pnl = float(retained.net_pnl.sum())
    sl_share = float((cohort.exit_reason == "initial_sl").mean()) if len(cohort) else None
    frame = pd.DataFrame(rows)
    mean = float(frame.train1_net_pnl.mean())
    monthly = _monthly(cohort)
    per_symbol_months = {
        symbol: int((_monthly(cohort.loc[cohort.symbol == symbol]) < 0).sum())
        for symbol in harness.SYMBOLS
    }
    checks = {
        "mean_beats_control": mean > baseline_mean,
        "initial_sl_down_10pp": sl_share is not None and baseline_sl_share - sl_share >= 0.10,
        "big_winner_pnl_retained_50pct": winner_pnl > 0 and retained_pnl / winner_pnl >= 0.5,
        "pooled_losing_month_floor_improves": int((monthly < 0).sum()) < baseline_losing_months,
        "not_thin": len(cohort) / 10 >= 10,
    }
    return {
        "cell": rows[0]["cell"], "gated": rows[0]["gated"],
        "mean_train1_net_pnl": mean,
        "pooled_train1_net_pnl": float(frame.train1_net_pnl.sum()),
        "entry_cohort_net_pnl": float(cohort.net_pnl.sum()),
        "entry_cohort_net_per_trade": float(cohort.net_pnl.mean()) if len(cohort) else None,
        "n_train1_entry_trades": len(cohort), "mean_n_trades_per_series": len(cohort) / 10,
        "n_closed_trades_including_warmup": int(frame.n_trades.sum()),
        "initial_sl_share": sl_share,
        "initial_sl_share_drop_pp": 100 * (baseline_sl_share - sl_share) if sl_share is not None else None,
        "baseline_big_winner_count": len(winners), "retained_big_winner_count": len(retained),
        "baseline_big_winner_pnl": winner_pnl, "retained_big_winner_pnl": retained_pnl,
        "big_winner_pnl_retained_fraction": retained_pnl / winner_pnl if winner_pnl else None,
        "losing_entry_months": int((monthly < 0).sum()),
        "entry_month_net_pnl": monthly.to_dict(),
        "n_net_positive_symbols": int((frame.groupby("symbol").train1_net_pnl.sum() > 0).sum()),
        "per_symbol_train1_net_pnl": frame.groupby("symbol").train1_net_pnl.sum().to_dict(),
        "per_symbol_losing_entry_months": per_symbol_months,
        "checks": checks, "pass": all(checks.values()),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    log_lines = []

    def log(message):
        print(message, flush=True)
        log_lines.append(message)
        (OUT / "run.log").write_text("\n".join(log_lines) + "\n")

    data, checksums = {}, {}
    for symbol in harness.SYMBOLS:
        for interval in harness.INTERVALS:
            bars, data_manifest = harness.load_train1(symbol, interval)
            data[symbol, interval] = bars
            checksums[f"{symbol}_{interval}"] = data_manifest.checksum_sha256

    controls, baseline = run_cell(data, "control", False)
    replay = harness.verify_harness_control(controls, CONTROL_NAME, str(REFERENCE))
    prior = pd.read_csv(REFERENCE)
    prior["interval"] = prior.interval.astype(str)
    joined = pd.DataFrame(controls).merge(
        prior, on=["symbol", "interval", "strategy"], suffixes=("", "_prior"),
    )
    if len(joined) != 10 or (joined.train1_net_pnl - joined.train1_net_pnl_prior).abs().max() > 1e-6:
        raise AssertionError("Train-1 control PnL replay failed")
    baseline_mean = float(pd.DataFrame(controls).train1_net_pnl.mean())
    if abs(baseline_mean - EXPECTED_MEAN) > 1e-6:
        raise AssertionError(f"baseline mean {baseline_mean} != {EXPECTED_MEAN}")
    if len(baseline) != EXPECTED_COHORT_N or abs(float(baseline.net_pnl.sum()) - EXPECTED_COHORT_NET) > 1e-6:
        raise AssertionError("control entry cohort did not reproduce the pre-registered baseline")
    baseline_sl_share = float((baseline.exit_reason == "initial_sl").mean())
    baseline_losing_months = int((_monthly(baseline) < 0).sum())
    if baseline_losing_months != 7:
        raise AssertionError(f"control losing-month floor {baseline_losing_months} != 7")

    manifest = {
        "hypothesis": "H-BB-20-25-ENTRY-HTF-DIRECTION-01",
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=ROOT).strip(),
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in ("scripts/f006_bb_20_25_entry_htf_direction.py", "scripts/f006_family_runner.py", "entry_masks.py")
        },
        "python": sys.version, "pandas": pd.__version__, "checksums_used": checksums,
        "data_window": [harness.WARMUP_START, str(harness.TRAIN1_END)],
        "validation_holdout_loaded": False,
        "params": {"activate_pct": harness.ACTIVATE_PCT, "trail_pct": harness.TRAIL_PCT,
                   "max_sl_pct": harness.MAX_SL_PCT, "cooldown_candles": harness.COOLDOWN,
                   "stake": harness.STAKE, "initial_equity": harness.INITIAL_EQUITY, **harness.FIXED_PARAMS},
        "mask": ("BB_20_25_EMA200 one_shot AND signal direction == sign(close-open) of the prior fully closed "
                 "4-native-bar HTF bucket (Unix-epoch floor of bar open; bucket close <= signal bar open; "
                 "exactly 4 native bars else reject; flat rejects); exits use ungated signal"),
        "htf_bars": HTF_BARS, "htf_minutes": {str(i): HTF_BARS * int(i) for i in harness.INTERVALS},
        "cache_dir": str(Path("data_cache").resolve()),
        "big_winner_definition_frozen": f"baseline trade net_pnl >= {BIG_WINNER_THRESHOLD}",
        "gated_cells": [GATED_LABEL], "number_of_trials": 1,
        "harness_control": replay, "control_mean_train1_net_pnl": baseline_mean,
        "control_entry_cohort_n": len(baseline), "control_entry_cohort_net_pnl": float(baseline.net_pnl.sum()),
        "control_losing_entry_months": baseline_losing_months,
        "metric_cohort": "2024-03-01 <= entry_time < 2025-03-01 UTC",
        "retention": "sum baseline net>=29.9 trades retained by symbol/interval/entry_time/direction; matched economics must be identical",
    }
    dump(OUT / "grid_freeze.json", manifest)
    log(f"Control replay: 10/10 exact; mean={baseline_mean:.6f}; cohort={len(baseline)} trades / net={baseline.net_pnl.sum():.6f}; losing months={baseline_losing_months}")

    summaries = [score_cell(controls, baseline, baseline, baseline_mean, baseline_sl_share, baseline_losing_months)]
    dump(OUT / "control" / "summary.json", summaries[0])
    all_rows = list(controls)
    rows, cohort = run_cell(data, GATED_LABEL, True)
    gated = score_cell(rows, cohort, baseline, baseline_mean, baseline_sl_share, baseline_losing_months)
    dump(OUT / GATED_LABEL / "summary.json", gated)
    summaries.append(gated)
    all_rows.extend(rows)
    log(json.dumps(gated))

    pd.DataFrame(all_rows)[["cell", "gated", *harness.SUMMARY_COLUMNS]].to_csv(OUT / "results.csv", index=False)
    nested = {"checks", "entry_month_net_pnl", "per_symbol_train1_net_pnl", "per_symbol_losing_entry_months"}
    pd.DataFrame([{k: v for k, v in summary.items() if k not in nested} for summary in summaries]).to_csv(
        OUT / "cell_summary.csv", index=False,
    )
    checks = gated["checks"]
    falsifiers = {
        "a_mean_not_above_control": not checks["mean_beats_control"],
        "b_removes_over_half_big_winner_pnl": not checks["big_winner_pnl_retained_50pct"],
        "c_initial_sl_fails_10pp_drop": not checks["initial_sl_down_10pp"],
        "d_pooled_losing_month_floor_not_improved": not checks["pooled_losing_month_floor_improves"],
        "e_thin_under_10_trades_per_series": not checks["not_thin"],
    }
    manifest.update(cells=summaries, falsifiers=falsifiers,
                    hypothesis_falsified=any(falsifiers.values()),
                    passing_cells=[GATED_LABEL] if gated["pass"] else [],
                    no_trail_violations=0, retained_trade_economics_mismatches=0)
    dump(OUT / "manifest.json", manifest)
    log(f"Falsifiers: {json.dumps(falsifiers)}; passing cells: {manifest['passing_cells']}")


if __name__ == "__main__":
    main()
