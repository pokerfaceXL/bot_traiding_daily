"""Frozen exit-only continuation of H-SUBE-INV-FVG-01 (Train-1 only).

The shared run_family is deliberately NO_TRAIL-only. This sibling reuses its
bounded loader, constants, control verifier, and monthly helpers without mutating
that harness. Entries are computed once per series by the unchanged signal module.
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
import sube_inv_fvg
from scripts import f006_family_runner as runner

OUT = Path("output/f006_sube_inv_fvg/exit_grid")
PRIOR = Path("output/f006_sube_inv_fvg")
EXIT_GRID = {
    "NO_TRAIL": dict(activate_pct=10.0, trail_pct=0.04, take_profit_multiple=None),
    "TP_x2": dict(activate_pct=10.0, trail_pct=0.04, take_profit_multiple=2.0),
    "TRAIL_a0.06_t0.04": dict(activate_pct=0.06, trail_pct=0.04, take_profit_multiple=None),
    "TRAIL_a0.03_t0.02": dict(activate_pct=0.03, trail_pct=0.02, take_profit_multiple=None),
}


def sparse_months(trades: pd.DataFrame) -> list[dict]:
    """Exit-month realized PnL; empty Train-1 months are explicitly ABSENT."""
    buckets = {}
    if not trades.empty:
        exits = pd.to_datetime(trades["exit_time"], utc=True).dt.tz_convert("Europe/Warsaw")
        for stamp, pnl in zip(exits, trades["net_pnl"]):
            key = (stamp.year, stamp.month)
            if key in runner.TRAIN1_MONTHS_SET:
                buckets.setdefault(key, []).append(float(pnl))
    return [dict(year=y, month=m, status="scored" if (y, m) in buckets else "ABSENT",
                 n_trades=len(buckets.get((y, m), [])),
                 net_pnl=sum(buckets[(y, m)]) if (y, m) in buckets else None)
            for y, m in runner.TRAIN1_MONTHS]


def sparse_pass(months: list[dict], train1_net_pnl: float, max_dd: float) -> bool:
    scored = [m for m in months if m["n_trades"] > 0]
    return bool(scored and all(m["net_pnl"] >= 0 for m in scored)
                and train1_net_pnl >= 0 and max_dd <= 50)


def summarize(result) -> tuple[dict, list[dict]]:
    days, months = runner.regularity.compute_regularity(result.equity_curve)
    by_key = {(m.year, m.month): m for m in months}
    sparse = sparse_months(result.trades)
    monthly = []
    for sm in sparse:
        y, m = sm["year"], sm["month"]
        legacy = by_key.get((y, m))
        valid = legacy is not None and legacy.is_valid
        monthly.append({**sm, "legacy_is_valid": bool(valid),
                        "legacy_equity_net_pnl": runner._net_pnl_for_month(days, y, m) if valid else None})
    train_pnl = runner._net_pnl_for_months(days, runner.TRAIN1_MONTHS_SET)
    n_valid = sum(m["legacy_is_valid"] for m in monthly)
    nonnegative = all(m["legacy_equity_net_pnl"] >= 0 for m in monthly if m["legacy_is_valid"])
    dd = result.metrics["max_drawdown_pct"]
    trades = result.trades
    n_trades = len(trades)
    row = dict(net_pnl=result.metrics["total_net_pnl"], train1_net_pnl=round(train_pnl, 6),
               win_rate=result.metrics["win_rate"], n_trades=n_trades,
               n_wins=int((trades.net_pnl > 0).sum()) if n_trades else 0,
               max_drawdown_pct=dd, final_equity=result.metrics["final_equity"],
               n_valid_months=n_valid, all_valid_months_nonnegative=nonnegative,
               legacy_h2=bool(dd <= 50 and nonnegative and n_valid == 12 and train_pnl >= 0 and n_trades > 0),
               h2_sparse_absent_zero_trade=sparse_pass(sparse, train_pnl, dd),
               n_scored_months=sum(m["n_trades"] > 0 for m in sparse),
               train1_exit_n_trades=sum(m["n_trades"] for m in sparse),
               train1_exit_net_pnl=sum(m["net_pnl"] for m in sparse if m["n_trades"] > 0),
               exit_mix=json.dumps(trades.exit_reason.value_counts().to_dict() if n_trades else {}, sort_keys=True))
    return row, monthly


def verify_prior(rows: list[dict]) -> dict:
    """Exact prior NO_TRAIL reproduction, including both month validity and PnL."""
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
    candidates = results[results.strategy.isin(sube_inv_fvg.NAMES)]
    rows = []
    keys = ["exit_cell"] if pooled else ["strategy", "exit_cell"]
    for key, group in candidates.groupby(keys):
        if pooled:
            row = {"exit_cell": key[0]}
        else:
            row = dict(zip(keys, key))
        n = int(group.n_trades.sum())
        h1 = bool(group.train1_net_pnl.mean() > 0)
        row.update(win_rate=100 * int(group.n_wins.sum()) / n if n else 0,
                   mean_train1_net_pnl=float(group.train1_net_pnl.mean()), h1_pass=h1,
                   n_series=len(group), n_trades=n, mean_trades_per_series=n / len(group),
                   density_below_10=n / len(group) < 10,
                   max_drawdown_pct=float(group.max_drawdown_pct.max()),
                   legacy_h2_series=int(group.legacy_h2.sum()),
                   sparse_h2_series=int(group.h2_sparse_absent_zero_trade.sum()))
        if not pooled:
            row.update(legacy_h2_after_h1=int(group.legacy_h2.sum()) if h1 else 0,
                       sparse_h2_after_h1=int(group.h2_sparse_absent_zero_trade.sum()) if h1 else 0)
        rows.append(row)
    order = ["win_rate", "exit_cell"] if pooled else ["strategy", "win_rate", "exit_cell"]
    return pd.DataFrame(rows).sort_values(order, ascending=[False, True] if pooled else [True, False, True])


def main() -> None:
    if subprocess.check_output(["git", "diff", "HEAD", "--name-only"], text=True).strip():
        raise SystemExit("Commit tracked changes before running evidence")
    tip = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    started = datetime.now(timezone.utc).isoformat()
    rows, monthly_rows, trades_rows, checksums, signal_hashes = [], [], [], {}, {}
    for interval in runner.INTERVALS:
        loaded = {symbol: runner.load_train1(symbol, interval) for symbol in runner.SYMBOLS}
        for symbol, (frame, manifest) in loaded.items():
            checksums[f"{symbol}_{interval}"] = manifest.checksum_sha256
            peer = loaded["ETHUSDT" if symbol == "BTCUSDT" else "BTCUSDT"][0]
            signals = sube_inv_fvg.compute_signals(frame, int(interval), peer)
            for name, signal in signals.items():
                # Pure memoization of the unchanged generator, not a new entry rule.
                def cached(work, signal=signal):
                    if not work.index.equals(signal.index):
                        raise AssertionError("Engine frame differs from computed signal frame")
                    return signal.copy()
                runner.strategy.STRATEGY_CATALOG[name] = cached
            signals[runner.CONTROL_NAME] = runner.entry_masks.strategy_signal_series(
                frame, runner.CONTROL_NAME, interval=interval, now=runner.NOW)
            for name, signal in signals.items():
                mask = runner.entry_masks.one_shot_entry_mask(signal)
                signal_hashes[f"{symbol}_{interval}_{name}"] = hashlib.sha256(signal.to_csv().encode()).hexdigest()
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
    results = pd.DataFrame(rows)
    ranks, pooled = rank_table(results), rank_table(results, pooled=True)
    sources = ["sube_inv_fvg.py", "backtest_engine.py", "scripts/f006_family_runner.py", __file__]
    meta = dict(git_commit=tip, started_utc=started, python=sys.version, pandas=pd.__version__,
                exit_grid=EXIT_GRID, candidate_names=list(sube_inv_fvg.NAMES), n_runs=len(rows),
                checksums_used=checksums, signal_hashes=signal_hashes,
                source_sha256={str(Path(p).name): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
                train1_end=str(runner.TRAIN1_END), warmup_start=runner.WARMUP_START,
                fixed_params={**runner.FIXED_PARAMS, "max_sl_pct": runner.MAX_SL_PCT,
                              "stake": runner.STAKE, "initial_equity": runner.INITIAL_EQUITY,
                              "cooldown_candles": runner.COOLDOWN, "mask": "one_shot"},
                sparse_month_bucket="exit month Europe/Warsaw; zero exits ABSENT; Train-1 months only",
                rank_metric="trade-weighted win_rate; pooled excludes DONCHIAN_55",
                prior_no_trail_check=prior, harness_control=control, one_shot_violations=0)
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
    print(ranks.to_string(index=False))
    print("\nPooled (descriptive, not the per-name H1 decision):\n", pooled.to_string(index=False))
    print("\nChecks:", prior, control)


if __name__ == "__main__":
    main()
