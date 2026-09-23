"""
F006 -- re-entry cooldown hypothesis experiment, TRAIN 1 ONLY.

Tests the hypothesis in spec/research/F006-hypothesis-cooldown.md: that
backtest_engine.run_backtest's existing cooldown_candles gate (loop step 2 ->
step 4: after an "initial_sl" exit no new entry is queued for cooldown_candles
bars) suppresses the wasteful re-entry chains measured in
spec/research/F006-lorentzian-causality.md (4-5 executed trades per directional
call at 4h) and thereby improves net PnL at leverage=1 -- the one combination
spec/research/F005-leverage-sensitivity.md's cooldown sweep never tested
(it swept cooldown only at leverage=10).

Grid: cooldown_candles in {0, 5, 10, 20, 50} x 12 signal names x 5 symbols x
2 intervals = 600 runs. The 12 names are the 10-strategy sample of
spec/research/F006-hypothesis-stop-width.md plus LORENTZIAN_default and
LORENTZIAN_raw (added to strategy.STRATEGY_CATALOG by the already-merged
lorentzian.py). Everything else is held at the stop-width experiment's fixed
block, at its max_sl_pct=0.03 row, so the cooldown=0 rows are directly
comparable with -- and are checked against -- the stored results of the two
prior experiments.

TWO PASSES, ONE SCHEMA. advanced-ta (needed by lorentzian.py) declares
Requires-Python >=3.10, so the LORENTZIAN_* rows cannot run on the project's
Python 3.9 .venv_test. The grid is therefore split by interpreter:

    .venv_test/bin/python        scripts/f006_cooldown_experiment.py --catalog
    .venv_lorentzian/bin/python  scripts/f006_cooldown_experiment.py --lorentzian
    <either>/bin/python          scripts/f006_cooldown_experiment.py --merge

Both passes write the SAME row schema to output/f006_cooldown/summary/
(results_catalog.csv / results_lorentzian.csv, each with its own manifest);
`--merge` concatenates them into results.csv + manifest.json and re-runs the
cross-checks over the union. Running `--all` on a >=3.10 interpreter does both
passes plus the merge in one process. (The mode flags are dashed on purpose:
strategy.py reads a bare sys.argv[1] as its config path at import time.)

Scope discipline, identical to scripts/f006_stop_width_experiment.py and
scripts/f006_lorentzian_experiment.py: the frozen protocol-scoped cache is
loaded and checksum-verified against spec/research/F005-validation-protocol.md
section 6, then sliced to [2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z) --
warm-up + Train 1 only -- before run_backtest ever sees it. Validation 1-4 and
Holdout are never loaded into a run, and regularity is not computed.

Reads strategy.py/backtest_engine.py/data_contract.py/lorentzian.py and
changes none of them: cooldown_candles is already a run_backtest parameter, so
this experiment needs no engine change. Writes only new files (this script,
output/f006_cooldown/, the research note). Zero network connections.
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
import strategy  # noqa: E402

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]

WARMUP_START = "2024-01-26T00:00:00Z"
HOLDOUT_END = "2026-09-01T00:00:00Z"
TRAIN1_END = pd.Timestamp("2025-03-01T00:00:00Z")
NOW = TRAIN1_END  # fixed, not wall-clock -- filter_closed_candles stays deterministic

# spec/research/F005-validation-protocol.md section 6 -- same table as
# scripts/f006_stop_width_experiment.py and scripts/f006_lorentzian_experiment.py,
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

COOLDOWN_SWEEP = [0, 5, 10, 20, 50]

# Identical to the stop-width experiment's fixed block at its max_sl_pct=0.03 row
# (which is also the Lorentzian comparison run's block), minus cooldown_candles,
# which is this experiment's swept dimension.
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

OUT_DIR = "output/f006_cooldown/summary"
# cooldown=0 rows must reproduce these stored runs exactly (same engine, same
# fixed params, same data slice) -- the strongest available check that this
# grid is comparable with the prior two experiments rather than merely similar.
STOP_WIDTH_RESULTS = "output/f006_stop_width/summary/results.csv"
LORENTZIAN_RESULTS = "output/f006_lorentzian/summary/results.csv"


def _run_one(df, symbol, interval, strategy_name, cooldown, group) -> dict:
    t0 = time.time()
    result = backtest_engine.run_backtest(
        df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE, max_sl_pct=MAX_SL_PCT,
        cooldown_candles=cooldown, **FIXED_PARAMS,
    )
    m = result.metrics
    trades = result.trades
    n_initial_sl = int((trades["exit_reason"] == "initial_sl").sum()) if len(trades) else 0
    # gross_pnl / total_costs are summed per run so the note can separate "cooldown
    # saved round-trip costs" (total_costs falls with n_trades) from "cooldown avoided
    # genuinely bad re-entries" (gross_pnl improves) -- the exact distinction
    # spec/research/F006-hypothesis-entry-regime-filter.md could not make.
    gross_sum = float(trades["gross_pnl"].sum()) if len(trades) else 0.0
    costs_sum = float(trades["total_costs"].sum()) if len(trades) else 0.0
    return {
        "group": group,
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "cooldown_candles": cooldown,
        "max_sl_pct": MAX_SL_PCT,
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


def verify_cooldown_zero(results: pd.DataFrame, stored_path: str, names: list) -> dict:
    """cooldown=0 rows vs a stored prior experiment's rows for the same names."""
    if not os.path.exists(stored_path):
        return {"checked": False, "reason": f"{stored_path} not found"}
    stored = pd.read_csv(stored_path)
    stored = stored[(stored["max_sl_pct"] == MAX_SL_PCT) & (stored["strategy"].isin(names))].copy()
    stored["interval"] = stored["interval"].astype(str)  # CSV reads "240" back as int64
    mine = results[(results["cooldown_candles"] == 0) & (results["strategy"].isin(names))].copy()
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
    return {"checked": True, "stored_path": stored_path,
            "rows_compared": int(len(merged)), "mismatches": mismatches}


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
                for cooldown in COOLDOWN_SWEEP:
                    rows.append(_run_one(train1_df, symbol, interval, name, cooldown, group))
            print(f"done {group} {symbol}/{interval} ({len(rows)} runs, {time.time() - t_start:.1f}s elapsed)")

    os.makedirs(OUT_DIR, exist_ok=True)
    results_df = pd.DataFrame(rows)
    results_df.to_csv(f"{OUT_DIR}/results_{group}.csv", index=False)

    stored_path = STOP_WIDTH_RESULTS if group == "catalog" else LORENTZIAN_RESULTS
    verification = verify_cooldown_zero(results_df, stored_path, names)
    with open(f"{OUT_DIR}/manifest_{group}.json", "w") as f:
        json.dump(_manifest(group, names, results_df, t_start, {"cooldown_zero_cross_check": verification}), f, indent=2)

    print(f"\n{group} cooldown=0 cross-check vs {stored_path}: "
          f"{verification.get('rows_compared')} rows, "
          f"{len(verification.get('mismatches', []))} mismatches")
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


