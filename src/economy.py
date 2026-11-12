"""Macro effects of a hurricane (growth and primary deficit)."""
from __future__ import annotations
import numpy as np


def growth(p: dict, d_t, d_prev):
    """g_t = g_bar - phi*D_t + psi*phi*D_{t-1}  (D in % of GDP, so divide by 100).
    Economic meaning: the hit destroys output in year t; a share psi of that loss is regained
    next year through rebuilding."""
    return p["g_bar"] - p["phi"] * d_t / 100.0 + p["psi"] * p["phi"] * d_prev / 100.0


def primary_deficit(p: dict, pd_bar: float, recon_damage_avg, b_prev):
    """pd_t = pd_bar + kappa * sum_{j<R} D_{t-j}/R - rho*(b_{t-1} - b*)  (all % of GDP).
    Economic meaning: the budget pays a share kappa of damage, spread evenly over R years;
    rho > 0 adds a fiscal reaction (consolidation) when debt exceeds its target b*.
    fra_surplus_rule (Fiscal Resilience Act): a baseline primary SURPLUS (pd_bar < 0) is run only while lagged debt exceeds
    b*; at or below b* the baseline primary balance is 0. Reconstruction spending (kappa term) always applies."""
    base = pd_bar
    if p.get("fra_surplus_rule", 0) and pd_bar < 0:
        base = np.where(b_prev > p["b_star"], pd_bar, 0.0)
    return base + p["kappa"] * recon_damage_avg - p["rho"] * (b_prev - p["b_star"])
