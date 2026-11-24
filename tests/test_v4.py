"""Tests for the v4 additions: refinanced lump rule, explicit-inflow hook, lump diagnostics, robustness variants, Beryl validation, figure data."""
import numpy as np
import pandas as pd
import pytest
from src import config, hurricanes, simulate, v3, v4, plots_v3
from tests.helpers import P, GREN, HIGH, DESIGNS, SIM

H = 6


def _p(design, key, **kw):
    return v3.schedule_params(config.design_params(P(**kw), DESIGNS[design]), key, H)


@pytest.mark.parametrize("scen", [GREN, HIGH])
@pytest.mark.parametrize("version", [1, 2])
def test_refinanced_lump_pays_no_cash_lump_and_clears_the_tranche(scen, version):
    p = _p("barbados_style", "lump_refi", **{"lambda": 0.0})
    s = simulate.simulate(p, scen, "B", version, forced_hits={5: 20.0}, n_paths=1, horizon=40)
    assert np.nansum(s["catchup"]) == 0.0                       # never a cash repayment of the deferred balance
    assert s["q"][0, 5:7].max() > 0                              # deferred during the window
    assert s["q"][0, 5 + H:].max() == 0.0                        # folded into the regular stock at strike year + 6
    assert s["q"][0, 5 + H - 1] > 0                              # ... and not before


def test_refinanced_lump_v1_stock_equals_no_clause_and_beats_cash_lump_on_gfn():
    kw = {"lambda": 0.0}
    pr, pl = _p("barbados_style", "lump_refi", **kw), _p("barbados_style", "lump", **kw)
    A = simulate.simulate(pl, GREN, "A", 1, forced_hits={5: 20.0}, n_paths=1, horizon=40)
    R = simulate.simulate(pr, GREN, "B", 1, forced_hits={5: 20.0}, n_paths=1, horizon=40)
    L = simulate.simulate(pl, GREN, "B", 1, forced_hits={5: 20.0}, n_paths=1, horizon=40)
    assert np.allclose(R["b"], A["b"])
    assert R["gfn"][0, 5 + H] < L["gfn"][0, 5 + H] - 1.0         # no lump hump in the due year
    assert np.allclose(R["gfn"][0, 5 + H + 12:], A["gfn"][0, 5 + H + 12:], atol=1e-9)   # converges back to the no-clause schedule


def test_baseline_rules_still_reject_unknown_rule_and_refi_needs_due():
    from src import regimes
    with pytest.raises(ValueError):
        regimes.service_split("B", np.zeros(1, bool), np.ones(1), np.ones(1), np.zeros(1), np.zeros(1), 10.0, 5, rule="nope")
    with pytest.raises(ValueError):
        regimes.service_split("B", np.zeros(1, bool), np.ones(1), np.ones(1), np.zeros(1), np.zeros(1), 10.0, 5, rule="lump_refinanced")


def test_inflow_hook_lowers_that_years_deficit_and_debt_one_for_one_and_default_is_inert():
    p = P(**{"lambda": 0.0})
    base = simulate.simulate(p, GREN, "A", 1, forced_hits={1: 16.5}, n_paths=1, horizon=4)
    inert = simulate.simulate(p, GREN, "A", 1, forced_hits={1: 16.5}, n_paths=1, horizon=4, inflows=None)
    assert np.array_equal(base["b"], inert["b"])
    s = simulate.simulate(p, GREN, "A", 1, forced_hits={1: 16.5}, n_paths=1, horizon=4, inflows={1: 3.2})
    assert s["pd"][0, 1] == pytest.approx(base["pd"][0, 1] - 3.2)
    assert s["b"][0, 1] == pytest.approx(base["b"][0, 1] - 3.2)      # V1: stock law adds pd one for one
    assert s["pd"][0, 2] == pytest.approx(base["pd"][0, 2])           # only year 1


def test_first_lump_equals_deferred_balance_due_and_diagnostics_are_consistent():
    p = _p("barbados_style", "lump", **{"lambda": 0.0})
    s = simulate.simulate(p, GREN, "B", 1, forced_hits={5: 20.0}, n_paths=1, horizon=40)
    has, idx, amt = v4.first_lump(s)
    assert has[0] and idx[0] + 1 == 5 + H                             # year index t = 11
    assert amt[0] == pytest.approx(s["catchup"][0, 5 + H]) and amt[0] > 0
    assert s["q"][0, 5 + H] == pytest.approx(0.0, abs=1e-9)           # the lump clears the whole balance


def test_lump_diagnostics_small_run():
    scens, _ = config.load_scenarios()
    sc = config.main_scenarios(scens)["grenada_like"]
    params, _, _ = config.load_calibration()
    designs, _ = config.load_designs()
    N, T = 1500, 30
    d = hurricanes.draw_noise(7, N, T)
    out = v4.lump_diagnostics(params, sc, designs["barbados_style"], 1, d, N, T, config.load_v3())
    assert 0 < out["n_lump_paid_within_T"] <= out["n_strike_paths"] <= N
    assert out["lump_mean"] > 0 and out["lump_median"] > 0
    for k in ("A", "inst", "lump"):
        assert 0 <= out[f"p15_year_{k}_unc"] <= out[f"p15_year_{k}"] <= 1
        assert out[f"p15_any_{k}"] >= out[f"p15_year_{k}_unc"] - 1e-12
    assert out["stress5_A"] >= out["stress10_A"] >= out["stress15_A"]          # nested thresholds
    assert out["stress5_lump"] >= out["stress10_lump"] >= out["stress15_lump"]
    assert out["peak7_lump"] > out["peak7_inst"]                                # the lump year is inside t..t+6
    assert out["skipped_first_mean"] > out["lump_mean"] * 0.5


