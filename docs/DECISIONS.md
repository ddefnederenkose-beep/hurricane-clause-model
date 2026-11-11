# Modelling decisions (running log)

| # | Decision | Why |
|---|---|---|
| 1 | Overlapping qualifying hit during a deferral restarts the K-year window; already-deferred amounts stay deferred (no catch-up payments while a window is active). | Group answer Q1. |
| 2 | Interest paid_t = r_t b_{t-1}/(1+g_t); amortization_t = b_{t-1}/(M(1+g_t)); negative stocks pay nothing. | Consistent with the debt equation (Q2). |
| 3 | Version 1: Regime B debt stock = Regime A by construction; the clause only moves GFN. Deferred service sits in an account Q that accrues at the contractual rate and is repaid at 1/M of its balance per year when no window is active. Test 2 therefore discounts cash-flow streams (interest+amortization+catch-up) at r and values the terminal Q. | A pure deferral is liquidity, not solvency, relief (Q3). The 1/M-declining catch-up is the builder's reading of "spread over remaining maturity"; it has a long geometric tail. |
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
