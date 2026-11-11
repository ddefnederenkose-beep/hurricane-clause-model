"""Grenada anchor (Experiment 5, function only). NO Grenada numbers are filled in here: the group enters the
actual deferral figures after Hurricane Beryl (2024) from the official sources."""
from __future__ import annotations


def grenada_relief(deferred_payments, schedule, rate, gdp=None, damage=None, base_year=None):
    """Relief from a payment deferral, measured from actual (or hypothetical) cash-flow data.

    deferred_payments : list of (year, amount)  payments that would have been due but were suspended
    schedule          : list of (year, amount)  repayments of the deferred amounts (incl. capitalized interest)
    rate              : discount rate (decimal), normally the contractual rate
    gdp, damage      : optional, same currency units as the amounts, used for the '% of GDP' and '% of damage' lines
    base_year         : year to discount to (default: first deferred year)

    Returns dict with
      nominal_deferred   sum of suspended payments (gross cash relief in the window)
      nominal_net        suspended minus later repayments (negative if capitalization makes you repay more)
      npv_relief         PV(suspended) - PV(repayments): the economic value of the deferral
      npv_pct_gdp, npv_pct_damage  (None when gdp / damage not supplied)
    A deferral capitalized at the discount rate gives npv_relief ~ 0: it is liquidity, not solvency, relief.
    """
    if base_year is None:
        base_year = min(y for y, _ in deferred_payments)
    pv = lambda flows: sum(a / (1.0 + rate) ** (y - base_year) for y, a in flows)
    nominal_def = sum(a for _, a in deferred_payments)
    nominal_rep = sum(a for _, a in schedule)
    npv = pv(deferred_payments) - pv(schedule)
    return {
        "nominal_deferred": nominal_def,
        "nominal_net": nominal_def - nominal_rep,
        "npv_relief": npv,
        "npv_pct_gdp": None if gdp is None else 100.0 * npv / gdp,
        "npv_pct_damage": None if damage is None else 100.0 * npv / damage,
    }
