"""
F006 -- entry-side width-expansion gate for the three NO_TRAIL aggregate-positive names.

Tests the hypothesis in spec/research/F006-hypothesis-entry-width-expansion.md: whether gating
new entries of DONCHIAN_55, BB_20_25_breakout, DONCHIAN_PULLBACK_55 on their own channel/band
width being above its own trailing 30-bar mean (the mechanism of strategy.py's existing
sig_bb_breakout_squeeze, applied here as a standalone entry_regime_mask rather than baked into
signal generation) causes any of the 30 (name, symbol, interval) series to clear
spec/research/F005-validation-protocol.md section 7's monthly promotion checklist at NO_TRAIL,
where F006-hypothesis-notrail-monthly.md found 0/30 without the gate.

Single pass, .venv_test only -- no Lorentzian dependency in this sample.

Reuses backtest_engine.py/entry_masks.py/regularity.py/data_contract.py/donchian.py/strategy.py
unmodified. Writes only output/f006_entry_width_expansion/. Zero network connections.
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
import donchian  # noqa: E402
import entry_masks  # noqa: E402
import regularity  # noqa: E402
import strategy  # noqa: E402

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]
NAMES = ["DONCHIAN_55", "BB_20_25_breakout", "DONCHIAN_PULLBACK_55"]
DONCHIAN_N = 55
WIDTH_LOOKBACK = 30  # sig_bb_breakout_squeeze's own lookback, reused unchanged

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

TRAIN1_MONTHS = [
    (2024, 3), (2024, 4), (2024, 5), (2024, 6), (2024, 7), (2024, 8),
    (2024, 9), (2024, 10), (2024, 11), (2024, 12), (2025, 1), (2025, 2),
]
TRAIN1_MONTHS_SET = set(TRAIN1_MONTHS)

OUT_DIR = "output/f006_entry_width_expansion"
PRIOR_RESULTS = "output/f006_notrail_monthly/summary/results.csv"


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
    return train1_df


def width_series(df: pd.DataFrame, interval: str, name: str) -> pd.Series:
    """Channel/band width on the engine's own frame (filter_closed_candles applied first)."""
    closed_df, _dropped = data_contract.filter_closed_candles(df, interval, now=NOW)
    if name == "BB_20_25_breakout":
        work = strategy.add_indicators(closed_df.copy())
        return work["bb_20_2.5_width"]
    ch = donchian.donchian_channel(closed_df, DONCHIAN_N)
    return (ch["upper"] - ch["lower"]) / ch["mid"]


def width_gate(width: pd.Series) -> pd.Series:
    return (width > width.rolling(WIDTH_LOOKBACK).mean()).fillna(False)


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


