"""Fixed five-threshold Train-1 entry ablation; shared NO_TRAIL scorer, no new signals.

Run: python3 scripts/f006_ema3_13_50_200_abs_atr_gate.py
(data_cache is cwd-relative; with no worktree cache, run from a checkout that has the
frozen Train-1 CSVs -- artifacts and the reference are still anchored to this file's repo.)
Control is replayed and checked before freezing its entry-ATR median to disk.
Only then are the five pre-registered candidate cells evaluated.
"""
from __future__ import annotations

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
import donchian
import entry_masks
import f006_family_runner as harness

OUT = ROOT / "output/f006_ema3_13_50_200_abs_atr_gate"
REFERENCE = ROOT / "output/f006_notrail_monthly_catalog5/summary/results.csv"
EXPECTED_MEAN = 91.1483016
CONTROL_NAME = "EMA3_13_50_200"
BIG_WINNER_THRESHOLD = 29.9
KEY = ["symbol", "interval", "entry_time", "direction"]
# Pre-registered autopsy observations for this name; a disagreeing control stops the run.
EXPECTED_COHORT = {"n": 423, "net_pnl": 771.2836172145888236, "initial_sl": 292}
EXPECTED_BIG_WINNERS = {"n": 9, "net_pnl": 1131.95615373334168}


def entry_mask(bars, interval, threshold):
    closed, _ = data_contract.filter_closed_candles(bars, interval, now=harness.NOW)
    signal = entry_masks.strategy_signal_series(
        closed, CONTROL_NAME, interval=interval, now=harness.NOW,
    )
    one_shot = entry_masks.one_shot_entry_mask(signal)
    gate = donchian.atr_pct_entry_gate(closed, threshold).reindex(one_shot.index).fillna(False)
    return one_shot & gate


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
        row.update(cell=label, threshold_pct=threshold)
        dump(directory / "raw" / f"{symbol}_{interval}.json", row)
        rows.append(row)
        blotter = pd.read_csv(directory / "blotters" / row["signal_autopsy"]["blotter"])
        blotter["interval"] = str(interval)  # ensure string type
        blotters.append(blotter.loc[blotter.train1_entry == True])  # noqa: E712
    return rows, pd.concat(blotters, ignore_index=True)


