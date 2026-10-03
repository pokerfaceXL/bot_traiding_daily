"""Pre-registered Train-1 candle-confirmation gate for BB_20_25_EMA200.

Run: python3 scripts/f006_bb_20_25_entry_candle_confirm.py
The ungated control is reproduced and the fixed threshold grid is written before
any gated cell is evaluated. Validation and holdout data are never loaded.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import data_contract
import entry_masks
import f006_family_runner as harness

OUT = ROOT / "output/f006_bb_20_25_entry_candle_confirm"
REFERENCE = "output/f006_signal_autopsy/catalog5_ema_bb/summary/results.csv"
CONTROL_NAME = "BB_20_25_EMA200"
EXPECTED_MEAN = 82.900262
EXPECTED_COHORT_N = 512
EXPECTED_COHORT_NET = 709.8492091190283
BIG_WINNER_THRESHOLD = 29.9
THRESHOLDS = (0.50, 0.60, 0.70, 0.80, 0.90)
KEY = ["symbol", "interval", "entry_time", "direction"]


def candle_confirmation_gate(bars, signal, threshold):
    """Directional close location on the closed signal bar; zero-range bars fail."""
    signal = entry_masks.normalized_signal(signal).reindex(bars.index).fillna(0).astype(int)
    bar_range = bars["high"] - bars["low"]
    valid = bar_range > 0
    long_strength = (bars["close"] - bars["low"]) / bar_range
    short_strength = (bars["high"] - bars["close"]) / bar_range
    return (
        valid
        & (((signal == 1) & (long_strength >= threshold))
           | ((signal == -1) & (short_strength >= threshold)))
    ).fillna(False).astype(bool)


def candle_confirmation_entry_mask(bars, signal, threshold):
    one_shot = entry_masks.one_shot_entry_mask(signal)
    if threshold is None:
        return one_shot
    gate = candle_confirmation_gate(bars.reindex(one_shot.index), signal, threshold)
    return one_shot & gate.reindex(one_shot.index).fillna(False)


def entry_mask(bars, interval, threshold):
    closed, _ = data_contract.filter_closed_candles(bars, interval, now=harness.NOW)
    signal = entry_masks.strategy_signal_series(
        closed, CONTROL_NAME, interval=interval, now=harness.NOW,
    )
    return candle_confirmation_entry_mask(closed, signal, threshold)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str) + "\n")


def run_cell(data, label, threshold):
    rows, blotters = [], []
    directory = OUT / label
    for (symbol, interval), bars in data.items():
        mask = entry_mask(bars, interval, threshold)
        row = harness._run_one(
            bars, mask, symbol, interval, CONTROL_NAME, int(mask.sum()),
            autopsy_dir=directory / "blotters",
        )
        if row["exit_trailing_sl"] or row["exit_take_profit"]:
            raise AssertionError("NO_TRAIL exit geometry changed")
        if row["n_trades"] > row["n_calls"]:
            raise AssertionError("one-shot invariant failed")
        row.update(cell=label, threshold=threshold)
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
        "cell": rows[0]["cell"], "threshold": rows[0]["threshold"],
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

    controls, baseline = run_cell(data, "control", None)
    replay = harness.verify_harness_control(controls, CONTROL_NAME, REFERENCE)
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

    grid = [(f"t_{str(value).replace('.', '_')}", value) for value in THRESHOLDS]
    manifest = {
        "hypothesis": "H-BB-20-25-ENTRY-CANDLE-CONFIRM-01",
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in ("scripts/f006_bb_20_25_entry_candle_confirm.py", "scripts/f006_family_runner.py", "entry_masks.py")
        },
        "python": sys.version, "pandas": pd.__version__, "checksums_used": checksums,
        "data_window": [harness.WARMUP_START, str(harness.TRAIN1_END)],
        "validation_holdout_loaded": False,
        "params": {"activate_pct": harness.ACTIVATE_PCT, "trail_pct": harness.TRAIL_PCT,
                   "max_sl_pct": harness.MAX_SL_PCT, "cooldown_candles": harness.COOLDOWN,
                   "stake": harness.STAKE, "initial_equity": harness.INITIAL_EQUITY, **harness.FIXED_PARAMS},
        "mask": "BB_20_25_EMA200 one_shot AND directional signal-bar close strength >= T; zero range rejects; exits use ungated signal",
        "big_winner_definition_frozen": f"baseline trade net_pnl >= {BIG_WINNER_THRESHOLD}",
        "threshold_grid": list(THRESHOLDS), "number_of_trials": 5,
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
    for label, threshold in grid:
        rows, cohort = run_cell(data, label, threshold)
        summary = score_cell(rows, cohort, baseline, baseline_mean, baseline_sl_share, baseline_losing_months)
        dump(OUT / label / "summary.json", summary)
        summaries.append(summary)
        all_rows.extend(rows)
        log(json.dumps(summary))

    pd.DataFrame(all_rows)[["cell", "threshold", *harness.SUMMARY_COLUMNS]].to_csv(OUT / "results.csv", index=False)
    nested = {"checks", "entry_month_net_pnl", "per_symbol_train1_net_pnl", "per_symbol_losing_entry_months"}
    pd.DataFrame([{k: v for k, v in summary.items() if k not in nested} for summary in summaries]).to_csv(
        OUT / "cell_summary.csv", index=False,
    )
    gated = summaries[1:]
    best = max(gated, key=lambda item: item["mean_train1_net_pnl"])
    otherwise_qualifying = [
        item for item in gated
        if item["checks"]["mean_beats_control"]
        and item["checks"]["initial_sl_down_10pp"]
        and item["checks"]["big_winner_pnl_retained_50pct"]
        and item["checks"]["not_thin"]
    ]
    falsifiers = {
        "a_all_thresholds_fail_to_beat_mean_control": all(not item["checks"]["mean_beats_control"] for item in gated),
        "b_every_non_thin_threshold_removes_over_half_big_winner_pnl": all(
            not item["checks"]["big_winner_pnl_retained_50pct"]
            for item in gated if item["checks"]["not_thin"]
        ),
        "c_best_pnl_threshold_fails_10pp_initial_sl_drop": not best["checks"]["initial_sl_down_10pp"],
        "d_no_otherwise_qualifying_threshold_improves_month_floor": bool(otherwise_qualifying) and not any(
            item["checks"]["pooled_losing_month_floor_improves"] for item in otherwise_qualifying
        ),
        "e_improvement_only_thin": any(item["checks"]["mean_beats_control"] for item in gated)
        and not any(item["checks"]["mean_beats_control"] and item["checks"]["not_thin"] for item in gated),
    }
    manifest.update(cells=summaries, best_pnl_cell=best["cell"], falsifiers=falsifiers,
                    hypothesis_falsified=any(falsifiers.values()),
                    passing_cells=[item["cell"] for item in gated if item["pass"]],
                    no_trail_violations=0, retained_trade_economics_mismatches=0)
    dump(OUT / "manifest.json", manifest)
    log(f"Falsifiers: {json.dumps(falsifiers)}; passing cells: {manifest['passing_cells']}")


if __name__ == "__main__":
    main()
