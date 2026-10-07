"""F014 frozen splits, protocol constants and the 28-hypothesis registry.

This module is the machine-readable freeze. It is committed (and its JSON export hashed) before
any scoring code exists. Do not add, remove or edit hypotheses after scoring has started; the
runner refuses to score if the exported registry hash differs from
output/f014_discovery/hypothesis_registry.json.
"""
from __future__ import annotations

import hashlib
import json

# ---------------------------------------------------------------- splits (UTC, [start, end))
SPLITS = {
    "warmup": ["2024-01-26T00:00:00+00:00", "2024-03-01T00:00:00+00:00"],
    "discovery": ["2024-03-01T00:00:00+00:00", "2025-03-01T00:00:00+00:00"],
    "validation": ["2025-03-01T00:00:00+00:00", "2026-03-01T00:00:00+00:00"],
    "final_holdout": ["2026-03-01T00:00:00+00:00", "2026-09-01T00:00:00+00:00"],
}
SCORED_SPLIT = "discovery"
FROZEN_SPLITS = ["validation", "final_holdout"]
BLOCKS = {
    "Q1": ["2024-03-01T00:00:00+00:00", "2024-06-01T00:00:00+00:00"],
    "Q2": ["2024-06-01T00:00:00+00:00", "2024-09-01T00:00:00+00:00"],
    "Q3": ["2024-09-01T00:00:00+00:00", "2024-12-01T00:00:00+00:00"],
    "Q4": ["2024-12-01T00:00:00+00:00", "2025-03-01T00:00:00+00:00"],
}

# ---------------------------------------------------------------- protocol constants
PROTOCOL = {
    "bar": "1h (Bybit linear OHLCV, timestamp = bar open, UTC)",
    "decision": "at close of bar t (= timestamp_t + 1h); all state inputs known by then",
    "forward_return": "y_h = 1e4 * ln(close_{t+h} / close_t) in bp; NaN if t+h outside the loaded Train-1 file",
    "horizons_reported": [1, 2, 4, 12],
    "lookback_bars": 720,  # 30 d rolling window for regime quantiles
    "quantile_rule": "threshold_t = rolling(720, min_periods=720) quantile of the state variable over bars "
                     "t-720..t-1 (shift 1, causal); 'top 20%' = value > q80 strictly; 'bottom 20%' = value < q20 "
                     "strictly; 'top 5%' = value > q95 strictly",
    "vol_window_bars": 24,
    "breakout_window_bars": 20,  # prior 20 bars, excluding bar t
    "aux_alignment": "funding / OI / account-ratio rows are attached to bar t only if their timestamp <= "
                     "bar-open timestamp_t (>= 1h before the decision; conservative, no same-bar peek)",
    "primary_test": "OLS y = a + b*S over the hypothesis population (S = state indicator); b = mean(y|S) - "
                    "mean(y|population & not S); two-sided p from Newey-West HAC SE (Bartlett, 24 lags), "
                    "normal approximation",
    "hac_lags": 24,
    "ic": "Spearman rank correlation of the hypothesis' continuous score with y over the population "
          "(diagnostic; criterion 1 accepts b sign OR IC sign)",
    "min_state_n_full": 30,   # fewer state bars in discovery for an asset -> test INSUFFICIENT, p = 1
    "min_state_n_block": 10,  # fewer state bars in a block -> that block is not sign-OK
    "fdr": {
        "method": "Benjamini-Hochberg",
        "family": "one primary test per (hypothesis, required asset) at the primary horizon; required "
                  "assets = 2 (see each hypothesis' replication pair) -> m = 28 x 2 = 56; SKIPPED or "
                  "INSUFFICIENT tests stay in the family with p = 1",
        "m": 56,
        "q_max": 0.10,
        "secondary": "all non-primary horizons and the optional third asset are reported, NOT in the family",
    },
    "cost_bp_rt": {"primary_owner_tier": 9.9, "stress_historical": 34.0},
    "cost_rule": "one RT per hypothetical state-bar trade (overlapping state bars each pay a full RT); "
                 "pair expressions (residual) pay RT x (1 + |beta_t|) averaged over state bars",
    "tradable_gross": "gross_bp = mean over state bars of d * y (d = predicted direction of the expression)",
    "success": [
        "C1 sign: b sign == d OR IC sign == d, on BOTH required assets",
        "C2 FDR: BH q <= 0.10 on BOTH required-asset primary tests (family m = 56)",
        "C3 stability: block b sign == d in >= 3 of 4 quarterly blocks, on BOTH required assets",
        "C4 replication: both required assets have b sign == d (third asset optional, bonus only)",
        "C5 economics: tradable expression with gross_bp - 9.9 * cost_mult > 0 on BOTH required assets "
        "(net @34 reported as stress); non-tradable hypotheses fail C5 by construction",
    ],
    "robustness_score": "mean_asset(n_blocks_ok)/4 + 1{C4} + 1{C2} + clip(min_asset((gross - 9.9*cm)/(9.9*cm)), 0, 1); "
                        "survivors ranked by this score, never by max return; at most 3 recommended",
    "two_sided_hyps": "for d = 0 hypotheses (time-of-day) the predicted sign is set to sign(b_BTC) on the full "
                      "discovery window; ETH and blocks must then agree",
}

