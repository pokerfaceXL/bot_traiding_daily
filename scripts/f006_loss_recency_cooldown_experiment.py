"""
F006 -- loss-conditioned re-entry cooldown ("loss recency") for the three NO_TRAIL
aggregate-positive names.

Tests the hypothesis in spec/research/F006-hypothesis-loss-recency-cooldown.md: whether
gating new entries so none may open within LOSS_COOLDOWN=50 candles of that same series'
own last LOSING trade's close (net_pnl < 0, any exit reason) causes any of the 30
(name, symbol, interval) series to clear spec/research/F005-validation-protocol.md section
7's monthly promotion checklist at NO_TRAIL, where F006-hypothesis-notrail-monthly.md found
0/30 at loss_cooldown_candles=0.

Single pass, .venv_test only -- no Lorentzian dependency in this sample.

Uses backtest_engine.py's new loss_cooldown_candles hook (this slice's one engine change,
additive, default 0 unchanged); reuses data_contract.py/regularity.py/donchian.py/
strategy.py unmodified. Writes only output/f006_loss_recency_cooldown/. Zero network
connections.
"""
from __future__ import annotations

import json
import os
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
COOLDOWN = 0  # blanket cooldown_candles, off -- this note tests loss_cooldown_candles in isolation
LOSS_COOLDOWN = 50
FIXED_PARAMS = dict(
    leverage=1.0,
    atr_multiplier=1.5,
    commission_rate_bps=10.0,
    half_spread_bps=5.0,
    slippage_bps=2.0,
)
INITIAL_EQUITY = 500.0
BASE_STAKE = 100.0

TRAIN1_MONTHS = [
    (2024, 3), (2024, 4), (2024, 5), (2024, 6), (2024, 7), (2024, 8),
    (2024, 9), (2024, 10), (2024, 11), (2024, 12), (2025, 1), (2025, 2),
]
TRAIN1_MONTHS_SET = set(TRAIN1_MONTHS)

OUT_DIR = "output/f006_loss_recency_cooldown"
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


def _evaluate(result) -> dict:
    days, months = regularity.compute_regularity(result.equity_curve)
    months_by_key = {(m.year, m.month): m for m in months}

    monthly_rows = []
    all_valid_months_nonneg = True
    n_negative_months = 0
    for (year, month) in TRAIN1_MONTHS:
        mr = months_by_key.get((year, month))
        if mr is None:
            monthly_rows.append({"year": year, "month": month, "is_valid": False, "net_pnl": None})
            continue
        net_pnl = _net_pnl_for_month(days, year, month) if mr.is_valid else None
        if mr.is_valid and net_pnl is not None and net_pnl < 0:
            all_valid_months_nonneg = False
            n_negative_months += 1
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
    n_trades = int(len(result.trades))
    return {
        "n_trades": n_trades,
        "train1_net_pnl": round(train1_net_pnl, 6),
        "full_run_max_drawdown_pct": full_max_dd,
        "full_run_final_equity": result.metrics["final_equity"],
        "n_valid_months": n_valid_months,
        "n_negative_months": n_negative_months,
        "all_valid_months_nonnegative": all_valid_months_nonneg,
        "promotion_pass": promotion_pass,
        "promotion_pass_genuine": bool(promotion_pass and n_trades > 0),
        "degenerate_pass": bool(promotion_pass and n_trades == 0),
        "win_rate_pct": float((result.trades["net_pnl"] > 0).mean() * 100) if n_trades > 0 else None,
        "n_wins": int((result.trades["net_pnl"] > 0).sum()) if n_trades > 0 else 0,
        "monthly": monthly_rows,
        "n_trades_per_month": {f"{y}-{m:02d}": c for (y, m), c in _n_trades_per_month(result.trades).items()},
    }


def _run_one(train1_df, symbol, interval, strategy_name) -> dict:
    t0 = time.time()
    sig = entry_masks.strategy_signal_series(train1_df, strategy_name, interval=interval, now=NOW)
    mask = entry_masks.one_shot_entry_mask(sig)
    baseline_result = backtest_engine.run_backtest(
        train1_df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=BASE_STAKE, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT, cooldown_candles=COOLDOWN,
        entry_regime_mask=mask, loss_cooldown_candles=0, **FIXED_PARAMS,
    )
    gated_result = backtest_engine.run_backtest(
        train1_df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=BASE_STAKE, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT, cooldown_candles=COOLDOWN,
        entry_regime_mask=mask, loss_cooldown_candles=LOSS_COOLDOWN, **FIXED_PARAMS,
    )

    baseline_eval = _evaluate(baseline_result)
    gated_eval = _evaluate(gated_result)

    if gated_eval["n_trades"] > baseline_eval["n_trades"]:
        raise SystemExit(
            f"STOP: subset invariant violated for {symbol}/{interval}/{strategy_name}: "
            f"gated n_trades={gated_eval['n_trades']} > baseline n_trades={baseline_eval['n_trades']}"
        )

    elapsed = time.time() - t0
    return {
        "symbol": symbol,
        "interval": interval,
        "strategy": strategy_name,
        "n_trades_baseline": baseline_eval["n_trades"],
        "n_trades_gated": gated_eval["n_trades"],
        "train1_net_pnl_baseline": baseline_eval["train1_net_pnl"],
        "train1_net_pnl_gated": gated_eval["train1_net_pnl"],
        "full_run_max_drawdown_pct_baseline": baseline_eval["full_run_max_drawdown_pct"],
        "full_run_max_drawdown_pct_gated": gated_eval["full_run_max_drawdown_pct"],
        "n_negative_months_baseline": baseline_eval["n_negative_months"],
        "n_negative_months_gated": gated_eval["n_negative_months"],
        "win_rate_pct_baseline": baseline_eval["win_rate_pct"],
        "win_rate_pct_gated": gated_eval["win_rate_pct"],
        "n_wins_baseline": baseline_eval["n_wins"],
        "n_wins_gated": gated_eval["n_wins"],
        "promotion_pass_baseline": baseline_eval["promotion_pass"],
        "promotion_pass_gated": gated_eval["promotion_pass"],
        "promotion_pass_genuine_gated": gated_eval["promotion_pass_genuine"],
        "degenerate_pass_gated": gated_eval["degenerate_pass"],
        "elapsed_seconds": round(elapsed, 3),
        "_baseline_eval": baseline_eval,
        "_gated_eval": gated_eval,
    }


