"""
beta_gate.py -- rolling beta / correlation gate on an alt continuation trigger (F006 hypothesis
H-BETA-GATE-01, spec/research/F006-hypothesis-beta-gate.md).

Additive module, same layer as donchian.py/lorentzian.py: it adds new runtime-only entries for
strategy.STRATEGY_CATALOG via catalog_entries(), registered by scripts/f006_beta_gate_experiment.py
through f006_family_runner.run_family's catalog_entries kwarg -- strategy.py is never edited.

WHY THIS EXISTS. Every other closed F006 gate/filter (cross-symbol agreement, width expansion,
trend confirm, H-BTC-FILTER-01's structural permission bit) is either a same-bar cross-sectional
vote among the 5 basket symbols or a single discrete regime flag. This tests a continuous,
rolling-window statistical relationship (an OLS beta of an alt's returns to BTC's) as the gate
itself, per the frozen mechanism in the hypothesis note.

UNLIKE donchian.py/lorentzian.py, the two catalog functions here are NOT pure functions of their
own df: run_family calls STRATEGY_CATALOG[name](work) with only the traded symbol's own frame (no
symbol name, no interval), but this gate needs BTC's own close series too. load_btc_close/
_infer_interval are the only I/O-touching parts of this module (data_contract, module-level
cache); rolling_beta/btc_bias/gated_trend_signal/gated_mr_signal are pure functions of two
already-aligned Series and take no dependency on data_contract, so they are unit-testable without
any CSV.

Zero network connections.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import data_contract
import donchian

# Frozen in the hypothesis note -- not retuned after seeing Train-1.
WINDOW = 48
BETA_MIN = 0.5
BETA_LOW = 0.2
ALT_TRIGGER_LOOKBACK = 20  # donchian.sig_donchian_breakout(df, 20), reused unmodified

# spec/research/F005-validation-protocol.md section 6, BTCUSDT rows only -- duplicated from
# scripts/f006_family_runner.py's own EXPECTED_CHECKSUMS, same precedent as every prior F006
# script that needed a second data source (e.g. scripts/f006_entry_cross_symbol_experiment.py).
BTC_CHECKSUMS = {
    "240": "94491aead67f72d67a8cf0723d383966309ea119426b82793ef18835a36c61eb",
    "60": "66776a15cbe6f3bb5f55c5de2d7aa1e510061a65b3a49f9263057a8c69e01ad6",
}
WARMUP_START = "2024-01-26T00:00:00Z"
TRAIN1_END = pd.Timestamp("2025-03-01T00:00:00Z")

_btc_close_cache: dict = {}


def _infer_interval(index: pd.DatetimeIndex) -> str:
    """The frozen basket only ever produces 60m or 240m bars; pick the nearer one.

    Mechanical consequence of run_family's fn(df) -> pd.Series catalog contract, which passes
    neither symbol nor interval to the catalog function (see module docstring).
    """
    diffs = pd.Series(index).diff().dropna()
    if diffs.empty:
        raise ValueError("cannot infer interval from an index with fewer than 2 bars")
    median_minutes = diffs.median().total_seconds() / 60.0
    return "60" if abs(median_minutes - 60) <= abs(median_minutes - 240) else "240"


def load_btc_close(interval: str) -> pd.Series:
    """BTCUSDT close, Train-1 + warm-up window, checksum-verified, cached per interval."""
    if interval in _btc_close_cache:
        return _btc_close_cache[interval]
    df, manifest = data_contract.load_dataset("data_cache", "BTCUSDT", interval, WARMUP_START, TRAIN1_END)
    expected = BTC_CHECKSUMS[interval]
    if manifest.checksum_sha256 != expected:
        raise SystemExit(
            f"STOP: checksum mismatch for BTCUSDT/{interval}: cache has "
            f"{manifest.checksum_sha256}, protocol section 6 expects {expected}."
        )
    close = df["close"].astype(float)
    _btc_close_cache[interval] = close
    return close


def rolling_beta(alt_close: pd.Series, btc_close: pd.Series, window: int) -> pd.Series:
    """Rolling OLS beta of alt's 1-bar log returns on BTC's, Cov(alt_ret, btc_ret) / Var(btc_ret).

    Computed on the intersection of the two indices, reindexed back onto alt_close's own index
    (NaN where BTC data is unavailable at a bar, or during the first `window` bars of warm-up).
    """
    alt_ret = np.log(alt_close.astype(float)).diff()
    btc_ret = np.log(btc_close.astype(float)).diff()
    common = alt_ret.index.intersection(btc_ret.index)
    a = alt_ret.reindex(common)
    b = btc_ret.reindex(common)
    cov = a.rolling(window).cov(b)
    var = b.rolling(window).var()
    beta = cov / var
    return beta.reindex(alt_close.index)


def btc_bias(btc_close: pd.Series, window: int) -> pd.Series:
    """+1 above BTC's own trailing `window`-bar SMA, -1 below, 0 exactly on it (or during warm-up)."""
    close = btc_close.astype(float)
    sma = close.rolling(window).mean()
    bias = pd.Series(0, index=close.index, dtype=int)
    bias[close > sma] = 1
    bias[close < sma] = -1
    bias[sma.isna()] = 0
    return bias


def gated_trend_signal(alt_df: pd.DataFrame, btc_close: pd.Series, *, window: int = WINDOW,
                        beta_min: float = BETA_MIN) -> pd.Series:
    """BETA_GATE_DONCH20: the Donchian-20 trigger, allowed only when beta > beta_min AND BTC's
    own bias agrees with the trigger's direction."""
    alt_trigger = donchian.sig_donchian_breakout(alt_df, ALT_TRIGGER_LOOKBACK)
    beta = rolling_beta(alt_df["close"], btc_close, window)
    bias = btc_bias(btc_close, window).reindex(alt_df.index).fillna(0).astype(int)
    allow = (beta > beta_min) & (
        ((alt_trigger == 1) & (bias == 1)) | ((alt_trigger == -1) & (bias == -1))
    )
    allow = allow.fillna(False)
    return (alt_trigger * allow.astype(int)).astype(int)


def gated_mr_signal(alt_df: pd.DataFrame, btc_close: pd.Series, *, window: int = WINDOW,
                     beta_low: float = BETA_LOW) -> pd.Series:
    """BETA_GATE_MR_DONCH20: a same-bar fade of the Donchian-20 trigger, allowed only when
    beta < beta_low (decoupled from BTC). No BTC-bias condition -- a decoupled alt is not read
    against BTC's own trend by construction."""
    alt_trigger = donchian.sig_donchian_breakout(alt_df, ALT_TRIGGER_LOOKBACK)
    beta = rolling_beta(alt_df["close"], btc_close, window)
    allow = (beta < beta_low).fillna(False)
    return ((-alt_trigger) * allow.astype(int)).astype(int)


def _trend_catalog_fn(df: pd.DataFrame) -> pd.Series:
    interval = _infer_interval(df.index)
    btc_close = load_btc_close(interval)
    return gated_trend_signal(df, btc_close)


def _mr_catalog_fn(df: pd.DataFrame) -> pd.Series:
    interval = _infer_interval(df.index)
    btc_close = load_btc_close(interval)
    return gated_mr_signal(df, btc_close)


def catalog_entries() -> dict:
    """New, additive, runtime-only STRATEGY_CATALOG entries. Never edits strategy.py."""
    return {
        "BETA_GATE_DONCH20": _trend_catalog_fn,
        "BETA_GATE_MR_DONCH20": _mr_catalog_fn,
    }
