"""H-CATALOG5-PARTIAL-EXIT-01 (Train-1 only): partial scale-out grid on the five CONDITIONAL
catalog5 NO_TRAIL profiles. Entries UNCHANGED -- same strategy.STRATEGY_CATALOG generators,
same one-shot mask, same frozen Train-1 5x2 basket as scripts/f006_catalog5_exit_class_grid.py
(whose summarize / prior-reproduction / sparse-H2 helpers are reused as-is). Only the exit
changes, via backtest_engine.run_backtest's additive partial_fraction / partial_r_multiple hook.

Pre-registration: spec/research/F006-hypothesis-catalog5-partial-exit.md.

Measurement definitions (frozen with this file, before the run):
- Entry-level accounting for partial cells: the partial_take leg and the remainder leg of one
  entry (same parent_id) are one trade. win_rate / n_trades / n_wins are per entry on the
  combined net_pnl; the engine's row-level metrics are kept as leg_* columns.
- initial_sl_share (falsifier b) = entries whose position ends at initial_sl WITHOUT a partial
  bank (full-R losers) / entries. initial_sl_share_any also counts remainder stop-outs after a
  partial bank (descriptive).
- Big-winner PnL retention (falsifier b): per name, the top-decile (ceil 10%) NO_TRAIL entries
  by net_pnl pooled over the 10 series, keyed (symbol, interval, entry_time). Retention = sum
  of those same entries' combined net_pnl in the cell / baseline sum (entry missing -> 0).
- Losing-month floor (falsifier c): per series, legacy-valid Train-1 months with equity
  net_pnl < 0; per name report worst (max) and best (min) series, as in EXIT-CLASS-01.
- Sparse months are bucketed by each leg's own exit month (realized PnL, causal).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import f006_family_runner as runner
from scripts import f006_catalog5_exit_class_grid as ecg
import entry_masks

OUT = Path("output/f006_catalog5_partial_exit")
CANDIDATE_NAMES = ecg.CANDIDATE_NAMES
BASELINE = "NO_TRAIL"
NO_TRAIL = dict(activate_pct=10.0, trail_pct=0.04)
EXIT_GRID = {
    "NO_TRAIL": dict(**NO_TRAIL),
    "PARTIAL_50_at_1R_NO_TRAIL": dict(**NO_TRAIL, partial_fraction=0.5, partial_r_multiple=1.0),
    "PARTIAL_50_at_1R_TRAIL_a0.06_t0.04": dict(activate_pct=0.06, trail_pct=0.04,
                                               partial_fraction=0.5, partial_r_multiple=1.0),
    "PARTIAL_50_at_1.5R_NO_TRAIL": dict(**NO_TRAIL, partial_fraction=0.5, partial_r_multiple=1.5),
    "PARTIAL_50_at_2R_NO_TRAIL": dict(**NO_TRAIL, partial_fraction=0.5, partial_r_multiple=2.0),
}


def entry_trades(trades: pd.DataFrame) -> pd.DataFrame:
    """One row per entry: combined net_pnl, final exit_reason, whether a partial was banked."""
    if trades.empty:
        return pd.DataFrame(columns=["entry_time", "net_pnl", "final_exit", "partial_taken"])
    if "leg" not in trades.columns:
        return pd.DataFrame(dict(entry_time=trades.entry_time, net_pnl=trades.net_pnl,
                                 final_exit=trades.exit_reason, partial_taken=False))
    rows = []
    for _, g in trades.groupby("parent_id", sort=False):
        last = g[g.leg != "partial"]
        rows.append(dict(entry_time=g.entry_time.iloc[0], net_pnl=float(g.net_pnl.sum()),
                         final_exit=last.exit_reason.iloc[-1] if len(last) else "partial_take",
                         partial_taken=bool((g.leg == "partial").any())))
    return pd.DataFrame(rows)


def summarize(result) -> tuple[dict, list[dict]]:
    row, months = ecg.summarize(result)
    entries = entry_trades(result.trades)
    n = len(entries)
    wins = int((entries.net_pnl > 0).sum()) if n else 0
    full_sl = int(((entries.final_exit == "initial_sl") & ~entries.partial_taken).sum()) if n else 0
    any_sl = int((entries.final_exit == "initial_sl").sum()) if n else 0
    row.update(leg_rows=row["n_trades"], leg_win_rate=row["win_rate"],
               n_trades=n, n_wins=wins, win_rate=round(100 * wins / n, 2) if n else 0.0,
               exit_initial_sl=full_sl, exit_initial_sl_any=any_sl,
               n_partial_taken=int(entries.partial_taken.sum()) if n else 0)
    return row, months


def losing_months(monthly: pd.DataFrame) -> pd.DataFrame:
    valid = monthly[monthly.legacy_is_valid]
    return (valid.assign(losing=valid.legacy_equity_net_pnl < 0)
            .groupby(["strategy", "exit_cell", "symbol", "interval"]).losing.sum().reset_index())


def falsifier_table(results: pd.DataFrame, monthly: pd.DataFrame, entries: pd.DataFrame) -> pd.DataFrame:
    lm = losing_months(monthly)
    rows = []
    for name in CANDIDATE_NAMES:
        base_e = entries[(entries.strategy == name) & (entries.exit_cell == BASELINE)]
        k = max(1, math.ceil(0.10 * len(base_e)))
        top = base_e.nlargest(k, "net_pnl")
        top_keys = set(zip(top.symbol, top.interval, top.entry_time))
        top_sum = float(top.net_pnl.sum())
        for cell in EXIT_GRID:
            r = results[(results.strategy == name) & (results.exit_cell == cell)]
            e = entries[(entries.strategy == name) & (entries.exit_cell == cell)]
            kept = e[[key in top_keys for key in zip(e.symbol, e.interval, e.entry_time)]]
            n = int(r.n_trades.sum())
            l = lm[(lm.strategy == name) & (lm.exit_cell == cell)].losing
            rows.append(dict(strategy=name, exit_cell=cell,
                             win_rate=100 * int(r.n_wins.sum()) / n if n else 0.0,
                             mean_train1_net_pnl=float(r.train1_net_pnl.mean()),
                             h1_pass=bool(r.train1_net_pnl.mean() > 0), n_entries=n,
                             initial_sl_share=int(r.exit_initial_sl.sum()) / n if n else 0.0,
                             initial_sl_share_any=int(r.exit_initial_sl_any.sum()) / n if n else 0.0,
                             partial_taken_share=int(r.n_partial_taken.sum()) / n if n else 0.0,
                             big_winner_k=k, big_winner_baseline_pnl=top_sum,
                             big_winner_cell_pnl=float(kept.net_pnl.sum()),
                             big_winner_retention=float(kept.net_pnl.sum()) / top_sum if top_sum else float("nan"),
                             worst_series_losing_months=int(l.max()), best_series_losing_months=int(l.min()),
                             mean_losing_months=float(l.mean()),
                             legacy_h2_series=int(r.legacy_h2.sum()),
                             sparse_h2_series=int(r.h2_sparse_absent_zero_trade.sum()),
                             max_drawdown_pct=float(r.max_drawdown_pct.max())))
    out = pd.DataFrame(rows)
    base = out[out.exit_cell == BASELINE].set_index("strategy")
    out["delta_mean_train1_net_pnl"] = out.mean_train1_net_pnl - out.strategy.map(base.mean_train1_net_pnl)
    out["initial_sl_cut_pp"] = 100 * (out.strategy.map(base.initial_sl_share) - out.initial_sl_share)
    out["worst_losing_months_delta"] = out.worst_series_losing_months - out.strategy.map(base.worst_series_losing_months)
    out["best_losing_months_delta"] = out.best_series_losing_months - out.strategy.map(base.best_series_losing_months)
    return out.sort_values(["strategy", "win_rate", "exit_cell"], ascending=[True, False, True])


def verdict(results: pd.DataFrame, fals: pd.DataFrame) -> dict:
    cand = results[results.strategy.isin(CANDIDATE_NAMES)]
    shared = cand.groupby("exit_cell").train1_net_pnl.mean().to_dict()
    partial = [c for c in EXIT_GRID if c != BASELINE]
    a_beats = [c for c in partial if shared[c] > shared[BASELINE]]
    b_hits = fals[(fals.exit_cell != BASELINE) & (fals.initial_sl_cut_pp >= 10)
                  & (fals.big_winner_retention < 0.5)][["strategy", "exit_cell"]].values.tolist()
    c_improved = fals[(fals.exit_cell != BASELINE) & (fals.worst_losing_months_delta < 0)][
        ["strategy", "exit_cell"]].values.tolist()
    return dict(shared_mean_train1_net_pnl=shared,
                a_partial_cells_beating_baseline=a_beats, a_triggers=not a_beats,
                b_hits=b_hits, b_triggers=bool(b_hits),
                c_worst_series_improved=c_improved, c_triggers=not c_improved,
                falsified=(not a_beats) or bool(b_hits) or (not c_improved))


def main() -> None:
    if subprocess.check_output(["git", "diff", "HEAD", "--name-only"], text=True).strip():
        raise SystemExit("Commit tracked changes before running evidence")
    tip = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    started = datetime.now(timezone.utc).isoformat()
    rows, monthly_rows, trades_rows, entry_rows, checksums, signal_hashes = [], [], [], [], {}, {}
    all_names = list(CANDIDATE_NAMES) + [runner.CONTROL_NAME]
    for symbol in runner.SYMBOLS:
        for interval in runner.INTERVALS:
            frame, manifest = runner.load_train1(symbol, interval)
            checksums[f"{symbol}_{interval}"] = manifest.checksum_sha256
            for name in all_names:
                signal = entry_masks.strategy_signal_series(frame, name, interval=interval, now=runner.NOW)
                mask = entry_masks.one_shot_entry_mask(signal)
                signal_hashes[f"{symbol}_{interval}_{name}"] = hashlib.sha256(signal.to_csv().encode()).hexdigest()
                cells = [BASELINE] if name == runner.CONTROL_NAME else EXIT_GRID
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
                    entry_rows.extend({**identity, **e} for e in entry_trades(result.trades).to_dict("records"))
    prior = ecg.verify_prior(rows)
    control = runner.verify_harness_control(rows, runner.CONTROL_NAME, runner.CONTROL_REFERENCE_CSV)
    if any(r["n_trades"] > r["n_calls"] for r in rows):
        raise AssertionError("one-shot violation")
    results, monthly, entries = pd.DataFrame(rows), pd.DataFrame(monthly_rows), pd.DataFrame(entry_rows)
    ranks, pooled = ecg.rank_table(results), ecg.rank_table(results, pooled=True)
    fals = falsifier_table(results, monthly, entries)
    decision = verdict(results, fals)
    sources = ["strategy.py", "backtest_engine.py", "equity.py", "entry_masks.py",
               "scripts/f006_family_runner.py", "scripts/f006_catalog5_exit_class_grid.py", __file__]
    meta = dict(git_commit=tip, started_utc=started, python=sys.version, pandas=pd.__version__,
                exit_grid=EXIT_GRID, candidate_names=list(CANDIDATE_NAMES), n_runs=len(rows),
                checksums_used=checksums, signal_hashes=signal_hashes,
                source_sha256={str(Path(p).name): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
                train1_end=str(runner.TRAIN1_END), warmup_start=runner.WARMUP_START,
                fixed_params={**runner.FIXED_PARAMS, "max_sl_pct": runner.MAX_SL_PCT,
                              "stake": runner.STAKE, "initial_equity": runner.INITIAL_EQUITY,
                              "cooldown_candles": runner.COOLDOWN, "mask": "one_shot"},
                accounting="entry-level (partial+remainder legs of one parent_id = one trade)",
                sparse_month_bucket="each leg's exit month Europe/Warsaw; zero exits ABSENT; Train-1 months only",
                rank_metric="entry-weighted win_rate among exit grid; still report train1_net_pnl/H1",
                big_winner_definition="per name top-decile (ceil 10%) NO_TRAIL entries by net_pnl over 10 series",
                initial_sl_share_definition="entries ending at initial_sl with no partial banked / entries",
                prior_no_trail_check=prior, harness_control=control, one_shot_violations=0,
                verdict=decision, hypothesis_note="spec/research/F006-hypothesis-catalog5-partial-exit.md")
    OUT.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT / "results.csv", index=False)
    monthly.to_csv(OUT / "monthly.csv", index=False)
    pd.DataFrame(trades_rows).to_csv(OUT / "trades.csv", index=False)
    entries.to_csv(OUT / "entries.csv", index=False)
    ranks.to_csv(OUT / "rank_by_name.csv", index=False)
    pooled.to_csv(OUT / "rank_pooled.csv", index=False)
    fals.to_csv(OUT / "falsifiers_by_name.csv", index=False)
    (OUT / "manifest.json").write_text(json.dumps(meta, indent=2, default=str) + "\n")
    pd.set_option("display.width", 250)
    print(fals.to_string(index=False))
    print("\nPooled (descriptive):\n", pooled.to_string(index=False))
    print("\nVerdict:", json.dumps(decision, indent=2, default=str))
    print("\nChecks:", prior, control)


if __name__ == "__main__":
    main()
