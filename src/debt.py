"""Debt building blocks: interest rate rule, scheduled debt service, stock law of motion.

Debt service conventions (all % of GDP_t, consistent with b_t = (1+r)/(1+g) b_{t-1} + pd_t):
    interest_t     = r_t * b_{t-1} / (1+g_t)
    amortization_t = b_{t-1} / (M (1+g_t))      (1/M of the stock matures each year and is rolled over)
Amortization is rolled over, so it enters GFN but does not change the stock.
"""
from __future__ import annotations
import numpy as np


def initial_effective_rate(p: dict, scenario: dict, version: int):
    """Version 1: r_bar. Version 2: r_eff_0 = r_safe + x_0, with x_0 computed from initial conditions
    (so a high-debt country does not start with artificially cheap debt). GFN_0 uses r_safe as interest rate
    to avoid circularity."""
    gfn0 = initial_gfn(p, scenario, version)
    if version == 1:
        return p["r_bar"], gfn0
    x0 = risk_premium(p, scenario["b_0"], gfn0)
    return p["r_safe"] + x0, gfn0


def initial_gfn(p: dict, scenario: dict, version: int = 1):
    rate = p["r_bar"] if version == 1 else p["r_safe"]
    return scenario["pd_bar"] + (rate + 1.0 / p["M"]) * scenario["b_0"]


def risk_premium(p: dict, b_prev, gfn_prev):
    """x_t = theta_b*max(0, b_{t-1}-b_bar) + theta_G*max(0, GFN_{t-1}-GFN_bar)."""
    x = risk_premium_uncapped(p, b_prev, gfn_prev)
    return np.minimum(x, p["x_max"])  # cap: keeps explosive debt spirals finite (see DECISIONS.md)


def risk_premium_uncapped(p: dict, b_prev, gfn_prev):
    return p["theta_b"] * np.maximum(0.0, b_prev - p["b_bar"]) + p["theta_G"] * np.maximum(0.0, gfn_prev - p["GFN_bar"])


def effective_rate(p: dict, version: int, reff_prev, b_prev, gfn_prev):
    """Returns (r_eff, premium_cap_binds). Version 1: constant r_bar. Version 2: the market rate r_safe + x_t only applies to the 1/M of the stock
    that is newly issued/rolled over, so r_eff_t = (1-1/M) r_eff_{t-1} + (1/M)(r_safe + x_t)."""
    if version == 1:
        return np.full_like(b_prev, p["r_bar"], dtype=float), np.zeros(b_prev.shape, dtype=bool)
    xu = risk_premium_uncapped(p, b_prev, gfn_prev)
    m = p["r_safe"] + np.minimum(xu, p["x_max"])
    return (1.0 - 1.0 / p["M"]) * reff_prev + m / p["M"], xu >= p["x_max"]


def scheduled_service(stock_prev, r, g, M):
    """Scheduled (interest, amortization) on a stock, % of GDP_t. Negative stocks (net assets) pay nothing."""
    pos = np.maximum(stock_prev, 0.0)
    d = 1.0 + g
    return r * pos / d, pos / (M * d)


def stock_step(stock_prev, r, g, pd_share, forgiven=0.0):
    """b^i_t = (1+r)/(1+g) b^i_{t-1} + (allocated primary deficit) - (debt written off)."""
    return (1.0 + r) / (1.0 + g) * stock_prev + pd_share - forgiven


def pd_allocation_share(bc_prev, b_prev, s):
    """Share of the primary deficit assigned to the covered stock: proportional to stock size."""
    safe = b_prev > 1.0
    return np.where(safe, np.clip(bc_prev / np.where(safe, b_prev, 1.0), 0.0, 1.0), s)