def _run_and_score(train1_df, mask, symbol, interval, strategy_name) -> dict:
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
        monthly_rows.append({
            "year": year, "month": month, "is_valid": mr.is_valid, "net_pnl": net_pnl,
        })

    n_neg_months = sum(
        1 for r in monthly_rows if r["is_valid"] and r["net_pnl"] is not None and r["net_pnl"] < 0
    )
    train1_net_pnl = _net_pnl_for_months(days, TRAIN1_MONTHS_SET)
    n_valid_months = sum(1 for r in monthly_rows if r["is_valid"])
    full_max_dd = result.metrics["max_drawdown_pct"]
    win_rate = result.metrics.get("win_rate")

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
        "win_rate_pct": win_rate,
        "n_valid_months": n_valid_months,
        "n_neg_months": n_neg_months,
        "all_valid_months_nonnegative": all_valid_months_nonneg,
        "promotion_pass": promotion_pass,
        "monthly": monthly_rows,
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
    subset_violations = []
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            train1_df = load_train1(symbol, interval)
            _fd, _man = data_contract.load_dataset("data_cache", symbol, interval, WARMUP_START, HOLDOUT_END)
            checksums_used[f"{symbol}_{interval}"] = _man.checksum_sha256
            for name in NAMES:
                sig = entry_masks.strategy_signal_series(train1_df, name, interval=interval, now=NOW)
                one_shot = entry_masks.one_shot_entry_mask(sig)

                w = width_series(train1_df, interval, name)
                gate = width_gate(w).reindex(one_shot.index).fillna(False)
                filtered_mask = one_shot & gate

                n_calls = int(one_shot.sum())
                n_calls_gated_out = int((one_shot & ~gate).sum())

                unfiltered_row = _run_and_score(train1_df, one_shot, symbol, interval, name)
                filtered_row = _run_and_score(train1_df, filtered_mask, symbol, interval, name)

                if filtered_row["n_trades"] > unfiltered_row["n_trades"]:
                    subset_violations.append((symbol, interval, name))

                row = {
                    "symbol": symbol, "interval": interval, "strategy": name,
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
                }
                rows.append(row)
                with open(f"{OUT_DIR}/raw/{symbol}_{interval}_{name}.json", "w") as f:
                    json.dump(
                        {"summary": row, "monthly_filtered": filtered_row["monthly"],
                         "monthly_unfiltered": unfiltered_row["monthly"]},
                        f, indent=2, default=str,
                    )
            print(f"done {symbol}/{interval} ({len(rows)} series so far, {time.time() - t_start:.1f}s elapsed)")

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(f"{OUT_DIR}/summary/results.csv", index=False)

    if subset_violations:
        raise SystemExit(f"STOP: subset invariant violated for {subset_violations}")

    # -------------------------------------------------- harness control vs. notrail-monthly
    harness = {"rows_compared": 0, "n_mismatches": 0, "mismatches": []}
    if os.path.exists(PRIOR_RESULTS):
        prior = pd.read_csv(PRIOR_RESULTS)
        prior["interval"] = prior["interval"].astype(str)
        merged = summary_df.merge(
            prior[["symbol", "interval", "strategy", "train1_net_pnl", "n_trades"]],
            on=["symbol", "interval", "strategy"], suffixes=("", "_prior"),
        )
        harness["rows_compared"] = int(len(merged))
        mismatches = []
        for _, r in merged.iterrows():
            if (abs(r["train1_net_pnl_unfiltered"] - r["train1_net_pnl"]) > 1e-3
                    or r["n_trades_unfiltered"] != r["n_trades"]):
                mismatches.append({
                    "symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"],
                    "unfiltered_net_pnl": r["train1_net_pnl_unfiltered"],
                    "prior_net_pnl": r["train1_net_pnl"],
                    "unfiltered_n_trades": r["n_trades_unfiltered"],
                    "prior_n_trades": r["n_trades"],
                })
        harness["n_mismatches"] = len(mismatches)
        harness["mismatches"] = mismatches
        if mismatches:
            raise SystemExit(
                f"STOP: {len(mismatches)} series' unfiltered (gate=all-True) rerun disagrees "
                f"with output/f006_notrail_monthly/summary/results.csv -- {mismatches[:5]}"
            )
    else:
        harness["source"] = f"{PRIOR_RESULTS} MISSING -- not compared"

    passing = [r for r in rows if r["promotion_pass_filtered"]]
    passing_unfiltered = [r for r in rows if r["promotion_pass_unfiltered"]]

    pooled_win_filtered = summary_df["win_rate_filtered"].mean()
    pooled_win_unfiltered = summary_df["win_rate_unfiltered"].mean()
    mean_neg_months_filtered = summary_df["n_neg_months_filtered"].mean()
    mean_neg_months_unfiltered = summary_df["n_neg_months_unfiltered"].mean()

    manifest_out = {
        "script": "scripts/f006_entry_width_expansion_experiment.py",
        "git_commit": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pandas": pd.__version__,
        "n_series": len(rows),
        "checksums_used": checksums_used,
        "params": {
            "activate_pct": ACTIVATE_PCT, "trail_pct": TRAIL_PCT, "max_sl_pct": MAX_SL_PCT,
            "cooldown_candles": COOLDOWN, "mask_mode": "one_shot + width_expansion_gate",
            "width_lookback": WIDTH_LOOKBACK,
            "initial_equity": INITIAL_EQUITY, "stake": STAKE, **FIXED_PARAMS,
        },
        "harness_control": harness,
        "subset_invariant_violations": subset_violations,
        "n_series_promotion_pass_filtered": len(passing),
        "n_series_promotion_pass_unfiltered": len(passing_unfiltered),
        "promotion_pass_series_filtered": [
            {"symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"],
             "train1_net_pnl": r["train1_net_pnl_filtered"]}
            for r in passing
        ],
        "pooled_mean_win_rate_pct_filtered": pooled_win_filtered,
        "pooled_mean_win_rate_pct_unfiltered": pooled_win_unfiltered,
        "mean_neg_months_filtered": mean_neg_months_filtered,
        "mean_neg_months_unfiltered": mean_neg_months_unfiltered,
        "seconds": round(time.time() - t_start, 2),
    }
    with open(f"{OUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(manifest_out, f, indent=2)

    print(f"\n{len(rows)} series in {time.time() - t_start:.1f}s -> {OUT_DIR}/summary/results.csv")
    print(f"harness control: {harness['n_mismatches']}/{harness['rows_compared']} mismatches")
    print(f"promotion_pass (filtered): {len(passing)}/{len(rows)} series "
          f"(unfiltered: {len(passing_unfiltered)}/{len(rows)})")
    print(f"pooled win rate: unfiltered {pooled_win_unfiltered:.2f}%, filtered {pooled_win_filtered:.2f}%")
    print(f"mean neg months: unfiltered {mean_neg_months_unfiltered:.2f}, filtered {mean_neg_months_filtered:.2f}")


if __name__ == "__main__":
    main()
