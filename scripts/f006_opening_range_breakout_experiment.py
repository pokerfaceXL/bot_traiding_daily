"""
F006 -- UTC opening-range breakout family, TRAIN 1 ONLY, NO_TRAIL.

Tests the hypothesis in
spec/research/F006-hypothesis-opening-range-breakout.md:
H1 (aggregate) -- does any of the 5 pre-registered ORB_UTC_* names have positive
mean net PnL over its 10-series pool at NO_TRAIL (activate_pct=10.0, max_sl_pct=0.03,
one-shot entry mask, cd=0, leverage=1)?
H2 (monthly, conditional on H1) -- does any H1-clearing name have a series clearing
spec/research/F005-validation-protocol.md section 7's monthly promotion checklist
(n_trades > 0, every valid month non-negative, all 12 Train-1 months valid, full-window
net PnL >= 0, DD <= 50%)?

Harness control (1 run, reported separately, NOT part of the 50-run grid):
DONCHIAN_55 on BTCUSDT/240 at the same NO_TRAIL/one-shot/cd=0 cell, checked row for
row against output/f006_catalog_notrail_sweep/summary/results.csv -- the experiment
script matching stored numbers before trusting the new ORB_UTC_* names, per the
research note's Sample section.

Does NOT import vol_range_expansion.py / cross_sectional_rs.py -- the ORB generator
and this script have no dependency on either family.

Reuses backtest_engine.py/entry_masks.py/regularity.py/data_contract.py/trade_stats.py/
opening_range_breakout.py unmodified. Writes only output/f006_opening_range_breakout/.
Zero network connections.

    python3 scripts/f006_opening_range_breakout_experiment.py
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
import opening_range_breakout as orb  # noqa: E402
import regularity  # noqa: E402
import strategy  # noqa: E402
import trade_stats  # noqa: E402

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]
CANDIDATE_NAMES = [f"ORB_UTC_{n}" for n in orb.OR_BARS_GRID]  # ORB_UTC_1/2/3/4/6

CONTROL_SYMBOL = "BTCUSDT"
CONTROL_INTERVAL = "240"
CONTROL_NAME = "DONCHIAN_55"

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

# NO_TRAIL exit geometry, identical to every other F006 NO_TRAIL cell.
ACTIVATE_PCT = 10.0
TRAIL_PCT = 0.04  # moot -- trail never arms
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

# spec/research/F005-validation-protocol.md section 3.2's train_1 window, duplicated
# from scripts/f005_run_baseline.py's _month_range(2024, 3, 2025, 2).
TRAIN1_MONTHS = [
    (2024, 3), (2024, 4), (2024, 5), (2024, 6), (2024, 7), (2024, 8),
    (2024, 9), (2024, 10), (2024, 11), (2024, 12), (2025, 1), (2025, 2),
]
TRAIN1_MONTHS_SET = set(TRAIN1_MONTHS)
WARMUP_MONTHS_SET = {(2024, 1), (2024, 2)}

OUT_DIR = "output/f006_opening_range_breakout"
CONTROL_SOURCE = "output/f006_catalog_notrail_sweep/summary/results.csv"


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


def _run_one(train1_df, mask, symbol, interval, strategy_name, n_calls) -> dict:
    t0 = time.time()
    result = backtest_engine.run_backtest(
        train1_df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT,
        cooldown_candles=COOLDOWN,
        entry_regime_mask=mask,
        **FIXED_PARAMS,
    )
    m = result.metrics
    trades = result.trades
    n_trades = int(len(trades))
    exit_mix = trades["exit_reason"].value_counts().to_dict() if n_trades else {}
    d = trade_stats.win_loss_decomposition(trades)

    days, months = regularity.compute_regularity(result.equity_curve)
    months_by_key = {(mo.year, mo.month): mo for mo in months}

    # regularity.classify_days() unconditionally flags the first day of any equity
    # curve as "missing" (no prior day to diff against) -- see
    # spec/research/F006-hypothesis-notrail-monthly-catalog5.md's Run_id section.
    first_day_net_pnl = 0.0
    if days and days[0].status == "missing" and days[0].equity is not None:
        first_day_net_pnl = days[0].equity - INITIAL_EQUITY

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
        dd.pnl for dd in days
        if dd.status != "missing"
        and (dd.day.year, dd.day.month) not in TRAIN1_MONTHS_SET
        and (dd.day.year, dd.day.month) not in WARMUP_MONTHS_SET
    )
    full_max_dd = m["max_drawdown_pct"]
    n_valid_months = sum(1 for r in monthly_rows if r["is_valid"])

    promotion_pass = (
        full_max_dd <= 50.0
        and all_valid_months_positive
        and n_valid_months == 12
        and train1_net_pnl >= 0
        and n_trades > 0
    )

    return {
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "n_calls": n_calls,
        "net_pnl": m["total_net_pnl"],
        "gross_pnl": round(float(trades["gross_pnl"].sum()) if n_trades else 0.0, 6),
        "win_rate": m["win_rate"],
        "n_trades": n_trades,
        "n_wins": d["n_wins"], "n_losses": d["n_losses"],
        "avg_winner": round(d["avg_winner"], 6),
        "avg_loser": round(d["avg_loser"], 6),
        "breakeven_win_rate_pct": (round(d["breakeven_win_rate_pct"], 4)
                                   if d["breakeven_win_rate_pct"] is not None else None),
        "exit_trailing_sl": int(exit_mix.get("trailing_sl", 0)),
        "max_drawdown_pct": full_max_dd,
        "final_equity": m["final_equity"],
        "train1_net_pnl": round(train1_net_pnl, 6),
        "warmup_net_pnl": round(warmup_net_pnl, 6),
        "boundary_net_pnl": round(boundary_net_pnl, 6),
        "first_day_net_pnl": round(first_day_net_pnl, 6),
        "n_valid_months": n_valid_months,
        "all_valid_months_nonnegative": all_valid_months_positive,
        "promotion_pass": promotion_pass,
        "monthly": monthly_rows,
        "seconds": round(time.time() - t0, 2),
    }


def run_harness_control() -> dict:
    """DONCHIAN_55 on BTCUSDT/240, same NO_TRAIL/one-shot/cd=0 cell, re-run through
    THIS script's harness and checked row for row against the stored catalog-sweep
    numbers -- the research note's Sample section control, run before trusting the
    ORB_UTC_* candidate rows below."""
    train1_df, manifest = load_train1(CONTROL_SYMBOL, CONTROL_INTERVAL)
    sig = entry_masks.strategy_signal_series(train1_df, CONTROL_NAME, interval=CONTROL_INTERVAL, now=NOW)
    mask = entry_masks.one_shot_entry_mask(sig)
    n_calls = int(mask.sum())
    row = _run_one(train1_df, mask, CONTROL_SYMBOL, CONTROL_INTERVAL, CONTROL_NAME, n_calls)

    if not os.path.exists(CONTROL_SOURCE):
        raise SystemExit(f"STOP: {CONTROL_SOURCE} not found -- cannot run harness control.")
    stored = pd.read_csv(CONTROL_SOURCE)
    stored["interval"] = stored["interval"].astype(str)
    stored = stored[
        (stored["symbol"] == CONTROL_SYMBOL) & (stored["interval"] == CONTROL_INTERVAL)
        & (stored["strategy"] == CONTROL_NAME) & (stored["no_trail"])
        & (stored["mask_mode"] == "one_shot") & (stored["cooldown_candles"] == COOLDOWN)
    ]
    if len(stored) != 1:
        raise SystemExit(f"STOP: expected exactly 1 stored control row, matched {len(stored)}.")
    stored_row = stored.iloc[0]
    mismatches = {}
    for col in ("net_pnl", "win_rate", "n_trades", "max_drawdown_pct", "final_equity"):
        new_val, stored_val = row[col], stored_row[col]
        if new_val != stored_val:
            mismatches[col] = {"new": new_val, "stored": stored_val}
    if mismatches:
        raise SystemExit(f"STOP: harness control mismatches -- {mismatches}")
    return {
        "checked": True, "stored_source": CONTROL_SOURCE,
        "symbol": CONTROL_SYMBOL, "interval": CONTROL_INTERVAL, "strategy": CONTROL_NAME,
        "checksum_verified": manifest.checksum_sha256 == EXPECTED_CHECKSUMS[(CONTROL_SYMBOL, CONTROL_INTERVAL)],
        "n_mismatches": 0, "row": {k: v for k, v in row.items() if k != "monthly"},
    }


def main():
    t_start = time.time()
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None

    for name in CANDIDATE_NAMES + [CONTROL_NAME]:
        assert name in strategy.STRATEGY_CATALOG, f"strategy {name!r} not in strategy.STRATEGY_CATALOG"

    os.makedirs(f"{OUT_DIR}/summary", exist_ok=True)
    os.makedirs(f"{OUT_DIR}/raw", exist_ok=True)

    print("running harness control (DONCHIAN_55, BTCUSDT/240) ...")
    harness = run_harness_control()
    print(f"harness control OK: {harness['n_mismatches']} mismatches vs {CONTROL_SOURCE}")

    rows = []
    checksums_used = {}
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            train1_df, manifest = load_train1(symbol, interval)
            checksums_used[f"{symbol}_{interval}"] = manifest.checksum_sha256
            for name in CANDIDATE_NAMES:
                sig = entry_masks.strategy_signal_series(train1_df, name, interval=interval, now=NOW)
                mask = entry_masks.one_shot_entry_mask(sig)
                n_calls = int(mask.sum())
                row = _run_one(train1_df, mask, symbol, interval, name, n_calls)
                rows.append(row)
                with open(f"{OUT_DIR}/raw/{symbol}_{interval}_{name}.json", "w") as f:
                    json.dump(row, f, indent=2, default=str)
            print(f"done {symbol}/{interval} ({len(rows)} runs so far, {time.time() - t_start:.1f}s elapsed)")

    assert len(rows) == 50, f"expected 50 candidate rows (5 names x 5 symbols x 2 intervals), got {len(rows)}"

    summary_rows = [{k: v for k, v in r.items() if k != "monthly"} for r in rows]
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(f"{OUT_DIR}/summary/results.csv", index=False)

    # -------------------------------------------------- discriminating checks
    no_trail_check = {"runs": len(rows), "runs_with_a_trailing_exit": int(sum(1 for r in rows if r["exit_trailing_sl"] > 0))}
    if no_trail_check["runs_with_a_trailing_exit"] > 0:
        raise SystemExit(f"STOP: {no_trail_check['runs_with_a_trailing_exit']} runs produced a trailing_sl exit under NO_TRAIL.")
    one_shot_violations = [r for r in rows if r["n_trades"] > r["n_calls"]]
    if one_shot_violations:
        raise SystemExit(f"STOP: {len(one_shot_violations)} one-shot violations.")

    # -------------------------------------------------- H1: aggregate check
    h1_table = []
    for name in CANDIDATE_NAMES:
        sub = summary_df[summary_df["strategy"] == name]
        h1_table.append({
            "strategy": name,
            "sum_net_pnl": round(float(sub["net_pnl"].sum()), 4),
            "mean_net_pnl": round(float(sub["net_pnl"].mean()), 4),
            "n_series": int(len(sub)),
            "n_profitable_series": int((sub["net_pnl"] > 0).sum()),
            "h1_pass": bool(sub["net_pnl"].mean() > 0),
        })
    h1_names_passing = [r["strategy"] for r in h1_table if r["h1_pass"]]
    h1_falsified = len(h1_names_passing) == 0

    # -------------------------------------------------- H2: monthly check (H1-passing names only)
    h2_table = []
    for r in rows:
        if r["strategy"] not in h1_names_passing:
            continue
        h2_table.append({
            "symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"],
            "train1_net_pnl": r["train1_net_pnl"], "n_neg_months": sum(
                1 for mo in r["monthly"] if mo["is_valid"] and mo["net_pnl"] is not None and mo["net_pnl"] < 0
            ),
            "promotion_pass": r["promotion_pass"],
        })
    h2_passing = [r for r in h2_table if r["promotion_pass"]]
    if h1_falsified:
        h2_verdict = "not_applicable_h1_failed"
    elif h2_passing:
        h2_verdict = "passed"
    else:
        h2_verdict = "falsified"

    manifest_out = {
        "script": "scripts/f006_opening_range_breakout_experiment.py",
        "git_commit": commit_sha,
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "pandas": pd.__version__,
        "n_candidate_series": len(rows),
        "candidate_names": CANDIDATE_NAMES,
        "checksums_used": checksums_used,
        "params": {
            "activate_pct": ACTIVATE_PCT, "trail_pct": TRAIL_PCT, "max_sl_pct": MAX_SL_PCT,
            "cooldown_candles": COOLDOWN, "mask_mode": "one_shot", "leverage": FIXED_PARAMS["leverage"],
            "initial_equity": INITIAL_EQUITY, "stake": STAKE, **FIXED_PARAMS,
        },
        "harness_control": harness,
        "no_trail_mechanism_check": no_trail_check,
        "one_shot_violations": len(one_shot_violations),
        "h1_aggregate_table": h1_table,
        "h1_names_passing": h1_names_passing,
        "h1_falsified": h1_falsified,
        "h2_monthly_table": h2_table,
        "h2_n_promotion_pass": len(h2_passing),
        "h2_promotion_pass_series": h2_passing,
        "h2_verdict": h2_verdict,
        "seconds": round(time.time() - t_start, 2),
    }
    with open(f"{OUT_DIR}/summary/manifest.json", "w") as f:
        json.dump(manifest_out, f, indent=2)

    print(f"\n{len(rows)} candidate series in {time.time() - t_start:.1f}s -> {OUT_DIR}/summary/results.csv")
    print(f"harness control: {harness['n_mismatches']} mismatches")
    print("\nH1 (per name, mean net PnL over 10 series):")
    for r in h1_table:
        print(f"  {r['strategy']:<10} mean_net_pnl={r['mean_net_pnl']:9.2f}  "
              f"profitable_series={r['n_profitable_series']}/10  h1_pass={r['h1_pass']}")
    print(f"H1 falsified: {h1_falsified} (names passing: {h1_names_passing})")
    print(f"H2 verdict: {h2_verdict} ({len(h2_passing)} promotion_pass series)")


if __name__ == "__main__":
    main()
