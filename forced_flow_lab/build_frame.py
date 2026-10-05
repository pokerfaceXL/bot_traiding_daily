"""
F011 T1: Build the causal per-hour feature frame for forced-flow lab.
Loads OHLCV (60min) + OI (1h) + funding (8h), aligns on hourly grid,
computes participant-state features per spec/research/F011-forced-flow-lab.md §3,§7.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from data_contract import load_dataset

# Train-1 span per F005
TRAIN1_START = "2024-01-26T00:00:00Z"
TRAIN1_END = "2025-03-01T00:00:00Z"

# Rolling window parameters (frozen choice, not tunable)
OI_ZSCORE_WINDOW = 168  # 7 days hourly
FUNDING_ZSCORE_WINDOW = 168  # 7 days hourly
REALIZED_VOL_WINDOW = 24  # 1 day hourly
ATR_WINDOW = 14  # 14 bars

SYMBOLS = ["BTCUSDT", "ETHUSDT"]


@dataclass
class FrameManifest:
    symbol: str
    window_start: str
    window_end: str
    row_count: int
    oi_zscore_window: int
    funding_zscore_window: int
    realized_vol_window: int
    atr_window: int
    funding_fills: int
    ohlcv_checksum: str
    oi_checksum: str
    funding_checksum: str
    frame_checksum: str
    generated_at: str

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "row_count": self.row_count,
            "rolling_windows": {
                "oi_zscore": self.oi_zscore_window,
                "funding_zscore": self.funding_zscore_window,
                "realized_vol": self.realized_vol_window,
                "atr": self.atr_window,
            },
            "funding_fills": self.funding_fills,
            "checksums": {
                "ohlcv": self.ohlcv_checksum,
                "oi": self.oi_checksum,
                "funding": self.funding_checksum,
                "frame": self.frame_checksum,
            },
            "generated_at": self.generated_at,
        }


def _checksum(df: pd.DataFrame) -> str:
    """SHA256 checksum of DataFrame as CSV."""
    payload = df.to_csv(index=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_ohlcv(symbol: str) -> pd.DataFrame:
    """Load hourly OHLCV from data_contract cache."""
    df, _ = load_dataset("data_cache", symbol, "60", TRAIN1_START, TRAIN1_END)
    # Ensure we have the full dataset including warmup
    df_full, _ = load_dataset("data_cache", symbol, "60", TRAIN1_START, TRAIN1_END)
    # Load the raw CSV to get all data including warmup
    csv_path = f"data_cache/{symbol}_60_20240126T000000Z_20250301T000000Z.csv"
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True)
    return df


def load_oi(symbol: str) -> pd.DataFrame:
    """Load hourly open interest."""
    path = f"data_cache/open_interest/{symbol}_oi_1h_20240126T000000Z_20250301T000000Z.csv"
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True)
    return df


def load_funding(symbol: str) -> pd.DataFrame:
    """Load funding (8-hour settlements)."""
    path = f"data_cache/funding/{symbol}_funding_20240126T000000Z_20250301T000000Z.csv"
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True)
    return df


def align_and_forward_fill_funding(funding_df: pd.DataFrame, hourly_index: pd.DatetimeIndex) -> tuple[pd.Series, int]:
    """Forward-fill funding to hourly grid. Funding applies to the next 8h period.
    
    Returns:
        (funding_series, fill_count): hourly funding series and count of filled values
    """
    # Funding is settled every 8h (00:00, 08:00, 16:00) and applies to the NEXT period
    # So we forward-fill to cover the hours where that rate applies
    aligned = funding_df.reindex(hourly_index, method='ffill')
    fill_count = aligned['funding_rate'].isna().sum()  # Count NaNs before filling any initial gap
    
    # For initial NaNs (before first funding timestamp), backfill from first value
    if aligned['funding_rate'].isna().any():
        first_valid_idx = aligned['funding_rate'].first_valid_index()
        if first_valid_idx is not None:
            first_val = aligned.loc[first_valid_idx, 'funding_rate']
            aligned['funding_rate'].fillna(first_val, inplace=True)
    
    # Count how many were filled (approximation: original funding is 1/3 of hourly)
    original_count = len(funding_df)
    hourly_count = len(hourly_index)
    fill_count = hourly_count - original_count
    
    return aligned['funding_rate'], fill_count


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int) -> pd.Series:
    """Compute Average True Range."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()


def compute_realized_vol(returns: pd.Series, window: int) -> pd.Series:
    """Compute realized volatility (std of returns)."""
    return returns.rolling(window=window).std()


def compute_zscore(series: pd.Series, window: int) -> pd.Series:
    """Compute rolling z-score. Returns 0 when std is 0 (no variation)."""
    mean = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    zscore = (series - mean) / std
    # When std is 0, the value equals the mean, so z-score is 0 (no deviation)
    zscore = zscore.fillna(0)
    return zscore


