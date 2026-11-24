"""v4 analyses (RESULTS_v4): lump-sum diagnostics, refinanced lump, robustness of the two conclusions that now drive the brief,
and the Beryl validation. NEW code only; no parameter and no baseline result is changed (run_v4.py asserts reproduction of v3)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from . import config, experiments, metrics, simulate, v3

BERYL_DAMAGE = 16.5     # % of GDP, IMF CR 25/39 para 8 (already in calibration.yaml notes)
BERYL_PAYOUT = 3.2      # CCRIF payout to central government, % of GDP (already netted inside kappa = 0.42)
IMF_DEBT = {1: 72.7, 2: 68.3, 3: 65.8}   # IMF CR 26/9 Table 1 p.26: public debt incl. SOEs, 2024 actual / 2025e / 2026p
IMF_PB = {1: 10.0, 2: -3.2, 3: -3.5}     # primary balance, same table (parameter_sourcing_register.md Task 6)


def _design(params, designs, name):
    return config.design_params(params, designs[name])


# ----------------------------------------------------------------------------------------------- B1 / B2: lump-sum diagnostics
def first_lump(sim):
    """For each path: (paid?, year index 0..T-1 of the first positive deferred-balance repayment, its size in % of GDP_t)."""
    c = np.nan_to_num(sim["catchup"][:, 1:])
    pos = c > 1e-9
    has = pos.any(axis=1)
    idx = pos.argmax(axis=1)
    amt = c[np.arange(c.shape[0]), idx]
    return has, idx, np.where(has, amt, np.nan)


def lump_diagnostics(params, scen, design, version, draws, N, T, v3cfg):
    """Grenada-like (or any scenario) lump-sum case: size of the lump, GFN > GFN_crit in the lump year and in any year,
    for no clause (A), the 5-yr instalment clause and B'-lump, plus P(stress) at larger thresholds (points above the no-storm path)."""
    p0 = params_for(params, design)
    A = simulate.simulate(p0, scen, "A", version, draws=draws, n_paths=N, horizon=T)
    I = simulate.simulate(p0, scen, "B", version, draws=draws, n_paths=N, horizon=T)
    pl = v3.schedule_params(p0, "lump", v3cfg["bprime_horizon"])
    L = simulate.simulate(pl, scen, "B", version, draws=draws, n_paths=N, horizon=T)
    has, idx, amt = first_lump(L)
    strike = (L["D"] >= p0["D_trig"]).any(axis=1)
    rows = np.arange(N)
    crit = p0["GFN_crit"]
    # total service SKIPPED (interest + amortization, % of GDP in each skipped year) during the first suspension window
    K = int(p0["K"])
    i0 = (L["D"] >= p0["D_trig"]).argmax(axis=1)
    okk = strike & (i0 + K <= T)
    skipped_first = np.array([np.nansum(L["skipped"][n, i0[n] + 1: i0[n] + 1 + K]) for n in np.flatnonzero(okk)])
    out = {"skipped_first_mean": float(skipped_first.mean()), "skipped_first_median": float(np.median(skipped_first)),
           "n_paths": N, "n_strike_paths": int(strike.sum()), "n_lump_paid_within_T": int(has.sum()),
           "lump_mean": float(np.nanmean(amt)), "lump_median": float(np.nanmedian(amt)),
           "lump_p90": float(np.nanpercentile(amt, 90))}
    for lab, s in (("A", A), ("inst", I), ("lump", L)):
        g = s["gfn"][:, 1:]
        out[f"p15_year_{lab}"] = float((g[rows, idx] > crit)[has].mean())          # conditional on a lump falling due in the window
        out[f"p15_year_{lab}_unc"] = float((g[rows, idx] > crit)[has].sum() / N)    # as a share of ALL paths
        out[f"p15_any_{lab}"] = float((g > crit).any(axis=1).mean())
        out[f"gfn_lumpyear_mean_{lab}"] = float(g[rows, idx][has].mean())
    baseL = experiments.baseline_gfn_path(pl, scen, version, T, "B")
    baseA = experiments.baseline_gfn_path(p0, scen, version, T, "A")
    for m in (5, 10, 15):
        fA = (v3.excess_gfn(A, baseA, np.full(A["D"].shape, float(m))) > 0).any(axis=1)
        fL = (v3.excess_gfn(L, baseL, np.full(L["D"].shape, float(m))) > 0).any(axis=1)
        out[f"stress{m}_A"], out[f"stress{m}_lump"] = float(fA.mean()), float(fL.mean())
    # peak GFN over t..t+6 (the lump falls due in t+6, OUTSIDE the t..t+5 window of Figure 1)
    out["peak7_A"] = float(metrics.event_peak_gfn(A, p0["D_trig"], 7).mean())
    out["peak7_inst"] = float(metrics.event_peak_gfn(I, p0["D_trig"], 7).mean())
    out["peak7_lump"] = float(metrics.event_peak_gfn(L, p0["D_trig"], 7).mean())
    return out


def params_for(params, design):
    return config.design_params(params, design)


# ------------------------------------------------------------------------------------------------------------- C: robustness
VARIANTS = {"base": {}, "median x0.75": {"damage_mult": 0.75}, "median x1.25": {"damage_mult": 1.25},
            "+25 bp delay premium": {"deferral_premium_on": 1}}


def variant_params(params, spec):
    p = dict(params)
    if "damage_mult" in spec:
        p["mu_D"] = float(np.log(np.exp(params["mu_D"]) * spec["damage_mult"]))   # same method as docs/damage_median_sign_test.py
    for k, v in spec.items():
        if k != "damage_mult":
            p[k] = v
    return p


def robustness(params, scenarios, designs, draws, N, T, v3cfg):
    """Grid under each variant: (i) B'-lump on the standard stress measure, (ii) 5-yr instalments on the 3-pt storm-window measure."""
    frames = []
    for name, spec in VARIANTS.items():
        g = v3.run_grid(variant_params(params, spec), scenarios, designs, draws, N, T, schedules=("5yr", "lump"), v3=v3cfg)
        frames.append(g.assign(variant=name))
    return pd.concat(frames, ignore_index=True)


# ------------------------------------------------------------------------------------------------------------ D: Beryl validation
def beryl(params, scen, design, version, regime="A", schedule="5yr", kappa=None, inflow=0.0, horizon=5, bprime_horizon=6):
    """One deterministic strike in year 1 (= 2024), damage 16.5% of GDP, no other storms. Returns model debt, GFN and primary
    balance for years 1..3 (2024-26). Nothing in config is modified: kappa is overridden in a COPY of the parameters."""
    p = params_for(params, design) if design is not None else dict(params)
    if kappa is not None:
        p = {**p, "kappa": kappa}
    if regime == "B":
        p = v3.schedule_params(p, schedule, bprime_horizon)
    s = simulate.simulate(p, scen, regime, version, forced_hits={1: BERYL_DAMAGE}, n_paths=1, horizon=horizon,
                          inflows={1: inflow} if inflow else None)
    return {"debt": s["b"][0, 1:4], "gfn": s["gfn"][0, 1:4], "pb": -s["pd"][0, 1:4], "g": s["g"][0, 1:4], "sim": s}
