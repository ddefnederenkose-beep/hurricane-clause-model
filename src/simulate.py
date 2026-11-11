"""Monte Carlo engine: vectorised over paths, loop over years.

Arrays have shape (N, T+1): index 0 is the initial condition, index t (1..T) is year t.
Flow variables at index 0 are NaN except gfn[:,0] (initial GFN, used only by the Version 2 premium).
"""
from __future__ import annotations
import numpy as np
from . import debt, economy, hurricanes, regimes
from .config import check_units


def simulate(params, scenario, regime="A", version=1, draws=None, forced_hits=None,
             n_paths=1000, horizon=30, seed=42):
    """Simulate one regime.

    draws       : HurricaneDraws shared across regimes/versions/grid cells (common random numbers).
                  If None, drawn from `seed`.
    forced_hits : {year: damage_pct_gdp}. Explicit deterministic injection hook: REPLACES the random hurricane
                  process (all paths get exactly these hits, nothing else). Used by tests and the video sample path.
    """
    p = params
    check_units(p, scenario)
    if forced_hits is not None:
        D = np.zeros((n_paths, horizon))
        for yr, dmg in forced_hits.items():
            D[:, yr - 1] = dmg
    else:
        if draws is None:
            draws = hurricanes.draw_noise(seed, n_paths, horizon)
        D = hurricanes.damages(draws, scenario.get("lambda", p["lambda"]), p["mu_D"], p["sigma_D"], p["D_max"])
    N, T = D.shape
    M, K, R = p["M"], int(p["K"]), int(p["R"])

    keys = ["b", "bc", "bo", "reff", "gfn", "pd", "g", "r", "interest", "amort", "catchup",
            "skipped", "forgiven", "q", "x_bind"]
    out = {k: np.full((N, T + 1), np.nan) for k in keys}
    out["suspended"] = np.zeros((N, T + 1), dtype=bool)
    Dpad = np.concatenate([np.zeros((N, max(R, 2))), D], axis=1)  # no hurricanes before year 1
    off = max(R, 2)

    b0 = scenario["b_0"]
    reff0, gfn0 = debt.initial_effective_rate(p, scenario, version)
    out["b"][:, 0] = b0
    out["bc"][:, 0] = p["s"] * b0
    out["bo"][:, 0] = (1 - p["s"]) * b0
    out["reff"][:, 0] = reff0
    out["gfn"][:, 0] = gfn0
    out["q"][:, 0] = 0.0   # q = deferred principal balance (defbal) of Regime B
    rem = np.zeros(N, dtype=int)
    count = np.zeros(N, dtype=int)
    no_debt = np.zeros(N, dtype=bool)
    cap = p["max_triggers"] if p.get("use_trigger_cap", 1) else np.inf
    spread = p.get("deferral_spread", 0.0) if (regime in ("B", "C") and p.get("deferral_premium_on", 0)) else 0.0

    for t in range(1, T + 1):
        d_t = D[:, t - 1]
        d_prev = Dpad[:, off + t - 2]
        recon = sum(Dpad[:, off + t - 1 - j] for j in range(R)) / R
        g = economy.growth(p, d_t, d_prev)
        b_prev, bc_prev, bo_prev = out["b"][:, t - 1], out["bc"][:, t - 1], out["bo"][:, t - 1]
        pd = economy.primary_deficit(p, scenario["pd_bar"], recon, b_prev)
        if p.get("no_surplus_rule", 0):
            # once total debt has been negative, the government stops running surpluses (pd floored at 0)
            no_debt = no_debt | (b_prev < 0)
            pd = np.where(no_debt, np.maximum(pd, 0.0), pd)
        reff, xbind = debt.effective_rate(p, version, out["reff"][:, t - 1], b_prev, out["gfn"][:, t - 1])

        susp, rem, count = regimes.suspension_mask(regime, d_t, rem, count, p["D_trig"], K, cap)
        rc = reff + spread   # covered-debt rate (spread only in B/C when the robustness switch is on)
        int_c, _ = debt.scheduled_service(bc_prev, rc, g, M)
        int_o, am_o = debt.scheduled_service(bo_prev, reff, g, M)
        sp = regimes.service_split(regime, susp, bc_prev, int_c, out["q"][:, t - 1], g, M,
                                   p.get("defer_repay_years", M))

        share = debt.pd_allocation_share(bc_prev, b_prev, p["s"])
        bc = debt.stock_step(bc_prev, rc, g, share * pd, sp["forgiven"])
        bo = debt.stock_step(bo_prev, reff, g, (1 - share) * pd)

        interest = int_o + sp["pay_int"]
        amort = am_o + sp["pay_am"]   # incl. repayment of deferred principal
        out["interest"][:, t], out["amort"][:, t], out["catchup"][:, t] = interest, amort, sp["defer_repay"]  # catchup is a memo item, already inside amort
        out["gfn"][:, t] = pd + interest + amort
        out["pd"][:, t], out["g"][:, t], out["r"][:, t], out["reff"][:, t] = pd, g, reff, reff
        out["bc"][:, t], out["bo"][:, t], out["b"][:, t] = bc, bo, bc + bo
        out["skipped"][:, t], out["forgiven"][:, t], out["q"][:, t] = sp["skipped"], sp["forgiven"], sp["defbal"]
        out["suspended"][:, t] = susp
        out["x_bind"][:, t] = xbind
        rem = np.maximum(rem - 1, 0)

    out["D"] = D
    out["regime"], out["version"] = regime, version
    return out


def run_regimes(params, scenario, version=1, draws=None, forced_hits=None, n_paths=1000, horizon=30, seed=42):
    """Run A, B and C on exactly the same hurricane draws."""
    if draws is None and forced_hits is None:
        draws = hurricanes.draw_noise(seed, n_paths, horizon)
    return {r: simulate(params, scenario, r, version, draws, forced_hits, n_paths, horizon, seed)
            for r in regimes.REGIMES}
