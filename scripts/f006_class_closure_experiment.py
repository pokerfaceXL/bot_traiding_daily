#!/usr/bin/env python3
"""H-CATALOG5-CLASS-CLOSURE-01 -- class exhaustion check for four catalog5 names.

Frozen spec: spec/research/F006-hypothesis-catalog5-class-closure.md. Tests whether
each of BB_20_25_EMA200, EMA_50_200, EMA3_13_50_200, BB_20_2_EMA200 can have its
monthly floor lowered by the two decisive levers (long-only, breadth-regime) on its
OWN trades, instead of being frozen by analogy to EMA3_21_50_200.

Reuses the shared F006 harness primitives from f006_family_runner (frozen basket,
checksummed Train-1 loader, NO_TRAIL geometry, costs/capital) and
backtest_engine.run_backtest. No new engine code; Train-1 only; no look-ahead.

Per name: baseline (no gate), long-only (direction==1 filter), breadth-regime veto
B in {0.4, 0.6, 0.8} using the identical causal breadth definition from
scripts/f006_breadth_regime_experiment.py.

Falsification rule (per name): NOT exhausted (keep CONDITIONAL) iff some lever
lowers that name's own baseline pooled floor by >=1 month AND keeps >=50% of that
name's baseline big-winner PnL AND holds for >=2 of its baseline carrier symbols.
Otherwise exhausted -> FREEZE candidate.
"""
from __future__ import annotations
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import backtest_engine  # noqa: E402
import entry_masks  # noqa: E402
import f006_family_runner as fr  # noqa: E402

NAMES = ["BB_20_25_EMA200", "EMA_50_200", "EMA3_13_50_200", "BB_20_2_EMA200"]
BREADTH_GRID = [0.4, 0.6, 0.8]
BIG = 29.9  # autopsy top-decile winner cut
COHORT_START = pd.Timestamp("2024-03-01T00:00:00Z")
COHORT_END = pd.Timestamp("2025-03-01T00:00:00Z")
OUT = "output/f006_class_closure"


def above_ema200(df: pd.DataFrame) -> pd.Series:
    c = df["close"]
    ema = c.ewm(span=200, adjust=False).mean()
    above = c > ema
    above.iloc[:200] = False  # frozen warm-up guard: <200 closed bars => not above
    return above


