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
    print(f"Finished in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
