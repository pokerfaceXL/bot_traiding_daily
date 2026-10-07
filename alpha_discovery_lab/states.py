"""F014 causal state builders — one function per registered hypothesis (registry.py is the spec).

Every builder returns a Case per asset: population / state masks on discovery bars, a continuous
score (oriented so that higher = deeper in state), targets y_h, the expression sign multiplier, and
the per-bar cost multiplier. Only bars t-720..t-1 feed thresholds (shift 1).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from alpha_discovery_lab.registry import PROTOCOL, SPLITS

LB = PROTOCOL["lookback_bars"]
VW = PROTOCOL["vol_window_bars"]
BW = PROTOCOL["breakout_window_bars"]
HORIZONS = PROTOCOL["horizons_reported"]
DISC_START = pd.Timestamp(SPLITS["discovery"][0])


class Skip(Exception):
    pass


@dataclass
class Case:
    asset: str
    pop: pd.Series                    # bool: eligible discovery bars
    S: pd.Series                      # bool: state (subset of pop)
    score: pd.Series                  # continuous score for IC
    y: dict                           # h -> Series target (bp, or unitless for VOL-COMPRESS)
    pos_base: pd.Series               # sign already embedded in y (1 for plain own fwd)
    px: pd.DataFrame | None           # traded-instrument OHLC for MFE/MAE (None for pairs)
    cost_mult: pd.Series
    trade_mask: pd.Series | None = None   # bars traded by the expression (default S)
    trade_sign: int | None = None         # multiplier on y for gross (default d)
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------- causal helpers
def r_bp(close: pd.Series, k: int = 1) -> pd.Series:
    return 1e4 * np.log(close / close.shift(k))


def fwd_bp(close: pd.Series, h: int) -> pd.Series:
    return 1e4 * np.log(close.shift(-h) / close)


def q_past(x: pd.Series, p: float, window: int = LB) -> pd.Series:
    """Quantile p of x over the previous `window` observations (excludes the current one)."""
    return x.rolling(window, min_periods=window).quantile(p).shift(1)


def disc(idx: pd.DatetimeIndex) -> pd.Series:
    return pd.Series(idx >= DISC_START, index=idx)


def sigma24(close: pd.Series) -> pd.Series:
    return r_bp(close).rolling(VW, min_periods=VW).std()


def trend_state(df: pd.DataFrame) -> pd.Series:
    hi = df["high"].shift(1).rolling(BW, min_periods=BW).max()
    lo = df["low"].shift(1).rolling(BW, min_periods=BW).min()
    ts = pd.Series(0.0, index=df.index)
    ts[df["close"] > hi] = 1.0
    ts[df["close"] < lo] = -1.0
    ts[hi.isna() | lo.isna()] = np.nan
    return ts


def beta_past(rx: pd.Series, rb: pd.Series) -> pd.Series:
    cov = rx.rolling(LB, min_periods=LB).cov(rb)
    var = rb.rolling(LB, min_periods=LB).var()
    return (cov / var).shift(1)


def _case(asset, df, valid, S, score, y, pos_base=None, cost_mult=None, px="self", **kw) -> Case:
    pop = (disc(df.index) & valid.fillna(False)).astype(bool)
    S = (S.fillna(False) & pop).astype(bool)
    one = pd.Series(1.0, index=df.index)
    return Case(asset=asset, pop=pop, S=S, score=score, y=y,
                pos_base=one if pos_base is None else pos_base,
                px=df if px == "self" else px, cost_mult=one if cost_mult is None else cost_mult, **kw)


def own_fwd(df: pd.DataFrame, mult: pd.Series | None = None) -> dict:
    m = 1.0 if mult is None else mult
    return {h: m * fwd_bp(df["close"], h) for h in HORIZONS}


# ---------------------------------------------------------------- Family A
def ps_rev(df, asset, up: bool):
    r = r_bp(df["close"])
    thr = q_past(r.abs(), 0.8)
    S = (r > 0 if up else r < 0) & (r.abs() > thr)
    return _case(asset, df, thr.notna() & r.notna(), S, r if up else -r, own_fwd(df))


def ps_trend(df, asset, up: bool):
    ts = trend_state(df)
    return _case(asset, df, ts.notna(), ts == (1 if up else -1), ts if up else -ts, own_fwd(df))


def ps_range_loc(df, asset, top: bool):
    rng = df["high"] - df["low"]
    loc = (df["close"] - df["low"]) / rng.where(rng > 0)
    q = q_past(loc, 0.8 if top else 0.2)
    S = loc > q if top else loc < q
    return _case(asset, df, loc.notna() & q.notna(), S, loc if top else -loc, own_fwd(df))


def ps_vol_compress(df, asset):
    sg = sigma24(df["close"])
    q = q_past(sg, 0.2)
    y = {h: fwd_bp(df["close"], h).abs() / (sg * np.sqrt(h)) for h in HORIZONS}
    return _case(asset, df, sg.notna() & q.notna(), sg < q, -sg, y)


def ps_gap_cont(df, asset):
    r = r_bp(df["close"]).where(df.index.hour == 0)
    g = r.dropna()
    thr = q_past(g.abs(), 0.8, window=30).reindex(df.index)
    sg = np.sign(r)
    valid = (df.index.hour == 0) & thr.notna() & r.notna() & (sg != 0)
    return _case(asset, df, pd.Series(valid, index=df.index), r.abs() > thr, r.abs(), own_fwd(df, sg),
                 pos_base=sg)


# ---------------------------------------------------------------- Family B
def _need(df, col, asset):
    if df[col].notna().sum() == 0:
        raise Skip(f"{asset}: no {col} data")


def der_fund(df, asset, top: bool):
    _need(df, "funding", asset)
    f = df["funding"]
    q = q_past(f, 0.8 if top else 0.2)
    return _case(asset, df, f.notna() & q.notna(), f > q if top else f < q, f if top else -f, own_fwd(df))


def der_fund_delta(df, asset):
    _need(df, "funding", asset)
    dF = df["funding"] - df["funding"].shift(24)
    q = q_past(dF, 0.8)
    return _case(asset, df, dF.notna() & q.notna(), (dF > 0) & (dF > q), dF, own_fwd(df))


def _doi(df, k):
    return 1e4 * np.log(df["oi"] / df["oi"].shift(k))


def der_oi_up(df, asset, px_up: bool):
    _need(df, "oi", asset)
    d4 = _doi(df, 4)
    r4 = r_bp(df["close"], 4)
    q = q_past(d4, 0.8)
    S = (d4 > q) & (r4 > 0 if px_up else r4 < 0)
    score = d4 * np.sign(r4) if px_up else -d4 * np.sign(r4)  # high dOI with matching price sign
    return _case(asset, df, d4.notna() & q.notna() & r4.notna(), S, score, own_fwd(df))


def der_oi_capit(df, asset):
    _need(df, "oi", asset)
    d4 = _doi(df, 4)
    r4 = r_bp(df["close"], 4)
    qo, qr = q_past(d4, 0.2), q_past(r4, 0.2)
    S = (d4 < qo) & (r4 < qr)
    return _case(asset, df, d4.notna() & r4.notna() & qo.notna() & qr.notna(), S, -(d4 + r4), own_fwd(df))


def der_oi_flat_move(df, asset):
    _need(df, "oi", asset)
    a1 = _doi(df, 1).abs()
    r = r_bp(df["close"])
    qo, qr = q_past(a1, 0.2), q_past(r.abs(), 0.8)
    sg = np.sign(r)
    S = (a1 < qo) & (r.abs() > qr)
    valid = a1.notna() & qo.notna() & qr.notna() & (sg != 0)
    return _case(asset, df, valid, S, r.abs() - a1, own_fwd(df, sg), pos_base=sg)


# ---------------------------------------------------------------- Family C
def of_buyratio(df, asset, kind: str):
    _need(df, "buyratio", asset)
    br = df["buyratio"]
    if kind == "spike":
        x = br - br.shift(4)
        q = q_past(x, 0.8)
        return _case(asset, df, x.notna() & q.notna(), x > q, x, own_fwd(df))
    top = kind == "hi"
    q = q_past(br, 0.8 if top else 0.2)
    return _case(asset, df, br.notna() & q.notna(), br > q if top else br < q, br if top else -br, own_fwd(df))


# ---------------------------------------------------------------- Family D
def _pair(frames, x):
    dx, db = frames[x], frames["BTCUSDT"].reindex(frames[x].index)
    rx, rb = r_bp(dx["close"]), r_bp(db["close"])
    beta = beta_past(rx, rb)
    e = rx - beta * rb
    resid = {h: fwd_bp(dx["close"], h) - beta * fwd_bp(db["close"], h) for h in HORIZONS}
    return dx, e, beta, resid


def xs_resid(frames, x, mode: str):
    dx, e, beta, resid = _pair(frames, x)
    cm = 1.0 + beta.abs()
    if mode == "abs":
        q = q_past(e.abs(), 0.8)
        sg = np.sign(e)
        y = {h: sg * v for h, v in resid.items()}
        return _case(x, dx, e.notna() & q.notna() & (sg != 0), e.abs() > q, e.abs(), y, pos_base=sg,
                     cost_mult=cm, px=None)
    top = mode == "up"
    q = q_past(e, 0.8 if top else 0.2)
    return _case(x, dx, e.notna() & q.notna(), e > q if top else e < q, e if top else -e, resid,
                 cost_mult=cm, px=None)


def xs_btc_lead(frames, x):
    dx = frames[x]
    rb = r_bp(frames["BTCUSDT"]["close"]).reindex(dx.index)
    q = q_past(rb.abs(), 0.8)
    sg = np.sign(rb)
    return _case(x, dx, rb.notna() & q.notna() & (sg != 0), rb.abs() > q, rb.abs(), own_fwd(dx, sg),
                 pos_base=sg)


# ---------------------------------------------------------------- Family E
def vol_regime_dir(df, asset):
    ts = trend_state(df)
    sg = sigma24(df["close"])
    qh, ql = q_past(sg, 0.8), q_past(sg, 0.2)
    hi, lo = sg > qh, sg < ql
    valid = (ts.abs() == 1) & qh.notna() & ql.notna() & (hi | lo)
    y = own_fwd(df, ts)
    c = _case(asset, df, valid, hi, sg, y, pos_base=ts)
    c.trade_mask = (c.pop & lo.fillna(False)).astype(bool)
    c.trade_sign = 1
    return c


def vol_spike(df, asset):
    r = r_bp(df["close"])
    q = q_past(r.abs(), 0.95)
    return _case(asset, df, r.notna() & q.notna(), r.abs() > q, r.abs(), own_fwd(df))


def vol_of_vol(df, asset):
    v = r_bp(df["close"]).abs().rolling(VW, min_periods=VW).std()
    q = q_past(v, 0.8)
    return _case(asset, df, v.notna() & q.notna(), v > q, v, own_fwd(df))


# ---------------------------------------------------------------- Family F
def time_hours(df, asset, hours):
    S = pd.Series(np.isin(df.index.hour, hours), index=df.index)
    valid = pd.Series(True, index=df.index)
    return _case(asset, df, valid, S, S.astype(float), own_fwd(df))


def time_funding(df, asset):
    _need(df, "funding", asset)
    sg = -np.sign(df["funding"])
    S = pd.Series(np.isin(df.index.hour, [22, 23, 6, 7, 14, 15]), index=df.index)
    return _case(asset, df, df["funding"].notna() & (sg != 0), S, S.astype(float), own_fwd(df, sg),
                 pos_base=sg)


# ---------------------------------------------------------------- dispatch
BUILDERS = {
    "H-PS-REV-UP": lambda F, a: ps_rev(F[a], a, True),
    "H-PS-REV-DN": lambda F, a: ps_rev(F[a], a, False),
    "H-PS-TREND-UP": lambda F, a: ps_trend(F[a], a, True),
    "H-PS-TREND-DN": lambda F, a: ps_trend(F[a], a, False),
    "H-PS-RANGE-LOC": lambda F, a: ps_range_loc(F[a], a, True),
    "H-PS-RANGE-LOC-DN": lambda F, a: ps_range_loc(F[a], a, False),
    "H-PS-VOL-COMPRESS": lambda F, a: ps_vol_compress(F[a], a),
    "H-PS-GAP-CONT": lambda F, a: ps_gap_cont(F[a], a),
    "H-DER-FUND-HI": lambda F, a: der_fund(F[a], a, True),
    "H-DER-FUND-LO": lambda F, a: der_fund(F[a], a, False),
    "H-DER-FUND-DELTA": lambda F, a: der_fund_delta(F[a], a),
    "H-DER-OI-UP-PX-UP": lambda F, a: der_oi_up(F[a], a, True),
    "H-DER-OI-UP-PX-DN": lambda F, a: der_oi_up(F[a], a, False),
    "H-DER-OI-DOWN-CAPIT": lambda F, a: der_oi_capit(F[a], a),
    "H-DER-OI-FLAT-MOVE": lambda F, a: der_oi_flat_move(F[a], a),
    "H-OF-BUYRATIO-HI": lambda F, a: of_buyratio(F[a], a, "hi"),
    "H-OF-BUYRATIO-LO": lambda F, a: of_buyratio(F[a], a, "lo"),
    "H-OF-BUYRATIO-SPIKE": lambda F, a: of_buyratio(F[a], a, "spike"),
    "H-XS-ETH-BTC-REV": lambda F, a: xs_resid(F, a, "up"),
    "H-XS-ETH-BTC-REV-DN": lambda F, a: xs_resid(F, a, "dn"),
    "H-XS-BTC-LEAD": lambda F, a: xs_btc_lead(F, a),
    "H-XS-SOL-BTC-REV": lambda F, a: xs_resid(F, a, "abs"),
    "H-VOL-REGIME-DIR": lambda F, a: vol_regime_dir(F[a], a),
    "H-VOL-SPIKE-DRIFT": lambda F, a: vol_spike(F[a], a),
    "H-VOL-OF-VOL": lambda F, a: vol_of_vol(F[a], a),
    "H-TIME-US-OPEN": lambda F, a: time_hours(F[a], a, [12, 13]),
    "H-TIME-ASIA": lambda F, a: time_hours(F[a], a, [23, 0, 1, 2]),
    "H-TIME-FUNDING-HOUR": lambda F, a: time_funding(F[a], a),
}


def build(hid: str, frames: dict, asset: str) -> Case:
    if asset not in frames:
        raise Skip(f"{asset}: no frame")
    return BUILDERS[hid](frames, asset)
