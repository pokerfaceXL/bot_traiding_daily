"""
F006 -- one-shot flip entry hypothesis experiment, TRAIN 1 ONLY.

Tests the hypothesis in spec/research/F006-hypothesis-one-shot-entry.md: that
allowing at most ONE entry per directional call -- a call being one maximal
contiguous run of the same nonzero signal value -- recovers more of the Train-1
deficit than the time-based `cooldown_candles=50` gate did
(spec/research/F006-hypothesis-cooldown.md: -$363.67 -> -$215.40 mean net PnL,
a $148.27 improvement, but with flat per-trade expectancy).

No engine change: the one-shot rule is expressed entirely as the existing
`backtest_engine.run_backtest(entry_regime_mask=...)` parameter, built by
entry_masks.one_shot_entry_mask from the strategy's OWN signal series computed
through the engine's own pipeline (entry_masks.strategy_signal_series). The mask
construction is unit-tested in tests/test_entry_masks.py.

Grid: mask in {one_shot, none(control)} x cooldown_candles in {0, 50} x 12 signal
names x 5 symbols x 2 intervals = 480 runs. cooldown=0 isolates the pure one-shot
effect against the recorded cooldown=0 baseline; cooldown=50 shows whether the two
gates compound or one subsumes the other. The unmasked control runs in the SAME
process over the SAME frames, so the comparison never depends on the other notes'
stored numbers -- though those are cross-checked too (see verify_control_rows).

TWO PASSES, ONE SCHEMA -- identical split to scripts/f006_cooldown_experiment.py,
because advanced-ta (lorentzian.py) needs Python >=3.10:

    .venv_test/bin/python        scripts/f006_one_shot_experiment.py --catalog
    .venv_lorentzian/bin/python  scripts/f006_one_shot_experiment.py --lorentzian
    <either>/bin/python          scripts/f006_one_shot_experiment.py --merge

Scope discipline, same as every F006 script: the frozen protocol-scoped cache is
checksum-verified against spec/research/F005-validation-protocol.md section 6 and
sliced to [2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z) -- warm-up + Train 1 only --
before run_backtest ever sees it. Validation 1-4 and Holdout are never loaded.

Reads strategy.py/backtest_engine.py/data_contract.py/lorentzian.py and changes
none of them. Writes only new files (this script, output/f006_one_shot/, the
research note, entry_masks.py, its test). Zero network connections.
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
import strategy  # noqa: E402

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]

WARMUP_START = "2024-01-26T00:00:00Z"
HOLDOUT_END = "2026-09-01T00:00:00Z"
TRAIN1_END = pd.Timestamp("2025-03-01T00:00:00Z")
NOW = TRAIN1_END  # fixed, not wall-clock -- filter_closed_candles stays deterministic

# spec/research/F005-validation-protocol.md section 6 -- same table as
# scripts/f006_stop_width_experiment.py / scripts/f006_cooldown_experiment.py,
# duplicated (not imported) so this script verifies independently before using cache.
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

# The 10-strategy sample of spec/research/F006-hypothesis-stop-width.md, verbatim.
CATALOG_SAMPLE = [
    "EMA_8_21", "EMA_13_34_RSI14_55", "RSI14_7030", "MACD_12_26_hist", "MACD_RSI14_50",
    "BB_20_25_breakout", "BB_20_2_RSI14", "ADX14_DI_20", "STOCH14_cross", "TS_13_34_200_14",
]
LORENTZIAN_SAMPLE = ["LORENTZIAN_default", "LORENTZIAN_raw"]

COOLDOWN_SWEEP = [0, 50]
MASK_MODES = ["none", "one_shot"]  # "none" = the unmasked control, run side by side

# Identical fixed block to scripts/f006_cooldown_experiment.py (itself the
# stop-width experiment's block at max_sl_pct=0.03), minus the swept dimensions.
FIXED_PARAMS = dict(
    leverage=1.0,
    atr_multiplier=1.5,
    activate_pct=0.03,
    trail_pct=0.02,
    commission_rate_bps=10.0,
    half_spread_bps=5.0,
    slippage_bps=2.0,
)
MAX_SL_PCT = 0.03
INITIAL_EQUITY = 500.0
STAKE = 100.0
REENTRY_FLOOR = 100.0

OUT_DIR = "output/f006_one_shot/summary"
# The unmasked control rows must reproduce the stored prior runs exactly -- same
# engine, same fixed params, same data slice. cooldown=0 controls vs the
# stop-width/Lorentzian results, cooldown=50 controls vs the cooldown sweep.
STOP_WIDTH_RESULTS = "output/f006_stop_width/summary/results.csv"
LORENTZIAN_RESULTS = "output/f006_lorentzian/summary/results.csv"
COOLDOWN_RESULTS = "output/f006_cooldown/summary/results.csv"


def _run_one(df, mask, symbol, interval, strategy_name, mask_mode, cooldown, n_calls, group) -> dict:
    t0 = time.time()
    result = backtest_engine.run_backtest(
        df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE, max_sl_pct=MAX_SL_PCT,
        cooldown_candles=cooldown,
        entry_regime_mask=(mask if mask_mode == "one_shot" else None),
        **FIXED_PARAMS,
    )
    m = result.metrics
    trades = result.trades
    n_initial_sl = int((trades["exit_reason"] == "initial_sl").sum()) if len(trades) else 0
    # gross/costs are kept for the same reason as the cooldown experiment: to split
    # "saved round-trip costs" from "avoided genuinely bad trades". n_calls lets the
    # note report trades-per-call, the quantity the Lorentzian note measured at 4-5.
    gross_sum = float(trades["gross_pnl"].sum()) if len(trades) else 0.0
    costs_sum = float(trades["total_costs"].sum()) if len(trades) else 0.0
    return {
        "group": group,
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "mask_mode": mask_mode,
        "cooldown_candles": cooldown,
        "max_sl_pct": MAX_SL_PCT,
        "n_calls": n_calls,
        "net_pnl": m["total_net_pnl"],
        "gross_pnl": round(gross_sum, 6),
        "total_costs": round(costs_sum, 6),
        "win_rate": m["win_rate"],
        "n_trades": int(len(trades)),
        "n_initial_sl_exits": n_initial_sl,
        "max_drawdown_pct": m["max_drawdown_pct"],
        "final_equity": m["final_equity"],
        "survived": bool(m["final_equity"] >= REENTRY_FLOOR),
        "seconds": round(time.time() - t0, 2),
    }


def load_train1(symbol: str, interval: str) -> pd.DataFrame:
    """Checksum-verified protocol cache, sliced to warm-up + Train 1 only."""
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


def verify_control_rows(results: pd.DataFrame, stored_path: str, names: list,
                        cooldown: int, stored_filter: dict) -> dict:
    """Unmasked control rows vs a stored prior experiment's rows for the same config."""
    if not os.path.exists(stored_path):
        return {"checked": False, "reason": f"{stored_path} not found"}
    stored = pd.read_csv(stored_path)
    stored = stored[stored["strategy"].isin(names)].copy()
    for col, val in stored_filter.items():
        stored = stored[stored[col] == val]
    stored["interval"] = stored["interval"].astype(str)  # CSV reads "240" back as int64
    mine = results[(results["mask_mode"] == "none") & (results["cooldown_candles"] == cooldown)
                   & (results["strategy"].isin(names))].copy()
    mine["interval"] = mine["interval"].astype(str)
    merged = mine.merge(stored, on=["symbol", "interval", "strategy"], suffixes=("_new", "_stored"))
    mismatches = []
    for col in ("net_pnl", "win_rate", "n_trades", "max_drawdown_pct", "final_equity"):
        bad = merged[merged[f"{col}_new"] != merged[f"{col}_stored"]]
        for _, row in bad.iterrows():
            mismatches.append({
                "symbol": row["symbol"], "interval": row["interval"], "strategy": row["strategy"],
                "column": col, "new": row[f"{col}_new"], "stored": row[f"{col}_stored"],
            })
    return {"checked": True, "stored_path": stored_path, "cooldown_candles": cooldown,
            "stored_filter": stored_filter, "rows_compared": int(len(merged)),
            "mismatches": mismatches}


