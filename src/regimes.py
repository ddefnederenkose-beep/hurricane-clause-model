"""Policy regimes.

A  No clause: all debt service paid as scheduled.
B  Hurricane clause: if D_t >= D_trig, interest + amortization on clause-covered debt are suspended for K years
   starting in year t. The skipped service goes into a deferred account Q that accrues at the contractual rate
   (capitalization) and is repaid at 1/M of its balance per year once no suspension is active.
   The debt STOCK is identical to Regime A in Version 1: a pure deferral is liquidity relief, not solvency relief.
C  Hypothetical debt relief (benchmark, not a real instrument): same trigger, but suspended interest and
   amortization are forgiven. Forgiven interest is never added to the stock, forgiven principal is deducted.
Overlap rule: a new qualifying hit during an active window restarts the K-year window; Q already accrued stays deferred.
"""
from __future__ import annotations
import numpy as np

REGIMES = ("A", "B", "C")


def suspension_mask(regime: str, d_t, rem, d_trig: float, k: int):
    """Return (suspended_this_year, updated remaining-window counter). Window includes the hit year."""
    if regime == "A":
        return np.zeros(d_t.shape, dtype=bool), rem
    rem = np.where(d_t >= d_trig, k, rem)
    return rem > 0, rem


def service_split(regime: str, susp, int_c, am_c, q_prev, r, g, m):
    """Cash actually paid on covered debt and the deferral/forgiveness bookkeeping (all % of GDP_t)."""
    z = np.zeros_like(int_c)
    pay_int = np.where(susp, 0.0, int_c)
    pay_am = np.where(susp, 0.0, am_c)
    skipped = np.where(susp, int_c + am_c, 0.0)
    if regime == "B":
        q_acc = q_prev * (1.0 + r) / (1.0 + g)          # capitalization at the contractual rate
        catch = np.where(susp, 0.0, q_acc / m)           # deferred service added back after the window
        q_new = q_acc + skipped - catch
        return dict(pay_int=pay_int, pay_am=pay_am, catch=catch, skipped=skipped, forgiven=z, q=q_new)
    if regime == "C":
        return dict(pay_int=pay_int, pay_am=pay_am, catch=z, skipped=z, forgiven=skipped, q=q_prev)
    return dict(pay_int=pay_int, pay_am=pay_am, catch=z, skipped=z, forgiven=z, q=q_prev)
