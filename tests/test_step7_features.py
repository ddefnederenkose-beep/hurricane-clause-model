import numpy as np, pytest
from src import config, experiments, hurricanes, simulate
from tests.helpers import P, GREN, HIGH, SCEN, DESIGNS


def test_scenario_lambda_override_and_crn():
    d = hurricanes.draw_noise(1, 5000, 30)
    g = simulate.simulate(P(), SCEN["grenada_like"], "A", 1, draws=d)["D"]
    h = simulate.simulate(P(), SCEN["high_debt"], "A", 1, draws=d)["D"]
    assert abs((g > 0).mean() - 0.051) < 0.005 and abs((h > 0).mean() - 0.10) < 0.005
    assert ((g > 0) <= (h > 0)).all()   # same draws: the lower-lambda scenario's hits are a subset


def test_designs_load_and_are_placeholders():
    des, ph = config.load_designs()
    assert set(des) == {"grenada_style", "barbados_style"}
    assert des["barbados_style"]["overrides"]["s"] >= 0.9 and des["grenada_style"]["overrides"]["K"] == 1
    assert any(x.startswith("barbados_style") for x in ph)


def test_trigger_cap_three_triggers():
    p = P(**{"lambda": 0.0}, K=1)
    hits = {3: 20.0, 8: 20.0, 13: 20.0, 18: 20.0}
    on = simulate.simulate(p, GREN, "B", 1, forced_hits=hits, n_paths=1, horizon=25)
    assert list(np.flatnonzero(on["suspended"][0])) == [3, 8, 13]      # 4th hit finds the clause exhausted
    off = simulate.simulate({**p, "use_trigger_cap": 0}, GREN, "B", 1, forced_hits=hits, n_paths=1, horizon=25)
    assert list(np.flatnonzero(off["suspended"][0])) == [3, 8, 13, 18]
    c = simulate.simulate(p, GREN, "C", 1, forced_hits=hits, n_paths=1, horizon=25)
    assert list(np.flatnonzero(c["suspended"][0])) == [3, 8, 13]       # same trigger logic in C


def test_deferral_premium_only_in_B_C_and_off_by_default():
    base = P(**{"lambda": 0.0})
    on = {**base, "deferral_premium_on": 1}
    kw = dict(forced_hits={5: 20.0}, n_paths=1, horizon=30)
    A0, A1 = simulate.simulate(base, HIGH, "A", 1, **kw), simulate.simulate(on, HIGH, "A", 1, **kw)
    np.testing.assert_array_equal(A0["b"], A1["b"])                     # A unaffected
    B0, B1 = simulate.simulate(base, HIGH, "B", 1, **kw), simulate.simulate(on, HIGH, "B", 1, **kw)
    np.testing.assert_array_equal(A0["b"], B0["b"])                     # default off: B == A stock
    assert B1["b"][0, -1] > B0["b"][0, -1]                              # spread raises covered debt cost


def test_experiment4_scoped_to_default_repay_rule():
    d = hurricanes.draw_noise(5, 200, 30)
    scen = {"grenada_like": SCEN["grenada_like"]}
    with pytest.raises(ValueError):
        experiments.experiment_npv_relief(P(defer_repay_years=2), scen, d, 1, n_paths=200, horizon=30)
    with pytest.raises(ValueError):
        experiments.experiment_npv_relief(P(deferral_premium_on=1), scen, d, 1, n_paths=200, horizon=30)
    ok = experiments.experiment_npv_relief(P(defer_repay_years=2), scen, d, 1, n_paths=200, horizon=30,
                                           allow_nondefault_repay=True)
    assert len(ok) == 2


def test_no_surplus_rule_floors_primary_balance_once_debt_negative():
    p = P(**{"lambda": 0.0}, no_surplus_rule=1)
    scen = {"name": "t", "b_0": 8.0, "pd_bar": -4.0}
    on = simulate.simulate(p, scen, "A", 1, forced_hits={}, n_paths=1, horizon=30)
    off = simulate.simulate({**p, "no_surplus_rule": 0}, scen, "A", 1, forced_hits={}, n_paths=1, horizon=30)
    first = int(np.argmax(on["b"][0] < 0))           # first year with negative debt
    assert first > 0
    assert (on["pd"][0, first + 1:] >= 0).all() and (off["pd"][0, first + 1:] < 0).all()
    np.testing.assert_array_equal(on["pd"][0, 1:first + 1], off["pd"][0, 1:first + 1])   # unchanged before the trigger
