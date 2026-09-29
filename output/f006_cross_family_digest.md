# F006 cross-family digest

Generated 2026-09-29T20:32:58.580334+00:00. 22 `output/f006_*` directories found (1 frozen-schema, 20 legacy-schema, 1 other/missing).

## Frozen-schema families (H1/H2 per name)

| family | name | mean net PnL (10-series) | H1 pass | H2 status |
| --- | --- | ---: | --- | --- |
| runner_selfcheck | DONCHIAN_20 | 19.6661 | True | falsified |

## Frozen-schema families -- summary/results.csv aggregates (all rows, incl. control)

| family | rows | mean n_trades | mean win_rate | mean max_drawdown_pct | exit mix totals |
| --- | ---: | ---: | ---: | ---: | --- |
| runner_selfcheck | 20 | 87.85 | 25.0335 | 14.6717 | exit_initial_sl=826, exit_trailing_sl=0, exit_take_profit=0, exit_signal_reverse=920, exit_end_of_data=11 |

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
