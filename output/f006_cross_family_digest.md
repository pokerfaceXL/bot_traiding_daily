# F006 cross-family digest

Generated 2026-09-29T22:27:41.724193+00:00. 31 `output/f006_*` directories found (10 frozen-schema, 20 legacy-schema, 1 other/missing).

Learning only: imported Train-1 artifacts; no reruns, holdout or promotion.
H1 uses CSV `train1_net_pnl` when complete (manifest fallback is labelled). H2 uses stored CSV `promotion_pass`, gated by Train-1 H1; it is not a new validation.
Trade/WR/DD/exit metrics cover the stored simulation rows, including warm-up/boundary where present; only PnL/H1 is Train-1-filtered. Means are unweighted over finite values. Missing columns are unavailable, not zero. Thin-series means mean n_trades < 15.

Control sanity: **PASS** — DONCHIAN_55 / runner_selfcheck, 10 series, mean Train-1 = 58.3870526; delta vs +58.39 = -0.0029474 (tolerance $0.01). This checks archived CSV plus the stored harness comparison, not a fresh experiment.

## Frozen-schema families (H1/H2 per name)

Names ranked within each family by mean Train-1 PnL; control excluded from ranking.

| family | name | mean Train-1 PnL | H1 pass | family H2 status | H1 source | mean n_trades | mean WR | mean DD % | thin-series | exit mix totals |
| --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| beta_gate | BETA_GATE_DONCH20 | 31.4003 | True | falsified | results.csv train1_net_pnl | 136.2 | 26.464 | 17.3583 | False | exit_trailing_sl=0 |
| beta_gate | BETA_GATE_MR_DONCH20 | -3.6515 | False | falsified | results.csv train1_net_pnl | 1.1 | 0.0 | 0.8204 | True | exit_trailing_sl=0 |
| btc_filter | BTC_FILTER_ER20_DONCHIAN_20 | 73.6501 | True | falsified | results.csv train1_net_pnl | 59.8 | 20.112 | 11.4664 | False | exit_trailing_sl=0 |
| btc_filter | BTC_FILTER_ER20_DONCHIAN_10 | 60.5683 | True | falsified | results.csv train1_net_pnl | 69.7 | 20.433 | 12.2183 | False | exit_trailing_sl=0 |
| btc_filter | BTC_FILTER_ER20_DONCHIAN_5 | 44.5903 | True | falsified | results.csv train1_net_pnl | 79.5 | 20.694 | 10.8195 | False | exit_trailing_sl=0 |
| htf_gap_midfill | HTF_FVG_MID_R1 | 26.7072 | True | falsified | results.csv train1_net_pnl | 35.8 | 20.717 | 12.2376 | False | exit_trailing_sl=0 |
| htf_gap_midfill | HTF_FVG_MID_R3 | 23.8136 | True | falsified | results.csv train1_net_pnl | 40.1 | 21.266 | 12.1765 | False | exit_trailing_sl=0 |
| htf_gap_midfill | HTF_FVG_MID_R2 | 23.7520 | True | falsified | results.csv train1_net_pnl | 39.7 | 21.596 | 11.9772 | False | exit_trailing_sl=0 |
| liq_cascade_proxy | LIQ_CASCADE_20_120_6_R15_V25_C75 | 25.3974 | True | falsified | results.csv train1_net_pnl | 22.1 | 17.478 | 9.2524 | False | exit_trailing_sl=0 |
| liq_cascade_proxy | LIQ_CASCADE_20_120_6_R18_V20_C80 | 23.7958 | True | falsified | results.csv train1_net_pnl | 23.9 | 14.713 | 9.0721 | False | exit_trailing_sl=0 |
| liq_cascade_proxy | LIQ_CASCADE_20_120_6_R20_V15_C75 | 19.4507 | True | falsified | results.csv train1_net_pnl | 28.2 | 16.947 | 10.1186 | False | exit_trailing_sl=0 |
| liq_cascade_proxy | LIQ_CASCADE_20_120_6_R18_V20_C75 | 18.7588 | True | falsified | results.csv train1_net_pnl | 27.5 | 17.363 | 9.9806 | False | exit_trailing_sl=0 |
| liq_cascade_proxy | LIQ_CASCADE_20_120_6_R18_V30_C75 | 15.3423 | True | falsified | results.csv train1_net_pnl | 16.3 | 16.433 | 8.0665 | False | exit_trailing_sl=0 |
| liq_range_eqh | RANGE_EQH_RECLAIM_WIDE | 64.3201 | True | falsified | results.csv train1_net_pnl | 58.8 | 28.789 | 13.2053 | False | exit_trailing_sl=0 |
| liq_range_eqh | RANGE_EQH_RECLAIM_L2 | 54.1309 | True | falsified | results.csv train1_net_pnl | 55.7 | 29.283 | 12.6483 | False | exit_trailing_sl=0 |
| liq_range_eqh | RANGE_EQH_RECLAIM_TIGHT | 39.5076 | True | falsified | results.csv train1_net_pnl | 51.2 | 26.788 | 12.3061 | False | exit_trailing_sl=0 |
| liq_range_eqh | RANGE_EQH_RECLAIM_WICK | 31.2783 | True | falsified | results.csv train1_net_pnl | 44.3 | 23.461 | 12.6809 | False | exit_trailing_sl=0 |
| liq_range_eqh | RANGE_EQH_RECLAIM_L3 | -4.1399 | False | falsified | results.csv train1_net_pnl | 99.4 | 33.436 | 14.3292 | False | exit_trailing_sl=0 |
| multi_tf_pa | MTFP_HTF_BRK20 | 35.0825 | True | falsified | results.csv train1_net_pnl | 97.8 | 25.019 | 16.2622 | False | exit_trailing_sl=0 |
| multi_tf_pa | MTFP_HTF_BRK10 | 29.8073 | True | falsified | results.csv train1_net_pnl | 127.0 | 26.371 | 15.6355 | False | exit_trailing_sl=0 |
| multi_tf_pa | MTFP_HTF_PIN | 22.5572 | True | falsified | results.csv train1_net_pnl | 23.7 | 18.49 | 10.9205 | False | exit_trailing_sl=0 |
| multi_tf_pa | MTFP_HTF_BLOCK | 18.9065 | True | falsified | results.csv train1_net_pnl | 128.3 | 26.415 | 17.5495 | False | exit_trailing_sl=0 |
| multi_tf_pa | MTFP_HTF_BRK5 | 11.0717 | True | falsified | results.csv train1_net_pnl | 138.7 | 25.181 | 17.3518 | False | exit_trailing_sl=0 |
| runner_selfcheck | DONCHIAN_20 | 19.6661 | True | falsified | results.csv train1_net_pnl | 128.1 | 26.371 | 18.3637 | False | exit_initial_sl=532, exit_trailing_sl=0, exit_take_profit=0, exit_signal_reverse=742, exit_end_of_data=7 |
| session_regime | SESSION_NY_ASIA_CONT | -4.8106 | False | not_applicable_h1_failed | results.csv train1_net_pnl | 186.8 | 25.601 | 22.5188 | False | exit_trailing_sl=0 |
| session_regime | SESSION_LONDON_ASIA_CONT_ADR_VETO | -39.6807 | False | not_applicable_h1_failed | results.csv train1_net_pnl | 186.4 | 26.789 | 21.8174 | False | exit_trailing_sl=0 |
| session_regime | SESSION_LONDON_ASIA_CONT | -41.4239 | False | not_applicable_h1_failed | results.csv train1_net_pnl | 187.3 | 26.755 | 22.1597 | False | exit_trailing_sl=0 |
| session_regime | SESSION_ASIA_FADE | -48.5038 | False | not_applicable_h1_failed | results.csv train1_net_pnl | 215.2 | 37.229 | 22.9383 | False | exit_trailing_sl=0 |
| sube_inv_fvg | SINV_FIRST_H4 | 41.4145 | True | falsified | results.csv train1_net_pnl | 0.6 | 10.0 | 4.6303 | True | exit_trailing_sl=0 |
| sube_inv_fvg | SINV_FIRST_SMT | -1.3298 | False | falsified | results.csv train1_net_pnl | 0.4 | 0.0 | 0.2683 | True | exit_trailing_sl=0 |
| sube_inv_fvg | SINV_MSS_IN_FVG | -5.4986 | False | falsified | results.csv train1_net_pnl | 2.2 | 6.666 | 2.3991 | True | exit_trailing_sl=0 |
| sube_inv_fvg | SINV_FIRST_FVG | -7.1403 | False | falsified | results.csv train1_net_pnl | 2.2 | 0.0 | 3.2722 | True | exit_trailing_sl=0 |
| sube_inv_fvg | SINV_MSS_CLOSE | -10.1421 | False | falsified | results.csv train1_net_pnl | 3.6 | 6.666 | 2.9284 | True | exit_trailing_sl=0 |
| vol_regime_wrap | VOLW_HIGH_BRK_20 | 59.6513 | True | falsified | results.csv train1_net_pnl | 88.6 | 23.773 | 14.7152 | False | exit_trailing_sl=0 |
| vol_regime_wrap | VOLW_HL_20 | 1.3981 | True | falsified | results.csv train1_net_pnl | 226.4 | 37.978 | 17.26 | False | exit_trailing_sl=0 |
| vol_regime_wrap | VOLW_LOW_MR_20 | -2.8766 | False | falsified | results.csv train1_net_pnl | 124.5 | 43.132 | 11.8639 | False | exit_trailing_sl=0 |