def build_frame(symbol: str) -> tuple[pd.DataFrame, FrameManifest]:
    """Build the complete feature frame for one symbol."""
    print(f"Building frame for {symbol}...")
    
    # Load data
    ohlcv = load_ohlcv(symbol)
    oi = load_oi(symbol)
    funding = load_funding(symbol)
    
    # Store checksums
    ohlcv_checksum = _checksum(ohlcv)
    oi_checksum = _checksum(oi)
    funding_checksum = _checksum(funding)
    
    # Align on hourly grid (use OHLCV index as master)
    hourly_index = ohlcv.index
    
    # Align OI (should already be hourly-aligned)
    oi_aligned = oi.reindex(hourly_index)
    
    # Forward-fill funding to hourly
    funding_aligned, funding_fills = align_and_forward_fill_funding(funding, hourly_index)
    
    # Initialize frame
    frame = pd.DataFrame(index=hourly_index)
    
    # Add flag for funding fills
    frame['funding_filled'] = False
    # Mark hours that were filled (not in original funding data)
    original_funding_times = set(funding.index)
    for ts in hourly_index:
        if ts not in original_funding_times:
            frame.loc[ts, 'funding_filled'] = True
    
    # Price features
    frame['close'] = ohlcv['close']
    frame['open'] = ohlcv['open']
    frame['high'] = ohlcv['high']
    frame['low'] = ohlcv['low']
    frame['volume'] = ohlcv['volume']
    
    # Return (causal: use close-to-close)
    frame['return'] = ohlcv['close'].pct_change()
    
    # ATR
    frame['atr'] = compute_atr(ohlcv['high'], ohlcv['low'], ohlcv['close'], ATR_WINDOW)
    
    # Realized volatility
    frame['realized_vol'] = compute_realized_vol(frame['return'], REALIZED_VOL_WINDOW)
    
    # OI features
    frame['oi'] = oi_aligned['open_interest']
    frame['oi_delta'] = oi_aligned['open_interest'].diff()
    frame['oi_zscore'] = compute_zscore(oi_aligned['open_interest'], OI_ZSCORE_WINDOW)
    # OI acceleration (second derivative)
    frame['oi_acceleration'] = frame['oi_delta'].diff()
    
    # Funding features
    frame['funding_rate'] = funding_aligned
    frame['funding_zscore'] = compute_zscore(funding_aligned, FUNDING_ZSCORE_WINDOW)
    
    # Derived features
    # Fuel = |ΔOI| / ATR
    frame['fuel'] = frame['oi_delta'].abs() / frame['atr']
    
    # Price impact = |Δprice| / volume
    price_delta = (ohlcv['close'] - ohlcv['close'].shift(1)).abs()
    frame['price_impact'] = price_delta / frame['volume']
    
    # Replace inf with NaN (division by zero cases)
    frame.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    # Reorder columns for clarity
    cols = [
        'close', 'open', 'high', 'low', 'volume', 'return',
        'atr', 'realized_vol',
        'oi', 'oi_delta', 'oi_zscore', 'oi_acceleration',
        'funding_rate', 'funding_zscore', 'funding_filled',
        'fuel', 'price_impact',
    ]
    frame = frame[cols]
    
    # Build manifest
    manifest = FrameManifest(
        symbol=symbol,
        window_start=TRAIN1_START,
        window_end=TRAIN1_END,
        row_count=len(frame),
        oi_zscore_window=OI_ZSCORE_WINDOW,
        funding_zscore_window=FUNDING_ZSCORE_WINDOW,
        realized_vol_window=REALIZED_VOL_WINDOW,
        atr_window=ATR_WINDOW,
        funding_fills=funding_fills,
        ohlcv_checksum=ohlcv_checksum,
        oi_checksum=oi_checksum,
        funding_checksum=funding_checksum,
        frame_checksum=_checksum(frame),
        generated_at=datetime.utcnow().isoformat() + "Z",
    )
    
    print(f"  {len(frame)} bars, {funding_fills} funding fills, "
          f"warmup ~{max(OI_ZSCORE_WINDOW, FUNDING_ZSCORE_WINDOW, REALIZED_VOL_WINDOW, ATR_WINDOW)} bars")
    
    return frame, manifest


def main():
    """Build frames for all symbols and save with manifests."""
    os.makedirs("output/f011_forced_flow/frame", exist_ok=True)
    
    manifests = {}
    
    for symbol in SYMBOLS:
        frame, manifest = build_frame(symbol)
        
        # Save frame
        frame_path = f"output/f011_forced_flow/frame/{symbol}.csv"
        frame.to_csv(frame_path, index=True)
        print(f"  Wrote {frame_path}")
        
        # Save manifest
        manifest_path = f"output/f011_forced_flow/frame/{symbol}.manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2, sort_keys=True)
        print(f"  Wrote {manifest_path}")
        
        manifests[symbol] = manifest.to_dict()
    
    # Save combined manifest
    combined_manifest_path = "output/f011_forced_flow/frame/manifest.json"
    combined_manifest = {
        "symbols": SYMBOLS,
        "train1_window": {
            "start": TRAIN1_START,
            "end": TRAIN1_END,
        },
        "rolling_windows": {
            "oi_zscore": OI_ZSCORE_WINDOW,
            "funding_zscore": FUNDING_ZSCORE_WINDOW,
            "realized_vol": REALIZED_VOL_WINDOW,
            "atr": ATR_WINDOW,
        },
        "per_symbol": manifests,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    with open(combined_manifest_path, 'w') as f:
        json.dump(combined_manifest, f, indent=2, sort_keys=True)
    print(f"\nWrote {combined_manifest_path}")
    print("\nFrame build complete.")


if __name__ == "__main__":
    main()
