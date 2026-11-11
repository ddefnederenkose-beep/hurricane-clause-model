"""Policy regimes.

A  No clause: all debt service paid as scheduled.
B  Hurricane clause: if D_t >= D_trig, interest and amortization on clause-covered debt are suspended for K years
   starting in year t.
     * Skipped interest is capitalized at the contractual rate. Because the debt stock already accrues interest at
       (1+r), the covered stock in Version 1 is IDENTICAL to Regime A: a pure deferral is liquidity, not solvency, relief.
     * Skipped amortization becomes a deferred balance `defbal` (a sub-tranche INSIDE the covered stock b^c).
       After the window the amortization is  (b^c - defbal)/M + defbal/m_rep , i.e. the deferred principal is carved out
       of the regular 1/M schedule and repaid on its own schedule (m_rep = defer_repay_years), so principal is never
       paid twice. defbal is reduced by its own repayments. Coupons are paid on the whole stock (incl. defbal).
   Overlap rule: a new qualifying hit during an active window restarts the K-year window; defbal stays deferred.
C  Hypothetical debt relief (benchmark, not a real instrument): same trigger, but suspended interest and
   amortization are forgiven. Forgiven interest is never added to the stock, forgiven principal is deducted.
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


def service_split(regime: str, susp, bc_prev, int_c, defbal_prev, g, M, m_rep):
    """Cash actually paid on covered debt plus deferral/forgiveness bookkeeping (all % of GDP_t).

    Returns dict: pay_int, pay_am (incl. repayment of defbal), defer_repay, skipped (cash service not paid
    because of the clause), forgiven, defbal (new balance)."""
    d = 1.0 + g
    pos = np.maximum(bc_prev, 0.0)
    z = np.zeros_like(pos)
    if regime == "B":
        dprev = np.minimum(defbal_prev, pos)
        reg_am = (pos - dprev) / (M * d)            # regular schedule on the non-deferred part
        rep = dprev / (m_rep * d)                    # scheduled repayment of the deferred tranche
        pay_int = np.where(susp, 0.0, int_c)
        rep_paid = np.where(susp, 0.0, rep)
        pay_am = np.where(susp, 0.0, reg_am + rep)
        skipped = np.where(susp, int_c + reg_am + rep, 0.0)
        defbal = defbal_prev / d - rep_paid + np.where(susp, reg_am, 0.0)
        return dict(pay_int=pay_int, pay_am=pay_am, defer_repay=rep_paid, skipped=skipped, forgiven=z, defbal=defbal)
    am_c = pos / (M * d)
    if regime == "C":
        forg = np.where(susp, int_c + am_c, 0.0)
        return dict(pay_int=np.where(susp, 0.0, int_c), pay_am=np.where(susp, 0.0, am_c), defer_repay=z,
                    skipped=z, forgiven=forg, defbal=defbal_prev)
    return dict(pay_int=int_c, pay_am=am_c, defer_repay=z, skipped=z, forgiven=z, defbal=defbal_prev)
