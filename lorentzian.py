"""
lorentzian.py -- causal adapter for advanced-ta 0.1.8's Lorentzian Classification (F006).

Additive module: it adds new entries to strategy.STRATEGY_CATALOG (registered at
the bottom of strategy.py) and changes nothing in the existing engine.
backtest_engine.run_backtest calls the new entries through exactly the same
contract as every existing entry -- `run_backtest(df, "LORENTZIAN_default", ...)`.

WHY THIS MODULE EXISTS AT ALL (short form of spec/research/F006-lorentzian-causality.md,
section "Causality audit"): advanced-ta's documented usage --
`LorentzianClassification(df)` over the whole frame, then read the per-bar
`signal` column -- is NOT causal, for two independent reasons found by reading
the installed 0.1.8 source:

  L1  MLExtensions.normalize() fits an sklearn MinMaxScaler on the WHOLE array,
      so the WT and CCI features at bar i are scaled by the global min/max of the
      entire frame, including bars after i. That is real future-value leakage
      into 2 of the 5 default features, hence into every Lorentzian distance.

  L2  Classifier.__classify() derives maxBarsBackIndex = len(df) - maxBarsBack and
      keeps the `predictions`/`distances` neighbour lists alive across bars (Pine
      `var` semantics). The value yielded at bar i therefore depends on how many
      bars follow i in the frame handed to the library: append 50 bars and the
      number at bar i changes. No future price enters through L2, but the number
      is not reproducible from a prefix ending at bar i.

The algorithm itself is causal -- the neighbour scan is truncated at
`span = min(maxBarsBack, bar_index + 1)`, so no candidate index ever exceeds the
current bar, and the label array only ever compares src[i-4] with src[i]. The
defect is in the calling pattern. This module therefore reframes the call rather
than changing the algorithm:

  * features and filters come from advanced-ta's OWN functions
    (advanced_ta.LorentzianClassification.MLExtensions), unchanged, except that
    the two `normalize()` call sites (WT, CCI) are replaced by an expanding-window
    normalisation -- (x - cummin) / (cummax - cummin) over bars 0..i -- which is
    what MinMaxScaler would produce if it were only ever fit on the data available
    at bar i. That removes L1.
  * the neighbour loop is the library's own loop, transcribed line for line from
    Classifier.__classify() (see _knn_predictions below), with the accumulation
    anchored at the FIRST bar of the frame instead of at len(df) - maxBarsBack.
    That removes L2: the anchor no longer moves when bars are appended.

Net effect: the value at bar i is a function of bars 0..i only, bit-identical
whether the frame is truncated at bar i or continues for another 50 bars. That is
asserted, not assumed -- tests/test_lorentzian.py.

Scope cut (per spec/build.md, which separates the generator from useDynamicExits):
this module produces the ENTRY signal only. `useDynamicExits` stays at the library
default (False) and is not reproduced inside backtest_engine.py; exits remain the
engine's own max_sl_pct / trailing / signal-reversal rules.

Runtime note: advanced-ta 0.1.8 declares Requires-Python >=3.10,<4.0 and its
Classifier.py uses `match`/`case`, so it cannot even be imported on the project's
current Python 3.9 test venv. The import is therefore lazy: importing this module
is always safe, and only actually computing a Lorentzian signal raises
LorentzianUnavailable with an explicit message.

Zero network connections.
"""
from __future__ import annotations

import hashlib
from typing import Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# advanced-ta 0.1.8 defaults, read from Types.py / Classifier.__init__ --
# see spec/research/F006-lorentzian-causality.md section A. Not tuned in this slice.
DEFAULT_FEATURES: Tuple[Tuple[str, int, int], ...] = (
    ("RSI", 14, 2),   # f1
    ("WT", 10, 11),   # f2
    ("CCI", 20, 2),   # f3
    ("ADX", 20, 2),   # f4
    ("RSI", 9, 2),    # f5
)
DEFAULT_NEIGHBORS_COUNT = 8
DEFAULT_MAX_BARS_BACK = 2000
DEFAULT_USE_VOLATILITY_FILTER = True
DEFAULT_USE_REGIME_FILTER = True
DEFAULT_USE_ADX_FILTER = False
DEFAULT_REGIME_THRESHOLD = -0.1
DEFAULT_ADX_THRESHOLD = 20

_CACHE: dict = {}
_CACHE_MAX_ENTRIES = 8


class LorentzianUnavailable(ImportError):
    """advanced-ta is not importable in this interpreter (needs Python >= 3.10)."""


def _advanced_ta():
    """Lazy import of advanced-ta's own modules. Never imported at module import time."""
    try:
        from advanced_ta.LorentzianClassification import MLExtensions as ml
    except Exception as exc:  # SyntaxError on py3.9 (match/case), ImportError if absent
        raise LorentzianUnavailable(
            "advanced-ta 0.1.8 is required for the LORENTZIAN_* strategies but could not be "
            f"imported ({type(exc).__name__}: {exc}). It declares Requires-Python >=3.10,<4.0 "
            "and uses match/case syntax, so it cannot run on Python 3.9. Use a Python >=3.10 "
            "environment with `pip install -r requirements.txt`."
        ) from exc
    return ml


