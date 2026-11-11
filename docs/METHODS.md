# Data & methods note (DRAFT: full equations, parameter table and software versions are completed in build step 8)

## Key properties of the model the reader must know
- **Deferral design drives the hump.** With deferred principal repaid at 1/M (`defer_repay_years` = M), the clause weakly dominates no clause in Version 1 (B's GFN <= A's every year, stocks identical), so every post-hurricane repayment-hump result is driven by repayment faster than 1/M (a parameter to be set from Grenada's actual clause terms) and/or the Version 2 risk-premium channel.
- **No default or restructuring.** The model has no default, so unsustainable paths grow without bound; terminal-debt levels in spiral scenarios (e.g. `high_debt`, Version 2, median b_T ~ 1,350% of GDP) should be read as "unsustainable", not as forecasts. Use "years until b exceeds 150% of GDP" and the share of paths where the premium cap binds instead.
- **B's "relief" in experiment 4 is gross cash-flow relief** (suspended interest + amortization, discounted at r). Because the debt stock is identical to Regime A, it is not a net transfer: the creditor's net position is unchanged. Regime C's relief is a genuine grant (the stock falls by the forgiven amount compounded forward).
- All calibration values are `PLACEHOLDER_VERIFY` until sourced; every run prints the list.
