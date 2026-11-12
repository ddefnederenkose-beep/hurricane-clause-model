import numpy as np, pytest
from src import config, experiments, hurricanes, simulate
from tests.helpers import P, PD, GREN, HIGH, SCEN, DESIGNS, eff


def test_scenario_lambda_override_and_crn():
    d = hurricanes.draw_noise(1, 5000, 30)
    g = simulate.simulate(P(), SCEN["grenada_like"], "A", 1, draws=d)["D"]               # global lambda = 0.051
    h = simulate.simulate(P(), SCEN["grenada_like_lambda_010"], "A", 1, draws=d)["D"]    # scenario override 0.10
    assert abs((g > 0).mean() - 0.051) < 0.005 and abs((h > 0).mean() - 0.10) < 0.005
    assert ((g > 0) <= (h > 0)).all()   # same draws: the lower-lambda scenario's hits are a subset


def test_designs_load_with_sourced_terms_and_statuses():
    des, ph = config.load_designs()
    assert set(des) == {"grenada_style", "barbados_style"}
    assert des["grenada_style"]["overrides"] == {"s": 0.10, "K": 1, "defer_repay_years": 5}
    assert des["barbados_style"]["overrides"] == {"s": 0.80, "K": 2, "defer_repay_years": 5}


def test_status_vocabulary_and_verified_is_reserved(tmp_path):
    counts = config.status_counts()
    assert set(counts) <= set(config.STATUSES) and counts.get("VERIFIED", 0) == 0   # only the group sets VERIFIED
    bad = tmp_path / "c.yaml"
    bad.write_text("parameters:\n  x:\n    value: 1\n    source: ''\n    status: FACT\n    meaning: m\nsimulation: {T: 1, N: 1, seed: 1}\n")
    with pytest.raises(ValueError):
        config.load_calibration(bad)


def test_scenario_overrides_reach_the_model():
    """Scenario-level mu_D / sigma_D / kappa / r_bar / r_safe override the global calibration inside simulate()."""
    d = hurricanes.draw_noise(3, 2000, 30)
    base = simulate.simulate(P(), SCEN["grenada_like"], "A", 1, draws=d)
    small = simulate.simulate(P(), SCEN["grenada_like_lambda_010"], "A", 1, draws=d)  # mu_D 1.012 -> smaller damages
    assert np.median(small["D"][small["D"] > 0]) < 0.5 * np.median(base["D"][base["D"] > 0])   # medians 2.75 vs 11.18
    assert eff(P(), SCEN["grenada_like_kappa_062"])["kappa"] == 0.62
    assert eff(P(), SCEN["high_debt"])["r_bar"] == 0.058 and eff(P(), SCEN["grenada_like"])["r_bar"] == 0.024


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
        experiments.experiment_npv_relief(PD(defer_repay_years=2), scen, d, 1, n_paths=200, horizon=30)
    with pytest.raises(ValueError):
        experiments.experiment_npv_relief(PD(deferral_premium_on=1), scen, d, 1, n_paths=200, horizon=30)
    ok = experiments.experiment_npv_relief(PD(defer_repay_years=2), scen, d, 1, n_paths=200, horizon=30,
                                           allow_nondefault_repay=True)
    assert len(ok) == 2
    # also scoped out: equal instalments (the default repay_rule) even when defer_repay_years == M
    with pytest.raises(ValueError):
        experiments.experiment_npv_relief(P(defer_repay_years=P()["M"]), scen, d, 1, n_paths=200, horizon=30)


def test_no_surplus_rule_floors_primary_balance_once_debt_negative():
    p = P(**{"lambda": 0.0}, no_surplus_rule=1, fra_surplus_rule=0)   # isolate the sticky negative-debt rule
    scen = {"name": "t", "b_0": 8.0, "pd_bar": -4.0}
    on = simulate.simulate(p, scen, "A", 1, forced_hits={}, n_paths=1, horizon=30)
    off = simulate.simulate({**p, "no_surplus_rule": 0}, scen, "A", 1, forced_hits={}, n_paths=1, horizon=30)
    first = int(np.argmax(on["b"][0] < 0))           # first year with negative debt
    assert first > 0
    assert (on["pd"][0, first + 1:] >= 0).all() and (off["pd"][0, first + 1:] < 0).all()
    np.testing.assert_array_equal(on["pd"][0, 1:first + 1], off["pd"][0, 1:first + 1])   # unchanged before the trigger