# ──────────────────────────────────────────────────────────────
#  Causal replacement for MLExtensions.normalize()
# ──────────────────────────────────────────────────────────────

def _expanding_normalize(src: np.ndarray) -> np.ndarray:
    """
    Causal counterpart of MLExtensions.normalize(): instead of MinMaxScaler fit on
    the whole array, rescale bar i by the min/max of bars 0..i. NaN warm-up values
    are ignored by the running min/max and stay NaN (MinMaxScaler behaves the same
    way -- it allows and preserves NaN).
    """
    s = pd.Series(np.asarray(src, dtype=float))
    lo = s.expanding().min()
    hi = s.expanding().max()
    rng = (hi - lo).to_numpy()
    out = np.divide(
        (s - lo).to_numpy(), rng,
        out=np.zeros(len(s), dtype=float), where=(rng > 0),
    )
    return np.where(np.isnan(s.to_numpy()), np.nan, out)


def _feature_series(ml, data: pd.DataFrame, kind: str, param_a: int, param_b: int) -> np.ndarray:
    """
    advanced-ta's Classifier.series_from, with the two leaky call sites fixed.

    RSI/ADX go through advanced-ta's n_rsi/n_adx unchanged: both use rescale() with
    fixed 0..100 bounds, which is already causal. WT/CCI reproduce n_wt/n_cci's own
    arithmetic (copied from MLExtensions 0.1.8) but finish with _expanding_normalize
    instead of the whole-array normalize().
    """
    from ta.trend import ema_indicator as EMA, sma_indicator as SMA, cci as CCI

    if kind == "RSI":
        return ml.n_rsi(data["close"], param_a, param_b)
    if kind == "ADX":
        return ml.n_adx(data["high"], data["low"], data["close"], param_a)
    if kind == "WT":
        hlc3 = (data["high"] + data["low"] + data["close"]) / 3
        ema1 = EMA(hlc3, param_a)
        ema2 = EMA(abs(hlc3 - ema1), param_a)
        ci = (hlc3 - ema1) / (0.015 * ema2)
        wt1 = EMA(ci, param_b)
        wt2 = SMA(wt1, 4)
        return _expanding_normalize((wt1 - wt2).values)
    if kind == "CCI":
        return _expanding_normalize(EMA(CCI(data["high"], data["low"], data["close"], param_a), param_b).values)
    raise ValueError(f"unknown Lorentzian feature type: {kind!r} (expected RSI/WT/CCI/ADX)")


# ──────────────────────────────────────────────────────────────
#  Neighbour search (advanced-ta's own loop, anchored start)
# ──────────────────────────────────────────────────────────────

def _knn_predictions(features: Sequence[np.ndarray], y_train: np.ndarray,
                     neighbors_count: int, max_bars_back: int) -> np.ndarray:
    """
    Transcription of advanced-ta 0.1.8 Classifier.__classify()'s
    get_lorentzian_predictions(), with one change: maxBarsBackIndex is pinned to 0
    (the first bar of the frame) instead of len(df) - maxBarsBack, so the
    accumulation anchor does not move when bars are appended (defect L2). The
    candidate set and the `span = min(maxBarsBack, bar_index + 1)` truncation are
    the library's, unchanged -- candidate index j is always <= bar_index, so the
    scan stays causal.

    Distances are the library's Lorentzian metric, sum over features of
    log(1 + |f[bar] - f[j]|), computed in numpy batches instead of the library's
    Distances class (same arithmetic, same candidate columns).
    """
    n = len(y_train)
    size = min(n, max_bars_back)          # candidate ("training") prefix, as in the library
    cand = [f[:size] for f in features]
    labels = np.rint(y_train[:size]).astype(float)

    predictions: list = []
    distances: list = []
    out = np.zeros(n, dtype=float)
    pop_index = round(neighbors_count * 3 / 4)

    batch = 256
    for start in range(0, n, batch):
        stop = min(start + batch, n)
        rows = np.zeros((stop - start, size), dtype=float)
        for f, c in zip(features, cand):
            rows += np.log(1.0 + np.abs(f[start:stop].reshape(-1, 1) - c.reshape(1, -1)))
        for local, bar_index in enumerate(range(start, stop)):
            last_distance = -1.0
            span = min(max_bars_back, bar_index + 1)
            row = rows[local]
            for j in range(span):
                d = row[j]
                if d >= last_distance and j % 4:
                    last_distance = d
                    distances.append(d)
                    predictions.append(labels[j])
                    if len(predictions) > neighbors_count:
                        last_distance = distances[pop_index]
                        distances.pop(0)
                        predictions.pop(0)
            out[bar_index] = float(sum(predictions))
    return out


# ──────────────────────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────────────────────