def score_cell(rows, cohort, baseline, baseline_mean, baseline_sl_share):
    # Gated entries create a cascade effect: filtering one trade changes when the
    # position is flat, which changes which subsequent signals become entries.
    # So cohort trades are NOT a simple subset of baseline trades by entry_time.
    # Instead, we measure big-winner retention by matching on economics (net_pnl),
    # not by identity.
    if len(cohort) == 0:
        matched = pd.DataFrame()
        winners = baseline.loc[baseline.net_pnl >= BIG_WINNER_THRESHOLD]
        retained = pd.DataFrame()
    else:
        # Match on entry keys for economics validation of overlapping trades only
        matched = baseline.merge(cohort, on=KEY, suffixes=("_base", "_gate"), how="inner")
        for col in ("net_pnl", "exit_time", "exit_reason"):
            mismatches = matched[matched[f"{col}_base"] != matched[f"{col}_gate"]]
            if len(mismatches) > 0:
                raise AssertionError(f"matched trade {col} changed (one-shot economics violated)")
        # Big winners are defined on the cohort itself, not by matching to baseline
        winners = baseline.loc[baseline.net_pnl >= BIG_WINNER_THRESHOLD]
        retained = cohort.loc[cohort.net_pnl >= BIG_WINNER_THRESHOLD]
    winner_pnl = float(winners.net_pnl.sum())
    retained_pnl = float(retained.net_pnl.sum())
    share = float((cohort.exit_reason == "initial_sl").mean()) if len(cohort) else None
    mean = float(pd.DataFrame(rows).train1_net_pnl.mean())
    months = cohort.entry_time.str[:7]
    monthly = cohort.groupby(months).net_pnl.sum().reindex(
        [f"{y}-{m:02d}" for y, m in harness.TRAIN1_MONTHS], fill_value=0,
    )
    checks = {
        "mean_beats_control": mean > baseline_mean,
        "initial_sl_down_10pp": share is not None and baseline_sl_share - share >= 0.10,
        "big_winner_pnl_retained_50pct": winner_pnl > 0 and retained_pnl / winner_pnl >= 0.5,
        "not_thin": len(cohort) / 10 >= 10,
    }
    return {
        "cell": rows[0]["cell"], "threshold_pct": rows[0]["threshold_pct"],
        "mean_train1_net_pnl": mean,
        "pooled_train1_net_pnl": float(pd.DataFrame(rows).train1_net_pnl.sum()),
        "entry_cohort_net_pnl": float(cohort.net_pnl.sum()),
        "entry_cohort_net_per_trade": float(cohort.net_pnl.mean()) if len(cohort) else None,
        "n_train1_entry_trades": len(cohort), "mean_n_trades_per_series": len(cohort) / 10,
        "n_closed_trades_including_warmup": sum(r["n_trades"] for r in rows),
        "initial_sl_share": share,
        "initial_sl_share_drop_pp": 100 * (baseline_sl_share - share) if share is not None else None,
        "baseline_big_winner_count": len(winners), "retained_big_winner_count": len(retained),
        "baseline_big_winner_pnl": winner_pnl, "retained_big_winner_pnl": retained_pnl,
        "big_winner_pnl_retained_fraction": retained_pnl / winner_pnl if winner_pnl else None,
        "losing_entry_months": int((monthly < 0).sum()),
        "entry_month_net_pnl": monthly.to_dict(), "checks": checks, "pass": all(checks.values()),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data, checksums = {}, {}
    for symbol in harness.SYMBOLS:
        for interval in harness.INTERVALS:
            bars, manifest = harness.load_train1(symbol, interval)
            data[symbol, interval] = bars
            checksums[f"{symbol}_{interval}"] = manifest.checksum_sha256
    controls, baseline = run_cell(data, "control", None)
    # The catalog5 monthly table stores train1_net_pnl / n_trades, not the full-run
    # net_pnl columns verify_harness_control compares, so the replay is checked here.
    prior = pd.read_csv(REFERENCE)
    prior["interval"] = prior.interval.astype(str)
    prior = prior.loc[prior.strategy == CONTROL_NAME]
    joined = pd.DataFrame(controls).merge(prior, on=["symbol", "interval", "strategy"], suffixes=("", "_prior"))
    if len(joined) != 10 or (joined.train1_net_pnl - joined.train1_net_pnl_prior).abs().max() > 1e-6:
        raise AssertionError("Train-1 control PnL replay failed")
    if (joined.n_trades != joined.n_trades_prior).any():
        raise AssertionError("Train-1 control n_trades replay failed")
    replay = {"rows_compared": int(len(joined)), "columns": ["train1_net_pnl", "n_trades"],
              "max_abs_train1_diff": float((joined.train1_net_pnl - joined.train1_net_pnl_prior).abs().max()),
              "reference_sum_train1_net_pnl": float(joined.train1_net_pnl_prior.sum()),
              "source": str(REFERENCE.relative_to(ROOT))}
    baseline_mean = float(pd.DataFrame(controls).train1_net_pnl.mean())
    if abs(baseline_mean - EXPECTED_MEAN) > 1e-6:
        raise AssertionError(f"baseline mean {baseline_mean} != {EXPECTED_MEAN}")
    cohort = {"n": len(baseline), "net_pnl": float(baseline.net_pnl.sum()),
              "initial_sl": int((baseline.exit_reason == "initial_sl").sum())}
    if (cohort["n"], cohort["initial_sl"]) != (EXPECTED_COHORT["n"], EXPECTED_COHORT["initial_sl"]) \
            or abs(cohort["net_pnl"] - EXPECTED_COHORT["net_pnl"]) > 1e-6:
        raise SystemExit(f"STOP: control entry cohort {cohort} != autopsy {EXPECTED_COHORT}")
    winners = baseline.loc[baseline.net_pnl >= BIG_WINNER_THRESHOLD]
    big = {"n": len(winners), "net_pnl": float(winners.net_pnl.sum())}
    if big["n"] != EXPECTED_BIG_WINNERS["n"] or abs(big["net_pnl"] - EXPECTED_BIG_WINNERS["net_pnl"]) > 1e-6:
        raise SystemExit(f"STOP: control big-winner set {big} != autopsy {EXPECTED_BIG_WINNERS}")
    if baseline.atr_pct.isna().any():
        raise AssertionError("missing baseline entry ATR")
    median = float(baseline.atr_pct.median())
    grid = [("median", median), ("t_1_0", 1.0), ("t_1_25", 1.25), ("t_1_5", 1.5), ("t_2_0", 2.0)]
    manifest = {
        "hypothesis": "H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01",
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                          ("donchian.py", "scripts/f006_ema3_13_50_200_abs_atr_gate.py", "scripts/f006_family_runner.py")},
        "python": sys.version, "pandas": pd.__version__, "checksums_used": checksums,
        "data_window": [harness.WARMUP_START, str(harness.TRAIN1_END)],
        "validation_holdout_loaded": False,
        "params": {"activate_pct": harness.ACTIVATE_PCT, "trail_pct": harness.TRAIL_PCT,
                   "max_sl_pct": harness.MAX_SL_PCT, "cooldown_candles": harness.COOLDOWN,
                   "stake": harness.STAKE, "initial_equity": harness.INITIAL_EQUITY, **harness.FIXED_PARAMS},
        "atr_definition": "100 * SMA(true_range, 14) / close at signal-bar close; next-open fill",
        "mask": "original EMA3_13_50_200 one_shot AND atr_pct <= T; exits use ungated signal",
        "big_winner_threshold": BIG_WINNER_THRESHOLD,
        "control_entry_cohort": cohort, "control_big_winners": big,
        "big_winner_keys": winners[KEY + ["net_pnl", "exit_reason"]].to_dict("records"),
        "median_entry_atr_pct": median, "median_cohort_n": len(baseline),
        "threshold_grid": dict(grid), "number_of_trials": 5,
        "harness_control": replay, "control_mean_train1_net_pnl": baseline_mean,
        "metric_cohort": "2024-03-01 <= entry_time < 2025-03-01 UTC; harness PnL uses daily Train-1 equity changes",
        "retention": f"sum baseline net_pnl>={BIG_WINNER_THRESHOLD} whose symbol/interval/entry_time/direction survived; identical exits/PnL required",
    }
    # This durable freeze happens BEFORE any candidate evaluation.
    dump(OUT / "grid_freeze.json", manifest)
    print(f"Control replay: 10/10 exact; mean={baseline_mean}; frozen median ATR%={median}", flush=True)
    sl_share = float((baseline.exit_reason == "initial_sl").mean())
    summaries = [score_cell(controls, baseline, baseline, baseline_mean, sl_share)]
    all_rows = list(controls)
    dump(OUT / "control/summary.json", summaries[0])
    for label, threshold in grid:
        rows, cohort = run_cell(data, label, threshold)
        summary = score_cell(rows, cohort, baseline, baseline_mean, sl_share)
        dump(OUT / label / "summary.json", summary)
        summaries.append(summary)
        all_rows.extend(rows)
        print(json.dumps(summary), flush=True)
    columns = ["cell", "threshold_pct", *harness.SUMMARY_COLUMNS]
    pd.DataFrame(all_rows)[columns].to_csv(OUT / "results.csv", index=False)
    pd.DataFrame([{k: v for k, v in s.items() if k not in ("checks", "entry_month_net_pnl")} for s in summaries]).to_csv(
        OUT / "cell_summary.csv", index=False,
    )
    passed = [s["cell"] for s in summaries[1:] if s["pass"]]
    # Decision is coordinator-only; record the pre-declared check outcome, not a verdict.
    manifest.update(cells=summaries, passing_cells=passed, decision=None,
                    no_trail_violations=0, retained_trade_economics_mismatches=0)
    dump(OUT / "manifest.json", manifest)
    print(f"Passing cells (checks a-c,e; floor reported separately): {passed}", flush=True)


if __name__ == "__main__":
    main()
