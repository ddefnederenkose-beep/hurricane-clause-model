# RESULTS v4: second revision (figure 1 v4, lump-sum diagnostics, robustness, Beryl validation)

Seed 42, N = 10,000 paths x T = 30 years, common random numbers across regimes and variants. No parameter changed; RESULTS_v3.md is untouched. Reproduction: the v3 grid is recomputed and matches outputs/v3/tables/grid_seed42.csv (max abs diff 0.0e+00); the robustness base cells match v3; the damage-median x0.75 / x1.25 cells (5-yr, standard measure) match outputs/tables/damage_median_sign_test.csv to 1e-6 points. Regenerate with `python run_v4.py`.

Conventions: 'points' = percentage points (of probability, or of GDP for GFN). Clause-minus-no-clause differences are paired per path (same draws), 95% CI = mean(d) +/- 1.96 sd(d)/sqrt(N); `*` = CI excludes 0. High-coverage design = s = 0.80, K = 2 (`barbados_style` in code). B'-lump = whole deferred balance paid in strike year + 6.

## A. Figure 1 (figures/figure1_v4.png): every number printed on the bars

Version 1, 5-year instalments unless stated. Panel B error bars are the marginal 95% CI of each probability (normal approximation). Panel A uses the existing windows: 'strike yr + next' = max GFN in t..t+1, 'strike yr + 5' = max over t..t+5, averaged over strikes with D >= 5.

**Panel A. Mean peak GFN, % of GDP (high-coverage design)**