def compute_lorentzian(
    df: pd.DataFrame,
    features: Sequence[Tuple[str, int, int]] = DEFAULT_FEATURES,
    neighbors_count: int = DEFAULT_NEIGHBORS_COUNT,
    max_bars_back: int = DEFAULT_MAX_BARS_BACK,
    use_volatility_filter: bool = DEFAULT_USE_VOLATILITY_FILTER,
    use_regime_filter: bool = DEFAULT_USE_REGIME_FILTER,
    use_adx_filter: bool = DEFAULT_USE_ADX_FILTER,
    regime_threshold: float = DEFAULT_REGIME_THRESHOLD,
    adx_threshold: int = DEFAULT_ADX_THRESHOLD,
) -> pd.DataFrame:
    """
    Causal per-bar Lorentzian classification for `df` (needs open/high/low/close).

    Returns a DataFrame indexed like `df` with:
      prediction  -- the raw kNN vote, sum of the neighbour labels (range +/- neighborsCount)
      signal      -- advanced-ta's filtered, forward-filled state signal, +1/-1/0
      raw_signal  -- sign(prediction), +1/-1/0, no filters (the bare generator)
      filter_all  -- the volatility & regime & adx filter conjunction

    Every column at bar i is a function of bars 0..i only; see the module docstring.
    """
    ml = _advanced_ta()
    data = df[["open", "high", "low", "close"]].astype(float)
    src = data["close"]

    feats = [_feature_series(ml, data, kind, a, b) for (kind, a, b) in features]

    # Labels: advanced-ta's own y_train_array. src[i-4] vs src[i] -- past only.
    y_train = np.where(
        (src.shift(4) < src.shift(0)).to_numpy(), -1.0,
        np.where((src.shift(4) > src.shift(0)).to_numpy(), 1.0, 0.0),
    )

    prediction = _knn_predictions(feats, y_train, neighbors_count, max_bars_back)

    ohlc4 = (data["open"] + data["high"] + data["low"] + data["close"]) / 4
    filter_all = (
        ml.filter_volatility(data["high"], data["low"], data["close"], use_volatility_filter, 1, 10)
        & ml.regime_filter(ohlc4, data["high"], data["low"], use_regime_filter, regime_threshold)
        & ml.filter_adx(src, data["high"], data["low"], adx_threshold, use_adx_filter, 14)
    )

    # advanced-ta's signal construction, verbatim in effect: a bar with a zero vote
    # or a blocked filter produces None and inherits the previous bar's state
    # (the library's `for i in np.where(signal == None)[0]: signal[i] = signal[i-1]`),
    # with bar 0 defaulting to 0. Forward fill only -- causal.
    raw = np.sign(prediction).astype(float)
    gated = np.where(filter_all & (prediction != 0), raw, np.nan)
    signal = pd.Series(gated, index=df.index).ffill().fillna(0.0)

    return pd.DataFrame(
        {
            "prediction": prediction,
            "signal": signal.to_numpy(dtype=float).astype(int),
            "raw_signal": raw.astype(int),
            "filter_all": np.asarray(filter_all, dtype=bool),
        },
        index=df.index,
    )


def _cache_key(df: pd.DataFrame, kwargs: dict) -> str:
    h = hashlib.sha1()
    for col in ("open", "high", "low", "close"):
        h.update(np.ascontiguousarray(df[col].to_numpy(dtype=float)).tobytes())
    h.update(repr(sorted(kwargs.items())).encode())
    h.update(str(len(df)).encode())
    return h.hexdigest()


def lorentzian_frame(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """compute_lorentzian() memoised on the OHLC content, so the catalog's two entries
    (filtered / raw) do not pay for the neighbour search twice on the same frame."""
    key = _cache_key(df, kwargs)
    hit = _CACHE.get(key)
    if hit is not None and len(hit) == len(df):
        return hit
    frame = compute_lorentzian(df, **kwargs)
    if len(_CACHE) >= _CACHE_MAX_ENTRIES:
        _CACHE.pop(next(iter(_CACHE)))
    _CACHE[key] = frame
    return frame


def sig_lorentzian(df: pd.DataFrame, **kwargs) -> pd.Series:
    """Entry signal for STRATEGY_CATALOG: advanced-ta's filtered state signal, +1/-1/0."""
    return lorentzian_frame(df, **kwargs)["signal"].astype(int)


def sig_lorentzian_raw(df: pd.DataFrame, **kwargs) -> pd.Series:
    """Entry signal for STRATEGY_CATALOG: bare kNN vote sign, no volatility/regime filters."""
    return lorentzian_frame(df, **kwargs)["raw_signal"].astype(int)


def catalog_entries() -> dict:
    """New, additive STRATEGY_CATALOG entries. Registered from strategy.py."""
    return {
        # advanced-ta 0.1.8 defaults throughout (RSI/WT/CCI/ADX features,
        # neighborsCount=8, maxBarsBack=2000, volatility+regime filters on),
        # made causal per this module's docstring. No tuning in this slice.
        "LORENTZIAN_default": lambda df: sig_lorentzian(df),
        # Same classifier, but the bare kNN vote sign: no volatility/regime filter and
        # no state carry-over, so any difference between the two entries is attributable
        # to advanced-ta's filtering/forward-fill layer rather than to the generator.
        "LORENTZIAN_raw": lambda df: sig_lorentzian_raw(df),
    }
