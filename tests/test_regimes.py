import numpy as np
from src import simulate
from tests.helpers import P, GREN, HIGH

LONG = dict(n_paths=1, horizon=300)


def test2_npv_neutrality_of_cash_flows_v1():
    """PV of debt-service cash flows (discounted at r) is equal in A and B once the deferred balance is valued."""
    p = P(**{"lambda": 0.0})
    for scen in (GREN, HIGH):
        A = simulate.simulate(p, scen, "A", 1, forced_hits={5: 30.0}, **LONG)
        B = simulate.simulate(p, scen, "B", 1, forced_hits={5: 30.0}, **LONG)
        np.testing.assert_allclose(A["b"], B["b"], atol=1e-10)   # stocks equal by construction in V1
        T = 300; r = p["r_bar"]
        Y = np.cumprod(1 + A["g"][0, 1:])                          # GDP level, Y_0 = 1
        disc = (1 + r) ** -np.arange(1, T + 1)
        serv = lambda s: s["interest"][0, 1:] + s["amort"][0, 1:] + s["catchup"][0, 1:]
        pvA, pvB = (serv(A) * Y * disc).sum(), (serv(B) * Y * disc).sum()
        pvQ = B["q"][0, -1] * Y[-1] * disc[-1]
        assert np.nansum(B["skipped"]) > 0 and pvB < pvA * 1.0000001 + 1  # relief is real in timing
        assert abs(pvB + pvQ - pvA) / pvA < 1e-9
        # and the timing really differs: B pays less in the window
        assert B["gfn"][0, 5] < A["gfn"][0, 5]


def test3_forgiveness_accounting():
    p = P(**{"lambda": 0.0})
    for scen in (GREN, HIGH):
        B = simulate.simulate(p, scen, "B", 1, forced_hits={5: 30.0}, n_paths=1, horizon=30)
        C = simulate.simulate(p, scen, "C", 1, forced_hits={5: 30.0}, n_paths=1, horizon=30)
        F = C["forgiven"][0]; r = C["r"][0]; g = C["g"][0]
        assert F[5] > 0 and F[6] > 0 and F[7] == 0
        # first forgiven amount recomputed independently from Regime A/B covered stock
        exp5 = (p["r_bar"] + 1 / p["M"]) * B["bc"][0, 4] / (1 + g[5])
        np.testing.assert_allclose(F[5], exp5, rtol=1e-12)
        gap = 0.0
        for t in range(1, 31):
            gap = gap * (1 + r[t]) / (1 + g[t]) + (0 if np.isnan(F[t]) else F[t])
        np.testing.assert_allclose(B["b"][0, -1] - C["b"][0, -1], gap, rtol=1e-10)
        assert C["b"][0, -1] < B["b"][0, -1]


def test6_trigger_logic():
    p = P(**{"lambda": 0.0})
    below = simulate.simulate(p, GREN, "B", 1, forced_hits={5: 4.99}, n_paths=1, horizon=20)
    assert not below["suspended"].any() and below["skipped"][0, 1:].sum() == 0
    for K in (1, 2, 3):
        hit = simulate.simulate(P(**{"lambda": 0.0}, K=K), GREN, "B", 1, forced_hits={5: 5.0}, n_paths=1, horizon=20)
        yrs = np.flatnonzero(hit["suspended"][0])
        assert list(yrs) == list(range(5, 5 + K))
    # overlap: a second qualifying hit inside the window restarts it
    ov = simulate.simulate(p, GREN, "B", 1, forced_hits={5: 20.0, 6: 20.0}, n_paths=1, horizon=20)
    assert list(np.flatnonzero(ov["suspended"][0])) == [5, 6, 7]
    # regime A never suspends
    a = simulate.simulate(p, GREN, "A", 1, forced_hits={5: 50.0}, n_paths=1, horizon=20)
    assert not a["suspended"].any()