| country | window | No clause | Clause, five-year instalments | Clause, lump sum (B'-lump) |
|---|---|---|---|---|
| Grenada-like | strike yr + next | 9.0 | 4.5 | 4.5 |
| Grenada-like | strike yr + 5 | 9.5 | 9.8 | 8.4 |
| High-debt | strike yr + next | 27.0 | 9.6 | 9.6 |
| High-debt | strike yr + 5 | 27.4 | 29.5 | 25.3 |

**Panel B. P(financing-stress episode), % (+/- half-width of 95% CI)**

| country | No clause | Grenada-style clause | High-coverage clause | High-coverage clause, B'-lump |
|---|---|---|---|---|
| Grenada-like | 23.1 (+/- 0.8) | 22.7 (+/- 0.8) | 24.7 (+/- 0.8) | 52.3 (+/- 1.0) |
| High-debt | 30.3 (+/- 0.9) | 30.5 (+/- 0.9) | 45.6 (+/- 1.0) | 62.0 (+/- 1.0) |

**Panel C. Equal-instalment break-even (years)**

| country | version | value |
|---|---|---|
| Grenada-like | V1 | 5.9 |
| Grenada-like | V2 | 5.9 |
| High-debt | V1 | 9.3 |
| High-debt | V2 | 5.6 |

Panel C's dashed line is the assumed five-year instalment period. These values are generated from the same data object as the figure labels.

## B1. Size of the deferred balance repaid in the lump-sum year (B'-lump, high-coverage)

| country | version | paths with a strike | lump falls due within 30 yrs | mean lump, % of GDP | median lump, % of GDP | 90th pct, % of GDP | service skipped in the first suspension (interest + principal, % of GDP at strike): mean / median |
|---|---|---|---|---|---|---|---|
| Grenada-like | V1 | 7,099 | 6,074 | 6.5 | 5.9 | 10.1 | 8.9 / 8.9 |
| Grenada-like | V2 | 7,099 | 6,074 | 6.6 | 6.0 | 10.2 | 9.1 / 9.1 |
| High-debt | V1 | 7,099 | 6,074 | 17.0 | 14.9 | 26.1 | 32.0 / 31.2 |
| High-debt | V2 | 7,099 | 6,074 | 28.8 | 22.7 | 54.2 | 96.1 / 62.7 |

The lump is the first positive deferred-balance repayment on each path (cash, % of GDP in the year it is paid, which is strike year + 6). Paths whose strike is too late for the lump to fall inside the 30 years are excluded from the mean and median. The last column is the total debt service suspended in the first window (interest and principal, each year as % of that year's GDP). The brief's 'about 12% of GDP' is higher than every Grenada-like number here; it matches a static back-of-envelope, 2 years x 0.8 x 65 x (2.4% + 1/10.6) = 12.3, i.e. two years of full service on the covered debt at b_0 = 65 with no growth and no debt run-down (the derivation is not in the repo, so this is my inference). In the model the lump is smaller than the skipped service for two reasons: (a) it contains only the deferred AMORTIZATION; skipped interest is capitalised into the covered stock and then amortised on the ordinary 1/M schedule (the interpretation flagged in RESULTS_v3); (b) it is paid six years later in a larger economy (nominal growth 4.8% a year), so the same currency amount is a smaller share of GDP. A variant in which capitalised interest is also paid in the lump would give a larger lump than reported here; it was not run.

## B2. How extreme is the lump-sum year? P(GFN > 15% of GDP)

| country | version | regime | mean GFN in the lump year, % of GDP | P(GFN>15 in the lump year), % of paths where a lump falls due | same, as % of ALL paths | P(GFN>15 in any of 30 years), % |
|---|---|---|---|---|---|---|
| Grenada-like | V1 | No clause | 5.8 | 0.1 | 0.0 | 5.9 |
| Grenada-like | V1 | Clause, 5-yr instalments | 6.9 | 0.1 | 0.1 | 5.8 |
| Grenada-like | V1 | Clause, B'-lump | 11.7 | 11.4 | 6.9 | 10.4 |
| Grenada-like | V2 | No clause | 5.9 | 0.2 | 0.1 | 6.0 |
| Grenada-like | V2 | Clause, 5-yr instalments | 7.1 | 0.5 | 0.3 | 5.9 |
| Grenada-like | V2 | Clause, B'-lump | 11.9 | 12.4 | 7.6 | 10.8 |
| High-debt | V1 | No clause | 24.4 | 100.0 | 60.7 | 100.0 |
| High-debt | V1 | Clause, 5-yr instalments | 27.3 | 100.0 | 60.7 | 100.0 |
| High-debt | V1 | Clause, B'-lump | 39.8 | 100.0 | 60.7 | 100.0 |
| High-debt | V2 | No clause | 85.7 | 100.0 | 60.7 | 100.0 |
| High-debt | V2 | Clause, 5-yr instalments | 89.5 | 100.0 | 60.7 | 100.0 |
| High-debt | V2 | Clause, B'-lump | 110.4 | 100.0 | 60.7 | 100.0 |

'Lump year' = each path's own year in which the B'-lump regime pays its lump; the same calendar year is used for the no-clause and instalment regimes on that path. In High-debt the absolute flag is saturated by construction (starting GFN is already above 15% of GDP).

**How much of the lump-sum effect is the 5-point measure?** P(GFN more than m points above the same regime's no-storm path in at least one year), no clause vs B'-lump:

| country | version | m=5: no clause / B'-lump / diff, % | m=10: no clause / B'-lump / diff, % | m=15: no clause / B'-lump / diff, % |
|---|---|---|---|---|
| Grenada-like | V1 | 23.1 / 52.3 / +29.2 | 6.2 / 11.6 / +5.4 | 2.4 / 2.4 / +0.0 |
| Grenada-like | V2 | 23.0 / 53.4 / +30.4 | 6.2 / 11.8 / +5.6 | 2.5 / 2.6 / +0.1 |
| High-debt | V1 | 30.3 / 62.0 / +31.6 | 10.3 / 61.2 / +50.8 | 4.4 / 41.2 / +36.8 |
| High-debt | V2 | 61.9 / 63.1 / +1.2 | 47.1 / 61.6 / +14.5 | 36.2 / 55.2 / +19.0 |

Mean peak GFN over t..t+6 (the window that includes the lump year), % of GDP, no clause / 5-yr instalments / B'-lump. Figure 1's 'strike yr + 5' window ends one year BEFORE the lump falls due, which is why its B'-lump bars look lower than the instalment bars:

| country | version | t..t+6: no clause / 5-yr / B'-lump |
|---|---|---|
| Grenada-like | V1 | 9.6 / 9.9 / 11.3 |
| Grenada-like | V2 | 9.7 / 10.0 / 11.5 |
| High-debt | V1 | 27.4 / 29.7 / 38.1 |
| High-debt | V2 | 101.6 / 103.8 / 119.4 |

## B3. Refinanced lump sum (new rule `lump_refinanced`; optional item)

Interpretation: nothing is paid in cash in year strike + 6. The deferred balance is folded into the regular covered stock and then amortises on the ordinary 1/M schedule at the market rate (in V2 the effective rate, which carries the endogenous risk premium). Clause-minus-no-clause on the standard stress measure, high-coverage design:

| country | version | schedule | P no clause, % | P clause, % | difference, points [95% CI] |
|---|---|---|---|---|---|
| Grenada-like | V1 | 5-yr equal [baseline] | 23.1 | 24.7 | +1.6 [+1.1, +2.0]* |
| Grenada-like | V1 | B'-lump | 23.1 | 52.3 | +29.2 [+28.3, +30.1]* |
| Grenada-like | V1 | B'-lump refinanced | 23.1 | 16.3 | -6.9 [-7.3, -6.4]* |
| Grenada-like | V2 | 5-yr equal [baseline] | 23.0 | 24.5 | +1.5 [+1.1, +2.0]* |
| Grenada-like | V2 | B'-lump | 23.0 | 53.4 | +30.4 [+29.5, +31.4]* |
| Grenada-like | V2 | B'-lump refinanced | 23.0 | 16.1 | -6.9 [-7.3, -6.4]* |
| High-debt | V1 | 5-yr equal [baseline] | 30.3 | 45.6 | +15.2 [+14.5, +16.0]* |
| High-debt | V1 | B'-lump | 30.3 | 62.0 | +31.6 [+30.6, +32.6]* |
| High-debt | V1 | B'-lump refinanced | 30.3 | 17.7 | -12.6 [-13.3, -12.0]* |
| High-debt | V2 | 5-yr equal [baseline] | 61.9 | 63.1 | +1.2 [+0.5, +2.0]* |
| High-debt | V2 | B'-lump | 61.9 | 63.1 | +1.1 [+0.5, +1.8]* |
| High-debt | V2 | B'-lump refinanced | 61.9 | 41.7 | -20.2 [-21.0, -19.4]* |

## C. Robustness of the two conclusions that now drive the brief

Variants: damage median x0.75 and x1.25 (mu_D = ln(new median), sigma_D unchanged; same method as docs/damage_median_sign_test.py); '+25 bp delay premium' = `deferral_premium_on = 1` with the existing 25 bp spread on the covered stock's rate in the clause regime only (each regime is compared with its own no-storm path). Cells: clause minus no clause, points [95% CI]; * = CI excludes 0.

**(i) B'-lump, standard stress measure (5 points)**

| country | design | version | base | median x0.75 | median x1.25 | +25 bp delay premium | sign flips vs base | loses significance vs base |
|---|---|---|---|---|---|---|---|---|
| Grenada-like | Grenada-style (s=0.10, K=1) | V1 | -1.1 [-1.3, -0.8]* | -0.7 [-0.9, -0.6]* | -1.1 [-1.3, -0.9]* | -1.1 [-1.3, -0.9]* | none | no |
| Grenada-like | Grenada-style (s=0.10, K=1) | V2 | -1.1 [-1.3, -0.8]* | -0.8 [-1.0, -0.6]* | -1.3 [-1.5, -1.0]* | -1.1 [-1.3, -0.9]* | none | no |
| Grenada-like | High-coverage (s=0.80, K=2) | V1 | +29.2 [+28.3, +30.1]* | +31.2 [+30.2, +32.1]* | +26.2 [+25.2, +27.1]* | +31.2 [+30.3, +32.2]* | none | no |
| Grenada-like | High-coverage (s=0.80, K=2) | V2 | +30.4 [+29.5, +31.4]* | +32.5 [+31.6, +33.4]* | +27.4 [+26.4, +28.3]* | +32.5 [+31.6, +33.5]* | none | no |
| High-debt | Grenada-style (s=0.10, K=1) | V1 | -1.5 [-1.8, -1.3]* | -1.2 [-1.4, -0.9]* | -1.4 [-1.6, -1.1]* | -1.5 [-1.7, -1.2]* | none | no |
| High-debt | Grenada-style (s=0.10, K=1) | V2 | -0.5 [-0.9, -0.1]* | -0.3 [-0.7, +0.1] | -0.8 [-1.2, -0.4]* | -0.3 [-0.7, +0.1] | none | median x0.75 (point estimate -0.3, CI spans 0), +25 bp delay premium (point estimate -0.3, CI spans 0) |
| High-debt | High-coverage (s=0.80, K=2) | V1 | +31.6 [+30.6, +32.6]* | +36.5 [+35.5, +37.5]* | +27.8 [+26.8, +28.7]* | +31.6 [+30.6, +32.6]* | none | no |
| High-debt | High-coverage (s=0.80, K=2) | V2 | +1.1 [+0.5, +1.8]* | +2.8 [+2.1, +3.5]* | +0.0 [-0.7, +0.7] | +1.3 [+0.6, +2.0]* | none | median x1.25 (point estimate +0.0, CI spans 0) |

**(ii) 5-year instalments, 3-point storm-window measure**

| country | design | version | base | median x0.75 | median x1.25 | +25 bp delay premium | sign flips vs base | loses significance vs base |
|---|---|---|---|---|---|---|---|---|
| Grenada-like | Grenada-style (s=0.10, K=1) | V1 | -0.6 [-0.8, -0.3]* | -0.5 [-0.7, -0.2]* | -0.7 [-0.9, -0.5]* | -0.6 [-0.8, -0.3]* | none | no |
| Grenada-like | Grenada-style (s=0.10, K=1) | V2 | -0.7 [-1.0, -0.5]* | -0.5 [-0.7, -0.3]* | -0.7 [-1.0, -0.5]* | -0.7 [-1.0, -0.4]* | none | no |
| Grenada-like | High-coverage (s=0.80, K=2) | V1 | -12.8 [-13.5, -12.2]* | -12.2 [-12.8, -11.6]* | -13.2 [-13.9, -12.6]* | -13.1 [-13.8, -12.4]* | none | no |
| Grenada-like | High-coverage (s=0.80, K=2) | V2 | -13.1 [-13.7, -12.4]* | -12.2 [-12.8, -11.6]* | -13.2 [-13.9, -12.6]* | -13.3 [-14.0, -12.7]* | none | no |
| High-debt | Grenada-style (s=0.10, K=1) | V1 | +0.3 [-0.0, +0.6] | +0.3 [-0.0, +0.6] | +0.2 [-0.1, +0.5] | +0.3 [-0.0, +0.6] | none | no |
| High-debt | Grenada-style (s=0.10, K=1) | V2 | -1.6 [-1.8, -1.3]* | -1.5 [-1.8, -1.2]* | -1.6 [-1.9, -1.3]* | -1.5 [-1.8, -1.2]* | none | no |
| High-debt | High-coverage (s=0.80, K=2) | V1 | +1.4 [+0.9, +1.9]* | +2.3 [+1.8, +2.8]* | +0.7 [+0.2, +1.2]* | +2.5 [+2.0, +3.1]* | none | no |
| High-debt | High-coverage (s=0.80, K=2) | V2 | -2.0 [-2.7, -1.3]* | -1.9 [-2.7, -1.2]* | -2.4 [-3.0, -1.7]* | -1.7 [-2.4, -1.0]* | none | no |

- (i) B'-lump: no sign flips in any of the 24 variant cells (3 variants x 8 cells). Loses significance (same sign or zero, CI now spans 0): High-debt / Grenada-style (s=0.10, K=1) / V2: median x0.75 (point estimate -0.3, CI spans 0), +25 bp delay premium (point estimate -0.3, CI spans 0); High-debt / High-coverage (s=0.80, K=2) / V2: median x1.25 (point estimate +0.0, CI spans 0).

- (ii) 3-point window, 5-yr: no sign flips in any of the 24 variant cells (3 variants x 8 cells). No cell loses significance.

## D. Beryl validation (Grenada-like, no calibration change)

Set-up: b_0 = 65% of GDP (unchanged), one deterministic strike in year 1 (= 2024) of 16.5% of GDP, no other storms, R = 3, FRA surplus rule on, all other parameters as in calibration.yaml. Debt is public debt incl. SOEs at year end. **Insurance:** kappa = 0.42 is already net of the 3.2%-of-GDP CCRIF payout ((10.2 - 3.2) / 16.5), so the sourced run has the payout inside it. The second setting uses the gross share 0.62 with the payout as an explicit 3.2-point cash inflow in 2024; the third is the literal reading (0.42 plus an extra 3.2) and double-counts the payout; it is shown only for completeness. IMF reference (IMF CR 26/9 Table 1 p.26, from docs/parameter_sourcing_register.md): public debt 72.7% (2024), 68.3% (2025e), 65.8% (2026p); primary balance +10.0, -3.2, -3.5. The docs contain no IMF GFN path, so GFN has no reference column.

| version | setting | regime | debt 2024 | debt 2025 | debt 2026 | GFN 2024 | GFN 2025 | GFN 2026 |
|---|---|---|---|---|---|---|---|---|
| V1 | kappa 0.42 (payout netted in; sourced setting) | A (no clause) | 65.9 | 64.4 | 63.7 | 8.3 | 8.2 | 8.1 |
| V1 | kappa 0.42 (payout netted in; sourced setting) | B'-lump, Grenada-style (s=0.10, K=1) | 65.9 | 64.4 | 63.7 | 7.6 | 8.1 | 8.0 |
| V1 | kappa 0.62 gross + explicit 3.2 payout in 2024 | A (no clause) | 63.8 | 63.5 | 63.9 | 6.2 | 9.0 | 9.1 |
| V1 | kappa 0.62 gross + explicit 3.2 payout in 2024 | B'-lump, Grenada-style (s=0.10, K=1) | 63.8 | 63.5 | 63.9 | 5.5 | 9.0 | 9.0 |
| V1 | kappa 0.42 + extra 3.2 payout (literal; double-counts) | A (no clause) | 62.7 | 61.3 | 60.7 | 5.1 | 7.8 | 7.7 |
| V1 | kappa 0.42 + extra 3.2 payout (literal; double-counts) | B'-lump, Grenada-style (s=0.10, K=1) | 62.7 | 61.3 | 60.7 | 4.4 | 7.7 | 7.7 |
| V2 | kappa 0.42 (payout netted in; sourced setting) | A (no clause) | 66.0 | 64.7 | 64.2 | 8.5 | 8.3 | 8.3 |
| V2 | kappa 0.42 (payout netted in; sourced setting) | B'-lump, Grenada-style (s=0.10, K=1) | 66.0 | 64.7 | 64.2 | 7.7 | 8.3 | 8.2 |
| V2 | kappa 0.62 gross + explicit 3.2 payout in 2024 | A (no clause) | 63.9 | 63.8 | 64.4 | 6.4 | 9.2 | 9.3 |
| V2 | kappa 0.62 gross + explicit 3.2 payout in 2024 | B'-lump, Grenada-style (s=0.10, K=1) | 63.9 | 63.8 | 64.4 | 5.6 | 9.1 | 9.2 |
| V2 | kappa 0.42 + extra 3.2 payout (literal; double-counts) | A (no clause) | 62.8 | 61.6 | 61.1 | 5.3 | 8.0 | 7.9 |
| V2 | kappa 0.42 + extra 3.2 payout (literal; double-counts) | B'-lump, Grenada-style (s=0.10, K=1) | 62.8 | 61.6 | 61.1 | 4.5 | 7.9 | 7.8 |

IMF: debt 72.7 / 68.3 / 65.8 (2024 / 2025e / 2026p).

Gap for the sourced setting (no clause), reported as it is:

| version | debt gap vs IMF, 2024 / 2025 / 2026 (model minus IMF, points) | model primary balance 2024 / 2025 / 2026 | IMF primary balance | model nominal growth 2024 / 2025 / 2026, % |
|---|---|---|---|---|
| V1 | -6.8 / -3.9 / -2.1 | -0.8 / -0.8 / -0.8 | +10.0 / -3.2 / -3.5 | 2.3 / 6.0 / 4.8 |
| V2 | -6.7 / -3.6 / -1.6 | -0.8 / -0.8 / -0.8 | +10.0 / -3.2 / -3.5 | 2.3 / 6.0 / 4.8 |