def _all_cross_checks(results_df: pd.DataFrame, names: list, group: str) -> dict:
    stored_path = STOP_WIDTH_RESULTS if group == "catalog" else LORENTZIAN_RESULTS
    return {
        "control_cooldown0_vs_prior_experiment": verify_control_rows(
            results_df, stored_path, names, 0, {"max_sl_pct": MAX_SL_PCT}),
        "control_cooldown50_vs_cooldown_sweep": verify_control_rows(
            results_df, COOLDOWN_RESULTS, names, 50, {"cooldown_candles": 50}),
    }


def run_pass(group: str) -> pd.DataFrame:
    """One interpreter's share of the grid: `catalog` (py3.9 ok) or `lorentzian` (needs >=3.10)."""
    names = CATALOG_SAMPLE if group == "catalog" else LORENTZIAN_SAMPLE
    if group == "lorentzian":
        import lorentzian  # noqa: F401  -- registers LORENTZIAN_* in strategy.STRATEGY_CATALOG
    for name in names:
        assert name in strategy.STRATEGY_CATALOG, f"strategy {name!r} not in strategy.STRATEGY_CATALOG"

    t_start = time.time()
    rows = []
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            train1_df = load_train1(symbol, interval)
            for name in names:
                # One signal computation per (symbol, interval, name); the mask is a
                # pure function of it, so both cooldown values reuse the same object.
                sig = entry_masks.strategy_signal_series(train1_df, name, interval=interval, now=NOW)
                mask = entry_masks.one_shot_entry_mask(sig)
                n_calls = int(mask.sum())
                for mask_mode in MASK_MODES:
                    for cooldown in COOLDOWN_SWEEP:
                        rows.append(_run_one(train1_df, mask, symbol, interval, name,
                                             mask_mode, cooldown, n_calls, group))
            print(f"done {group} {symbol}/{interval} ({len(rows)} runs, {time.time() - t_start:.1f}s elapsed)")

    os.makedirs(OUT_DIR, exist_ok=True)
    results_df = pd.DataFrame(rows)
    results_df.to_csv(f"{OUT_DIR}/results_{group}.csv", index=False)

    checks = _all_cross_checks(results_df, names, group)
    with open(f"{OUT_DIR}/manifest_{group}.json", "w") as f:
        json.dump(_manifest(group, names, results_df, t_start, checks), f, indent=2)

    for key, v in checks.items():
        print(f"{group} {key}: {v.get('rows_compared')} rows, {len(v.get('mismatches', []))} mismatches")
    _print_means(results_df, group)
    return results_df


