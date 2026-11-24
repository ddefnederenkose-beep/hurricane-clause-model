"""Revised-brief runs (items 1-7 of the v3 request). Usage: python run_v3.py
Writes outputs/v3/tables/*.csv (full precision), outputs/figures/figure1_v3.png and docs/RESULTS_v3.md.
Does not touch any baseline table: it only READS exp1_baseline_v1.csv / exp3_repay_switch_points.csv /
exp3_reconstruction_check.csv to assert that the new code reproduces them."""
import pathlib, time
import numpy as np
import pandas as pd
from src import config, experiments, hurricanes, v3, plots_v3, results_v3

ROOT = pathlib.Path(__file__).parent


def main():
    t0 = time.time()
    params, sim, _ = config.load_calibration()
    scenarios, _ = config.load_scenarios()
    designs, _ = config.load_designs()
    main_sc = config.main_scenarios(scenarios)
    cfg3 = config.load_v3()
    N, T, seed = sim["N"], sim["T"], sim["seed"]
    out = ROOT / "outputs" / "v3" / "tables"
    out.mkdir(parents=True, exist_ok=True)
    draws = hurricanes.draw_noise(seed, N, T)

    # ---- tables 1-5: one paired grid (scenario x design x version x schedule)
    grid = v3.run_grid(params, main_sc, designs, draws, N, T, v3=cfg3)
    grid.to_csv(out / "grid_seed42.csv", index=False)

    # ---- reproduction check against the untouched baseline table (5-yr equal-instalment rows)
    e1 = pd.read_csv(ROOT / "outputs" / "tables" / "exp1_baseline_v1.csv")
    chk = []
    for r in grid[(grid.schedule == "5yr") & (grid.version == 1)].itertuples():
        old = e1[(e1.scenario == r.scenario) & (e1.design == r.design)].set_index("regime")
        chk.append(abs(old.loc["A", "p_hcrisis_any"] - r.stress_mean_a) + abs(old.loc["B", "p_hcrisis_any"] - r.stress_mean_b)
                   + abs(old.loc["A", "peak_gfn2_mean"] - r.peak2_A) + abs(old.loc["B", "peak_gfn2_mean"] - r.peak2_B)
                   + abs(old.loc["A", "peak_gfn6_mean"] - r.peak6_A) + abs(old.loc["B", "peak_gfn6_mean"] - r.peak6_B))
    repro = float(max(chk))
    assert repro < 1e-9, f"baseline not reproduced (max abs diff {repro})"
    print("baseline reproduction (exp1_baseline_v1.csv, 8 cells, P(stress) + peaks): max abs diff", repro)

    # ---- table 3: break-evens
    hc = designs["barbados_style"]
    lump = v3.lump_breakeven_sweep(params, main_sc, hc, draws, N, T)
    lump.to_csv(out / "lump_sweep_seed42.csv", index=False)
    first = v3.first_negative_L(lump)
    eqb = v3.equal_instalment_breakeven(params, main_sc, hc, draws, N, T)
    eqb.to_csv(out / "equal_instalment_breakeven_seed42.csv", index=False)
    old = pd.read_csv(ROOT / "outputs" / "tables" / "exp3_repay_switch_points.csv")
    old = old[(old.metric == "benefit_p_hcrisis_any") & (old.repay_rule == "equal_instalments") & (old.design == "barbados_style")]
    m = eqb.merge(old, on=["design", "scenario", "version"], suffixes=("", "_old"))
    assert np.allclose(m.switch_years, m.switch_years_old), "equal-instalment break-evens not reproduced"
    print("equal-instalment break-evens reproduced:", m[["scenario", "version", "switch_years"]].round(2).values.tolist())

    # ---- table 6: K-vs-R grid (Grenada-like)
    gl = {"grenada_like": main_sc["grenada_like"]}
    rk = experiments.experiment_reconstruction_check(params, gl, designs, draws, N, T, r_grid=(2, 3, 4), k_grid=(1, 2, 3, 4))
    rk.to_csv(out / "k_vs_r_grid_seed42.csv", index=False)
    oldrk = pd.read_csv(ROOT / "outputs" / "tables" / "exp3_reconstruction_check.csv")
    mm = rk.merge(oldrk, on=["R", "design", "scenario", "version", "K"], suffixes=("", "_old"))
    assert len(mm) == len(rk) and np.allclose(mm.benefit_p_hcrisis_any, mm.benefit_p_hcrisis_any_old), "K-vs-R grid not reproduced"
    print("K-vs-R grid reproduced:", len(rk), "cells")

    # ---- robustness: seeds 43 and 44 (high-coverage, Grenada-like, tables 2 and 4)
    seeds = {seed: grid[(grid.design == "barbados_style") & (grid.scenario == "grenada_like")]}
    for s in (43, 44):
        d = hurricanes.draw_noise(s, N, T)
        g = v3.run_grid(params, {"grenada_like": main_sc["grenada_like"]}, {"barbados_style": hc}, d, N, T, v3=cfg3)
        g.to_csv(out / f"grid_seed{s}_hc_grenada_like.csv", index=False)
        seeds[s] = g

    plots_v3.figure1(grid, eqb, N, T, seed, ROOT / "outputs" / "figures" / "figure1_v3.png")
    results_v3.write(ROOT / "docs" / "RESULTS_v3.md", grid, lump, first, eqb, rk, seeds, cfg3, N, T, seed, repro)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
