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


# ---------------------------------------------------------------------------------------------------------
# Experiment 3: sensitivity of the clause's benefit (Regime A minus Regime B; positive = clause helps)
# ---------------------------------------------------------------------------------------------------------
import numpy as np
from . import hurricanes  # noqa: E402

B0_GRID = np.linspace(40, 140, 9)
LAMBDA_GRID = np.array([0.03, 0.05, 0.08, 0.10, 0.13, 0.16, 0.20, 0.25])


def scenario_for_b0(b0, scenarios):
    """Heatmap scenario: initial debt b0 with the primary balance interpolated linearly between the two
    scenario anchors (grenada_like: b0=65, pd=-2 ; high_debt: b0=110, pd=+1), so higher debt comes with a
    weaker primary balance instead of an implausible large surplus (DECISIONS #20)."""
    g, h = scenarios["grenada_like"], scenarios["high_debt"]
    pd_bar = g["pd_bar"] + (b0 - g["b_0"]) * (h["pd_bar"] - g["pd_bar"]) / (h["b_0"] - g["b_0"])
    return {"name": f"b0={b0:.0f}", "b_0": float(b0), "pd_bar": float(pd_bar)}


def _benefit(simA, simB, params, baseline):
    mA, mB = metrics.summarize(simA, params, baseline), metrics.summarize(simB, params, baseline)
    out = {}
    for k in ("peak_gfn2_mean", "peak_gfn6_mean", "p_crisis_any", "mean_crisis_years", "p_hcrisis_any", "bT_mean"):
        out[f"benefit_{k}"] = mA[k] - mB[k]
    out["A_peak_gfn2_mean"], out["B_peak_gfn2_mean"] = mA["peak_gfn2_mean"], mB["peak_gfn2_mean"]
    out["A_p_crisis_any"], out["B_p_crisis_any"] = mA["p_crisis_any"], mB["p_crisis_any"]
    return out


def experiment_heatmaps(params, scenarios, draws, versions=(1, 2), n_paths=10000, horizon=30):
    """Grid over initial debt b0 x hurricane probability lambda. Same hurricane draws in every cell."""
    rows = []
    for v in versions:
        for b0 in B0_GRID:
            scen = scenario_for_b0(b0, scenarios)
            base = baseline_gfn_path(params, scen, v, horizon)
            for lam in LAMBDA_GRID:
                p = {**params, "lambda": float(lam)}
                A = simulate.simulate(p, scen, "A", v, draws=draws, n_paths=n_paths, horizon=horizon)
                B = simulate.simulate(p, scen, "B", v, draws=draws, n_paths=n_paths, horizon=horizon)
                rows.append({"version": v, "b_0": b0, "pd_bar": scen["pd_bar"], "lambda": lam,
                             **_benefit(A, B, p, base)})
    return pd.DataFrame(rows)


