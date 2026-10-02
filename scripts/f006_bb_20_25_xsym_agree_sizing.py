"""
F006 -- cross-symbol agreement position sizing for BB_20_25_EMA200 NO_TRAIL.

Tests the hypothesis in spec/research/F006-hypothesis-bb-20-25-xsym-agree-sizing.md: whether
scaling each trade's stake by the count of other basket symbols showing the same-direction
BB_20_25_EMA200 signal at entry causes mean Train-1 net PnL to rise versus uniform stake=100
AND strictly lowers the pooled losing-month floor, with mean(mult|winner) > mean(mult|loser).

Single pre-registered formula: mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0), where n_agree
is the count (0-4) of other symbols whose BB_20_25_EMA200 persistent signal matches the traded
symbol's nonzero direction on the same closed bar.

Adapts stake_series pattern from scripts/f006_position_sizing_vol_inverse_experiment.py and
agreement inputs from scripts/f006_entry_cross_symbol_experiment.py.

Single pass, .venv_test only. Writes only output/f006_bb_20_25_xsym_agree_sizing/.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine  # noqa: E402
import data_contract  # noqa: E402
import entry_masks  # noqa: E402
import regularity  # noqa: E402
import strategy  # noqa: E402

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]
NAME = "BB_20_25_EMA200"

WARMUP_START = "2024-01-26T00:00:00Z"
HOLDOUT_END = "2026-09-01T00:00:00Z"
TRAIN1_END = pd.Timestamp("2025-03-01T00:00:00Z")
NOW = TRAIN1_END

# spec/research/F005-validation-protocol.md section 6, duplicated not imported.
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

# NO_TRAIL cell, identical to other F006 scripts.
ACTIVATE_PCT = 10.0
TRAIL_PCT = 0.04  # moot -- trail never arms, recorded as None
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

# Pre-registered formula from spec/research/F006-hypothesis-bb-20-25-xsym-agree-sizing.md.
MULT_LO, MULT_HI = 0.5, 2.0

TRAIN1_MONTHS = [
    (2024, 3), (2024, 4), (2024, 5), (2024, 6), (2024, 7), (2024, 8),
    (2024, 9), (2024, 10), (2024, 11), (2024, 12), (2025, 1), (2025, 2),
]
TRAIN1_MONTHS_SET = set(TRAIN1_MONTHS)

OUT_DIR = "output/f006_bb_20_25_xsym_agree_sizing"


def load_train1(symbol: str, interval: str):
    try:
        full_df, manifest = data_contract.load_dataset(
            "data_cache", symbol, interval, WARMUP_START, HOLDOUT_END
        )
    except data_contract.DataContractError as exc:
        raise SystemExit(
            f"STOP: cannot load frozen dataset for {symbol}/{interval} from data_cache -- {exc}."
        ) from exc
    expected = EXPECTED_CHECKSUMS[(symbol, interval)]
    if manifest.checksum_sha256 != expected:
        raise SystemExit(
            f"STOP: checksum mismatch for {symbol}/{interval}: cache has "
            f"{manifest.checksum_sha256}, protocol section 6 expects {expected}."
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
    others_train1_dfs: dict,
    interval: str,
    traded_symbol: str,
) -> pd.Series:
    """Compute stake multiplier series based on cross-symbol agreement count.
    
    For each bar where this symbol's BB_20_25_EMA200 signal is nonzero, count how many of the
    other 4 symbols have the same-direction signal on that bar. Apply the pre-registered formula:
        n_agree ∈ {0,1,2,3,4}
        mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)
    
    Returns a multiplier series aligned to the engine's work index (via strategy_signal_series).
    """
    own_signal = entry_masks.strategy_signal_series(own_train1_df, NAME, interval=interval, now=NOW)
    own_normalized = entry_masks.normalized_signal(own_signal)
    
    other_signals = {}
    for sym, df in others_train1_dfs.items():
        sig = entry_masks.strategy_signal_series(df, NAME, interval=interval, now=NOW)
        other_signals[sym] = entry_masks.normalized_signal(sig).reindex(own_normalized.index).fillna(0)
    
    # Count agreement: how many others match own's nonzero direction on each bar.
    n_agree = pd.Series(0, index=own_normalized.index, dtype=int)
    for other_sig in other_signals.values():
        n_agree = n_agree + ((other_sig == own_normalized) & (own_normalized != 0)).astype(int)
    
    # Apply pre-registered formula.
    mult = (0.5 + 0.375 * n_agree).clip(lower=MULT_LO, upper=MULT_HI)
    
    return mult


def _net_pnl_for_month(days, year: int, month: int) -> float:
    total = 0.0
    for d in days:
        if d.day.year == year and d.day.month == month and d.status != "missing":
            total += d.pnl
    return total


def _net_pnl_for_months(days, months_set) -> float:
    total = 0.0
    for d in days:
        if (d.day.year, d.day.month) in months_set and d.status != "missing":
            total += d.pnl
    return total


def _n_trades_per_month(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {}
    entry_times = pd.DatetimeIndex(trades["entry_time"])
    counts = {}
    for (y, m) in TRAIN1_MONTHS:
        counts[(y, m)] = int(((entry_times.year == y) & (entry_times.month == m)).sum())
    return counts


def _evaluate(result, symbol, interval) -> dict:
    days, months = regularity.compute_regularity(result.equity_curve)
    months_by_key = {(m.year, m.month): m for m in months}

    monthly_rows = []
    losing_months = []
    for (year, month) in TRAIN1_MONTHS:
        mr = months_by_key.get((year, month))
        if mr is None:
            monthly_rows.append({
                "year": year, "month": month, "is_valid": False, "net_pnl": None,
            })
            continue
        net_pnl = _net_pnl_for_month(days, year, month) if mr.is_valid else None
        monthly_rows.append({"year": year, "month": month, "is_valid": mr.is_valid, "net_pnl": net_pnl})
        if mr.is_valid and net_pnl is not None and net_pnl < 0:
            losing_months.append((year, month))

    train1_net_pnl = _net_pnl_for_months(days, TRAIN1_MONTHS_SET)
    n_valid_months = sum(1 for r in monthly_rows if r["is_valid"])
    pooled_losing_month_floor = len(losing_months)

    return {
        "n_trades": int(len(result.trades)),
        "train1_net_pnl": round(train1_net_pnl, 6),
        "n_valid_months": n_valid_months,
        "pooled_losing_month_floor": pooled_losing_month_floor,
        "losing_months": losing_months,
        "monthly": monthly_rows,
        "n_trades_per_month": {f"{y}-{m:02d}": c for (y, m), c in _n_trades_per_month(result.trades).items()},
    }


def _run_one(train1_df, mask, mult_series, symbol, interval) -> dict:
    t0 = time.time()
    
    # Control arm: stake_series=None (uniform 100).
    baseline_result = backtest_engine.run_backtest(
        train1_df, NAME, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=BASE_STAKE, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT, cooldown_candles=COOLDOWN,
        entry_regime_mask=mask, stake_series=None, **FIXED_PARAMS,
    )
    
    # Sized arm: stake_series = BASE_STAKE * mult.
    stake_series = BASE_STAKE * mult_series
    sized_result = backtest_engine.run_backtest(
        train1_df, NAME, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=BASE_STAKE, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT, cooldown_candles=COOLDOWN,
        entry_regime_mask=mask, stake_series=stake_series, **FIXED_PARAMS,
    )

    baseline_eval = _evaluate(baseline_result, symbol, interval)
    sized_eval = _evaluate(sized_result, symbol, interval)

    n_trades_baseline = baseline_eval["n_trades"]
    n_trades_sized = sized_eval["n_trades"]
    trade_count_invariant_ok = (n_trades_baseline == n_trades_sized) and (
        baseline_eval["n_trades_per_month"] == sized_eval["n_trades_per_month"]
    )
    if not trade_count_invariant_ok:
        raise SystemExit(
            f"STOP: trade-count invariant violated for {symbol}/{interval}: "
            f"baseline n_trades={n_trades_baseline} n_trades_per_month="
            f"{baseline_eval['n_trades_per_month']}, sized n_trades={n_trades_sized} "
            f"n_trades_per_month={sized_eval['n_trades_per_month']}"
        )

    # Per-trade multiplier actually applied (read from sized trades' stake column).
    sized_trades = sized_result.trades
    if len(sized_trades) > 0:
        applied_mult = (sized_trades["stake"] / BASE_STAKE).to_numpy()
        stake_cv = float(np.std(applied_mult) / np.mean(applied_mult)) if np.mean(applied_mult) != 0 else 0.0
        
        wins = sized_trades["net_pnl"] > 0
        mean_mult_winners = float(applied_mult[wins.to_numpy()].mean()) if wins.any() else None
        mean_mult_losers = float(applied_mult[(~wins).to_numpy()].mean()) if (~wins).any() else None
        mean_mult_gap = (
            round(mean_mult_winners - mean_mult_losers, 6)
            if mean_mult_winners is not None and mean_mult_losers is not None
            else None
        )
        
        # stake_cv > 0.05 genuineness check.
        stake_cv_ok = stake_cv > 0.05
    else:
        stake_cv, mean_mult_winners, mean_mult_losers, mean_mult_gap = 0.0, None, None, None
        stake_cv_ok = False

    return {
        "symbol": symbol,
        "interval": interval,
        "n_trades_baseline": n_trades_baseline,
        "n_trades_sized": n_trades_sized,
        "train1_net_pnl_baseline": baseline_eval["train1_net_pnl"],
        "train1_net_pnl_sized": sized_eval["train1_net_pnl"],
        "pooled_losing_month_floor_baseline": baseline_eval["pooled_losing_month_floor"],
        "pooled_losing_month_floor_sized": sized_eval["pooled_losing_month_floor"],
        "losing_months_baseline": baseline_eval["losing_months"],
        "losing_months_sized": sized_eval["losing_months"],
        "stake_cv": round(stake_cv, 6),
        "stake_cv_ok": stake_cv_ok,
        "mean_mult_winners": mean_mult_winners,
        "mean_mult_losers": mean_mult_losers,
        "mean_mult_gap": mean_mult_gap,
        "baseline_monthly": baseline_eval["monthly"],
        "sized_monthly": sized_eval["monthly"],
        "seconds": round(time.time() - t0, 2),
    }


def main():
    t_start = time.time()
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None

    assert NAME in strategy.STRATEGY_CATALOG, f"strategy {NAME!r} not in strategy.STRATEGY_CATALOG"

    os.makedirs(f"{OUT_DIR}/summary", exist_ok=True)
    os.makedirs(f"{OUT_DIR}/raw", exist_ok=True)

    rows = []
    checksums_used = {}
    
    for interval in INTERVALS:
        # Load all 5 symbols once per interval (needed for cross-symbol agreement).
        frames = {}
        for symbol in SYMBOLS:
            train1_df, manifest = load_train1(symbol, interval)
            frames[symbol] = train1_df
            checksums_used[f"{symbol}_{interval}"] = manifest.checksum_sha256

        # Index-equality precondition check (defensive, following f006_entry_cross_symbol pattern).
        ref_idx = pd.DatetimeIndex(frames["BTCUSDT"].index)
        for symbol in SYMBOLS:
            if not pd.DatetimeIndex(frames[symbol].index).equals(ref_idx):
                raise SystemExit(
                    f"STOP: index-equality precondition violated for {symbol}/{interval} vs BTCUSDT"
                )

        for symbol in SYMBOLS:
            own_df = frames[symbol]
            others_dfs = {s: frames[s] for s in SYMBOLS if s != symbol}
            
            mult_series = compute_agreement_multiplier_series(own_df, others_dfs, interval, symbol)
            sig = entry_masks.strategy_signal_series(own_df, NAME, interval=interval, now=NOW)
            mask = entry_masks.one_shot_entry_mask(sig)
            
            row = _run_one(own_df, mask, mult_series, symbol, interval)
            rows.append(row)
            
            with open(f"{OUT_DIR}/raw/{symbol}_{interval}.json", "w") as f:
                json.dump(row, f, indent=2, default=str)
        
        print(f"done interval={interval} ({len(rows)} series so far, {time.time() - t_start:.1f}s elapsed)")

    summary_rows = [
        {k: v for k, v in r.items() if k not in ("baseline_monthly", "sized_monthly", "losing_months_baseline", "losing_months_sized")}
        for r in rows
    ]
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(f"{OUT_DIR}/summary/results.csv", index=False)

    # Aggregate metrics for the Result section.
    mean_train1_net_pnl_baseline = summary_df["train1_net_pnl_baseline"].mean()
    mean_train1_net_pnl_sized = summary_df["train1_net_pnl_sized"].mean()
    
    # Pooled entry cohort: sum all trades across all series.
    pooled_n_trades_baseline = int(summary_df["n_trades_baseline"].sum())
    pooled_net_pnl_baseline = summary_df["train1_net_pnl_baseline"].sum()
    pooled_n_trades_sized = int(summary_df["n_trades_sized"].sum())
    pooled_net_pnl_sized = summary_df["train1_net_pnl_sized"].sum()
    
    # Pooled losing-month floor: count unique losing months across all series.
    all_losing_baseline = set()
    all_losing_sized = set()
    for r in rows:
        all_losing_baseline.update(r["losing_months_baseline"])
        all_losing_sized.update(r["losing_months_sized"])
    pooled_losing_floor_baseline = len(all_losing_baseline)
    pooled_losing_floor_sized = len(all_losing_sized)
    
    # Mean mult gap across series.
    gaps = [r["mean_mult_gap"] for r in rows if r["mean_mult_gap"] is not None]
    mean_gap = round(np.mean(gaps), 6) if gaps else None
    
    # Falsification checks.
    falsified = []
    if mean_train1_net_pnl_sized <= mean_train1_net_pnl_baseline:
        falsified.append("(a) mean train1_net_pnl_sized <= baseline")
    if pooled_losing_floor_sized >= pooled_losing_floor_baseline:
        falsified.append(f"(b) pooled losing-month floor did not improve ({pooled_losing_floor_sized} >= {pooled_losing_floor_baseline})")
    if mean_gap is not None and mean_gap <= 0:
        falsified.append(f"(c) mean(mult|winner) - mean(mult|loser) <= 0 ({mean_gap})")
    if not all(r["stake_cv_ok"] for r in rows if r["n_trades_sized"] > 0):
        falsified.append("(e) stake_cv <= 0.05 on some series (degenerate uniform)")

    manifest_out = {
        "script": "scripts/f006_bb_20_25_xsym_agree_sizing.py",
        "git_commit": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "n_series": len(rows),
        "strategy": NAME,
        "checksums_used": checksums_used,
        "params": {
            "activate_pct": ACTIVATE_PCT, "trail_pct": TRAIL_PCT, "max_sl_pct": MAX_SL_PCT,
            "cooldown_candles": COOLDOWN, "mask_mode": "one_shot",
            "initial_equity": INITIAL_EQUITY, "base_stake": BASE_STAKE,
            "mult_lo": MULT_LO, "mult_hi": MULT_HI,
            "mult_formula": "clip(0.5 + 0.375 * n_agree, 0.5, 2.0)",
            **FIXED_PARAMS,
        },
        "results": {
            "mean_train1_net_pnl_baseline": round(mean_train1_net_pnl_baseline, 6),
            "mean_train1_net_pnl_sized": round(mean_train1_net_pnl_sized, 6),
            "pooled_n_trades_baseline": pooled_n_trades_baseline,
            "pooled_net_pnl_baseline": round(pooled_net_pnl_baseline, 6),
            "pooled_n_trades_sized": pooled_n_trades_sized,
            "pooled_net_pnl_sized": round(pooled_net_pnl_sized, 6),
            "pooled_losing_month_floor_baseline": pooled_losing_floor_baseline,
            "pooled_losing_month_floor_sized": pooled_losing_floor_sized,
            "mean_mult_gap": mean_gap,
            "number_of_trials": 1,
        },
        "falsification": {
            "falsified": len(falsified) > 0,
            "conditions_violated": falsified,
        },
        "seconds": round(time.time() - t_start, 2),
    }
    with open(f"{OUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(manifest_out, f, indent=2)

    with open(f"{OUT_DIR}/summary/run.log", "w") as f:
        f.write(f"F006 H-BB-20-25-XSYM-AGREE-SIZING-01\n")
        f.write(f"Run started: {manifest_out['run_started_utc']}\n")
        f.write(f"Commit: {commit_sha}\n\n")
        f.write(f"Control arm (stake_series=None, uniform 100):\n")
        f.write(f"  mean train1_net_pnl: {mean_train1_net_pnl_baseline:.2f} (across {len(rows)} series)\n")
        f.write(f"  pooled entry cohort: n={pooled_n_trades_baseline}, net={pooled_net_pnl_baseline:.2f}\n")
        f.write(f"  pooled losing-month floor: {pooled_losing_floor_baseline}/12\n\n")
        f.write(f"Sized arm (mult=clip(0.5+0.375*n_agree,0.5,2.0)):\n")
        f.write(f"  mean train1_net_pnl: {mean_train1_net_pnl_sized:.2f}\n")
        f.write(f"  pooled entry cohort: n={pooled_n_trades_sized}, net={pooled_net_pnl_sized:.2f}\n")
        f.write(f"  pooled losing-month floor: {pooled_losing_floor_sized}/12\n")
        f.write(f"  mean(mult|winner) - mean(mult|loser): {mean_gap}\n\n")
        f.write(f"Falsification status: {manifest_out['falsification']['falsified']}\n")
        if falsified:
            f.write(f"Conditions violated:\n")
            for cond in falsified:
                f.write(f"  - {cond}\n")
        f.write(f"\nElapsed: {time.time() - t_start:.1f}s\n")

    print(f"\n{len(rows)} series in {time.time() - t_start:.1f}s -> {OUT_DIR}/summary/")
    print(f"Control: mean train1_net_pnl={mean_train1_net_pnl_baseline:.2f}, pooled losing floor={pooled_losing_floor_baseline}/12")
    print(f"Sized: mean train1_net_pnl={mean_train1_net_pnl_sized:.2f}, pooled losing floor={pooled_losing_floor_sized}/12")
    print(f"mean(mult|winner) - mean(mult|loser) = {mean_gap}")
    print(f"Falsified: {manifest_out['falsification']['falsified']} {falsified if falsified else ''}")


if __name__ == "__main__":
    main()
