"""v4 runs (tasks A-D of the second revision). Usage: python run_v4.py
Writes outputs/v4/tables/*.csv, figures/figure1_v4.png (+ copy in outputs/figures/) and docs/RESULTS_v4.md.
RESULTS_v3.md and every v3 output are left untouched; the script asserts that the v3 numbers are reproduced."""
import pathlib, shutil, time
import numpy as np
import pandas as pd
from src import config, hurricanes, v3, v4, plots_v3
from src.results_v3 import md, ORDER, DORDER

ROOT = pathlib.Path(__file__).parent
CN, DN = v3.COUNTRY, v3.DESIGN


def f1(x): return f"{x:.1f}"
def pc(x): return f"{100 * x:.1f}"
def cell(d, lo, hi): return f"{100 * d:+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}]{'*' if (lo > 0 or hi < 0) else ''}"
def sg(x): return 0 if abs(x) < 1e-12 else (1 if x > 0 else -1)


def cells(grid):
    return sorted({(r.scenario, r.design, r.version) for r in grid.itertuples()}, key=lambda k: (ORDER[k[0]], DORDER[k[1]], k[2]))


def main():
    t0 = time.time()
    params, sim, _ = config.load_calibration()
    scenarios, _ = config.load_scenarios()
    designs, _ = config.load_designs()
    main_sc = config.main_scenarios(scenarios)
    cfg3 = config.load_v3()
    N, T, seed = sim["N"], sim["T"], sim["seed"]
    out = ROOT / "outputs" / "v4" / "tables"
    out.mkdir(parents=True, exist_ok=True)
    draws = hurricanes.draw_noise(seed, N, T)
    hc = designs["barbados_style"]

    # ------------------------------------------------------------------ reproduction of v3 (nothing changed)
    grid = pd.read_csv(ROOT / "outputs" / "v3" / "tables" / "grid_seed42.csv")
    chk = v3.run_grid(params, main_sc, designs, draws, N, T, v3=cfg3)
    num = [c for c in grid.columns if grid[c].dtype.kind == "f"]
    repro = float(np.abs(chk[num].values - grid[num].values).max())
    assert repro < 1e-9, f"v3 grid not reproduced ({repro})"
    print("v3 grid reproduced, max abs diff", repro)

    # ------------------------------------------------------------------ A: figure
    eqb = pd.read_csv(ROOT / "outputs" / "v3" / "tables" / "equal_instalment_breakeven_seed42.csv")
    figpath = ROOT / "figures" / "figure1_v4.png"
    fdata = plots_v3.figure1_v4(grid, eqb, N, figpath)
    shutil.copy(figpath, ROOT / "outputs" / "figures" / "figure1_v4.png")

    # ------------------------------------------------------------------ B1 / B2: lump-sum diagnostics (high-coverage clause)
    diag = {}
    for sname, scen in main_sc.items():
        for v in (1, 2):
            diag[(sname, v)] = v4.lump_diagnostics(params, scen, hc, v, draws, N, T, cfg3)
    pd.DataFrame([{"scenario": k[0], "version": k[1], **d} for k, d in diag.items()]).to_csv(out / "lump_diagnostics.csv", index=False)

    # ------------------------------------------------------------------ B3: refinanced lump
    refi = v3.run_grid(params, main_sc, {"barbados_style": hc}, draws, N, T, schedules=("5yr", "lump", "lump_refi"), v3=cfg3)
    refi.to_csv(out / "refinanced_lump.csv", index=False)

    # ------------------------------------------------------------------ C: robustness
    rob = v4.robustness(params, main_sc, designs, draws, N, T, cfg3)
    rob.to_csv(out / "robustness.csv", index=False)
    base = rob[rob.variant == "base"]
    for sk, col in (("5yr", "stress_diff"), ("lump", "stress_diff"), ("5yr", "stress_tw_diff"), ("lump", "stress_tw_diff")):
        a = base[base.schedule == sk].sort_values(["scenario", "design", "version"])[col].values
        b = grid[grid.schedule == sk].sort_values(["scenario", "design", "version"])[col].values
        assert np.allclose(a, b, atol=1e-12), f"robustness base != v3 ({sk}, {col})"
    old = pd.read_csv(ROOT / "outputs" / "tables" / "damage_median_sign_test.csv")
    for mult, vn in ((0.75, "median x0.75"), (1.25, "median x1.25")):
        r5 = rob[(rob.variant == vn) & (rob.schedule == "5yr")]
        for o in old[old.damage_median_multiplier == mult].itertuples():
            n = r5[(r5.scenario == o.scenario) & (r5.design == o.design) & (r5.version == o.version)].iloc[0]
            assert abs(100 * n.stress_diff - o.diff_clause_minus_no_clause_pp) < 1e-6, "damage-median variant != existing check"
    print("robustness base and damage-median variants reproduce v3 / damage_median_sign_test.csv")

    # ------------------------------------------------------------------ D: Beryl
    gren = main_sc["grenada_like"]
    gs = designs["grenada_style"]
    kap_net = params["kappa"]                                    # 0.42 = (10.2 - 3.2) / 16.5, payout already netted
    kap_gross = round(10.2 / 16.5, 2)                            # 0.62 (scenarios.yaml grenada_like_kappa_062), payout explicit
    variants = [("kappa 0.42 (payout netted in; sourced setting)", kap_net, 0.0),
                ("kappa 0.62 gross + explicit 3.2 payout in 2024", scenarios["grenada_like_kappa_062"]["kappa"], v4.BERYL_PAYOUT),
                ("kappa 0.42 + extra 3.2 payout (literal; double-counts)", kap_net, v4.BERYL_PAYOUT)]
    assert abs(scenarios["grenada_like_kappa_062"]["kappa"] - 0.62) < 1e-12
    beryl = []
    for ver in (1, 2):
        for vlab, kap, infl in variants:
            for reg, sk, rlab in (("A", "5yr", "A (no clause)"), ("B", "lump", "B'-lump, Grenada-style (s=0.10, K=1)")):
                r = v4.beryl(params, gren, gs, ver, reg, sk, kappa=kap, inflow=infl)
                beryl.append({"version": ver, "setting": vlab, "regime": rlab, **{f"debt{i + 2024}": r["debt"][i] for i in range(3)},
                              **{f"gfn{i + 2024}": r["gfn"][i] for i in range(3)}, **{f"pb{i + 2024}": r["pb"][i] for i in range(3)},
                              **{f"g{i + 2024}": 100 * r["g"][i] for i in range(3)}})
    bdf = pd.DataFrame(beryl)
    bdf.to_csv(out / "beryl_validation.csv", index=False)

    L = build(grid, diag, refi, rob, bdf, fdata, N, T, seed, repro, cfg3)
    (ROOT / "docs" / "RESULTS_v4.md").write_text("\n".join(L) + "\n")
    print(f"done in {time.time() - t0:.0f}s")


