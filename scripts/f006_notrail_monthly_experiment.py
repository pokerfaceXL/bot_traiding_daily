"""
F006 -- Train-1 monthly PnL breakdown for the three NO_TRAIL aggregate-positive names.

Tests the hypothesis in spec/research/F006-hypothesis-notrail-monthly.md: whether any of
the 30 (name, symbol, interval) series -- DONCHIAN_55, BB_20_25_breakout,
DONCHIAN_PULLBACK_55 x 5 symbols x 2 intervals -- clears the frozen protocol's monthly
promotion checklist (spec/research/F005-validation-protocol.md section 7) at the NO_TRAIL
control (activate_pct=10.0, trail never arms) on Train 1.

Single pass, .venv_test only -- no Lorentzian dependency in this sample.

Reuses backtest_engine.py/entry_masks.py/regularity.py/data_contract.py unmodified.
Writes only output/f006_notrail_monthly/. Zero network connections.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

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

# NO_TRAIL cell, identical to scripts/f006_trailing_boundary_experiment.py's cell.
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
STAKE = 100.0

# spec/research/F005-validation-protocol.md section 3.2's train_1 window, duplicated from
# scripts/f005_run_baseline.py's _month_range(2024, 3, 2025, 2) -- 12 full calendar months.
TRAIN1_MONTHS = [
    (2024, 3), (2024, 4), (2024, 5), (2024, 6), (2024, 7), (2024, 8),
    (2024, 9), (2024, 10), (2024, 11), (2024, 12), (2025, 1), (2025, 2),
]
TRAIN1_MONTHS_SET = set(TRAIN1_MONTHS)
WARMUP_MONTHS_SET = {(2024, 1), (2024, 2)}

OUT_DIR = "output/f006_notrail_monthly"
PRIOR_RESULTS = "output/f006_trailing_boundary/summary/results.csv"


def load_train1(symbol: str, interval: str) -> pd.DataFrame:
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


def _run_one(train1_df, mask, symbol, interval, strategy_name) -> dict:
    t0 = time.time()
    result = backtest_engine.run_backtest(
        train1_df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT,
        cooldown_candles=COOLDOWN,
        entry_regime_mask=mask,
        **FIXED_PARAMS,
    )
    days, months = regularity.compute_regularity(result.equity_curve)
    months_by_key = {(m.year, m.month): m for m in months}

    monthly_rows = []
    all_valid_months_positive = True
    for (year, month) in TRAIN1_MONTHS:
        mr = months_by_key.get((year, month))
        if mr is None:
            # No day in this series' curve falls in this calendar month at all
            # (should not happen given the Train-1 load slice, but treated as
            # not-evaluated rather than silently skipped).
            monthly_rows.append({
                "year": year, "month": month, "is_valid": False, "is_partial": None,
                "net_pnl": None, "positive_day_pct": None, "deviation_pct": None,
                "target_met": None,
            })
            continue
        net_pnl = _net_pnl_for_month(days, year, month) if mr.is_valid else None
        if mr.is_valid and net_pnl is not None and net_pnl < 0:
            all_valid_months_positive = False
        monthly_rows.append({
            "year": year, "month": month, "is_valid": mr.is_valid, "is_partial": mr.is_partial,
            "net_pnl": net_pnl, "positive_day_pct": mr.positive_day_pct,
            "deviation_pct": mr.deviation_pct, "target_met": mr.target_met,
        })

    train1_net_pnl = _net_pnl_for_months(days, TRAIN1_MONTHS_SET)
    warmup_net_pnl = _net_pnl_for_months(days, WARMUP_MONTHS_SET)
    full_max_dd = result.metrics["max_drawdown_pct"]
    n_valid_months = sum(1 for r in monthly_rows if r["is_valid"])

    promotion_pass = (
        full_max_dd <= 50.0
        and all_valid_months_positive
        and n_valid_months == 12
        and train1_net_pnl >= 0
    )

    return {
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "n_trades": int(len(result.trades)),
        "train1_net_pnl": round(train1_net_pnl, 6),
        "warmup_net_pnl": round(warmup_net_pnl, 6),
        "full_run_max_drawdown_pct": full_max_dd,
        "full_run_final_equity": result.metrics["final_equity"],
        "n_valid_months": n_valid_months,
        "all_valid_months_nonnegative": all_valid_months_positive,
        "promotion_pass": promotion_pass,
        "monthly": monthly_rows,
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
            for name in NAMES:
                sig = entry_masks.strategy_signal_series(train1_df, name, interval=interval, now=NOW)
                mask = entry_masks.one_shot_entry_mask(sig)
                row = _run_one(train1_df, mask, symbol, interval, name)
                rows.append(row)
                with open(f"{OUT_DIR}/raw/{symbol}_{interval}_{name}.json", "w") as f:
                    json.dump(row, f, indent=2, default=str)
            print(f"done {symbol}/{interval} ({len(rows)} series so far, {time.time() - t_start:.1f}s elapsed)")

    summary_rows = [{k: v for k, v in r.items() if k != "monthly"} for r in rows]
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(f"{OUT_DIR}/summary/results.csv", index=False)

    # -------------------------------------------------- harness control
    harness = {"rows_compared": 0, "n_mismatches": 0, "mismatches": []}
    if os.path.exists(PRIOR_RESULTS):
        prior = pd.read_csv(PRIOR_RESULTS)
        prior["interval"] = prior["interval"].astype(str)
        prior_no_trail = prior[(prior["no_trail"] == True) & (prior["mask_mode"] == "one_shot")]  # noqa: E712
        merged = summary_df.merge(
            prior_no_trail[["symbol", "interval", "strategy", "net_pnl", "n_trades"]],
            on=["symbol", "interval", "strategy"], suffixes=("", "_prior"),
        )
        harness["rows_compared"] = int(len(merged))
        mismatches = []
        for _, r in merged.iterrows():
            # The prior slice's stored net_pnl is the FULL loaded slice's total
            # (warm-up buffer + Train 1), since that script never sliced by
            # calendar month; this slice's train1_net_pnl deliberately excludes
            # the 2024-01/02 warm-up buffer (never evaluated by the protocol), so
            # the invariant checked here is train1 + warmup == prior's full total.
            reconstructed = r["train1_net_pnl"] + r["warmup_net_pnl"]
            if abs(reconstructed - r["net_pnl"]) > 1e-6 or r["n_trades"] != r["n_trades_prior"]:
                mismatches.append({
                    "symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"],
                    "train1_net_pnl": r["train1_net_pnl"], "warmup_net_pnl": r["warmup_net_pnl"],
                    "reconstructed_total": reconstructed, "prior_net_pnl": r["net_pnl"],
                    "n_trades": r["n_trades"], "prior_n_trades": r["n_trades_prior"],
                })
        harness["n_mismatches"] = len(mismatches)
        harness["mismatches"] = mismatches
        if mismatches:
            raise SystemExit(
                f"STOP: {len(mismatches)} series disagree with "
                f"output/f006_trailing_boundary/summary/results.csv's stored NO_TRAIL rows -- "
                f"{mismatches[:5]}"
            )
    else:
        harness["source"] = f"{PRIOR_RESULTS} MISSING -- not compared"

    passing = [r for r in rows if r["promotion_pass"]]

    manifest_out = {
        "script": "scripts/f006_notrail_monthly_experiment.py",
        "git_commit": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pandas": pd.__version__,
        "n_series": len(rows),
        "checksums_used": checksums_used,
        "params": {
            "activate_pct": ACTIVATE_PCT, "trail_pct": TRAIL_PCT, "max_sl_pct": MAX_SL_PCT,
            "cooldown_candles": COOLDOWN, "mask_mode": "one_shot",
            "initial_equity": INITIAL_EQUITY, "stake": STAKE, **FIXED_PARAMS,
        },
        "harness_control": harness,
        "n_series_promotion_pass": len(passing),
        "promotion_pass_series": [
            {"symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"],
             "train1_net_pnl": r["train1_net_pnl"]}
            for r in passing
        ],
        "seconds": round(time.time() - t_start, 2),
    }
    with open(f"{OUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(manifest_out, f, indent=2)

    print(f"\n{len(rows)} series in {time.time() - t_start:.1f}s -> {OUT_DIR}/summary/results.csv")
    print(f"harness control: {harness['n_mismatches']}/{harness['rows_compared']} mismatches")
    print(f"promotion_pass: {len(passing)}/{len(rows)} series")


if __name__ == "__main__":
    main()