def train1(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    et = pd.to_datetime(trades["entry_time"], utc=True)
    return trades[(et >= COHORT_START) & (et < COHORT_END)].copy()


def losing_months(trades: pd.DataFrame) -> int:
    if trades.empty:
        return 0
    t = trades.copy()
    t["m"] = pd.to_datetime(t["entry_time"], utc=True).dt.strftime("%Y-%m")
    monthly = t.groupby("m")["net_pnl"].sum()
    return int((monthly < 0).sum())


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    # load all 10 series once, compute per-interval breadth on the union index
    dfs = {}
    for s in fr.SYMBOLS:
        for iv in fr.INTERVALS:
            df, _ = fr.load_train1(s, iv)
            dfs[(s, iv)] = df
    breadth = {}
    for iv in fr.INTERVALS:
        aboves = {s: above_ema200(dfs[(s, iv)]) for s in fr.SYMBOLS}
        union = pd.DatetimeIndex(sorted(set().union(*[a.index for a in aboves.values()])))
        stack = pd.DataFrame({s: aboves[s].reindex(union).fillna(False) for s in fr.SYMBOLS})
        breadth[iv] = stack.sum(axis=1) / 5.0

    # per-name results
    verdicts = []
    for name in NAMES:
        print(f"\n{'='*60}")
        print(f"Processing {name}...")
        print('='*60)
        
        cells = {"BASELINE": None, "LONG_ONLY": "long", **{f"B{int(b * 100)}": b for b in BREADTH_GRID}}
        # trades[cell][ (symbol,interval) ] = train1 trade df
        trades = {cell: {} for cell in cells}
        rawrows = []
        
        for s in fr.SYMBOLS:
            for iv in fr.INTERVALS:
                df = dfs[(s, iv)]
                sig = entry_masks.strategy_signal_series(df, name, interval=iv, now=fr.NOW)
                base_mask = entry_masks.one_shot_entry_mask(sig)
                br = breadth[iv].reindex(df.index)
                
                for cell, lever in cells.items():
                    if lever is None:
                        mask = base_mask
                    elif lever == "long":
                        # long-only: direction==1 filter (faithful for NO_TRAIL one-shot)
                        mask = base_mask & (sig == 1)
                    else:
                        # breadth-regime veto
                        mask = base_mask & (br >= lever).fillna(False)
                    
                    res = backtest_engine.run_backtest(
                        df, name, interval=iv, now=fr.NOW, symbol=s,
                        initial_equity=fr.INITIAL_EQUITY, stake=fr.STAKE,
                        max_sl_pct=fr.MAX_SL_PCT, activate_pct=fr.ACTIVATE_PCT,
                        trail_pct=fr.TRAIL_PCT, cooldown_candles=fr.COOLDOWN,
                        entry_regime_mask=mask, **fr.FIXED_PARAMS,
                    )
                    tr = train1(res.trades)
                    trades[cell][(s, iv)] = tr
                    rawrows.append({
                        "name": name, "cell": cell, "symbol": s, "interval": iv,
                        "n_calls": int(mask.sum()), "n_trades": int(len(tr)),
                        "net": round(float(tr["net_pnl"].sum()) if len(tr) else 0.0, 4),
                    })

        # pooled + per-symbol aggregates per cell
        base_big = None
        base_n = None
        summary = []
        for cell in cells:
            allt = pd.concat([t for t in trades[cell].values() if len(t)], ignore_index=True) \
                if any(len(t) for t in trades[cell].values()) else pd.DataFrame(columns=["net_pnl", "entry_time", "exit_reason"])
            net = float(allt["net_pnl"].sum()) if len(allt) else 0.0
            n = int(len(allt))
            big = float(allt.loc[allt["net_pnl"] >= BIG, "net_pnl"].sum()) if len(allt) else 0.0
            if cell == "BASELINE":
                base_big = big
                base_n = n
            exit_mix = allt["exit_reason"].value_counts().to_dict() if len(allt) else {}
            # per symbol
            persym_net = {}
            persym_floor = {}
            for s in fr.SYMBOLS:
                st = pd.concat([trades[cell][(s, iv)] for iv in fr.INTERVALS if len(trades[cell][(s, iv)])],
                               ignore_index=True) if any(len(trades[cell][(s, iv)]) for iv in fr.INTERVALS) else pd.DataFrame(columns=["net_pnl", "entry_time"])
                persym_net[s] = round(float(st["net_pnl"].sum()) if len(st) else 0.0, 2)
                persym_floor[s] = losing_months(st)
            summary.append({
                "cell": cell,
                "n_trades": n,
                "net": round(net, 2),
                "mean_per_trade": round(net / n, 4) if n else None,
                "pooled_losing_months": losing_months(allt),
                "big_winner_pnl": round(big, 2),
                "big_winner_pnl_retained_pct": round(100 * big / base_big, 1) if base_big else None,
                "n_trades_vs_baseline_pct": round(100 * n / base_n, 1) if base_n else None,
                "symbols_net_positive": int(sum(v > 0 for v in persym_net.values())),
                "persym_net": persym_net,
                "persym_losing_months": persym_floor,
                "exit_mix": {k: int(v) for k, v in exit_mix.items()},
            })

        # write per-name results
        pd.DataFrame(rawrows).to_csv(f"{OUT}/{name}_results.csv", index=False)
        with open(f"{OUT}/{name}_summary.json", "w") as f:
            json.dump(summary, f, indent=2, default=str)

        # ---- report + falsification for this name
        base = summary[0]
        print(f"\n=== {name} (Train-1 pooled) ===")
        hdr = f"{'cell':<11}{'n':>5}{'net':>9}{'mt':>8}{'losMo':>7}{'bigPnL':>9}{'bigKept%':>10}{'nTr%':>7}{'symPos':>8}"
        print(hdr)
        for r in summary:
            print(f"{r['cell']:<11}{r['n_trades']:>5}{r['net']:>9.1f}"
                  f"{(r['mean_per_trade'] or 0):>8.2f}{r['pooled_losing_months']:>7}"
                  f"{r['big_winner_pnl']:>9.1f}{(r['big_winner_pnl_retained_pct'] or 0):>10.1f}"
                  f"{(r['n_trades_vs_baseline_pct'] or 0):>7.1f}{r['symbols_net_positive']:>8}")
        print("\nper-symbol losing-month floor (baseline -> each cell):")
        for s in fr.SYMBOLS:
            line = f"  {s:<9} " + " ".join(f"{r['cell']}={r['persym_losing_months'][s]}" for r in summary)
            print(line)

        # falsification (per-name rule from spec)
        # NOT exhausted (keep CONDITIONAL) iff some lever lowers that name's own baseline
        # pooled floor by >=1 month AND keeps >=50% of that name's baseline big-winner PnL
        # AND holds for >=2 of its baseline carrier symbols. Otherwise exhausted -> FREEZE.
        cands = summary[1:]  # exclude baseline
        best = min(cands, key=lambda r: r["pooled_losing_months"]) if cands else None
        
        baseline_floor = base["pooled_losing_months"]
        baseline_carriers = [s for s in fr.SYMBOLS if base["persym_net"][s] > 0]
        
        if best is None:
            verdict = "FREEZE (no levers tested)"
            reason = "no candidate levers"
        else:
            floor_improved = best["pooled_losing_months"] < baseline_floor
            big_retained = (best["big_winner_pnl_retained_pct"] or 0) >= 50.0
            carriers_held = sum(1 for s in baseline_carriers if best["persym_net"][s] > 0) >= 2
            
            if floor_improved and big_retained and carriers_held:
                verdict = f"KEEP (exception: {best['cell']} lowers floor)"
                reason = f"{best['cell']} lowers floor to {best['pooled_losing_months']} (vs {baseline_floor}), keeps {best['big_winner_pnl_retained_pct']:.1f}% big PnL, {sum(1 for s in baseline_carriers if best['persym_net'][s] > 0)}/{len(baseline_carriers)} carriers"
            else:
                verdict = "FREEZE (exhausted)"
                if not floor_improved:
                    reason = f"best cell {best['cell']} does not lower floor ({best['pooled_losing_months']} vs {baseline_floor} baseline)"
                elif not big_retained:
                    reason = f"best cell {best['cell']} keeps only {best['big_winner_pnl_retained_pct']:.1f}% big PnL (<50%)"
                else:
                    reason = f"best cell {best['cell']} holds only {sum(1 for s in baseline_carriers if best['persym_net'][s] > 0)}/{len(baseline_carriers)} carriers (<2)"
        
        print(f"\nbaseline pooled losing months: {baseline_floor}")
        if best:
            print(f"best cell: {best['cell']} with {best['pooled_losing_months']} losing months")
        print(f"VERDICT: {verdict}")
        print(f"  {reason}")
        
        verdicts.append({
            "name": name,
            "baseline_losing_months": baseline_floor,
            "best_cell": best["cell"] if best else None,
            "best_losing_months": best["pooled_losing_months"] if best else None,
            "verdict": verdict,
            "reason": reason,
            "baseline_carriers": baseline_carriers,
            "baseline_big_pnl": base["big_winner_pnl"],
        })

    # ---- write class-level summary
    with open(f"{OUT}/verdicts.json", "w") as f:
        json.dump(verdicts, f, indent=2, default=str)
    
    print("\n" + "="*60)
    print("CLASS-LEVEL SUMMARY")
    print("="*60)
    for v in verdicts:
        print(f"{v['name']:<20} {v['verdict']}")
    print()
    
    all_freeze = all("FREEZE" in v["verdict"] for v in verdicts)
    if all_freeze:
        print("ALL FOUR NAMES EXHAUSTED -> catalog5 class closure confirmed")
    else:
        exceptions = [v["name"] for v in verdicts if "KEEP" in v["verdict"]]
        print(f"EXCEPTIONS (not exhausted): {', '.join(exceptions)}")


if __name__ == "__main__":
    main()
