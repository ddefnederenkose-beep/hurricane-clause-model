"""Revised-brief analyses (RESULTS_v3): paired confidence intervals, Grenada's actual repayment (regime B'),
timing-dependent and continuous stress measures, break-evens. Adds NEW code paths only; nothing here changes a baseline number.

Terminology: the old "hurricane-attributable crisis" is now the "financing-stress episode" (definition unchanged): GFN more
than `GFN_margin` (5) pp of GDP above the SAME regime's no-hurricane path in at least one of the T years.

Paired design: every regime sees the same hurricane draws, so per path d_i = 1[stress with clause] - 1[stress without];
mean(d) is the clause effect and mean(d) +/- 1.96 sd(d)/sqrt(N) its 95% CI (the CI of a difference of two correlated proportions).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from . import config, experiments, metrics, simulate

COUNTRY = {"grenada_like": "Grenada-like", "high_debt": "High-debt"}
DESIGN = {"grenada_style": "Grenada-style (s=0.10, K=1)", "barbados_style": "High-coverage (s=0.80, K=2)"}
SCHEDULE = {"5yr": "5-yr equal [baseline]", "lump": "B'-lump", "inst": "B'-inst", "lump_refi": "B'-lump refinanced"}


def schedule_params(p: dict, key: str, horizon: int) -> dict:
    """Parameters of a repayment schedule. '5yr' = the existing baseline (equal instalments over the design's 5 years)."""
    if key == "5yr":
        return dict(p)
    rule = {"lump": "lump_at_horizon", "inst": "equal_to_horizon", "lump_refi": "lump_refinanced"}[key]
    return {**p, "repay_rule": rule, "defer_repay_years": horizon}


# ------------------------------------------------------------------------------------------------- statistics
def paired(a, b, z: float = 1.96) -> dict:
    """b minus a on the same paths: mean, 95% CI (normal approx.), and whether the CI excludes zero. a, b: (N,) bool/float."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    n = d.size
    m = float(d.mean())
    se = float(d.std(ddof=1) / np.sqrt(n)) if n > 1 else 0.0
    lo, hi = m - z * se, m + z * se
    return {"mean_a": float(a.mean()), "mean_b": float(b.mean()), "diff": m, "se": se, "lo": lo, "hi": hi,
            "sig": bool(lo > 0 or hi < 0)}


# ---------------------------------------------------------------------------------------------- stress measures
def stress_thresholds(D, d_trig: float, margin: float, window_margin: float | None = None):
    """Threshold (pp of GDP above the no-hurricane path) per path and year, shape (N, T).
    window_margin=None -> `margin` everywhere (the standard financing-stress episode).
    Timing-dependent variant: `window_margin` in the strike year (a hit with D >= d_trig) and the year after, `margin` elsewhere."""
    if window_margin is None:
        return np.full(D.shape, float(margin))
    strike = D >= d_trig
    window = strike.copy()
    window[:, 1:] |= strike[:, :-1]
    return np.where(window, float(window_margin), float(margin))


def excess_gfn(sim, base, thr):
    """Per-path excess GFN above the no-hurricane path and above the threshold, shape (N, T)."""
    return np.maximum(0.0, sim["gfn"][:, 1:] - np.asarray(base)[..., 1:] - thr)


def measures(sim, base, p, v3):
    """All per-path measures for one simulated regime: stress flag (5 pp), timing-dependent flag (3 pp window / 5 pp),
    absolute GFN > GFN_crit flag, and continuous expected excess GFN (sum over years, pp of GDP)."""
    D, gfn = sim["D"], sim["gfn"][:, 1:]
    th5 = stress_thresholds(D, p["D_trig"], p["GFN_margin"])
    th3 = stress_thresholds(D, p["D_trig"], p["GFN_margin"], v3["storm_window_margin"])
    return {"stress": (excess_gfn(sim, base, th5) > 0).any(axis=1),
            "stress_tw": (excess_gfn(sim, base, th3) > 0).any(axis=1),
            "gfn15": (gfn > p["GFN_crit"]).any(axis=1),
            "excess": excess_gfn(sim, base, th5).sum(axis=1)}


# ------------------------------------------------------------------------------------------------------ grid
def run_grid(params, scenarios, designs, draws, N, T, versions=(1, 2), schedules=("5yr", "lump", "inst"),
             horizon=None, v3=None):
    """One row per scenario x design x version x schedule: clause (B or B') versus no clause (A), paired."""
    v3 = v3 or config.load_v3()
    horizon = horizon or v3["bprime_horizon"]
    rows = []
    for dname, design in designs.items():
        p0 = config.design_params(params, design)
        for sname, scen in scenarios.items():
            for v in versions:
                A = simulate.simulate(p0, scen, "A", v, draws=draws, n_paths=N, horizon=T)
                mA = measures(A, experiments.baseline_gfn_path(p0, scen, v, T, "A"), p0, v3)
                pk = {w: metrics.event_peak_gfn(A, p0["D_trig"], w) for w in (2, 6)}
                for sk in schedules:
                    p = schedule_params(p0, sk, horizon)
                    B = simulate.simulate(p, scen, "B", v, draws=draws, n_paths=N, horizon=T)
                    mB = measures(B, experiments.baseline_gfn_path(p, scen, v, T, "B"), p, v3)
                    row = {"scenario": sname, "design": dname, "version": v, "schedule": sk}
                    for key in ("stress", "stress_tw", "gfn15", "excess"):
                        row.update({f"{key}_{k}": val for k, val in paired(mA[key], mB[key]).items()})
                    for w in (2, 6):
                        row[f"peak{w}_A"] = float(pk[w].mean())
                        row[f"peak{w}_B"] = float(metrics.event_peak_gfn(B, p["D_trig"], w).mean())
                    row["n_events"] = int(pk[2].size)
                    rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------ break-evens
def lump_breakeven_sweep(params, scenarios, design, draws, N, T, l_grid=range(1, 16), versions=(1, 2)):
    """Stress-episode effect (clause minus no clause, paired) of the lump-sum schedule for lump horizons L = 1..15 years
    after the strike. Returns one row per scenario x version x L."""
    p0 = config.design_params(params, design)
    v3 = config.load_v3()
    rows = []
    for sname, scen in scenarios.items():
        for v in versions:
            A = simulate.simulate(p0, scen, "A", v, draws=draws, n_paths=N, horizon=T)
            fA = measures(A, experiments.baseline_gfn_path(p0, scen, v, T, "A"), p0, v3)["stress"]
            for L in l_grid:
                p = schedule_params(p0, "lump", L)
                B = simulate.simulate(p, scen, "B", v, draws=draws, n_paths=N, horizon=T)
                fB = measures(B, experiments.baseline_gfn_path(p, scen, v, T, "B"), p, v3)["stress"]
                rows.append({"scenario": sname, "version": v, "L": L, **paired(fA, fB)})
    return pd.DataFrame(rows)


def first_negative_L(df) -> dict:
    """Per (scenario, version): smallest L with diff < 0 ('lowers P(stress)'), the smallest L with a CI entirely below 0,
    and whether the effect stays negative for every larger L (monotone) -- 'never' if no L in the grid works."""
    out = {}
    for key, g in df.groupby(["scenario", "version"]):
        g = g.sort_values("L")
        neg = g[g["diff"] < 0]
        sig = g[g["hi"] < 0]
        L0 = int(neg["L"].min()) if len(neg) else None
        out[key] = {"L_first_negative": L0,
                    "L_first_significant": int(sig["L"].min()) if len(sig) else None,
                    "stays_negative_after": bool((g[g["L"] >= L0]["diff"] < 0).all()) if L0 else None}
    return out


def equal_instalment_breakeven(params, scenarios, design, draws, N, T, m_grid=tuple(range(2, 13)), versions=(1, 2)):
    """Repayment period (years, linear interpolation) at which the equal-instalment clause switches from raising to lowering
    P(stress): the same method and grid as exp3_repay_switch_points.csv, so 5.9 / 9.3 / 5.6 are reproduced and the
    Grenada-like V2 value is added."""
    p0 = config.design_params(params, design)
    rows = []
    for sname, scen in scenarios.items():
        for v in versions:
            A = simulate.simulate(p0, scen, "A", v, draws=draws, n_paths=N, horizon=T)
            pA = ((A["gfn"][:, 1:] > experiments.baseline_gfn_path(p0, scen, v, T, "A")[..., 1:] + p0["GFN_margin"]).any(axis=1)).mean()
            baseB = experiments.baseline_gfn_path(p0, scen, v, T, "B")
            for m in m_grid:
                p = {**p0, "repay_rule": "equal_instalments", "defer_repay_years": m}
                B = simulate.simulate(p, scen, "B", v, draws=draws, n_paths=N, horizon=T)
                pB = ((B["gfn"][:, 1:] > baseB[..., 1:] + p["GFN_margin"]).any(axis=1)).mean()
                rows.append({"design": "barbados_style", "scenario": sname, "version": v, "repay_rule": "equal_instalments",
                             "defer_repay_years": m, "benefit_p_hcrisis_any": float(pA - pB)})
    return experiments.repay_switch_points(pd.DataFrame(rows))