def build(grid, diag, refi, rob, bdf, fdata, N, T, seed, repro, cfg3):
    L, A = [], None
    A = L.append
    A("# RESULTS v4: second revision (figure 1 v4, lump-sum diagnostics, robustness, Beryl validation)\n")
    A(f"Seed {seed}, N = {N:,} paths x T = {T} years, common random numbers across regimes and variants. No parameter changed; RESULTS_v3.md is untouched. "
      f"Reproduction: the v3 grid is recomputed and matches outputs/v3/tables/grid_seed42.csv (max abs diff {repro:.1e}); the robustness base cells match v3; the damage-median "
      "x0.75 / x1.25 cells (5-yr, standard measure) match outputs/tables/damage_median_sign_test.csv to 1e-6 points. Regenerate with `python run_v4.py`.\n")
    A("Conventions: 'points' = percentage points (of probability, or of GDP for GFN). Clause-minus-no-clause differences are paired per path (same draws), 95% CI = mean(d) +/- 1.96 sd(d)/sqrt(N); "
      "`*` = CI excludes 0. High-coverage design = s = 0.80, K = 2 (`barbados_style` in code). B'-lump = whole deferred balance paid in strike year + 6.\n")

    # ---------------------------------------------------------------------------------------------- A
    A("## A. Figure 1 (figures/figure1_v4.png): every number printed on the bars\n")
    A("Version 1, 5-year instalments unless stated. Panel B error bars are the marginal 95% CI of each probability (normal approximation). "
      "Panel A uses the existing windows: 'strike yr + next' = max GFN in t..t+1, 'strike yr + 5' = max over t..t+5, averaged over strikes with D >= 5.\n")
    pa = pd.DataFrame(fdata["A"])
    pa = pa.pivot_table(index=["country", "window"], columns="bar", values="value", sort=False).reset_index()
    pa = pa[["country", "window", "No clause", "Clause, five-year instalments", "Clause, lump sum (B'-lump)"]]
    for c in pa.columns[2:]:
        pa[c] = pa[c].map(f1)
    A("**Panel A. Mean peak GFN, % of GDP (high-coverage design)**\n")
    A(md(pa) + "\n")
    A("**Panel B. P(financing-stress episode), % (+/- half-width of 95% CI)**\n")
    pb = pd.DataFrame(fdata["B"]).assign(v=lambda d: d.apply(lambda r: f"{r.value:.1f} (+/- {r.ci_half:.1f})", axis=1))
    pb = pb.pivot_table(index="country", columns="bar", values="v", aggfunc="first", sort=False)
    pb = pb[["No clause", "Grenada-style clause", "High-coverage clause", "High-coverage clause, B'-lump"]].reset_index()
    A(md(pb) + "\n")
    A("**Panel C. Equal-instalment break-even (years)**\n")
    pcx = pd.DataFrame(fdata["C"]).assign(value=lambda d: d.value.map(lambda x: "undefined" if np.isnan(x) else f1(x)))
    A(md(pcx) + "\n")
    A("Panel C's dashed line is the assumed five-year instalment period. These values are generated from the same data object as the figure labels.\n")

    # ---------------------------------------------------------------------------------------------- B1
    A("## B1. Size of the deferred balance repaid in the lump-sum year (B'-lump, high-coverage)\n")
    rows = []
    for (sc, v), d in sorted(diag.items(), key=lambda kv: (ORDER[kv[0][0]], kv[0][1])):
        rows.append({"country": CN[sc], "version": f"V{v}", "paths with a strike": f"{d['n_strike_paths']:,}",
                     "lump falls due within 30 yrs": f"{d['n_lump_paid_within_T']:,}", "mean lump, % of GDP": f1(d["lump_mean"]),
                     "median lump, % of GDP": f1(d["lump_median"]), "90th pct, % of GDP": f1(d["lump_p90"]),
                     "service skipped in the first suspension (interest + principal, % of GDP at strike): mean / median": f"{f1(d['skipped_first_mean'])} / {f1(d['skipped_first_median'])}"})
    A(md(pd.DataFrame(rows)) + "\n")
    A("The lump is the first positive deferred-balance repayment on each path (cash, % of GDP in the year it is paid, which is strike year + 6). "
      "Paths whose strike is too late for the lump to fall inside the 30 years are excluded from the mean and median. "
      "The last column is the total debt service suspended in the first window (interest and principal, each year as % of that year's GDP). "
      "The brief's 'about 12% of GDP' is higher than every Grenada-like number here; it matches a static back-of-envelope, 2 years x 0.8 x 65 x (2.4% + 1/10.6) = 12.3, "
      "i.e. two years of full service on the covered debt at b_0 = 65 with no growth and no debt run-down (the derivation is not in the repo, so this is my inference). "
      "In the model the lump is smaller than the skipped service for two reasons: (a) it contains only the deferred AMORTIZATION; skipped interest is capitalised into the covered stock and then amortised on the ordinary 1/M schedule "
      "(the interpretation flagged in RESULTS_v3); (b) it is paid six years later in a larger economy (nominal growth 4.8% a year), so the same currency amount is a smaller share of GDP. "
"A variant in which capitalised interest is also paid in the lump would give a larger lump than reported here; it was not run.\n")

    # ---------------------------------------------------------------------------------------------- B2
    A("## B2. How extreme is the lump-sum year? P(GFN > 15% of GDP)\n")
    rows = []
    for (sc, v), d in sorted(diag.items(), key=lambda kv: (ORDER[kv[0][0]], kv[0][1])):
        for lab, k in (("No clause", "A"), ("Clause, 5-yr instalments", "inst"), ("Clause, B'-lump", "lump")):
            rows.append({"country": CN[sc], "version": f"V{v}", "regime": lab,
                         "mean GFN in the lump year, % of GDP": f1(d[f"gfn_lumpyear_mean_{k}"]),
                         "P(GFN>15 in the lump year), % of paths where a lump falls due": pc(d[f"p15_year_{k}"]),
                         "same, as % of ALL paths": pc(d[f"p15_year_{k}_unc"]),
                         "P(GFN>15 in any of 30 years), %": pc(d[f"p15_any_{k}"])})
    A(md(pd.DataFrame(rows)) + "\n")
    A("'Lump year' = each path's own year in which the B'-lump regime pays its lump; the same calendar year is used for the no-clause and instalment regimes on that path. "
      "In High-debt the absolute flag is saturated by construction (starting GFN is already above 15% of GDP).\n")
    A("**How much of the lump-sum effect is the 5-point measure?** P(GFN more than m points above the same regime's no-storm path in at least one year), no clause vs B'-lump:\n")
    rows = []
    for (sc, v), d in sorted(diag.items(), key=lambda kv: (ORDER[kv[0][0]], kv[0][1])):
        row = {"country": CN[sc], "version": f"V{v}"}
        for m in (5, 10, 15):
            row[f"m={m}: no clause / B'-lump / diff, %"] = f"{pc(d[f'stress{m}_A'])} / {pc(d[f'stress{m}_lump'])} / {100 * (d[f'stress{m}_lump'] - d[f'stress{m}_A']):+.1f}"
        rows.append(row)
    A(md(pd.DataFrame(rows)) + "\n")
    A("Mean peak GFN over t..t+6 (the window that includes the lump year), % of GDP, no clause / 5-yr instalments / B'-lump. Figure 1's 'strike yr + 5' window ends one year BEFORE the lump falls due, "
      "which is why its B'-lump bars look lower than the instalment bars:\n")
    rows = [{"country": CN[sc], "version": f"V{v}", "t..t+6: no clause / 5-yr / B'-lump": f"{f1(d['peak7_A'])} / {f1(d['peak7_inst'])} / {f1(d['peak7_lump'])}"}
            for (sc, v), d in sorted(diag.items(), key=lambda kv: (ORDER[kv[0][0]], kv[0][1]))]
    A(md(pd.DataFrame(rows)) + "\n")

    # ---------------------------------------------------------------------------------------------- B3
    A("## B3. Refinanced lump sum (new rule `lump_refinanced`; optional item)\n")
    A("Interpretation: nothing is paid in cash in year strike + 6. The deferred balance is folded into the regular covered stock and then amortises on the ordinary 1/M schedule at the market rate "
      "(in V2 the effective rate, which carries the endogenous risk premium). Clause-minus-no-clause on the standard stress measure, high-coverage design:\n")
    rows = []
    for r in refi.assign(_s=refi.scenario.map(ORDER)).sort_values(["_s", "version", "schedule"]).itertuples():
        rows.append({"country": CN[r.scenario], "version": f"V{r.version}", "schedule": v3.SCHEDULE[r.schedule], "P no clause, %": pc(r.stress_mean_a),
                     "P clause, %": pc(r.stress_mean_b), "difference, points [95% CI]": cell(r.stress_diff, r.stress_lo, r.stress_hi)})
    A(md(pd.DataFrame(rows)) + "\n")

    # ---------------------------------------------------------------------------------------------- C
    A("## C. Robustness of the two conclusions that now drive the brief\n")
    A("Variants: damage median x0.75 and x1.25 (mu_D = ln(new median), sigma_D unchanged; same method as docs/damage_median_sign_test.py); '+25 bp delay premium' = `deferral_premium_on = 1` with the existing 25 bp "
      "spread on the covered stock's rate in the clause regime only (each regime is compared with its own no-storm path). Cells: clause minus no clause, points [95% CI]; * = CI excludes 0.\n")
    flips = {"i": [], "ii": []}
    lost = {"i": [], "ii": []}
    for tag, sk, col, title in (("i", "lump", "stress", "(i) B'-lump, standard stress measure (5 points)"),
                                ("ii", "5yr", "stress_tw", "(ii) 5-year instalments, 3-point storm-window measure")):
        A(f"**{title}**\n")
        rows = []
        for (sc, dn, v) in cells(rob):
            row = {"country": CN[sc], "design": DN[dn], "version": f"V{v}"}
            ref, ref_sig = None, None
            fl, lose = [], []
            for vn in v4.VARIANTS:
                r = rob[(rob.scenario == sc) & (rob.design == dn) & (rob.version == v) & (rob.schedule == sk) & (rob.variant == vn)].iloc[0]
                d = r[f"{col}_diff"]
                row[vn] = cell(d, r[f"{col}_lo"], r[f"{col}_hi"])
                sig = bool(r[f"{col}_lo"] > 0 or r[f"{col}_hi"] < 0)
                if vn == "base":
                    ref, ref_sig = d, sig
                else:
                    if sg(d) * sg(ref) < 0:
                        fl.append(vn)
                    elif ref_sig and not sig:
                        lose.append(f"{vn} (point estimate {100 * d:+.1f}, CI spans 0)")
            row["sign flips vs base"] = ", ".join(fl) if fl else "none"
            row["loses significance vs base"] = ", ".join(lose) if lose else "no"
            if fl:
                flips[tag].append(f"{CN[sc]} / {DN[dn]} / V{v}: {', '.join(fl)}")
            if lose:
                lost[tag].append(f"{CN[sc]} / {DN[dn]} / V{v}: {', '.join(lose)}")
            rows.append(row)
        A(md(pd.DataFrame(rows)) + "\n")
    for tag, lab in (("i", "(i) B'-lump"), ("ii", "(ii) 3-point window, 5-yr")):
        A(f"- {lab}: " + ("**sign flips in** " + "; ".join(flips[tag]) if flips[tag] else "no sign flips in any of the 24 variant cells (3 variants x 8 cells).")
          + (" Loses significance (same sign or zero, CI now spans 0): " + "; ".join(lost[tag]) + "." if lost[tag] else " No cell loses significance.") + "\n")

    # ---------------------------------------------------------------------------------------------- D
    A("## D. Beryl validation (Grenada-like, no calibration change)\n")
    A("Set-up: b_0 = 65% of GDP (unchanged), one deterministic strike in year 1 (= 2024) of 16.5% of GDP, no other storms, R = 3, FRA surplus rule on, all other parameters as in calibration.yaml. "
      "Debt is public debt incl. SOEs at year end. **Insurance:** kappa = 0.42 is already net of the 3.2%-of-GDP CCRIF payout ((10.2 - 3.2) / 16.5), so the sourced run has the payout inside it. "
      "The second setting uses the gross share 0.62 with the payout as an explicit 3.2-point cash inflow in 2024; the third is the literal reading (0.42 plus an extra 3.2) and double-counts the payout; it is shown only for completeness. "
      "IMF reference (IMF CR 26/9 Table 1 p.26, from docs/parameter_sourcing_register.md): public debt 72.7% (2024), 68.3% (2025e), 65.8% (2026p); primary balance +10.0, -3.2, -3.5. "
      "The docs contain no IMF GFN path, so GFN has no reference column.\n")
    imf = {2024: v4.IMF_DEBT[1], 2025: v4.IMF_DEBT[2], 2026: v4.IMF_DEBT[3]}
    rows = []
    for r in bdf.itertuples():
        row = {"version": f"V{r.version}", "setting": r.setting, "regime": r.regime}
        for y in (2024, 2025, 2026):
            row[f"debt {y}"] = f1(getattr(r, f"debt{y}"))
        for y in (2024, 2025, 2026):
            row[f"GFN {y}"] = f1(getattr(r, f"gfn{y}"))
        rows.append(row)
    A(md(pd.DataFrame(rows)) + "\n")
    A("IMF: debt 72.7 / 68.3 / 65.8 (2024 / 2025e / 2026p).\n")
    sel = bdf[(bdf.regime == "A (no clause)") & bdf.setting.str.startswith("kappa 0.42 (")]
    rows = []
    for r in sel.itertuples():
        rows.append({"version": f"V{r.version}", "debt gap vs IMF, 2024 / 2025 / 2026 (model minus IMF, points)": " / ".join(f"{getattr(r, f'debt{y}') - imf[y]:+.1f}" for y in (2024, 2025, 2026)),
                     "model primary balance 2024 / 2025 / 2026": " / ".join(f"{getattr(r, f'pb{y}'):+.1f}" for y in (2024, 2025, 2026)),
                     "IMF primary balance": "+10.0 / -3.2 / -3.5", "model nominal growth 2024 / 2025 / 2026, %": " / ".join(f"{getattr(r, f'g{y}'):.1f}" for y in (2024, 2025, 2026))})
    A("Gap for the sourced setting (no clause), reported as it is:\n")
    A(md(pd.DataFrame(rows)) + "\n")
    return L


if __name__ == "__main__":
    main()
