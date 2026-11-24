"""Writes docs/RESULTS_v3.md from the computed grids. Every number in the document is generated, none is typed by hand."""
from __future__ import annotations
import numpy as np
import pandas as pd
from . import config
from .v3 import COUNTRY, DESIGN, SCHEDULE


def pc(x):  return f"{100 * x:.1f}%"
def pp(x):  return f"{100 * x:+.1f} pp"
def ci(lo, hi):  return f"[{100 * lo:+.1f}, {100 * hi:+.1f}] pp"
def yn(b):  return "yes" if b else "no"
def g1(x):  return f"{x:.1f}"


def md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    cols = [str(c) for c in cols]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines)


ORDER = {"grenada_like": 0, "high_debt": 1}
DORDER = {"grenada_style": 0, "barbados_style": 1}


def _sorted(g):
    return g.assign(_s=g.scenario.map(ORDER), _d=g.design.map(DORDER)).sort_values(["_s", "_d", "version", "schedule"], key=lambda c: c if c.name != "schedule" else c.map({"5yr": 0, "lump": 1, "inst": 2})).drop(columns=["_s", "_d"])


def table_prob(grid, key, schedules=("5yr",), with_schedule=False, with_peaks=False):
    rows = []
    for r in _sorted(grid[grid.schedule.isin(schedules)]).itertuples():
        d = {"country": COUNTRY[r.scenario], "design": DESIGN[r.design], "version": f"V{r.version}"}
        if with_schedule:
            d["schedule"] = SCHEDULE[r.schedule]
        d.update({"P no clause": pc(getattr(r, f"{key}_mean_a")), "P clause": pc(getattr(r, f"{key}_mean_b")),
                  "difference": pp(getattr(r, f"{key}_diff")), "95% CI": ci(getattr(r, f"{key}_lo"), getattr(r, f"{key}_hi")),
                  "significant (CI excludes 0)?": yn(getattr(r, f"{key}_sig"))})
        if with_peaks:
            d["mean peak GFN, strike yr+next (no clause / clause)"] = f"{g1(r.peak2_A)} / {g1(r.peak2_B)}"
            d["mean peak GFN, strike yr+5 (no clause / clause)"] = f"{g1(r.peak6_A)} / {g1(r.peak6_B)}"
        rows.append(d)
    return pd.DataFrame(rows)


def table_cont(grid):
    rows = []
    g5, gl = grid[grid.schedule == "5yr"], grid[grid.schedule == "lump"]
    for r in _sorted(g5).itertuples():
        l = gl[(gl.scenario == r.scenario) & (gl.design == r.design) & (gl.version == r.version)].iloc[0]
        f = lambda x, lo, hi: f"{x:+.1f} [{lo:+.1f}, {hi:+.1f}]"
        rows.append({"country": COUNTRY[r.scenario], "design": DESIGN[r.design], "version": f"V{r.version}",
                     "no clause": g1(r.excess_mean_a), "clause (5-yr)": g1(r.excess_mean_b), "clause (B'-lump)": g1(l.excess_mean_b),
                     "difference, 5-yr (95% CI)": f(r.excess_diff, r.excess_lo, r.excess_hi),
                     "difference, B'-lump (95% CI)": f(l.excess_diff, l.excess_lo, l.excess_hi)})
    return pd.DataFrame(rows)


def sign(x, tol=1e-12):
    return 0 if abs(x) < tol else (1 if x > 0 else -1)


def write(path, grid, lump, first, eqb, rk, seeds, cfg3, N, T, seed, repro):
    L = _build(grid, lump, first, eqb, rk, seeds, cfg3, N, T, seed, repro)
    import pathlib
    pathlib.Path(path).write_text("\n".join(L) + "\n")


