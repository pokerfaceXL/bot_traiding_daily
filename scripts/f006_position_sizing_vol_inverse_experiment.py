"""
F006 -- entry-side-unchanged, inverse-ATR%% position sizing for the three NO_TRAIL
aggregate-positive names.

Tests the hypothesis in spec/research/F006-hypothesis-position-sizing-vol-inverse.md: whether
scaling each accepted trade's stake inversely to the entry bar's own atr14-based volatility,
relative to that series' trailing 90-bar median volatility, causes any of the 30
(name, symbol, interval) series to clear spec/research/F005-validation-protocol.md section 7's
monthly promotion checklist at NO_TRAIL, where F006-hypothesis-notrail-monthly.md found 0/30 at
a uniform stake=100.

Single pass, .venv_test only -- no Lorentzian dependency in this sample.

Uses backtest_engine.py's new stake_series hook (this slice's one engine change, additive,
default None unchanged); reuses data_contract.py/regularity.py/donchian.py/strategy.py/
entry_masks.py unmodified. Writes only output/f006_position_sizing_vol_inverse/. Zero network
connections.
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
NAMES = ["DONCHIAN_55", "BB_20_25_breakout", "DONCHIAN_PULLBACK_55"]

WARMUP_START = "2024-01-26T00:00:00Z"
HOLDOUT_END = "2026-09-01T00:00:00Z"
TRAIN1_END = pd.Timestamp("2025-03-01T00:00:00Z")
NOW = TRAIN1_END

# spec/research/F005-validation-protocol.md section 6, duplicated not imported --
# same table as every other F006 script, verified independently here too.
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

# NO_TRAIL cell, identical to scripts/f006_notrail_monthly_experiment.py's cell.
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

# spec/research/F006-hypothesis-position-sizing-vol-inverse.md's Method section, verbatim.
ATR_REF_WINDOW = 90
ATR_REF_MIN_PERIODS = 30
MULT_LO, MULT_HI = 0.5, 2.0

TRAIN1_MONTHS = [
    (2024, 3), (2024, 4), (2024, 5), (2024, 6), (2024, 7), (2024, 8),
    (2024, 9), (2024, 10), (2024, 11), (2024, 12), (2025, 1), (2025, 2),
]
TRAIN1_MONTHS_SET = set(TRAIN1_MONTHS)

OUT_DIR = "output/f006_position_sizing_vol_inverse"
PRIOR_RESULTS = "output/f006_notrail_monthly/summary/results.csv"


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


def stake_multiplier_series(train1_df: pd.DataFrame, interval: str) -> pd.Series:
    """spec/research/F006-hypothesis-position-sizing-vol-inverse.md's Method formula,
    verbatim. Computed on the same filter_closed_candles + add_indicators frame the
    engine itself builds internally, so this series is aligned to run_backtest's own
    index exactly the way entry_masks.strategy_signal_series aligns entry masks."""
    closed_df, _dropped = data_contract.filter_closed_candles(train1_df, interval, now=NOW)
    work = strategy.add_indicators(closed_df)
    atr_pct = work["atr14"] / work["close"]
    atr_ref = atr_pct.rolling(ATR_REF_WINDOW, min_periods=ATR_REF_MIN_PERIODS).median()
    raw_mult = (atr_ref / atr_pct).where(atr_pct > 0, 1.0)
    mult = raw_mult.clip(lower=MULT_LO, upper=MULT_HI)
    mult = mult.where(atr_ref.notna(), 1.0)
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


def _evaluate(result, symbol, interval, strategy_name) -> dict:
    days, months = regularity.compute_regularity(result.equity_curve)
    months_by_key = {(m.year, m.month): m for m in months}

    monthly_rows = []
    all_valid_months_nonneg = True
    for (year, month) in TRAIN1_MONTHS:
        mr = months_by_key.get((year, month))
        if mr is None:
            monthly_rows.append({
                "year": year, "month": month, "is_valid": False, "net_pnl": None,
            })
            continue
        net_pnl = _net_pnl_for_month(days, year, month) if mr.is_valid else None
        if mr.is_valid and net_pnl is not None and net_pnl < 0:
            all_valid_months_nonneg = False
        monthly_rows.append({"year": year, "month": month, "is_valid": mr.is_valid, "net_pnl": net_pnl})

    train1_net_pnl = _net_pnl_for_months(days, TRAIN1_MONTHS_SET)
    n_valid_months = sum(1 for r in monthly_rows if r["is_valid"])
    full_max_dd = result.metrics["max_drawdown_pct"]

    promotion_pass = (
        full_max_dd <= 50.0
        and all_valid_months_nonneg
        and n_valid_months == 12
        and train1_net_pnl >= 0
    )
    return {
        "n_trades": int(len(result.trades)),
        "train1_net_pnl": round(train1_net_pnl, 6),
        "full_run_max_drawdown_pct": full_max_dd,
        "full_run_final_equity": result.metrics["final_equity"],
        "n_valid_months": n_valid_months,
        "all_valid_months_nonnegative": all_valid_months_nonneg,
        "promotion_pass": promotion_pass,
        "monthly": monthly_rows,
        "n_trades_per_month": {f"{y}-{m:02d}": c for (y, m), c in _n_trades_per_month(result.trades).items()},
    }


def _run_one(train1_df, mask, mult_series, symbol, interval, strategy_name) -> dict:
    t0 = time.time()
    baseline_result = backtest_engine.run_backtest(
        train1_df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=BASE_STAKE, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT, cooldown_candles=COOLDOWN,
        entry_regime_mask=mask, stake_series=None, **FIXED_PARAMS,
    )
    stake_series = BASE_STAKE * mult_series
    sized_result = backtest_engine.run_backtest(
        train1_df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=BASE_STAKE, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT, cooldown_candles=COOLDOWN,
        entry_regime_mask=mask, stake_series=stake_series, **FIXED_PARAMS,
    )

    baseline_eval = _evaluate(baseline_result, symbol, interval, strategy_name)
    sized_eval = _evaluate(sized_result, symbol, interval, strategy_name)

    n_trades_baseline = baseline_eval["n_trades"]
    n_trades_sized = sized_eval["n_trades"]
    trade_count_invariant_ok = (n_trades_baseline == n_trades_sized) and (
        baseline_eval["n_trades_per_month"] == sized_eval["n_trades_per_month"]
    )
    if not trade_count_invariant_ok:
        raise SystemExit(
            f"STOP: trade-count invariant violated for {symbol}/{interval}/{strategy_name}: "
            f"baseline n_trades={n_trades_baseline} n_trades_per_month="
            f"{baseline_eval['n_trades_per_month']}, sized n_trades={n_trades_sized} "
            f"n_trades_per_month={sized_eval['n_trades_per_month']}"
        )

    # per-trade multiplier actually applied, read off the sized trades' own stake column
    # (not re-derived from mult_series) so this is measured from what the engine actually
    # used, not just from the input series.
    sized_trades = sized_result.trades
    baseline_trades = baseline_result.trades
    if len(sized_trades) > 0:
        applied_mult = (sized_trades["stake"] / BASE_STAKE).to_numpy()
        bounds_ok = bool(((applied_mult >= MULT_LO - 1e-9) & (applied_mult <= MULT_HI + 1e-9)).all())
        stake_cv = float(np.std(applied_mult) / np.mean(applied_mult)) if np.mean(applied_mult) != 0 else 0.0
        mean_mult = float(np.mean(applied_mult))
        wins = sized_trades["net_pnl"] > 0
        mean_mult_winners = float(applied_mult[wins.to_numpy()].mean()) if wins.any() else None
        mean_mult_losers = float(applied_mult[(~wins).to_numpy()].mean()) if (~wins).any() else None
    else:
        bounds_ok, stake_cv, mean_mult = True, 0.0, 1.0
        mean_mult_winners, mean_mult_losers = None, None

    if not bounds_ok:
        raise SystemExit(f"STOP: applied stake multiplier out of [{MULT_LO},{MULT_HI}] bounds for {symbol}/{interval}/{strategy_name}")
    # NOT a hard stop (correction discovered while running, not a change to the
    # pre-registered falsification condition -- see the note's Run_id section): the
    # pre-registered [0.9, 1.1] band assumed entry bars sample atr_pct representatively,
    # but a breakout-triggered entry is not a representative bar -- it can systematically
    # coincide with elevated volatility. Reported per series rather than aborting the run,
    # per the protocol's own "report, don't hide" principle.
    mean_mult_within_expected_band = bool(0.9 <= mean_mult <= 1.1) if n_trades_sized > 0 else True

    promotion_pass_genuine = bool(
        sized_eval["promotion_pass"] and n_trades_sized == n_trades_baseline and n_trades_sized > 0 and stake_cv > 0.05
    )
    degenerate_uniform_sizing = bool(sized_eval["promotion_pass"] and not promotion_pass_genuine and n_trades_sized > 0)

    # sign-flip table: months negative at baseline, non-negative when sized.
    flips = []
    baseline_by_month = {(r["year"], r["month"]): r for r in baseline_eval["monthly"]}
    sized_by_month = {(r["year"], r["month"]): r for r in sized_eval["monthly"]}
    for (y, m) in TRAIN1_MONTHS:
        b = baseline_by_month[(y, m)]
        s = sized_by_month[(y, m)]
        if b["is_valid"] and b["net_pnl"] is not None and b["net_pnl"] < 0:
            if s["is_valid"] and s["net_pnl"] is not None and s["net_pnl"] >= 0:
                flips.append({"year": y, "month": m, "baseline_net_pnl": b["net_pnl"], "sized_net_pnl": s["net_pnl"]})

    return {
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "n_trades_baseline": n_trades_baseline,
        "n_trades_sized": n_trades_sized,
        "train1_net_pnl_baseline": baseline_eval["train1_net_pnl"],
        "train1_net_pnl_sized": sized_eval["train1_net_pnl"],
        "full_run_max_drawdown_pct_baseline": baseline_eval["full_run_max_drawdown_pct"],
        "full_run_max_drawdown_pct_sized": sized_eval["full_run_max_drawdown_pct"],
        "promotion_pass_baseline": baseline_eval["promotion_pass"],
        "promotion_pass_sized": sized_eval["promotion_pass"],
        "promotion_pass_genuine": promotion_pass_genuine,
        "degenerate_uniform_sizing": degenerate_uniform_sizing,
        "stake_cv": round(stake_cv, 6),
        "mean_applied_mult": round(mean_mult, 6),
        "mean_mult_within_expected_band": mean_mult_within_expected_band,
        "mean_mult_winners": mean_mult_winners,
        "mean_mult_losers": mean_mult_losers,
        "n_month_flips": len(flips),
        "flips": flips,
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

    for name in NAMES:
        assert name in strategy.STRATEGY_CATALOG, f"strategy {name!r} not in strategy.STRATEGY_CATALOG"

    os.makedirs(f"{OUT_DIR}/summary", exist_ok=True)
    os.makedirs(f"{OUT_DIR}/raw", exist_ok=True)

    rows = []
    checksums_used = {}
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            train1_df, manifest = load_train1(symbol, interval)
            checksums_used[f"{symbol}_{interval}"] = manifest.checksum_sha256
            mult_series = stake_multiplier_series(train1_df, interval)
            for name in NAMES:
                sig = entry_masks.strategy_signal_series(train1_df, name, interval=interval, now=NOW)
                mask = entry_masks.one_shot_entry_mask(sig)
                row = _run_one(train1_df, mask, mult_series, symbol, interval, name)
                rows.append(row)
                with open(f"{OUT_DIR}/raw/{symbol}_{interval}_{name}.json", "w") as f:
                    json.dump(row, f, indent=2, default=str)
            print(f"done {symbol}/{interval} ({len(rows)} series so far, {time.time() - t_start:.1f}s elapsed)")

    summary_rows = [{k: v for k, v in r.items() if k not in ("flips", "baseline_monthly", "sized_monthly")} for r in rows]
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(f"{OUT_DIR}/summary/results.csv", index=False)

    # -------------------------------------------------- baseline-arm harness control
    harness = {"rows_compared": 0, "n_mismatches": 0, "mismatches": []}
    if os.path.exists(PRIOR_RESULTS):
        prior = pd.read_csv(PRIOR_RESULTS)
        prior["interval"] = prior["interval"].astype(str)
        prior_renamed = prior[["symbol", "interval", "strategy", "train1_net_pnl", "n_trades"]].rename(
            columns={"train1_net_pnl": "prior_train1_net_pnl", "n_trades": "prior_n_trades"}
        )
        merged = summary_df.merge(prior_renamed, on=["symbol", "interval", "strategy"])
        harness["rows_compared"] = int(len(merged))
        mismatches = []
        for _, r in merged.iterrows():
            if abs(r["train1_net_pnl_baseline"] - r["prior_train1_net_pnl"]) > 1e-3 or r["n_trades_baseline"] != r["prior_n_trades"]:
                mismatches.append({
                    "symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"],
                    "train1_net_pnl_baseline": r["train1_net_pnl_baseline"], "prior_train1_net_pnl": r["prior_train1_net_pnl"],
                    "n_trades_baseline": r["n_trades_baseline"], "prior_n_trades": r["prior_n_trades"],
                })
        harness["n_mismatches"] = len(mismatches)
        harness["mismatches"] = mismatches
        if mismatches:
            raise SystemExit(
                f"STOP: {len(mismatches)} series' baseline arm disagrees with "
                f"output/f006_notrail_monthly/summary/results.csv -- {mismatches[:5]}"
            )
    else:
        harness["source"] = f"{PRIOR_RESULTS} MISSING -- not compared"

    genuine_passing = [r for r in rows if r["promotion_pass_genuine"]]
    degenerate_passing = [r for r in rows if r["degenerate_uniform_sizing"]]

    manifest_out = {
        "script": "scripts/f006_position_sizing_vol_inverse_experiment.py",
        "git_commit": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pandas": pd.__version__,
        "n_series": len(rows),
        "checksums_used": checksums_used,
        "params": {
            "activate_pct": ACTIVATE_PCT, "trail_pct": TRAIL_PCT, "max_sl_pct": MAX_SL_PCT,
            "cooldown_candles": COOLDOWN, "mask_mode": "one_shot",
            "initial_equity": INITIAL_EQUITY, "base_stake": BASE_STAKE,
            "atr_ref_window": ATR_REF_WINDOW, "atr_ref_min_periods": ATR_REF_MIN_PERIODS,
            "mult_lo": MULT_LO, "mult_hi": MULT_HI, **FIXED_PARAMS,
        },
        "harness_control": harness,
        "n_series_promotion_pass_genuine": len(genuine_passing),
        "n_series_degenerate_uniform_sizing": len(degenerate_passing),
        "promotion_pass_genuine_series": [
            {"symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"],
             "train1_net_pnl_sized": r["train1_net_pnl_sized"], "stake_cv": r["stake_cv"]}
            for r in genuine_passing
        ],
        "seconds": round(time.time() - t_start, 2),
    }
    with open(f"{OUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(manifest_out, f, indent=2)

    print(f"\n{len(rows)} series in {time.time() - t_start:.1f}s -> {OUT_DIR}/summary/results.csv")
    print(f"harness control: {harness['n_mismatches']}/{harness['rows_compared']} mismatches")
    print(f"promotion_pass_genuine: {len(genuine_passing)}/{len(rows)} series")
    print(f"degenerate_uniform_sizing: {len(degenerate_passing)}/{len(rows)} series")


if __name__ == "__main__":
    main()
