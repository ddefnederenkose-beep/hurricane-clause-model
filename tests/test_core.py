import numpy as np, pytest
from src import hurricanes, simulate, config
from tests.helpers import P, GREN, HIGH


def test1_no_hurricanes_closed_form():
    p = P(**{"lambda": 0.0})
    for scen in (GREN, HIGH):
        sim = simulate.simulate(p, scen, "A", 1, n_paths=5, horizon=30, seed=1)
        pe = config.scenario_params(p, scen)      # scenario-level r_bar override applies
        b = scen["b_0"]
        for t in range(1, 31):
            b = (1 + pe["r_bar"]) / (1 + pe["g_bar"]) * b + scen["pd_bar"]
            np.testing.assert_allclose(sim["b"][:, t], b, rtol=1e-13, atol=1e-12)


def test4_common_random_numbers_across_regimes_versions_and_lambda():
    d = hurricanes.draw_noise(7, 500, 30)
    p = P()
    runs = {(v, r): simulate.simulate(p, HIGH, r, v, draws=d) for v in (1, 2) for r in "ABC"}
    ref = runs[(1, "A")]["D"]
    assert ref.sum() > 0
    for s in runs.values():
        np.testing.assert_array_equal(s["D"], ref)
    lo = hurricanes.damages(d, 0.05, p["mu_D"], p["sigma_D"], p["D_max"])
    hi = hurricanes.damages(d, 0.20, p["mu_D"], p["sigma_D"], p["D_max"])
    assert ((lo > 0) <= (hi > 0)).all()          # more hits at higher lambda, never fewer
    np.testing.assert_array_equal(lo[lo > 0], hi[lo > 0])  # shared hits have identical damage


def test5_reproducibility():
    a = hurricanes.draw_noise(42, 100, 30); b = hurricanes.draw_noise(42, 100, 30); c = hurricanes.draw_noise(43, 100, 30)
    np.testing.assert_array_equal(a.u, b.u); np.testing.assert_array_equal(a.z, b.z)
    assert not np.array_equal(a.u, c.u)
    r1 = simulate.simulate(P(), HIGH, "B", 2, n_paths=100, seed=42)
    r2 = simulate.simulate(P(), HIGH, "B", 2, n_paths=100, seed=42)
    np.testing.assert_array_equal(r1["b"], r2["b"])


@pytest.mark.parametrize("regime", "ABC")
@pytest.mark.parametrize("version", (1, 2))
def test7_gfn_accounting(regime, version):
    p = P(**{"lambda": 0.2})
    sim = simulate.simulate(p, HIGH, regime, version, n_paths=300, seed=3)
    s = slice(1, None)
    np.testing.assert_allclose(sim["gfn"][:, s], sim["pd"][:, s] + sim["interest"][:, s] + sim["amort"][:, s],
                               rtol=0, atol=1e-12)
    if regime == "A":  # independent recomputation of scheduled service
        b_prev, g, r = sim["b"][:, :-1], sim["g"][:, s], sim["r"][:, s]
        expect = sim["pd"][:, s] + (r + 1 / p["M"]) * b_prev / (1 + g)
        np.testing.assert_allclose(sim["gfn"][:, s], expect, rtol=1e-12)


def test_unit_guard():
    with pytest.raises(ValueError):
        config.check_units(P(r_bar=3.0), GREN)
    with pytest.raises(ValueError):
        config.check_units(P(), {**GREN, "b_0": 0.65})
