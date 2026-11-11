"""Experiments. Each returns a pandas DataFrame and is saved to outputs/tables by run_all.py."""
from __future__ import annotations
import pandas as pd
from . import metrics, simulate


def baseline_gfn_path(params, scenario, version, horizon):
    """No-hurricane GFN path (deterministic; identical for all regimes because nothing is ever triggered)."""
    sim = simulate.simulate({**params, "lambda": 0.0}, scenario, "A", version, forced_hits={},
                            n_paths=1, horizon=horizon)
    return sim["gfn"]


def experiment_baseline(params, scenarios, draws, version=1, n_paths=10000, horizon=30):
    """Experiment 1 (version=1) / 2 (version=2): regimes A/B/C x scenarios on common hurricane draws."""
    rows = []
    for sname, scen in scenarios.items():
        base = baseline_gfn_path(params, scen, version, horizon)
        runs = simulate.run_regimes(params, scen, version, draws=draws, n_paths=n_paths, horizon=horizon)
        for reg, sim in runs.items():
            rows.append({"scenario": sname, "version": version, "regime": reg,
                         **metrics.summarize(sim, params, base)})
    return pd.DataFrame(rows)