def test_app_path_reproduces_experiment1_exactly():
    """The app (plots.collect on the interpolated scenario) and experiment 1 give identical metrics for the same
    scenario, design, version and draws; only the sample size differs by default."""
    from src import plots
    n, T = 3000, 30
    d = hurricanes.draw_noise(42, n, T)
    des = DESIGNS["barbados_style"]; p = config.design_params(P(), des)
    scen = {**experiments.scenario_for_b0(65.0, SCEN, P()), "lambda": P()["lambda"]}
    out = plots.collect(p, scen, 1, d, n, T, experiments.baselines(p, scen, 1, T))
    df = experiments.experiment_baseline(P(), {"grenada_like": SCEN["grenada_like"]}, {"barbados_style": des}, d, 1, n, T)
    for r in "AB":
        row = df[df.regime == r].iloc[0]
        assert abs(out["m"][r]["p_hcrisis_any"] - row.p_hcrisis_any) < 1e-12
        assert abs(out["m"][r]["p_crisis_any"] - row.p_crisis_any) < 1e-12


def test_attributable_flag_uses_regime_own_baseline_with_premium_on():
    """With the deferral premium on, B's no-hurricane GFN is above A's; the flag must not count that as hurricane-caused."""
    p = P(deferral_premium_on=1, **{"lambda": 0.0})
    scen = {k: v for k, v in SCEN["grenada_like"].items() if k != "lambda"}
    d = hurricanes.draw_noise(1, 200, 30)
    df = experiments.experiment_baseline(p, {"g": scen}, {"barbados_style": DESIGNS["barbados_style"]}, d, 1, 200, 30)
    assert (df.p_hcrisis_any == 0).all()


def test_fra_surplus_rule_surplus_only_above_b_star():
    p = P(**{"lambda": 0.0})
    assert p["fra_surplus_rule"] == 1 and p["b_star"] == 60
    sim = simulate.simulate(p, GREN, "A", 1, forced_hits={}, n_paths=1, horizon=30)
    b, pd = sim["b"][0], sim["pd"][0]
    for t in range(1, 31):
        assert pd[t] == (-1.5 if b[t - 1] > 60 else 0.0)            # surplus only while lagged debt > 60
    assert (b[:3] > 60).sum() >= 1 and (pd[1:] == 0).any() and (pd[1:] == -1.5).any()
    off = simulate.simulate({**p, "fra_surplus_rule": 0}, GREN, "A", 1, forced_hits={}, n_paths=1, horizon=30)
    assert (off["pd"][0, 1:] == -1.5).all()


def test_fra_surplus_rule_resumes_after_a_hurricane_and_ignores_deficits():
    p = P(**{"lambda": 0.0})
    sim = simulate.simulate(p, GREN, "A", 1, forced_hits={12: 80.0}, n_paths=1, horizon=30)
    b, pd = sim["b"][0], sim["pd"][0]
    assert b[12] > 60 and b[11] < 60                                  # the hit pushes debt back above the anchor ...
    assert pd[13] <= -1.5 + p["kappa"] * 80.0 / p["R"] + 1e-9         # ... so the surplus is run again (net of reconstruction spending)
    assert abs(pd[13] - (-1.5 + p["kappa"] * 80.0 / p["R"])) < 1e-9
    hi = simulate.simulate(p, HIGH, "A", 1, forced_hits={}, n_paths=1, horizon=30)
    assert (hi["pd"][0, 1:] == 1.0).all()                            # a deficit is never touched by the rule


def test_no_placeholder_verify_left_and_assumptions_are_noted():
    import yaml
    _, _, ph = config.load_calibration(); _, ph_s = config.load_scenarios(); _, ph_d = config.load_designs()
    assert ph == [] and ph_s == [] and ph_d == []
    for fn, key in ((config.CAL_PATH, "parameters"), (config.SCN_PATH, "scenarios"), (config.DES_PATH, "designs")):
        raw = yaml.safe_load(fn.read_text())[key]
        entries = raw.items() if key == "parameters" else [(f"{n}.{k}", v) for n, d in raw.items() for k, v in (d.get("overrides", d)).items() if isinstance(v, dict) and "status" in v]
        for name, v in entries:
            if v["status"] == "ASSUMPTION":
                assert "ASSUMPTION" in (v.get("note", "") + v.get("meaning", "")), name
