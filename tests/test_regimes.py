import numpy as np
from src import simulate
from tests.helpers import P, PD, GREN, HIGH, eff

LONG = dict(n_paths=1, horizon=300)


def _pv(x, A, r):
    Y = np.cumprod(1 + A["g"][0, 1:])
    return (x[0, 1:] * Y * (1 + r) ** -np.arange(1, x.shape[1])).sum()


def test2_no_double_counting_and_service_pv_identity_v1():
    """Deterministic single hurricane. (a) stocks identical; (b) amortization = (b-defbal)/M + repayment of defbal,
    so deferred principal is paid exactly once; (c) with m_rep = M, B's GFN equals A's in every non-suspended year;
    (d) discounted (interest + amortization) of A minus B equals the discounted service that was suspended."""
    p = PD(**{"lambda": 0.0})
    for scen in (GREN, HIGH):
        r = eff(p, scen)["r_bar"]
        A = simulate.simulate(p, scen, "A", 1, forced_hits={5: 30.0}, **LONG)
        B = simulate.simulate(p, scen, "B", 1, forced_hits={5: 30.0}, **LONG)
        np.testing.assert_allclose(A["b"], B["b"], atol=1e-10)                  # (a)
        ok = ~B["suspended"][0, 1:]
        np.testing.assert_allclose(B["gfn"][0, 1:][ok], A["gfn"][0, 1:][ok], atol=1e-10)   # (c)
        sus = B["suspended"][0, 1:]
        np.testing.assert_allclose((A["gfn"] - B["gfn"])[0, 1:][sus], B["skipped"][0, 1:][sus], atol=1e-10)
        assert sus.sum() == 2 and (B["gfn"][0, 5] < A["gfn"][0, 5])
        serv = lambda s: s["interest"] + s["amort"]
        assert abs((_pv(serv(A), A, r) - _pv(serv(B), A, r)) - _pv(B["skipped"], A, r)) < 1e-8 * _pv(serv(A), A, r)  # (d)
        # (b) explicit decomposition of amortization with a faster repayment schedule (m_rep = 4)
        B4 = simulate.simulate(PD(**{"lambda": 0.0}, defer_repay_years=4), scen, "B", 1, forced_hits={5: 30.0}, **LONG)
        g = B4["g"][0]; M = p["M"]
        bc, bo, D = B4["bc"][0], B4["bo"][0], B4["q"][0]
        for t in range(8, 40):                                  # after the window, deferral outstanding
            pbo, pbc = max(bo[t-1], 0.0), max(bc[t-1], 0.0)          # stocks in net-asset position pay nothing
            dd = min(D[t-1], pbc)
            exp = pbo / (M * (1 + g[t])) + (pbc - dd) / (M * (1 + g[t])) + dd / (4 * (1 + g[t]))
            np.testing.assert_allclose(B4["amort"][0, t], exp, rtol=1e-12)
        assert B4["q"][0, 7] > 0 and B4["q"][0, 40] < 0.05 * B4["q"][0, 7]      # defbal is created, repaid, and reduced by its own repayments
        # faster repayment => a post-window GFN hump relative to A (the cost of a deferral)
        assert (B4["gfn"][0, 7:20] > A["gfn"][0, 7:20] - 1e-12).all() and (B4["gfn"][0, 7:20] > A["gfn"][0, 7:20] + 1e-6).any()


def test3_forgiveness_accounting():
    p = P(**{"lambda": 0.0}, fra_surplus_rule=0)   # the FRA rule makes pd depend on debt, which differs between B and C
    for scen in (GREN, HIGH):
        pe = eff(p, scen)
        B = simulate.simulate(p, scen, "B", 1, forced_hits={5: 30.0}, n_paths=1, horizon=30)
        C = simulate.simulate(p, scen, "C", 1, forced_hits={5: 30.0}, n_paths=1, horizon=30)
        F = C["forgiven"][0]; r = C["r"][0]; g = C["g"][0]
        assert F[5] > 0 and F[6] > 0 and F[7] == 0
        exp5 = (pe["r_bar"] + 1 / p["M"]) * B["bc"][0, 4] / (1 + g[5])
        np.testing.assert_allclose(F[5], exp5, rtol=1e-12)
        gap = 0.0
        for t in range(1, 31):
            gap = gap * (1 + r[t]) / (1 + g[t]) + (0 if np.isnan(F[t]) else F[t])
        np.testing.assert_allclose(B["b"][0, -1] - C["b"][0, -1], gap, rtol=1e-10)
        assert C["b"][0, -1] < B["b"][0, -1]


