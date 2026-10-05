"""
F011 T1: Causality test for forced-flow features.

Proves that features at bar i use only data at or before bar i by verifying
that truncating the input leaves features at bar i unchanged.
"""

import pandas as pd
import numpy as np
import pytest

from forced_flow_lab.build_frame import (
    load_ohlcv, load_oi, load_funding,
    align_and_forward_fill_funding,
    compute_atr, compute_realized_vol, compute_zscore,
    OI_ZSCORE_WINDOW, FUNDING_ZSCORE_WINDOW, REALIZED_VOL_WINDOW, ATR_WINDOW
)


def build_frame_up_to_bar(symbol: str, bar_index: int) -> pd.DataFrame:
    """Build features using only data up to bar_index (inclusive)."""
    # Load full data
    ohlcv = load_ohlcv(symbol)
    oi = load_oi(symbol)
    funding = load_funding(symbol)
    
    # Truncate to bar_index
    ohlcv_truncated = ohlcv.iloc[:bar_index + 1].copy()
    oi_truncated = oi.iloc[:bar_index + 1].copy()
    
    # Funding is 8-hourly, so we need to truncate it properly
    funding_truncated = funding[funding.index <= ohlcv_truncated.index[-1]].copy()
    
    # Align on hourly grid
    hourly_index = ohlcv_truncated.index
    oi_aligned = oi_truncated.reindex(hourly_index)
    funding_aligned, _ = align_and_forward_fill_funding(funding_truncated, hourly_index)
    
    # Initialize frame
    frame = pd.DataFrame(index=hourly_index)
    
    # Price features
    frame['close'] = ohlcv_truncated['close']
    frame['return'] = ohlcv_truncated['close'].pct_change()
    frame['atr'] = compute_atr(ohlcv_truncated['high'], ohlcv_truncated['low'], ohlcv_truncated['close'], ATR_WINDOW)
    frame['realized_vol'] = compute_realized_vol(frame['return'], REALIZED_VOL_WINDOW)
    
    # OI features
    frame['oi'] = oi_aligned['open_interest']
    frame['oi_delta'] = oi_aligned['open_interest'].diff()
    frame['oi_zscore'] = compute_zscore(oi_aligned['open_interest'], OI_ZSCORE_WINDOW)
    frame['oi_acceleration'] = frame['oi_delta'].diff()
    
    # Funding features
    frame['funding_rate'] = funding_aligned
    frame['funding_zscore'] = compute_zscore(funding_aligned, FUNDING_ZSCORE_WINDOW)
    
    # Derived features
    frame['fuel'] = frame['oi_delta'].abs() / frame['atr']
    price_delta = (ohlcv_truncated['close'] - ohlcv_truncated['close'].shift(1)).abs()
    frame['price_impact'] = price_delta / ohlcv_truncated['volume']
    
    frame.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    return frame


def test_causality_btcusdt():
    """Test that BTCUSDT features at bar i don't change when truncating after bar i."""
    symbol = "BTCUSDT"
    
    # Load full frame
    full_frame = pd.read_csv(f"output/f011_forced_flow/frame/{symbol}.csv", index_col=0, parse_dates=True)
    
    # Test at multiple points: after warm-up, middle, and near end
    warmup = max(OI_ZSCORE_WINDOW, FUNDING_ZSCORE_WINDOW, REALIZED_VOL_WINDOW, ATR_WINDOW)
    test_bars = [
        warmup + 10,      # Just after warm-up
        len(full_frame) // 2,  # Middle
        len(full_frame) - 100,  # Near end
    ]
    
    for bar_idx in test_bars:
        # Build frame using only data up to bar_idx
        truncated_frame = build_frame_up_to_bar(symbol, bar_idx)
        
        # Get features at bar_idx from both frames
        full_features = full_frame.iloc[bar_idx]
        truncated_features = truncated_frame.iloc[bar_idx]
        
        # Compare key features (skip NaN comparisons)
        for feature in ['return', 'atr', 'oi_delta', 'oi_zscore', 'funding_zscore', 'fuel']:
            full_val = full_features[feature]
            trunc_val = truncated_features[feature]
            
            # Both NaN is OK (for features in warm-up period)
            if pd.isna(full_val) and pd.isna(trunc_val):
                continue
            
            # Otherwise, values should match closely
            if pd.notna(full_val) and pd.notna(trunc_val):
                # Use relative tolerance for numerical stability
                assert np.isclose(full_val, trunc_val, rtol=1e-9, atol=1e-12), \
                    f"Bar {bar_idx}, feature {feature}: full={full_val}, truncated={trunc_val}"


