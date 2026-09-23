"""
F006 -- Donchian breakout / pullback-after-breakout family, TRAIN 1 ONLY.

Tests the hypothesis in spec/research/F006-hypothesis-donchian.md: that a generator
built on realised N-bar extremes (no smoothing anywhere) escapes the negative
per-trade expectancy every smoothed-state name in STRATEGY_CATALOG has shown across
five prior F006 slices.

Grid: 4 variants (DONCHIAN_20/55, DONCHIAN_PULLBACK_20/55) x 5 symbols x 2 intervals
x mask in {one_shot, none} = 80 runs, all at cooldown_candles=0. The one-shot mask is
on from the start, per spec/research/F006-hypothesis-one-shot-entry.md's decision; the
unmasked arm is the before/after control in the same format as that note.

HARNESS CONTROL (40 further runs, reported separately, NOT part of the 80): the same
two mask modes for EMA_8_21 and BB_20_25_breakout -- the catalog's canonical persistent
state and its least-bad breakout name -- re-run here and compared row by row against
output/f006_one_shot/summary/results.csv. The Donchian numbers are only comparable to
that note's -$0.985 per-trade bar if this script's harness reproduces that note's rows
to the cent, so this is checked rather than assumed.

One interpreter: donchian.py is pure OHLC, no advanced-ta, so unlike the Lorentzian
and one-shot experiments there is no second pass.

    .venv_test/bin/python scripts/f006_donchian_experiment.py

Scope discipline, same as every F006 script: the frozen protocol-scoped cache is
checksum-verified against spec/research/F005-validation-protocol.md section 6 and
sliced to [2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z) -- warm-up + Train 1 only --
before run_backtest ever sees it. Validation 1-4 and Holdout are never loaded.

Reads strategy.py/backtest_engine.py/data_contract.py/entry_masks.py/donchian.py and
changes none of them. Writes only output/f006_donchian/. Zero network connections.
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
# scripts/f006_stop_width_experiment.py / f006_cooldown_experiment.py /
# f006_one_shot_experiment.py, duplicated (not imported) so this script verifies
# independently before using the cache.
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

DONCHIAN_NAMES = ["DONCHIAN_20", "DONCHIAN_55", "DONCHIAN_PULLBACK_20", "DONCHIAN_PULLBACK_55"]
CONTROL_NAMES = ["EMA_8_21", "BB_20_25_breakout"]
MASK_MODES = ["none", "one_shot"]
COOLDOWN = 0

# Identical fixed block to scripts/f006_one_shot_experiment.py (itself the cooldown
# experiment's, itself the stop-width experiment's at max_sl_pct=0.03).
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

OUT_DIR = "output/f006_donchian/summary"
ONE_SHOT_RESULTS = "output/f006_one_shot/summary/results.csv"
# The bar the falsification condition names: the 12-name catalog sample's mean net PnL
# per trade in the one-shot cd=0 cell of spec/research/F006-hypothesis-one-shot-entry.md.
CATALOG_ONE_SHOT_PER_TRADE = -0.985


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


def _run_one(df, mask, symbol, interval, strategy_name, mask_mode, n_calls, group) -> dict:
    t0 = time.time()
    result = backtest_engine.run_backtest(
        df, strategy_name, interval=interval, now=NOW, symbol=symbol,
        initial_equity=INITIAL_EQUITY, stake=STAKE, max_sl_pct=MAX_SL_PCT,
        cooldown_candles=COOLDOWN,
        entry_regime_mask=(mask if mask_mode == "one_shot" else None),
        **FIXED_PARAMS,
    )
    m = result.metrics
    trades = result.trades
    n_initial_sl = int((trades["exit_reason"] == "initial_sl").sum()) if len(trades) else 0
    gross_sum = float(trades["gross_pnl"].sum()) if len(trades) else 0.0
    costs_sum = float(trades["total_costs"].sum()) if len(trades) else 0.0
    # Win/loss decomposition and exit-reason mix: with expectancy negative everywhere,
    # what F006 should try next turns on WHICH of the two it is -- too few winners (a
    # direction problem) or winners cut too small relative to losers (an exit problem,
    # which spec/research/F006-hypothesis-stop-width.md already swept once).
    wins = trades[trades["net_pnl"] > 0]["net_pnl"] if len(trades) else pd.Series(dtype=float)
    losses = trades[trades["net_pnl"] <= 0]["net_pnl"] if len(trades) else pd.Series(dtype=float)
    exit_mix = trades["exit_reason"].value_counts().to_dict() if len(trades) else {}
    return {
        "group": group,
        "symbol": symbol, "interval": interval, "strategy": strategy_name,
        "mask_mode": mask_mode,
        "cooldown_candles": COOLDOWN,
        "max_sl_pct": MAX_SL_PCT,
        "n_calls": n_calls,
        "net_pnl": m["total_net_pnl"],
        "gross_pnl": round(gross_sum, 6),
        "total_costs": round(costs_sum, 6),
        "win_rate": m["win_rate"],
        "n_trades": int(len(trades)),
        "n_initial_sl_exits": n_initial_sl,
        "sum_wins": round(float(wins.sum()), 6),
        "n_wins": int(len(wins)),
        "sum_losses": round(float(losses.sum()), 6),
        "n_losses": int(len(losses)),
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


def _mean_bars_held(trades: pd.DataFrame, interval: str) -> float:
    """Mean holding time in bars. Both variants hold a call until the opposite extreme,
    so how long the ENGINE actually holds one is not readable off the signal."""
    if not len(trades):
        return 0.0
    span = pd.to_datetime(trades["exit_time"]) - pd.to_datetime(trades["entry_time"])
    return round(float((span.dt.total_seconds() / 60.0 / int(interval)).mean()), 2)


def verify_harness_against_one_shot_note(results: pd.DataFrame) -> dict:
    """The control rows must reproduce output/f006_one_shot/summary/results.csv exactly.

    Same engine, same fixed params, same data slice, same mask helper -- so any
    difference means this script's harness drifted and the Donchian numbers are not
    comparable to the -$0.985 bar the falsification condition cites.
    """
    if not os.path.exists(ONE_SHOT_RESULTS):
        return {"checked": False, "reason": f"{ONE_SHOT_RESULTS} not found"}
    stored = pd.read_csv(ONE_SHOT_RESULTS)
    stored = stored[(stored["strategy"].isin(CONTROL_NAMES)) & (stored["cooldown_candles"] == COOLDOWN)].copy()
    stored["interval"] = stored["interval"].astype(str)  # CSV reads "240" back as int64
    mine = results[results["group"] == "harness_control"].copy()
    mine["interval"] = mine["interval"].astype(str)
    merged = mine.merge(stored, on=["symbol", "interval", "strategy", "mask_mode"],
                        suffixes=("_new", "_stored"))
    mismatches = []
    for col in ("net_pnl", "win_rate", "n_trades", "max_drawdown_pct", "final_equity", "n_calls"):
        bad = merged[merged[f"{col}_new"] != merged[f"{col}_stored"]]
        for _, row in bad.iterrows():
            mismatches.append({
                "symbol": row["symbol"], "interval": row["interval"], "strategy": row["strategy"],
                "mask_mode": row["mask_mode"], "column": col,
                "new": row[f"{col}_new"], "stored": row[f"{col}_stored"],
            })
    return {"checked": True, "stored_path": ONE_SHOT_RESULTS,
            "rows_compared": int(len(merged)), "mismatches": mismatches}


def verify_one_shot_rule_held(results: pd.DataFrame) -> dict:
    """On every masked run, executed trades must not exceed directional calls."""
    masked = results[results["mask_mode"] == "one_shot"]
    unmasked = results[results["mask_mode"] == "none"]
    violations = masked[masked["n_trades"] > masked["n_calls"]]
    return {
        "masked_runs": int(len(masked)),
        "masked_violations": int(len(violations)),
        "unmasked_runs": int(len(unmasked)),
        "unmasked_runs_exceeding_n_calls": int((unmasked["n_trades"] > unmasked["n_calls"]).sum()),
        "violating_rows": violations[["symbol", "interval", "strategy", "n_trades", "n_calls"]]
                          .to_dict("records"),
    }


def run_grid() -> pd.DataFrame:
    for name in DONCHIAN_NAMES + CONTROL_NAMES:
        assert name in strategy.STRATEGY_CATALOG, f"strategy {name!r} not in strategy.STRATEGY_CATALOG"

    t_start = time.time()
    rows = []
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            train1_df = load_train1(symbol, interval)
            for group, names in (("donchian", DONCHIAN_NAMES), ("harness_control", CONTROL_NAMES)):
                for name in names:
                    # One signal computation per (symbol, interval, name); the mask is a
                    # pure function of it, built by the SAME helper the one-shot note used.
                    sig = entry_masks.strategy_signal_series(train1_df, name, interval=interval, now=NOW)
                    mask = entry_masks.one_shot_entry_mask(sig)
                    n_calls = int(mask.sum())
                    for mask_mode in MASK_MODES:
                        rows.append(_run_one(train1_df, mask, symbol, interval, name,
                                             mask_mode, n_calls, group))
            print(f"done {symbol}/{interval} ({len(rows)} runs, {time.time() - t_start:.1f}s elapsed)")

    os.makedirs(OUT_DIR, exist_ok=True)
    results_df = pd.DataFrame(rows)
    results_df.to_csv(f"{OUT_DIR}/results.csv", index=False)

    donchian_df = results_df[results_df["group"] == "donchian"]
    checks = {
        "harness_control_vs_one_shot_note": verify_harness_against_one_shot_note(results_df),
        "one_shot_rule_donchian": verify_one_shot_rule_held(donchian_df),
        "one_shot_rule_harness_control": verify_one_shot_rule_held(
            results_df[results_df["group"] == "harness_control"]),
    }
    manifest = _manifest(results_df, t_start, {
        **checks,
        "means_by_variant": _per_strategy_table(results_df),
        "means_by_cell": _means_table(donchian_df),
        "means_by_cell_4h": _means_table(donchian_df[donchian_df["interval"] == "240"]),
        "means_by_cell_1h": _means_table(donchian_df[donchian_df["interval"] == "60"]),
        "falsification": _falsification_verdict(donchian_df),
    })
    with open(f"{OUT_DIR}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    hc = checks["harness_control_vs_one_shot_note"]
    print(f"\nharness control vs one-shot note: {hc.get('rows_compared')} rows compared, "
          f"{len(hc.get('mismatches', []))} mismatches")
    for key in ("one_shot_rule_donchian", "one_shot_rule_harness_control"):
        v = checks[key]
        print(f"{key}: {v['masked_violations']}/{v['masked_runs']} masked runs violate "
              f"n_trades<=n_calls; {v['unmasked_runs_exceeding_n_calls']}/{v['unmasked_runs']} "
              f"unmasked runs exceed n_calls")
    _print_means(donchian_df, "DONCHIAN (4 variants x 10 series)")
    _print_means(donchian_df[donchian_df["interval"] == "240"], "donchian 4h")
    _print_means(donchian_df[donchian_df["interval"] == "60"], "donchian 1h")
    _print_per_strategy(results_df)
    _print_falsification(manifest["falsification"])
    return results_df


def _cell_stats(sub: pd.DataFrame) -> dict:
    per_trade = sub["net_pnl"] / sub["n_trades"].replace(0, pd.NA)
    pooled = float(sub["net_pnl"].sum()) / max(int(sub["n_trades"].sum()), 1)
    return {
        "mean_net_pnl": round(float(sub["net_pnl"].mean()), 2),
        "mean_gross_pnl": round(float(sub["gross_pnl"].mean()), 2),
        "mean_total_costs": round(float(sub["total_costs"].mean()), 2),
        # mean of per-series ratios -- exactly how F006-hypothesis-one-shot-entry.md
        # reported per-trade expectancy, so the -$0.985 comparison is like for like
        "mean_net_pnl_per_trade": round(float(per_trade.mean()), 4),
        # pooled expectancy too: with N=55 some series trade very little, and a mean of
        # ratios over-weights those. Reported alongside, never instead.
        "pooled_net_pnl_per_trade": round(pooled, 4),
        "series_with_zero_trades": int((sub["n_trades"] == 0).sum()),
        "mean_win_rate": round(float(sub["win_rate"].mean()), 2),
        "mean_n_trades": round(float(sub["n_trades"].mean()), 1),
        "mean_n_calls": round(float(sub["n_calls"].mean()), 1),
        "mean_trades_per_call": round(float((sub["n_trades"] / sub["n_calls"].replace(0, pd.NA)).mean()), 3),
        "mean_n_initial_sl_exits": round(float(sub["n_initial_sl_exits"].mean()), 1),
        "mean_max_drawdown_pct": round(float(sub["max_drawdown_pct"].mean()), 2),
        # pooled over every trade in the cell, not a mean of per-series means
        "pooled_avg_win": round(float(sub["sum_wins"].sum()) / max(int(sub["n_wins"].sum()), 1), 4),
        "pooled_avg_loss": round(float(sub["sum_losses"].sum()) / max(int(sub["n_losses"].sum()), 1), 4),
        "pooled_win_rate": round(100.0 * int(sub["n_wins"].sum()) / max(int(sub["n_trades"].sum()), 1), 2),
        "pooled_gross_per_trade": round(float(sub["gross_pnl"].sum()) / max(int(sub["n_trades"].sum()), 1), 4),
        "pooled_cost_per_trade": round(float(sub["total_costs"].sum()) / max(int(sub["n_trades"].sum()), 1), 4),
        "mean_bars_held": round(float(sub["mean_bars_held"].mean()), 2),
        "exit_mix_pct": {
            reason: round(100.0 * int(sub[f"exit_{reason}"].sum()) / max(int(sub["n_trades"].sum()), 1), 2)
            for reason in ("initial_sl", "trailing_sl", "signal_reverse", "end_of_data")
        },
        "survived": int(sub["survived"].sum()),
        "n": int(len(sub)),
        "positive_net_pnl": int((sub["net_pnl"] > 0).sum()),
        "positive_per_trade": int((per_trade.dropna() > 0).sum()),
        "best_net_pnl": round(float(sub["net_pnl"].max()), 2),
    }


def _cell(df: pd.DataFrame, mask_mode: str) -> pd.DataFrame:
    return df[df["mask_mode"] == mask_mode]


def _means_table(df: pd.DataFrame) -> list:
    return [{"mask_mode": m, **_cell_stats(_cell(df, m))} for m in MASK_MODES if not _cell(df, m).empty]


def _per_strategy_table(df: pd.DataFrame) -> dict:
    out = {}
    for name in DONCHIAN_NAMES + CONTROL_NAMES:
        sub = df[df["strategy"] == name]
        if sub.empty:
            continue
        out[name] = {m: _cell_stats(_cell(sub, m)) for m in MASK_MODES if not _cell(sub, m).empty}
        for interval in INTERVALS:
            si = sub[sub["interval"] == interval]
            out[name][f"one_shot_{interval}"] = _cell_stats(_cell(si, "one_shot"))
    return out


def _falsification_verdict(donchian_df: pd.DataFrame) -> dict:
    """The condition as written in the research note, evaluated mechanically."""
    masked = _cell(donchian_df, "one_shot")
    per_variant = {}
    for name in DONCHIAN_NAMES:
        sub = masked[masked["strategy"] == name]
        pt = float((sub["net_pnl"] / sub["n_trades"].replace(0, pd.NA)).mean())
        per_variant[name] = {
            "mean_net_pnl_per_trade": round(pt, 4),
            "positive": bool(pt > 0),
            "beats_catalog_one_shot_bar": bool(pt > CATALOG_ONE_SHOT_PER_TRADE),
        }
    any_positive = any(v["positive"] for v in per_variant.values())
    n_beating = sum(v["beats_catalog_one_shot_bar"] for v in per_variant.values())
    return {
        "catalog_one_shot_per_trade_bar": CATALOG_ONE_SHOT_PER_TRADE,
        "per_variant": per_variant,
        "clause_a_no_variant_positive": not any_positive,
        "clause_b_fewer_than_2_beat_the_bar": n_beating < 2,
        "n_variants_beating_bar": n_beating,
        "falsified": (not any_positive) or (n_beating < 2),
    }


def _print_means(df: pd.DataFrame, label: str) -> None:
    print(f"\n-- {label}: means by mask_mode --")
    for mask_mode in MASK_MODES:
        sub = _cell(df, mask_mode)
        if sub.empty:
            continue
        s = _cell_stats(sub)
        print(f"{mask_mode:>8}: net_pnl={s['mean_net_pnl']:9.2f}  per_trade={s['mean_net_pnl_per_trade']:7.3f}  "
              f"pooled={s['pooled_net_pnl_per_trade']:7.3f}  win_rate={s['mean_win_rate']:6.2f}%  "
              f"n_trades={s['mean_n_trades']:7.1f}  maxDD={s['mean_max_drawdown_pct']:6.2f}%  "
              f"survived={s['survived']}/{s['n']}  positive={s['positive_net_pnl']}/{s['n']}")


def _print_per_strategy(df: pd.DataFrame) -> None:
    print("\n-- per strategy (10 series each) --")
    print(f"{'strategy':<24} {'mode':>8} {'net_pnl':>9} {'per_trade':>10} {'pooled':>8} "
          f"{'win%':>6} {'trades':>7} {'calls':>7} {'surv':>5} {'pos':>4}")
    for name, cells in _per_strategy_table(df).items():
        for mask_mode in MASK_MODES:
            s = cells[mask_mode]
            print(f"{name:<24} {mask_mode:>8} {s['mean_net_pnl']:9.2f} {s['mean_net_pnl_per_trade']:10.3f} "
                  f"{s['pooled_net_pnl_per_trade']:8.3f} {s['mean_win_rate']:6.2f} {s['mean_n_trades']:7.1f} "
                  f"{s['mean_n_calls']:7.1f} {s['survived']:>3}/{s['n']:<2} {s['positive_net_pnl']:>2}/{s['n']:<2}")


def _print_falsification(verdict: dict) -> None:
    print("\n-- falsification condition (as pre-registered) --")
    for name, v in verdict["per_variant"].items():
        print(f"  {name:<24} per_trade={v['mean_net_pnl_per_trade']:8.4f}  positive={v['positive']}  "
              f"beats -$0.985 bar={v['beats_catalog_one_shot_bar']}")
    print(f"  clause (a) no variant has positive expectancy : {verdict['clause_a_no_variant_positive']}")
    print(f"  clause (b) fewer than 2 beat the catalog bar  : {verdict['clause_b_fewer_than_2_beat_the_bar']} "
          f"({verdict['n_variants_beating_bar']}/4 beat it)")
    print(f"  => FALSIFIED: {verdict['falsified']}")


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
        "n_runs_donchian_grid": int((results_df["group"] == "donchian").sum()),
        "n_runs_harness_control": int((results_df["group"] == "harness_control").sum()),
        "donchian_names": DONCHIAN_NAMES,
        "harness_control_names": CONTROL_NAMES,
        "mask_modes": MASK_MODES,
        "cooldown_candles": COOLDOWN,
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


if __name__ == "__main__":
    run_grid()
