# RESULTS v3: revised brief runs

Model: seed 42, N = 10,000 paths x T = 30 years, common random numbers across regimes, calibration unchanged (config/calibration.yaml, scenarios.yaml, designs.yaml). New code only: regime B' (src/regimes.py rules `lump_at_horizon`, `equal_to_horizon`), src/v3.py, run_v3.py. Regenerate with `python run_v3.py`; full-precision CSVs are in outputs/v3/tables/.

**Reproduction check.** The new code reproduces the existing baseline (5-yr equal-instalment) P(stress) and mean peak GFN of outputs/tables/exp1_baseline_v1.csv in all 8 country x design cells (max absolute difference 0.0e+00), the equal-instalment break-evens of exp3_repay_switch_points.csv, and the K-vs-R grid of exp3_reconstruction_check.csv. No baseline number changed.

## Definitions

- **Financing-stress episode** (formerly "hurricane-attributable crisis"; definition unchanged): GFN more than 5 pp of GDP above the same regime's no-hurricane path in at least one of the 30 years.
- **Countries:** Grenada-like (b0 = 65, primary surplus) and High-debt (b0 = 110, primary deficit). **Designs:** Grenada-style (s = 0.10, K = 1) and High-coverage (s = 0.80, K = 2; `barbados_style` in the code). **V1** = fixed r, **V2** = endogenous risk premium.
- **Paired CI:** per path d_i = 1[stress with clause] - 1[stress without clause]; difference = mean(d); 95% CI = mean(d) +/- 1.96 sd(d)/sqrt(N). "Significant" = CI excludes 0. A negative difference means the clause LOWERS the probability. Percentages and pp are shown to 1 decimal; significance is decided on the unrounded values.
- **Regime B' (Grenada's actual repayment).** Deferred amounts are repaid starting the year after the suspension ends; due date = strike year + 6. **B'-lump:** one lump-sum payment in strike year + 6 (IMF CR 25/39: added to the principal due at the 2030 maturity). **B'-inst:** equal annual instalments from the year after the suspension ends through strike year + 6 (Asonuma et al. 2017: repaid over the bond's remaining life), i.e. 6 instalments for K = 1 and 5 for K = 2. Interpretations to confirm: (i) "capitalized interest" is treated exactly as in the baseline - skipped interest accrues into the covered stock (so the V1 stock equals regime A) and is amortised on the regular 1/M schedule; only the deferred *amortization* tranche follows the B' schedule; (ii) a second trigger re-sets the due date to (latest trigger year + 6) for the pooled balance (the analogue of the baseline's instalment-counter reset).
- **Mean peak GFN** (% of GDP) is averaged over qualifying strikes (D >= D_trig = 5); "strike year+next" = max GFN in years t, t+1; "strike year+5" = max over t..t+5.

## Table 1. Paired effect of the clause on P(financing-stress episode), baseline 5-year equal-instalment repayment

| country | design | version | P no clause | P clause | difference | 95% CI | significant (CI excludes 0)? |
|---|---|---|---|---|---|---|---|
| Grenada-like | Grenada-style (s=0.10, K=1) | V1 | 23.1% | 22.7% | -0.5 pp | [-0.7, -0.3] pp | yes |
| Grenada-like | Grenada-style (s=0.10, K=1) | V2 | 23.0% | 22.5% | -0.4 pp | [-0.7, -0.2] pp | yes |
| Grenada-like | High-coverage (s=0.80, K=2) | V1 | 23.1% | 24.7% | +1.6 pp | [+1.1, +2.0] pp | yes |
| Grenada-like | High-coverage (s=0.80, K=2) | V2 | 23.0% | 24.5% | +1.5 pp | [+1.1, +2.0] pp | yes |
| High-debt | Grenada-style (s=0.10, K=1) | V1 | 30.3% | 30.5% | +0.2 pp | [-0.1, +0.5] pp | no |
| High-debt | Grenada-style (s=0.10, K=1) | V2 | 61.9% | 60.7% | -1.2 pp | [-1.4, -0.9] pp | yes |
| High-debt | High-coverage (s=0.80, K=2) | V1 | 30.3% | 45.6% | +15.2 pp | [+14.5, +16.0] pp | yes |
| High-debt | High-coverage (s=0.80, K=2) | V2 | 61.9% | 63.1% | +1.2 pp | [+0.5, +2.0] pp | yes |

### Table 1b. Same, for P(GFN > 15% of GDP in at least one year)

| country | design | version | P no clause | P clause | difference | 95% CI | significant (CI excludes 0)? |
|---|---|---|---|---|---|---|---|
| Grenada-like | Grenada-style (s=0.10, K=1) | V1 | 5.9% | 5.8% | -0.1 pp | [-0.2, -0.0] pp | yes |
| Grenada-like | Grenada-style (s=0.10, K=1) | V2 | 6.0% | 5.9% | -0.2 pp | [-0.3, -0.1] pp | yes |
| Grenada-like | High-coverage (s=0.80, K=2) | V1 | 5.9% | 5.8% | -0.1 pp | [-0.3, +0.1] pp | no |
| Grenada-like | High-coverage (s=0.80, K=2) | V2 | 6.0% | 5.9% | -0.1 pp | [-0.3, +0.1] pp | no |
| High-debt | Grenada-style (s=0.10, K=1) | V1 | 100.0% | 100.0% | +0.0 pp | [+0.0, +0.0] pp | no |
| High-debt | Grenada-style (s=0.10, K=1) | V2 | 100.0% | 100.0% | +0.0 pp | [+0.0, +0.0] pp | no |
| High-debt | High-coverage (s=0.80, K=2) | V1 | 100.0% | 100.0% | +0.0 pp | [+0.0, +0.0] pp | no |
| High-debt | High-coverage (s=0.80, K=2) | V2 | 100.0% | 100.0% | +0.0 pp | [+0.0, +0.0] pp | no |

Note: in High-debt, starting GFN is already above 15% of GDP, so this absolute flag is 100% in every regime by construction: the difference is exactly 0 with a degenerate CI (zero variance). That is why the brief's stress measure is defined relative to the no-hurricane path.

## Table 2. Repayment schedules: 5-yr equal [baseline] vs B'-lump vs B'-inst

| country | design | version | schedule | P no clause | P clause | difference | 95% CI | significant (CI excludes 0)? | mean peak GFN, strike yr+next (no clause / clause) | mean peak GFN, strike yr+5 (no clause / clause) |
|---|---|---|---|---|---|---|---|---|---|---|
| Grenada-like | Grenada-style (s=0.10, K=1) | V1 | 5-yr equal [baseline] | 23.1% | 22.7% | -0.5 pp | [-0.7, -0.3] pp | yes | 9.0 / 8.9 | 9.5 / 9.4 |
| Grenada-like | Grenada-style (s=0.10, K=1) | V1 | B'-lump | 23.1% | 22.1% | -1.1 pp | [-1.3, -0.8] pp | yes | 9.0 / 8.8 | 9.5 / 9.3 |
| Grenada-like | Grenada-style (s=0.10, K=1) | V1 | B'-inst | 23.1% | 22.5% | -0.7 pp | [-0.9, -0.5] pp | yes | 9.0 / 8.9 | 9.5 / 9.4 |
| Grenada-like | Grenada-style (s=0.10, K=1) | V2 | 5-yr equal [baseline] | 23.0% | 22.5% | -0.4 pp | [-0.7, -0.2] pp | yes | 9.1 / 9.0 | 9.7 / 9.6 |
| Grenada-like | Grenada-style (s=0.10, K=1) | V2 | B'-lump | 23.0% | 21.9% | -1.1 pp | [-1.3, -0.8] pp | yes | 9.1 / 8.9 | 9.7 / 9.5 |
| Grenada-like | Grenada-style (s=0.10, K=1) | V2 | B'-inst | 23.0% | 22.4% | -0.6 pp | [-0.8, -0.4] pp | yes | 9.1 / 9.0 | 9.7 / 9.6 |
| Grenada-like | High-coverage (s=0.80, K=2) | V1 | 5-yr equal [baseline] | 23.1% | 24.7% | +1.6 pp | [+1.1, +2.0] pp | yes | 9.0 / 4.5 | 9.5 / 9.8 |
| Grenada-like | High-coverage (s=0.80, K=2) | V1 | B'-lump | 23.1% | 52.3% | +29.2 pp | [+28.3, +30.1] pp | yes | 9.0 / 4.5 | 9.5 / 8.4 |
| Grenada-like | High-coverage (s=0.80, K=2) | V1 | B'-inst | 23.1% | 24.7% | +1.6 pp | [+1.1, +2.0] pp | yes | 9.0 / 4.5 | 9.5 / 9.8 |
| Grenada-like | High-coverage (s=0.80, K=2) | V2 | 5-yr equal [baseline] | 23.0% | 24.5% | +1.5 pp | [+1.1, +2.0] pp | yes | 9.1 / 4.5 | 9.7 / 9.9 |
| Grenada-like | High-coverage (s=0.80, K=2) | V2 | B'-lump | 23.0% | 53.4% | +30.4 pp | [+29.5, +31.4] pp | yes | 9.1 / 4.5 | 9.7 / 8.5 |
| Grenada-like | High-coverage (s=0.80, K=2) | V2 | B'-inst | 23.0% | 24.5% | +1.5 pp | [+1.1, +2.0] pp | yes | 9.1 / 4.5 | 9.7 / 9.9 |
| High-debt | Grenada-style (s=0.10, K=1) | V1 | 5-yr equal [baseline] | 30.3% | 30.5% | +0.2 pp | [-0.1, +0.5] pp | no | 27.0 / 27.0 | 27.4 / 27.4 |
| High-debt | Grenada-style (s=0.10, K=1) | V1 | B'-lump | 30.3% | 28.8% | -1.5 pp | [-1.8, -1.3] pp | yes | 27.0 / 26.7 | 27.4 / 27.1 |
| High-debt | Grenada-style (s=0.10, K=1) | V1 | B'-inst | 30.3% | 30.2% | -0.1 pp | [-0.4, +0.1] pp | no | 27.0 / 27.0 | 27.4 / 27.4 |
| High-debt | Grenada-style (s=0.10, K=1) | V2 | 5-yr equal [baseline] | 61.9% | 60.7% | -1.2 pp | [-1.4, -0.9] pp | yes | 89.3 / 89.2 | 98.5 / 98.4 |
| High-debt | Grenada-style (s=0.10, K=1) | V2 | B'-lump | 61.9% | 61.4% | -0.5 pp | [-0.9, -0.1] pp | yes | 89.3 / 88.6 | 98.5 / 97.8 |
| High-debt | Grenada-style (s=0.10, K=1) | V2 | B'-inst | 61.9% | 60.5% | -1.4 pp | [-1.7, -1.1] pp | yes | 89.3 / 89.1 | 98.5 / 98.3 |
| High-debt | High-coverage (s=0.80, K=2) | V1 | 5-yr equal [baseline] | 30.3% | 45.6% | +15.2 pp | [+14.5, +16.0] pp | yes | 27.0 / 9.6 | 27.4 / 29.5 |
| High-debt | High-coverage (s=0.80, K=2) | V1 | B'-lump | 30.3% | 62.0% | +31.6 pp | [+30.6, +32.6] pp | yes | 27.0 / 9.6 | 27.4 / 25.3 |
| High-debt | High-coverage (s=0.80, K=2) | V1 | B'-inst | 30.3% | 45.6% | +15.2 pp | [+14.5, +16.0] pp | yes | 27.0 / 9.6 | 27.4 / 29.5 |
| High-debt | High-coverage (s=0.80, K=2) | V2 | 5-yr equal [baseline] | 61.9% | 63.1% | +1.2 pp | [+0.5, +2.0] pp | yes | 89.3 / 24.9 | 98.5 / 100.7 |
| High-debt | High-coverage (s=0.80, K=2) | V2 | B'-lump | 61.9% | 63.1% | +1.1 pp | [+0.5, +1.8] pp | yes | 89.3 / 24.8 | 98.5 / 91.5 |
| High-debt | High-coverage (s=0.80, K=2) | V2 | B'-inst | 61.9% | 63.1% | +1.2 pp | [+0.5, +2.0] pp | yes | 89.3 / 24.9 | 98.5 / 100.7 |

Reading notes. (1) For the High-coverage design (K = 2) B'-inst coincides with the 5-yr baseline: the suspension covers years t and t+1, so instalments run t+2..t+6 = 5 equal instalments. The two differ only for the Grenada-style design (K = 1: 6 instalments vs 5). (2) The Grenada-like results use Grenada's actual 6-year horizon; the High-coverage clause is a net stress-raiser under B'-lump because the whole deferred balance falls due in one year (see Table 3b for the horizon at which this reverses). Figure: figures/figure1_v3.png (copy of outputs/figures/figure1_v3.png).

## Table 3. Break-evens for the High-coverage clause (s = 0.80, K = 2)

| country | version | equal-instalment break-even (years of repayment; existing method, linear interpolation) | lump-sum break-even: smallest L (years after strike) with clause effect < 0 | smallest L with CI entirely below 0 | stays < 0 for all larger L? |
|---|---|---|---|---|---|
| Grenada-like | V1 | 5.9 | 15 | 15 | yes |
| Grenada-like | V2 | 5.9 | 15 | 15 | yes |
| High-debt | V1 | 9.3 | none in 1..15 | none in 1..15 | n/a |
| High-debt | V2 | 5.6 | 7 | 8 | yes |

The equal-instalment values 5.9 (Grenada-like V1), 9.3 (High-debt V1) and 5.6 (High-debt V2) are the existing ones, reproduced; Grenada-like V2 (5.9) is added (it was in outputs/tables/exp3_repay_switch_points.csv but not in the figure). The two columns are not on the same clock: the equal-instalment period counts years of repayment after the suspension ends; the lump-sum horizon L counts years from the strike (the lump is paid in strike year + L; for K = 2 the suspension covers the first two of them).

### Table 3b. Lump-sum horizon sweep: clause effect on P(stress), High-coverage clause (difference in pp; negative = clause lowers P(stress); * = CI excludes 0)

| L | Grenada-like V1 | Grenada-like V2 | High-debt V1 | High-debt V2 |
|---|---|---|---|---|
| 1 | +44.9* | +45.1* | +37.7* | +7.1* |
| 2 | +44.9* | +45.1* | +37.7* | +7.1* |
| 3 | +37.9* | +39.0* | +36.5* | +5.9* |
| 4 | +35.1* | +36.3* | +35.1* | +4.5* |
| 5 | +32.1* | +33.4* | +33.4* | +2.8* |
| 6 | +29.2* | +30.4* | +31.6* | +1.1* |
| 7 | +25.7* | +27.1* | +29.9* | -0.4 |
| 8 | +22.0* | +23.3* | +27.8* | -2.1* |
| 9 | +18.4* | +19.6* | +25.9* | -3.6* |
| 10 | +14.5* | +15.6* | +23.6* | -5.2* |
| 11 | +9.2* | +9.6* | +21.1* | -6.8* |
| 12 | +4.7* | +4.8* | +18.7* | -8.3* |
| 13 | +1.8* | +2.0* | +16.0* | -9.9* |
| 14 | +0.3 | +0.4 | +13.4* | -11.4* |
| 15 | -1.1* | -1.0* | +10.9* | -12.7* |

L = 1 and L = 2 give identical results: with K = 2 the clause is active in the strike year and the next, so a lump due in year t+1 is first payable in t+2, the same as L = 2.

## Table 4. Timing-dependent stress measure (3 pp in the strike year and the year after, 5 pp in all other years)

| country | design | version | schedule | P no clause | P clause | difference | 95% CI | significant (CI excludes 0)? |
|---|---|---|---|---|---|---|---|---|
| Grenada-like | Grenada-style (s=0.10, K=1) | V1 | 5-yr equal [baseline] | 38.5% | 37.9% | -0.6 pp | [-0.8, -0.3] pp | yes |
| Grenada-like | Grenada-style (s=0.10, K=1) | V1 | B'-lump | 38.5% | 37.1% | -1.3 pp | [-1.6, -1.1] pp | yes |
| Grenada-like | Grenada-style (s=0.10, K=1) | V2 | 5-yr equal [baseline] | 38.5% | 37.8% | -0.7 pp | [-1.0, -0.5] pp | yes |
| Grenada-like | Grenada-style (s=0.10, K=1) | V2 | B'-lump | 38.5% | 37.1% | -1.4 pp | [-1.6, -1.2] pp | yes |
| Grenada-like | High-coverage (s=0.80, K=2) | V1 | 5-yr equal [baseline] | 38.5% | 25.7% | -12.8 pp | [-13.5, -12.2] pp | yes |
| Grenada-like | High-coverage (s=0.80, K=2) | V1 | B'-lump | 38.5% | 52.6% | +14.1 pp | [+13.2, +14.9] pp | yes |
| Grenada-like | High-coverage (s=0.80, K=2) | V2 | 5-yr equal [baseline] | 38.5% | 25.4% | -13.1 pp | [-13.7, -12.4] pp | yes |
| Grenada-like | High-coverage (s=0.80, K=2) | V2 | B'-lump | 38.5% | 53.6% | +15.1 pp | [+14.3, +16.0] pp | yes |
| High-debt | Grenada-style (s=0.10, K=1) | V1 | 5-yr equal [baseline] | 44.1% | 44.4% | +0.3 pp | [-0.0, +0.6] pp | no |
| High-debt | Grenada-style (s=0.10, K=1) | V1 | B'-lump | 44.1% | 41.8% | -2.3 pp | [-2.6, -2.0] pp | yes |
| High-debt | Grenada-style (s=0.10, K=1) | V2 | 5-yr equal [baseline] | 65.2% | 63.6% | -1.6 pp | [-1.8, -1.3] pp | yes |
| High-debt | Grenada-style (s=0.10, K=1) | V2 | B'-lump | 65.2% | 62.8% | -2.4 pp | [-2.8, -2.0] pp | yes |
| High-debt | High-coverage (s=0.80, K=2) | V1 | 5-yr equal [baseline] | 44.1% | 45.6% | +1.4 pp | [+0.9, +1.9] pp | yes |
| High-debt | High-coverage (s=0.80, K=2) | V1 | B'-lump | 44.1% | 62.0% | +17.8 pp | [+16.9, +18.8] pp | yes |
| High-debt | High-coverage (s=0.80, K=2) | V2 | 5-yr equal [baseline] | 65.2% | 63.1% | -2.0 pp | [-2.7, -1.3] pp | yes |
| High-debt | High-coverage (s=0.80, K=2) | V2 | B'-lump | 65.2% | 63.1% | -2.1 pp | [-2.8, -1.4] pp | yes |

### Does the sign of the high-coverage effect change versus the baseline (5 pp everywhere) measure?

| country | version | schedule | baseline measure | 3-pp window measure | sign changes? |
|---|---|---|---|---|---|
| Grenada-like | V1 | 5-yr equal [baseline] | +1.6 pp* | -12.8 pp* | yes |
| Grenada-like | V1 | B'-lump | +29.2 pp* | +14.1 pp* | no |
| Grenada-like | V2 | 5-yr equal [baseline] | +1.5 pp* | -13.1 pp* | yes |
| Grenada-like | V2 | B'-lump | +30.4 pp* | +15.1 pp* | no |
| High-debt | V1 | 5-yr equal [baseline] | +15.2 pp* | +1.4 pp* | no |
| High-debt | V1 | B'-lump | +31.6 pp* | +17.8 pp* | no |
| High-debt | V2 | 5-yr equal [baseline] | +1.2 pp* | -2.0 pp* | yes |
| High-debt | V2 | B'-lump | +1.1 pp* | -2.1 pp* | yes |

(* = CI excludes 0.)

**The sign changes** for: Grenada-like V1 5-yr equal [baseline]; Grenada-like V2 5-yr equal [baseline]; High-debt V2 5-yr equal [baseline]; High-debt V2 B'-lump.

Change in the effect (3-pp measure minus baseline measure, pp): Grenada-like V1 5-yr equal [baseline] -14.4; Grenada-like V1 B'-lump -15.1; Grenada-like V2 5-yr equal [baseline] -14.6; Grenada-like V2 B'-lump -15.3; High-debt V1 5-yr equal [baseline] -13.8; High-debt V1 B'-lump -13.8; High-debt V2 5-yr equal [baseline] -3.2; High-debt V2 B'-lump -3.2.

## Table 5. Continuous measure: expected excess GFN = mean over paths of sum_t max(0, GFN_t - no-storm GFN_t - 5), pp of GDP (summed over 30 years)

| country | design | version | no clause | clause (5-yr) | clause (B'-lump) | difference, 5-yr (95% CI) | difference, B'-lump (95% CI) |
|---|---|---|---|---|---|---|---|
| Grenada-like | Grenada-style (s=0.10, K=1) | V1 | 2.6 | 2.5 | 2.5 | -0.1 [-0.1, -0.1] | -0.1 [-0.2, -0.1] |
| Grenada-like | Grenada-style (s=0.10, K=1) | V2 | 3.1 | 2.9 | 2.9 | -0.1 [-0.1, -0.1] | -0.2 [-0.2, -0.1] |
| Grenada-like | High-coverage (s=0.80, K=2) | V1 | 2.6 | 1.7 | 2.7 | -0.9 [-0.9, -0.8] | +0.1 [+0.0, +0.1] |
| Grenada-like | High-coverage (s=0.80, K=2) | V2 | 3.1 | 2.1 | 3.1 | -1.0 [-1.0, -0.9] | +0.0 [-0.0, +0.1] |
| High-debt | Grenada-style (s=0.10, K=1) | V1 | 8.2 | 7.8 | 7.6 | -0.5 [-0.5, -0.4] | -0.7 [-0.7, -0.6] |
| High-debt | Grenada-style (s=0.10, K=1) | V2 | 97.8 | 92.5 | 91.0 | -5.3 [-5.5, -5.2] | -6.8 [-7.0, -6.6] |
| High-debt | High-coverage (s=0.80, K=2) | V1 | 8.2 | 9.2 | 13.9 | +1.0 [+0.9, +1.2] | +5.7 [+5.5, +5.9] |
| High-debt | High-coverage (s=0.80, K=2) | V2 | 97.8 | 76.4 | 69.2 | -21.4 [-22.5, -20.2] | -28.6 [-30.0, -27.2] |

Differences are clause minus no clause, with a paired 95% CI on the per-path excess; negative = the clause lowers expected excess GFN.

## Table 6. K-vs-R grid (Grenada-like): difference in P(stress), clause minus no clause, in pp (negative = clause lowers P(stress))

| design | version | R | K=1 | K=2 | K=3 | K=4 |
|---|---|---|---|---|---|---|
| High-coverage (s=0.80, K=2) | V1 | 2 | +0.4 | -19.6 | -19.4 | -19.2 |
| High-coverage (s=0.80, K=2) | V1 | 3 | +1.2 | +1.6 | -15.7 | -14.8 |
| High-coverage (s=0.80, K=2) | V1 | 4 | +1.7 | +3.0 | +2.9 | -11.0 |
| High-coverage (s=0.80, K=2) | V2 | 2 | +0.3 | -19.8 | -19.7 | -19.4 |
| High-coverage (s=0.80, K=2) | V2 | 3 | +1.2 | +1.5 | -15.6 | -14.8 |
| High-coverage (s=0.80, K=2) | V2 | 4 | +1.7 | +2.9 | +2.8 | -10.8 |
| Grenada-style (s=0.10, K=1) | V1 | 2 | -0.6 | -3.6 | -3.7 | -3.7 |
| Grenada-style (s=0.10, K=1) | V1 | 3 | -0.5 | -0.9 | -3.5 | -3.5 |
| Grenada-style (s=0.10, K=1) | V1 | 4 | -0.4 | -0.4 | -0.9 | -3.3 |
| Grenada-style (s=0.10, K=1) | V2 | 2 | -0.7 | -3.8 | -3.8 | -3.8 |
| Grenada-style (s=0.10, K=1) | V2 | 3 | -0.4 | -0.8 | -3.5 | -3.4 |
| Grenada-style (s=0.10, K=1) | V2 | 4 | -0.4 | -0.4 | -1.1 | -3.4 |

R = years over which reconstruction spending is spread; K = years of service deferred per trigger; each cell uses the design's own share s and 5-yr equal-instalment repayment (s = 0.10 Grenada-style, s = 0.80 High-coverage), the existing grid restricted to K = 1..4. Only the point estimate is tabulated here (the existing grid carries no CI).

## Robustness: seeds 43 and 44 (High-coverage, Grenada-like; Tables 2 and 4)

| largest difference vs seed 42 | 43 | 44 |
|---|---|---|
| max |diff| P(stress) no clause | 0.7 pp (V2, 5-yr equal [baseline]) | 0.6 pp (V2, 5-yr equal [baseline]) |
| max |diff| P(stress) clause | 0.6 pp (V2, 5-yr equal [baseline]) | 0.7 pp (V1, B'-lump) |
| max |diff| difference (Table 2) | 0.4 pp (V1, B'-lump) | 0.6 pp (V2, 5-yr equal [baseline]) |
| max |diff| difference, 3-pp measure (Table 4) | 0.5 pp (V1, B'-lump) | 0.5 pp (V1, 5-yr equal [baseline]) |
| max |diff| mean peak GFN t..t+1 no clause | 0.0 pp of GDP (V2, 5-yr equal [baseline]) | 0.0 pp of GDP (V2, 5-yr equal [baseline]) |
| max |diff| mean peak GFN t..t+1 clause | 0.0 pp of GDP (V1, 5-yr equal [baseline]) | 0.0 pp of GDP (V1, B'-lump) |
| max |diff| mean peak GFN t..t+5 no clause | 0.1 pp of GDP (V1, 5-yr equal [baseline]) | 0.0 pp of GDP (V2, 5-yr equal [baseline]) |
| max |diff| mean peak GFN t..t+5 clause | 0.0 pp of GDP (V1, 5-yr equal [baseline]) | 0.0 pp of GDP (V2, 5-yr equal [baseline]) |

**No sign changes:** the sign of the clause effect (both measures, all 6 version x schedule cells) is identical in seeds 42, 43 and 44.

No cell changes between significant and not significant.

### Seed-by-seed values (P(stress) and its paired effect, both measures)

| seed | version | schedule | P no clause | P clause | difference (95% CI) | 3-pp: P no clause | 3-pp: P clause | 3-pp: difference (95% CI) |
|---|---|---|---|---|---|---|---|---|
| 42 | V1 | 5-yr equal [baseline] | 23.1% | 24.7% | +1.6 pp [+1.1, +2.0] pp | 38.5% | 25.7% | -12.8 pp [-13.5, -12.2] pp |
| 43 | V1 | 5-yr equal [baseline] | 23.8% | 25.3% | +1.5 pp [+1.1, +2.0] pp | 39.3% | 26.1% | -13.2 pp [-13.9, -12.6] pp |
| 44 | V1 | 5-yr equal [baseline] | 23.7% | 24.7% | +1.0 pp [+0.5, +1.4] pp | 39.1% | 25.8% | -13.4 pp [-14.0, -12.7] pp |
| 42 | V1 | B'-lump | 23.1% | 52.3% | +29.2 pp [+28.3, +30.1] pp | 38.5% | 52.6% | +14.1 pp [+13.2, +14.9] pp |
| 43 | V1 | B'-lump | 23.8% | 52.6% | +28.8 pp [+27.9, +29.7] pp | 39.3% | 52.9% | +13.6 pp [+12.7, +14.4] pp |
| 44 | V1 | B'-lump | 23.7% | 53.0% | +29.3 pp [+28.4, +30.3] pp | 39.1% | 53.4% | +14.3 pp [+13.4, +15.1] pp |
| 42 | V1 | B'-inst | 23.1% | 24.7% | +1.6 pp [+1.1, +2.0] pp | 38.5% | 25.7% | -12.8 pp [-13.5, -12.2] pp |
| 43 | V1 | B'-inst | 23.8% | 25.3% | +1.5 pp [+1.1, +2.0] pp | 39.3% | 26.1% | -13.2 pp [-13.9, -12.6] pp |
| 44 | V1 | B'-inst | 23.7% | 24.7% | +1.0 pp [+0.5, +1.4] pp | 39.1% | 25.8% | -13.4 pp [-14.0, -12.7] pp |
| 42 | V2 | 5-yr equal [baseline] | 23.0% | 24.5% | +1.5 pp [+1.1, +2.0] pp | 38.5% | 25.4% | -13.1 pp [-13.7, -12.4] pp |
| 43 | V2 | 5-yr equal [baseline] | 23.7% | 25.1% | +1.5 pp [+1.0, +1.9] pp | 39.3% | 26.0% | -13.4 pp [-14.0, -12.7] pp |
| 44 | V2 | 5-yr equal [baseline] | 23.6% | 24.6% | +0.9 pp [+0.5, +1.4] pp | 39.1% | 25.6% | -13.5 pp [-14.2, -12.8] pp |
| 42 | V2 | B'-lump | 23.0% | 53.4% | +30.4 pp [+29.5, +31.4] pp | 38.5% | 53.6% | +15.1 pp [+14.3, +16.0] pp |
| 43 | V2 | B'-lump | 23.7% | 53.7% | +30.1 pp [+29.1, +31.0] pp | 39.3% | 54.0% | +14.7 pp [+13.8, +15.6] pp |
| 44 | V2 | B'-lump | 23.6% | 54.1% | +30.4 pp [+29.5, +31.4] pp | 39.1% | 54.3% | +15.3 pp [+14.4, +16.2] pp |
| 42 | V2 | B'-inst | 23.0% | 24.5% | +1.5 pp [+1.1, +2.0] pp | 38.5% | 25.4% | -13.1 pp [-13.7, -12.4] pp |
| 43 | V2 | B'-inst | 23.7% | 25.1% | +1.5 pp [+1.0, +1.9] pp | 39.3% | 26.0% | -13.4 pp [-14.0, -12.7] pp |
| 44 | V2 | B'-inst | 23.6% | 24.6% | +0.9 pp [+0.5, +1.4] pp | 39.1% | 25.6% | -13.5 pp [-14.2, -12.8] pp |

## (a) Parameter entries by status

| status | before (baseline) | added in v3 | now |
|---|---|---|---|
| sourced | 15 | 0 | 15 |
| calibrated | 15 | 1 | 16 |
| assumed | 22 | 1 | 23 |
| **total** | 52 | 2 | 54 |

Counting rule: every entry with a status in config/calibration.yaml (global), scenarios.yaml and designs.yaml, as in `config.status_counts()` (the baseline 52 = 15 + 15 + 22), plus config/v3.yaml. The two new entries are: `storm_window_margin` = 3 pp, the timing-dependent stress threshold (**assumed**: our own choice), and `bprime_horizon` = 6 years, the strike-to-due-date horizon of regime B' (**calibrated**: 2030 bond maturity minus 2024 strike, from sourced dates; status is my classification and can be changed to assumed). None is VERIFIED (reserved for the group).

## (b) Draft rows for the brief's AI decision log

| Tool and task | What the AI produced | How we verified it | Effect on our decisions |
|---|---|---|---|
| Claude Code: review of Regime B principal accounting after a suspected double count (2026-11-11) | Confirmed that deferred principal was paid twice (liability outside the stock); rewrote regime B so the deferred balance is a tranche inside the covered stock | Re-derived the amortization split by hand; replaced the old 'equal discounted GFN' test with five explicit accounting checks; compared old and new CSVs | Fix accepted (DECISIONS #3); under V1 the clause stock now equals the no-clause stock, which makes the clause a liquidity-only instrument |
| Claude Code: entered the sourced calibration, scenario overrides and the repay_rule option (2026-11-12) | Rewrote the three YAML files with source, page and status for each value; fitted the lognormal damage law (docs/fit.py) | docs/fit.py reproduces the World Bank AAL and 250-year-PML targets through the model's own damage generator; new tests on instalment clearing and override plumbing | Group confirmed mu_D = ln(median), nominal r and g, scenario-level overrides (DECISIONS #40-#44); every non-sourced value labelled ASSUMPTION |
| Claude Code: HURDAT2 check of the hurricane frequency lambda for Grenada (2026-11-12) | docs/hurdat_check.py and a report: lambda ranges 0.044-0.067 depending on radius; Emily 2005 was not Cat 3+ at Grenada | Cross-checked Ivan, Emily and Beryl closest approaches and the Allen 1980 100-nm hit by listing track points by hand | lambda = 0.051 kept, with the HURDAT2 bracket in its YAML note (DECISIONS #47, #49); report-only, no re-calibration |
| Claude Code: Fiscal Resilience Act surplus rule (2026-11-12) | economy.primary_deficit option: a baseline primary surplus applies only while lagged debt exceeds 60% of GDP; three tests | Independent closed-form iteration in the no-hurricane test; checked which parameters the +-25% sweep really covers before labelling them | Rule on by default and b_star SOURCED (DECISIONS #50); the forgiveness-accounting test switches it off |
| Claude Code: revised-brief runs (2026-11-22): paired CIs, Grenada's actual repayment (B'-lump, B'-inst), timing-dependent and continuous stress measures, seeds 43/44 | New regime rules, src/v3.py, run_v3.py, 29 new tests, RESULTS_v3.md and Figure 1 (v3); no existing parameter or result changed | New code reproduces the saved baseline tables to 1e-9 (P(stress), peaks, break-evens, K-vs-R grid); tests that B' repays the full deferred balance and that the V1 debt stock equals the no-clause path; seed 43/44 reruns | Both repayment readings reported side by side instead of choosing one (DECISIONS #52-#56); measure renamed 'financing-stress episode'; two new parameter entries added |

