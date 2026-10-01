#!/usr/bin/env python3
"""F006 -- independent protocol autopsy of EMA3_21_50_200 (NO_TRAIL), Train-1 cohort.

Analysis only, on the existing immutable trade table
output/f006_catalog5_trio_autopsy/trades/EMA3_21_50_200_train1_trades.csv (no new backtest).
Purpose (RESEARCH_JOURNAL 2026-10-01): decide, on THIS name's own trades, whether an
entry-time (causal) feature separates initial_sl deaths from signal_reverse runners without
cutting the fat-tail winners -- i.e. whether the Donchian abs-ATR transfer actually holds here.

Causality note: features available AT ENTRY (causal, usable as a filter): atr_pct,
atr_percentile, calm, direction, symbol, interval, month. Features computed AFTER entry
(forward/outcome, diagnostic LABEL ONLY, never a filter): forward_signed_return_pct,
forward_agreement, mfe_pct, mae_pct, bars_held, quick_reverse, exit_reason, *_pnl.
"""
import pandas as pd
import numpy as np

SRC = "output/f006_catalog5_trio_autopsy/trades/EMA3_21_50_200_train1_trades.csv"
CAUSAL = ["atr_pct", "atr_percentile", "calm"]          # available at entry
FORWARD = ["forward_agreement", "mfe_pct", "mae_pct", "bars_held", "quick_reverse"]  # label only


def hdr(s): print("\n" + "=" * 78 + "\n" + s + "\n" + "=" * 78)


