"""F011 T3: forced-flow state-entry event study on the 5m T2 states (non-trading).

Answers H-FORCEDFLOW-CONTINUATION-01 and H-FORCEDFLOW-EXHAUSTION-01 (spec/research/
F011-forced-flow-lab.md §9, amended 2026-10-06). No orders, positions, sizing or PnL.

Event = state entry. A hypothesis owns a set of states per side; bar t is an entry when its
state is in the side's set and bar t-1's is not (STRESS -> CASCADE on the same side is one
continuing episode, not a new entry).

Timing. A T2 label for bar t (bar-open timestamp) is available at bar t's close, so the
event's reference price is close_t and the forward return at horizon h bars is
close_{t+h} / close_t - 1. Events whose t+h falls past the last labelled bar (Train-1 end)
are dropped, never truncated: every horizon window ends at or before the data end.

Overlap policy: per hypothesis x symbol x horizon, events are thinned greedily in time
order so that no kept event starts before the previous kept event's horizon window has
closed (next kept t >= previous kept t + h). Long- and short-side entries share one stream.
The event set therefore shrinks with the horizon; raw entry counts are reported too.

Signing: forward returns are multiplied by the hypothesis' predicted direction, so a
positive signed return always means "moved the way the hypothesis says".
  continuation: LONG_* side predicts down (-1), SHORT_* side predicts up (+1)
  exhaustion:   LONG_EXHAUSTION predicts up (+1), SHORT_EXHAUSTION predicts down (-1)
Baseline: the unconditional forward return over every labelled bar of the same symbol
with a complete window, signed by each event's side (side-mix weighted).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from forced_flow_lab import label_states as ls

STATES = Path("output/f011_forced_flow/states")
OUTPUT = Path("output/f011_forced_flow/event_study")
SYMBOLS = ("BTCUSDT", "ETHUSDT")
COST_BAND = 0.0034  # 34 bps round trip: (10 commission + 5 half-spread + 2 slippage) x 2 sides
HYPOTHESES = {
    "H-FORCEDFLOW-CONTINUATION-01": {
        "sides": {-1: ("LONG_STRESS", "LONG_LIQUIDATION_CASCADE"),
                  +1: ("SHORT_STRESS", "SHORT_LIQUIDATION_CASCADE")},
        "horizons": {"5m": 1, "15m": 3, "30m": 6, "60m": 12, "4h": 48},
    },
    "H-FORCEDFLOW-EXHAUSTION-01": {
        "sides": {+1: ("LONG_EXHAUSTION",), -1: ("SHORT_EXHAUSTION",)},
        "horizons": {"5m": 1, "15m": 3, "30m": 6, "60m": 12, "4h": 48, "8h": 96},
    },
}


def entries(state: pd.Series, sides: dict) -> pd.DataFrame:
    """Positional index and predicted direction of every state entry (no overlap filter)."""
    values = state.to_numpy()
    rows = []
    for direction, names in sides.items():
        inside = np.isin(values, names)
        prev = np.concatenate(([False], inside[:-1]))
        for pos in np.flatnonzero(inside & ~prev):
            rows.append((int(pos), direction))
    return pd.DataFrame(sorted(rows), columns=["pos", "direction"])


def forward_returns(close: pd.Series, horizon: int) -> np.ndarray:
    """close_{t+h}/close_t - 1; NaN where t+h is past the last row (no truncated windows)."""
    c = close.to_numpy(dtype=float)
    out = np.full(len(c), np.nan)
    if horizon < len(c):
        out[:-horizon] = c[horizon:] / c[:-horizon] - 1.0
    return out


def non_overlapping(pos: np.ndarray, horizon: int) -> np.ndarray:
    """Boolean mask over time-sorted positions: greedy keep, next kept >= last kept + horizon."""
    keep = np.zeros(len(pos), dtype=bool)
    free_from = -np.inf
    for i, p in enumerate(pos):
        if p >= free_from:
            keep[i] = True
            free_from = p + horizon
    return keep


def events(state: pd.Series, close: pd.Series, sides: dict, horizon: int) -> pd.DataFrame:
    """Kept events with complete windows: pos, direction, fwd return, signed return."""
    assert state.index.equals(close.index)
    ev = entries(state, sides)
    fwd = forward_returns(close, horizon)
    ev["fwd"] = fwd[ev.pos.to_numpy()] if len(ev) else []
    ev = ev[ev.fwd.notna()].reset_index(drop=True)
    ev = ev[non_overlapping(ev.pos.to_numpy(), horizon)].reset_index(drop=True)
    ev["signed"] = ev.direction * ev.fwd
    return ev


def cell(ev: pd.DataFrame, fwd_all: np.ndarray) -> dict:
    """Conditional vs side-weighted unconditional stats for one hypothesis x symbol x horizon."""
    base = fwd_all[~np.isnan(fwd_all)]
    n = len(ev)
    out = {"n_events": n, "n_long_side": int((ev.direction == -1).sum()) if n else 0}
    weights = {d: float((ev.direction == d).mean()) if n else 0.0 for d in (-1, +1)}
    out.update({
        "base_n": int(len(base)),
        "base_mean": sum(w * d * base.mean() for d, w in weights.items()),
        "base_median": sum(w * d * np.median(base) for d, w in weights.items()),
        "base_hit_rate": sum(w * float((d * base > 0).mean()) for d, w in weights.items()),
        "base_std": float(base.std(ddof=1)),
    })
    if n == 0:
        out.update({k: np.nan for k in ("mean", "median", "hit_rate", "std", "t_stat", "excess_mean", "excess_median")})
        out["beats_cost_band"] = False
        return out
    s = ev.signed
    std = float(s.std(ddof=1)) if n > 1 else np.nan
    out.update({
        "mean": float(s.mean()), "median": float(s.median()), "hit_rate": float((s > 0).mean()),
        "std": std, "t_stat": float(s.mean() / (std / np.sqrt(n))) if n > 1 and std > 0 else np.nan,
    })
    out["excess_mean"] = out["mean"] - out["base_mean"]
    out["excess_median"] = out["median"] - out["base_median"]
    # §9: conditional mean in the predicted direction AND beats baseline by more than the band.
    out["beats_cost_band"] = bool(out["mean"] > 0 and out["excess_mean"] > COST_BAND)
    return out


def study(state: pd.Series, close: pd.Series) -> list[dict]:
    rows = []
    for hyp, spec in HYPOTHESES.items():
        raw = entries(state, spec["sides"])
        for label, h in spec["horizons"].items():
            ev = events(state, close, spec["sides"], h)
            rows.append({"hypothesis": hyp, "horizon": label, "horizon_bars": h,
                         "n_entries_raw": int(len(raw)),
                         **cell(ev, forward_returns(close, h))})
    return rows


def verdict(table: pd.DataFrame, symbols=SYMBOLS) -> dict:
    """Edge iff, at >=1 horizon, the primary cell beats the band on every symbol."""
    out = {}
    primary = table[table.variant == "primary"]
    for hyp, g in primary.groupby("hypothesis", sort=False):
        passing = g[g.beats_cost_band].groupby("horizon").symbol.nunique()
        horizons = sorted(passing[passing == len(symbols)].index)
        per_symbol = {sym: sorted(g[(g.symbol == sym) & g.beats_cost_band].horizon) for sym in symbols}
        out[hyp] = {"edge": bool(horizons), "horizons_passing_all_symbols": horizons,
                    "horizons_passing_per_symbol": per_symbol}
    return out


def load(symbol: str, manifest: dict) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    frame = ls.read_frame(symbol)
    states = pd.read_csv(STATES / f"{symbol}.csv.gz", index_col=0, parse_dates=True, usecols=["timestamp", "state"])
    close = frame.close.loc[states.index]  # labelled (Train-1) rows only: windows never pass data end
    return frame, close, states


def run(symbols=SYMBOLS) -> pd.DataFrame:
    manifest = ls.load_manifest()
    rows = []
    for symbol in symbols:
        frame, close, states = load(symbol, manifest)
        variants = [("primary", states.state)] + [
            (f"{k}={v}", ls.label(frame, manifest, **{k: v}).state.loc[states.index])
            for k, v in ls.grid_variants(manifest)]
        for name, state in variants:
            for row in study(state, close):
                rows.append({"symbol": symbol, "variant": name, **row})
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    table = run(args.symbols)
    table.to_csv(OUTPUT / "cells.csv", index=False, float_format="%.6g")
    primary = table[table.variant == "primary"]
    for hyp, g in primary.groupby("hypothesis", sort=False):
        g.to_csv(OUTPUT / f"{hyp}.csv", index=False, float_format="%.6g")
    v = verdict(table, args.symbols)
    v["_meta"] = {
        "cost_band_round_trip": COST_BAND,
        "cells_primary": int(len(primary)),
        "cells_total_incl_robustness": int(len(table)),
        "variants": sorted(table.variant.unique().tolist()),
    }
    (OUTPUT / "verdict.json").write_text(json.dumps(v, indent=2) + "\n")
    print(json.dumps(v, indent=2))


if __name__ == "__main__":
    main()
