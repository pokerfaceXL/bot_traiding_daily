"""Frozen BTC permission × CASCADE, Train-1 only; four exits, dual H2.

run_family owns NO_TRAIL/control/H1. The additive exit loop uses the already
merged sparse-H2 summarizer and engine hooks, without modifying the harness.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import btc_perm_cascade as bpc
from scripts import f006_family_runner as runner
from scripts.f006_sube_inv_fvg_exit_grid import EXIT_GRID, summarize

OUT = Path("output/f006_btc_perm_cascade")


def rank_table(results: pd.DataFrame, spam: dict, primary_h1: dict) -> pd.DataFrame:
    rows = []
    for (name, cell), group in results.groupby(["strategy", "exit_cell"]):
        n = int(group.n_trades.sum())
        h1 = bool(group.train1_net_pnl.mean() > 0)
        rows.append(dict(
            strategy=name, exit_cell=cell,
            win_rate=100 * int(group.n_wins.sum()) / n if n else 0,
            mean_train1_net_pnl=float(group.train1_net_pnl.mean()), h1_pass=h1,
            primary_no_trail_h1=primary_h1[name], n_trades=n,
            mean_trades_per_series=n / len(group), mean_trades_per_alt_series=n / 8,
            thin_series_below_15=n / len(group) < 15,
            max_drawdown_pct=float(group.max_drawdown_pct.max()),
            legacy_h2_series=int(group.legacy_h2.sum()),
            sparse_h2_series=int(group.h2_sparse_absent_zero_trade.sum()),
            legacy_h2_after_h1=int(group.legacy_h2.sum()) if h1 else 0,
            sparse_h2_after_h1=int(group.h2_sparse_absent_zero_trade.sum()) if h1 else 0,
            mean_signals_per_alt_series_month=spam[name], spam_rejected=spam[name] > 8,
        ))
    return pd.DataFrame(rows).sort_values(["strategy", "win_rate", "exit_cell"], ascending=[True, False, True])


def main() -> None:
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=normal"], text=True).strip():
        raise SystemExit("Commit changes before producing evidence")
    tip = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    btc = {iv: runner.load_train1("BTCUSDT", iv)[0] for iv in runner.INTERVALS}
    baseline = runner.run_family(
        family="btc_perm_cascade", candidate_names=bpc.NAMES,
        catalog_entries=bpc.catalog_entries(btc),
        hypothesis_note="spec/research/F006-hypothesis-btc-perm-cascade.md",
        script_path="scripts/f006_btc_perm_cascade_experiment.py",
    )
    primary_h1 = {r["strategy"]: r["h1_pass"] for r in baseline["h1_table"]}
    rows, months, trades, hashes = [], [], [], {}
    signals_per_name = dict.fromkeys(bpc.NAMES, 0)
    for interval in runner.INTERVALS:
        for symbol in runner.SYMBOLS:
            frame, _ = runner.load_train1(symbol, interval)
            for name in bpc.NAMES:
                signal = bpc.signal(frame, btc[interval], name)
                mask = runner.entry_masks.one_shot_entry_mask(signal)
                train = signal.loc[(signal.index >= pd.Timestamp("2024-03-01T00:00:00Z"))
                                   & (signal.index < runner.TRAIN1_END)]
                signals_per_name[name] += int(train.ne(0).sum())
                hashes[f"{symbol}_{interval}_{name}"] = hashlib.sha256(signal.to_csv().encode()).hexdigest()

                def cached(work, signal=signal):
                    if not work.index.equals(signal.index):
                        raise AssertionError("Engine frame differs from signal frame")
                    return signal.copy()

                runner.strategy.STRATEGY_CATALOG[name] = cached
                for cell, params in EXIT_GRID.items():
                    result = runner.backtest_engine.run_backtest(
                        frame, name, interval=interval, now=runner.NOW, symbol=symbol,
                        initial_equity=runner.INITIAL_EQUITY, stake=runner.STAKE,
                        max_sl_pct=runner.MAX_SL_PCT, cooldown_candles=runner.COOLDOWN,
                        entry_regime_mask=mask, **runner.FIXED_PARAMS, **params)
                    row, monthly = summarize(result)
                    identity = dict(symbol=symbol, interval=interval, strategy=name, exit_cell=cell)
                    row = {**identity, "n_calls": int(mask.sum()), "train1_n_signals": int(train.ne(0).sum()), **row}
                    if row["n_trades"] > row["n_calls"]:
                        raise AssertionError("one-shot violation")
                    if symbol == "BTCUSDT" and (row["n_trades"] or row["n_calls"]):
                        raise AssertionError("BTC must remain forced flat")
                    if cell == "NO_TRAIL":
                        old = json.loads((OUT / "raw" / f"{symbol}_{interval}_{name}.json").read_text())
                        for col in ("n_calls", "n_trades", "win_rate", "net_pnl", "train1_net_pnl",
                                    "max_drawdown_pct", "final_equity", "n_valid_months"):
                            if row[col] != old[col]:
                                raise AssertionError(f"NO_TRAIL differs from run_family: {identity} {col}")
                        if row["legacy_h2"] != old["promotion_pass"]:
                            raise AssertionError("Legacy H2 differs from run_family")
                    rows.append(row)
                    months.extend({**identity, **m} for m in monthly)
                    trades.extend({**identity, **t} for t in result.trades.to_dict("records"))
    # The spam denominator excludes forced-flat BTC, rather than diluting alt density.
    spam = {name: count / (8 * 12) for name, count in signals_per_name.items()}
    results = pd.DataFrame(rows)
    ranks = rank_table(results, spam, primary_h1)
    control = pd.read_csv(OUT / "summary/results.csv")
    control_mean = float(control.loc[control.strategy == runner.CONTROL_NAME, "train1_net_pnl"].mean())
    if abs(control_mean - 58.387) > 0.001:
        raise AssertionError(f"DONCHIAN_55 Train-1 reference changed: {control_mean}")
    sources = ["btc_perm_cascade.py", "scripts/f006_btc_perm_cascade_experiment.py",
               "scripts/f006_sube_inv_fvg_exit_grid.py", "scripts/f006_family_runner.py",
               "backtest_engine.py", "entry_masks.py", "regularity.py", "strategy.py"]
    dest = OUT / "exit_grid"
    dest.mkdir(parents=True, exist_ok=True)
    results.to_csv(dest / "results.csv", index=False)
    pd.DataFrame(months).to_csv(dest / "monthly.csv", index=False)
    pd.DataFrame(trades).to_csv(dest / "trades.csv", index=False)
    ranks.to_csv(dest / "rank_by_name.csv", index=False)
    meta = dict(
        producing_commit=tip, packaging_tip_sha=None,
        packaging_note="Set after evidence packaging commit; final metadata commit records that immutable tip.",
        base_commit="eaf4add", candidate_names=list(bpc.NAMES), exit_grid=EXIT_GRID,
        train1_end=str(runner.TRAIN1_END), warmup_start=runner.WARMUP_START,
        checksums_used=baseline["checksums_used"], fixed_params=baseline["params"],
        n_runs=len(rows), python=sys.version, pandas=pd.__version__,
        source_sha256={p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
        signal_hashes=hashes, control_mean_train1_net_pnl=control_mean,
        harness_control=baseline["harness_control"], no_trail_reproduction_rows=50,
        one_shot_violations=0, btc_forced_flat_rows=40,
        sparse_month_bucket="exit month Europe/Warsaw; zero trades ABSENT; Train-1 only",
        rank_metric="trade-weighted win_rate per name across exits (warm-up included as harness metrics)",
        h1_metric="mean train1_net_pnl across 10 rows; NO_TRAIL primary",
        h2_note="Raw dual H2 always reported; after_h1 columns conditional on each cell H1; primary_no_trail_h1 retained.",
        spam_note="Train-1 emitted signals / (8 alt series * 12 months); reject >8, not retuned",
        mean_signals_per_alt_series_month=spam,
        density_note="Mean harness trades includes warm-up; BTC diagnostics dilute 10-series mean. Alt-only mean also reported; <15 thin. Exits do not add signals.",
    )
    (dest / "manifest.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(ranks.to_string(index=False))
    print(f"DONCHIAN_55 mean Train-1: {control_mean:.9f}; 10 reference rows, 0 mismatches")
    print("NO_TRAIL reproduced 50 candidate rows; BTC flat in 40 cells; one-shot violations 0")


if __name__ == "__main__":
    main()
