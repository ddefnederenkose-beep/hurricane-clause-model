"""Run every experiment and regenerate all tables and figures. Usage: python run_all.py [--seed 42]"""
import argparse, pathlib, time
import pandas as pd
from src import config, docs_gen, experiments, hurricanes, plots

ROOT = pathlib.Path(__file__).parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--outdir", default=None, help="write tables/figures here instead of outputs/ (docs are then not touched)")
    a = ap.parse_args()
    t0 = time.time()
    params, sim, ph = config.load_calibration()
    scenarios, ph_s = config.load_scenarios()
    designs, ph_d = config.load_designs()
    print(config.placeholder_warning(ph + ph_s + ph_d))
    print("Parameter status counts:", config.status_counts(), "(VERIFIED is reserved for the group)")
    main_sc = config.main_scenarios(scenarios)
    for s in scenarios.values():
        config.check_units(params, s)
    seed = a.seed if a.seed is not None else sim["seed"]
    N, T = sim["N"], sim["T"]
    draws = hurricanes.draw_noise(seed, N, T)       # ONE set of hurricane histories used everywhere (CRN)
    out_root = pathlib.Path(a.outdir) if a.outdir else ROOT / "outputs"
    tables, figs = out_root / "tables", out_root / "figures"
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
            df = experiments.experiment_npv_relief(config.design_params(params, dsg), main_sc, draws, v, N, T,
                                                   allow_nondefault_repay=True)   # baseline rule is equal_instalments, not the identity's scope
            df.insert(0, "design", dn); e4.append(df)
    e4 = pd.concat(e4); e4.to_csv(tables / "exp4_npv_relief.csv", index=False)
    print("\nExperiment 4 (version 1 shown): B = PV of deferred cash flows (timing relief; net transfer ~ 0), "
          "C = PV of debt relief (net transfer). Run with the override flag: the identity PV(B deferred) = PV(A svc) - PV(B svc) "
          "is NOT checked under the baseline repay rule (see net_pv_advantage_vs_A column).")
    print(e4[e4.version == 1][["design", "scenario", "regime", "n_spells", "pv_pct_gdp_mean", "pv_pct_gdp_p95",
                               "pct_damage_mean"]].to_string(index=False))
    print("\nExperiment 5: grenada_relief() in src/grenada.py (no Grenada numbers entered).")

    if not a.no_figures:
        t2 = time.time()
        plots.CAPTIONS.clear(); plots.QA.clear()
        for v in (1, 2):
            data = {}
            for dn, dsg in designs.items():
                p = config.design_params(params, dsg)
                for sn, sc in main_sc.items():
                    base = experiments.baselines(p, sc, v, T)
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
        nfig, nissue = plots.qa_report(figs)
        print(f"\nFigure QA: {nfig} figures, {nissue} issue(s) (see outputs/figures/QA_REPORT.md)")
        print(f"\nFigures written to outputs/figures ({len(plots.CAPTIONS)} files, {time.time()-t2:.0f}s)")
    t4 = time.time()
    sw = experiments.experiment_repay_sweep(params, main_sc, designs, draws, n_paths=N, horizon=T)
    sw.to_csv(tables / "exp3_repay_sweep.csv", index=False)
    sp = pd.concat([experiments.repay_switch_points(sw, c) for c in ("benefit_p_hcrisis_any", "benefit_p_crisis_any", "benefit_peak_gfn6_mean")])
    sp.to_csv(tables / "exp3_repay_switch_points.csv", index=False)
    print(f"\nRepayment-years sweep (2-12) saved ({time.time()-t4:.0f}s). Switch from harmful to helpful (years; hurricane-attributable crisis):")
    print(sp[sp.metric == "benefit_p_hcrisis_any"][["design", "scenario", "version", "repay_rule", "switch_years", "verdict",
                                                  "benefit_at_2y_pp", "benefit_at_12y_pp"]].to_string(index=False))
    t3 = time.time()
    rk = experiments.experiment_reconstruction_check(params, main_sc, designs, draws, n_paths=N, horizon=T)
    rk.to_csv(tables / "exp3_reconstruction_check.csv", index=False)
    jumps = experiments.largest_jump(rk); jumps.to_csv(tables / "exp3_reconstruction_check_jumps.csv", index=False)
    print("\nK-vs-R check (largest rise in clause benefit, hurricane-attributable crisis; K at which it occurs):")
    print(jumps.pivot_table(index=["design", "scenario", "version"], columns="R", values="jump_at_K").to_string())
    infl = experiments.parameter_influence(params, main_sc, designs, draws, n=min(N, 5000), T=T)
    infl.to_csv(tables / "parameter_influence.csv", index=False)
    ptab = docs_gen.status_table(params, scenarios, designs, infl)
    ptab.to_csv(tables / "placeholder_status.csv", index=False)
    print(f"\n(K-vs-R check and parameter sweep: {time.time()-t3:.0f}s)")
    print("\nPARAMETER STATUS TABLE: sourceable parameters first, sorted by influence on P(hurricane-attributable crisis) of Regime B")
    print("(one-at-a-time +-25% sweep, mean |change| in pp over 2 versions x 2 scenarios x 2 designs; set status VERIFIED once sourced)")
    show = ptab[["parameter", "value", "type", "influence_pp", "delta_minus25_pp", "delta_plus25_pp", "status", "note"]]
    print(show.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    if not a.outdir:
        docs_gen.update_methods(ROOT / "docs" / "METHODS.md")
    print(f"Finished in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
