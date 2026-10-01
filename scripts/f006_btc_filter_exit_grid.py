"""Frozen exit-only continuation of H-BTC-FILTER-01 (Train-1 only).

H-BTC-FILTER-EXIT-GRID-SPARSE-01. Entries are the unchanged parent ``btc_filter``
module (tip e518682); BTC is permission context only and its candidate rows stay
forced flat. Reuses the Sube exit-grid sparse-month/summary helpers and the shared
runner's loader, constants, and control verifier without mutating either.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import btc_filter
from scripts import f006_family_runner as runner
from scripts.f006_sube_inv_fvg_exit_grid import EXIT_GRID, sparse_months, sparse_pass, summarize

__all__ = ["EXIT_GRID", "sparse_months", "sparse_pass", "summarize"]

OUT = Path("output/f006_btc_filter/exit_grid")
PRIOR = Path("output/f006_btc_filter")
NAMES = tuple(f"BTC_FILTER_ER20_DONCHIAN_{n}" for n in btc_filter.ALT_LOOKBACKS)


def verify_prior(rows: list[dict]) -> dict:
    """Exact parent NO_TRAIL reproduction, including both month validity and PnL."""
    for row in rows:
        if row["exit_cell"] != "NO_TRAIL":
            continue
        path = PRIOR / "raw" / f'{row["symbol"]}_{row["interval"]}_{row["strategy"]}.json'
        old = json.loads(path.read_text())
        for col in ("n_calls", "n_trades", "n_wins", "win_rate", "net_pnl", "train1_net_pnl",
                    "max_drawdown_pct", "final_equity", "n_valid_months", "all_valid_months_nonnegative"):
            if row[col] != old[col]:
                raise AssertionError(f"NO_TRAIL reproduction failed: {path.name} {col}: {row[col]} != {old[col]}")
        if row["legacy_h2"] != old["promotion_pass"]:
            raise AssertionError(f"legacy H2 changed: {path.name}")
    return {"rows_compared": sum(r["exit_cell"] == "NO_TRAIL" for r in rows), "mismatches": 0}


def rank_table(results: pd.DataFrame, pooled: bool = False) -> pd.DataFrame:
    """Trade-weighted WR rank; H1 is the ten-row mean (BTC rows forced flat).

    Per name, a non-NO_TRAIL cell whose WR beats NO_TRAIL while its mean Train-1
    PnL falls below NO_TRAIL is flagged ``s8_regression`` (fat winners cut).
    """
    candidates = results[results.strategy.isin(NAMES)]
    rows = []
    keys = ["exit_cell"] if pooled else ["strategy", "exit_cell"]
    for key, group in candidates.groupby(keys):
        row = {"exit_cell": key[0]} if pooled else dict(zip(keys, key))
        n = int(group.n_trades.sum())
        alts = group[group.symbol != btc_filter.BTC_SYMBOL]
        h1 = bool(group.train1_net_pnl.mean() > 0)
        row.update(win_rate=100 * int(group.n_wins.sum()) / n if n else 0,
                   mean_train1_net_pnl=float(group.train1_net_pnl.mean()), h1_pass=h1,
                   alt_mean_train1_net_pnl=float(alts.train1_net_pnl.mean()),
                   n_series=len(group), n_trades=n, mean_trades_per_series=n / len(group),
                   density_below_10=n / len(group) < 10,
                   max_drawdown_pct=float(group.max_drawdown_pct.max()),
                   legacy_h2_series=int(group.legacy_h2.sum()),
                   sparse_h2_series=int(group.h2_sparse_absent_zero_trade.sum()))
        if not pooled:
            row.update(legacy_h2_after_h1=int(group.legacy_h2.sum()) if h1 else 0,
                       sparse_h2_after_h1=int(group.h2_sparse_absent_zero_trade.sum()) if h1 else 0)
        rows.append(row)
    table = pd.DataFrame(rows)
    base = table[table.exit_cell == "NO_TRAIL"].set_index(["exit_cell"] if pooled else ["strategy"])
    def regression(r):
        b = base.iloc[0] if pooled else base.loc[r["strategy"]]
        return bool(r["exit_cell"] != "NO_TRAIL" and r["win_rate"] > b.win_rate
                    and r["mean_train1_net_pnl"] < b.mean_train1_net_pnl)
    table["delta_mean_train1_vs_no_trail"] = [
        r["mean_train1_net_pnl"] - (base.iloc[0] if pooled else base.loc[r["strategy"]]).mean_train1_net_pnl
        for _, r in table.iterrows()]
    table["s8_regression"] = [regression(r) for _, r in table.iterrows()]
    order = ["win_rate", "exit_cell"] if pooled else ["strategy", "win_rate", "exit_cell"]
    return table.sort_values(order, ascending=[False, True] if pooled else [True, False, True])


def main() -> None:
    if subprocess.check_output(["git", "diff", "HEAD", "--name-only"], text=True).strip():
        raise SystemExit("Commit tracked changes before running evidence")
    tip = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    started = datetime.now(timezone.utc).isoformat()
    btc_by_interval = {i: runner.load_train1(btc_filter.BTC_SYMBOL, i)[0] for i in runner.INTERVALS}
    runner.register_catalog_entries(btc_filter.catalog_entries(btc_by_interval))
    rows, monthly_rows, trades_rows, checksums, signal_hashes = [], [], [], {}, {}
    for interval in runner.INTERVALS:
        for symbol in runner.SYMBOLS:
            frame, manifest = runner.load_train1(symbol, interval)
            checksums[f"{symbol}_{interval}"] = manifest.checksum_sha256
            for name in (*NAMES, runner.CONTROL_NAME):
                signal = runner.entry_masks.strategy_signal_series(frame, name, interval=interval, now=runner.NOW)
                mask = runner.entry_masks.one_shot_entry_mask(signal)
                signal_hashes[f"{symbol}_{interval}_{name}"] = hashlib.sha256(signal.to_csv().encode()).hexdigest()
                if symbol == btc_filter.BTC_SYMBOL and name in NAMES and mask.any():
                    raise AssertionError("BTC must never trigger a BTC-FILTER entry")
                cells = ["NO_TRAIL"] if name == runner.CONTROL_NAME else EXIT_GRID
                for cell in cells:
                    result = runner.backtest_engine.run_backtest(
                        frame, name, interval=interval, now=runner.NOW, symbol=symbol,
                        initial_equity=runner.INITIAL_EQUITY, stake=runner.STAKE,
                        max_sl_pct=runner.MAX_SL_PCT, cooldown_candles=runner.COOLDOWN,
                        entry_regime_mask=mask, **runner.FIXED_PARAMS, **EXIT_GRID[cell])
                    identity = dict(symbol=symbol, interval=interval, strategy=name, exit_cell=cell)
                    row, months = summarize(result)
                    rows.append({**identity, "n_calls": int(mask.sum()), **row})
                    monthly_rows.extend({**identity, **m} for m in months)
                    trades_rows.extend({**identity, **t} for t in result.trades.to_dict("records"))
    prior = verify_prior(rows)
    control = runner.verify_harness_control(rows, runner.CONTROL_NAME, runner.CONTROL_REFERENCE_CSV)
    if any(r["n_trades"] > r["n_calls"] for r in rows):
        raise AssertionError("one-shot violation")
    if any(r["n_trades"] for r in rows if r["symbol"] == btc_filter.BTC_SYMBOL and r["strategy"] in NAMES):
        raise AssertionError("BTC traded under a BTC-FILTER name")
    results = pd.DataFrame(rows)
    ranks, pooled = rank_table(results), rank_table(results, pooled=True)
    sources = ["btc_filter.py", "backtest_engine.py", "scripts/f006_family_runner.py",
               "scripts/f006_sube_inv_fvg_exit_grid.py", __file__]
    meta = dict(hypothesis="H-BTC-FILTER-EXIT-GRID-SPARSE-01",
                hypothesis_note="spec/research/F006-hypothesis-btc-filter-exit-grid-sparse.md",
                parent="H-BTC-FILTER-01 tip e518682; baseline output/f006_btc_filter/raw",
                git_commit=tip, started_utc=started, python=sys.version, pandas=pd.__version__,
                exit_grid=EXIT_GRID, candidate_names=list(NAMES), n_runs=len(rows),
                checksums_used=checksums, signal_hashes=signal_hashes,
                source_sha256={str(Path(p).name): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
                train1_end=str(runner.TRAIN1_END), warmup_start=runner.WARMUP_START,
                fixed_params={**runner.FIXED_PARAMS, "max_sl_pct": runner.MAX_SL_PCT,
                              "stake": runner.STAKE, "initial_equity": runner.INITIAL_EQUITY,
                              "cooldown_candles": runner.COOLDOWN, "mask": "one_shot"},
                sparse_month_bucket="exit month Europe/Warsaw; zero exits ABSENT; Train-1 months only",
                h1_basis="ten-row mean train1_net_pnl (BTC rows forced flat), as parent",
                rank_metric="trade-weighted win_rate; pooled excludes DONCHIAN_55",
                s8_regression="non-NO_TRAIL cell with higher WR but lower mean Train-1 than NO_TRAIL, same name",
                prior_no_trail_check=prior, harness_control=control, one_shot_violations=0,
                btc_trades_under_candidates=0)
    OUT.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT / "results.csv", index=False)
    pd.DataFrame(monthly_rows).to_csv(OUT / "monthly.csv", index=False)
    pd.DataFrame(trades_rows).to_csv(OUT / "trades.csv", index=False)
    ranks.to_csv(OUT / "rank_by_name.csv", index=False)
    pooled.to_csv(OUT / "rank_pooled.csv", index=False)
    (OUT / "manifest.json").write_text(json.dumps(meta, indent=2) + "\n")
    for cell in EXIT_GRID:
        dest = OUT / cell
        dest.mkdir(exist_ok=True)
        results[results.exit_cell == cell].to_csv(dest / "results.csv", index=False)
        (dest / "manifest.json").write_text(json.dumps({"git_commit": tip, "exit_cell": cell,
            "params": EXIT_GRID[cell], "shared_manifest": "../manifest.json"}, indent=2) + "\n")
    pd.set_option("display.width", 250)
    print(ranks.to_string(index=False))
    print("\nPooled (descriptive, not the per-name H1 decision):\n", pooled.to_string(index=False))
    print("\nChecks:", prior, control)


if __name__ == "__main__":
    main()
