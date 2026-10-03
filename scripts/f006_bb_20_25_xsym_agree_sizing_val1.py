"""Run the pre-registered Validation-1 check of the frozen xsym agreement sizing formula.

Same rules as ``scripts/f006_bb_20_25_xsym_agree_sizing.py`` (causal one-bar shifted
``mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)``, leading stake 100). One continuous
backtest per series from the 2024-01-26 warmup through bars < 2025-06-01; metrics are
scored only on entries with 2025-03-01 <= entry_time < 2025-06-01 UTC. Before trusting
Validation-1, the Train-1 slice of the control arm must reproduce the Train-1 run.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine  # noqa: E402
import data_contract  # noqa: E402
import entry_masks  # noqa: E402
import regularity  # noqa: E402
import strategy  # noqa: E402

import f006_bb_20_25_xsym_agree_sizing as train1  # noqa: E402

NAME = train1.NAME
SYMBOLS = train1.SYMBOLS
INTERVALS = train1.INTERVALS
BASE_STAKE = train1.BASE_STAKE
BIG_WINNER_THRESHOLD = train1.BIG_WINNER_THRESHOLD

TRAIN1_START = train1.TRAIN1_START
TRAIN1_END = train1.TRAIN1_END
VAL1_START = pd.Timestamp("2025-03-01T00:00:00Z")
VAL1_END = pd.Timestamp("2025-06-01T00:00:00Z")
NOW = VAL1_END
VAL1_MONTHS = [(2025, 3), (2025, 4), (2025, 5)]
VAL1_MONTHS_SET = set(VAL1_MONTHS)

TRAIN1_CONTROL_MEAN = 82.90
TRAIN1_CONTROL_N = 512
TRAIN1_CONTROL_MEAN_EXACT_PATH = "output/f006_bb_20_25_xsym_agree_sizing/summary/cell_summary.json"
GATE_TOL = 1e-6

OUT_DIR = "output/f006_bb_20_25_xsym_agree_sizing_val1"


def load_through_val1(symbol: str, interval: str) -> tuple[pd.DataFrame, object]:
    try:
        full_df, manifest = data_contract.load_dataset(
            "data_cache", symbol, interval, train1.WARMUP_START, train1.HOLDOUT_END
        )
    except data_contract.DataContractError as exc:
        raise SystemExit(
            f"STOP: cannot load frozen dataset for {symbol}/{interval} from data_cache -- {exc}."
        ) from exc
    expected = train1.EXPECTED_CHECKSUMS[(symbol, interval)]
    if manifest.checksum_sha256 != expected:
        raise SystemExit(
            f"STOP: checksum mismatch for {symbol}/{interval}: cache has "
            f"{manifest.checksum_sha256}, protocol section 6 expects {expected}."
        )
    idx = pd.DatetimeIndex(full_df.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    df = full_df.loc[(idx >= pd.Timestamp(train1.WARMUP_START)) & (idx < VAL1_END)]
    assert not df.empty, f"empty slice for {symbol}/{interval}"
    assert pd.DatetimeIndex(df.index).max() < VAL1_END
    return df, manifest


def _window_entries(trades: pd.DataFrame, start, end) -> pd.DataFrame:
    result = trades.copy()
    result["entry_time"] = pd.to_datetime(result["entry_time"], utc=True)
    result = result.loc[(result["entry_time"] >= start) & (result["entry_time"] < end)]
    return result.reset_index(drop=True)


def _equity_net_pnl_for(result, months_set) -> float:
    days, _months = regularity.compute_regularity(result.equity_curve)
    return round(
        sum(
            d.pnl for d in days
            if (d.day.year, d.day.month) in months_set and d.status != "missing"
        ),
        6,
    )


def _val1_month_rows(trades: pd.DataFrame) -> list[dict]:
    if trades.empty:
        pnl_by_month = pd.Series(dtype=float)
    else:
        pnl_by_month = trades.groupby(trades["entry_time"].dt.strftime("%Y-%m"))["net_pnl"].sum()
    return [
        {
            "month": f"{year}-{month:02d}",
            "net_pnl": round(float(pnl_by_month.get(f"{year}-{month:02d}", 0.0)), 6),
        }
        for year, month in VAL1_MONTHS
    ]


def _losing_count(rows: list[dict]) -> int:
    return sum(row["net_pnl"] < 0 for row in rows)


def _run_one(df, mask, mult_series, symbol: str, interval: str):
    t0 = time.time()
    common = dict(
        interval=interval,
        now=NOW,
        symbol=symbol,
        initial_equity=train1.INITIAL_EQUITY,
        stake=BASE_STAKE,
        max_sl_pct=train1.MAX_SL_PCT,
        activate_pct=train1.ACTIVATE_PCT,
        trail_pct=train1.TRAIL_PCT,
        cooldown_candles=train1.COOLDOWN,
        entry_regime_mask=mask,
        **train1.FIXED_PARAMS,
    )
    baseline_result = backtest_engine.run_backtest(df, NAME, stake_series=None, **common)
    stake_series = (BASE_STAKE * mult_series).fillna(BASE_STAKE)
    sized_result = backtest_engine.run_backtest(df, NAME, stake_series=stake_series, **common)

    baseline_all = baseline_result.trades.copy()
    sized_all = sized_result.trades.copy()
    baseline_t1 = _window_entries(baseline_all, TRAIN1_START, TRAIN1_END)
    baseline_v1 = _window_entries(baseline_all, VAL1_START, VAL1_END)
    sized_v1 = _window_entries(sized_all, VAL1_START, VAL1_END)
    invariant_ok = (
        len(baseline_all) == len(sized_all)
        and list(baseline_v1["entry_time"]) == list(sized_v1["entry_time"])
    )
    if not invariant_ok:
        raise SystemExit(
            f"STOP: trade-count invariant violated for {symbol}/{interval}: "
            f"total {len(baseline_all)} vs {len(sized_all)}, "
            f"Val-1-entry {len(baseline_v1)} vs {len(sized_v1)}"
        )

    stats = train1._stake_stats(sized_v1) if len(sized_v1) else {
        "stake_cv": 0.0, "stake_cv_ok": False, "mean_mult_winners": None,
        "mean_mult_losers": None, "mean_mult_gap": None,
    }
    baseline_monthly = _val1_month_rows(baseline_v1)
    sized_monthly = _val1_month_rows(sized_v1)
    row = {
        "symbol": symbol,
        "interval": interval,
        "n_trades_total_baseline": int(len(baseline_all)),
        "n_trades_total_sized": int(len(sized_all)),
        "n_trades_train1_entry_baseline": int(len(baseline_t1)),
        "n_trades_val1_entry_baseline": int(len(baseline_v1)),
        "n_trades_val1_entry_sized": int(len(sized_v1)),
        "n_val1_end_of_data_exits": int((baseline_v1.get("exit_reason") == "end_of_data").sum())
        if "exit_reason" in baseline_v1 else None,
        "trade_count_invariant_ok": invariant_ok,
        "train1_net_pnl_baseline": _equity_net_pnl_for(baseline_result, train1.TRAIN1_MONTHS_SET),
        "val1_entry_net_pnl_baseline": round(float(baseline_v1["net_pnl"].sum()), 6),
        "val1_entry_net_pnl_sized": round(float(sized_v1["net_pnl"].sum()), 6),
        "val1_equity_net_pnl_baseline": _equity_net_pnl_for(baseline_result, VAL1_MONTHS_SET),
        "val1_equity_net_pnl_sized": _equity_net_pnl_for(sized_result, VAL1_MONTHS_SET),
        "losing_months_baseline": _losing_count(baseline_monthly),
        "losing_months_sized": _losing_count(sized_monthly),
        **stats,
        "baseline_entry_monthly": baseline_monthly,
        "sized_entry_monthly": sized_monthly,
        "seconds": round(time.time() - t0, 2),
    }
    for cohort in (baseline_v1, sized_v1):
        cohort["symbol"] = symbol
        cohort["interval"] = interval
    return row, baseline_v1, sized_v1


GATE_COLUMNS = [
    "symbol", "interval", "n_trades_total_baseline", "n_trades_train1_entry_baseline",
    "train1_net_pnl_baseline",
]
TRAIN1_RESULTS_PATH = "output/f006_bb_20_25_xsym_agree_sizing/summary/results.csv"


def _write_gate_failure(summary_df, gate, checksums_used, commit_sha, t_start) -> None:
    """Record only the Train-1 gate; Validation-1 metrics are neither written nor printed."""
    reference = pd.read_csv(TRAIN1_RESULTS_PATH)[
        ["symbol", "interval", "train1_net_pnl_baseline", "n_trades_train1_entry_baseline"]
    ].astype({"interval": str}).rename(columns={
        "train1_net_pnl_baseline": "train1_net_pnl_baseline_train1_run",
        "n_trades_train1_entry_baseline": "n_trades_train1_entry_baseline_train1_run",
    })
    gate_df = summary_df[GATE_COLUMNS].merge(reference, on=["symbol", "interval"], how="left")
    gate_df["train1_net_pnl_diff"] = (
        gate_df["train1_net_pnl_baseline"] - gate_df["train1_net_pnl_baseline_train1_run"]
    ).round(6)
    gate_df.to_csv(f"{OUT_DIR}/summary/results.csv", index=False)
    for record in gate_df.to_dict(orient="records"):
        with open(f"{OUT_DIR}/raw/{record['symbol']}_{record['interval']}.json", "w") as f:
            json.dump(record, f, indent=2, default=str)
    verdict = "STOP (Train-1 control gate failed; Validation-1 not scored)"
    cell_summary = {
        "experiment_id": "H-BB-20-25-XSYM-AGREE-SIZING-VAL1-01",
        "strategy": NAME,
        "number_of_trials": 1,
        "train1_control_gate": gate,
        "verdict": verdict,
    }
    with open(f"{OUT_DIR}/summary/cell_summary.json", "w") as f:
        json.dump(cell_summary, f, indent=2)
    manifest = {
        "script": "scripts/f006_bb_20_25_xsym_agree_sizing_val1.py",
        "git_commit_at_run": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "n_series": len(summary_df),
        "checksums_used": checksums_used,
        "engine_bars": f"{train1.WARMUP_START} <= ts < {VAL1_END.isoformat()}",
        "cell_summary": cell_summary,
        "seconds": round(time.time() - t_start, 2),
    }
    with open(f"{OUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    lines = [
        "H-BB-20-25-XSYM-AGREE-SIZING-VAL1-01",
        f"Run started: {manifest['run_started_utc']}",
        f"Commit at run: {commit_sha}",
        f"Train-1 control gate: mean={gate['observed_mean_train1_net_pnl']:.6f} "
        f"(ref {gate['reference_mean_train1_net_pnl']:.6f}, diff {gate['abs_diff']:.6f}, "
        f"tol {GATE_TOL}), n={gate['observed_train1_entry_n']} "
        f"(ref {gate['reference_train1_entry_n']}) -> FAIL",
        gate_df[["symbol", "interval", "train1_net_pnl_baseline_train1_run",
                 "train1_net_pnl_baseline", "train1_net_pnl_diff"]].to_string(index=False),
        f"Verdict: {verdict}",
    ]
    with open(f"{OUT_DIR}/summary/run.log", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    t_start = time.time()
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None

    assert NAME in strategy.STRATEGY_CATALOG
    os.makedirs(f"{OUT_DIR}/summary", exist_ok=True)
    os.makedirs(f"{OUT_DIR}/raw", exist_ok=True)

    rows, baseline_cohorts, sized_cohorts, checksums_used = [], [], [], {}
    for interval in INTERVALS:
        frames = {}
        for symbol in SYMBOLS:
            frames[symbol], manifest = load_through_val1(symbol, interval)
            checksums_used[f"{symbol}_{interval}"] = manifest.checksum_sha256
        ref_idx = pd.DatetimeIndex(frames["BTCUSDT"].index)
        for symbol in SYMBOLS:
            if not pd.DatetimeIndex(frames[symbol].index).equals(ref_idx):
                raise SystemExit(f"STOP: index-equality precondition violated for {symbol}/{interval}")

        for symbol in SYMBOLS:
            own_df = frames[symbol]
            others = {other: frames[other] for other in SYMBOLS if other != symbol}
            mult_series = train1.compute_agreement_multiplier_series(
                own_df, others, interval, now=NOW
            )
            signal = entry_masks.strategy_signal_series(own_df, NAME, interval=interval, now=NOW)
            mask = entry_masks.one_shot_entry_mask(signal)
            row, baseline_v1, sized_v1 = _run_one(own_df, mask, mult_series, symbol, interval)
            rows.append(row)
            baseline_cohorts.append(baseline_v1)
            sized_cohorts.append(sized_v1)
        print(f"done interval={interval} ({len(rows)} series, {time.time() - t_start:.1f}s)")

    summary_df = pd.DataFrame([
        {k: v for k, v in row.items() if k not in ("baseline_entry_monthly", "sized_entry_monthly")}
        for row in rows
    ])

    # Sanity gate: Train-1 slice of the longer control run must reproduce the Train-1 run.
    with open(TRAIN1_CONTROL_MEAN_EXACT_PATH) as f:
        train1_ref = json.load(f)["control"]
    ref_mean = float(train1_ref["mean_train1_net_pnl"])
    gate_mean = float(summary_df["train1_net_pnl_baseline"].mean())
    gate_n = int(summary_df["n_trades_train1_entry_baseline"].sum())
    gate_ok = (
        abs(gate_mean - ref_mean) <= GATE_TOL
        and round(gate_mean, 2) == TRAIN1_CONTROL_MEAN
        and gate_n == TRAIN1_CONTROL_N
    )
    gate = {
        "reference_mean_train1_net_pnl": ref_mean,
        "observed_mean_train1_net_pnl": round(gate_mean, 6),
        "abs_diff": abs(gate_mean - ref_mean),
        "tolerance": GATE_TOL,
        "reference_train1_entry_n": TRAIN1_CONTROL_N,
        "observed_train1_entry_n": gate_n,
        "passed": gate_ok,
    }
    print(f"Train-1 control gate: {gate}")
    if not gate_ok:
        _write_gate_failure(summary_df, gate, checksums_used, commit_sha, t_start)
        raise SystemExit("STOP: Train-1 control sanity gate failed; Validation-1 not scored")

    summary_df.to_csv(f"{OUT_DIR}/summary/results.csv", index=False)
    for row in rows:
        with open(f"{OUT_DIR}/raw/{row['symbol']}_{row['interval']}.json", "w") as f:
            json.dump(row, f, indent=2, default=str)

    baseline_pool = pd.concat(baseline_cohorts, ignore_index=True)
    sized_pool = pd.concat(sized_cohorts, ignore_index=True)
    baseline_monthly = _val1_month_rows(baseline_pool)
    sized_monthly = _val1_month_rows(sized_pool)
    pooled_stats = train1._stake_stats(sized_pool)
    big_winners = train1._big_winner_metrics(baseline_pool, sized_pool)

    mean_baseline = float(summary_df["val1_entry_net_pnl_baseline"].mean())
    mean_sized = float(summary_df["val1_entry_net_pnl_sized"].mean())
    losing_baseline = _losing_count(baseline_monthly)
    losing_sized = _losing_count(sized_monthly)
    total_invariant = bool(summary_df["trade_count_invariant_ok"].all())
    all_series_cv_ok = bool(summary_df["stake_cv_ok"].all())
    mean_gap = pooled_stats["mean_mult_gap"]

    falsified = []
    if mean_sized <= mean_baseline:
        falsified.append("(a) sized mean val1 net <= control")
    if losing_sized > losing_baseline:
        falsified.append(
            f"(b) pooled Val-1 losing-month count rose ({losing_sized} > {losing_baseline})"
        )
    if mean_gap is None or mean_gap <= 0:
        falsified.append(f"(c) pooled winner-minus-loser mean multiplier <= 0 ({mean_gap})")
    if not total_invariant:
        falsified.append("(d) trade-count invariant broken")
    if pooled_stats["stake_cv"] <= 0.05 or not all_series_cv_ok:
        falsified.append("(e) Val-1-entry stake_cv <= 0.05 (pooled or some series)")
    verdict = "FALSIFIED" if falsified else "NOT FALSIFIED"

    def _arm(pool, monthly, losing, mean, total_key, equity_key):
        return {
            "mean_val1_entry_net_pnl": round(mean, 6),
            "mean_val1_equity_net_pnl_informational": round(float(summary_df[equity_key].mean()), 6),
            "total_closed_trades": int(summary_df[total_key].sum()),
            "val1_entry_trades": int(len(pool)),
            "val1_entry_net_pnl": round(float(pool["net_pnl"].sum()), 6),
            "val1_entry_net_per_trade": round(float(pool["net_pnl"].mean()), 6),
            "pooled_entry_month_net_pnl": monthly,
            "pooled_losing_month_count": losing,
        }

    cell_summary = {
        "experiment_id": "H-BB-20-25-XSYM-AGREE-SIZING-VAL1-01",
        "strategy": NAME,
        "number_of_trials": 1,
        "train1_control_gate": gate,
        "control": _arm(baseline_pool, baseline_monthly, losing_baseline, mean_baseline,
                        "n_trades_total_baseline", "val1_equity_net_pnl_baseline"),
        "sized": {
            **_arm(sized_pool, sized_monthly, losing_sized, mean_sized,
                   "n_trades_total_sized", "val1_equity_net_pnl_sized"),
            "pooled_stake_cv": pooled_stats["stake_cv"],
            "all_series_stake_cv_gt_0_05": all_series_cv_ok,
            "series_stake_cv_min": float(summary_df["stake_cv"].min()),
            "mean_mult_winners": pooled_stats["mean_mult_winners"],
            "mean_mult_losers": pooled_stats["mean_mult_losers"],
            "mean_mult_winner_minus_loser": mean_gap,
        },
        "trade_count_invariant_all_series": total_invariant,
        "big_winner_contribution": big_winners,
        "verdict": verdict,
        "falsified": bool(falsified),
        "falsification_conditions_fired": falsified,
    }
    with open(f"{OUT_DIR}/summary/cell_summary.json", "w") as f:
        json.dump(cell_summary, f, indent=2)

    manifest = {
        "script": "scripts/f006_bb_20_25_xsym_agree_sizing_val1.py",
        "git_commit_at_run": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "n_series": len(rows),
        "checksums_used": checksums_used,
        "engine_bars": f"{train1.WARMUP_START} <= ts < {VAL1_END.isoformat()}",
        "scored_entries": f"{VAL1_START.isoformat()} <= entry_time < {VAL1_END.isoformat()}",
        "params": {
            "activate_pct": train1.ACTIVATE_PCT,
            "trail_pct": train1.TRAIL_PCT,
            "max_sl_pct": train1.MAX_SL_PCT,
            "cooldown_candles": train1.COOLDOWN,
            "mask_mode": "one_shot",
            "initial_equity": train1.INITIAL_EQUITY,
            "base_stake": BASE_STAKE,
            "mult_formula": "clip(0.5 + 0.375 * n_agree, 0.5, 2.0)",
            "stake_alignment": "fill bar uses multiplier from prior closed bar; leading fillna(100.0)",
            **train1.FIXED_PARAMS,
        },
        "cell_summary": cell_summary,
        "seconds": round(time.time() - t_start, 2),
    }
    with open(f"{OUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    c, s = cell_summary["control"], cell_summary["sized"]
    lines = [
        "H-BB-20-25-XSYM-AGREE-SIZING-VAL1-01",
        f"Run started: {manifest['run_started_utc']}",
        f"Commit at run: {commit_sha}",
        f"Train-1 control gate: mean={gate_mean:.6f} (ref {ref_mean:.6f}, diff {gate['abs_diff']:.2e}), "
        f"n={gate_n} (ref {TRAIN1_CONTROL_N}) -> {'PASS' if gate_ok else 'FAIL'}",
        f"Control: mean val1 entry net={mean_baseline:.6f}, total={c['total_closed_trades']}, "
        f"val1-entry n={c['val1_entry_trades']}, net={c['val1_entry_net_pnl']:.6f}, "
        f"losing months={losing_baseline}/3 {[m['net_pnl'] for m in baseline_monthly]}",
        f"Sized:   mean val1 entry net={mean_sized:.6f}, total={s['total_closed_trades']}, "
        f"val1-entry n={s['val1_entry_trades']}, net={s['val1_entry_net_pnl']:.6f}, "
        f"losing months={losing_sized}/3 {[m['net_pnl'] for m in sized_monthly]}",
        f"Pooled stake CV: {pooled_stats['stake_cv']:.6f} (series min {s['series_stake_cv_min']:.6f})",
        f"Pooled mult winners={pooled_stats['mean_mult_winners']}, losers={pooled_stats['mean_mult_losers']}, "
        f"gap={mean_gap}",
        f"Big winners: {big_winners}",
        f"Verdict: {verdict}",
        *[f"  {cond}" for cond in falsified],
    ]
    with open(f"{OUT_DIR}/summary/run.log", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
