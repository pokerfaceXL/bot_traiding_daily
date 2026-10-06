"""F011 T2: causal forced-flow state labels on the 5m frame (non-trading).

Every threshold and lookback is read from the frozen states manifest; nothing is
fitted. Bybit is the only venue inside a rule; bn_ OI is emitted as a separate
cross-check column. No forward returns, PnL, or trades.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

FRAME = Path("output/f011_forced_flow/frame_5m")
OUTPUT = Path("output/f011_forced_flow/states")
MANIFEST = OUTPUT / "manifest.json"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
STATES = ("NORMAL", "LONG_CROWDING", "SHORT_CROWDING", "LONG_STRESS", "SHORT_STRESS",
          "LONG_LIQUIDATION_CASCADE", "SHORT_LIQUIDATION_CASCADE", "LONG_EXHAUSTION", "SHORT_EXHAUSTION")
STRESS_FAMILY = ("LONG_STRESS", "SHORT_STRESS", "LONG_LIQUIDATION_CASCADE", "SHORT_LIQUIDATION_CASCADE")


def load_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text())


def compute_states(frame: pd.DataFrame, thresholds: dict, lookbacks: dict) -> pd.DataFrame:
    """State + triggering values for every row; row t depends on rows <= t only."""
    t, lb = thresholds, lookbacks
    fz, oz = frame.funding_zscore, frame.oi_zscore
    fps_long, fps_short = oz + fz, oz - fz
    crowded_long = (fps_long >= t["fps_threshold"]) & (fz > 0)
    crowded_short = (fps_short >= t["fps_threshold"]) & (fz < 0)
    side_bar = pd.Series(np.where(crowded_long, 1.0, np.where(crowded_short, -1.0, np.nan)), index=frame.index)
    crowd_side = side_bar.ffill(limit=lb["crowd_memory"] - 1).fillna(0.0)

    w = lb["stress_window"]
    anr = frame.atr_normalized_return
    anr_w = anr.rolling(w, min_periods=w).sum()
    doi_w = frame.open_interest - frame.open_interest.shift(w)
    ofi_w = frame.ofi.rolling(w, min_periods=w).mean()
    long_stress = (crowd_side == 1) & (anr_w <= -t["stress_return_atr"]) & (doi_w < 0) & (ofi_w <= -t["ofi_threshold"])
    short_stress = (crowd_side == -1) & (anr_w >= t["stress_return_atr"]) & (doi_w < 0) & (ofi_w >= t["ofi_threshold"])

    n = lb["fuel_rank_window"]
    fuel_pct = frame.fuel.rolling(n, min_periods=n).rank(method="max", pct=True)
    fuel_high = (fuel_pct >= t["fuel_percentile"]) & (frame.delta_oi < 0)
    anr_prev = anr.shift(1)
    long_cascade = long_stress & fuel_high & (anr < 0) & (anr < anr_prev)
    short_cascade = short_stress & fuel_high & (anr > 0) & (anr > anr_prev)
    cascade = long_cascade | short_cascade

    e, r = lb["exhaustion_after_cascade"], lb["impact_reference_window"]
    recent_long = long_cascade.astype(float).shift(1).rolling(e, min_periods=1).max().fillna(0) > 0
    recent_short = short_cascade.astype(float).shift(1).rolling(e, min_periods=1).max().fillna(0) > 0
    sell_ratio = frame.sell_impact / frame.sell_impact.shift(1).rolling(r, min_periods=1).max()
    buy_ratio = frame.buy_impact / frame.buy_impact.shift(1).rolling(r, min_periods=1).max()
    decel = frame.oi_acceleration > 0
    long_exh = ~cascade & recent_long & decel & (sell_ratio <= t["exhaustion_impact_ratio"]) & (frame.ofi < 0)
    short_exh = ~cascade & recent_short & decel & (buy_ratio <= t["exhaustion_impact_ratio"]) & (frame.ofi > 0)

    # Lowest precedence first so later assignments win (manifest "precedence").
    state = pd.Series("NORMAL", index=frame.index, dtype=object)
    for mask, name in ((crowded_short, "SHORT_CROWDING"), (crowded_long, "LONG_CROWDING"),
                       (short_stress, "SHORT_STRESS"), (long_stress, "LONG_STRESS"),
                       (short_exh, "SHORT_EXHAUSTION"), (long_exh, "LONG_EXHAUSTION"),
                       (short_cascade, "SHORT_LIQUIDATION_CASCADE"), (long_cascade, "LONG_LIQUIDATION_CASCADE")):
        state[mask.to_numpy()] = name

    impact_ratio = np.where(recent_long, sell_ratio, np.where(recent_short, buy_ratio, np.nan))
    lsr = frame.long_short_ratio
    lsr_z = (lsr - lsr.rolling(n, min_periods=n).mean()) / lsr.rolling(n, min_periods=n).std(ddof=1)
    lsr_confirms = np.where(crowd_side == 1, lsr_z > 0, np.where(crowd_side == -1, lsr_z < 0, False))
    bn = frame["bn_sum_open_interest"] if "bn_sum_open_interest" in frame else pd.Series(np.nan, index=frame.index)
    return pd.DataFrame({
        "state": state,
        "crowd_side": crowd_side.astype(int),
        "fps_long": fps_long, "fps_short": fps_short,
        "anr": anr, "anr_w": anr_w, "doi_w": doi_w, "ofi_w": ofi_w,
        "fuel_pct": fuel_pct, "oi_acceleration": frame.oi_acceleration,
        "impact_ratio": impact_ratio, "lsr_confirms": lsr_confirms,
        "bn_doi_w": bn - bn.shift(w),
    }, index=frame.index)


def label(frame: pd.DataFrame, manifest: dict, **override) -> pd.DataFrame:
    """Labels for non-warmup rows only; warm-up rows are causal history."""
    thresholds = {**manifest["thresholds"], **override}
    states = compute_states(frame, thresholds, manifest["lookbacks_bars"])
    return states.loc[~frame.is_warmup.astype(bool).to_numpy()]


def durations(state: pd.Series) -> dict:
    runs = (state != state.shift()).cumsum()
    lengths = state.groupby(runs).agg(["first", "size"])
    return {name: {"runs": int(len(g)), "median_bars": float(g["size"].median()),
                   "median_minutes": float(g["size"].median() * 5), "max_bars": int(g["size"].max())}
            for name, g in lengths.groupby("first")}


def summarize(states: pd.DataFrame) -> dict:
    counts = states.state.value_counts()
    stress = states.state.isin(STRESS_FAMILY)
    bn_known = stress & states.bn_doi_w.notna()
    return {
        "labelled_bars": int(len(states)),
        "counts": {name: int(counts.get(name, 0)) for name in STATES},
        "durations": durations(states.state),
        "bn_cross_check": {
            "stress_or_cascade_bars": int(stress.sum()),
            "with_bn_oi": int(bn_known.sum()),
            "bn_oi_also_falling_fraction": float((states.bn_doi_w[bn_known] < 0).mean()) if bn_known.any() else None,
        },
        "lsr_confirms_fraction_on_crowding": float(states.lsr_confirms[states.state.str.endswith("CROWDING")].mean())
        if states.state.str.endswith("CROWDING").any() else None,
    }


def grid_variants(manifest: dict):
    primary = manifest["thresholds"]
    for key, values in manifest["robustness_grid"].items():
        if key == "design":
            continue
        for value in values:
            if value != primary[key]:
                yield key, value


def read_frame(symbol: str) -> pd.DataFrame:
    with gzip.open(FRAME / f"{symbol}.csv.gz", "rt") as fh:
        return pd.read_csv(fh, index_col=0, parse_dates=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    args = parser.parse_args()
    manifest = load_manifest()
    summary = {}
    for symbol in args.symbols:
        frame = read_frame(symbol)
        states = label(frame, manifest)
        assert states.state.isin(STATES).all() and len(states) == int((~frame.is_warmup).sum())
        states.to_csv(OUTPUT / f"{symbol}.csv.gz", float_format="%.6g", compression={"method": "gzip", "mtime": 0})
        summary[symbol] = summarize(states)
        summary[symbol]["robustness"] = {
            f"{key}={value}": {name: int(n) for name, n in label(frame, manifest, **{key: value}).state.value_counts().items()}
            for key, value in grid_variants(manifest)}
        print(symbol, json.dumps(summary[symbol]["counts"]))
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