def _print_means(results_df: pd.DataFrame, label: str) -> None:
    print(f"\n-- {label}: means by cooldown_candles --")
    for cooldown in COOLDOWN_SWEEP:
        sub = results_df[results_df["cooldown_candles"] == cooldown]
        if sub.empty:
            continue
        print(f"cooldown={cooldown:>3}: net_pnl={sub['net_pnl'].mean():9.2f}  "
              f"win_rate={sub['win_rate'].mean():6.2f}%  n_trades={sub['n_trades'].mean():7.1f}  "
              f"maxDD={sub['max_drawdown_pct'].mean():6.2f}%  "
              f"survived={int(sub['survived'].sum())}/{len(sub)}  "
              f"positive={int((sub['net_pnl'] > 0).sum())}/{len(sub)}")


def merge() -> pd.DataFrame:
    """Concatenate both passes into one results.csv + manifest.json, re-checking both cross-checks."""
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
            "cooldown_zero_cross_check_catalog": verify_cooldown_zero(
                results_df, STOP_WIDTH_RESULTS, CATALOG_SAMPLE),
            "cooldown_zero_cross_check_lorentzian": verify_cooldown_zero(
                results_df, LORENTZIAN_RESULTS, LORENTZIAN_SAMPLE),
            "means_by_cooldown": _means_table(results_df),
            "means_by_cooldown_catalog": _means_table(results_df[results_df["group"] == "catalog"]),
            "means_by_cooldown_lorentzian": _means_table(results_df[results_df["group"] == "lorentzian"]),
            "means_by_strategy_cooldown": _per_strategy_table(results_df),
        },
    )
    merged_manifest["elapsed_seconds"] = None  # merge is not a timed run
    with open(f"{OUT_DIR}/manifest.json", "w") as f:
        json.dump(merged_manifest, f, indent=2)

    _print_means(results_df, "ALL (12 names)")
    _print_means(results_df[results_df["group"] == "catalog"], "catalog (10 names)")
    _print_means(results_df[results_df["group"] == "lorentzian"], "lorentzian (2 names)")
    for key in ("cooldown_zero_cross_check_catalog", "cooldown_zero_cross_check_lorentzian"):
        v = merged_manifest[key]
        print(f"{key}: {v.get('rows_compared')} rows compared, "
              f"{len(v.get('mismatches', []))} mismatches")
    return results_df


def _means_table(df: pd.DataFrame) -> list:
    out = []
    for cooldown in COOLDOWN_SWEEP:
        sub = df[df["cooldown_candles"] == cooldown]
        if sub.empty:
            continue
        out.append({
            "cooldown_candles": cooldown,
            "mean_net_pnl": round(float(sub["net_pnl"].mean()), 2),
            "mean_gross_pnl": round(float(sub["gross_pnl"].mean()), 2),
            "mean_total_costs": round(float(sub["total_costs"].mean()), 2),
            "mean_net_pnl_per_trade": round(float((sub["net_pnl"] / sub["n_trades"]).mean()), 4),
            "mean_win_rate": round(float(sub["win_rate"].mean()), 2),
            "mean_n_trades": round(float(sub["n_trades"].mean()), 1),
            "mean_n_initial_sl_exits": round(float(sub["n_initial_sl_exits"].mean()), 1),
            "mean_max_drawdown_pct": round(float(sub["max_drawdown_pct"].mean()), 2),
            "survived": int(sub["survived"].sum()),
            "n": int(len(sub)),
            "positive_net_pnl": int((sub["net_pnl"] > 0).sum()),
        })
    return out


def _per_strategy_table(df: pd.DataFrame) -> dict:
    out = {}
    for name in sorted(df["strategy"].unique()):
        sub_name = df[df["strategy"] == name]
        out[name] = {
            str(cooldown): {
                "mean_net_pnl": round(float(s["net_pnl"].mean()), 2),
                "mean_win_rate": round(float(s["win_rate"].mean()), 2),
                "mean_n_trades": round(float(s["n_trades"].mean()), 1),
                "survived": int(s["survived"].sum()),
                "n": int(len(s)),
            }
            for cooldown in COOLDOWN_SWEEP
            for s in [sub_name[sub_name["cooldown_candles"] == cooldown]]
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
