"""Robustness check (NOT a re-calibration): does the SIGN of the clause effect survive a +-25% change in the damage median?

Reruns the committed final configuration (commit edc3665) for grenada_like and high_debt, both clause designs (5-year equal
instalments), with the median damage multiplied by 0.75 and 1.25 (mu_D = ln(new median); sigma_D unchanged). The multiplier
1.0 rows reproduce the baseline as a check. Effect = P(hurricane-attributable crisis) with the clause (B) minus without (A).
SE of the difference is the paired standard error over paths (same hurricane draws in A and B).
Usage:  .venv/bin/python docs/damage_median_sign_test.py     (refuses to overwrite an existing output file)
"""
import pathlib, sys
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import config, experiments, hurricanes, simulate  # noqa: E402

OUT = ROOT / "outputs" / "tables" / "damage_median_sign_test.csv"
if OUT.exists():
    sys.exit(f"{OUT} already exists; refusing to overwrite.")

params, sim, _ = config.load_calibration()
scenarios = config.main_scenarios(config.load_scenarios()[0])
designs, _ = config.load_designs()
N, T, seed = sim["N"], sim["T"], sim["seed"]
draws = hurricanes.draw_noise(seed, N, T)
base_median = float(np.exp(params["mu_D"]))
rows = []
for mult in (0.75, 1.0, 1.25):
    mu = float(np.log(base_median * mult))
    p0 = {**params, "mu_D": mu}
    for v in (1, 2):
        for dname, design in designs.items():
            p = config.design_params(p0, design)
            for sname, scen in scenarios.items():
                bases = experiments.baselines(p, scen, v, T)
                flag = {}
                for reg in ("A", "B"):
                    s = simulate.simulate(p, scen, reg, v, draws=draws, n_paths=N, horizon=T)
                    flag[reg] = (s["gfn"][:, 1:] > bases[reg][..., 1:] + p["GFN_margin"]).any(axis=1)
                a, b = flag["A"].mean(), flag["B"].mean()
                se = float(np.std(flag["B"].astype(float) - flag["A"].astype(float), ddof=1) / np.sqrt(N))
                rows.append({"version": v, "scenario": sname, "design": dname, "damage_median_multiplier": mult,
                             "median_damage_pct_gdp": base_median * mult, "mu_D": mu, "sigma_D": p["sigma_D"],
                             "p_hac_no_clause_pct": 100 * a, "p_hac_clause_pct": 100 * b,
                             "diff_clause_minus_no_clause_pp": 100 * (b - a), "se_diff_pp": 100 * se})
df = pd.DataFrame(rows)
df["sign"] = np.sign(df["diff_clause_minus_no_clause_pp"]).map({1.0: "clause worse", -1.0: "clause better", 0.0: "no difference"})
ref = df[df.damage_median_multiplier == 1.0].set_index(["version", "scenario", "design"])["sign"]
df["sign_same_as_baseline"] = [ref[(r.version, r.scenario, r.design)] == r.sign for r in df.itertuples()]
df["effect_exceeds_2se"] = df["diff_clause_minus_no_clause_pp"].abs() > 2 * df["se_diff_pp"]
df.to_csv(OUT, index=False)
pd.set_option("display.width", 250, "display.max_columns", 30, "display.float_format", "{:.2f}".format)
print(df.drop(columns=["mu_D", "sigma_D", "median_damage_pct_gdp"]).to_string(index=False))
