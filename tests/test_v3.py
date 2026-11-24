"""Tests for the revised-brief additions: regime B' (Grenada's actual repayment), paired CIs, timing-dependent stress."""
import numpy as np
import pytest
from src import config, hurricanes, simulate, v3
from tests.helpers import P, GREN, HIGH, DESIGNS, eff

H = 6
LONG = dict(n_paths=1, horizon=40)
STRIKE = 5


def _bprime(design, key, **kw):
    return v3.schedule_params(config.design_params(P(**{"lambda": 0.0}, **kw), DESIGNS[design]), key, H)


def _currency(x, g):
    """% of GDP_t flows -> currency units (GDP_0 = 1), index 1..T."""
    return x[1:] * np.cumprod(1.0 + g[1:])


@pytest.mark.parametrize("design", ["grenada_style", "barbados_style"])
@pytest.mark.parametrize("key", ["lump", "inst"])
@pytest.mark.parametrize("scen", [GREN, HIGH])
@pytest.mark.parametrize("version", [1, 2])
def test_a_bprime_repays_full_deferred_balance(design, key, scen, version):
    """(a) One strike. The deferred principal (regular amortization skipped in the K suspended years) is repaid in full, in
    currency units, the balance ends at zero, and the timing is as specified: lump = a single payment in strike year + 6;
    inst = equal currency instalments from the year after the suspension through strike year + 6."""
    p = _bprime(design, key)
    K = int(p["K"])
    A = simulate.simulate(p, scen, "A", version, forced_hits={STRIKE: 30.0}, **LONG)
    B = simulate.simulate(p, scen, "B", version, forced_hits={STRIKE: 30.0}, **LONG)
    g = B["g"][0]
    sus = B["suspended"][0]
    assert sus.sum() == K and sus[STRIKE]
    rep = _currency(B["catchup"][0], g)
    # deferred principal = skipped regular amortization (skipped = interest + regular amortization while defbal = 0)
    added = np.zeros_like(rep)
    d = 1.0 + g[1:]
    bc_prev = B["bc"][0, :-1]
    Mm = eff(p, scen)["M"]
    q_prev = np.nan_to_num(B["q"][0, :-1])
    reg_am = (np.maximum(bc_prev, 0.0) - q_prev) / (Mm * d)   # regular schedule on the NON-deferred part
    added[sus[1:]] = (reg_am * np.cumprod(d))[sus[1:]]
    np.testing.assert_allclose(np.nansum(rep), added.sum(), rtol=1e-10)     # repays the whole deferred balance
    assert abs(B["q"][0, -1]) < 1e-9                                         # nothing left over
    pay_years = np.flatnonzero(rep > 1e-12) + 1
    due = STRIKE + H
    if key == "lump":
        assert list(pay_years) == [due]
    else:
        assert list(pay_years) == list(range(STRIKE + K, due + 1))
        np.testing.assert_allclose(rep[pay_years - 1], rep[pay_years[0] - 1], rtol=1e-10)   # equal instalments
    assert A["gfn"][0, due] >= 0   # sanity: A untouched


@pytest.mark.parametrize("design", ["grenada_style", "barbados_style"])
@pytest.mark.parametrize("key", ["lump", "inst"])
@pytest.mark.parametrize("scen", [GREN, HIGH])
def test_b_v1_debt_stock_equals_no_clause_under_both_schedules(design, key, scen):
    """(b) Version 1: a deferral is liquidity, not solvency, relief. Debt stock (total and covered) under B' equals regime A on
    random hurricane histories (several triggers per path, restarts, the trigger cap), exactly."""
    p = {**_bprime(design, key), "lambda": 0.25}
    draws = hurricanes.draw_noise(11, 3000, 30)
    A = simulate.simulate(p, scen, "A", 1, draws=draws, n_paths=3000, horizon=30)
    B = simulate.simulate(p, scen, "B", 1, draws=draws, n_paths=3000, horizon=30)
    assert B["suspended"].any()
    np.testing.assert_allclose(B["b"], A["b"], atol=1e-9)
    np.testing.assert_allclose(B["bc"], A["bc"], atol=1e-9)


def test_bprime_leaves_baseline_rules_untouched():
    """The default (5-yr equal-instalment) path gives bit-identical results with and without the new bookkeeping."""
    p = config.design_params(P(), DESIGNS["barbados_style"])
    draws = hurricanes.draw_noise(42, 500, 30)
    a = simulate.simulate(p, GREN, "B", 1, draws=draws, n_paths=500, horizon=30)
    b = simulate.simulate({**p, "repay_rule": "equal_instalments"}, GREN, "B", 1, draws=draws, n_paths=500, horizon=30)
    np.testing.assert_array_equal(a["gfn"], b["gfn"])


def test_lump_sum_is_one_payment_hump_and_cap_resets_due_year():
    """A second trigger re-sets the due year to (latest trigger year + 6): the pooled balance is paid once, then nothing."""
    p = _bprime("barbados_style", "lump")
    B = simulate.simulate(p, GREN, "B", 1, forced_hits={5: 30.0, 9: 30.0}, **LONG)
    pay_years = np.flatnonzero(B["catchup"][0, 1:] > 1e-12) + 1
    assert list(pay_years) == [9 + H] and abs(B["q"][0, -1]) < 1e-9


def test_paired_ci_formula_and_significance():
    rng = np.random.default_rng(0)
    a = rng.random(10000) < 0.3
    b = a | (rng.random(10000) < 0.1)                      # clause strictly worse: d in {0, 1}
    r = v3.paired(a, b)
    d = b.astype(float) - a.astype(float)
    assert r["diff"] == pytest.approx(d.mean())
    assert r["hi"] - r["lo"] == pytest.approx(2 * 1.96 * d.std(ddof=1) / np.sqrt(d.size))
    assert r["sig"] and r["lo"] > 0
    z = v3.paired(a, a)
    assert z["diff"] == 0 and z["lo"] == 0 and z["hi"] == 0 and not z["sig"]   # degenerate (zero variance) case


def test_timing_dependent_threshold_window():
    D = np.zeros((1, 10)); D[0, 3] = 20.0; D[0, 7] = 2.0                   # strike in year 4; a sub-trigger hit in year 8
    th = v3.stress_thresholds(D, 5.0, 5.0, 3.0)[0]
    assert list(th) == [5, 5, 5, 3, 3, 5, 5, 5, 5, 5]                      # 3 pp in strike year and the next, 5 pp elsewhere
    assert (v3.stress_thresholds(D, 5.0, 5.0)[0] == 5).all()


def test_stress_flags_are_nested_and_zero_without_hurricanes():
    p = config.design_params(P(), DESIGNS["barbados_style"]); v = config.load_v3()
    from src import experiments
    draws = hurricanes.draw_noise(1, 800, 30)
    A = simulate.simulate(p, GREN, "A", 1, draws=draws, n_paths=800, horizon=30)
    m = v3.measures(A, experiments.baseline_gfn_path(p, GREN, 1, 30, "A"), p, v)
    assert (m["stress_tw"] | ~m["stress"]).all()                           # the 3-pp variant flags a superset of the 5-pp one
    z = simulate.simulate(P(**{"lambda": 0.0}), GREN, "A", 1, forced_hits={}, n_paths=5, horizon=30)
    mz = v3.measures(z, experiments.baseline_gfn_path(P(), GREN, 1, 30, "A"), P(), v)
    assert not mz["stress"].any() and mz["excess"].sum() == 0