REQ_DEFAULT = ["BTCUSDT", "ETHUSDT"]
BONUS_DEFAULT = "SOLUSDT"


def _h(id_, family, state, why, expected, d, horizons, target, expression, tradable=True,
       data=("ohlcv",), req=None, bonus=BONUS_DEFAULT, notes=""):
    return {
        "id": id_, "family": family, "state": state, "why": why, "expected": expected,
        "d": d, "horizons": horizons, "primary_horizon": horizons[0], "target": target,
        "expression": expression, "tradable": tradable, "data": list(data),
        "required_assets": req or list(REQ_DEFAULT), "bonus_asset": bonus, "notes": notes,
    }


FWD = "y = own forward log return (bp)"

HYPOTHESES = [
    # ------------------------------------------------ Family A: price structure (1h)
    _h("H-PS-REV-UP", "A", "r_1h(t) > 0 AND |r_1h(t)| > q80 of trailing 720 |r_1h|",
       "short-horizon overreaction to large up bars", "negative fwd return", -1, [1, 2, 4], FWD,
       "short on state bar"),
    _h("H-PS-REV-DN", "A", "r_1h(t) < 0 AND |r_1h(t)| > q80 of trailing 720 |r_1h|",
       "short-horizon overreaction to large down bars", "positive fwd return", +1, [1, 2, 4], FWD,
       "long on state bar"),
    _h("H-PS-TREND-UP", "A", "close_t > max(high_{t-20..t-1})",
       "momentum continuation after range breakout (IC/state test, not a Donchian strategy reopen)",
       "positive fwd return", +1, [1, 2, 4], FWD, "long on state bar"),
    _h("H-PS-TREND-DN", "A", "close_t < min(low_{t-20..t-1})", "momentum continuation",
       "negative fwd return", -1, [1, 2, 4], FWD, "short on state bar"),
    _h("H-PS-RANGE-LOC", "A", "loc_t = (close-low)/(high-low) of bar t > q80 of trailing 720 loc",
       "close near the high = unabsorbed buying", "positive fwd return", +1, [1, 2, 4], FWD,
       "long on state bar", notes="bars with high == low have loc undefined (NaN, excluded)"),
    _h("H-PS-RANGE-LOC-DN", "A", "loc_t < q20 of trailing 720 loc", "close near the low = unabsorbed selling",
       "negative fwd return", -1, [1, 2, 4], FWD, "short on state bar"),
    _h("H-PS-VOL-COMPRESS", "A", "sigma24_t (std of last 24 1h log returns) < q20 of trailing 720 sigma24",
       "volatility compression precedes expansion",
       "higher vol-normalised forward move", +1, [4, 1, 2, 12],
       "y = |fwd log return_h| / (sigma24_t * sqrt(h)) (unitless); |r|, MFE, MAE reported",
       "none (non-directional; a straddle is not available on linear perps)", tradable=False,
       notes="fails C5 by construction; kept for information and multiplicity"),
    _h("H-PS-GAP-CONT", "A",
       "population = 00:00 UTC bars only; g = log return of the 00:00-01:00 bar; state = |g| > q80 of |g| "
       "over the previous 30 00:00 bars (causal)",
       "day-roll repricing (UTC day open) continues", "same-sign continuation over next 4h", +1, [4, 1, 2, 12],
       "y = sign(g) * fwd log return_h", "position sign(g) at 01:00 UTC",
       notes="crypto has no session gap; the 00:00 UTC bar return is the frozen proxy"),
    # ------------------------------------------------ Family B: derivatives (Train-1)
    _h("H-DER-FUND-HI", "B", "funding_t (last settled, aligned) > q80 of trailing 720 aligned funding",
       "crowded longs pay and unwind", "negative fwd return", -1, [4, 12, 1, 2], FWD, "short on state bar",
       data=("ohlcv", "funding")),
    _h("H-DER-FUND-LO", "B", "funding_t < q20 of trailing 720 aligned funding", "crowded shorts",
       "positive fwd return", +1, [4, 12, 1, 2], FWD, "long on state bar", data=("ohlcv", "funding")),
    _h("H-DER-FUND-DELTA", "B", "dF = funding_t - funding_{t-24}; dF > 0 AND dF > q80 of trailing 720 dF",
       "crowding acceleration", "negative fwd return", -1, [4, 12, 1, 2], FWD, "short on state bar",
       data=("ohlcv", "funding")),
    _h("H-DER-OI-UP-PX-UP", "B", "dOI4 = ln(OI_t/OI_{t-4}) > q80 of trailing 720 dOI4 AND r_4h(t) > 0",
       "new leveraged longs chase -> long-squeeze risk", "negative fwd return", -1, [4, 1, 2, 12], FWD,
       "short on state bar", data=("ohlcv", "oi_1h")),
    _h("H-DER-OI-UP-PX-DN", "B", "dOI4 > q80 AND r_4h(t) < 0", "new shorts pile in -> short-squeeze risk",
       "positive fwd return", +1, [4, 1, 2, 12], FWD, "long on state bar", data=("ohlcv", "oi_1h")),
    _h("H-DER-OI-DOWN-CAPIT", "B", "dOI4 < q20 AND r_4h(t) < q20 of trailing 720 r_4h",
       "capitulation / forced deleveraging exhausts sellers", "positive bounce", +1, [1, 2, 4], FWD,
       "long on state bar", data=("ohlcv", "oi_1h")),
    _h("H-DER-OI-FLAT-MOVE", "B",
       "|dOI1| = |ln(OI_t/OI_{t-1})| < q20 of trailing 720 |dOI1| AND |r_1h(t)| > q80 of trailing 720 |r_1h|",
       "price move without positioning change = thin-book move", "mean reversion next 1-2h", -1, [1, 2],
       "y = sign(r_1h(t)) * fwd log return_h (d = -1: reversal)", "position -sign(r_1h(t))",
       data=("ohlcv", "oi_1h")),
    # ------------------------------------------------ Family C: positioning proxy (BTC/ETH only)
    _h("H-OF-BUYRATIO-HI", "C",
       "buyRatio_t (Bybit account ratio 5m, last row <= bar open) > q80 of trailing 720",
       "retail long crowding is contrarian", "negative fwd return", -1, [1, 2, 4], FWD, "short on state bar",
       data=("ohlcv", "account_ratio_5m"), bonus=None),
    _h("H-OF-BUYRATIO-LO", "C", "buyRatio_t < q20 of trailing 720", "retail short crowding is contrarian",
       "positive fwd return", +1, [1, 2, 4], FWD, "long on state bar", data=("ohlcv", "account_ratio_5m"),
       bonus=None),
    _h("H-OF-BUYRATIO-SPIKE", "C", "dBR4 = buyRatio_t - buyRatio_{t-4} > q80 of trailing 720 dBR4",
       "fast retail long build-up is contrarian", "negative fwd return", -1, [1, 2, 4], FWD,
       "short on state bar", data=("ohlcv", "account_ratio_5m"), bonus=None),
    # ------------------------------------------------ Family D: cross-market
    _h("H-XS-ETH-BTC-REV", "D",
       "e_t = r_X(t) - beta_t r_BTC(t), beta_t = OLS slope over bars t-720..t-1; e_t > q80 of trailing 720 e",
       "idiosyncratic relative moves revert (relative value)", "negative fwd residual", -1, [1, 2, 4],
       "y = r_X,fwd_h - beta_t * r_BTC,fwd_h (bp)", "short X / long beta BTC (pair)",
       req=["ETHUSDT", "SOLUSDT"], bonus=None,
       notes="required pair: X = ETH (primary), replication X = SOL; cost multiplier 1 + |beta_t|"),
    _h("H-XS-ETH-BTC-REV-DN", "D", "e_t < q20 of trailing 720 e", "relative value reversion",
       "positive fwd residual", +1, [1, 2, 4], "y = r_X,fwd_h - beta_t * r_BTC,fwd_h (bp)",
       "long X / short beta BTC (pair)", req=["ETHUSDT", "SOLUSDT"], bonus=None,
       notes="X = ETH primary, X = SOL replication; cost multiplier 1 + |beta_t|"),
    _h("H-XS-BTC-LEAD", "D", "|r_BTC(t)| > q80 of trailing 720 |r_BTC|",
       "BTC leads alt repricing", "same-sign follower return next 1h", +1, [1, 2],
       "y = sign(r_BTC(t)) * r_X,fwd_h", "position sign(r_BTC(t)) in follower X",
       req=["ETHUSDT", "SOLUSDT"], bonus=None, notes="follower X = ETH (primary) and SOL (replication)"),
    _h("H-XS-SOL-BTC-REV", "D", "|e_t| > q80 of trailing 720 |e| (residual as in H-XS-ETH-BTC-REV)",
       "symmetric residual reversion", "residual reverts", -1, [1, 2, 4],
       "y = sign(e_t) * (r_X,fwd_h - beta_t r_BTC,fwd_h)", "position -sign(e_t) in pair",
       req=["SOLUSDT", "ETHUSDT"], bonus=None,
       notes="X = SOL primary, X = ETH replication; cost multiplier 1 + |beta_t|"),
    # ------------------------------------------------ Family E: liquidity / vol regime
    _h("H-VOL-REGIME-DIR", "E",
       "population = bars with a trend state (TS = +1 if H-PS-TREND-UP, -1 if H-PS-TREND-DN); "
       "S = sigma24_t > q80 (high vol); bars with sigma24 between q20 and q80 excluded",
       "in high vol noise dominates breakouts", "trend-follow return lower in high-vol than low-vol regime",
       -1, [1, 2, 4], "y = TS_t * fwd log return_h", "trend-follow (position TS_t) only in low-vol regime",
       notes="b = mean(y|high vol) - mean(y|low vol); tradable gross = mean(y | low vol) (d applied to the "
             "regime contrast, the expression itself is long TS)"),
    _h("H-VOL-SPIKE-DRIFT", "E", "|r_1h(t)| > q95 of trailing 720 |r_1h|", "risk-off after shock",
       "negative drift next 2-4h", -1, [2, 4, 1, 12], FWD, "short on state bar"),
    _h("H-VOL-OF-VOL", "E", "vov_t = std of |r_1h| over last 24 bars > q80 of trailing 720 vov",
       "unstable volatility = risk-off", "negative mean drift 4h (and elevated |fwd r|, secondary)",
       -1, [4, 1, 2, 12], FWD, "short on state bar"),
    # ------------------------------------------------ Family F: time
    _h("H-TIME-US-OPEN", "F", "forward window starts 13:00 or 14:00 UTC (bar t open hour in {12, 13})",
       "US cash open flow", "directional edge differs from other hours (two-sided); |r| secondary",
       0, [1, 2], FWD, "position sign(b_BTC) on state bars"),
    _h("H-TIME-ASIA", "F", "forward window starts 00:00-03:00 UTC (bar t open hour in {23, 0, 1, 2})",
       "Asia session flow", "directional edge differs (two-sided); |r| secondary", 0, [1, 2], FWD,
       "position sign(b_BTC) on state bars"),
    _h("H-TIME-FUNDING-HOUR", "F",
       "forward window starts within +-1h of a funding settlement 00/08/16 UTC "
       "(bar t open hour in {22, 23, 6, 7, 14, 15}); target signed by last settled funding",
       "payers of funding de-risk around settlement (inventory management)",
       "price moves against the funding-paying side", +1, [1, 2],
       "y = -sign(funding_t) * fwd log return_h (funding_t == 0 -> excluded)",
       "position -sign(funding_t) on state bars", data=("ohlcv", "funding")),
]

assert len(HYPOTHESES) == 28 and len({h["id"] for h in HYPOTHESES}) == 28


def registry_payload() -> dict:
    return {"feature": "F014", "splits": SPLITS, "blocks": BLOCKS, "protocol": PROTOCOL,
            "hypotheses": HYPOTHESES}


def registry_sha256() -> str:
    blob = json.dumps(registry_payload(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()
