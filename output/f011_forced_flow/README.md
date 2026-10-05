# F011 T1: Forced-Flow Event Frame (Non-Trading)

Implementation of the causal per-hour feature frame for forced-flow participant modeling.

## Output

### Feature Frames
- `frame/BTCUSDT.csv` - 9600 hourly bars (2024-01-26 to 2025-03-01)
- `frame/ETHUSDT.csv` - 9600 hourly bars (2024-01-26 to 2025-03-01)

### Manifests
- `frame/manifest.json` - Combined manifest with rolling window parameters
- `frame/{SYMBOL}.manifest.json` - Per-symbol manifests with checksums

## Features (per spec §3)

All features use only data at or before the current bar (causal):

### Price Features
- **return**: Close-to-close percentage return
- **atr**: Average True Range (14-bar rolling)
- **realized_vol**: Realized volatility from returns (24-bar rolling std)
- **volume**: Trading volume

### Open Interest Features
- **oi**: Raw open interest value
- **oi_delta**: Change in OI (first derivative)
- **oi_zscore**: Normalized OI (168-bar rolling z-score)
- **oi_acceleration**: Change in ΔOI (second derivative)

### Funding Features
- **funding_rate**: Funding rate (8-hour settlements, forward-filled to hourly)
- **funding_zscore**: Normalized funding (168-bar rolling z-score)
- **funding_filled**: Boolean flag marking forward-filled hours

### Derived Features
- **fuel**: `|ΔOI| / ATR` - Normalized OI change intensity
- **price_impact**: `|Δprice| / volume` - Price movement per unit volume

## Rolling Window Parameters (Frozen)

- **OI z-score**: 168 hours (7 days)
- **Funding z-score**: 168 hours (7 days)
- **Realized vol**: 24 hours (1 day)
- **ATR**: 14 bars

## Data Quality

- **Warm-up period**: 168 bars (longest rolling window)
- **NaN handling**: No NaNs after warm-up; initial NaNs from rolling windows
- **Funding fills**: 8400 per symbol (from 8-hour to hourly grid)
- **Checksums**: All input data validated against manifests

## Causality Guarantee

Verified via `forced_flow_lab/test_causality.py`:
- Truncating input at bar i leaves features at bar i unchanged
- No look-ahead bias in any feature calculation
- All features computable in real-time with only past data

## Usage

Build frames:
```bash
python3 forced_flow_lab/build_frame.py
```

Run causality tests:
```bash
python3 -m pytest forced_flow_lab/test_causality.py -v
```

## Next Steps (Out of Scope for T1)

- T2: State labeling (NORMAL, LONG_CROWDING, CASCADE, EXHAUSTION, etc.)
- T3: Event study on pre-registered hypotheses H-FORCEDFLOW-CONTINUATION-01 and H-FORCEDFLOW-EXHAUSTION-01

See `spec/research/F011-forced-flow-lab.md` for full specification.
