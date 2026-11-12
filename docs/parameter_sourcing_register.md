# Hurricane-clause model: parameter sourcing register (tasks 2–6)
Compiled 12 Nov 2026. Status key: **FACT** = number read directly from the source; **JUDGMENT** = our calculation or choice based on sourced numbers; **OPEN** = not settled, a group member must check.
Assignment rule (guidelines §6): every source below must also be opened by a group member before it is cited.

## Task 2 – Damage distribution (μ_D, σ_D)

| Param | Proposed value | Source | Page / table | Status | Note for YAML |
|---|---|---|---|---|---|
| μ_D (median damage, % GDP) | **11.2** (if λ = 0.051) / 2.75 (if λ = 0.10) | Fitted to World Bank, *Country Disaster Risk Profile: Grenada* (2016): AAL 0.9% GDP; 250-yr PML 43.6% GDP; GDP US$912m | 1-page profile, hurricane panel | JUDGMENT (fit) | Lognormal fit with cap 200%, matching AAL = λ·E[D] and P(annual loss > 43.6%) = 1/250. Code: calib/fit.py. The profile covers modelled *building* losses, so it understates total damage. |
| σ_D (log-sd) | **0.96** (λ = 0.051) / 1.58 (λ = 0.10) | Same fit | – | JUDGMENT (fit) | Check that the code uses σ on the log scale. |
| Cross-check | median 8.1, σ 0.98 | IMF (2016) *Small States' Resilience to Natural Disasters and Climate Change*, EM-DAT 1950–2014: average disaster ≈ 13% GDP; ≈ 9% of disasters ≥ 30% GDP | Table 1 / Fig. 1 (values read from text) | FACT inputs, JUDGMENT fit | Covers all small states and all disaster types, not just Caribbean hurricanes. Agrees with the λ = 0.051 fit. |
| Validation point | Ivan 2004 ≈ 200% GDP (US$900m / EC$2.4bn) | Asonuma et al. (2017) IMF WP/17/171, Sec. III.A and Box 2; OECS/ECLAC assessment | p. ~10, Box 2 pp. 25–26 | FACT | Acevedo (2016) Table 2 p. 8 gives 148.4% (2010 constant US$). Quote the source you use. |
| Validation point | Beryl 2024 = 16.5% GDP (US$218m); PDNA 17% (US$220m) | IMF CR 25/39 (2024 Art. IV) ¶8 p. 7–8; IMF CR 26/9 (2025 Art. IV) Box 1 p. 7 | as stated | FACT | Beryl sits near the 60th percentile of the λ = 0.051 fit. |
| Modern Ivan | 25% GDP (US$230m) | World Bank risk profile 2016 | same page | FACT | Same storm, modelled on today's building stock and GDP. Explains why 200% is an extreme tail value. |

## Task 4 – Frequency (λ)

| Param | Proposed value | Source | Page / table | Status | Note |
|---|---|---|---|---|---|
| λ baseline | **0.051** | Mallucci (2020/2022), IFDP 1291r1: annual frequency of Cat ≥ 3 hurricane hits since 1980 (NOAA) | Table 1 Panel B p. 9; definition fn. 14 p. 8; hit list Table 7 p. 27 | FACT | 0.051 = 2/39 (Grenada hits 2004, 2005). OPEN: Emily 2005 was Cat 1 at Grenada (ReliefWeb, OCHA), so check it in HURDAT2. |
| λ updated | 0.067 | Mallucci's rule extended to 1980–2024, adding Beryl (Cat 4, Carriacou) | – | JUDGMENT | 3/45. Needs a HURDAT2 check. |
| λ sensitivity | **0.10** | Guerson (2020) IMF **WP/20/266** (not "WP 2021/230"): "storm probability threshold" Grenada 0.10 | Appendix 1 p. 25; Fig. 1 p. 23 | FACT (but different definition) | Guerson's 0.10 is a probability for a fiscally relevant natural disaster, not a hurricane-hit frequency. |
| Consistency rule | – | – | – | JUDGMENT | λ and μ_D must describe the same set of events. Use the pairs (0.051, 11.2, 0.96) or (0.10, 2.75, 1.58). Both match the same annual average loss. |

## Task 3 – Reconstruction (κ, R)