def test6_trigger_logic():
    p = P(**{"lambda": 0.0})
    below = simulate.simulate(p, GREN, "B", 1, forced_hits={5: 4.99}, n_paths=1, horizon=20)
    assert not below["suspended"].any() and np.nansum(below["skipped"]) == 0
    for K in (1, 2, 3):
        hit = simulate.simulate(P(**{"lambda": 0.0}, K=K), GREN, "B", 1, forced_hits={5: 5.0}, n_paths=1, horizon=20)
        assert list(np.flatnonzero(hit["suspended"][0])) == list(range(5, 5 + K))
    ov = simulate.simulate(p, GREN, "B", 1, forced_hits={5: 20.0, 6: 20.0}, n_paths=1, horizon=20)
    assert list(np.flatnonzero(ov["suspended"][0])) == [5, 6, 7]
    a = simulate.simulate(p, GREN, "A", 1, forced_hits={5: 50.0}, n_paths=1, horizon=20)
    assert not a["suspended"].any()


def _deferral_run(rule, m_rep, hits=None, horizon=60):
    p = P(**{"lambda": 0.0}, repay_rule=rule, defer_repay_years=m_rep, K=2)
    return simulate.simulate(p, HIGH, "B", 1, forced_hits=hits or {5: 30.0}, n_paths=1, horizon=horizon)


def test_equal_instalments_clear_the_deferred_balance_after_m_rep_years():
    for m_rep in (2, 5, 8):
        B = _deferral_run("equal_instalments", m_rep)
        q, g = B["q"][0], B["g"][0]
        paid = B["catchup"][0]
        first = 7                                    # window = years 5, 6 -> first instalment in year 7
        assert q[6] > 0 and not B["suspended"][0, 7]
        # equal instalments in currency units: instalment_t * GDP level is constant
        Y = np.cumprod(1 + g[1:])                    # GDP level, year 1..T
        cash = paid[first:first + m_rep] * Y[first - 1:first - 1 + m_rep]
        np.testing.assert_allclose(cash, cash[0], rtol=1e-10)
        assert q[first + m_rep - 1] < 1e-10                  # fully cleared after exactly m_rep instalments
        assert (paid[first + m_rep:] < 1e-10).all()
        # the declining-balance rule does NOT clear it in the same time
        D = _deferral_run("declining_balance", m_rep)
        assert D["q"][0, first + m_rep - 1] > 1e-3


def test_equal_instalments_reamortise_when_a_new_deferral_arrives():
    B = _deferral_run("equal_instalments", 5, hits={5: 30.0, 10: 30.0}, horizon=40)
    q = B["q"][0]
    assert q[11] > 0.2 * q[9] and q[10] > 0              # window 10-11 adds new deferral on top of the old balance
    assert q[16 + 5 - 1] < 1e-9                          # cleared m_rep instalments after the second window (first paying year 12)


def test_stock_identity_with_equal_instalments_in_version_1_finding_2():
    """Finding 2: in Version 1 the debt stock under the clause equals the no-clause stock, whatever the repayment rule."""
    for rule in ("equal_instalments", "declining_balance"):
        for scen in (GREN, HIGH):
            p = P(**{"lambda": 0.0}, repay_rule=rule, defer_repay_years=5)
            A = simulate.simulate(p, scen, "A", 1, forced_hits={5: 30.0, 12: 20.0}, n_paths=1, horizon=40)
            B = simulate.simulate(p, scen, "B", 1, forced_hits={5: 30.0, 12: 20.0}, n_paths=1, horizon=40)
            np.testing.assert_allclose(B["b"], A["b"], atol=1e-10)
            assert B["gfn"][0, 5] < A["gfn"][0, 5]        # ... while GFN differs