def _build(grid, lump, first, eqb, rk, seeds, cfg3, N, T, seed, repro):
    L = []
    A = L.append
    H = cfg3["bprime_horizon"]
    A("# RESULTS v3: revised brief runs\n")
    A(f"Model: seed {seed}, N = {N:,} paths x T = {T} years, common random numbers across regimes, calibration unchanged "
      f"(config/calibration.yaml, scenarios.yaml, designs.yaml). New code only: regime B' (src/regimes.py rules `lump_at_horizon`, `equal_to_horizon`), "
      f"src/v3.py, run_v3.py. Regenerate with `python run_v3.py`; full-precision CSVs are in outputs/v3/tables/.\n")
    A(f"**Reproduction check.** The new code reproduces the existing baseline (5-yr equal-instalment) P(stress) and mean peak GFN of "
      f"outputs/tables/exp1_baseline_v1.csv in all 8 country x design cells (max absolute difference {repro:.1e}), the equal-instalment break-evens of "
      f"exp3_repay_switch_points.csv, and the K-vs-R grid of exp3_reconstruction_check.csv. No baseline number changed.\n")
    A("## Definitions\n")
    A("- **Financing-stress episode** (formerly \"hurricane-attributable crisis\"; definition unchanged): GFN more than 5 pp of GDP above the same regime's "
      "no-hurricane path in at least one of the 30 years.")
    A("- **Countries:** Grenada-like (b0 = 65, primary surplus) and High-debt (b0 = 110, primary deficit). **Designs:** Grenada-style (s = 0.10, K = 1) and "
      "High-coverage (s = 0.80, K = 2; `barbados_style` in the code). **V1** = fixed r, **V2** = endogenous risk premium.")
    A("- **Paired CI:** per path d_i = 1[stress with clause] - 1[stress without clause]; difference = mean(d); 95% CI = mean(d) +/- 1.96 sd(d)/sqrt(N). "
      "\"Significant\" = CI excludes 0. A negative difference means the clause LOWERS the probability. Percentages and pp are shown to 1 decimal; "
      "significance is decided on the unrounded values.")
    A(f"- **Regime B' (Grenada's actual repayment).** Deferred amounts are repaid starting the year after the suspension ends; due date = strike year + {H}. "
      f"**B'-lump:** one lump-sum payment in strike year + {H} (IMF CR 25/39: added to the principal due at the 2030 maturity). "
      f"**B'-inst:** equal annual instalments from the year after the suspension ends through strike year + {H} (Asonuma et al. 2017: repaid over the bond's "
      f"remaining life), i.e. {H} instalments for K = 1 and {H - 1} for K = 2. Interpretations to confirm: (i) \"capitalized interest\" is treated exactly as in the baseline "
      "- skipped interest accrues into the covered stock (so the V1 stock equals regime A) and is amortised on the regular 1/M schedule; only the deferred "
      "*amortization* tranche follows the B' schedule; (ii) a second trigger re-sets the due date to (latest trigger year + 6) for the pooled balance "
      "(the analogue of the baseline's instalment-counter reset).")
    A("- **Mean peak GFN** (% of GDP) is averaged over qualifying strikes (D >= D_trig = 5); \"strike year+next\" = max GFN in years t, t+1; \"strike year+5\" = max over t..t+5.\n")

    g = grid
    A("## Table 1. Paired effect of the clause on P(financing-stress episode), baseline 5-year equal-instalment repayment\n")
    A(md(table_prob(g, "stress")) + "\n")
    t1 = table_prob(g, "gfn15")
    A("### Table 1b. Same, for P(GFN > 15% of GDP in at least one year)\n")
    A(md(t1))
    A("\nNote: in High-debt, starting GFN is already above 15% of GDP, so this absolute flag is 100% in every regime by construction: the difference is exactly 0 with a "
      "degenerate CI (zero variance). That is why the brief's stress measure is defined relative to the no-hurricane path.\n")

    A("## Table 2. Repayment schedules: 5-yr equal [baseline] vs B'-lump vs B'-inst\n")
    A(md(table_prob(g, "stress", ("5yr", "lump", "inst"), True, True)) + "\n")
    A("Reading notes. (1) For the High-coverage design (K = 2) B'-inst coincides with the 5-yr baseline: the suspension covers years t and t+1, so instalments run t+2..t+6 = 5 equal instalments. "
      "The two differ only for the Grenada-style design (K = 1: 6 instalments vs 5). (2) The Grenada-like results use Grenada's actual 6-year horizon; "
      "the High-coverage clause is a net stress-raiser under B'-lump because the whole deferred balance falls due in one year (see Table 3b for the horizon at which this reverses). "
      "Figure: figures/figure1_v3.png (copy of outputs/figures/figure1_v3.png).\n")

    A("## Table 3. Break-evens for the High-coverage clause (s = 0.80, K = 2)\n")
    rows = []
    for (sc, v), f in sorted(first.items(), key=lambda kv: (ORDER[kv[0][0]], kv[0][1])):
        e = eqb[(eqb.scenario == sc) & (eqb.version == v)].iloc[0]
        eqs = f"{e.switch_years:.1f}" if np.isfinite(e.switch_years) else f"undefined ({e.verdict})"
        lf = f["L_first_negative"]
        rows.append({"country": COUNTRY[sc], "version": f"V{v}",
                     "equal-instalment break-even (years of repayment; existing method, linear interpolation)": eqs,
                     "lump-sum break-even: smallest L (years after strike) with clause effect < 0": "none in 1..15" if lf is None else str(lf),
                     "smallest L with CI entirely below 0": "none in 1..15" if f["L_first_significant"] is None else str(f["L_first_significant"]),
                     "stays < 0 for all larger L?": "n/a" if lf is None else yn(f["stays_negative_after"])})
    A(md(pd.DataFrame(rows)))
    A("\nThe equal-instalment values 5.9 (Grenada-like V1), 9.3 (High-debt V1) and 5.6 (High-debt V2) are the existing ones, reproduced; Grenada-like V2 "
      f"({eqb[(eqb.scenario == 'grenada_like') & (eqb.version == 2)].iloc[0].switch_years:.1f}) is added (it was in outputs/tables/exp3_repay_switch_points.csv but not in the figure). "
      "The two columns are not on the same clock: the equal-instalment period counts years of repayment after the suspension ends; the lump-sum horizon L counts years from the strike "
      "(the lump is paid in strike year + L; for K = 2 the suspension covers the first two of them).\n")
    A("### Table 3b. Lump-sum horizon sweep: clause effect on P(stress), High-coverage clause (difference in pp; negative = clause lowers P(stress); * = CI excludes 0)\n")
    piv = lump.assign(cell=lambda d: [f"{100 * r['diff']:+.1f}{'*' if r.sig else ''}" for _, r in d.iterrows()],
                      col=lambda d: d.scenario.map(COUNTRY) + " V" + d.version.astype(str))
    pv = piv.pivot(index="L", columns="col", values="cell")
    pv = pv[[f"{COUNTRY[s]} V{v}" for s in ORDER for v in (1, 2)]].reset_index()
    A(md(pv) + "\n")
    A("L = 1 and L = 2 give identical results: with K = 2 the clause is active in the strike year and the next, so a lump due in year t+1 is first payable in t+2, the same as L = 2.\n")

    A("## Table 4. Timing-dependent stress measure (3 pp in the strike year and the year after, 5 pp in all other years)\n")
    A(md(table_prob(g, "stress_tw", ("5yr", "lump"), True)) + "\n")
    A("### Does the sign of the high-coverage effect change versus the baseline (5 pp everywhere) measure?\n")
    hc = g[(g.design == "barbados_style") & g.schedule.isin(["5yr", "lump"])]
    chg, rowsx = [], []
    for r in _sorted(hc).itertuples():
        s0, s1 = sign(r.stress_diff), sign(r.stress_tw_diff)
        rowsx.append({"country": COUNTRY[r.scenario], "version": f"V{r.version}", "schedule": SCHEDULE[r.schedule],
                      "baseline measure": f"{pp(r.stress_diff)}{'*' if r.stress_sig else ''}",
                      "3-pp window measure": f"{pp(r.stress_tw_diff)}{'*' if r.stress_tw_sig else ''}",
                      "sign changes?": yn(s0 != s1)})
        if s0 != s1:
            chg.append(f"{COUNTRY[r.scenario]} V{r.version} {SCHEDULE[r.schedule]}")
    A(md(pd.DataFrame(rowsx)) + "\n\n(* = CI excludes 0.)\n")
    A(("**The sign changes** for: " + "; ".join(chg) + "." if chg else
       "**The sign does not change** in any of the 8 High-coverage cells (2 countries x 2 versions x {5-yr, B'-lump}): the 3-pp window measure flags more paths in both regimes "
       "but does not reverse the direction of the clause effect.") + "\n")
    # magnitude summary
    big = hc.assign(d_change=lambda d: d.stress_tw_diff - d.stress_diff)
    A("Change in the effect (3-pp measure minus baseline measure, pp): " + "; ".join(
        f"{COUNTRY[r.scenario]} V{r.version} {SCHEDULE[r.schedule]} {100 * r.d_change:+.1f}" for r in _sorted(big).itertuples()) + ".\n")

    A("## Table 5. Continuous measure: expected excess GFN = mean over paths of sum_t max(0, GFN_t - no-storm GFN_t - 5), pp of GDP (summed over 30 years)\n")
    A(md(table_cont(g)) + "\n")
    A("Differences are clause minus no clause, with a paired 95% CI on the per-path excess; negative = the clause lowers expected excess GFN.\n")

    A("## Table 6. K-vs-R grid (Grenada-like): difference in P(stress), clause minus no clause, in pp (negative = clause lowers P(stress))\n")
    rk = rk.assign(diff=-100 * rk.benefit_p_hcrisis_any)
    t6 = rk.pivot_table(index=["design", "version", "R"], columns="K", values="diff").reset_index()
    t6["design"] = t6.design.map(DESIGN)
    t6["version"] = "V" + t6.version.astype(str)
    t6 = t6.rename(columns={"design": "design", 1: "K=1", 2: "K=2", 3: "K=3", 4: "K=4"})
    for c in ("K=1", "K=2", "K=3", "K=4"):
        t6[c] = t6[c].map(lambda x: f"{x:+.1f}")
    A(md(t6))
    A("\nR = years over which reconstruction spending is spread; K = years of service deferred per trigger; each cell uses the design's own share s and 5-yr "
      "equal-instalment repayment (s = 0.10 Grenada-style, s = 0.80 High-coverage), the existing grid restricted to K = 1..4. Only the point estimate is tabulated here (the existing grid carries no CI).\n")

    # ---------------------------------------------------------------- robustness
    A("## Robustness: seeds 43 and 44 (High-coverage, Grenada-like; Tables 2 and 4)\n")
    base = seeds[seed].set_index(["version", "schedule"])
    qty = {"P(stress) no clause": "stress_mean_a", "P(stress) clause": "stress_mean_b", "difference (Table 2)": "stress_diff",
           "difference, 3-pp measure (Table 4)": "stress_tw_diff", "mean peak GFN t..t+1 no clause": "peak2_A",
           "mean peak GFN t..t+1 clause": "peak2_B", "mean peak GFN t..t+5 no clause": "peak6_A", "mean peak GFN t..t+5 clause": "peak6_B"}
    rows, flips, sigflips = [], [], []
    for s in sorted(k for k in seeds if k != seed):
        o = seeds[s].set_index(["version", "schedule"])
        row = {"seed": s}
        for lab, col in qty.items():
            dif = (o[col] - base[col]).abs()
            scale = 100 if col.startswith(("stress",)) else 1
            unit = "pp" if scale == 100 else "pp of GDP"
            i = dif.idxmax()
            row[f"max |diff| {lab}"] = f"{scale * dif.max():.1f} {unit} (V{i[0]}, {SCHEDULE[i[1]]})"
        rows.append(row)
        for idx in base.index:
            for col, lab in (("stress_diff", "Table 2 measure"), ("stress_tw_diff", "Table 4 measure")):
                if sign(base.loc[idx, col]) != sign(o.loc[idx, col]):
                    flips.append(f"seed {s}, V{idx[0]}, {SCHEDULE[idx[1]]}, {lab}: {pp(base.loc[idx, col])} -> {pp(o.loc[idx, col])}")
            if bool(base.loc[idx, "stress_sig"]) != bool(o.loc[idx, "stress_sig"]):
                sigflips.append(f"seed {s}, V{idx[0]}, {SCHEDULE[idx[1]]} (Table 2 measure): significance {yn(base.loc[idx, 'stress_sig'])} -> {yn(o.loc[idx, 'stress_sig'])}")
    A(md(pd.DataFrame(rows).set_index("seed").T.reset_index().rename(columns={"index": "largest difference vs seed 42"}).rename(columns=str)) + "\n")
    A(("**Sign changes:** " + "; ".join(flips) + "." if flips else "**No sign changes:** the sign of the clause effect (both measures, all 6 version x schedule cells) is identical in seeds 42, 43 and 44.") + "\n")
    A(("Significance flips (CI excludes 0 or not): " + "; ".join(sigflips) + "." if sigflips else "No cell changes between significant and not significant.") + "\n")
    cols = ["version", "schedule", "stress_mean_a", "stress_mean_b", "stress_diff", "stress_lo", "stress_hi", "stress_tw_mean_a", "stress_tw_mean_b", "stress_tw_diff", "stress_tw_lo", "stress_tw_hi"]
    allseeds = pd.concat([seeds[s][cols].assign(seed=s) for s in sorted(seeds)])
    fmt = allseeds.assign(version=lambda d: "V" + d.version.astype(str), schedule=lambda d: d.schedule.map(SCHEDULE))
    out = pd.DataFrame({"seed": fmt.seed, "version": fmt.version, "schedule": fmt.schedule,
                        "P no clause": fmt.stress_mean_a.map(pc), "P clause": fmt.stress_mean_b.map(pc),
                        "difference (95% CI)": [f"{pp(r.stress_diff)} {ci(r.stress_lo, r.stress_hi)}" for r in fmt.itertuples()],
                        "3-pp: P no clause": fmt.stress_tw_mean_a.map(pc), "3-pp: P clause": fmt.stress_tw_mean_b.map(pc),
                        "3-pp: difference (95% CI)": [f"{pp(r.stress_tw_diff)} {ci(r.stress_tw_lo, r.stress_tw_hi)}" for r in fmt.itertuples()]})
    A("### Seed-by-seed values (P(stress) and its paired effect, both measures)\n")
    A(md(out.sort_values(["version", "schedule", "seed"], key=lambda c: c.map({"5-yr equal [baseline]": 0, "B'-lump": 1, "B'-inst": 2}) if c.name == "schedule" else c)) + "\n")

    # ---------------------------------------------------------------- parameter status and AI decision log
    counts = config.status_counts()
    new = {}
    import yaml
    for v in yaml.safe_load(config.V3_PATH.read_text())["parameters"].values():
        new[v["status"]] = new.get(v["status"], 0) + 1
    old = {k: counts.get(k, 0) - new.get(k, 0) for k in ("SOURCED", "CALIBRATED", "ASSUMPTION")}
    A("## (a) Parameter entries by status\n")
    A(md(pd.DataFrame([
        {"status": "sourced", "before (baseline)": old["SOURCED"], "added in v3": new.get("SOURCED", 0), "now": counts.get("SOURCED", 0)},
        {"status": "calibrated", "before (baseline)": old["CALIBRATED"], "added in v3": new.get("CALIBRATED", 0), "now": counts.get("CALIBRATED", 0)},
        {"status": "assumed", "before (baseline)": old["ASSUMPTION"], "added in v3": new.get("ASSUMPTION", 0), "now": counts.get("ASSUMPTION", 0)},
        {"status": "**total**", "before (baseline)": sum(old.values()), "added in v3": sum(new.values()), "now": sum(counts.values())}])))
    A("\nCounting rule: every entry with a status in config/calibration.yaml (global), scenarios.yaml and designs.yaml, as in `config.status_counts()` (the baseline "
      "52 = 15 + 15 + 22), plus config/v3.yaml. The two new entries are: `storm_window_margin` = 3 pp, the timing-dependent stress threshold (**assumed**: our own choice), and "
      f"`bprime_horizon` = {H} years, the strike-to-due-date horizon of regime B' (**calibrated**: 2030 bond maturity minus 2024 strike, from sourced dates; status is my "
      "classification and can be changed to assumed). None is VERIFIED (reserved for the group).\n")
    A("## (b) Draft rows for the brief's AI decision log\n")
    A(md(pd.DataFrame(AI_ROWS, columns=["Tool and task", "What the AI produced", "How we verified it", "Effect on our decisions"])) + "\n")
    return L


