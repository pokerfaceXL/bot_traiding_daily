"""Run the pre-registered cross-symbol agreement sizing test for EMA_50_200.

The only sized arm uses the frozen formula
``mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)``. Metrics that describe the
entry cohort use trades entered from 2024-03-01 through 2025-02-28 UTC; the
backtest itself retains the earlier warmup so indicators are unchanged.

Run: [F006_DATA_CACHE=DIR] python3 scripts/f006_ema_50_200_xsym_agree_sizing.py
Only the frozen Train-1 caches (*_20240126T000000Z_20250301T000000Z.csv) are loaded; their
checksums must equal output/f006_ema_50_200_abs_atr_gate/grid_freeze.json. F006_DATA_CACHE
defaults to this checkout's data_cache (strategy.py owns sys.argv[1]); artifacts stay anchored to this file's repo.
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

import backtest_engine  # noqa: E402
import data_contract  # noqa: E402
import entry_masks  # noqa: E402
import regularity  # noqa: E402
import strategy  # noqa: E402

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]
NAME = "EMA_50_200"

WARMUP_START = "2024-01-26T00:00:00Z"
TRAIN1_START = pd.Timestamp("2024-03-01T00:00:00Z")
TRAIN1_END = pd.Timestamp("2025-03-01T00:00:00Z")
NOW = TRAIN1_END
CACHE_DIR = os.environ.get("F006_DATA_CACHE", str(ROOT / "data_cache"))

FREEZE_JSON = ROOT / "output/f006_ema_50_200_abs_atr_gate/grid_freeze.json"
REFERENCE_CSV = ROOT / "output/f006_notrail_monthly_catalog5/summary/results.csv"
EXPECTED_CONTROL_MEAN = 72.6693115

ACTIVATE_PCT = 10.0
TRAIL_PCT = 0.04
MAX_SL_PCT = 0.03
COOLDOWN = 0
FIXED_PARAMS = dict(
    leverage=1.0,
    atr_multiplier=1.5,
    commission_rate_bps=10.0,
    half_spread_bps=5.0,
    slippage_bps=2.0,
)
INITIAL_EQUITY = 500.0
BASE_STAKE = 100.0
MULT_LO, MULT_HI = 0.5, 2.0
BIG_WINNER_THRESHOLD = 29.9

TRAIN1_MONTHS = [
    (2024, 3), (2024, 4), (2024, 5), (2024, 6), (2024, 7), (2024, 8),
    (2024, 9), (2024, 10), (2024, 11), (2024, 12), (2025, 1), (2025, 2),
]
TRAIN1_MONTHS_SET = set(TRAIN1_MONTHS)
OUT_DIR = str(ROOT / "output/f006_ema_50_200_xsym_agree_sizing")


def _expected_checksums() -> dict:
    with open(FREEZE_JSON) as f:
        return json.load(f)["checksums_used"]


def load_train1(symbol: str, interval: str, expected_checksums: dict):
    try:
        # The cache request ends at TRAIN1_END: no validation/holdout bars are loaded.
        full_df, manifest = data_contract.load_dataset(
            CACHE_DIR, symbol, interval, WARMUP_START, TRAIN1_END
        )
    except data_contract.DataContractError as exc:
        raise SystemExit(
            f"STOP: cannot load frozen dataset for {symbol}/{interval} from {CACHE_DIR} -- {exc}."
        ) from exc
    expected = expected_checksums[f"{symbol}_{interval}"]
    if manifest.checksum_sha256 != expected:
        raise SystemExit(
            f"STOP: checksum mismatch for {symbol}/{interval}: cache has "
            f"{manifest.checksum_sha256}, abs-ATR grid_freeze.json expects {expected}."
        )
    idx = pd.DatetimeIndex(full_df.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    train1_df = full_df.loc[(idx >= pd.Timestamp(WARMUP_START)) & (idx < TRAIN1_END)]
    assert not train1_df.empty, f"empty Train 1 slice for {symbol}/{interval}"
    assert pd.DatetimeIndex(train1_df.index).max() < TRAIN1_END
    return train1_df, manifest


def compute_agreement_multiplier_series(
    own_train1_df: pd.DataFrame,
    others_train1_dfs: dict[str, pd.DataFrame],
    interval: str,
    now: pd.Timestamp | None = None,
) -> pd.Series:
    """Return the causal frozen multiplier aligned to the engine's fill-bar index.

    A signal observed at bar i close queues an entry filled at bar i+1 open. The engine reads
    stake_series at that fill bar, so shift the closed-bar agreement forward one row. The first
    bar has no prior closed-bar agreement; _run_one fills its final stake with BASE_STAKE.
    """
    now = NOW if now is None else now
    own = entry_masks.normalized_signal(
        entry_masks.strategy_signal_series(own_train1_df, NAME, interval=interval, now=now)
    )
    n_agree = pd.Series(0, index=own.index, dtype=int)
    for df in others_train1_dfs.values():
        other = entry_masks.normalized_signal(
            entry_masks.strategy_signal_series(df, NAME, interval=interval, now=now)
        ).reindex(own.index).fillna(0)
        n_agree += ((other == own) & (own != 0)).astype(int)
    closed_bar_mult = (0.5 + 0.375 * n_agree).clip(lower=MULT_LO, upper=MULT_HI)
    return closed_bar_mult.shift(1)


def _net_pnl_for_months(days) -> float:
    return sum(
        d.pnl for d in days
        if (d.day.year, d.day.month) in TRAIN1_MONTHS_SET and d.status != "missing"
    )


def _equity_train1_net_pnl(result) -> float:
    days, _months = regularity.compute_regularity(result.equity_curve)
    return round(_net_pnl_for_months(days), 6)


def _train1_entry_trades(trades: pd.DataFrame) -> pd.DataFrame:
    result = trades.copy()
    entry_times = pd.to_datetime(result["entry_time"], utc=True)
    result = result.loc[(entry_times >= TRAIN1_START) & (entry_times < TRAIN1_END)].copy()
    result["entry_time"] = pd.to_datetime(result["entry_time"], utc=True)
    return result.reset_index(drop=True)


def _entry_month_rows(trades: pd.DataFrame) -> list[dict]:
    if trades.empty:
        pnl_by_month = pd.Series(dtype=float)
    else:
        keys = trades["entry_time"].dt.strftime("%Y-%m")
        pnl_by_month = trades.groupby(keys)["net_pnl"].sum()
    return [
        {
            "month": f"{year}-{month:02d}",
            "net_pnl": round(float(pnl_by_month.get(f"{year}-{month:02d}", 0.0)), 6),
        }
        for year, month in TRAIN1_MONTHS
    ]


def _losing_floor(monthly_rows: list[dict]) -> int:
    return sum(row["net_pnl"] < 0 for row in monthly_rows)


def _stake_stats(trades: pd.DataFrame) -> dict:
    applied_mult = (trades["stake"] / BASE_STAKE).to_numpy()
    mean_mult = float(np.mean(applied_mult))
    cv = float(np.std(applied_mult) / mean_mult) if mean_mult else 0.0
    wins = trades["net_pnl"] > 0
    mean_winners = float(applied_mult[wins.to_numpy()].mean()) if wins.any() else None
    mean_losers = float(applied_mult[(~wins).to_numpy()].mean()) if (~wins).any() else None
    gap = mean_winners - mean_losers if mean_winners is not None and mean_losers is not None else None
    return {
        "stake_cv": round(cv, 6),
        "stake_cv_ok": cv > 0.05,
        "mean_mult_winners": mean_winners,
        "mean_mult_losers": mean_losers,
        "mean_mult_gap": round(gap, 6) if gap is not None else None,
    }


def _run_one(train1_df, mask, mult_series, symbol: str, interval: str):
    t0 = time.time()
    common = dict(
        interval=interval,
        now=NOW,
        symbol=symbol,
        initial_equity=INITIAL_EQUITY,
        stake=BASE_STAKE,
        max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT,
        trail_pct=TRAIL_PCT,
        cooldown_candles=COOLDOWN,
        entry_regime_mask=mask,
        **FIXED_PARAMS,
    )
    baseline_result = backtest_engine.run_backtest(
        train1_df, NAME, stake_series=None, **common
    )
    stake_series = (BASE_STAKE * mult_series).fillna(BASE_STAKE)
    sized_result = backtest_engine.run_backtest(
        train1_df, NAME, stake_series=stake_series, **common
    )

    baseline_all = baseline_result.trades.copy()
    sized_all = sized_result.trades.copy()
    baseline_cohort = _train1_entry_trades(baseline_all)
    sized_cohort = _train1_entry_trades(sized_all)
    baseline_keys = list(pd.to_datetime(baseline_cohort["entry_time"], utc=True))
    sized_keys = list(pd.to_datetime(sized_cohort["entry_time"], utc=True))
    invariant_ok = len(baseline_all) == len(sized_all) and baseline_keys == sized_keys
    if not invariant_ok:
        raise SystemExit(
            f"STOP: trade-count invariant violated for {symbol}/{interval}: "
            f"total {len(baseline_all)} != {len(sized_all)} or Train-1-entry keys differ "
            f"({len(baseline_cohort)} vs {len(sized_cohort)})"
        )

    baseline_monthly = _entry_month_rows(baseline_cohort)
    sized_monthly = _entry_month_rows(sized_cohort)
    stats = _stake_stats(sized_cohort)
    row = {
        "symbol": symbol,
        "interval": interval,
        "n_trades_total_baseline": int(len(baseline_all)),
        "n_trades_total_sized": int(len(sized_all)),
        "n_trades_train1_entry_baseline": int(len(baseline_cohort)),
        "n_trades_train1_entry_sized": int(len(sized_cohort)),
        "trade_count_invariant_ok": invariant_ok,
        "train1_net_pnl_baseline": _equity_train1_net_pnl(baseline_result),
        "train1_net_pnl_sized": _equity_train1_net_pnl(sized_result),
        "train1_entry_net_pnl_baseline": round(float(baseline_cohort["net_pnl"].sum()), 6),
        "train1_entry_net_pnl_sized": round(float(sized_cohort["net_pnl"].sum()), 6),
        "losing_month_floor_baseline": _losing_floor(baseline_monthly),
        "losing_month_floor_sized": _losing_floor(sized_monthly),
        **stats,
        "baseline_entry_monthly": baseline_monthly,
        "sized_entry_monthly": sized_monthly,
        "seconds": round(time.time() - t0, 2),
    }
    for cohort in (baseline_cohort, sized_cohort):
        cohort["symbol"] = symbol
        cohort["interval"] = interval
    return row, baseline_cohort, sized_cohort


def _pooled_monthly(trades: pd.DataFrame) -> list[dict]:
    return _entry_month_rows(trades)


def _big_winner_metrics(baseline: pd.DataFrame, sized: pd.DataFrame) -> dict:
    key_columns = ["symbol", "interval", "entry_time"]
    baseline_big = baseline.loc[baseline["net_pnl"] >= BIG_WINNER_THRESHOLD]
    sized_big = sized.loc[sized["net_pnl"] >= BIG_WINNER_THRESHOLD]
    baseline_keys = baseline_big[key_columns]
    sized_on_baseline_keys = sized.merge(baseline_keys, on=key_columns, how="inner")
    return {
        "threshold_net_pnl": BIG_WINNER_THRESHOLD,
        "baseline_count": int(len(baseline_big)),
        "baseline_pnl_sum": round(float(baseline_big["net_pnl"].sum()), 6),
        "sized_count": int(len(sized_big)),
        "sized_pnl_sum": round(float(sized_big["net_pnl"].sum()), 6),
        "sized_pnl_on_baseline_big_winner_entry_keys": round(
            float(sized_on_baseline_keys["net_pnl"].sum()), 6
        ),
    }


def main():
    t_start = time.time()
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None

    expected_checksums = _expected_checksums()
    assert NAME in strategy.STRATEGY_CATALOG
    os.makedirs(f"{OUT_DIR}/summary", exist_ok=True)
    os.makedirs(f"{OUT_DIR}/raw", exist_ok=True)

    rows = []
    baseline_cohorts = []
    sized_cohorts = []
    checksums_used = {}
    for interval in INTERVALS:
        frames = {}
        for symbol in SYMBOLS:
            frames[symbol], manifest = load_train1(symbol, interval, expected_checksums)
            checksums_used[f"{symbol}_{interval}"] = manifest.checksum_sha256

        ref_idx = pd.DatetimeIndex(frames["BTCUSDT"].index)
        for symbol in SYMBOLS:
            if not pd.DatetimeIndex(frames[symbol].index).equals(ref_idx):
                raise SystemExit(
                    f"STOP: index-equality precondition violated for {symbol}/{interval}"
                )

        for symbol in SYMBOLS:
            own_df = frames[symbol]
            others = {other: frames[other] for other in SYMBOLS if other != symbol}
            mult_series = compute_agreement_multiplier_series(own_df, others, interval)
            signal = entry_masks.strategy_signal_series(own_df, NAME, interval=interval, now=NOW)
            mask = entry_masks.one_shot_entry_mask(signal)
            row, baseline_cohort, sized_cohort = _run_one(
                own_df, mask, mult_series, symbol, interval
            )
            rows.append(row)
            baseline_cohorts.append(baseline_cohort)
            sized_cohorts.append(sized_cohort)
            with open(f"{OUT_DIR}/raw/{symbol}_{interval}.json", "w") as f:
                json.dump(row, f, indent=2, default=str)
        print(
            f"done interval={interval} ({len(rows)} series so far, "
            f"{time.time() - t_start:.1f}s elapsed)"
        )

    baseline_pool = pd.concat(baseline_cohorts, ignore_index=True)
    sized_pool = pd.concat(sized_cohorts, ignore_index=True)
    baseline_monthly = _pooled_monthly(baseline_pool)
    sized_monthly = _pooled_monthly(sized_pool)
    pooled_stats = _stake_stats(sized_pool)
    big_winners = _big_winner_metrics(baseline_pool, sized_pool)

    summary_rows = [
        {
            key: value for key, value in row.items()
            if key not in ("baseline_entry_monthly", "sized_entry_monthly")
        }
        for row in rows
    ]
    summary_df = pd.DataFrame(summary_rows)

    # Control gate: the uniform arm must replay this name's catalog5 Train-1 rows before the
    # sized arm is scored.
    prior = pd.read_csv(REFERENCE_CSV)
    prior = prior.loc[prior.strategy == NAME].assign(interval=lambda d: d.interval.astype(str))
    joined = summary_df.merge(prior, on=["symbol", "interval"], how="inner")
    control_diff = (joined["train1_net_pnl_baseline"] - joined["train1_net_pnl"]).abs()
    control_match = {
        "reference_csv": str(REFERENCE_CSV.relative_to(ROOT)),
        "n_rows_matched": int(len(joined)),
        "reference_mean_train1_net_pnl": round(float(prior["train1_net_pnl"].mean()), 7),
        "replayed_mean_train1_net_pnl": round(float(summary_df["train1_net_pnl_baseline"].mean()), 7),
        "max_abs_train1_net_pnl_diff": float(control_diff.max()) if len(joined) else None,
        "n_trades_all_equal": bool(
            (joined["n_trades_total_baseline"] == joined["n_trades"]).all()
        ),
    }
    if (
        len(joined) != 10
        or control_match["max_abs_train1_net_pnl_diff"] > 1e-6
        or not control_match["n_trades_all_equal"]
        or abs(control_match["replayed_mean_train1_net_pnl"] - EXPECTED_CONTROL_MEAN) > 1e-6
    ):
        raise SystemExit(f"STOP: control replay failed: {control_match}")

    summary_df.to_csv(f"{OUT_DIR}/summary/results.csv", index=False)
    baseline_pool.to_csv(f"{OUT_DIR}/summary/control_train1_entry_blotter.csv", index=False)
    sized_pool.to_csv(f"{OUT_DIR}/summary/sized_train1_entry_blotter.csv", index=False)

    mean_baseline = float(summary_df["train1_net_pnl_baseline"].mean())
    mean_sized = float(summary_df["train1_net_pnl_sized"].mean())
    floor_baseline = _losing_floor(baseline_monthly)
    floor_sized = _losing_floor(sized_monthly)
    total_invariant = bool(summary_df["trade_count_invariant_ok"].all())
    all_series_cv_ok = bool(summary_df["stake_cv_ok"].all())
    mean_gap = pooled_stats["mean_mult_gap"]

    falsified = []
    if mean_sized <= mean_baseline:
        falsified.append("(a) mean train1_net_pnl_sized <= baseline")
    if floor_sized >= floor_baseline:
        falsified.append(
            f"(b) pooled losing-month floor did not improve ({floor_sized} >= {floor_baseline})"
        )
    if mean_gap is None or mean_gap <= 0:
        falsified.append(f"(c) pooled winner-minus-loser mean multiplier <= 0 ({mean_gap})")
    if not total_invariant:
        falsified.append("(d) trade-count invariant broken")
    if pooled_stats["stake_cv"] <= 0.05 or not all_series_cv_ok:
        falsified.append("(e) Train-1-entry stake_cv <= 0.05")

    cell_summary = {
        "experiment_id": "H-EMA-50-200-XSYM-AGREE-SIZING-01",
        "strategy": NAME,
        "number_of_trials": 1,
        "control": {
            "mean_train1_net_pnl": round(mean_baseline, 6),
            "total_closed_trades": int(summary_df["n_trades_total_baseline"].sum()),
            "train1_entry_trades": int(len(baseline_pool)),
            "train1_entry_net_pnl": round(float(baseline_pool["net_pnl"].sum()), 6),
            "train1_entry_net_per_trade": round(float(baseline_pool["net_pnl"].mean()), 6),
            "pooled_entry_month_net_pnl": baseline_monthly,
            "pooled_losing_month_floor": floor_baseline,
        },
        "sized": {
            "mean_train1_net_pnl": round(mean_sized, 6),
            "total_closed_trades": int(summary_df["n_trades_total_sized"].sum()),
            "train1_entry_trades": int(len(sized_pool)),
            "train1_entry_net_pnl": round(float(sized_pool["net_pnl"].sum()), 6),
            "train1_entry_net_per_trade": round(float(sized_pool["net_pnl"].mean()), 6),
            "pooled_entry_month_net_pnl": sized_monthly,
            "pooled_losing_month_floor": floor_sized,
            "pooled_stake_cv": pooled_stats["stake_cv"],
            "all_series_stake_cv_gt_0_05": all_series_cv_ok,
            "mean_mult_winners": pooled_stats["mean_mult_winners"],
            "mean_mult_losers": pooled_stats["mean_mult_losers"],
            "mean_mult_winner_minus_loser": mean_gap,
        },
        "control_match": control_match,
        "trade_count_invariant_all_series": total_invariant,
        "big_winner_contribution": big_winners,
        "falsified": bool(falsified),
        "falsification_conditions_fired": falsified,
    }
    with open(f"{OUT_DIR}/summary/cell_summary.json", "w") as f:
        json.dump(cell_summary, f, indent=2)

    manifest = {
        "script": "scripts/f006_ema_50_200_xsym_agree_sizing.py",
        "git_commit_at_run": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "n_series": len(rows),
        "cache_dir": CACHE_DIR,
        "data_window": [WARMUP_START, str(TRAIN1_END)],
        "validation_holdout_loaded": False,
        "checksums_used": checksums_used,
        "checksums_match_abs_atr_grid_freeze": checksums_used == expected_checksums,
        "params": {
            "activate_pct": ACTIVATE_PCT,
            "trail_pct": TRAIL_PCT,
            "max_sl_pct": MAX_SL_PCT,
            "cooldown_candles": COOLDOWN,
            "mask_mode": "one_shot",
            "initial_equity": INITIAL_EQUITY,
            "base_stake": BASE_STAKE,
            "mult_formula": "clip(0.5 + 0.375 * n_agree, 0.5, 2.0)",
            "stake_alignment": "fill bar uses multiplier from prior closed bar; leading fillna(100.0)",
            **FIXED_PARAMS,
        },
        "cell_summary": cell_summary,
        "seconds": round(time.time() - t_start, 2),
    }
    with open(f"{OUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    verdict = "FALSIFIED" if falsified else "NOT FALSIFIED"
    with open(f"{OUT_DIR}/summary/run.log", "w") as f:
        f.write("H-EMA-50-200-XSYM-AGREE-SIZING-01\n")
        f.write(f"Run started: {manifest['run_started_utc']}\n")
        f.write(f"Commit at run: {commit_sha}\n")
        f.write(f"Control mean Train-1 net PnL: {mean_baseline:.6f}\n")
        f.write(
            f"Control match vs catalog5: rows={control_match['n_rows_matched']}, "
            f"max_abs_diff={control_match['max_abs_train1_net_pnl_diff']:.3e}, "
            f"n_trades_equal={control_match['n_trades_all_equal']}\n"
        )
        f.write(
            f"Control trades: total={cell_summary['control']['total_closed_trades']}, "
            f"Train-1-entry={len(baseline_pool)}, "
            f"entry net={baseline_pool['net_pnl'].sum():.6f}\n"
        )
        f.write(f"Control pooled losing-month floor: {floor_baseline}/12\n")
        f.write(f"Sized mean Train-1 net PnL: {mean_sized:.6f}\n")
        f.write(
            f"Sized trades: total={cell_summary['sized']['total_closed_trades']}, "
            f"Train-1-entry={len(sized_pool)}, entry net={sized_pool['net_pnl'].sum():.6f}\n"
        )
        f.write(f"Sized pooled losing-month floor: {floor_sized}/12\n")
        f.write(f"Pooled stake CV: {pooled_stats['stake_cv']:.6f}\n")
        f.write(f"Pooled winner-minus-loser mean multiplier: {mean_gap:.6f}\n")
        f.write(f"Verdict: {verdict}\n")
        for condition in falsified:
            f.write(f"  {condition}\n")

    print(f"\n{len(rows)} series -> {OUT_DIR}/summary/")
    print(
        f"Control: mean={mean_baseline:.2f}, entry cohort n={len(baseline_pool)}, "
        f"net={baseline_pool['net_pnl'].sum():.2f}, floor={floor_baseline}/12"
    )
    print(
        f"Sized: mean={mean_sized:.2f}, entry cohort n={len(sized_pool)}, "
        f"net={sized_pool['net_pnl'].sum():.2f}, floor={floor_sized}/12"
    )
    print(f"Pooled winner-minus-loser multiplier gap={mean_gap:.6f}")
    print(f"Verdict: {verdict} {falsified}")


if __name__ == "__main__":
    main()
