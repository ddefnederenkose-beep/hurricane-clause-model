# Modelling decisions (running log)

| # | Decision | Why |
|---|---|---|
| 1 | Overlapping qualifying hit during a deferral restarts the K-year window; already-deferred amounts stay deferred (no catch-up payments while a window is active). | Group answer Q1. |
| 2 | Interest paid_t = r_t b_{t-1}/(1+g_t); amortization_t = b_{t-1}/(M(1+g_t)); negative stocks pay nothing. | Consistent with the debt equation (Q2). |
| 3 | **REVISED.** Version 1: Regime B debt stock = Regime A by construction (skipped interest is capitalized, and the stock already accrues interest). Skipped amortization becomes `defbal`, a tranche INSIDE the covered stock. After the window: amortization = (b^c - defbal)/M + defbal/m_rep (m_rep = `defer_repay_years`, default M); defbal is reduced by its own repayments; coupons are paid on the whole stock. Principal is paid once. | Group answer Q3 + review. The first version repaid a separate 'catch-up' account on top of b/M on the full stock, i.e. deferred principal was paid twice and the account was a liability outside the stock; it also inflated B's P(crisis) (12.3% vs A's 8.5%). That was an accounting artifact. |
| 4 | Regime C forgives interest AND amortization due in the window; forgiven interest is never added to the stock, forgiven principal is deducted. Terminal gap C vs B = forgiven amounts compounded at (1+r)/(1+g). | Pure solvency benchmark (Q4). |
| 5 | Primary deficit allocated to covered/other stocks in proportion to lagged stock size (share clipped to [0,1]; falls back to s if b<=1). | Q5. |
| 6 | Version 2: r_eff_t = (1-1/M) r_eff_{t-1} + (r_safe + x_t)/M; r_eff_0 = r_safe + x_0 with x_0 from b_0 and GFN_0 = pd_bar + (r_safe + 1/M) b_0. | Q6 (GFN_0 uses r_safe to avoid circularity). |
| 7 | Units: D, b, pd, GFN in % of GDP as plain numbers; rates/growth as decimals; `check_units` guards the common mix-ups. | Q7. |
| 8 | mu_D = ln 10, sigma_D = 1.0 are placeholders (95th pct damage ~52% of GDP), to be refit to EM-DAT. | Q8. |
| 9 | No floor on debt; run_all prints the share of paths with negative debt. | Q9. |
| 10 | Event windows: average around every hit with a complete t-2..t+5 window (clean-window variant to be added with the figures). | Q10. |
| 11 | Common random numbers: draws (u, z) are generated once from the seed; hit if u < lambda, damage = exp(mu+sigma z). Same draws for all regimes, versions and grid cells; raising lambda only adds hits. | Added requirement. |
| 12 | `simulate(..., forced_hits={year: damage})` replaces the random process with deterministic hits (tests, video). | Added requirement. |
| 13 | "Peak GFN after a hurricane" = max GFN over the hit year and the next year (window=2 starting at t), pooled over events with D >= D_trig. Configurable in `metrics.summarize(window=...)`. | Spec ambiguous ("2 years after"); chosen so the window covers the K=2 deferral. |
| 14 | P(b_t > 100 at any point) is evaluated for t = 1..T (not t=0). | Avoid trivially 1 for high_debt because of b_0 = 110. |
| 15 | NEW parameter x_max = 0.10 caps the risk premium (Version 2). Not in the spec. Without it, r-g grows linearly with b and high-debt paths overflow numerically (median b_T ~ 1e31). | Numerical/economic backstop; PLACEHOLDER_VERIFY. |
| 16 | With m_rep = M, B's GFN equals A's in every non-suspended year, so in Version 1 the clause weakly dominates A in GFN. Strict equality of discounted GFN between A and B is NOT a property of this model: the stock is identical, so the skipped service is never repaid in gross terms (the creditor's net position is unchanged because A re-borrows what it pays). Test 2 checks instead: identical stocks, no double counting (explicit amortization decomposition), B = A outside the window, and PV(A service) - PV(B service) = PV(suspended service). A faster repayment (m_rep < M) creates a post-window hump. | Review item 1. |
| 17 | Second crisis metric: hurricane-attributable crisis = GFN_t > no-hurricane (lambda=0) GFN path + GFN_margin (5 pp, placeholder). Reported next to the absolute GFN_crit flag. | Review item 2: in high_debt, GFN_t > 15 in every year by construction. |
| 18 | Peak GFN is reported over t..t+1 (clause window) and t..t+5 (covers repayment hump). | Review item 3. |
| 19 | Version 2 output reports share of path-years and share of paths where the premium cap x_max binds. Explosive high-debt paths are a finding (debt spiral), not hidden. | Review item 4. |