def test_variant_params_scale_the_median_and_do_not_mutate_inputs():
    params, _, _ = config.load_calibration()
    before = dict(params)
    lo = v4.variant_params(params, v4.VARIANTS["median x0.75"])
    assert np.exp(lo["mu_D"]) == pytest.approx(0.75 * np.exp(params["mu_D"]))
    assert lo["sigma_D"] == params["sigma_D"]
    assert v4.variant_params(params, v4.VARIANTS["+25 bp delay premium"])["deferral_premium_on"] == 1
    assert v4.variant_params(params, v4.VARIANTS["base"]) == params
    assert params == before


def test_premium_variant_changes_only_the_clause_regime():
    params, _, _ = config.load_calibration()
    scens, _ = config.load_scenarios()
    sc = config.main_scenarios(scens)["grenada_like"]
    p0 = config.design_params(params, DESIGNS["barbados_style"])
    pv = v4.variant_params(p0, v4.VARIANTS["+25 bp delay premium"])
    A0 = simulate.simulate(p0, sc, "A", 1, forced_hits={3: 20.0}, n_paths=1, horizon=10)
    A1 = simulate.simulate(pv, sc, "A", 1, forced_hits={3: 20.0}, n_paths=1, horizon=10)
    B0 = simulate.simulate(p0, sc, "B", 1, forced_hits={3: 20.0}, n_paths=1, horizon=10)
    B1 = simulate.simulate(pv, sc, "B", 1, forced_hits={3: 20.0}, n_paths=1, horizon=10)
    assert np.array_equal(A0["gfn"], A1["gfn"], equal_nan=True) and not np.allclose(B0["gfn"][0, 1:], B1["gfn"][0, 1:])


def test_beryl_replicates_the_closed_form_and_leaves_config_untouched():
    params, _, _ = config.load_calibration()
    scens, _ = config.load_scenarios()
    sc = config.main_scenarios(scens)["grenada_like"]
    before = dict(params)
    r = v4.beryl(params, sc, DESIGNS["grenada_style"], 1, "A")
    p = config.scenario_params(params, sc)
    g1 = p["g_bar"] - p["phi"] * v4.BERYL_DAMAGE / 100
    pd1 = 0.0 * 0 + (-1.5) + p["kappa"] * v4.BERYL_DAMAGE / p["R"]          # surplus applies: b_0 = 65 > b_star = 60
    assert r["g"][0] == pytest.approx(g1)
    assert r["debt"][0] == pytest.approx((1 + p["r_bar"]) / (1 + g1) * 65 + pd1)
    assert r["gfn"][0] == pytest.approx(pd1 + (p["r_bar"] + 1 / p["M"]) * 65 / (1 + g1))
    assert params == before                                                  # kappa override acts on a copy
    net = v4.beryl(params, sc, DESIGNS["grenada_style"], 1, "A", kappa=0.42)
    lit = v4.beryl(params, sc, DESIGNS["grenada_style"], 1, "A", kappa=0.42, inflow=v4.BERYL_PAYOUT)
    assert lit["debt"][0] == pytest.approx(net["debt"][0] - 3.2)
    assert v4.IMF_DEBT[1] == 72.7


def test_beryl_clause_changes_gfn_not_v1_debt():
    params, _, _ = config.load_calibration()
    scens, _ = config.load_scenarios()
    sc = config.main_scenarios(scens)["grenada_like"]
    a = v4.beryl(params, sc, DESIGNS["grenada_style"], 1, "A")
    b = v4.beryl(params, sc, DESIGNS["grenada_style"], 1, "B", "lump")
    assert np.allclose(a["debt"], b["debt"]) and b["gfn"][0] < a["gfn"][0]


def test_figure_data_matches_grid_and_one_decimal_labels(tmp_path):
    grid = pd.read_csv(config.ROOT / "outputs" / "v3" / "tables" / "grid_seed42.csv")
    eqb = pd.read_csv(config.ROOT / "outputs" / "v3" / "tables" / "equal_instalment_breakeven_seed42.csv")
    n = SIM["N"]
    d = plots_v3.figure_data(grid, eqb, n)
    assert len(d["A"]) == 12 and len(d["B"]) == 8 and len(d["C"]) == 4
    hd = [x for x in d["A"] if x["country"] == "High-debt" and x["window"] == "strike yr + 5"]
    assert {x["bar"]: f"{x['value']:.1f}" for x in hd} == {"No clause": "27.4", "Clause, five-year instalments": "29.5", "Clause, lump sum (B'-lump)": "25.3"}
    gl = {x["bar"]: x["value"] for x in d["B"] if x["country"] == "Grenada-like"}
    assert f"{gl['High-coverage clause']:.1f}" == "24.7" and f"{gl[chr(72) + 'igh-coverage clause, B' + chr(39) + '-lump']:.1f}" == "52.3"
    p = grid[(grid.scenario == "grenada_like") & (grid.design == "barbados_style") & (grid.version == 1) & (grid.schedule == "lump")].iloc[0].stress_mean_b
    assert f"{100 * p:.1f}" == "52.3"
    figpath = tmp_path / "f.png"
    plots_v3.figure1_v4(grid, eqb, n, figpath)
    from PIL import Image
    assert Image.open(figpath).size == (3300, 1140)
