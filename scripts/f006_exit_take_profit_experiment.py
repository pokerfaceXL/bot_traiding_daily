"""
F006 -- exit-side take-profit at TP_MULTIPLE=2.0 x initial stop distance, NO_TRAIL, Train 1.

Tests spec/research/F006-hypothesis-exit-take-profit.md: whether any of the 30
(name, symbol, interval) series -- DONCHIAN_55, BB_20_25_breakout, DONCHIAN_PULLBACK_55 x
5 symbols x 2 intervals -- clears spec/research/F005-validation-protocol.md section 7's
monthly promotion checklist at NO_TRAIL (activate_pct=10.0) plus the new
backtest_engine.run_backtest(take_profit_multiple=2.0) hook, on Train 1.

Two arms per series: baseline (take_profit_multiple=None, must reproduce
output/f006_notrail_monthly/summary/results.csv exactly) and gated (take_profit_multiple=2.0).

Single pass, .venv_test only -- no Lorentzian dependency in this sample.
Reuses backtest_engine.py/entry_masks.py/regularity.py/data_contract.py unmodified except for
backtest_engine.py's one new additive parameter. Writes only output/f006_exit_take_profit/.
Zero network connections.
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
TRAIL_PCT = 0.04  # moot -- trail never arms
MAX_SL_PCT = 0.03
COOLDOWN = 0
TP_MULTIPLE = 2.0
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
WARMUP_MONTHS_SET = {(2024, 1), (2024, 2)}

OUT_DIR = "output/f006_exit_take_profit"
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


def _run_one(train1_df, mask, symbol, interval, strategy_name, take_profit_multiple) -> dict:
    t0 = time.time()
    result = backtest_engine.run_backtest(
        train1_df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT,
        cooldown_candles=COOLDOWN,
        take_profit_multiple=take_profit_multiple,
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
    boundary_net_pnl = sum(
        d.pnl for d in days
        if d.status != "missing"
        and (d.day.year, d.day.month) not in TRAIN1_MONTHS_SET
        and (d.day.year, d.day.month) not in WARMUP_MONTHS_SET
    )
    full_max_dd = result.metrics["max_drawdown_pct"]
    n_valid_months = sum(1 for r in monthly_rows if r["is_valid"])
    n_trades = int(len(result.trades))

    promotion_pass = (
        full_max_dd <= 50.0
        and all_valid_months_positive
        and n_valid_months == 12
        and train1_net_pnl >= 0
    )
    promotion_pass_genuine = promotion_pass and n_trades > 0
    degenerate_pass = promotion_pass and n_trades == 0
    n_neg_months = sum(
        1 for r in monthly_rows if r["is_valid"] and r["net_pnl"] is not None and r["net_pnl"] < 0
    )

    trades = result.trades
    if n_trades > 0:
        wins = trades[trades["net_pnl"] > 0]["net_pnl"]
        losses = trades[trades["net_pnl"] <= 0]["net_pnl"]
        win_rate = round(100.0 * len(wins) / n_trades, 4)
        avg_win = round(float(wins.mean()), 6) if len(wins) else None
        avg_loss = round(float(losses.mean()), 6) if len(losses) else None
        exit_reason_counts = trades["exit_reason"].value_counts().to_dict()
    else:
        win_rate = None
        avg_win = None
        avg_loss = None
        exit_reason_counts = {}

    return {
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "take_profit_multiple": take_profit_multiple,
        "n_trades": n_trades,
        "train1_net_pnl": round(train1_net_pnl, 6),
        "warmup_net_pnl": round(warmup_net_pnl, 6),
        "boundary_net_pnl": round(boundary_net_pnl, 6),
        "full_run_max_drawdown_pct": full_max_dd,
        "full_run_final_equity": result.metrics["final_equity"],
        "n_valid_months": n_valid_months,
        "n_neg_months": n_neg_months,
        "all_valid_months_nonnegative": all_valid_months_positive,
        "promotion_pass": promotion_pass,
        "promotion_pass_genuine": promotion_pass_genuine,
        "degenerate_pass": degenerate_pass,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "exit_reason_counts": exit_reason_counts,
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
                baseline_row = _run_one(train1_df, mask, symbol, interval, name, take_profit_multiple=None)
                gated_row = _run_one(train1_df, mask, symbol, interval, name, take_profit_multiple=TP_MULTIPLE)
                rows.append(("baseline", baseline_row))
                rows.append(("gated", gated_row))
                with open(f"{OUT_DIR}/raw/{symbol}_{interval}_{name}_baseline.json", "w") as f:
                    json.dump(baseline_row, f, indent=2, default=str)
                with open(f"{OUT_DIR}/raw/{symbol}_{interval}_{name}_gated.json", "w") as f:
                    json.dump(gated_row, f, indent=2, default=str)
            print(f"done {symbol}/{interval} ({len(rows)} rows so far, {time.time() - t_start:.1f}s elapsed)")

    summary_rows = [{"arm": arm, **{k: v for k, v in r.items() if k not in ("monthly", "exit_reason_counts")}}
                     for arm, r in rows]
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(f"{OUT_DIR}/summary/results.csv", index=False)

    # -------------------------------------------------- harness control
    harness = {"rows_compared": 0, "n_mismatches": 0, "mismatches": []}
    baseline_rows = summary_df[summary_df["arm"] == "baseline"]
    if os.path.exists(PRIOR_RESULTS):
        prior = pd.read_csv(PRIOR_RESULTS)
        prior["interval"] = prior["interval"].astype(str)
        merged = baseline_rows.merge(
            prior[["symbol", "interval", "strategy", "train1_net_pnl", "n_trades"]],
            on=["symbol", "interval", "strategy"], suffixes=("", "_prior"),
        )
        harness["rows_compared"] = int(len(merged))
        mismatches = []
        for _, r in merged.iterrows():
            if abs(r["train1_net_pnl"] - r["train1_net_pnl_prior"]) > 1e-3 or r["n_trades"] != r["n_trades_prior"]:
                mismatches.append({
                    "symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"],
                    "train1_net_pnl": r["train1_net_pnl"], "prior_train1_net_pnl": r["train1_net_pnl_prior"],
                    "n_trades": r["n_trades"], "prior_n_trades": r["n_trades_prior"],
                })
        harness["n_mismatches"] = len(mismatches)
        harness["mismatches"] = mismatches
        if mismatches:
            raise SystemExit(
                f"STOP: {len(mismatches)} baseline-arm series disagree with "
                f"{PRIOR_RESULTS}'s stored NO_TRAIL rows -- {mismatches[:5]}"
            )
    else:
        harness["source"] = f"{PRIOR_RESULTS} MISSING -- not compared"

    gated_rows = [r for arm, r in rows if arm == "gated"]
    passing = [r for r in gated_rows if r["promotion_pass"]]
    genuine_passing = [r for r in gated_rows if r["promotion_pass_genuine"]]
    degenerate = [r for r in gated_rows if r["degenerate_pass"]]

    manifest_out = {
        "script": "scripts/f006_exit_take_profit_experiment.py",
        "git_commit": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pandas": pd.__version__,
        "n_series": len(gated_rows),
        "checksums_used": checksums_used,
        "params": {
            "activate_pct": ACTIVATE_PCT, "trail_pct": TRAIL_PCT, "max_sl_pct": MAX_SL_PCT,
            "cooldown_candles": COOLDOWN, "take_profit_multiple": TP_MULTIPLE, "mask_mode": "one_shot",
            "initial_equity": INITIAL_EQUITY, "stake": STAKE, **FIXED_PARAMS,
        },
        "harness_control": harness,
        "n_series_promotion_pass_gated": len(passing),
        "n_series_promotion_pass_genuine_gated": len(genuine_passing),
        "n_series_degenerate_pass_gated": len(degenerate),
        "promotion_pass_genuine_series": [
            {"symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"],
             "train1_net_pnl": r["train1_net_pnl"], "n_trades": r["n_trades"], "n_neg_months": r["n_neg_months"]}
            for r in genuine_passing
        ],
        "seconds": round(time.time() - t_start, 2),
    }
    with open(f"{OUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(manifest_out, f, indent=2)

    print(f"\n{len(gated_rows)} series (2 arms each) in {time.time() - t_start:.1f}s -> {OUT_DIR}/summary/results.csv")
    print(f"harness control: {harness['n_mismatches']}/{harness['rows_compared']} mismatches")
    print(f"gated promotion_pass: {len(passing)}/{len(gated_rows)} series, genuine: {len(genuine_passing)}, degenerate: {len(degenerate)}")


if __name__ == "__main__":
    main()