| Param | Proposed value | Source | Page / table | Status | Note |
|---|---|---|---|---|---|
| κ (gross) | **0.62** | IMF CR 25/39: reconstruction public capex 10.2% GDP over 2024–26 (support total 13.5%); staff estimate ≈ 10% GDP; damage 16.5% | p. 9 table; ¶17 pp. 12–13; ¶8 p. 7 | JUDGMENT (10.2 / 16.5) | |
| κ (net of insurance) | 0.42 | Same, minus CCRIF payout to central government US$44m = 3.2% GDP | p. 7 | JUDGMENT ((10.2 − 3.2) / 16.5) | Use this if the model has no separate insurance channel. |
| R | **3 years** | IMF CR 25/39 (2024–26 window); IMF CR 26/9 Box 1 p. 7: spending of ≈ 4.5% GDP by Jul 2025, ≈ 6% by end-2025, continuing into 2026 | as stated | FACT (window) / JUDGMENT (R = 3) | Realised spending is running below the 10.2% plan, so κ may be lower. |
| Ivan κ, R | not sourced | GFDRR/World Bank (2005) *Grenada: A Nation Rebuilding* | – | OPEN | Not opened. Needed for the Ivan validation. |

## Task 5 – Contract terms (K, s, repayment)

| Param | Grenada 2015 | Barbados 2018/19 | Source | Status |
|---|---|---|---|---|
| Trigger | CCRIF modelled loss > US$15m (1 payment date) / > US$30m (2 dates) | CCRIF payout > US$5m (2nd iteration: US$7.5m for hurricanes) | Asonuma et al. App. II p. 51 & Box 2; Ho & Fontana (2021) pp. 7–8 | FACT |
| **K** | **0.5 yr or 1 yr**; Beryl used 1 yr (Nov 2024 + May 2025) | **2 yrs** | Ho & Fontana pp. 7–8; IMF CR 25/39 p. 5 ¶7 | FACT |
| ICMA model | 3 yrs, maturity extended by 3 yrs, no cap on triggers | – | Ho & Fontana p. 9 | FACT |
| Capitalisation | deferred interest capitalised | same | Asonuma Box 2; Ho & Fontana p. 8 | FACT |
| **Repayment** | equal semi-annual instalments **over the remaining term to May 2030** (≈ 5 yrs after Beryl) | remaining amortisations increased pro rata (over remaining life) | Asonuma App. II p. 51; Ho & Fontana p. 8 | FACT |
| Conflict | IMF CR 25/39 and 26/9 say deferred amounts are "added to the lump-sum principal due at maturity in 2030" | – | CR 26/9 Box 1 fn. 1 p. 7 | OPEN: check the bond terms or the MoF notice |
| Max triggers | 3 | 3 | Asonuma; Ho & Fontana p. 8 | FACT |
| **s** (share of total debt service suspended) | **≈ 0.07–0.11** | **≈ 0.8** | see below | JUDGMENT |
| s inputs | International bonds EC$189.8m of EC$2,731m public debt = 6.9% (Grenada *Debt Report 2024*, App. 1 p. 16). Beryl deferral: bond US$12m (0.9% GDP, IMF) + ≈ US$5m Taiwan Ex-Im and others (Reuters, via Claims Journal) vs 2024 debt service EC$420m ≈ US$156m (Debt Report App. 2) | "Around 80% of Barbados' total debt now has this clause" (GlobalCapital, news). Ho & Fontana p. 8: "nearly their entire debt stock" (domestic) | | Barbados: confirm with an official source (IMF CR 19/370) |

**Implication:** the brief's s = 0.30 (Grenada) and s = 0.90 (Barbados) are not supported. Grenada's clause covers well under a fifth of debt service, because multilaterals hold 66.8% of external central-government debt and have no clause. In the brief, defer_repay_years should be read as "remaining maturity at trigger", not a contract constant.

## Task 6 – Macro starting values (Grenada)

| Param | Proposed value | Source | Page / table | Status |
|---|---|---|---|---|
| b0 (public debt incl. SOEs) | 72.7% (2024); 68.3% (2025e); 65.8% (2026p) | IMF CR 26/9 (2025 Art. IV) | Table 1 p. 26 / Table 3b p. 29 | FACT. Choosing 65% (= 2026 projection) is JUDGMENT. |
| b0 (central gov.) | 58.7% (2024) | same | Table 1 p. 26 | FACT |
| b0 (cross-check) | 71.3% end-2024 (EC$2.73bn) | Grenada MoF *Debt Report 2024* | Exec. summary p. 1; App. 1 p. 16 | FACT |
| pb (steady state) | **+1.5%** (FRA floor; projected 2027–30) | IMF CR 26/9 | Key Rules box p. 12; Table 1 p. 26 | FACT. The brief's 2% should become 1.5. |
| pb (path) | +10.0 (2024), −3.2 (2025), −3.5 (2026) | same | Table 1 p. 26 | FACT |
| g real (long run) | 2.7% | IMF CR 26/9 Table 1 (2029–30); CR 25/39 DSA | p. 26 | FACT |
| g nominal (long run) | 4.8% | IMF CR 26/9 Table 1 (2029–30) | p. 26 | FACT |
| r (effective, central gov.) | 2.4% (2023) | IMF CR 25/39, DSA ¶5 | DSA p. 4 | FACT |
| r (alt.) | 3.57% implicit | Guerson WP/20/266 | App. 1 p. 25 | FACT (older) |
| r 2024 caveat | 8.0% weighted average in 2024 | Debt Report 2024 §8 p. 14 | | FACT. Distorted by one-off IMA performance payments, so don't use it. |
| M (avg. time to maturity) | **10.6 yrs** (2024); 10.4 (2023) | Debt Report 2024 Table 7 p. 14; IMF CR 25/39 DSA ¶5 p. 4 | | FACT |