def _manifest(group, names, results_df, t_start, extra) -> dict:
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None
    return {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit_parent": commit_sha,
        "group": group,
        "python_version": sys.version.split()[0],
        "pandas_version": pd.__version__,
        "n_runs": int(len(results_df)),
        "strategy_names": names,
        "mask_modes": MASK_MODES,
        "cooldown_sweep": COOLDOWN_SWEEP,
        "symbols": SYMBOLS,
        "intervals": INTERVALS,
        "fixed_params": {**FIXED_PARAMS, "max_sl_pct": MAX_SL_PCT,
                         "initial_equity": INITIAL_EQUITY, "stake": STAKE},
        "warmup_start": WARMUP_START,
        "train1_end": str(TRAIN1_END),
        "now_fixed": str(NOW),
        "data_checksums_verified": {f"{s}_{i}": c for (s, i), c in EXPECTED_CHECKSUMS.items()},
        "elapsed_seconds": round(time.time() - t_start, 1),
        **extra,
    }


def _cell(df: pd.DataFrame, mask_mode: str, cooldown: int) -> pd.DataFrame:
    return df[(df["mask_mode"] == mask_mode) & (df["cooldown_candles"] == cooldown)]


def _print_means(results_df: pd.DataFrame, label: str) -> None:
    print(f"\n-- {label}: means by (mask_mode, cooldown) --")
    for mask_mode in MASK_MODES:
        for cooldown in COOLDOWN_SWEEP:
            sub = _cell(results_df, mask_mode, cooldown)
            if sub.empty:
                continue
            per_trade = (sub["net_pnl"] / sub["n_trades"].replace(0, pd.NA)).mean()
            print(f"{mask_mode:>8} cd={cooldown:>2}: net_pnl={sub['net_pnl'].mean():9.2f}  "
                  f"per_trade={per_trade:7.3f}  win_rate={sub['win_rate'].mean():6.2f}%  "
                  f"n_trades={sub['n_trades'].mean():7.1f}  maxDD={sub['max_drawdown_pct'].mean():6.2f}%  "
                  f"survived={int(sub['survived'].sum())}/{len(sub)}  "
                  f"positive={int((sub['net_pnl'] > 0).sum())}/{len(sub)}")


