"""
trade_stats.py -- win/loss decomposition of a backtest's trade list (F006).

Additive research module. It reads a `BacktestResult.trades` frame and returns the
three quantities spec/research/F006-hypothesis-donchian.md's decomposition turned on,
and which spec/research/F006-hypothesis-trailing-sweep.md sweeps the exit parameters
against:

    avg_winner              mean net_pnl over winning trades
    avg_loser               mean net_pnl over losing trades (negative, or 0)
    breakeven_win_rate_pct  |avg_loser| / (avg_winner + |avg_loser|) * 100

The third is the win rate a name would need for zero expectancy at that trade
geometry: with winners of $1.46 against losers of -$2.55 a strategy must win 63.6% of
its trades to break even, which is the invariant the Donchian note measured and no
F006 name has come within 20 percentage points of.

WIN CONVENTION, reused not reinvented: a trade is a win iff `net_pnl > 0`, exactly
backtest_engine._compute_metrics' own `win_rate = (net_pnl > 0).mean() * 100`. A
zero-PnL trade is therefore counted on the LOSS side by both, and
tests/test_trade_stats.py asserts the two agree on a real engine run rather than
assuming it. Nothing here recomputes a metric the engine already publishes -- net_pnl
per trade comes straight from `result.trades`, and callers take win_rate,
total_net_pnl, max_drawdown_pct etc. from `result.metrics`.

POOLING: cells in an experiment grid contain many series with very different trade
counts, so a mean of per-series averages is not the per-trade figure it looks like.
`win_loss_decomposition` therefore also returns the raw sums and counts, and
`pool_decompositions` adds those up across runs before dividing -- the same
"pooled, not mean of ratios" discipline the Donchian note's tables use.

Zero network connections. Imports pandas only.
"""

from __future__ import annotations

from typing import Iterable, Optional

import pandas as pd

WIN_COLUMN = "net_pnl"


def breakeven_win_rate_pct(avg_winner: float, avg_loser: float) -> Optional[float]:
    """Win rate (in %) at which `avg_winner`/`avg_loser` trades have zero expectancy.

    `avg_loser` is expected to be <= 0 (the sign convention of `net_pnl`); its absolute
    value is used, so passing it either way round gives the same answer.

    Returns None when the quantity is undefined: `avg_winner + |avg_loser| == 0` means
    there is no trade geometry to speak of (no trades, or winners and losers both
    exactly zero). Callers must not silently turn that into 0.0 or 100.0 -- an empty
    cell is not a cell that breaks even for free.
    """
    denom = float(avg_winner) + abs(float(avg_loser))
    if denom == 0:
        return None
    return abs(float(avg_loser)) / denom * 100.0


def win_loss_decomposition(trades: pd.DataFrame) -> dict:
    """Split `trades` into winners and losers and describe the resulting geometry.

    Accepts the `BacktestResult.trades` frame (or any frame with a `net_pnl` column);
    an empty frame -- which the engine returns as a column-less DataFrame -- yields
    all-zero counts and None for the two ratios.
    """
    if trades is None or len(trades) == 0 or WIN_COLUMN not in getattr(trades, "columns", []):
        return {
            "n_trades": 0, "n_wins": 0, "n_losses": 0,
            "sum_wins": 0.0, "sum_losses": 0.0,
            "avg_winner": 0.0, "avg_loser": 0.0,
            "win_rate_pct": None, "breakeven_win_rate_pct": None,
        }
    net = pd.to_numeric(trades[WIN_COLUMN], errors="raise")
    wins = net[net > 0]
    losses = net[net <= 0]  # zero-PnL trades count as losses, as in backtest_engine's win_rate
    return _finish(int(len(net)), int(len(wins)), int(len(losses)),
                   float(wins.sum()), float(losses.sum()))


def pool_decompositions(parts: Iterable[dict]) -> dict:
    """Combine per-run decompositions into one pooled decomposition over all trades.

    Sums the counts and sums first, divides once -- so a 500-trade series and a
    12-trade series weigh by their trades, not equally.
    """
    n_trades = n_wins = n_losses = 0
    sum_wins = sum_losses = 0.0
    for part in parts:
        n_trades += int(part["n_trades"])
        n_wins += int(part["n_wins"])
        n_losses += int(part["n_losses"])
        sum_wins += float(part["sum_wins"])
        sum_losses += float(part["sum_losses"])
    return _finish(n_trades, n_wins, n_losses, sum_wins, sum_losses)


def _finish(n_trades: int, n_wins: int, n_losses: int, sum_wins: float, sum_losses: float) -> dict:
    avg_winner = (sum_wins / n_wins) if n_wins else 0.0
    avg_loser = (sum_losses / n_losses) if n_losses else 0.0
    return {
        "n_trades": n_trades,
        "n_wins": n_wins,
        "n_losses": n_losses,
        "sum_wins": sum_wins,
        "sum_losses": sum_losses,
        "avg_winner": avg_winner,
        "avg_loser": avg_loser,
        "win_rate_pct": (100.0 * n_wins / n_trades) if n_trades else None,
        "breakeven_win_rate_pct": breakeven_win_rate_pct(avg_winner, avg_loser),
    }