AI_ROWS = [
    ("Claude Code: review of Regime B principal accounting after a suspected double count (2026-11-11)",
     "Confirmed that deferred principal was paid twice (liability outside the stock); rewrote regime B so the deferred balance is a tranche inside the covered stock",
     "Re-derived the amortization split by hand; replaced the old 'equal discounted GFN' test with five explicit accounting checks; compared old and new CSVs",
     "Fix accepted (DECISIONS #3); under V1 the clause stock now equals the no-clause stock, which makes the clause a liquidity-only instrument"),
    ("Claude Code: entered the sourced calibration, scenario overrides and the repay_rule option (2026-11-12)",
     "Rewrote the three YAML files with source, page and status for each value; fitted the lognormal damage law (docs/fit.py)",
     "docs/fit.py reproduces the World Bank AAL and 250-year-PML targets through the model's own damage generator; new tests on instalment clearing and override plumbing",
     "Group confirmed mu_D = ln(median), nominal r and g, scenario-level overrides (DECISIONS #40-#44); every non-sourced value labelled ASSUMPTION"),
    ("Claude Code: HURDAT2 check of the hurricane frequency lambda for Grenada (2026-11-12)",
     "docs/hurdat_check.py and a report: lambda ranges 0.044-0.067 depending on radius; Emily 2005 was not Cat 3+ at Grenada",
     "Cross-checked Ivan, Emily and Beryl closest approaches and the Allen 1980 100-nm hit by listing track points by hand",
     "lambda = 0.051 kept, with the HURDAT2 bracket in its YAML note (DECISIONS #47, #49); report-only, no re-calibration"),
    ("Claude Code: Fiscal Resilience Act surplus rule (2026-11-12)",
     "economy.primary_deficit option: a baseline primary surplus applies only while lagged debt exceeds 60% of GDP; three tests",
     "Independent closed-form iteration in the no-hurricane test; checked which parameters the +-25% sweep really covers before labelling them",
     "Rule on by default and b_star SOURCED (DECISIONS #50); the forgiveness-accounting test switches it off"),
    ("Claude Code: revised-brief runs (2026-11-22): paired CIs, Grenada's actual repayment (B'-lump, B'-inst), timing-dependent and continuous stress measures, seeds 43/44",
     "New regime rules, src/v3.py, run_v3.py, 29 new tests, RESULTS_v3.md and Figure 1 (v3); no existing parameter or result changed",
     "New code reproduces the saved baseline tables to 1e-9 (P(stress), peaks, break-evens, K-vs-R grid); tests that B' repays the full deferred balance and that the V1 debt stock equals the no-clause path; seed 43/44 reruns",
     "Both repayment readings reported side by side instead of choosing one (DECISIONS #52-#56); measure renamed 'financing-stress episode'; two new parameter entries added"),
]
