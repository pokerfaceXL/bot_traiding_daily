"""
F006 -- refined cross-symbol signal-agreement gate: restrict to the 2 names it helped
(BB_20_25_breakout, DONCHIAN_55; drop DONCHIAN_PULLBACK_55) and sweep MIN_AGREE.

Tests the hypothesis in spec/research/F006-hypothesis-entry-cross-symbol-refined.md: whether
narrowing the gate to the two names whose per-name signature was positive in
F006-hypothesis-entry-cross-symbol-agreement.md, swept over MIN_AGREE in {1, 2, 3, 4}, causes any
of the 20 (name, symbol, interval) series, at any threshold, to GENUINELY clear
spec/research/F005-validation-protocol.md section 7's monthly promotion checklist
(n_trades_filtered > 0 required, unchanged guard from every prior note in this family).

Single pass, .venv_test only -- no Lorentzian dependency in this sample.

Reuses scripts/f006_entry_cross_symbol_experiment.py's cross_symbol_gate() and monthly-scoring
helpers unmodified (imported via importlib, not copy-pasted). Writes only
output/f006_entry_cross_symbol_refined/. Zero network connections.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import pandas as pd

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

import backtest_engine  # noqa: E402
import data_contract  # noqa: E402
import entry_masks  # noqa: E402
import regularity  # noqa: E402
import strategy  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "f006_entry_cross_symbol_experiment",
    os.path.join(_REPO_ROOT, "scripts", "f006_entry_cross_symbol_experiment.py"),
)
_prior = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prior)

# Reused, unmodified, from the prior note's script.
cross_symbol_gate = _prior.cross_symbol_gate
own_signal_series = _prior.own_signal_series
load_train1 = _prior.load_train1
_run_and_score = _prior._run_and_score
_n_months_flipped_to_zero_trade = _prior._n_months_flipped_to_zero_trade
WARMUP_START = _prior.WARMUP_START
HOLDOUT_END = _prior.HOLDOUT_END
EXPECTED_CHECKSUMS = _prior.EXPECTED_CHECKSUMS

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]
NAMES = ["DONCHIAN_55", "BB_20_25_breakout"]  # DONCHIAN_PULLBACK_55 dropped -- see pre-reg note
MIN_AGREE_VALUES = [1, 2, 3, 4]  # swept -- prior note tried only 2

OUT_DIR = "output/f006_entry_cross_symbol_refined"
PRIOR_CROSS_SYMBOL_RESULTS = "output/f006_entry_cross_symbol/summary/results.csv"
PRIOR_NOTRAIL_RESULTS = "output/f006_notrail_monthly/summary/results.csv"


def main():
    t_start = time.time()
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None

    for name in NAMES:
        assert name in strategy.STRATEGY_CATALOG, f"strategy {name!r} not in strategy.STRATEGY_CATALOG"

    os.makedirs(f"{OUT_DIR}/summary", exist_ok=True)
    os.makedirs(f"{OUT_DIR}/raw", exist_ok=True)

    rows = []
    unfiltered_rows = {}  # (symbol, interval, name) -> row, shared across all MIN_AGREE values
    checksums_used = {}
    subset_violations = []
    degenerate_passes = []
    genuine_passes = []
    index_mismatches = []

    for interval in INTERVALS:
        frames = {}
        for symbol in SYMBOLS:
            frames[symbol] = load_train1(symbol, interval)
            _fd, _man = data_contract.load_dataset("data_cache", symbol, interval, WARMUP_START, HOLDOUT_END)
            checksums_used[f"{symbol}_{interval}"] = _man.checksum_sha256

        # Discriminating check 1: index-equality precondition, re-asserted.
        ref_idx = pd.DatetimeIndex(frames["BTCUSDT"].index)
        for symbol in SYMBOLS:
            if not pd.DatetimeIndex(frames[symbol].index).equals(ref_idx):
                index_mismatches.append((symbol, interval))

        for name in NAMES:
            own_by_symbol = {s: own_signal_series(frames[s], name, interval) for s in SYMBOLS}
            for symbol in SYMBOLS:
                own = own_by_symbol[symbol]
                others = [own_by_symbol[s2] for s2 in SYMBOLS if s2 != symbol]
                one_shot = entry_masks.one_shot_entry_mask(own)

                # Unfiltered arm computed once per series, shared across all MIN_AGREE values.
                unfiltered_row = _run_and_score(frames[symbol], one_shot, symbol, interval, name)
                unfiltered_rows[(symbol, interval, name)] = unfiltered_row

                n_trades_by_min_agree = {}
                for min_agree in MIN_AGREE_VALUES:
                    gate = cross_symbol_gate(own, others, min_agree).reindex(one_shot.index).fillna(False)
                    filtered_mask = one_shot & gate

                    n_calls = int(one_shot.sum())
                    n_calls_gated_out = int((one_shot & ~gate).sum())

                    filtered_row = _run_and_score(frames[symbol], filtered_mask, symbol, interval, name)
                    n_trades_by_min_agree[min_agree] = filtered_row["n_trades"]

                    if filtered_row["n_trades"] > unfiltered_row["n_trades"]:
                        subset_violations.append((symbol, interval, name, min_agree))

                    n_flipped_zero = _n_months_flipped_to_zero_trade(unfiltered_row, filtered_row)

                    row = {
                        "symbol": symbol, "interval": interval, "strategy": name,
                        "min_agree": min_agree,
                        "n_calls": n_calls, "n_calls_gated_out": n_calls_gated_out,
                        "n_trades_unfiltered": unfiltered_row["n_trades"],
                        "n_trades_filtered": filtered_row["n_trades"],
                        "train1_net_pnl_unfiltered": unfiltered_row["train1_net_pnl"],
                        "train1_net_pnl_filtered": filtered_row["train1_net_pnl"],
                        "win_rate_unfiltered": unfiltered_row["win_rate_pct"],
                        "win_rate_filtered": filtered_row["win_rate_pct"],
                        "n_neg_months_unfiltered": unfiltered_row["n_neg_months"],
                        "n_neg_months_filtered": filtered_row["n_neg_months"],
                        "full_run_max_drawdown_pct_filtered": filtered_row["full_run_max_drawdown_pct"],
                        "promotion_pass_unfiltered": unfiltered_row["promotion_pass"],
                        "promotion_pass_filtered": filtered_row["promotion_pass"],
                        "promotion_pass_genuine_filtered": filtered_row["promotion_pass_genuine"],
                        "n_months_flipped_to_zero_trade": n_flipped_zero,
                    }
                    rows.append(row)
                    if filtered_row["promotion_pass"] and filtered_row["n_trades"] == 0:
                        degenerate_passes.append((symbol, interval, name, min_agree))
                    if filtered_row["promotion_pass_genuine"]:
                        genuine_passes.append((symbol, interval, name, min_agree))
                    with open(f"{OUT_DIR}/raw/{symbol}_{interval}_{name}_ma{min_agree}.json", "w") as f:
                        json.dump(
                            {"summary": row, "monthly_filtered": filtered_row["monthly"],
                             "monthly_unfiltered": unfiltered_row["monthly"]},
                            f, indent=2, default=str,
                        )

                # Discriminating check 5: monotonicity of n_trades_filtered in MIN_AGREE.
                for i in range(len(MIN_AGREE_VALUES) - 1):
                    lo, hi = MIN_AGREE_VALUES[i], MIN_AGREE_VALUES[i + 1]
                    if n_trades_by_min_agree[hi] > n_trades_by_min_agree[lo]:
                        subset_violations.append(("MONOTONICITY", symbol, interval, name, lo, hi))
        print(f"done interval={interval} ({len(rows)} cells so far, {time.time() - t_start:.1f}s elapsed)")

    if index_mismatches:
        raise SystemExit(f"STOP: index-equality precondition violated for {index_mismatches}")

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(f"{OUT_DIR}/summary/results.csv", index=False)

    if subset_violations:
        raise SystemExit(f"STOP: subset/monotonicity invariant violated for {subset_violations}")

    # ---------------------------------------------- harness control 3: vs. prior cross-symbol note
    harness_prior_cross_symbol = {"rows_compared": 0, "n_mismatches": 0, "mismatches": []}
    if os.path.exists(PRIOR_CROSS_SYMBOL_RESULTS):
        prior = pd.read_csv(PRIOR_CROSS_SYMBOL_RESULTS)
        prior["interval"] = prior["interval"].astype(str)
        ma2 = summary_df[summary_df["min_agree"] == 2]
        merged = ma2.merge(
            prior[["symbol", "interval", "strategy", "train1_net_pnl_filtered", "n_trades_filtered"]],
            on=["symbol", "interval", "strategy"], suffixes=("", "_prior"),
        )
        harness_prior_cross_symbol["rows_compared"] = int(len(merged))
        mismatches = []
        for _, r in merged.iterrows():
            if (abs(r["train1_net_pnl_filtered"] - r["train1_net_pnl_filtered_prior"]) > 1e-3
                    or r["n_trades_filtered"] != r["n_trades_filtered_prior"]):
                mismatches.append({
                    "symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"],
                    "this_pnl": r["train1_net_pnl_filtered"], "prior_pnl": r["train1_net_pnl_filtered_prior"],
                    "this_trades": r["n_trades_filtered"], "prior_trades": r["n_trades_filtered_prior"],
                })
        harness_prior_cross_symbol["n_mismatches"] = len(mismatches)
        harness_prior_cross_symbol["mismatches"] = mismatches
        if mismatches:
            raise SystemExit(
                f"STOP: {len(mismatches)} series' MIN_AGREE=2 rerun disagrees with "
                f"{PRIOR_CROSS_SYMBOL_RESULTS} -- {mismatches[:5]}"
            )
    else:
        harness_prior_cross_symbol["source"] = f"{PRIOR_CROSS_SYMBOL_RESULTS} MISSING -- not compared"

    # ---------------------------------------------- harness control 4: vs. notrail-monthly baseline
    harness_notrail = {"rows_compared": 0, "n_mismatches": 0, "mismatches": []}
    if os.path.exists(PRIOR_NOTRAIL_RESULTS):
        prior_nt = pd.read_csv(PRIOR_NOTRAIL_RESULTS)
        prior_nt["interval"] = prior_nt["interval"].astype(str)
        unf = summary_df[summary_df["min_agree"] == MIN_AGREE_VALUES[0]][
            ["symbol", "interval", "strategy", "n_trades_unfiltered", "train1_net_pnl_unfiltered"]
        ]
        merged_nt = unf.merge(
            prior_nt[["symbol", "interval", "strategy", "train1_net_pnl", "n_trades"]],
            on=["symbol", "interval", "strategy"], suffixes=("", "_prior"),
        )
        harness_notrail["rows_compared"] = int(len(merged_nt))
        mismatches_nt = []
        for _, r in merged_nt.iterrows():
            if (abs(r["train1_net_pnl_unfiltered"] - r["train1_net_pnl"]) > 1e-3
                    or r["n_trades_unfiltered"] != r["n_trades"]):
                mismatches_nt.append({
                    "symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"],
                    "unfiltered_net_pnl": r["train1_net_pnl_unfiltered"], "prior_net_pnl": r["train1_net_pnl"],
                    "unfiltered_n_trades": r["n_trades_unfiltered"], "prior_n_trades": r["n_trades"],
                })
        harness_notrail["n_mismatches"] = len(mismatches_nt)
        harness_notrail["mismatches"] = mismatches_nt
        if mismatches_nt:
            raise SystemExit(
                f"STOP: {len(mismatches_nt)} series' unfiltered rerun disagrees with "
                f"{PRIOR_NOTRAIL_RESULTS} -- {mismatches_nt[:5]}"
            )
    else:
        harness_notrail["source"] = f"{PRIOR_NOTRAIL_RESULTS} MISSING -- not compared"

    passing_genuine = [r for r in rows if r["promotion_pass_genuine_filtered"]]
    passing_any = [r for r in rows if r["promotion_pass_filtered"]]

    per_min_agree_summary = {}
    for ma in MIN_AGREE_VALUES:
        sub = summary_df[summary_df["min_agree"] == ma]
        total_u = int(sub["n_trades_unfiltered"].sum())
        total_f = int(sub["n_trades_filtered"].sum())
        wins_u = (sub["win_rate_unfiltered"] / 100.0 * sub["n_trades_unfiltered"]).sum()
        wins_f = (sub["win_rate_filtered"] / 100.0 * sub["n_trades_filtered"]).sum()
        per_min_agree_summary[ma] = {
            "pooled_trade_weighted_win_rate_pct_unfiltered": round(100.0 * wins_u / total_u, 4) if total_u else None,
            "pooled_trade_weighted_win_rate_pct_filtered": round(100.0 * wins_f / total_f, 4) if total_f else None,
            "simple_mean_win_rate_pct_unfiltered": round(sub["win_rate_unfiltered"].mean(), 4),
            "simple_mean_win_rate_pct_filtered": round(sub["win_rate_filtered"].mean(), 4),
            "mean_net_pnl_unfiltered": round(sub["train1_net_pnl_unfiltered"].mean(), 4),
            "mean_net_pnl_filtered": round(sub["train1_net_pnl_filtered"].mean(), 4),
            "mean_neg_months_unfiltered": round(sub["n_neg_months_unfiltered"].mean(), 4),
            "mean_neg_months_filtered": round(sub["n_neg_months_filtered"].mean(), 4),
            "total_trades_unfiltered": total_u,
            "total_trades_filtered": total_f,
            "trade_count_reduction_pct": round(100.0 * (1 - total_f / total_u), 2) if total_u else None,
            "n_positive_series_unfiltered": int((sub["train1_net_pnl_unfiltered"] > 0).sum()),
            "n_positive_series_filtered": int((sub["train1_net_pnl_filtered"] > 0).sum()),
            "n_promotion_pass_genuine": int(sub["promotion_pass_genuine_filtered"].sum()),
            "n_promotion_pass_any": int(sub["promotion_pass_filtered"].sum()),
            "min_filtered_trades": int(sub["n_trades_filtered"].min()),
        }

    manifest_out = {
        "script": "scripts/f006_entry_cross_symbol_refined_experiment.py",
        "git_commit": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pandas": pd.__version__,
        "n_series": len(NAMES) * len(SYMBOLS) * len(INTERVALS),
        "n_cells": len(rows),
        "min_agree_values": MIN_AGREE_VALUES,
        "names": NAMES,
        "checksums_used": checksums_used,
        "index_equality_precondition_ok": len(index_mismatches) == 0,
        "harness_control_vs_prior_cross_symbol_note_at_min_agree_2": harness_prior_cross_symbol,
        "harness_control_vs_notrail_monthly": harness_notrail,
        "subset_and_monotonicity_invariant_violations": subset_violations,
        "n_cells_promotion_pass_genuine": len(passing_genuine),
        "n_cells_promotion_pass_any": len(passing_any),
        "genuine_pass_cells": [
            {"symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"], "min_agree": r["min_agree"]}
            for r in passing_genuine
        ],
        "degenerate_pass_cells": [
            {"symbol": s, "interval": i, "strategy": n, "min_agree": ma}
            for (s, i, n, ma) in degenerate_passes
        ],
        "per_min_agree_summary": per_min_agree_summary,
        "seconds": round(time.time() - t_start, 2),
    }
    with open(f"{OUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(manifest_out, f, indent=2)

    print(f"\n{len(rows)} cells in {time.time() - t_start:.1f}s -> {OUT_DIR}/summary/results.csv")
    print(f"harness vs prior cross-symbol (MIN_AGREE=2): "
          f"{harness_prior_cross_symbol['n_mismatches']}/{harness_prior_cross_symbol['rows_compared']} mismatches")
    print(f"harness vs notrail-monthly: {harness_notrail['n_mismatches']}/{harness_notrail['rows_compared']} mismatches")
    print(f"promotion_pass genuine: {len(passing_genuine)}/{len(rows)} cells (any incl. degenerate: {len(passing_any)}/{len(rows)})")
    for ma, s in per_min_agree_summary.items():
        print(f"MIN_AGREE={ma}: pooled win% unf->filt {s['pooled_trade_weighted_win_rate_pct_unfiltered']:.2f}->"
              f"{s['pooled_trade_weighted_win_rate_pct_filtered']:.2f}, "
              f"trades {s['total_trades_unfiltered']}->{s['total_trades_filtered']} "
              f"(-{s['trade_count_reduction_pct']}%), genuine passes {s['n_promotion_pass_genuine']}")


if __name__ == "__main__":
    main()