**Warning:** with r ≈ 2.4% and g ≈ 4.8% (both nominal), r − g < 0 on Grenada's mostly concessional debt. Check that the model uses r and g on the same basis (both nominal or both real). Version 2's premium applies to new market borrowing, which these averages understate.

## [VERIFY] claims checked along the way (for task 7)

1. Grenada clause 2015: **confirmed** (2030 bonds, Ex-Im, Paris Club; closed 12 Nov 2015, MoF press release). Triggered after Beryl: **confirmed** (Aug 2024 notice; IMF CR 25/39 ¶7).
2. Asonuma et al.: "inherently a liquidity relief instrument" **confirmed** (Box 2). Relief is "**up to** 2.6 percent of GDP" for one trigger, and up to 7.4% for three. Write "up to". Ivan 200% **confirmed**.
3. Cebotari & Youssef (WP/20/3): **not supported as written.** They do not simulate clauses. They only say clauses "can be structured to be NPV-neutral" and that a standstill "would be similar to insurance" (p. 31). Barbados is not mentioned.
4. Guerson: correct the citation to IMF WP/20/266 (Dec 2020).
5. Mallucci: the welfare result and the debt-limit caution are **confirmed**. Note that his clause defers for one year (Sec. 6 p. 15).
6. Barbados: the domestic exchange was in 2018, but the external bond was restructured in late 2019. Write "2018–19".
7. Brief §4 says deferred principal is repaid "over a fixed number of years". In both real contracts it is repaid over the bond's *remaining* life.

## Sources
- Acevedo (2016) IMF WP/16/199 – https://www.imf.org/external/pubs/ft/wp/2016/wp16199.pdf
- Mallucci (2020) IFDP 1291r1 – https://federalreserve.gov/econres/ifdp/files/ifdp1291r1.pdf
- Cebotari & Youssef (2020) IMF WP/20/3 – https://imf.org/-/media/Files/Publications/WP/2020/English/wpiea2020003-print-pdf.ashx
- Guerson (2020) IMF WP/20/266 – https://imf.org/-/media/Files/Publications/WP/2020/English/wpiea2020266-print-pdf.ashx
- Asonuma et al. (2017) IMF WP/17/171 – https://imf.org/~/media/Files/Publications/WP/2017/wp17171.ashx
- Ho & Fontana (2021) EMRJ 11 – https://www.clearygottlieb.com/-/media/files/emrj-materials/issue-11-spring-2021/article_natural_disaster_clause_v3-pdf
- Anthony, Impavido & van Selm (2020) IMF WP/20/34 – https://imf.org/-/media/Files/Publications/WP/2020/English/wpiea2020034-print-pdf.ashx
- IMF CR 25/39 Grenada 2024 Art. IV – https://caribmagplus.com/wp-content/uploads/2025/02/1grdea2025001-print-pdf.pdf (mirror; get the imf.org copy for citation)
- IMF CR 26/9 Grenada 2025 Art. IV – https://www.imf.org/-/media/files/publications/cr/2026/english/1grdea2026001-source-pdf.pdf
- Grenada MoF Debt Report 2024 – https://www.finance.gd/docs/2025/DEBT_REPORT_2024.pdf
- World Bank Grenada Disaster Risk Profile (2016) – https://www.gfdrr.org/sites/default/files/Grenada1.pdf
- IMF (2016) Small States' Resilience – https://www.elibrary.imf.org/view/journals/007/2016/038/article-A001-en.xml
- Grenada MoF exchange-offer releases (2015) – https://finance.gd/index.php/news/17-news-release/258-126-grenada-launches-debt-exchange-offer
- GlobalCapital (Barbados 80%) – https://www.globalcapital.com/globalmarkets/article/28mtznbpn4d9xw151l7up/emerging-markets/make-debt-climate-resilient-says-barbados-pm-after-restructuring-agreement
