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
   Trigger cap: at most `max_triggers` activations per path (config option `use_trigger_cap`, default on); applies to B and C.
   Optional deferral-risk premium: constant spread on the covered stock's rate in B/C only (default off).
C  Hypothetical debt relief (benchmark, not a real instrument): same trigger, but suspended interest and
   amortization are forgiven. Forgiven interest is never added to the stock, forgiven principal is deducted.
"""
from __future__ import annotations
import numpy as np

REGIMES = ("A", "B", "C")


def suspension_mask(regime: str, d_t, rem, count, d_trig: float, k: int, cap=np.inf):
    """Return (suspended_this_year, remaining-window counter, trigger count).
    Window includes the hit year. A qualifying hit (D >= D_trig) uses one trigger while count < cap (lifetime
    three-trigger cap, default on); a hit during an active window restarts it and also uses a trigger."""
    if regime == "A":
        return np.zeros(d_t.shape, dtype=bool), rem, count
    fire = (d_t >= d_trig) & (count < cap)
    rem = np.where(fire, k, rem)
    return rem > 0, rem, count + fire


REPAY_RULES = ("equal_instalments", "declining_balance")


def service_split(regime: str, susp, bc_prev, int_c, defbal_prev, g, M, m_rep, rule="declining_balance", n_rem=None):
    """Cash actually paid on covered debt plus deferral/forgiveness bookkeeping (all % of GDP_t).

    Repayment rule for the deferred balance defbal (Regime B):
      equal_instalments  equal amounts (in currency units) over m_rep years, fully cleared (Asonuma et al. 2017, App. II);
                         the instalment counter n_rem is reset to m_rep whenever new service is deferred (re-amortised),
                         and each paying year pays defbal/n_rem, so the balance reaches zero after m_rep years.
      declining_balance  1/m_rep of the remaining balance each year (geometric run-off, never fully cleared).

    Returns dict: pay_int, pay_am (incl. repayment of defbal), defer_repay, skipped (cash service not paid
    because of the clause), forgiven, defbal (new balance), n_rem (instalments left)."""
    if rule not in REPAY_RULES:
        raise ValueError(f"repay_rule must be one of {REPAY_RULES}")
    d = 1.0 + g
    pos = np.maximum(bc_prev, 0.0)
    z = np.zeros_like(pos)
    if n_rem is None:
        n_rem = np.full(pos.shape, float(m_rep))
    if regime == "B":
        dprev = np.minimum(defbal_prev, pos)
        reg_am = (pos - dprev) / (M * d)            # regular schedule on the non-deferred part
        if rule == "equal_instalments":
            n_use = np.maximum(n_rem, 1.0)
            rep = dprev / (n_use * d)                # equal instalments in currency units; last one clears the balance
        else:
            rep = dprev / (m_rep * d)                # scheduled repayment of the deferred tranche
        pay_int = np.where(susp, 0.0, int_c)
        rep_paid = np.where(susp, 0.0, rep)
        pay_am = np.where(susp, 0.0, reg_am + rep)
        skipped = np.where(susp, int_c + reg_am + rep, 0.0)
        defbal = defbal_prev / d - rep_paid + np.where(susp, reg_am, 0.0)
        n_new = np.where(susp, float(m_rep), np.maximum(n_rem - 1.0, 0.0))
        return dict(pay_int=pay_int, pay_am=pay_am, defer_repay=rep_paid, skipped=skipped, forgiven=z, defbal=defbal,
                    n_rem=n_new)
    am_c = pos / (M * d)
    if regime == "C":
        forg = np.where(susp, int_c + am_c, 0.0)
        return dict(pay_int=np.where(susp, 0.0, int_c), pay_am=np.where(susp, 0.0, am_c), defer_repay=z,
                    skipped=z, forgiven=forg, defbal=defbal_prev, n_rem=n_rem)
    return dict(pay_int=int_c, pay_am=am_c, defer_repay=z, skipped=z, forgiven=z, defbal=defbal_prev, n_rem=n_rem)