def main():
    df = pd.read_csv(SRC)
    df["dt"] = pd.to_datetime(df.entry_time, utc=True)
    df["month"] = df.dt.dt.strftime("%Y-%m")
    df["interval"] = df.symbol_interval.str.split("_").str[-1]
    df["symbol"] = df.symbol_interval.str.split("_").str[0]
    df["win"] = df.net_pnl > 0

    hdr("1. OVERALL (Train-1 pooled, 10 series)")
    print(f"n={len(df)}  net={df.net_pnl.sum():.2f}  mean/trade={df.net_pnl.mean():.3f}  "
          f"WR={100*df.win.mean():.2f}%  gross={df.gross_pnl.sum():.2f}  costs={df.total_costs.sum():.2f}")

    hdr("2. EXIT-REASON ECONOMICS")
    g = df.groupby("exit_reason").agg(n=("net_pnl", "size"), WR=("win", "mean"),
                                      mean=("net_pnl", "mean"), sum=("net_pnl", "sum"))
    g["WR"] = (100 * g["WR"]).round(1)
    g["share_%"] = (100 * g.n / len(df)).round(1)
    print(g.round(2).sort_values("sum", ascending=False))

    hdr("3. WINNER / LOSER CONCENTRATION")
    wins = df[df.win].net_pnl.sort_values(ascending=False)
    losses = df[~df.win].net_pnl
    tot = df.net_pnl.sum()
    for k in (1, 3, 5, 10):
        print(f"top {k:>2} winners = {wins.head(k).sum():.1f}  "
              f"({100*wins.head(k).sum()/tot:.0f}% of net)")
    print(f"wins: n={len(wins)} mean={wins.mean():.2f} median={wins.median():.2f} max={wins.max():.2f}")
    print(f"losses: n={len(losses)} mean={losses.mean():.2f} median={losses.median():.2f} min={losses.min():.2f}")

    hdr("4. PER SYMBOL / INTERVAL / DIRECTION")
    for col in ("symbol", "interval", "direction"):
        t = df.groupby(col).agg(n=("net_pnl", "size"), net=("net_pnl", "sum"),
                                mean=("net_pnl", "mean"), WR=("win", "mean"))
        t["WR"] = (100 * t.WR).round(1)
        print(f"\n-- by {col} --\n", t.round(2).sort_values("net", ascending=False))

    hdr("5. PER MONTH (losing-month structure)")
    m = df.groupby("month").agg(n=("net_pnl", "size"), net=("net_pnl", "sum"),
                                WR=("win", "mean"))
    m["WR"] = (100 * m.WR).round(1)
    m["neg"] = m.net < 0
    print(m.round(2))
    print(f"\nLosing months (pooled): {int(m.neg.sum())}/{len(m)}")

    hdr("5b. ARE LOSING MONTHS SHARED ACROSS SYMBOLS? (regime vs idiosyncratic)")
    piv = df.pivot_table(index="month", columns="symbol", values="net_pnl", aggfunc="sum").round(1)
    print(piv.fillna(0))
    sign = (piv < 0).sum(axis=1)
    print("\n# symbols net-negative per month (of 5):")
    print(sign.to_string())
    print(f"\nmonths where >=4/5 symbols negative (shared-regime months): "
          f"{list(sign[sign>=4].index)}")

    hdr("6. ENTRY-TIME (CAUSAL) FEATURE SEPARATION: initial_sl vs signal_reverse")
    sub = df[df.exit_reason.isin(["initial_sl", "signal_reverse"])]
    sep = sub.groupby("exit_reason")[CAUSAL].mean()
    print("means of entry-time features:\n", sep.round(3))
    print("\nwinners vs losers (entry-time features):")
    print(df.groupby("win")[CAUSAL].mean().round(3))

    hdr("6b. CAUSAL ATR-PERCENTILE GATE TRADE-OFF (mirror Donchian H-ABS-ATR criteria)")
    # Big-winner PnL = sum of positive net over the top decile of winners by size.
    big_cut = wins.quantile(0.90)
    big_mask = df.win & (df.net_pnl >= big_cut)
    big_total = df.loc[big_mask, "net_pnl"].sum()
    base_sl_share = (df.exit_reason == "initial_sl").mean()
    print(f"baseline: initial_sl share={100*base_sl_share:.1f}%  "
          f"big-winner PnL (top-decile wins, >= {big_cut:.1f})={big_total:.1f}  net={tot:.1f}")
    print("\nGATE = keep trades with atr_percentile <= T  (drop the highest-vol entries)")
    print(f"{'T':>6}{'kept':>7}{'net':>9}{'sl_share%':>10}{'sl_dropΔpp':>11}{'bigPnL_kept%':>13}")
    for T in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        kept = df[df.atr_percentile <= T]
        if len(kept) == 0:
            continue
        sl_share = (kept.exit_reason == "initial_sl").mean()
        big_kept = kept.loc[kept.win & (kept.net_pnl >= big_cut), "net_pnl"].sum()
        print(f"{T:>6.2f}{len(kept):>7}{kept.net_pnl.sum():>9.1f}"
              f"{100*sl_share:>10.1f}{100*(base_sl_share-sl_share):>11.2f}"
              f"{100*big_kept/big_total if big_total else 0:>13.1f}")
    print("\nGATE = keep trades with atr_percentile >= T  (drop the lowest-vol entries)")
    print(f"{'T':>6}{'kept':>7}{'net':>9}{'sl_share%':>10}{'sl_dropΔpp':>11}{'bigPnL_kept%':>13}")
    for T in (0.1, 0.2, 0.3, 0.4, 0.5):
        kept = df[df.atr_percentile >= T]
        sl_share = (kept.exit_reason == "initial_sl").mean()
        big_kept = kept.loc[kept.win & (kept.net_pnl >= big_cut), "net_pnl"].sum()
        print(f"{T:>6.2f}{len(kept):>7}{kept.net_pnl.sum():>9.1f}"
              f"{100*sl_share:>10.1f}{100*(base_sl_share-sl_share):>11.2f}"
              f"{100*big_kept/big_total if big_total else 0:>13.1f}")

    hdr("7. FORWARD/OUTCOME FEATURES (LABEL ONLY -- not usable as entry filter)")
    print(df.groupby("win")[FORWARD].mean().round(3))
    print("\nquick_reverse rate by exit_reason:")
    print(df.groupby("exit_reason").quick_reverse.mean().round(3))


if __name__ == "__main__":
    main()
