"""Run every implemented experiment and write tables/figures. Usage: python run_all.py [--seed 42]"""
import argparse, pathlib, time
import pandas as pd
from src import config, hurricanes, experiments

ROOT = pathlib.Path(__file__).parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()
    t0 = time.time()
    params, sim, ph = config.load_calibration()
    scenarios, ph_s = config.load_scenarios()
    print(config.placeholder_warning(ph + ph_s))
    for s in scenarios.values():
        config.check_units(params, s)
    seed = a.seed if a.seed is not None else sim["seed"]
    N, T = sim["N"], sim["T"]
    draws = hurricanes.draw_noise(seed, N, T)  # one set of hurricane histories used everywhere (CRN)
    tables = ROOT / "outputs" / "tables"
    tables.mkdir(parents=True, exist_ok=True)

    exp1 = experiments.experiment_baseline(params, scenarios, draws, version=1, n_paths=N, horizon=T)
    exp1.to_csv(tables / "exp1_baseline_v1.csv", index=False)
    pd.set_option("display.width", 220, "display.max_columns", 30, "display.float_format", "{:.3f}".format)
    print("\nExperiment 1: baseline (Version 1, exogenous rate), seed", seed)
    print(exp1.to_string(index=False))
    print(f"\nShare of paths with negative debt, by scenario (A): "
          + ", ".join(f"{r.scenario}={r.share_paths_negative_debt:.3f}" for r in exp1[exp1.regime == 'A'].itertuples()))
    exp2 = experiments.experiment_baseline(params, scenarios, draws, version=2, n_paths=N, horizon=T)
    exp2.to_csv(tables / "exp2_endogenous_premium_v2.csv", index=False)
    print("\nExperiment 2: endogenous risk premium (Version 2), same hurricane draws")
    print(exp2.to_string(index=False))
    t1 = time.time()
    h = experiments.experiment_heatmaps(params, scenarios, draws, n_paths=N, horizon=T)
    h.to_csv(tables / "exp3_heatmap_grid.csv", index=False)
    d = experiments.experiment_design_sensitivity(params, scenarios, draws, n_paths=N, horizon=T)
    d.to_csv(tables / "exp3_design_sensitivity.csv", index=False)
    print(f"\nExperiment 3: heatmap grid ({len(h)} cells) and design sensitivity ({len(d)} rows) saved ({time.time()-t1:.0f}s)")
    cols = ["scenario", "version", "regime", "n_spells", "relief_pct_gdp_mean", "relief_pct_gdp_p95",
            "relief_pct_damage_mean", "relief_pct_damage_median"]
    e4 = pd.concat([experiments.experiment_npv_relief(params, scenarios, draws, version=v, n_paths=N, horizon=T)
                    for v in (1, 2)])
    e4.to_csv(tables / "exp4_npv_relief.csv", index=False)
    print("\nExperiment 4: PV of relief per triggered event (B: deferral; C: forgiveness). "
          "Consistency check B-relief == PV(A svc)-PV(B svc) passed (version 1).")
    print(e4[cols].to_string(index=False))
    print("\nExperiment 5: grenada_relief() is available in src/grenada.py (no Grenada numbers entered).")
    print(f"Finished in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
