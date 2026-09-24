"""
F006 -- catalog-wide NO_TRAIL sweep, TRAIN 1 ONLY. EXPLORATORY, not a pre-registered
falsifiable hypothesis in the strict sense every other F006 note uses.

spec/research/F006-hypothesis-exit-take-profit.md closed out the entry/exit/sizing axis
for the three original NO_TRAIL leads (DONCHIAN_55, BB_20_25_breakout,
DONCHIAN_PULLBACK_55) -- six independent mechanisms all falsified at that exit geometry.
spec/research/F006-hypothesis-trailing-boundary.md's 8-name sample (chosen for family
coverage, not exhaustiveness -- see that note's "Sample" section) is the only slice ever
run at NO_TRAIL, out of strategy.STRATEGY_CATALOG's 85 names. This script runs the other
~77 names through the exact same NO_TRAIL exit geometry, at the aggregate (pooled)
level only, to find whether any OTHER catalog name is aggregate-Train-1-positive and
worth a future monthly-criterion check (the same check
spec/research/F006-hypothesis-notrail-monthly.md ran for the original 3). It does NOT run
that monthly check itself, and aggregate-positive is explicitly NOT the promotion bar --
see spec/research/F006-catalog-notrail-sweep.md's "Scope" section.

Exit geometry (identical to every NO_TRAIL cell used elsewhere in F006, unchanged):
activate_pct=10.0 (unreachable in Train 1, so backtest_engine._update_trailing's arming
condition never fires and trail_active stays False for the life of every trade),
trail_pct irrelevant (recorded as None), max_sl_pct=0.03, one-shot entry mask,
cooldown_candles=0, leverage=1.

TWO PASSES, ONE SCHEMA, same split as every other F006 script:

    .venv_test/bin/python        scripts/f006_catalog_notrail_sweep.py --catalog
    .venv_lorentzian/bin/python  scripts/f006_catalog_notrail_sweep.py --lorentzian
    <either>/bin/python          scripts/f006_catalog_notrail_sweep.py --merge

Per spec/research/F006-hypothesis-one-shot-entry.md's Run_id recipe: Lorentzian variants
beyond LORENTZIAN_default (already tested) and LORENTZIAN_raw are excluded -- only
LORENTZIAN_raw is new here, and it is cheap (one name, 10 series), so it is included.

HARNESS CONTROL: DONCHIAN_55 (one of the 8 already-tested names) is re-run at NO_TRAIL in
this script and diffed row by row against the stored NO_TRAIL rows of
output/f006_trailing_boundary/summary/results.csv, to prove this script's numbers agree
with the established harness before trusting any of the 77 new names.

Scope discipline, same as every F006 script: the frozen protocol-scoped cache is
checksum-verified against spec/research/F005-validation-protocol.md section 6 and
sliced to [2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z) -- warm-up + Train 1 only --
before run_backtest ever sees it. Validation 1-4 and Holdout are never loaded.

Reads strategy.py/backtest_engine.py/data_contract.py/entry_masks.py/donchian.py/
lorentzian.py/trade_stats.py and changes none of them. Writes only
output/f006_catalog_notrail_sweep/. Zero network connections.
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
import trade_stats  # noqa: E402

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]

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

# Names already run at NO_TRAIL by spec/research/F006-hypothesis-trailing-boundary.md.
# Not re-run here (except CONTROL_NAME, for the harness-control diff).
ALREADY_TESTED_AT_NO_TRAIL = [
    "EMA_8_21", "MACD_12_26_hist", "RSI14_7030", "BB_20_25_breakout", "ADX14_DI_20",
    "LORENTZIAN_default", "DONCHIAN_55", "DONCHIAN_PULLBACK_55",
]
CONTROL_NAME = "DONCHIAN_55"  # harness control: re-run, diffed against the prior note's rows

ALL_CATALOG_NAMES = sorted(strategy.STRATEGY_CATALOG.keys())
NEW_NAMES = [n for n in ALL_CATALOG_NAMES if n not in ALREADY_TESTED_AT_NO_TRAIL]
LORENTZIAN_NEW_NAMES = [n for n in NEW_NAMES if n.startswith("LORENTZIAN")]
CATALOG_NEW_NAMES = [n for n in NEW_NAMES if not n.startswith("LORENTZIAN")]

CATALOG_PASS_NAMES = CATALOG_NEW_NAMES + [CONTROL_NAME]
LORENTZIAN_PASS_NAMES = LORENTZIAN_NEW_NAMES

# NO_TRAIL exit geometry, identical to every other F006 NO_TRAIL cell.
ACTIVATE_PCT = 10.0  # +1000% -- unreachable in Train 1, trail never arms
TRAIL_PCT = 0.04  # moot: arming condition never fires; recorded as None

FIXED_PARAMS = dict(
    leverage=1.0,
    atr_multiplier=1.5,
    commission_rate_bps=10.0,
    half_spread_bps=5.0,
    slippage_bps=2.0,
)
MAX_SL_PCT = 0.03
COOLDOWN = 0
INITIAL_EQUITY = 500.0
STAKE = 100.0
REENTRY_FLOOR = 100.0

OUT_DIR = "output/f006_catalog_notrail_sweep/summary"
PRIOR_RESULTS = "output/f006_trailing_boundary/summary/results.csv"

DECOMP_COLUMNS = ["n_wins", "n_losses", "sum_wins", "sum_losses",
                  "avg_winner", "avg_loser", "breakeven_win_rate_pct"]

TOP_N_CANDIDATES = 5


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


def _mean_bars_held(trades: pd.DataFrame, interval: str) -> float:
    if not len(trades):
        return 0.0
    span = pd.to_datetime(trades["exit_time"]) - pd.to_datetime(trades["entry_time"])
    return round(float((span.dt.total_seconds() / 60.0 / int(interval)).mean()), 2)


def _run_one(df, mask, symbol, interval, strategy_name, n_calls) -> dict:
    t0 = time.time()
    result = backtest_engine.run_backtest(
        df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT,
        cooldown_candles=COOLDOWN,
        entry_regime_mask=mask,
        **FIXED_PARAMS,
    )
    m = result.metrics
    trades = result.trades
    d = trade_stats.win_loss_decomposition(trades)
    exit_mix = trades["exit_reason"].value_counts().to_dict() if len(trades) else {}
    return {
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "activate_pct": ACTIVATE_PCT, "trail_pct": None, "no_trail": True,
        "max_sl_pct": MAX_SL_PCT, "cooldown_candles": COOLDOWN, "mask_mode": "one_shot",
        "n_calls": n_calls,
        "net_pnl": m["total_net_pnl"],
        "gross_pnl": round(float(trades["gross_pnl"].sum()) if len(trades) else 0.0, 6),
        "total_costs": round(float(trades["total_costs"].sum()) if len(trades) else 0.0, 6),
        "win_rate": m["win_rate"],
        "n_trades": int(len(trades)),
        "n_wins": d["n_wins"], "n_losses": d["n_losses"],
        "sum_wins": round(d["sum_wins"], 6), "sum_losses": round(d["sum_losses"], 6),
        "avg_winner": round(d["avg_winner"], 6),
        "avg_loser": round(d["avg_loser"], 6),
        "breakeven_win_rate_pct": (round(d["breakeven_win_rate_pct"], 4)
                                   if d["breakeven_win_rate_pct"] is not None else None),
        "mean_bars_held": _mean_bars_held(trades, interval),
        "exit_initial_sl": int(exit_mix.get("initial_sl", 0)),
        "exit_trailing_sl": int(exit_mix.get("trailing_sl", 0)),
        "exit_signal_reverse": int(exit_mix.get("signal_reverse", 0)),
        "exit_end_of_data": int(exit_mix.get("end_of_data", 0)),
        "max_drawdown_pct": m["max_drawdown_pct"],
        "final_equity": m["final_equity"],
        "survived": bool(m["final_equity"] >= REENTRY_FLOOR),
        "seconds": round(time.time() - t0, 2),
    }


def run_pass(names: list, tag: str) -> pd.DataFrame:
    for name in names:
        assert name in strategy.STRATEGY_CATALOG, f"strategy {name!r} not in strategy.STRATEGY_CATALOG"
    t_start = time.time()
    rows = []
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            train1_df = load_train1(symbol, interval)
            for name in names:
                sig = entry_masks.strategy_signal_series(train1_df, name, interval=interval, now=NOW)
                mask = entry_masks.one_shot_entry_mask(sig)
                n_calls = int(mask.sum())
                rows.append(_run_one(train1_df, mask, symbol, interval, name, n_calls))
            print(f"done {symbol}/{interval} ({len(rows)} runs, {time.time() - t_start:.1f}s elapsed)")
    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT_DIR}/results_{tag}.csv", index=False)
    with open(f"{OUT_DIR}/manifest_{tag}.json", "w") as f:
        json.dump(_manifest(df, t_start, {"pass": tag, "names": names}), f, indent=2)
    print(f"\n[{tag}] {len(df)} runs in {time.time() - t_start:.1f}s -> {OUT_DIR}/results_{tag}.csv")
    return df


# ---------------------------------------------------------------- checks

def verify_harness_control(results: pd.DataFrame) -> dict:
    """CONTROL_NAME's NO_TRAIL rows must reproduce the trailing-boundary note's stored rows."""
    mine = results[results["strategy"] == CONTROL_NAME].copy()
    mine["interval"] = mine["interval"].astype(str)
    if not os.path.exists(PRIOR_RESULTS):
        return {"rows_compared": 0, "n_mismatches": 0, "mismatches": [],
                "source": f"{PRIOR_RESULTS} MISSING -- not compared"}
    stored = pd.read_csv(PRIOR_RESULTS)
    stored["interval"] = stored["interval"].astype(str)
    stored = stored[(stored["strategy"] == CONTROL_NAME) & (stored["no_trail"])]
    merged = mine.merge(stored, on=["symbol", "interval", "strategy"], suffixes=("_new", "_stored"))
    mismatches = []
    for col in ("net_pnl", "win_rate", "n_trades", "max_drawdown_pct", "final_equity"):
        bad = merged[merged[f"{col}_new"] != merged[f"{col}_stored"]]
        for _, row in bad.iterrows():
            mismatches.append({"symbol": row["symbol"], "interval": row["interval"],
                               "strategy": row["strategy"], "column": col,
                               "new": row[f"{col}_new"], "stored": row[f"{col}_stored"]})
    return {"rows_compared": int(len(merged)), "n_mismatches": len(mismatches),
            "mismatches": mismatches[:20],
            "source": f"{len(merged)} rows vs {PRIOR_RESULTS} (control name {CONTROL_NAME!r})"}


def verify_no_trail_mechanism(results: pd.DataFrame) -> dict:
    bad = results[results["exit_trailing_sl"] > 0]
    return {"runs": int(len(results)), "runs_with_a_trailing_exit": int(len(bad)),
            "total_trailing_exits": int(results["exit_trailing_sl"].sum())}


def verify_one_shot_rule(results: pd.DataFrame) -> dict:
    violations = results[results["n_trades"] > results["n_calls"]]
    return {"runs": int(len(results)), "violations": int(len(violations))}


def verify_no_overlap_with_prior_sample(names_run: list) -> dict:
    overlap = sorted(set(names_run) & set(ALREADY_TESTED_AT_NO_TRAIL) - {CONTROL_NAME})
    return {"overlap_besides_control": overlap, "clean": len(overlap) == 0}


# ---------------------------------------------------------------- aggregation

def _pooled(sub: pd.DataFrame) -> dict:
    d = trade_stats.pool_decompositions(sub[["n_trades"] + DECOMP_COLUMNS].to_dict("records"))
    n = max(int(sub["n_trades"].sum()), 1)
    be_rate = d["breakeven_win_rate_pct"]
    win_rate = d["win_rate_pct"]
    return {
        "n_runs": int(len(sub)),
        "n_trades": int(sub["n_trades"].sum()),
        "avg_winner": round(d["avg_winner"], 4),
        "avg_loser": round(d["avg_loser"], 4),
        "reward_risk": round(d["avg_winner"] / abs(d["avg_loser"]), 4) if d["avg_loser"] else None,
        "breakeven_win_rate_pct": round(be_rate, 4) if be_rate is not None else None,
        "win_rate_pct": round(win_rate, 4) if win_rate is not None else None,
        "gap_pp": (round(be_rate - win_rate, 4)
                   if be_rate is not None and win_rate is not None else None),
        "net_per_trade": round(float(sub["net_pnl"].sum()) / n, 4),
        "gross_per_trade": round(float(sub["gross_pnl"].sum()) / n, 4),
        "mean_net_pnl": round(float(sub["net_pnl"].mean()), 2),
        "sum_net_pnl": round(float(sub["net_pnl"].sum()), 2),
        "mean_max_drawdown_pct": round(float(sub["max_drawdown_pct"].mean()), 2),
        "survived": int(sub["survived"].sum()),
        "positive_net_pnl_series": int((sub["net_pnl"] > 0).sum()),
    }


def _per_name_table(results: pd.DataFrame) -> dict:
    new_only = results[results["strategy"] != CONTROL_NAME]
    out = {}
    for name, sub in new_only.groupby("strategy"):
        out[name] = _pooled(sub)
    return out


def _rank_candidates(per_name: dict) -> dict:
    by_net = sorted(per_name.items(), key=lambda kv: kv[1]["sum_net_pnl"], reverse=True)
    # smaller gap_pp = actual win rate closer to (or above) the breakeven bar = better
    by_gap = sorted(
        [(k, v) for k, v in per_name.items() if v["gap_pp"] is not None],
        key=lambda kv: kv[1]["gap_pp"],
    )
    aggregate_positive = sorted(
        [(k, v) for k, v in per_name.items() if v["sum_net_pnl"] > 0],
        key=lambda kv: kv[1]["sum_net_pnl"], reverse=True,
    )
    top_by_net = [k for k, _ in by_net[:TOP_N_CANDIDATES]]
    top_by_gap = [k for k, _ in by_gap[:TOP_N_CANDIDATES]]
    return {
        "ranked_by_net_pnl": [{"strategy": k, **v} for k, v in by_net],
        "ranked_by_breakeven_gap": [{"strategy": k, **v} for k, v in by_gap],
        "aggregate_train1_positive_names": [k for k, _ in aggregate_positive],
        "n_aggregate_positive": len(aggregate_positive),
        "top_candidates_by_net_pnl": top_by_net,
        "top_candidates_by_breakeven_gap": top_by_gap,
        # union, in net-PnL rank order, capped at TOP_N_CANDIDATES*2 -- reported as the
        # flagged shortlist for a likely follow-up monthly check, not itself a promotion.
        "flagged_for_followup": [k for k, _ in by_net if k in set(top_by_net) | set(top_by_gap)][:TOP_N_CANDIDATES],
    }


def _manifest(results_df: pd.DataFrame, t_start: float, extra: dict) -> dict:
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit_sha = None
    return {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit_parent": commit_sha,
        "python_version": sys.version.split()[0],
        "pandas_version": pd.__version__,
        "n_runs": int(len(results_df)),
        "already_tested_at_no_trail": ALREADY_TESTED_AT_NO_TRAIL,
        "control_name": CONTROL_NAME,
        "new_names_count": len(NEW_NAMES),
        "catalog_pass_names": CATALOG_PASS_NAMES,
        "lorentzian_pass_names": LORENTZIAN_PASS_NAMES,
        "activate_pct": ACTIVATE_PCT, "trail_pct_recorded_as": None,
        "symbols": SYMBOLS, "intervals": INTERVALS,
        "fixed_params": {**FIXED_PARAMS, "max_sl_pct": MAX_SL_PCT, "cooldown_candles": COOLDOWN,
                         "initial_equity": INITIAL_EQUITY, "stake": STAKE},
        "warmup_start": WARMUP_START, "train1_end": str(TRAIN1_END),
        "elapsed_seconds": round(time.time() - t_start, 1),
        **extra,
    }


def merge() -> pd.DataFrame:
    t_start = time.time()
    parts = []
    for tag in ("catalog", "lorentzian"):
        path = f"{OUT_DIR}/results_{tag}.csv"
        if not os.path.exists(path):
            raise SystemExit(f"STOP: {path} missing -- run the --{tag} pass first.")
        parts.append(pd.read_csv(path))
    results = pd.concat(parts, ignore_index=True)
    results["interval"] = results["interval"].astype(str)
    expected = (len(CATALOG_PASS_NAMES) + len(LORENTZIAN_PASS_NAMES)) * len(SYMBOLS) * len(INTERVALS)
    assert len(results) == expected, f"expected {expected} runs, merged {len(results)}"
    results.to_csv(f"{OUT_DIR}/results.csv", index=False)

    names_run = sorted(results["strategy"].unique().tolist())
    checks = {
        "harness_control_vs_trailing_boundary": verify_harness_control(results),
        "no_trail_mechanism": verify_no_trail_mechanism(results),
        "one_shot_rule": verify_one_shot_rule(results),
        "no_overlap_with_prior_sample": verify_no_overlap_with_prior_sample(names_run),
    }
    per_name = _per_name_table(results)
    ranking = _rank_candidates(per_name)
    manifest = _manifest(results, t_start, {
        "pass": "merged", **checks,
        "per_name_aggregate": per_name,
        "ranking": ranking,
    })
    with open(f"{OUT_DIR}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    _print_report(checks, ranking)
    return results


def _print_report(checks, ranking) -> None:
    h = checks["harness_control_vs_trailing_boundary"]
    print(f"\nharness control ({CONTROL_NAME} vs prior boundary note): {h['rows_compared']} rows "
          f"compared, {h['n_mismatches']} mismatches ({h.get('source')})")
    nt = checks["no_trail_mechanism"]
    print(f"no_trail mechanism: {nt['runs']} runs, {nt['runs_with_a_trailing_exit']} with a "
          f"trailing exit, {nt['total_trailing_exits']} trailing exits total (expect 0)")
    print(f"one-shot rule violations: {checks['one_shot_rule']['violations']}/"
          f"{checks['one_shot_rule']['runs']}")
    ov = checks["no_overlap_with_prior_sample"]
    print(f"overlap with already-tested sample (besides control): {ov['overlap_besides_control']} "
          f"(clean: {ov['clean']})")

    print(f"\n{ranking['n_aggregate_positive']}/{len(ranking['ranked_by_net_pnl'])} new names "
          f"are aggregate-Train-1-positive at NO_TRAIL:")
    for name in ranking["aggregate_train1_positive_names"]:
        v = next(r for r in ranking["ranked_by_net_pnl"] if r["strategy"] == name)
        print(f"  {name:>24}  sum_net_pnl=${v['sum_net_pnl']:>10.2f}  "
              f"profitable_series={v['positive_net_pnl_series']}/10  gap_pp={v['gap_pp']}")

    print(f"\ntop {TOP_N_CANDIDATES} by net PnL:")
    for r in ranking["ranked_by_net_pnl"][:TOP_N_CANDIDATES]:
        print(f"  {r['strategy']:>24}  sum_net_pnl=${r['sum_net_pnl']:>10.2f}  "
              f"gap_pp={r['gap_pp']:>7}  n_trades={r['n_trades']}")

    print(f"\ntop {TOP_N_CANDIDATES} by breakeven-win-rate gap (smaller = closer to/above breakeven):")
    for r in ranking["ranked_by_breakeven_gap"][:TOP_N_CANDIDATES]:
        print(f"  {r['strategy']:>24}  gap_pp={r['gap_pp']:>7}  sum_net_pnl=${r['sum_net_pnl']:>10.2f}")

    print(f"\nflagged for follow-up monthly check: {ranking['flagged_for_followup']}")
    print("CAVEAT: aggregate Train-1-positive is NOT the monthly promotion criterion. No name here "
          "has had a monthly PnL breakdown run -- see spec/research/F006-hypothesis-notrail-monthly.md "
          "for what that check looks like and why it is required before any promotion.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--catalog":
        run_pass(CATALOG_PASS_NAMES, "catalog")
    elif mode == "--lorentzian":
        run_pass(LORENTZIAN_PASS_NAMES, "lorentzian")
    elif mode == "--merge":
        merge()
    else:
        raise SystemExit("usage: f006_catalog_notrail_sweep.py --catalog | --lorentzian | --merge")
