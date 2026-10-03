"""Run the pre-registered cross-symbol agreement sizing test for BB_20_2_EMA200.

Thin sibling of scripts/f006_bb_20_25_xsym_agree_sizing.py. The only sized arm uses the
frozen formula ``mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)``, with n_agree counted on
BB_20_2_EMA200's own persistent signal. Data are the Train-1 caches ending 2025-03-01
(checksums in output/f006_bb_20_2_abs_atr_gate/grid_freeze.json); no validation/holdout
cache is loaded. The control arm must replay catalog5's BB_20_2_EMA200 rows before the
sized arm is scored.

Run: python3 scripts/f006_bb_20_2_xsym_agree_sizing.py
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
import f006_bb_20_25_xsym_agree_sizing as sibling  # noqa: E402
import f006_family_runner as harness  # noqa: E402

NAME = "BB_20_2_EMA200"
SYMBOLS = list(harness.SYMBOLS)
INTERVALS = list(harness.INTERVALS)
NOW = harness.TRAIN1_END
TRAIN1_END = harness.TRAIN1_END
DATA_CACHE = os.environ.get("F006_DATA_CACHE", "data_cache")

OUT = ROOT / "output/f006_bb_20_2_xsym_agree_sizing"
REFERENCE = ROOT / "output/f006_notrail_monthly_catalog5/summary/results.csv"
FREEZE = ROOT / "output/f006_bb_20_2_abs_atr_gate/grid_freeze.json"
EXPECTED_MEAN = 95.3217987
BASE_STAKE = 100.0
MULT_LO, MULT_HI = 0.5, 2.0
MULT_FORMULA = "clip(0.5 + 0.375 * n_agree, 0.5, 2.0)"


def expected_checksums() -> dict[str, str]:
    return json.loads(FREEZE.read_text())["checksums_used"]


def load_train1(symbol: str, interval: str, expected: dict[str, str]):
    try:
        full_df, manifest = data_contract.load_dataset(
            DATA_CACHE, symbol, interval, harness.WARMUP_START, TRAIN1_END
        )
    except data_contract.DataContractError as exc:
        raise SystemExit(f"STOP: cannot load Train-1 cache {symbol}/{interval} -- {exc}.") from exc
    want = expected[f"{symbol}_{interval}"]
    if manifest.checksum_sha256 != want:
        raise SystemExit(
            f"STOP: checksum mismatch for {symbol}/{interval}: "
            f"{manifest.checksum_sha256} != grid_freeze {want}."
        )
    idx = pd.DatetimeIndex(full_df.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    train1_df = full_df.loc[(idx >= pd.Timestamp(harness.WARMUP_START)) & (idx < TRAIN1_END)]
    if train1_df.empty or pd.DatetimeIndex(train1_df.index).max() >= TRAIN1_END:
        raise SystemExit(f"STOP: bad Train-1 slice for {symbol}/{interval}.")
    return train1_df, manifest


def agreement_multiplier_series(own_signal: pd.Series, other_signals) -> pd.Series:
    """Causal frozen multiplier aligned to the engine's fill-bar index.

    A signal observed at bar i close fills at bar i+1 open, and the engine reads stake_series
    at the fill bar, so the closed-bar agreement is shifted forward one row. The first row is
    NaN (no prior closed bar); _run_one fills it with the uniform BASE_STAKE.
    """
    own = entry_masks.normalized_signal(own_signal)
    n_agree = pd.Series(0, index=own.index, dtype=int)
    for other_signal in other_signals:
        other = entry_masks.normalized_signal(other_signal).reindex(own.index).fillna(0)
        n_agree += ((other == own) & (own != 0)).astype(int)
    closed_bar_mult = (0.5 + 0.375 * n_agree).clip(lower=MULT_LO, upper=MULT_HI)
    return closed_bar_mult.shift(1)


def _run_one(train1_df, mask, mult_series, symbol: str, interval: str):
    t0 = time.time()
    common = dict(
        interval=interval, now=NOW, symbol=symbol,
        initial_equity=harness.INITIAL_EQUITY, stake=BASE_STAKE,
        max_sl_pct=harness.MAX_SL_PCT, activate_pct=harness.ACTIVATE_PCT,
        trail_pct=harness.TRAIL_PCT, cooldown_candles=harness.COOLDOWN,
        entry_regime_mask=mask, **harness.FIXED_PARAMS,
    )
    baseline_result = backtest_engine.run_backtest(train1_df, NAME, stake_series=None, **common)
    stake_series = (BASE_STAKE * mult_series).fillna(BASE_STAKE)
    sized_result = backtest_engine.run_backtest(
        train1_df, NAME, stake_series=stake_series, **common
    )

    baseline_all = baseline_result.trades.copy()
    sized_all = sized_result.trades.copy()
    baseline_cohort = sibling._train1_entry_trades(baseline_all)
    sized_cohort = sibling._train1_entry_trades(sized_all)
    baseline_keys = list(pd.to_datetime(baseline_all["entry_time"], utc=True))
    sized_keys = list(pd.to_datetime(sized_all["entry_time"], utc=True))
    invariant_ok = (
        len(baseline_all) == len(sized_all)
        and baseline_keys == sized_keys
        and list(baseline_cohort["entry_time"]) == list(sized_cohort["entry_time"])
    )
    if not invariant_ok:
        raise SystemExit(
            f"STOP: trade-count invariant violated for {symbol}/{interval}: "
            f"total {len(baseline_all)} vs {len(sized_all)}, "
            f"Train-1-entry {len(baseline_cohort)} vs {len(sized_cohort)}"
        )

    baseline_monthly = sibling._entry_month_rows(baseline_cohort)
    sized_monthly = sibling._entry_month_rows(sized_cohort)
    row = {
        "symbol": symbol,
        "interval": interval,
        "strategy": NAME,
        "n_trades": int(len(baseline_all)),
        "n_trades_total_baseline": int(len(baseline_all)),
        "n_trades_total_sized": int(len(sized_all)),
        "n_trades_train1_entry_baseline": int(len(baseline_cohort)),
        "n_trades_train1_entry_sized": int(len(sized_cohort)),
        "trade_count_invariant_ok": invariant_ok,
        "train1_net_pnl_baseline": sibling._equity_train1_net_pnl(baseline_result),
        "train1_net_pnl_sized": sibling._equity_train1_net_pnl(sized_result),
        "train1_entry_net_pnl_baseline": round(float(baseline_cohort["net_pnl"].sum()), 6),
        "train1_entry_net_pnl_sized": round(float(sized_cohort["net_pnl"].sum()), 6),
        "losing_month_floor_baseline": sibling._losing_floor(baseline_monthly),
        "losing_month_floor_sized": sibling._losing_floor(sized_monthly),
        **sibling._stake_stats(sized_cohort),
        "baseline_entry_monthly": baseline_monthly,
        "sized_entry_monthly": sized_monthly,
        "seconds": round(time.time() - t0, 2),
    }
    for frame in (baseline_all, sized_all, baseline_cohort, sized_cohort):
        frame["symbol"] = symbol
        frame["interval"] = interval
    return row, baseline_all, sized_all, baseline_cohort, sized_cohort


def control_replay(summary_df: pd.DataFrame) -> dict:
    prior = pd.read_csv(REFERENCE)
    prior["interval"] = prior.interval.astype(str)
    prior = prior.loc[prior.strategy == NAME]
    joined = summary_df.merge(
        prior, on=["symbol", "interval", "strategy"], suffixes=("", "_prior")
    )
    diff = (joined.train1_net_pnl_baseline - joined.train1_net_pnl).abs()
    if len(joined) != 10 or diff.max() > 1e-6:
        raise SystemExit(f"STOP: control train1_net_pnl replay failed (max diff {diff.max()}).")
    if (joined.n_trades != joined.n_trades_prior).any():
        raise SystemExit("STOP: control n_trades replay failed.")
    mean = float(joined.train1_net_pnl_baseline.mean())
    if abs(mean - EXPECTED_MEAN) > 1e-6:
        raise SystemExit(f"STOP: control mean {mean} != {EXPECTED_MEAN}.")
    return {
        "rows_compared": int(len(joined)),
        "columns": ["train1_net_pnl", "n_trades"],
        "max_abs_train1_diff": float(diff.max()),
        "n_trades_mismatches": int((joined.n_trades != joined.n_trades_prior).sum()),
        "control_mean_train1_net_pnl": mean,
        "control_sum_train1_net_pnl": float(joined.train1_net_pnl_baseline.sum()),
        "reference_sum_train1_net_pnl": float(joined.train1_net_pnl.sum()),
        "source": str(REFERENCE.relative_to(ROOT)),
    }


def main():
    t_start = time.time()
    commit_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True, cwd=ROOT
    ).strip()
    assert NAME in strategy.STRATEGY_CATALOG
    for sub in ("summary", "raw", "blotters"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    expected = expected_checksums()
    rows, base_all, sized_all, base_cohorts, sized_cohorts = [], [], [], [], []
    checksums_used = {}
    for interval in INTERVALS:
        frames = {}
        for symbol in SYMBOLS:
            frames[symbol], manifest = load_train1(symbol, interval, expected)
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
            mult_series = agreement_multiplier_series(
                signals[symbol], [signals[o] for o in SYMBOLS if o != symbol]
            )
            mask = entry_masks.one_shot_entry_mask(signals[symbol])
            row, b_all, s_all, b_cohort, s_cohort = _run_one(
                frames[symbol], mask, mult_series, symbol, interval
            )
            rows.append(row)
            base_all.append(b_all)
            sized_all.append(s_all)
            base_cohorts.append(b_cohort)
            sized_cohorts.append(s_cohort)
            (OUT / "raw" / f"{symbol}_{interval}.json").write_text(
                json.dumps(row, indent=2, default=str) + "\n"
            )
            b_all.to_csv(OUT / "blotters" / f"{symbol}_{interval}_control.csv", index=False)
            s_all.to_csv(OUT / "blotters" / f"{symbol}_{interval}_sized.csv", index=False)
        print(f"done interval={interval} ({len(rows)} series, {time.time() - t_start:.1f}s)")

    summary_df = pd.DataFrame([
        {k: v for k, v in row.items() if k not in ("baseline_entry_monthly", "sized_entry_monthly")}
        for row in rows
    ])
    # Control must replay catalog5 before anything about the sized arm is scored.
    replay = control_replay(summary_df)
    summary_df.to_csv(OUT / "summary" / "results.csv", index=False)
    control_cols = ["symbol", "interval", "strategy", "n_trades_total_baseline",
                    "n_trades_train1_entry_baseline", "train1_net_pnl_baseline",
                    "train1_entry_net_pnl_baseline", "losing_month_floor_baseline"]
    sized_cols = ["symbol", "interval", "strategy", "n_trades_total_sized",
                  "n_trades_train1_entry_sized", "train1_net_pnl_sized",
                  "train1_entry_net_pnl_sized", "losing_month_floor_sized",
                  "stake_cv", "mean_mult_winners", "mean_mult_losers", "mean_mult_gap"]
    summary_df[control_cols].to_csv(OUT / "summary" / "control.csv", index=False)
    summary_df[sized_cols].to_csv(OUT / "summary" / "sized.csv", index=False)

    baseline_pool = pd.concat(base_cohorts, ignore_index=True)
    sized_pool = pd.concat(sized_cohorts, ignore_index=True)
    baseline_monthly = sibling._entry_month_rows(baseline_pool)
    sized_monthly = sibling._entry_month_rows(sized_pool)
    pooled_stats = sibling._stake_stats(sized_pool)
    big_winners = sibling._big_winner_metrics(baseline_pool, sized_pool)

    mean_baseline = float(summary_df["train1_net_pnl_baseline"].mean())
    mean_sized = float(summary_df["train1_net_pnl_sized"].mean())
    floor_baseline = sibling._losing_floor(baseline_monthly)
    floor_sized = sibling._losing_floor(sized_monthly)
    total_invariant = bool(summary_df["trade_count_invariant_ok"].all())
    all_series_cv_ok = bool(summary_df["stake_cv_ok"].all())
    mean_gap = pooled_stats["mean_mult_gap"]

    falsified = []
    if mean_sized <= mean_baseline:
        falsified.append("(a) mean train1_net_pnl_sized <= control")
    if floor_sized >= floor_baseline:
        falsified.append(f"(b) pooled losing-month floor did not improve ({floor_sized} >= {floor_baseline})")
    if mean_gap is None or mean_gap <= 0:
        falsified.append(f"(c) pooled winner-minus-loser mean multiplier <= 0 ({mean_gap})")
    if not total_invariant:
        falsified.append("(d) trade-count invariant broken")
    if pooled_stats["stake_cv"] <= 0.05 or not all_series_cv_ok:
        falsified.append("(e) Train-1-entry stake_cv <= 0.05")

    def arm(pool, mean, monthly, floor, prefix):
        return {
            "mean_train1_net_pnl": round(mean, 6),
            "sum_train1_net_pnl": round(float(summary_df[f"train1_net_pnl_{prefix}"].sum()), 6),
            "positive_series": int((summary_df[f"train1_net_pnl_{prefix}"] > 0).sum()),
            "total_closed_trades": int(summary_df[f"n_trades_total_{prefix}"].sum()),
            "train1_entry_trades": int(len(pool)),
            "train1_entry_net_pnl": round(float(pool["net_pnl"].sum()), 6),
            "train1_entry_net_per_trade": round(float(pool["net_pnl"].mean()), 6),
            "pooled_entry_month_net_pnl": monthly,
            "pooled_losing_month_floor": floor,
        }

    cell_summary = {
        "experiment_id": "H-BB-20-2-XSYM-AGREE-SIZING-01",
        "strategy": NAME,
        "number_of_trials": 1,
        "mult_formula": MULT_FORMULA,
        "control_replay": replay,
        "control": arm(baseline_pool, mean_baseline, baseline_monthly, floor_baseline, "baseline"),
        "sized": {
            **arm(sized_pool, mean_sized, sized_monthly, floor_sized, "sized"),
            "pooled_stake_cv": pooled_stats["stake_cv"],
            "min_series_stake_cv": float(summary_df["stake_cv"].min()),
            "all_series_stake_cv_gt_0_05": all_series_cv_ok,
            "mean_mult_winners": pooled_stats["mean_mult_winners"],
            "mean_mult_losers": pooled_stats["mean_mult_losers"],
            "mean_mult_winner_minus_loser": mean_gap,
        },
        "trade_count_invariant_all_series": total_invariant,
        "big_winner_contribution": big_winners,
        "falsified": bool(falsified),
        "falsification_conditions_fired": falsified,
    }
    (OUT / "summary" / "cell_summary.json").write_text(json.dumps(cell_summary, indent=2) + "\n")

    manifest = {
        "script": "scripts/f006_bb_20_2_xsym_agree_sizing.py",
        "git_commit_at_run": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "n_series": len(rows),
        "data_cache": DATA_CACHE,
        "data_window": [harness.WARMUP_START, str(TRAIN1_END)],
        "validation_holdout_loaded": False,
        "checksums_used": checksums_used,
        "checksums_source": str(FREEZE.relative_to(ROOT)),
        "params": {
            "activate_pct": harness.ACTIVATE_PCT,
            "trail_pct": harness.TRAIL_PCT,
            "max_sl_pct": harness.MAX_SL_PCT,
            "cooldown_candles": harness.COOLDOWN,
            "mask_mode": "one_shot",
            "initial_equity": harness.INITIAL_EQUITY,
            "base_stake": BASE_STAKE,
            "mult_formula": MULT_FORMULA,
            "n_agree": "count of other 4 basket symbols whose BB_20_2_EMA200 persistent signal "
                       "equals the traded symbol's nonzero direction on the same closed bar",
            "stake_alignment": "fill bar uses multiplier from prior closed bar; first bar stake 100.0",
            **harness.FIXED_PARAMS,
        },
        "control_match": replay,
        "cell_summary": cell_summary,
        "seconds": round(time.time() - t_start, 2),
    }
    (OUT / "summary" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    verdict = "FALSIFIED" if falsified else "NOT FALSIFIED"
    lines = [
        "H-BB-20-2-XSYM-AGREE-SIZING-01",
        f"Run started: {manifest['run_started_utc']}",
        f"Commit at run: {commit_sha}",
        f"Control replay: {replay['rows_compared']} rows, max abs train1 diff "
        f"{replay['max_abs_train1_diff']:.3g}, n_trades mismatches {replay['n_trades_mismatches']}",
        f"Control mean Train-1 net PnL: {mean_baseline:.6f} (sum {replay['control_sum_train1_net_pnl']:.6f})",
        f"Control Train-1-entry: n={len(baseline_pool)}, net={baseline_pool['net_pnl'].sum():.6f}",
        f"Control pooled losing-month floor: {floor_baseline}/12",
        f"Sized mean Train-1 net PnL: {mean_sized:.6f}",
        f"Sized Train-1-entry: n={len(sized_pool)}, net={sized_pool['net_pnl'].sum():.6f}",
        f"Sized pooled losing-month floor: {floor_sized}/12",
        f"Pooled stake CV: {pooled_stats['stake_cv']:.6f} (min series {summary_df['stake_cv'].min():.6f})",
        f"Pooled winner-minus-loser mean multiplier: {mean_gap}",
        f"Big winners (control net>={sibling.BIG_WINNER_THRESHOLD}): "
        f"{big_winners['baseline_count']} / {big_winners['baseline_pnl_sum']:.6f}; "
        f"sized on same keys {big_winners['sized_pnl_on_baseline_big_winner_entry_keys']:.6f}",
        f"Verdict: {verdict}",
        *[f"  {c}" for c in falsified],
    ]
    (OUT / "summary" / "run.log").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
