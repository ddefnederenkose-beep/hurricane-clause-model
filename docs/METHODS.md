# Data & methods note (appendix)

Question: do sovereign hurricane clauses create meaningful fiscal space after a disaster, or are they too limited when the problem is solvency rather than liquidity? Annual Monte Carlo model, T = 30 years, N = 10,000 paths, seed 42, common random numbers (the same hurricane histories hit every regime, model version, clause design and grid cell, so differences are policy or parameters, never luck). **Every calibration value is `PLACEHOLDER_VERIFY` until the group enters a sourced value; each run prints the list.**

## Equations (b, D, pd, GFN in % of GDP; r, g decimals)
- Debt: b_t = [(1+r_t)/(1+g_t)] b_{t-1} + pd_t, split into a clause-covered stock b^c (initial share s) and other debt b^o; the primary deficit is allocated in proportion to stock size.
- Hurricane: hit with probability lambda (scenario-specific for `grenada_like`); damage D_t ~ lognormal(mu_D, sigma_D), capped at D_max.
- Growth: g_t = g_bar - phi D_t/100 + psi phi D_{t-1}/100. Primary deficit: pd_t = pd_bar + kappa sum_{j<R} D_{t-j}/R - rho (b_{t-1} - b*).
- Debt service: interest_t = r_t b_{t-1}/(1+g_t); amortization_t = b_{t-1}/(M(1+g_t)), rolled over (it enters GFN, not the stock). GFN_t = pd_t + interest_t + amortization_t.
- Version 2 rate: r_eff_t = (1-1/M) r_eff_{t-1} + (r_safe + x_t)/M, x_t = min{x_max, theta_b max(0, b_{t-1}-b_bar) + theta_G max(0, GFN_{t-1}-GFN_bar)}; r_eff_0 uses the initial conditions.
- Liquidity crisis: GFN_t > GFN_crit. Hurricane-attributable crisis: GFN_t exceeds the no-hurricane (lambda = 0) path by more than GFN_margin.

## Regimes and clause designs
- **A** no clause. **B** clause: a hit with D >= D_trig suspends interest and amortization on covered debt for K years (hit year included); a hit during a window restarts it; each activation uses one of at most three lifetime triggers (default on). Skipped interest is capitalized, so the covered stock is identical to A in Version 1. Skipped amortization becomes a deferred balance inside the stock, repaid after the window over `defer_repay_years`; amortization = (b^c - defbal)/M + repayment of defbal, so principal is paid once. **C** hypothetical forgiveness of the same suspended interest and amortization (a solvency benchmark, not a real instrument).
- Named designs (config/designs.yaml): **Grenada-style** (low covered share, K = 1, three-trigger cap, repayment over remaining maturity) and **Barbados-style** (covered share ~0.9, K = 2, same cap). Experiments 1-2 are run and labelled for both. An optional deferral-risk premium (constant spread on covered debt in B/C only, default off) is reported as one extra robustness table.

## Reading the results (important caveats)
- **Deferral design drives the hump.** With deferred principal repaid at 1/M (`defer_repay_years` = M), the clause weakly dominates no clause in Version 1 (B's GFN <= A's in every year, stocks identical), so every post-hurricane repayment-hump result is driven by repayment faster than 1/M and/or the Version 2 premium channel.
- **Real-world frame for repayment speed.** Actual clauses (Grenada 2015, Barbados 2018-19) repay deferred amounts over the remaining life of the instrument, the slow end of the grid we test. The result is therefore a design lesson, not an indictment: existing clauses sit in the helpful region, whereas a hypothetical clause with a 2-4-year catch-up would be actively harmful (in `grenada_like`, Version 1, a Barbados-style clause with 2-year catch-up raises P(liquidity crisis) by 9.1 pp relative to no clause; the worst corner of the design grid (Version 2, K = 4, 2-year catch-up) raises it by 19.9 pp). Do not quote "the clause hurts" without this condition.
- **No default or restructuring.** Unsustainable paths grow without bound, so terminal-debt levels in spiral scenarios (`high_debt`, Version 2, median b_T ~ 1,350% of GDP) are to be read as "unsustainable", not as forecasts. Use the years until b first exceeds 150% of GDP and the share of paths where the premium cap binds (100% of `high_debt` Version 2 paths: itself evidence for H2).
- **Heatmaps.** The debt axis varies the fiscal stance jointly (primary balance interpolated between the two scenarios): a vulnerability gradient, not a pure debt gradient. Colour scales are winsorized at the 95th percentile; the true maximum is printed in each caption.
- **Relief definitions (experiment 4), not comparable like-for-like.**
  - Regime B: *PV of deferred cash flows (timing relief; net transfer ~ 0)*: suspended interest + amortization on covered debt, discounted at r_bar, per suspension spell, reported as % of GDP only. It is gross cash-flow relief; the stock is unchanged, so creditors' net position is unchanged.
  - Regime C: *PV of debt relief (net transfer)*: forgiven service, reported as % of GDP and % of damage.
  - Scope: the identity PV(B deferred cash flows) = PV(A service) - PV(B service) holds only with `defer_repay_years` = M, no deferral premium and Version 1, where skipped service is never made up in gross terms; it is asserted path by path in that case and the code raises otherwise unless explicitly overridden.