def main():
    os.makedirs(f"{OUT_DIR}/raw", exist_ok=True)
    os.makedirs(f"{OUT_DIR}/summary", exist_ok=True)

    prior = pd.read_csv(PRIOR_RESULTS)
    prior_by_key = {
        (r["symbol"], str(r["interval"]), r["strategy"]): r
        for _, r in prior.iterrows()
    }

    rows = []
    t_start = time.time()
    harness_mismatches = []
    for interval in INTERVALS:
        for symbol in SYMBOLS:
            train1_df, manifest = load_train1(symbol, interval)
            for name in NAMES:
                res = _run_one(train1_df, symbol, interval, name)

                key = (symbol, interval, name)
                pr = prior_by_key.get(key)
                if pr is None:
                    raise SystemExit(f"STOP: no prior f006_notrail_monthly row for {key}")
                if res["n_trades_baseline"] != int(pr["n_trades"]) or abs(res["train1_net_pnl_baseline"] - float(pr["train1_net_pnl"])) > 1e-3:
                    harness_mismatches.append({
                        "key": key,
                        "n_trades_baseline": res["n_trades_baseline"], "n_trades_prior": int(pr["n_trades"]),
                        "train1_net_pnl_baseline": res["train1_net_pnl_baseline"], "train1_net_pnl_prior": float(pr["train1_net_pnl"]),
                    })

                with open(f"{OUT_DIR}/raw/{symbol}_{interval}_{name}.json", "w") as f:
                    json.dump({
                        "symbol": symbol, "interval": interval, "strategy": name,
                        "baseline": res["_baseline_eval"], "gated": res["_gated_eval"],
                    }, f, indent=2, default=str)

                row = {k: v for k, v in res.items() if not k.startswith("_")}
                rows.append(row)
                print(f"{symbol}/{interval}/{name}: baseline n={row['n_trades_baseline']} pnl={row['train1_net_pnl_baseline']:.2f} negmo={row['n_negative_months_baseline']} | "
                      f"gated n={row['n_trades_gated']} pnl={row['train1_net_pnl_gated']:.2f} negmo={row['n_negative_months_gated']} pass_genuine={row['promotion_pass_genuine_gated']}")

    if harness_mismatches:
        raise SystemExit(f"STOP: harness control against f006_notrail_monthly failed for {len(harness_mismatches)} series: {harness_mismatches}")

    results_df = pd.DataFrame(rows)
    results_df.to_csv(f"{OUT_DIR}/summary/results.csv", index=False)

    n_genuine = int(results_df["promotion_pass_genuine_gated"].sum())
    n_degenerate = int(results_df["degenerate_pass_gated"].sum())

    pooled_win_baseline = results_df["n_wins_baseline"].sum() / results_df["n_trades_baseline"].sum() * 100
    pooled_win_gated = results_df["n_wins_gated"].sum() / results_df["n_trades_gated"].sum() * 100
    mean_negmo_baseline = results_df["n_negative_months_baseline"].mean()
    mean_negmo_gated = results_df["n_negative_months_gated"].mean()
    mean_pnl_baseline = results_df["train1_net_pnl_baseline"].mean()
    mean_pnl_gated = results_df["train1_net_pnl_gated"].mean()
    trade_cut_pct = 100.0 * (1 - results_df["n_trades_gated"].sum() / results_df["n_trades_baseline"].sum())

    manifest_out = {
        "script": "scripts/f006_loss_recency_cooldown_experiment.py",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "n_series": len(rows),
        "loss_cooldown_candles": LOSS_COOLDOWN,
        "elapsed_seconds": round(time.time() - t_start, 2),
        "harness_control_mismatches": len(harness_mismatches),
        "n_promotion_pass_genuine": n_genuine,
        "n_degenerate_pass": n_degenerate,
        "pooled_trade_weighted_win_pct_baseline": pooled_win_baseline,
        "pooled_trade_weighted_win_pct_gated": pooled_win_gated,
        "mean_negative_months_baseline": mean_negmo_baseline,
        "mean_negative_months_gated": mean_negmo_gated,
        "mean_train1_net_pnl_baseline": mean_pnl_baseline,
        "mean_train1_net_pnl_gated": mean_pnl_gated,
        "trade_cut_pct": trade_cut_pct,
    }
    with open(f"{OUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(manifest_out, f, indent=2, default=str)

    print("\n=== SUMMARY ===")
    print(json.dumps(manifest_out, indent=2, default=str))


if __name__ == "__main__":
    main()
