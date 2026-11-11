"""Experiments. Each returns a pandas DataFrame and is saved to outputs/tables by run_all.py.

All outputs are labelled by clause DESIGN ('grenada_style', 'barbados_style'; see config/designs.yaml) and, where
relevant, scenario and model version. Regime A does not depend on the design (no clause), so its rows repeat.
Every function takes the same `draws` (common random numbers across regimes, versions, designs and grid cells).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from . import config, metrics, simulate

B0_GRID = np.linspace(40, 140, 9)
LAMBDA_GRID = np.array([0.03, 0.05, 0.08, 0.10, 0.13, 0.16, 0.20, 0.25])


def baseline_gfn_path(params, scenario, version, horizon):
    """No-hurricane GFN path (deterministic; identical for all regimes because nothing is ever triggered)."""
    sim = simulate.simulate(params, scenario, "A", version, forced_hits={}, n_paths=1, horizon=horizon)
    return sim["gfn"]


# ----------------------------------------------------------------------------------------- experiments 1 and 2
def experiment_baseline(params, scenarios, designs, draws, version=1, n_paths=10000, horizon=30):
    """Experiment 1 (version=1) / 2 (version=2): regimes A/B/C x scenarios x designs on common hurricane draws.
    With params['deferral_premium_on'] = 1 this is the robustness table with the deferral-risk premium."""
    rows = []
    for dname, design in designs.items():
        p = config.design_params(params, design)
        for sname, scen in scenarios.items():
            base = baseline_gfn_path(p, scen, version, horizon)
            runs = simulate.run_regimes(p, scen, version, draws=draws, n_paths=n_paths, horizon=horizon)
            for reg, sim in runs.items():
                rows.append({"design": dname, "scenario": sname, "version": version, "regime": reg,
                             "deferral_premium_on": int(p.get("deferral_premium_on", 0)),
                             **metrics.summarize(sim, p, base)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------- experiment 3
def scenario_for_b0(b0, scenarios):
    """Heatmap scenario: initial debt b0 with the primary balance interpolated linearly between the two scenario
    anchors (grenada_like: b0=65, pd=-2 ; high_debt: b0=110, pd=+1). The debt axis therefore varies the fiscal
    stance jointly: a VULNERABILITY gradient, not a pure debt gradient (DECISIONS #20)."""
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


def experiment_heatmaps(params, scenarios, designs, draws, versions=(1, 2), n_paths=10000, horizon=30):
    """Benefit (A minus B; positive = clause helps) over initial debt b0 x hurricane probability lambda."""
    rows = []
    for v in versions:
        for b0 in B0_GRID:
            scen = scenario_for_b0(b0, scenarios)
            for lam in LAMBDA_GRID:
                pl = {**params, "lambda": float(lam)}
                base = baseline_gfn_path(pl, scen, v, horizon)
                A = simulate.simulate(pl, scen, "A", v, draws=draws, n_paths=n_paths, horizon=horizon)
                for dname, design in designs.items():
                    p = config.design_params(pl, design)
                    B = simulate.simulate(p, scen, "B", v, draws=draws, n_paths=n_paths, horizon=horizon)
                    rows.append({"design": dname, "version": v, "b_0": b0, "pd_bar": scen["pd_bar"],
                                 "lambda": lam, **_benefit(A, B, p, base)})
    return pd.DataFrame(rows)


def experiment_design_sensitivity(params, scenarios, designs, draws, versions=(1, 2), n_paths=10000, horizon=30,
                                  dtrig_grid=(2, 5, 10, 20), k_grid=(1, 2, 3, 4), mrep_grid=(2, 4, 6, 8, 12)):
    """Sensitivity to clause design: (D_trig x K) at the design's own repayment speed, and (K x defer_repay_years)
    at the default D_trig. Benefit = A minus B."""
    rows = []
    for dname, design in designs.items():
        p0 = config.design_params(params, design)
        combos = [(dt, k, p0["defer_repay_years"]) for dt in dtrig_grid for k in k_grid]
        combos += [(p0["D_trig"], k, m) for k in k_grid for m in mrep_grid]
        combos = list(dict.fromkeys(combos))
        for sname, scen in scenarios.items():
            for v in versions:
                base = baseline_gfn_path(p0, scen, v, horizon)
                A = simulate.simulate(p0, scen, "A", v, draws=draws, n_paths=n_paths, horizon=horizon)
                for dt, k, m in combos:
                    p = {**p0, "D_trig": dt, "K": k, "defer_repay_years": m}
                    B = simulate.simulate(p, scen, "B", v, draws=draws, n_paths=n_paths, horizon=horizon)
                    rows.append({"design": dname, "scenario": sname, "version": v, "D_trig": dt, "K": k,
                                 "defer_repay_years": m, **_benefit(A, B, p, base)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------- experiment 4
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


MEASURE = {"B": "PV of deferred cash flows (timing relief; net transfer ~ 0)",
           "C": "PV of debt relief (net transfer)"}


def experiment_npv_relief(params, scenarios, draws, version=1, n_paths=10000, horizon=30,
                          allow_nondefault_repay=False):
    """Present value of relief per triggered event (suspension spell), discounted at r_bar.

    Two DIFFERENT quantities are reported and must not be compared as like with like:
      Regime B: PV of deferred cash flows = suspended interest + amortization on covered debt. A timing/liquidity
                item; the debt stock equals Regime A's, so the net transfer is ~ 0. Reported as % of GDP per
                spell only.
      Regime C: PV of debt relief = forgiven service. A genuine net transfer. Reported as % of GDP and % of damage.
    SCOPE: the identity  PV(B deferred cash flows) = PV(A service) - PV(B service)  holds only under the default
    repayment rule (defer_repay_years = M, no deferral premium, version 1), where skipped service is never made up in
    gross terms. It is asserted path by path in that case. Running with another repayment speed (or the premium on)
    raises unless allow_nondefault_repay=True, in which case the assertion is skipped and B's figure is only the
    suspended service, NOT the net cash advantage over A."""
    if (params["defer_repay_years"] != params["M"] or params.get("deferral_premium_on", 0)) \
            and not allow_nondefault_repay:
        raise ValueError("Experiment 4 is scoped to defer_repay_years == M and deferral_premium_on == 0. "
                         "Pass allow_nondefault_repay=True to run it anyway (identity check is then skipped).")
    r = params["r_bar"]
    scoped = (version == 1 and params["defer_repay_years"] == params["M"] and not params.get("deferral_premium_on", 0))
    rows = []
    for sname, scen in scenarios.items():
        runs = simulate.run_regimes(params, scen, version, draws=draws, n_paths=n_paths, horizon=horizon)
        A, B, C = runs["A"], runs["B"], runs["C"]
        Y = np.cumprod(1.0 + A["g"][:, 1:], axis=1)
        if scoped:
            svc = lambda s: s["interest"] + s["amort"]
            np.testing.assert_allclose(_pv0(B["skipped"], Y, r), _pv0(svc(A), Y, r) - _pv0(svc(B), Y, r),
                                       rtol=1e-9, atol=1e-9,
                                       err_msg="Experiment 4: PV(B deferred cash flows) != PV(A service) - PV(B service)")
        for reg, sim, key in (("B", B, "skipped"), ("C", C, "forgiven")):
            pv_gdp, pct_dmg = _spells(sim, key, r, params["D_trig"])
            row = {"scenario": sname, "version": version, "regime": reg, "measure": MEASURE[reg],
                   "n_spells": int(pv_gdp.size),
                   "pv_pct_gdp_mean": pv_gdp.mean(), "pv_pct_gdp_median": np.median(pv_gdp),
                   "pv_pct_gdp_p5": np.percentile(pv_gdp, 5), "pv_pct_gdp_p95": np.percentile(pv_gdp, 95),
                   "identity_checked": scoped}
            if reg == "C":   # % of damage only for the genuine transfer
                row.update(pct_damage_mean=pct_dmg.mean(), pct_damage_median=np.median(pct_dmg),
                           pct_damage_p5=np.percentile(pct_dmg, 5), pct_damage_p95=np.percentile(pct_dmg, 95))
            rows.append(row)
    return pd.DataFrame(rows)