- Regime C's covered-debt forgiveness can push debt below zero in a minority of paths (5.5% of Barbados-style `grenada_like` paths); no floor is imposed.

## Parameters, sources and status
<!-- PARAMS:START -->
| Parameter | Value | Meaning | Source | Status |
|---|---|---|---|---|
| lambda | 0.1 | annual probability of a major hurricane | (none yet) | PLACEHOLDER_VERIFY |
| mu_D | 2.302585092994046 | lognormal location parameter of damage (median damage = exp(mu_D) % of GDP) | (none yet) | PLACEHOLDER_VERIFY |
| sigma_D | 1.0 | lognormal scale parameter of damage (fat right tail) | (none yet) | PLACEHOLDER_VERIFY |
| D_max | 200 | cap on damage, % of GDP | (none yet) | PLACEHOLDER_VERIFY |
| D_trig | 5 | clause trigger threshold, % of GDP damage (proxy for a parametric trigger) | (none yet) | PLACEHOLDER_VERIFY |
| g_bar | 0.02 | trend real GDP growth | (none yet) | PLACEHOLDER_VERIFY |
| phi | 0.15 | output loss per unit of damage: growth falls by phi*D/100 in the hit year | (none yet) | PLACEHOLDER_VERIFY |
| psi | 0.5 | share of lost output recovered the following year through rebuilding | (none yet) | PLACEHOLDER_VERIFY |
| kappa | 0.3 | share of damage financed by the budget | (none yet) | PLACEHOLDER_VERIFY |
| R | 3 | years over which reconstruction spending is spread | (none yet) | PLACEHOLDER_VERIFY |
| r_bar | 0.03 | real effective interest rate, Version 1 (exogenous, constant) | (none yet) | PLACEHOLDER_VERIFY |
| r_safe | 0.03 | safe real rate, Version 2 (premium is added on top) | (none yet) | PLACEHOLDER_VERIFY |
| M | 8 | average maturity in years (1/M of each stock matures per year) | (none yet) | PLACEHOLDER_VERIFY |
| s | 0.6 | initial share of debt covered by the clause | (none yet) | PLACEHOLDER_VERIFY |
| K | 2 | deferral length in years | (none yet) | PLACEHOLDER_VERIFY |
| theta_b | 0.0005 | risk premium per pp of debt/GDP above b_bar (Version 2 only) | (none yet) | PLACEHOLDER_VERIFY |
| theta_G | 0.002 | risk premium per pp of GFN/GDP above GFN_bar (Version 2 only) | (none yet) | PLACEHOLDER_VERIFY |
| b_bar | 60 | debt/GDP threshold above which the premium rises (Version 2 only) | (none yet) | PLACEHOLDER_VERIFY |
| GFN_bar | 15 | GFN/GDP threshold above which the premium rises (Version 2 only) | (none yet) | PLACEHOLDER_VERIFY |
| defer_repay_years | 8 | ECONOMIC DESIGN PARAMETER: years over which deferred principal (defbal) is repaid after a deferral. = M gives post-window GFN of B equal to A (no hump); shorter than M creates a repayment hump. Set from the actual clause terms (remaining life of the instrument). | (none yet) | PLACEHOLDER_VERIFY |
| GFN_margin | 5 | hurricane-attributable liquidity crisis: GFN exceeds the no-hurricane (lambda=0) baseline path by more than this many pp of GDP | (none yet) | PLACEHOLDER_VERIFY |
| max_triggers | 3 | lifetime cap on the number of clause activations per path (every qualifying hit while the clause is still available uses one trigger) | Grenada 2015 bond terms, Asonuma et al. 2017 | PLACEHOLDER_VERIFY |
| use_trigger_cap | 1 | 1 = the lifetime trigger cap is on (default), 0 = unlimited triggers | Grenada 2015 bond terms, Asonuma et al. 2017 | PLACEHOLDER_VERIFY |
| deferral_spread | 0.0025 | constant spread (decimal, 0.0025 = 25 bps) added to the covered debt's interest rate in Regimes B/C only (robustness switch) | proxy for delay-risk pricing, cf. Mallucci 2022 | PLACEHOLDER_VERIFY |
| deferral_premium_on | 0 | 1 = apply deferral_spread to the covered stock in B/C; 0 = off (default) | proxy for delay-risk pricing, cf. Mallucci 2022 | PLACEHOLDER_VERIFY |
| x_max | 0.1 | cap on the risk premium x_t (decimal, 0.10 = 10pp); numerical/economic backstop, Version 2 only | (none yet) | PLACEHOLDER_VERIFY |
| GFN_crit | 15 | liquidity-crisis threshold, GFN as % of GDP | (none yet) | PLACEHOLDER_VERIFY |
| rho | 0.0 | fiscal reaction of primary deficit to debt above target (off by default) | (none yet) | PLACEHOLDER_VERIFY |
| b_star | 60 | debt target used by the fiscal reaction rule | (none yet) | PLACEHOLDER_VERIFY |
| grenada_like.b_0 | 65 | initial debt/GDP | (none yet) | PLACEHOLDER_VERIFY |
| grenada_like.pd_bar | -2 | baseline primary deficit/GDP (negative = surplus) | (none yet) | PLACEHOLDER_VERIFY |
| grenada_like.lambda | 0.051 | annual probability of a major hurricane for this scenario | Mallucci 2022, NOAA-based major-hurricane frequency, Grenada | PLACEHOLDER_VERIFY |
| high_debt.b_0 | 110 | initial debt/GDP | (none yet) | PLACEHOLDER_VERIFY |
| high_debt.pd_bar | 1 | baseline primary deficit/GDP (positive = deficit) | (none yet) | PLACEHOLDER_VERIFY |
| grenada_like_lambda_010.b_0 | 65 | initial debt/GDP | (none yet) | PLACEHOLDER_VERIFY |
| grenada_like_lambda_010.pd_bar | -2 | baseline primary deficit/GDP (negative = surplus) | (none yet) | PLACEHOLDER_VERIFY |
| grenada_like_lambda_010.lambda | 0.1 | sensitivity value only | (none yet) | PLACEHOLDER_VERIFY |
| grenada_style.s | 0.3 | share of debt covered (low) | (none yet) | PLACEHOLDER_VERIFY |
| grenada_style.K | 1 | years of service deferred per trigger | (none yet) | PLACEHOLDER_VERIFY |
| grenada_style.defer_repay_years | 8 | repayment over the remaining maturity (placeholder = M) | (none yet) | PLACEHOLDER_VERIFY |
| barbados_style.s | 0.9 | share of debt covered (high) | (none yet) | PLACEHOLDER_VERIFY |
| barbados_style.K | 2 | years of service deferred per trigger | (none yet) | PLACEHOLDER_VERIFY |
| barbados_style.defer_repay_years | 8 | repayment over the remaining maturity (placeholder = M) | (none yet) | PLACEHOLDER_VERIFY |

Software: Python 3.13.7, numpy 2.5.4, pandas 3.1.1, matplotlib 3.11.2, pyyaml 6.0.3. Seed and sizes: see `simulation` in calibration.yaml.
<!-- PARAMS:END -->
