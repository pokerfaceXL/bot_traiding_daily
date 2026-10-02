#!/usr/bin/env python3
"""H-CATALOG5-BREADTH-REGIME-01 -- causal basket-breadth entry veto on EMA3_21_50_200.

Frozen spec: spec/research/F006-hypothesis-catalog5-breadth-regime.md. Reuses the shared
F006 harness primitives from f006_family_runner (frozen basket, checksummed Train-1 loader,
NO_TRAIL geometry, costs/capital) and backtest_engine.run_backtest -- the SAME engine call
_run_one makes -- so the BASELINE cell reproduces the EMA3_21 autopsy (+817 net / 402 trades /
7 losing months) as a built-in control. No new engine code; Train-1 only; no look-ahead.

breadth(i) = (# of the 5 basket symbols whose close > its own EMA200 at bar i) / 5, same
interval, causal (EMA200 = ewm(span=200, adjust=False) as in strategy.py; first 200 bars of
each symbol forced not-above per the frozen warm-up rule -- these fall before the Mar-2024
cohort). Entry taken only if breadth(i) >= B. Exits unchanged (veto masks entries only).
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

NAME = "EMA3_21_50_200"
GRID = [0.4, 0.6, 0.8]
BIG = 29.9  # autopsy top-decile winner cut
COHORT_START = pd.Timestamp("2024-03-01T00:00:00Z")
COHORT_END = pd.Timestamp("2025-03-01T00:00:00Z")
OUT = "output/f006_breadth_regime"


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

    cells = {"BASELINE": None, **{f"B{int(b * 100)}": b for b in GRID}}
    # trades[cell][ (symbol,interval) ] = train1 trade df
    trades = {cell: {} for cell in cells}
    rawrows = []
    for s in fr.SYMBOLS:
        for iv in fr.INTERVALS:
            df = dfs[(s, iv)]
            sig = entry_masks.strategy_signal_series(df, NAME, interval=iv, now=fr.NOW)
            base_mask = entry_masks.one_shot_entry_mask(sig)
            br = breadth[iv].reindex(df.index)
            for cell, B in cells.items():
                mask = base_mask if B is None else (base_mask & (br >= B).fillna(False))
                res = backtest_engine.run_backtest(
                    df, NAME, interval=iv, now=fr.NOW, symbol=s,
                    initial_equity=fr.INITIAL_EQUITY, stake=fr.STAKE,
                    max_sl_pct=fr.MAX_SL_PCT, activate_pct=fr.ACTIVATE_PCT,
                    trail_pct=fr.TRAIL_PCT, cooldown_candles=fr.COOLDOWN,
                    entry_regime_mask=mask, **fr.FIXED_PARAMS,
                )
                tr = train1(res.trades)
                trades[cell][(s, iv)] = tr
                rawrows.append({
                    "cell": cell, "symbol": s, "interval": iv,
                    "n_calls": int(mask.sum()), "n_trades": int(len(tr)),
                    "net": round(float(tr["net_pnl"].sum()) if len(tr) else 0.0, 4),
                })

    # pooled + per-symbol aggregates per cell
    base_big = None
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

    pd.DataFrame(rawrows).to_csv(f"{OUT}/results.csv", index=False)
    with open(f"{OUT}/summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    # ---- report + falsifiers
    base = summary[0]
    print("\n=== H-CATALOG5-BREADTH-REGIME-01 (EMA3_21_50_200, Train-1 pooled) ===")
    hdr = f"{'cell':<9}{'n':>5}{'net':>9}{'mt':>8}{'losMo':>7}{'bigPnL':>9}{'bigKept%':>10}{'nTr%':>7}{'symPos':>8}"
    print(hdr)
    for r in summary:
        print(f"{r['cell']:<9}{r['n_trades']:>5}{r['net']:>9.1f}"
              f"{(r['mean_per_trade'] or 0):>8.2f}{r['pooled_losing_months']:>7}"
              f"{r['big_winner_pnl']:>9.1f}{(r['big_winner_pnl_retained_pct'] or 0):>10.1f}"
              f"{(r['n_trades_vs_baseline_pct'] or 0):>7.1f}{r['symbols_net_positive']:>8}")
    print("\nper-symbol losing-month floor (baseline -> each cell):")
    for s in fr.SYMBOLS:
        line = f"  {s:<9} " + " ".join(f"{r['cell']}={r['persym_losing_months'][s]}" for r in summary)
        print(line)

    # falsifiers (any one => FALSIFIED)
    cands = summary[1:]
    best = min(cands, key=lambda r: r["pooled_losing_months"])
    fa = all(r["pooled_losing_months"] >= base["pooled_losing_months"] for r in cands)  # no B lowers floor
    fb = (best["big_winner_pnl_retained_pct"] or 0) < 50.0
    carriers = [s for s in fr.SYMBOLS if base["persym_net"][s] > 0]
    fc = sum(1 for s in carriers if best["persym_net"][s] > 0) <= 1  # improvement single-symbol
    fd = (best["n_trades_vs_baseline_pct"] or 0) < 40.0  # >60% trade drop
    print("\nbaseline pooled losing months:", base["pooled_losing_months"],
          "| best cell:", best["cell"], best["pooled_losing_months"])
    print(f"falsifier (a) no B lowers floor below baseline : {fa}")
    print(f"falsifier (b) best-floor cell keeps <50% big PnL: {fb}")
    print(f"falsifier (c) improvement single-symbol         : {fc}")
    print(f"falsifier (d) best-floor n_trades drops >60%    : {fd}")
    print("VERDICT:", "FALSIFIED" if (fa or fb or fc or fd) else "NOT FALSIFIED (candidate)")


if __name__ == "__main__":
    main()
