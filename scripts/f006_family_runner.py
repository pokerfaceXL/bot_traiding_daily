"""
scripts/f006_family_runner.py -- shared F006 experiment harness (F006 shared-harness
ticket, spec/research/F006-shared-harness.md). Infrastructure, not a signal family:
`run_family()` here tests nothing about the market by itself.

Centralizes what every F006 family script since f006_notrail_monthly hand-copied:
the frozen symbol/interval basket, the ten data_cache checksums, the Train-1 window,
the NO_TRAIL exit geometry, the DONCHIAN_55 harness-control comparison, the per-
series raw/summary/manifest write under output/f006_<family>/, and the H1 (mean net
PnL > 0 across the 10-series pool) / H2 (monthly promotion checklist, conditional on
H1) checks.

A new signal-family script's whole job: define a signal module with
`catalog_entries() -> dict[str, Callable[[pd.DataFrame], pd.Series]]`, freeze its own
candidate names and hypothesis note in spec/research/F006-hypothesis-<family>.md, and
call `run_family(...)` once. It MUST NOT copy this loop, and MUST NOT depend on any
unmerged sibling family module at runtime -- catalog_entries are registered into
strategy.STRATEGY_CATALOG only inside this process, never by editing strategy.py.

Reuses backtest_engine.py/entry_masks.py/regularity.py/data_contract.py/
trade_stats.py unmodified. Zero network connections.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Callable, Mapping, Optional, Sequence

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine  # noqa: E402
import data_contract  # noqa: E402
import entry_masks  # noqa: E402
import regularity  # noqa: E402
import strategy  # noqa: E402
import trade_stats  # noqa: E402

# Frozen basket, identical across every F006 family script.
SYMBOLS = ("SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT")
INTERVALS = ("240", "60")

CONTROL_NAME = "DONCHIAN_55"  # closed/merged family, harness control only
CONTROL_REFERENCE_CSV = "output/f006_trailing_boundary/summary/results.csv"

WARMUP_START = "2024-01-26T00:00:00Z"
TRAIN1_END = pd.Timestamp("2025-03-01T00:00:00Z")
NOW = TRAIN1_END

# spec/research/F005-validation-protocol.md section 6.
EXPECTED_CHECKSUMS = {
    ("SOLUSDT", "240"): "d70b64f3a8730a34fa9dab462b409f7d826e547db584fdc219acdc8d4f6e2174",
    ("SOLUSDT", "60"): "99d6f5a73c5bb19a2693513db684d359f956760dc11ea66f9818173289eb2b6b",
    ("ETHUSDT", "240"): "781b50001b94cd76a576fb4ef8321b893c68470cdc3dc72854804556e3e94a95",
    ("ETHUSDT", "60"): "7122f57dca13a78cbff3f8a0ce1a42ee982292a2e63db2ef1995f9e133a78bfd",
    ("BTCUSDT", "240"): "94491aead67f72d67a8cf0723d383966309ea119426b82793ef18835a36c61eb",
    ("BTCUSDT", "60"): "66776a15cbe6f3bb5f55c5de2d7aa1e510061a65b3a49f9263057a8c69e01ad6",
    ("XRPUSDT", "240"): "02f0d2a2372d1b1282821228dedfc1a608135c7e25e453ee714a25efa1cc4d49",
    ("XRPUSDT", "60"): "bc970b808a3975295a5cff9e66e72b50c602eecd2d35441d0dcbf3057113c6dd",
    ("DOGEUSDT", "240"): "b96eb360778ee96384a18c725b92b6737dd33d66c2a2b10f24fdc65aaf7ec2b0",
    ("DOGEUSDT", "60"): "a6509502f310b4dadf1c29e5b9cd785671bc4e16ad1de75829deb4ce1c7243fe",
}

# NO_TRAIL exit geometry, identical across every F006 NO_TRAIL cell.
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

# spec/research/F005-validation-protocol.md section 3.2's Train-1 window (12 full months).
TRAIN1_MONTHS = [
    (2024, 3), (2024, 4), (2024, 5), (2024, 6), (2024, 7), (2024, 8),
    (2024, 9), (2024, 10), (2024, 11), (2024, 12), (2025, 1), (2025, 2),
]
TRAIN1_MONTHS_SET = set(TRAIN1_MONTHS)
WARMUP_MONTHS_SET = {(2024, 1), (2024, 2)}

# Columns written to summary/results.csv, in order (per spec/research/F006-shared-harness.md).
SUMMARY_COLUMNS = [
    "symbol", "interval", "strategy", "n_calls", "net_pnl", "gross_pnl", "win_rate",
    "n_trades", "n_wins", "n_losses", "avg_winner", "avg_loser", "breakeven_win_rate_pct",
    "exit_trailing_sl", "max_drawdown_pct", "final_equity", "train1_net_pnl",
    "warmup_net_pnl", "boundary_net_pnl", "n_valid_months", "all_valid_months_nonnegative",
    "promotion_pass", "seconds",
]


def register_catalog_entries(entries: Mapping[str, Callable]) -> None:
    """Runtime-only registration into strategy.STRATEGY_CATALOG. Never edits strategy.py."""
    for name, fn in entries.items():
        if name in strategy.STRATEGY_CATALOG:
            raise ValueError(f"{name!r} already registered in strategy.STRATEGY_CATALOG")
        strategy.STRATEGY_CATALOG[name] = fn


def load_train1(symbol: str, interval: str):
    try:
        # Do not load, slice, or inspect validation/holdout bars for a Train-1 H1 run.
        # The cache request ends at TRAIN1_END; WARMUP_START retains indicator warm-up.
        full_df, manifest = data_contract.load_dataset(
            "data_cache", symbol, interval, WARMUP_START, TRAIN1_END
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
    if train1_df.empty:
        raise SystemExit(f"STOP: empty Train-1 slice for {symbol}/{interval}.")
    if pd.DatetimeIndex(train1_df.index).max() >= TRAIN1_END:
        raise SystemExit(f"STOP: Train-1 slice for {symbol}/{interval} leaks past TRAIN1_END.")
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

    monthly_rows = []
    all_valid_months_nonnegative = True
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
            all_valid_months_nonnegative = False
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
        and all_valid_months_nonnegative
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
        "n_valid_months": n_valid_months,
        "all_valid_months_nonnegative": all_valid_months_nonnegative,
        "promotion_pass": promotion_pass,
        "monthly": monthly_rows,
        "seconds": round(time.time() - t0, 2),
    }


def verify_harness_control(rows: list, control_name: str, reference_csv: str) -> dict:
    """control_name's 10 rows must reproduce the referenced note's stored NO_TRAIL rows."""
    mine = pd.DataFrame([r for r in rows if r["strategy"] == control_name])
    mine["interval"] = mine["interval"].astype(str)
    if not os.path.exists(reference_csv):
        raise SystemExit(f"STOP: {reference_csv} not found -- cannot run harness control.")
    stored = pd.read_csv(reference_csv)
    stored["interval"] = stored["interval"].astype(str)
    stored = stored[stored["strategy"] == control_name]
    if "no_trail" in stored.columns:
        stored = stored[stored["no_trail"]]
    merged = mine.merge(stored, on=["symbol", "interval", "strategy"], suffixes=("_new", "_stored"))
    if len(merged) != 10:
        raise SystemExit(f"STOP: expected 10 control rows, matched {len(merged)}.")
    mismatches = []
    for col in ("net_pnl", "win_rate", "n_trades", "max_drawdown_pct", "final_equity"):
        bad = merged[merged[f"{col}_new"] != merged[f"{col}_stored"]]
        for _, row in bad.iterrows():
            mismatches.append({"symbol": row["symbol"], "interval": row["interval"],
                               "column": col, "new": row[f"{col}_new"], "stored": row[f"{col}_stored"]})
    if mismatches:
        raise SystemExit(f"STOP: {len(mismatches)} control mismatches -- {mismatches[:5]}")
    return {"rows_compared": int(len(merged)), "n_mismatches": 0, "source": reference_csv}


def run_family(
    family: str,
    candidate_names: Sequence[str],
    *,
    catalog_entries: Optional[Mapping[str, Callable]] = None,
    hypothesis_note: str,
    script_path: str,
    output_dir: Optional[str] = None,
) -> dict:
    """Runs the frozen F006 NO_TRAIL Train-1 sweep for one signal family and writes
    output/f006_<family>/{raw,summary}/. Returns the manifest dict (also written to
    summary/manifest.json). See spec/research/F006-shared-harness.md's "Frozen result
    schema" for the column/key contract.

    The symbol/interval basket and the DONCHIAN_55 harness control are NOT caller-
    configurable -- this function owns them so no family can emit a non-10-series or
    uncontrolled result while claiming the frozen schema. A family that needs a
    different basket or control is not this shared harness's caller; it needs its own
    reviewed exception, not a kwarg on this function.

    catalog_entries, if given, is registered into strategy.STRATEGY_CATALOG for this
    process only (never edits strategy.py) -- pass None if every name in
    candidate_names is already a production catalog entry (e.g. a harness self-check).
    """
    t_start = time.time()
    output_dir = output_dir or f"output/f006_{family}"
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None

    if catalog_entries:
        register_catalog_entries(catalog_entries)

    if CONTROL_NAME in candidate_names:
        raise ValueError(f"{CONTROL_NAME!r} is the harness control, not a candidate name")
    all_names = list(candidate_names) + [CONTROL_NAME]
    for name in all_names:
        if name not in strategy.STRATEGY_CATALOG:
            raise ValueError(f"strategy {name!r} not registered in strategy.STRATEGY_CATALOG")

    os.makedirs(f"{output_dir}/summary", exist_ok=True)
    os.makedirs(f"{output_dir}/raw", exist_ok=True)

    rows = []
    checksums_used = {}
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            train1_df, manifest = load_train1(symbol, interval)
            checksums_used[f"{symbol}_{interval}"] = manifest.checksum_sha256
            for name in all_names:
                sig = entry_masks.strategy_signal_series(train1_df, name, interval=interval, now=NOW)
                mask = entry_masks.one_shot_entry_mask(sig)
                n_calls = int(mask.sum())
                row = _run_one(train1_df, mask, symbol, interval, name, n_calls)
                rows.append(row)
                with open(f"{output_dir}/raw/{symbol}_{interval}_{name}.json", "w") as f:
                    json.dump(row, f, indent=2, default=str)

    summary_rows = [{k: r[k] for k in SUMMARY_COLUMNS} for r in rows]
    summary_df = pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS)
    summary_df.to_csv(f"{output_dir}/summary/results.csv", index=False)

    # -------------------------------------------------- discriminating checks
    # unconditional: no kwarg on this function can skip the harness control
    harness = verify_harness_control(rows, CONTROL_NAME, CONTROL_REFERENCE_CSV)

    no_trail_check = {"runs": len(rows),
                      "runs_with_a_trailing_exit": int(sum(1 for r in rows if r["exit_trailing_sl"] > 0))}
    if no_trail_check["runs_with_a_trailing_exit"] > 0:
        raise SystemExit(f"STOP: {no_trail_check['runs_with_a_trailing_exit']} runs produced a trailing_sl exit under NO_TRAIL.")
    one_shot_violations = [r for r in rows if r["n_trades"] > r["n_calls"]]
    if one_shot_violations:
        raise SystemExit(f"STOP: {len(one_shot_violations)} one-shot violations.")

    # -------------------------------------------------- H1: aggregate check (candidates only)
    cand_df = summary_df[summary_df["strategy"].isin(candidate_names)]
    h1_table = []
    for name in candidate_names:
        sub = cand_df[cand_df["strategy"] == name]
        h1_table.append({
            "strategy": name,
            "sum_net_pnl": round(float(sub["net_pnl"].sum()), 4),
            "mean_net_pnl": round(float(sub["net_pnl"].mean()), 4),
            "n_series": int(len(sub)),
            "n_profitable_series": int((sub["net_pnl"] > 0).sum()),
            "n_trades_total": int(sub["n_trades"].sum()),
            "h1_pass": bool(sub["net_pnl"].mean() > 0),
        })
    h1_names_passing = [r["strategy"] for r in h1_table if r["h1_pass"]]
    h1_falsified = len(h1_names_passing) == 0

    # -------------------------------------------------- H2: monthly check (H1-passing names only)
    h2_table = []
    if not h1_falsified:
        for r in rows:
            if r["strategy"] not in h1_names_passing:
                continue
            h2_table.append({
                "symbol": r["symbol"], "interval": r["interval"], "strategy": r["strategy"],
                "train1_net_pnl": r["train1_net_pnl"], "n_trades": r["n_trades"],
                "max_drawdown_pct": r["max_drawdown_pct"],
                "n_neg_months": sum(
                    1 for mo in r["monthly"] if mo["is_valid"] and mo["net_pnl"] is not None and mo["net_pnl"] < 0
                ),
                "n_valid_months": r["n_valid_months"],
                "promotion_pass": r["promotion_pass"],
            })
    h2_passing = [r for r in h2_table if r["promotion_pass"]]
    h2_status = "not_applicable_h1_failed" if h1_falsified else (
        "falsified" if not h2_passing else "cleared")

    manifest_out = {
        "family": family,
        "script": script_path,
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
        "candidate_names": list(candidate_names),
        "control_name": CONTROL_NAME,
        "hypothesis_note": hypothesis_note,
        "harness_control": harness,
        "no_trail_mechanism_check": no_trail_check,
        "one_shot_violations": len(one_shot_violations),
        "h1_table": h1_table,
        "h1_names_passing": h1_names_passing,
        "h1_falsified": h1_falsified,
        "h2_table": h2_table,
        "h2_names_with_a_passing_series": sorted({r["strategy"] for r in h2_passing}),
        "h2_status": h2_status,
        "elapsed_seconds": round(time.time() - t_start, 1),
    }
    with open(f"{output_dir}/summary/manifest.json", "w") as f:
        json.dump(manifest_out, f, indent=2, default=str)

    return manifest_out


def _selfcheck() -> None:
    """Reference/self-check caller: DONCHIAN_20 (already merged) as the lone
    'candidate' against the DONCHIAN_55 control, both already in the production
    catalog -- proves run_family's engine wiring reproduces the frozen NO_TRAIL
    numbers with zero new catalog registration. Not a new hypothesis test; DONCHIAN_20
    is a closed F006 catalog entry, not a candidate under evaluation here."""
    manifest = run_family(
        family="runner_selfcheck",
        candidate_names=["DONCHIAN_20"],
        catalog_entries=None,
        hypothesis_note=(
            "Runner self-check only (spec/research/F006-shared-harness.md's Acceptance "
            "section), not a new signal-family test. DONCHIAN_20/DONCHIAN_55 are closed "
            "F006 catalog entries reused here only to prove run_family() reproduces "
            "output/f006_trailing_boundary/summary/results.csv's stored NO_TRAIL numbers."
        ),
        script_path="scripts/f006_family_runner.py",
    )
    print(f"harness control ({manifest['control_name']}): "
          f"{manifest['harness_control']['rows_compared']} rows, "
          f"{manifest['harness_control']['n_mismatches']} mismatches")
    print(f"no-trail mechanism check: "
          f"{manifest['no_trail_mechanism_check']['runs_with_a_trailing_exit']}/"
          f"{manifest['no_trail_mechanism_check']['runs']} runs had a trailing exit")
    print(f"one-shot violations: {manifest['one_shot_violations']}")
    print(f"h1_table: {json.dumps(manifest['h1_table'], indent=2)}")
    print(f"elapsed: {manifest['elapsed_seconds']}s -> output/f006_runner_selfcheck/summary/")


if __name__ == "__main__":
    _selfcheck()
