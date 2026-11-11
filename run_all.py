"""Run every experiment and regenerate all tables and figures. Usage: python run_all.py [--seed 42]"""
import argparse, pathlib, time
import pandas as pd
from src import config, docs_gen, experiments, hurricanes, plots

ROOT = pathlib.Path(__file__).parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--no-figures", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    params, sim, ph = config.load_calibration()
    scenarios, ph_s = config.load_scenarios()
    designs, ph_d = config.load_designs()
    print(config.placeholder_warning(ph + ph_s + ph_d))
    main_sc = config.main_scenarios(scenarios)
    for s in scenarios.values():
        config.check_units(params, s)
    seed = a.seed if a.seed is not None else sim["seed"]
    N, T = sim["N"], sim["T"]
    draws = hurricanes.draw_noise(seed, N, T)       # ONE set of hurricane histories used everywhere (CRN)
    tables, figs = ROOT / "outputs" / "tables", ROOT / "outputs" / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.float_format", "{:.3f}".format)
    short = ["design", "scenario", "regime", "peak_gfn2_mean", "peak_gfn6_mean", "p_crisis_any", "p_hcrisis_any",
             "mean_crisis_years", "bT_median", "p_bT_gt100", "median_years_to_b150", "share_paths_cap_ever",
             "share_pathyears_cap_binds"]

    exp = {}
    for v, name in ((1, "exp1_baseline_v1"), (2, "exp2_endogenous_premium_v2")):
        exp[v] = experiments.experiment_baseline(params, scenarios, designs, draws, v, N, T)
        exp[v].to_csv(tables / f"{name}.csv", index=False)
        print(f"\nExperiment {v}: {'baseline, exogenous rate (Version 1)' if v == 1 else 'endogenous risk premium (Version 2)'}; seed {seed}")
        print(exp[v][short].to_string(index=False))
    prem = experiments.experiment_baseline({**params, "deferral_premium_on": 1}, scenarios, designs, draws, 1, N, T)
    prem.to_csv(tables / "exp1_deferral_premium_on_v1.csv", index=False)
    print(f"\nExperiment 1 robustness: deferral-risk premium ON ({params['deferral_spread']*1e4:.0f} bps on covered debt, B/C only)")
    print(prem[prem.regime != "A"][short + ["bT_mean"]].to_string(index=False))
    neg = pd.concat(exp.values())
    print("\nShare of paths with negative debt (max over rows): %.4f" % neg.share_paths_negative_debt.max())

    t1 = time.time()
    h = experiments.experiment_heatmaps(params, main_sc, designs, draws, n_paths=N, horizon=T)
    h.to_csv(tables / "exp3_heatmap_grid.csv", index=False)
    d = experiments.experiment_design_sensitivity(params, main_sc, designs, draws, n_paths=N, horizon=T)
    d.to_csv(tables / "exp3_design_sensitivity.csv", index=False)
    print(f"\nExperiment 3: heatmap grid ({len(h)} cells) and design sensitivity ({len(d)} rows) saved ({time.time()-t1:.0f}s)")

    e4 = []
    for dn, dsg in designs.items():
        for v in (1, 2):
            df = experiments.experiment_npv_relief(config.design_params(params, dsg), main_sc, draws, v, N, T)
            df.insert(0, "design", dn); e4.append(df)
    e4 = pd.concat(e4); e4.to_csv(tables / "exp4_npv_relief.csv", index=False)
    print("\nExperiment 4 (version 1 shown): B = PV of deferred cash flows (timing relief; net transfer ~ 0), "
          "C = PV of debt relief (net transfer). Identity check PV(B deferred) = PV(A svc) - PV(B svc) passed (v1, default repay rule).")
    print(e4[e4.version == 1][["design", "scenario", "regime", "n_spells", "pv_pct_gdp_mean", "pv_pct_gdp_p95",
                               "pct_damage_mean"]].to_string(index=False))
    print("\nExperiment 5: grenada_relief() in src/grenada.py (no Grenada numbers entered).")

    if not a.no_figures:
        t2 = time.time()
        plots.CAPTIONS.clear()
        for v in (1, 2):
            data = {}
            for dn, dsg in designs.items():
                p = config.design_params(params, dsg)
                for sn, sc in main_sc.items():
                    base = experiments.baseline_gfn_path(p, sc, v, T)
                    data[(sn, dn)] = plots.collect(p, sc, v, draws, N, T, base)
            p0 = params
            plots.fan_charts(data, p0, figs, v, N, T, seed)
            plots.event_window_chart(data, figs, v, N, T, seed)
            plots.event_window_chart(data, figs, v, N, T, seed, clean=True)
            plots.bar_charts(data, figs, v, N, T, seed)
            if v == 1:
                for (sn, dn), dd in data.items():
                    plots.sample_path(dd, config.design_params(params, designs[dn]), figs, f"sample_path_{sn}_{dn}",
                                      f"Sample path: {plots.SLAB[sn]}, {plots.DLAB[dn]}", T, seed)
        plots.heatmaps(h, figs, N, T, seed)
        plots.design_heatmaps(d, figs, N, T, seed)
        plots.design_heatmaps(d, figs, N, T, seed, "benefit_peak_gfn6_mean", "reduction in mean peak GFN over t..t+5 (pp of GDP)", "peak6", 1.0)
        plots.write_captions(figs)
        print(f"\nFigures written to outputs/figures ({len(plots.CAPTIONS)} files, {time.time()-t2:.0f}s)")
    docs_gen.update_methods(ROOT / "docs" / "METHODS.md")
    print(f"Finished in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