def test_causality_ethusdt():
    """Test that ETHUSDT features at bar i don't change when truncating after bar i."""
    symbol = "ETHUSDT"
    
    # Load full frame
    full_frame = pd.read_csv(f"output/f011_forced_flow/frame/{symbol}.csv", index_col=0, parse_dates=True)
    
    # Test at multiple points
    warmup = max(OI_ZSCORE_WINDOW, FUNDING_ZSCORE_WINDOW, REALIZED_VOL_WINDOW, ATR_WINDOW)
    test_bars = [
        warmup + 10,
        len(full_frame) // 2,
        len(full_frame) - 100,
    ]
    
    for bar_idx in test_bars:
        truncated_frame = build_frame_up_to_bar(symbol, bar_idx)
        
        full_features = full_frame.iloc[bar_idx]
        truncated_features = truncated_frame.iloc[bar_idx]
        
        for feature in ['return', 'atr', 'oi_delta', 'oi_zscore', 'funding_zscore', 'fuel']:
            full_val = full_features[feature]
            trunc_val = truncated_features[feature]
            
            if pd.isna(full_val) and pd.isna(trunc_val):
                continue
            
            if pd.notna(full_val) and pd.notna(trunc_val):
                assert np.isclose(full_val, trunc_val, rtol=1e-9, atol=1e-12), \
                    f"Bar {bar_idx}, feature {feature}: full={full_val}, truncated={trunc_val}"


def test_no_nans_after_warmup():
    """Verify no NaN values exist after warm-up period."""
    warmup = max(OI_ZSCORE_WINDOW, FUNDING_ZSCORE_WINDOW, REALIZED_VOL_WINDOW, ATR_WINDOW)
    
    for symbol in ["BTCUSDT", "ETHUSDT"]:
        df = pd.read_csv(f"output/f011_forced_flow/frame/{symbol}.csv", index_col=0, parse_dates=True)
        usable = df.iloc[warmup:]
        
        nan_counts = usable.isna().sum()
        assert not nan_counts.any(), \
            f"{symbol} has NaNs past warmup: {nan_counts[nan_counts > 0].to_dict()}"


def test_funding_forward_fill_flag():
    """Verify funding_filled flag correctly marks forward-filled values."""
    for symbol in ["BTCUSDT", "ETHUSDT"]:
        df = pd.read_csv(f"output/f011_forced_flow/frame/{symbol}.csv", index_col=0, parse_dates=True)
        
        # Load original funding to know which timestamps are real
        funding = load_funding(symbol)
        original_funding_times = set(funding.index)
        
        # Check that funding_filled is True for hours not in original funding
        for idx in df.index:
            expected_filled = idx not in original_funding_times
            actual_filled = df.loc[idx, 'funding_filled']
            assert actual_filled == expected_filled, \
                f"{symbol} at {idx}: expected funding_filled={expected_filled}, got {actual_filled}"


if __name__ == "__main__":
    # Run tests
    print("Testing causality for BTCUSDT...")
    test_causality_btcusdt()
    print("✓ BTCUSDT causality test passed")
    
    print("\nTesting causality for ETHUSDT...")
    test_causality_ethusdt()
    print("✓ ETHUSDT causality test passed")
    
    print("\nTesting no NaNs after warmup...")
    test_no_nans_after_warmup()
    print("✓ No NaNs after warmup")
    
    print("\nTesting funding forward-fill flag...")
    test_funding_forward_fill_flag()
    print("✓ Funding forward-fill flag correct")
    
    print("\n✓ All causality tests passed!")
