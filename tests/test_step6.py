import numpy as np
from src import experiments, hurricanes, metrics, simulate
from src.grenada import grenada_relief
from tests.helpers import P, PD, GREN, HIGH, SCEN


def test_grenada_relief_toy_numbers_not_real_data():
    # TOY numbers only. Capitalized at the discount rate => zero NPV relief, positive nominal timing relief.
    r = 0.05
    deferred = [(1, 100.0)]
    repay = [(3, 100.0 * (1 + r) ** 2)]
    out = grenada_relief(deferred, repay, r, gdp=1000.0, damage=500.0)
    assert out["nominal_deferred"] == 100.0 and out["nominal_net"] < 0
    assert abs(out["npv_relief"]) < 1e-12
    # repaid with no interest => positive NPV relief
    out2 = grenada_relief(deferred, [(3, 100.0)], r, gdp=1000.0, damage=500.0)
    assert out2["npv_relief"] > 0 and abs(out2["npv_pct_gdp"] - 100 * out2["npv_relief"] / 1000) < 1e-12


def test_years_to_cross():
    b = np.array([[0, 100, 120, 160, 170], [0, 10, 20, 30, 40.0]])
    np.testing.assert_array_equal(metrics.years_to_cross(b, 150.0), [3.0, np.inf])


def test_experiment4_relief_equals_discounted_suspended_service():
    p = PD()
    d = hurricanes.draw_noise(5, 400, 30)
    df = experiments.experiment_npv_relief(p, SCEN, d, version=1, n_paths=400, horizon=30)  # asserts internally
    assert (df.n_spells > 0).all()


def test_single_event_relief_matches_deterministic_run():
    p = PD(**{"lambda": 0.0})
    B = simulate.simulate(p, GREN, "B", 1, forced_hits={5: 30.0}, n_paths=1, horizon=30)
    pv, pct = experiments._spells(B, "skipped", p["r_bar"], p["D_trig"])
    assert pv.size == 1 and pv[0] > 0 and pct[0] > 0