## Frozen-schema families -- summary/results.csv aggregates (all rows, incl. control)

| family | rows | mean n_trades | mean win_rate | mean max_drawdown_pct | mean phase-fit | mean profit_factor | mean calmar | mean DD USD | thin-series | exit mix totals |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| beta_gate | 30 | 61.6333 | 16.72 | 9.7195 | None | None | None | None | False | exit_trailing_sl=0 |
| btc_filter | 40 | 64.15 | 21.2338 | 11.371 | None | None | None | None | False | exit_trailing_sl=0 |
| htf_gap_midfill | 40 | 40.8 | 21.8188 | 11.8428 | None | None | None | None | False | exit_trailing_sl=0 |
| liq_cascade_proxy | 60 | 27.6 | 17.7717 | 9.5783 | None | None | None | None | False | exit_trailing_sl=0 |
| liq_range_eqh | 60 | 59.5 | 27.5755 | 12.6916 | None | None | None | None | False | exit_trailing_sl=0 |
| multi_tf_pa | 60 | 93.85 | 24.1953 | 14.7832 | None | None | None | None | False | exit_trailing_sl=0 |
| runner_selfcheck | 20 | 87.85 | 25.0335 | 14.6717 | None | 1.5848 | 0.5857 | 85.5716 | False | exit_initial_sl=826, exit_trailing_sl=0, exit_take_profit=0, exit_signal_reverse=920, exit_end_of_data=11 |
| session_regime | 50 | 164.66 | 28.014 | 20.0828 | None | None | None | None | False | exit_trailing_sl=0 |
| sube_inv_fvg | 60 | 9.4333 | 7.838 | 4.0797 | None | None | None | None | True | exit_trailing_sl=0 |
| vol_regime_wrap | 40 | 121.775 | 32.1448 | 13.7047 | None | None | None | None | False | exit_trailing_sl=0 |

## Non-frozen-schema directories (not digestible into the H1/H2 table above)

| dir | schema |
| --- | --- |
| f006_catalog_notrail_sweep | legacy |
| f006_cooldown | legacy |
| f006_donchian | legacy |
| f006_entry_cross_symbol | legacy |
| f006_entry_cross_symbol_refined | legacy |
| f006_entry_trend_confirm | legacy |
| f006_entry_width_expansion | legacy |
| f006_exit_take_profit | legacy |
| f006_lorentzian | legacy |
| f006_loss_recency_cooldown | legacy |
| f006_mean_reversion_notrail | legacy |
| f006_notrail_monthly | legacy |
| f006_notrail_monthly_catalog5 | legacy |
| f006_one_shot | legacy |
| f006_portfolio_diversification | missing_manifest |
| f006_position_sizing_vol_inverse | legacy |
| f006_regime_filter | legacy |
| f006_stop_width | legacy |
| f006_stop_width_notrail | legacy |
| f006_trailing_boundary | legacy |
| f006_trailing_sweep | legacy |