def merge() -> pd.DataFrame:
    """Concatenate both passes into one results.csv + manifest.json, re-checking everything."""
    parts = []
    for group in ("catalog", "lorentzian"):
        path = f"{OUT_DIR}/results_{group}.csv"
        if not os.path.exists(path):
            raise SystemExit(f"STOP: {path} missing -- run the {group} pass first.")
        part = pd.read_csv(path)
        part["interval"] = part["interval"].astype(str)
        parts.append(part)
    results_df = pd.concat(parts, ignore_index=True)
    results_df.to_csv(f"{OUT_DIR}/results.csv", index=False)

    manifests = {}
    for group in ("catalog", "lorentzian"):
        with open(f"{OUT_DIR}/manifest_{group}.json") as f:
            manifests[group] = json.load(f)
    merged_manifest = _manifest(
        "merged", CATALOG_SAMPLE + LORENTZIAN_SAMPLE, results_df, time.time(),
        {
            "pass_manifests": manifests,
            "cross_checks_catalog": _all_cross_checks(results_df, CATALOG_SAMPLE, "catalog"),
            "cross_checks_lorentzian": _all_cross_checks(results_df, LORENTZIAN_SAMPLE, "lorentzian"),
            "means_by_cell": _means_table(results_df),
            "means_by_cell_catalog": _means_table(results_df[results_df["group"] == "catalog"]),
            "means_by_cell_lorentzian": _means_table(results_df[results_df["group"] == "lorentzian"]),
            "means_by_cell_4h": _means_table(results_df[results_df["interval"] == "240"]),
            "means_by_cell_1h": _means_table(results_df[results_df["interval"] == "60"]),
            "means_by_strategy_cell": _per_strategy_table(results_df),
        },
    )
    merged_manifest["elapsed_seconds"] = None  # merge is not a timed run
    with open(f"{OUT_DIR}/manifest.json", "w") as f:
        json.dump(merged_manifest, f, indent=2)

    _print_means(results_df, "ALL (12 names)")
    _print_means(results_df[results_df["group"] == "catalog"], "catalog (10 names)")
    _print_means(results_df[results_df["group"] == "lorentzian"], "lorentzian (2 names)")
    _print_means(results_df[results_df["interval"] == "240"], "4h only")
    _print_means(results_df[results_df["interval"] == "60"], "1h only")
    for key in ("cross_checks_catalog", "cross_checks_lorentzian"):
        for sub_key, v in merged_manifest[key].items():
            print(f"{key}/{sub_key}: {v.get('rows_compared')} rows compared, "
                  f"{len(v.get('mismatches', []))} mismatches")
    return results_df


def _cell_stats(sub: pd.DataFrame) -> dict:
    return {
        "mean_net_pnl": round(float(sub["net_pnl"].mean()), 2),
        "mean_gross_pnl": round(float(sub["gross_pnl"].mean()), 2),
        "mean_total_costs": round(float(sub["total_costs"].mean()), 2),
        "mean_net_pnl_per_trade": round(float((sub["net_pnl"] / sub["n_trades"].replace(0, pd.NA)).mean()), 4),
        "mean_win_rate": round(float(sub["win_rate"].mean()), 2),
        "mean_n_trades": round(float(sub["n_trades"].mean()), 1),
        "mean_n_calls": round(float(sub["n_calls"].mean()), 1),
        "mean_trades_per_call": round(float((sub["n_trades"] / sub["n_calls"]).mean()), 3),
        "mean_n_initial_sl_exits": round(float(sub["n_initial_sl_exits"].mean()), 1),
        "mean_max_drawdown_pct": round(float(sub["max_drawdown_pct"].mean()), 2),
        "survived": int(sub["survived"].sum()),
        "n": int(len(sub)),
        "positive_net_pnl": int((sub["net_pnl"] > 0).sum()),
        "best_net_pnl": round(float(sub["net_pnl"].max()), 2),
    }


def _means_table(df: pd.DataFrame) -> list:
    out = []
    for mask_mode in MASK_MODES:
        for cooldown in COOLDOWN_SWEEP:
            sub = _cell(df, mask_mode, cooldown)
            if sub.empty:
                continue
            out.append({"mask_mode": mask_mode, "cooldown_candles": cooldown, **_cell_stats(sub)})
    return out


def _per_strategy_table(df: pd.DataFrame) -> dict:
    out = {}
    for name in sorted(df["strategy"].unique()):
        sub_name = df[df["strategy"] == name]
        out[name] = {
            f"{mask_mode}_cd{cooldown}": _cell_stats(s)
            for mask_mode in MASK_MODES
            for cooldown in COOLDOWN_SWEEP
            for s in [_cell(sub_name, mask_mode, cooldown)]
            if not s.empty
        }
    return out


def main(argv) -> None:
    mode = argv[1].lstrip("-") if len(argv) > 1 else "all"
    if mode in ("catalog", "lorentzian"):
        run_pass(mode)
    elif mode == "merge":
        merge()
    elif mode == "all":
        run_pass("catalog")
        run_pass("lorentzian")
        merge()
    else:
        raise SystemExit(f"usage: {argv[0]} [--catalog|--lorentzian|--merge|--all]")


if __name__ == "__main__":
    main(sys.argv)
