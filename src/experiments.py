"""Experiments. Each returns a pandas DataFrame and is saved to outputs/tables by run_all.py."""
from __future__ import annotations
import pandas as pd
from . import hurricanes, metrics, simulate

METRIC_COLS = ["peak_gfn_mean", "peak_gfn_p95", "n_events", "p_crisis_any", "mean_crisis_years",
               "bT_mean", "bT_median", "bT_p5", "bT_p95", "p_bT_gt100", "p_b_gt100_any",
               "share_paths_negative_debt"]


def experiment_baseline(params, scenarios, draws, version=1, n_paths=10000, horizon=30):
    """Experiment 1 (version=1) / 2 (version=2): regimes A/B/C x scenarios on common hurricane draws."""
    rows = []
    for sname, scen in scenarios.items():
        runs = simulate.run_regimes(params, scen, version, draws=draws, n_paths=n_paths, horizon=horizon)
        for reg, sim in runs.items():
            rows.append({"scenario": sname, "version": version, "regime": reg, **metrics.summarize(sim, params)})
    return pd.DataFrame(rows)
