"""
Regression tests for trade_stats.py -- the win/loss decomposition
spec/research/F006-hypothesis-trailing-sweep.md reads as its outcome variable.

Three things are pinned here, because a wrong breakeven_win_rate_pct would not look
wrong -- it would just quietly move the conclusion of the whole slice:

  1. The arithmetic, against numbers computed by hand in the docstrings below (and
     against the one figure already on record: the Donchian note's $1.46 / -$2.55
     geometry needs a 63.6% win rate).
  2. The boundaries, where a formula with a division in it goes wrong: no winners,
     no losers, no trades, and the zero-PnL trade that must land on the loss side
     because that is where backtest_engine's own win_rate puts it.
  3. Agreement with the engine on a real run, so the "reused, not reimplemented"
     claim in the module docstring is checked rather than asserted: the helper's win
     count over result.trades must reproduce result.metrics["win_rate"], and its sums
     must reproduce result.metrics["total_net_pnl"].
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine as be
import trade_stats

OHLCV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ohlcv_sample.csv")

# Seven trades, hand-decomposed:
#   wins   : 3.00, 1.50, 4.50            -> n=3, sum= 9.00, avg = 9.00/3 = 3.000
#   losses : -2.00, -2.50, 0.00, -1.00   -> n=4, sum=-5.50, avg = -5.50/4 = -1.375
#   win rate            = 3/7            = 42.857142857...%
#   breakeven win rate  = 1.375 / (3.000 + 1.375) = 1.375/4.375 = 31.428571428...%
#   expectancy          = (9.00 - 5.50)/7 = 0.50 per trade, and 42.86% > 31.43% --
#   i.e. this fixture is deliberately a PROFITABLE geometry, the opposite of every
#   cell F006 has measured, so a sign error in the formula cannot hide behind it.
HAND_PNLS = [3.00, -2.00, 1.50, -2.50, 0.00, 4.50, -1.00]


def _frame(pnls):
    return pd.DataFrame({"net_pnl": pnls, "exit_reason": ["x"] * len(pnls)})


def test_decomposition_matches_the_hand_calculation():
    d = trade_stats.win_loss_decomposition(_frame(HAND_PNLS))

    assert d["n_trades"] == 7
    assert d["n_wins"] == 3
    assert d["n_losses"] == 4
    assert d["sum_wins"] == pytest.approx(9.00)
    assert d["sum_losses"] == pytest.approx(-5.50)
    assert d["avg_winner"] == pytest.approx(3.000)
    assert d["avg_loser"] == pytest.approx(-1.375)
    assert d["win_rate_pct"] == pytest.approx(42.857142857, rel=1e-9)
    assert d["breakeven_win_rate_pct"] == pytest.approx(31.428571428, rel=1e-9)


def test_expectancy_is_zero_exactly_at_the_breakeven_win_rate():
    """The definition, restated as the property it is supposed to have.

    At win rate p, expectancy is p*avg_winner + (1-p)*avg_loser. Plugging in the
    returned breakeven rate must give 0 -- this is what makes the number mean
    "the win rate this trade geometry would need", and it fails for any formula that
    gets the ratio the wrong way up.
    """
    d = trade_stats.win_loss_decomposition(_frame(HAND_PNLS))
    p = d["breakeven_win_rate_pct"] / 100.0
    assert p * d["avg_winner"] + (1 - p) * d["avg_loser"] == pytest.approx(0.0, abs=1e-12)


def test_reproduces_the_donchian_notes_published_geometry():
    """spec/research/F006-hypothesis-donchian.md: $1.46 winner vs -$2.55 loser needs ~63%."""
    assert trade_stats.breakeven_win_rate_pct(1.46, -2.55) == pytest.approx(63.5910, abs=1e-4)
    # and the symmetric geometry needs exactly half the trades to win
    assert trade_stats.breakeven_win_rate_pct(2.0, -2.0) == pytest.approx(50.0)
    # sign of avg_loser must not matter: |avg_loser| is what the formula uses
    assert trade_stats.breakeven_win_rate_pct(1.46, 2.55) == pytest.approx(63.5910, abs=1e-4)


def test_zero_pnl_trade_counts_as_a_loss_exactly_as_the_engine_does():
    d = trade_stats.win_loss_decomposition(_frame([1.0, 0.0]))
    assert d["n_wins"] == 1 and d["n_losses"] == 1
    assert d["avg_loser"] == 0.0
    # engine convention, verbatim from backtest_engine._compute_metrics
    net = pd.Series([1.0, 0.0])
    assert d["win_rate_pct"] == pytest.approx(float((net > 0).mean() * 100))


def test_degenerate_cells_do_not_silently_become_numbers():
    all_losers = trade_stats.win_loss_decomposition(_frame([-1.0, -3.0]))
    assert all_losers["avg_winner"] == 0.0
    assert all_losers["breakeven_win_rate_pct"] == pytest.approx(100.0)  # needs every trade to win

    all_winners = trade_stats.win_loss_decomposition(_frame([1.0, 3.0]))
    assert all_winners["avg_loser"] == 0.0
    assert all_winners["breakeven_win_rate_pct"] == pytest.approx(0.0)

    empty = trade_stats.win_loss_decomposition(pd.DataFrame())
    assert empty["n_trades"] == 0
    assert empty["breakeven_win_rate_pct"] is None  # not 0.0, not 100.0
    assert empty["win_rate_pct"] is None
    assert trade_stats.win_loss_decomposition(None)["breakeven_win_rate_pct"] is None

    # winners and losers all exactly zero: no geometry, so no breakeven rate
    assert trade_stats.win_loss_decomposition(_frame([0.0, 0.0]))["breakeven_win_rate_pct"] is None


def test_pooling_weighs_by_trades_not_by_series():
    """A 6-trade series and a 1-trade series must not count equally.

    Pooling the two parts has to equal decomposing the concatenation -- that identity
    is the whole reason the experiment stores sums and counts per run instead of
    averaging each run's avg_winner.
    """
    big, small = HAND_PNLS[:6], HAND_PNLS[6:]
    pooled = trade_stats.pool_decompositions([
        trade_stats.win_loss_decomposition(_frame(big)),
        trade_stats.win_loss_decomposition(_frame(small)),
    ])
    whole = trade_stats.win_loss_decomposition(_frame(HAND_PNLS))
    for key in ("n_trades", "n_wins", "n_losses", "sum_wins", "sum_losses",
                "avg_winner", "avg_loser", "win_rate_pct", "breakeven_win_rate_pct"):
        assert pooled[key] == pytest.approx(whole[key]), key

    # and it is genuinely different from the mean of the two series' averages
    mean_of_ratios = (trade_stats.win_loss_decomposition(_frame(big))["avg_loser"]
                      + trade_stats.win_loss_decomposition(_frame(small))["avg_loser"]) / 2
    assert pooled["avg_loser"] != pytest.approx(mean_of_ratios)

    assert trade_stats.pool_decompositions([])["breakeven_win_rate_pct"] is None


def test_agrees_with_the_engines_own_metrics_on_a_real_run():
    df = pd.read_csv(OHLCV, index_col=0, parse_dates=True)
    result = be.run_backtest(
        df, "EMA_8_21", interval="240", now=df.index[-1] + pd.Timedelta(hours=4),
        initial_equity=500.0, stake=100.0, leverage=1.0, max_sl_pct=0.03,
        activate_pct=0.03, trail_pct=0.02,
    )
    assert len(result.trades) >= 5, "fixture must produce enough trades for this to mean anything"

    d = trade_stats.win_loss_decomposition(result.trades)
    assert d["n_trades"] == result.metrics["n_trades"]
    assert round(d["win_rate_pct"], 2) == result.metrics["win_rate"]
    assert d["sum_wins"] + d["sum_losses"] == pytest.approx(result.metrics["total_net_pnl"], abs=1e-6)
    assert d["n_wins"] + d["n_losses"] == d["n_trades"]
    # the engine's profit_factor is the same two sums, so it pins avg_winner/avg_loser
    # against a number computed independently inside backtest_engine
    if d["sum_losses"] != 0:
        assert result.metrics["profit_factor"] == pytest.approx(
            d["sum_wins"] / abs(d["sum_losses"]), abs=1e-6)