def experiment_design_sensitivity(params, scenarios, draws, versions=(1, 2), n_paths=10000, horizon=30,
                                  dtrig_grid=(2, 5, 10, 20), k_grid=(1, 2, 3, 4), mrep_grid=(2, 4, 6, 8, 12)):
    """Sensitivity to clause design: (D_trig x K) at default defer_repay_years, and (K x defer_repay_years)
    at default D_trig. Benefit = A minus B."""
    combos = [(dt, k, params["defer_repay_years"]) for dt in dtrig_grid for k in k_grid]
    combos += [(params["D_trig"], k, m) for k in k_grid for m in mrep_grid]
    combos = list(dict.fromkeys(combos))
    rows = []
    for sname, scen in scenarios.items():
        for v in versions:
            base = baseline_gfn_path(params, scen, v, horizon)
            for dt, k, m in combos:
                p = {**params, "D_trig": dt, "K": k, "defer_repay_years": m}
                A = simulate.simulate(p, scen, "A", v, draws=draws, n_paths=n_paths, horizon=horizon)
                B = simulate.simulate(p, scen, "B", v, draws=draws, n_paths=n_paths, horizon=horizon)
                rows.append({"scenario": sname, "version": v, "D_trig": dt, "K": k, "defer_repay_years": m,
                             **_benefit(A, B, p, base)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------------------------
# Experiment 4: NPV of relief per triggered event (spell)
# ---------------------------------------------------------------------------------------------------------
def _spells(sim, relief, r, d_trig):
    """One record per suspension spell (consecutive suspended years; a restart inside a window extends the spell).
    Returns arrays (pv_pct_gdp_at_start, pct_of_damage). Relief and damage are discounted at r to the spell start;
    relief in % of GDP at the start year, damage = sum of triggering hits in the spell (same discounting)."""
    D = sim["D"]; N, T = D.shape
    Y = np.cumprod(1.0 + sim["g"][:, 1:], axis=1)                      # GDP level in years 1..T (Y_0 = 1)
    DF = (1.0 + r) ** -np.arange(1, T + 1)
    susp = sim["suspended"][:, 1:]
    rel = np.nan_to_num(sim[relief][:, 1:])
    acc_pv = np.zeros(N); acc_dmg = np.zeros(N); base = np.zeros(N)
    out_gdp, out_dmg = [], []
    prev = np.zeros(N, dtype=bool)

    def record(mask):
        if mask.any():
            out_gdp.append(acc_pv[mask] / base[mask])
            out_dmg.append(100.0 * acc_pv[mask] / np.maximum(acc_dmg[mask], 1e-12))

    for t in range(T):
        record(prev & ~susp[:, t])                                        # spell ended last year
        start = susp[:, t] & ~prev
        acc_pv = np.where(start, 0.0, acc_pv); acc_dmg = np.where(start, 0.0, acc_dmg)
        base = np.where(start, Y[:, t] * DF[t], base)
        acc_pv = acc_pv + np.where(susp[:, t], rel[:, t] * Y[:, t] * DF[t], 0.0)
        acc_dmg = acc_dmg + np.where(susp[:, t] & (D[:, t] >= d_trig), D[:, t] * Y[:, t] * DF[t], 0.0)
        prev = susp[:, t]
    record(prev)                                                          # spells still open at T
    if not out_gdp:
        return np.array([]), np.array([])
    return np.concatenate(out_gdp), np.concatenate(out_dmg)


def _pv0(x, Y, r):
    T = Y.shape[1]
    return (np.nan_to_num(x[:, 1:]) * Y * (1.0 + r) ** -np.arange(1, T + 1)).sum(axis=1)


def experiment_npv_relief(params, scenarios, draws, version=1, n_paths=10000, horizon=30):
    """Present value of cash-flow relief per triggered event (spell), discounted at r_bar.
    Regime B relief = suspended service (interest + amortization on covered debt) that is not paid;
    Regime C relief = forgiven service. CONSISTENCY CHECK (version 1, defer_repay_years = M): the PV of B's relief
    must equal PV(A service) - PV(B service), the same quantity test 2 verifies; asserted path by path."""
    r = params["r_bar"]
    rows = []
    for sname, scen in scenarios.items():
        runs = simulate.run_regimes(params, scen, version, draws=draws, n_paths=n_paths, horizon=horizon)
        A, B, C = runs["A"], runs["B"], runs["C"]
        Y = np.cumprod(1.0 + A["g"][:, 1:], axis=1)
        if version == 1 and params["defer_repay_years"] == params["M"]:
            svc = lambda s: s["interest"] + s["amort"]
            lhs = _pv0(B["skipped"], Y, r)
            rhs = _pv0(svc(A), Y, r) - _pv0(svc(B), Y, r)
            np.testing.assert_allclose(lhs, rhs, rtol=1e-9, atol=1e-9,
                                       err_msg="Experiment 4 relief != discounted suspended service (test 2 quantity)")
        for reg, sim, key in (("B", B, "skipped"), ("C", C, "forgiven")):
            pv_gdp, pct_dmg = _spells(sim, key, r, params["D_trig"])
            rows.append({"scenario": sname, "version": version, "regime": reg, "n_spells": int(pv_gdp.size),
                         "relief_pct_gdp_mean": pv_gdp.mean(), "relief_pct_gdp_median": np.median(pv_gdp),
                         "relief_pct_gdp_p5": np.percentile(pv_gdp, 5), "relief_pct_gdp_p95": np.percentile(pv_gdp, 95),
                         "relief_pct_damage_mean": pct_dmg.mean(), "relief_pct_damage_median": np.median(pct_dmg),
                         "relief_pct_damage_p5": np.percentile(pct_dmg, 5),
                         "relief_pct_damage_p95": np.percentile(pct_dmg, 95)})
    return pd.DataFrame(rows)
