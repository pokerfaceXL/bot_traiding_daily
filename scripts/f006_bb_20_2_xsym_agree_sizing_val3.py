"""Run the pre-registered Validation-3 check of the frozen xsym agreement sizing on BB_20_2_EMA200.

Thin sibling of scripts/f006_bb_20_2_xsym_agree_sizing_val2.py. Same rules as
scripts/f006_bb_20_2_xsym_agree_sizing.py (causal one-bar shifted
``mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)``, leading stake 100, n_agree counted on
BB_20_2_EMA200's own persistent signal). One continuous backtest per series from the
2024-01-26 warmup through bars < 2025-12-01; metrics are scored only on entries with
2025-09-01 <= entry_time < 2025-12-01 UTC (F005 protocol section 3.2 Validation 3). The shared long protocol cache is verified against
EXPECTED_CHECKSUMS in scripts/f006_bb_20_25_xsym_agree_sizing.py (OHLCV identity only).
Before any Validation-3 scoring, the Train-1 slice of the control arm must sit within relative
0.25% of this name's Train-1 control mean with Train-1-entry n = 756.

Run: python3 scripts/f006_bb_20_2_xsym_agree_sizing_val3.py
(F006_DATA_CACHE overrides the cwd-relative data_cache when this worktree has no CSVs;
artifacts are always written under this file's repo.)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import backtest_engine  # noqa: E402
import data_contract  # noqa: E402
import entry_masks  # noqa: E402
import strategy  # noqa: E402

import f006_bb_20_25_xsym_agree_sizing as shared  # noqa: E402
import f006_bb_20_25_xsym_agree_sizing_val1 as val1_helpers  # noqa: E402
import f006_bb_20_2_xsym_agree_sizing as train1  # noqa: E402
import f006_family_runner as harness  # noqa: E402

NAME = train1.NAME
SYMBOLS = train1.SYMBOLS
INTERVALS = train1.INTERVALS
BASE_STAKE = train1.BASE_STAKE
DATA_CACHE = train1.DATA_CACHE

TRAIN1_START = shared.TRAIN1_START
TRAIN1_END = shared.TRAIN1_END
VAL3_START = pd.Timestamp("2025-09-01T00:00:00Z")
VAL3_END = pd.Timestamp("2025-12-01T00:00:00Z")
NOW = VAL3_END
VAL3_MONTHS = [(2025, 9), (2025, 10), (2025, 11)]
VAL3_MONTHS_SET = set(VAL3_MONTHS)

TRAIN1_CONTROL_N = 756
TRAIN1_REFERENCE = ROOT / "output/f006_bb_20_2_xsym_agree_sizing/summary/cell_summary.json"
TRAIN1_RESULTS = ROOT / "output/f006_bb_20_2_xsym_agree_sizing/summary/results.csv"
GATE_REL_TOL = 0.0025

EXPERIMENT_ID = "H-BB-20-2-XSYM-AGREE-SIZING-VAL3-01"
OUT = ROOT / "output/f006_bb_20_2_xsym_agree_sizing_val3"


def _val3_month_rows(trades: pd.DataFrame) -> list[dict]:
    if trades.empty:
        pnl_by_month = pd.Series(dtype=float)
    else:
        pnl_by_month = trades.groupby(trades["entry_time"].dt.strftime("%Y-%m"))["net_pnl"].sum()
    return [
        {
            "month": f"{year}-{month:02d}",
            "net_pnl": round(float(pnl_by_month.get(f"{year}-{month:02d}", 0.0)), 6),
        }
        for year, month in VAL3_MONTHS
    ]


def load_through_val3(symbol: str, interval: str) -> tuple[pd.DataFrame, object]:
    try:
        full_df, manifest = data_contract.load_dataset(
            DATA_CACHE, symbol, interval, shared.WARMUP_START, shared.HOLDOUT_END
        )
    except data_contract.DataContractError as exc:
        raise SystemExit(
            f"STOP: cannot load frozen dataset for {symbol}/{interval} from {DATA_CACHE} -- {exc}."
        ) from exc
    expected = shared.EXPECTED_CHECKSUMS[(symbol, interval)]
    if manifest.checksum_sha256 != expected:
        raise SystemExit(
            f"STOP: checksum mismatch for {symbol}/{interval}: cache has "
            f"{manifest.checksum_sha256}, protocol section 6 expects {expected}."
        )
    idx = pd.DatetimeIndex(full_df.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    df = full_df.loc[(idx >= pd.Timestamp(shared.WARMUP_START)) & (idx < VAL3_END)]
    if df.empty or pd.DatetimeIndex(df.index).max() >= VAL3_END:
        raise SystemExit(f"STOP: bad warmup..Val-3 slice for {symbol}/{interval}.")
    return df, manifest


def _run_one(df, mask, mult_series, symbol: str, interval: str):
    t0 = time.time()
    common = dict(
        interval=interval, now=NOW, symbol=symbol,
        initial_equity=harness.INITIAL_EQUITY, stake=BASE_STAKE,
        max_sl_pct=harness.MAX_SL_PCT, activate_pct=harness.ACTIVATE_PCT,
        trail_pct=harness.TRAIL_PCT, cooldown_candles=harness.COOLDOWN,
        entry_regime_mask=mask, **harness.FIXED_PARAMS,
    )
    baseline_result = backtest_engine.run_backtest(df, NAME, stake_series=None, **common)
    stake_series = (BASE_STAKE * mult_series).fillna(BASE_STAKE)
    sized_result = backtest_engine.run_backtest(df, NAME, stake_series=stake_series, **common)

    baseline_all = baseline_result.trades.copy()
    sized_all = sized_result.trades.copy()
    baseline_t1 = val1_helpers._window_entries(baseline_all, TRAIN1_START, TRAIN1_END)
    baseline_v3 = val1_helpers._window_entries(baseline_all, VAL3_START, VAL3_END)
    sized_v3 = val1_helpers._window_entries(sized_all, VAL3_START, VAL3_END)
    invariant_ok = (
        len(baseline_all) == len(sized_all)
        and list(pd.to_datetime(baseline_all["entry_time"], utc=True))
        == list(pd.to_datetime(sized_all["entry_time"], utc=True))
        and list(baseline_v3["entry_time"]) == list(sized_v3["entry_time"])
    )
    if not invariant_ok:
        raise SystemExit(
            f"STOP: trade-count invariant violated for {symbol}/{interval}: "
            f"total {len(baseline_all)} vs {len(sized_all)}, "
            f"Val-3-entry {len(baseline_v3)} vs {len(sized_v3)}"
        )

    stats = shared._stake_stats(sized_v3) if len(sized_v3) else {
        "stake_cv": 0.0, "stake_cv_ok": False, "mean_mult_winners": None,
        "mean_mult_losers": None, "mean_mult_gap": None,
    }
    baseline_monthly = _val3_month_rows(baseline_v3)
    sized_monthly = _val3_month_rows(sized_v3)
    row = {
        "symbol": symbol,
        "interval": interval,
        "strategy": NAME,
        "n_trades_total_baseline": int(len(baseline_all)),
        "n_trades_total_sized": int(len(sized_all)),
        "n_trades_train1_entry_baseline": int(len(baseline_t1)),
        "n_trades_val3_entry_baseline": int(len(baseline_v3)),
        "n_trades_val3_entry_sized": int(len(sized_v3)),
        "n_val3_end_of_data_exits": int((baseline_v3["exit_reason"] == "end_of_data").sum())
        if "exit_reason" in baseline_v3 else None,
        "trade_count_invariant_ok": invariant_ok,
        "train1_net_pnl_baseline": val1_helpers._equity_net_pnl_for(
            baseline_result, harness.TRAIN1_MONTHS_SET
        ),
        "val3_entry_net_pnl_baseline": round(float(baseline_v3["net_pnl"].sum()), 6),
        "val3_entry_net_pnl_sized": round(float(sized_v3["net_pnl"].sum()), 6),
        "val3_equity_net_pnl_baseline": val1_helpers._equity_net_pnl_for(baseline_result, VAL3_MONTHS_SET),
        "val3_equity_net_pnl_sized": val1_helpers._equity_net_pnl_for(sized_result, VAL3_MONTHS_SET),
        "losing_months_baseline": val1_helpers._losing_count(baseline_monthly),
        "losing_months_sized": val1_helpers._losing_count(sized_monthly),
        **stats,
        "baseline_entry_monthly": baseline_monthly,
        "sized_entry_monthly": sized_monthly,
        "seconds": round(time.time() - t0, 2),
    }
    for cohort in (baseline_v3, sized_v3):
        cohort["symbol"] = symbol
        cohort["interval"] = interval
    return row, baseline_v3, sized_v3


def train1_gate(summary_df: pd.DataFrame) -> dict:
    """Relative 0.25% mean band and exact n=756 on the Train-1 slice of the control arm."""
    ref_mean = float(
        json.loads(TRAIN1_REFERENCE.read_text())["control_replay"]["control_mean_train1_net_pnl"]
    )
    gate_mean = float(summary_df["train1_net_pnl_baseline"].mean())
    gate_n = int(summary_df["n_trades_train1_entry_baseline"].sum())
    allowance = GATE_REL_TOL * abs(ref_mean)
    return {
        "reference_mean_train1_net_pnl": ref_mean,
        "reference_source": str(TRAIN1_REFERENCE.relative_to(ROOT)),
        "observed_mean_train1_net_pnl": round(gate_mean, 6),
        "abs_diff": abs(gate_mean - ref_mean),
        "tolerance": GATE_REL_TOL,
        "tolerance_kind": "relative",
        "allowance": allowance,
        "reference_train1_entry_n": TRAIN1_CONTROL_N,
        "observed_train1_entry_n": gate_n,
        "passed": abs(gate_mean - ref_mean) <= allowance and gate_n == TRAIN1_CONTROL_N,
    }


def _gate_table(summary_df: pd.DataFrame) -> pd.DataFrame:
    reference = pd.read_csv(TRAIN1_RESULTS)[
        ["symbol", "interval", "train1_net_pnl_baseline", "n_trades_train1_entry_baseline"]
    ].astype({"interval": str}).rename(columns={
        "train1_net_pnl_baseline": "train1_net_pnl_baseline_train1_run",
        "n_trades_train1_entry_baseline": "n_trades_train1_entry_baseline_train1_run",
    })
    gate_df = summary_df[[
        "symbol", "interval", "n_trades_total_baseline", "n_trades_train1_entry_baseline",
        "train1_net_pnl_baseline",
    ]].merge(reference, on=["symbol", "interval"], how="left")
    gate_df["train1_net_pnl_diff"] = (
        gate_df["train1_net_pnl_baseline"] - gate_df["train1_net_pnl_baseline_train1_run"]
    ).round(6)
    return gate_df


def _manifest(commit_sha, checksums_used, n_series, cell_summary, t_start) -> dict:
    return {
        "script": "scripts/f006_bb_20_2_xsym_agree_sizing_val3.py",
        "git_commit_at_run": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "n_series": n_series,
        "data_cache": DATA_CACHE,
        "checksums_used": checksums_used,
        "checksums_source": "scripts/f006_bb_20_25_xsym_agree_sizing.py EXPECTED_CHECKSUMS "
                            "(shared long protocol cache OHLCV identity)",
        "engine_bars": f"{shared.WARMUP_START} <= ts < {VAL3_END.isoformat()}",
        "scored_entries": f"{VAL3_START.isoformat()} <= entry_time < {VAL3_END.isoformat()}",
        "holdout_scored": False,
        "params": {
            "activate_pct": harness.ACTIVATE_PCT,
            "trail_pct": harness.TRAIL_PCT,
            "max_sl_pct": harness.MAX_SL_PCT,
            "cooldown_candles": harness.COOLDOWN,
            "mask_mode": "one_shot",
            "initial_equity": harness.INITIAL_EQUITY,
            "base_stake": BASE_STAKE,
            "mult_formula": train1.MULT_FORMULA,
            "n_agree": "count of other 4 basket symbols whose BB_20_2_EMA200 persistent signal "
                       "equals the traded symbol's nonzero direction on the same closed bar",
            "stake_alignment": "fill bar uses multiplier from prior closed bar; first bar stake 100.0",
            **harness.FIXED_PARAMS,
        },
        "cell_summary": cell_summary,
        "seconds": round(time.time() - t_start, 2),
    }


def _write_gate_failure(summary_df, gate, checksums_used, commit_sha, t_start) -> None:
    """Record only the Train-1 gate; Validation-3 metrics are neither written nor printed."""
    gate_df = _gate_table(summary_df)
    gate_df.to_csv(OUT / "summary" / "results.csv", index=False)
    for record in gate_df.to_dict(orient="records"):
        (OUT / "raw" / f"{record['symbol']}_{record['interval']}.json").write_text(
            json.dumps(record, indent=2, default=str) + "\n"
        )
    verdict = "STOP (Train-1 control gate failed; Validation-3 not scored)"
    cell_summary = {
        "experiment_id": EXPERIMENT_ID,
        "strategy": NAME,
        "number_of_trials": 1,
        "train1_control_gate": gate,
        "verdict": verdict,
    }
    (OUT / "summary" / "cell_summary.json").write_text(json.dumps(cell_summary, indent=2) + "\n")
    manifest = _manifest(commit_sha, checksums_used, len(summary_df), cell_summary, t_start)
    (OUT / "summary" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    lines = [
        EXPERIMENT_ID,
        f"Run started: {manifest['run_started_utc']}",
        f"Commit at run: {commit_sha}",
        f"Train-1 control gate: mean={gate['observed_mean_train1_net_pnl']:.6f} "
        f"(ref {gate['reference_mean_train1_net_pnl']:.7f}, diff {gate['abs_diff']:.6f}, "
        f"allowance {gate['allowance']:.7f}), n={gate['observed_train1_entry_n']} "
        f"(ref {gate['reference_train1_entry_n']}) -> FAIL",
        gate_df[["symbol", "interval", "train1_net_pnl_baseline_train1_run",
                 "train1_net_pnl_baseline", "train1_net_pnl_diff"]].to_string(index=False),
        f"Verdict: {verdict}",
    ]
    (OUT / "summary" / "run.log").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    t_start = time.time()
    commit_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True, cwd=ROOT
    ).strip()
    assert NAME in strategy.STRATEGY_CATALOG
    for sub in ("summary", "raw"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    rows, baseline_cohorts, sized_cohorts, checksums_used = [], [], [], {}
    for interval in INTERVALS:
        frames = {}
        for symbol in SYMBOLS:
            frames[symbol], manifest = load_through_val3(symbol, interval)
            checksums_used[f"{symbol}_{interval}"] = manifest.checksum_sha256
        ref_idx = pd.DatetimeIndex(frames["BTCUSDT"].index)
        for symbol in SYMBOLS:
            if not pd.DatetimeIndex(frames[symbol].index).equals(ref_idx):
                raise SystemExit(f"STOP: index-equality precondition violated for {symbol}/{interval}")

        signals = {
            symbol: entry_masks.strategy_signal_series(frames[symbol], NAME, interval=interval, now=NOW)
            for symbol in SYMBOLS
        }
        for symbol in SYMBOLS:
            mult_series = train1.agreement_multiplier_series(
                signals[symbol], [signals[o] for o in SYMBOLS if o != symbol]
            )
            mask = entry_masks.one_shot_entry_mask(signals[symbol])
            row, baseline_v3, sized_v3 = _run_one(frames[symbol], mask, mult_series, symbol, interval)
            rows.append(row)
            baseline_cohorts.append(baseline_v3)
            sized_cohorts.append(sized_v3)
        print(f"done interval={interval} ({len(rows)} series, {time.time() - t_start:.1f}s)")

    summary_df = pd.DataFrame([
        {k: v for k, v in row.items() if k not in ("baseline_entry_monthly", "sized_entry_monthly")}
        for row in rows
    ])

    # Sanity gate before any Validation-3 number is computed into the summary.
    gate = train1_gate(summary_df)
    print(f"Train-1 control gate: {gate}")
    if not gate["passed"]:
        _write_gate_failure(summary_df, gate, checksums_used, commit_sha, t_start)
        raise SystemExit("STOP: Train-1 control sanity gate failed; Validation-3 not scored")

    summary_df.to_csv(OUT / "summary" / "results.csv", index=False)
    for row in rows:
        (OUT / "raw" / f"{row['symbol']}_{row['interval']}.json").write_text(
            json.dumps(row, indent=2, default=str) + "\n"
        )

    baseline_pool = pd.concat(baseline_cohorts, ignore_index=True)
    sized_pool = pd.concat(sized_cohorts, ignore_index=True)
    baseline_monthly = _val3_month_rows(baseline_pool)
    sized_monthly = _val3_month_rows(sized_pool)
    pooled_stats = shared._stake_stats(sized_pool)
    big_winners = shared._big_winner_metrics(baseline_pool, sized_pool)

    mean_baseline = float(summary_df["val3_entry_net_pnl_baseline"].mean())
    mean_sized = float(summary_df["val3_entry_net_pnl_sized"].mean())
    losing_baseline = val1_helpers._losing_count(baseline_monthly)
    losing_sized = val1_helpers._losing_count(sized_monthly)
    total_invariant = bool(summary_df["trade_count_invariant_ok"].all())
    all_series_cv_ok = bool(summary_df["stake_cv_ok"].all())
    mean_gap = pooled_stats["mean_mult_gap"]

    falsified = []
    if mean_sized <= mean_baseline:
        falsified.append("(a) sized mean val3 net <= control")
    if losing_sized > losing_baseline:
        falsified.append(
            f"(b) pooled Val-3 losing-month count rose ({losing_sized} > {losing_baseline})"
        )
    if mean_gap is None or mean_gap <= 0:
        falsified.append(f"(c) pooled winner-minus-loser mean multiplier <= 0 ({mean_gap})")
    if not total_invariant:
        falsified.append("(d) trade-count invariant broken")
    if pooled_stats["stake_cv"] <= 0.05 or not all_series_cv_ok:
        falsified.append("(e) Val-3-entry stake_cv <= 0.05 (pooled or some series)")
    verdict = "FALSIFIED" if falsified else "NOT FALSIFIED"

    # Month contribution of the entry-net difference (informational only).
    diff_by_month = [
        {"month": b["month"], "sized_minus_control": round(s["net_pnl"] - b["net_pnl"], 6)}
        for b, s in zip(baseline_monthly, sized_monthly)
    ]

    def _arm(pool, monthly, losing, mean, total_key, equity_key):
        return {
            "mean_val3_entry_net_pnl": round(mean, 6),
            "mean_val3_equity_net_pnl_informational": round(float(summary_df[equity_key].mean()), 6),
            "total_closed_trades": int(summary_df[total_key].sum()),
            "val3_entry_trades": int(len(pool)),
            "val3_entry_net_pnl": round(float(pool["net_pnl"].sum()), 6),
            "val3_entry_net_per_trade": round(float(pool["net_pnl"].mean()), 6),
            "pooled_entry_month_net_pnl": monthly,
            "pooled_losing_month_count": losing,
        }

    cell_summary = {
        "experiment_id": EXPERIMENT_ID,
        "strategy": NAME,
        "number_of_trials": 1,
        "mult_formula": train1.MULT_FORMULA,
        "train1_control_gate": gate,
        "control": _arm(baseline_pool, baseline_monthly, losing_baseline, mean_baseline,
                        "n_trades_total_baseline", "val3_equity_net_pnl_baseline"),
        "sized": {
            **_arm(sized_pool, sized_monthly, losing_sized, mean_sized,
                   "n_trades_total_sized", "val3_equity_net_pnl_sized"),
            "pooled_stake_cv": pooled_stats["stake_cv"],
            "all_series_stake_cv_gt_0_05": all_series_cv_ok,
            "series_stake_cv_min": float(summary_df["stake_cv"].min()),
            "mean_mult_winners": pooled_stats["mean_mult_winners"],
            "mean_mult_losers": pooled_stats["mean_mult_losers"],
            "mean_mult_winner_minus_loser": mean_gap,
        },
        "entry_net_diff_by_month": diff_by_month,
        "trade_count_invariant_all_series": total_invariant,
        "big_winner_contribution": big_winners,
        "verdict": verdict,
        "falsified": bool(falsified),
        "falsification_conditions_fired": falsified,
    }
    (OUT / "summary" / "cell_summary.json").write_text(json.dumps(cell_summary, indent=2) + "\n")
    manifest = _manifest(commit_sha, checksums_used, len(rows), cell_summary, t_start)
    (OUT / "summary" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    c, s = cell_summary["control"], cell_summary["sized"]
    lines = [
        EXPERIMENT_ID,
        f"Run started: {manifest['run_started_utc']}",
        f"Commit at run: {commit_sha}",
        f"Train-1 control gate: mean={gate['observed_mean_train1_net_pnl']:.6f} "
        f"(ref {gate['reference_mean_train1_net_pnl']:.7f}, diff {gate['abs_diff']:.6f}, "
        f"allowance {gate['allowance']:.7f}), n={gate['observed_train1_entry_n']} "
        f"(ref {TRAIN1_CONTROL_N}) -> PASS",
        f"Control: mean val3 entry net={mean_baseline:.6f}, total={c['total_closed_trades']}, "
        f"val3-entry n={c['val3_entry_trades']}, net={c['val3_entry_net_pnl']:.6f}, "
        f"losing months={losing_baseline}/3 {[m['net_pnl'] for m in baseline_monthly]}",
        f"Sized:   mean val3 entry net={mean_sized:.6f}, total={s['total_closed_trades']}, "
        f"val3-entry n={s['val3_entry_trades']}, net={s['val3_entry_net_pnl']:.6f}, "
        f"losing months={losing_sized}/3 {[m['net_pnl'] for m in sized_monthly]}",
        f"Pooled stake CV: {pooled_stats['stake_cv']:.6f} (series min {s['series_stake_cv_min']:.6f})",
        f"Pooled mult winners={pooled_stats['mean_mult_winners']}, losers={pooled_stats['mean_mult_losers']}, "
        f"gap={mean_gap}",
        f"Entry-net diff by month: {diff_by_month}",
        f"Big winners: {big_winners}",
        f"Verdict: {verdict}",
        *[f"  {cond}" for cond in falsified],
    ]
    (OUT / "summary" / "run.log").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
