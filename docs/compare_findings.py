"""Old (placeholder) vs new (sourced) calibration for the five findings. Reads the tables of an earlier commit with git.
Usage: .venv/bin/python docs/compare_findings.py [OLD_COMMIT]   (default: 87c1a0b, the last placeholder run)
Crisis measures are named in every row: HAC = hurricane-attributable crisis (GFN above the same regime's no-hurricane path
by more than 5 pp of GDP in at least one year); ABS = GFN above 15% of GDP in at least one year."""
import io, pathlib, subprocess, sys
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import experiments  # noqa: E402

OLD = sys.argv[1] if len(sys.argv) > 1 else "87c1a0b"
NEW = ROOT / "outputs" / "tables"
pd.set_option("display.width", 250, "display.max_columns", 30, "display.float_format", "{:.2f}".format)


def old(name):
    txt = subprocess.run(["git", "show", f"{OLD}:outputs/tables/{name}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return pd.read_csv(io.StringIO(txt))


def new(name):
    return pd.read_csv(NEW / name)


MAIN = ["grenada_like", "high_debt"]
rows = []
# ---- (1) clause cuts peak GFN after a hurricane (version 1; mean peak GFN, % of GDP)
for ver, f in ((1, "exp1_baseline_v1.csv"), (2, "exp2_endogenous_premium_v2.csv")):
    o, n = old(f), new(f)
    for d in ("grenada_style", "barbados_style"):
        for s in MAIN:
            for tag, col in (("t..t+1", "peak_gfn2_mean"), ("t..t+5", "peak_gfn6_mean")):
                def pick(df, r):
                    return float(df[(df.design == d) & (df.scenario == s) & (df.regime == r)][col].iloc[0])
                rows.append(dict(finding="1 clause cuts peak GFN", measure=f"mean peak GFN {tag}, % GDP", design=d, scenario=s, version=ver,
                                 old=f"A {pick(o,'A'):.1f} -> B {pick(o,'B'):.1f}", new=f"A {pick(n,'A'):.1f} -> B {pick(n,'B'):.1f}",
                                 old_cut=pick(o, 'A') - pick(o, 'B'), new_cut=pick(n, 'A') - pick(n, 'B')))
# ---- (2) debt stock unchanged (version 1)
o, n = old("exp1_baseline_v1.csv"), new("exp1_baseline_v1.csv")
for name, df in (("old", o), ("new", n)):
    g = df[df.regime.isin(["A", "B"])].pivot_table(index=["design", "scenario"], columns="regime", values=["bT_mean", "bT_median", "p_bT_gt100"])
    rows.append(dict(finding="2 debt stock unchanged (B = A)", measure="max |A-B| over designs x scenarios: b_T mean / median (% GDP), P(b_T>100)",
                     design="all", scenario="all", version=1, **{name: f"{(g['bT_mean']['A']-g['bT_mean']['B']).abs().max():.1e} / {(g['bT_median']['A']-g['bT_median']['B']).abs().max():.1e} / {(g['p_bT_gt100']['A']-g['p_bT_gt100']['B']).abs().max():.1e}"}))
o2, n2 = old("exp2_endogenous_premium_v2.csv"), new("exp2_endogenous_premium_v2.csv")
for name, df in (("old", o2), ("new", n2)):
    g = df[df.regime.isin(["A", "B"])].pivot_table(index=["design", "scenario"], columns="regime", values=["bT_mean"])
    rows.append(dict(finding="2 debt stock (version 2, premium)", measure="max |A-B| b_T mean, % GDP", design="all", scenario="all", version=2,
                     **{name: f"{(g['bT_mean']['A']-g['bT_mean']['B']).abs().max():.2f}"}))
# ---- (3) repayment speed decides the sign
od = old("exp3_design_sensitivity.csv")
od = od[(od.D_trig == 5) & (((od.design == "grenada_style") & (od.K == 1)) | ((od.design == "barbados_style") & (od.K == 2))) & od.scenario.isin(MAIN)].copy()
od["repay_rule"] = "declining_balance"
for metric in ("benefit_p_hcrisis_any", "benefit_p_crisis_any"):
    so = experiments.repay_switch_points(od, metric)
    sn = pd.read_csv(NEW / "exp3_repay_switch_points.csv"); sn = sn[sn.metric == metric]
    lab = "HAC" if "hcrisis" in metric else "ABS"
    for _, r in so.iterrows():
        k = sn[(sn.design == r.design) & (sn.scenario == r.scenario) & (sn.version == r.version)]
        for _, q in k.iterrows():
            f = lambda x: (f"switch at {x.switch_years:.1f}y" if x.verdict == "switch" else x.verdict) + f" (2y {x.benefit_at_2y_pp:+.1f} pp, 12y {x.benefit_at_12y_pp:+.1f} pp)"
            if q.repay_rule == "declining_balance" or True:
                rows.append(dict(finding="3 repayment speed decides sign", measure=f"{lab} benefit A-B; new rule = {q.repay_rule}", design=r.design, scenario=r.scenario,
                                 version=r.version, old=f(r), new=f(q)))
# ---- (4) benefit jumps at K = R
oj, nj = old("exp3_reconstruction_check_jumps.csv"), new("exp3_reconstruction_check_jumps.csv")
for (d, s, v), g in nj.groupby(["design", "scenario", "version"]):
    go = oj[(oj.design == d) & (oj.scenario == s) & (oj.version == v)]
    rows.append(dict(finding="4 benefit jumps at K=R", measure="K of the largest rise in HAC benefit (R=2/3/4)", design=d, scenario=s, version=v,
                     old="/".join(str(int(x)) for x in go.sort_values("R").jump_at_K), new="/".join(str(int(x)) for x in g.sort_values("R").jump_at_K)))
# ---- (5) high debt overwhelms the clause
for ver, f in ((1, "exp1_baseline_v1.csv"), (2, "exp2_endogenous_premium_v2.csv")):
    o, n = old(f), new(f)
    for d in ("grenada_style", "barbados_style"):
        for s in MAIN:
            def v(df, r, c):
                return float(df[(df.design == d) & (df.scenario == s) & (df.regime == r)][c].iloc[0])
            for c, lab in (("p_hcrisis_any", "HAC"), ("p_crisis_any", "ABS")):
                rows.append(dict(finding="5 high debt overwhelms clause", measure=f"P({lab}) %: A / B / C", design=d, scenario=s, version=ver,
                                 old=" / ".join(f"{100*v(o,r,c):.1f}" for r in "ABC"), new=" / ".join(f"{100*v(n,r,c):.1f}" for r in "ABC")))
            rows.append(dict(finding="5 high debt overwhelms clause", measure="median years until debt > 150% GDP: A / B / C (nan = <50% of paths)", design=d, scenario=s, version=ver,
                             old=" / ".join(f"{v(o,r,'median_years_to_b150'):.0f}" for r in "ABC"), new=" / ".join(f"{v(n,r,'median_years_to_b150'):.0f}" for r in "ABC")))
out = pd.DataFrame(rows)
out.to_csv(NEW / "old_vs_new_findings.csv", index=False)
for f, g in out.groupby("finding", sort=True):
    print(f"\n##### Finding {f}")
    print(g.drop(columns="finding").to_string(index=False))
