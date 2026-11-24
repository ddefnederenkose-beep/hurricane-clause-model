"""Streamlit demo for the video:  .venv/bin/streamlit run app.py
Runs off the same config/ and src/ code as run_all.py (no duplicated model logic).
Visual theme lives in .streamlit/config.toml; the small CSS block below adds what the theme cannot."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from src import config, experiments, hurricanes, plots, simulate, v3

st.set_page_config(page_title="Hurricane-clause model", layout="wide")
PARAMS, SIM, PH = config.load_calibration()
SCEN, PH_S = config.load_scenarios()
DESIGNS, PH_D = config.load_designs()
T, SEED = SIM["T"], SIM["seed"]
LABELS = {"Grenada-style (s=0.10, K=1)": "grenada_style", "High-coverage (s=0.80, K=2)": "barbados_style"}
CFG3 = config.load_v3()   # config/v3.yaml: storm_window_margin (3 points), bprime_horizon (6 years)
M = PARAMS["M"]

# Chart chrome matched to the page theme. Regime colours stay Okabe-Ito (src/plots.py) so the
# app and the paper's figures agree.
CHART_RC = {
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9, "text.color": "#1D1D1F", "axes.labelcolor": "#6E6E73", "axes.edgecolor": "#D2D2D7",
    "xtick.color": "#6E6E73", "ytick.color": "#6E6E73", "grid.color": "#E8E8ED", "grid.alpha": 1.0,
    "axes.titleweight": "bold", "axes.titlecolor": "#1D1D1F", "figure.facecolor": "white",
    "axes.facecolor": "white", "figure.dpi": 160,
}

st.markdown("""
<style>
  h1 { letter-spacing: -0.025em; line-height: 1.08 !important; text-wrap: balance; }
  h2, h3 { letter-spacing: -0.015em; }
  ::selection { background: rgba(0, 113, 227, 0.18); }
  :focus-visible { outline: 3px solid rgba(0, 113, 227, 0.45); outline-offset: 2px; }
  .lede { color: #6E6E73; font-size: 1.0625rem; line-height: 1.5; max-width: 68ch; margin: -0.25rem 0 0.75rem; }
  .note { display: flex; gap: 0.5rem; align-items: flex-start; color: #B25000; font-size: 0.875rem; line-height: 1.45; }
  .note svg { flex: none; margin-top: 0.15rem; }
  [class*="st-key-panel"] { background: #FFFFFF; border: none !important; border-radius: 18px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 6px 20px rgba(0, 0, 0, 0.05); padding: 1.25rem 1.5rem 1rem; }
  .verdict { display: flex; gap: 0.75rem; align-items: flex-start; }
  .verdict svg { flex: none; margin-top: 0.2rem; }
  .verdict b { display: block; font-size: 1.25rem; font-weight: 600; letter-spacing: -0.01em; color: #1D1D1F; }
  .verdict span { color: #6E6E73; line-height: 1.45; }
  table.risk, table.risk th, table.risk td, table.risk tr { border: none !important; background: transparent !important; }
  table.risk { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; margin-top: 0.5rem; }
  table.risk th { font-size: 0.8125rem; font-weight: 500; color: #6E6E73; text-align: right; padding: 0 0 0.5rem 1rem;
    border-bottom: 1px solid #E8E8ED !important; }
  table.risk th:first-child, table.risk td:first-child { text-align: left; padding-left: 0; }
  table.risk td { text-align: right; padding: 0.85rem 0 0.85rem 1rem; border-bottom: 1px solid #E8E8ED !important; vertical-align: top; }
  table.risk tr:last-child td { border-bottom: none !important; }
  table.risk td.num { font-size: 1.5rem; font-weight: 600; letter-spacing: -0.01em; white-space: nowrap; }
  table.risk .metric { font-weight: 600; }
  table.risk .sub { display: block; color: #6E6E73; font-size: 0.8125rem; line-height: 1.4; margin-top: 0.15rem; }
  .better { color: #248A3D; } .worse { color: #D70015; } .flat { color: #6E6E73; }
  p.foot { color: #6E6E73; font-size: 0.8125rem !important; line-height: 1.45; margin: 0.25rem 0 0; }
</style>
""", unsafe_allow_html=True)

ICON = {  # 20px SF Symbols-style line icons, drawn as SVG
    "good": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#248A3D" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/>'
            '<path d="m8 12.5 2.8 2.8L16.5 9"/></svg>',
    "bad": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#D70015" stroke-width="2" '
           'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/>'
           '<path d="M12 7v6"/><path d="M12 16.5h.01"/></svg>',
    "flat": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6E6E73" stroke-width="2" '
            'stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/></svg>',
    "warn": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 '
            '1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
}


def load_preset():
    d = DESIGNS[LABELS[st.session_state["preset"]]]["overrides"]
    st.session_state["s"], st.session_state["K"] = float(d["s"]), int(d["K"])
    st.session_state["m_rep"] = int(d["defer_repay_years"])
    st.session_state["h_bp"] = int(CFG3["bprime_horizon"])


if "s" not in st.session_state:
    st.session_state["preset"] = "High-coverage (s=0.80, K=2)"
    load_preset()
    st.session_state["lam"] = float(PARAMS["lambda"])   # baseline frequency 0.051 (Mallucci 2020; HURDAT2 brackets it)

# ---------------------------------------------------------------- sidebar: inputs
st.sidebar.header("Clause design")
st.sidebar.selectbox("Preset", list(LABELS), key="preset", on_change=load_preset,
                     help="Loads s, K and the repayment period from config/designs.yaml.")
s = st.sidebar.slider("Share of debt covered (s)", 0.0, 1.0, step=0.05, key="s",
                      help="Fraction of debt service that the clause defers when it triggers.")
K = st.sidebar.slider("Deferral length K (years)", 0, 5, key="K",
                      help="How many years payments are deferred after a trigger.")
d_trig = st.sidebar.slider("Trigger threshold D_trig (% of GDP damage)", 1, 30, int(PARAMS["D_trig"]),
                           help="Minimum hurricane damage, in % of GDP, that activates the clause.")
RULES = {"Equal instalments, fully repaid (baseline)": "equal_instalments",
         "Grenada's actual: one lump sum at strike year + 6 (B'-lump)": "lump_at_horizon",
         "Grenada's actual: equal instalments to strike year + 6 (B'-inst)": "equal_to_horizon",
         "Lump sum refinanced at the market rate (B'-lump refinanced)": "lump_refinanced",
         "Declining balance (1/m of the balance per year; sensitivity)": "declining_balance"}
rule_label = st.sidebar.selectbox("Repayment rule", list(RULES), index=0,
                                  help="Baseline: equal instalments clear the deferred principal after the repayment period "
                                       "(Asonuma et al. 2017). B' rules follow Grenada's Beryl deferral, whose sources disagree on the "
                                       "shape of repayment, so both readings are offered. 'Refinanced' folds the balance into ordinary "
                                       "debt at strike year + 6 instead of paying cash (V2: at the endogenous risk premium).")
repay_rule = RULES[rule_label]
if repay_rule in ("lump_at_horizon", "equal_to_horizon", "lump_refinanced"):
    m_rep = st.sidebar.slider("Years from the strike to the due date", 1, 15, key="h_bp",
                              help="6 = the 2030 bond maturity minus the 2024 strike (IMF CR 25/39). The deferred amortization, "
                                   "from the year after the suspension ends, is repaid at (lump) or through (instalments) this date.")
else:
    m_rep = st.sidebar.slider("Repayment period for deferred principal (years)", 1, 15, key="m_rep",
                              help=f"M = {M} is the normal debt run-off. Below M, deferred amounts are repaid faster "
                                   "than normal and create a post-window hump in financing needs.")
st.sidebar.header("Country and hurricanes")
b0 = st.sidebar.slider("Initial debt b0 (% of GDP)", 40, 140, int(SCEN["grenada_like"]["b_0"]),
                       help="65 is Grenada's 2026 projection (IMF CR 26/9). Higher values move towards the stylised, "
                            "unsourced high-debt scenario (110): the primary balance and interest rate are interpolated.")
lam = st.sidebar.slider("Hurricane probability per year (lambda)", 0.01, 0.30, step=0.001, key="lam", format="%.3f",
                        help="0.051 = Mallucci (2020). HURDAT2 gives 0.044 (within 60 nm) to 0.067 (within 100 nm). "
                             "Note: the damage size distribution is calibrated at 0.051.")
fra = st.sidebar.checkbox("Surplus only while debt > 60% of GDP", value=bool(PARAMS["fra_surplus_rule"]),
                          help="Fiscal Resilience Act: the 1.5% primary surplus is run only while debt exceeds 60% of GDP; "
                               "below 60% the baseline primary balance is 0.")
st.sidebar.header("Simulation")
version = st.sidebar.radio("Model version", [1, 2],
                           format_func=lambda v: "1: exogenous rate" if v == 1 else "2: endogenous risk premium")
n_paths = st.sidebar.select_slider("Simulated paths", [2000, 4000, 6000, 10000], value=10000,
                                   help="More paths give smoother estimates but run slower.")


@st.cache_resource
def get_draws(n):
    return hurricanes.draw_noise(SEED, n, T)


@st.cache_data(show_spinner=False)
def run(s, K, m_rep, d_trig, b0, lam, version, n, repay_rule, fra):
    p = {**PARAMS, "s": s, "K": K, "defer_repay_years": m_rep, "D_trig": d_trig, "repay_rule": repay_rule,
         "fra_surplus_rule": int(fra)}
    scen = {**experiments.scenario_for_b0(b0, SCEN, PARAMS), "lambda": lam}
    base = experiments.baselines(p, scen, version, T)
    out = plots.collect(p, scen, version, get_draws(n), n, T, base)
    # paired clause-vs-no-clause statistics (same draws): financing-stress episode, 3-point storm-window variant, GFN > 15%, excess GFN
    sim = {r: simulate.simulate(p, scen, r, version, draws=get_draws(n), n_paths=n, horizon=T) for r in "AB"}
    ms = {r: v3.measures(sim[r], base[r], p, CFG3) for r in "AB"}
    out["paired"] = {k: v3.paired(ms["A"][k], ms["B"][k]) for k in ("stress", "stress_tw", "gfn15", "excess")}
    return out, scen["pd_bar"]


with st.spinner("Simulating..."):
    data, pd_bar = run(s, K, m_rep, d_trig, b0, lam, version, n_paths, repay_rule, fra)
m = data["m"]
PR = data["paired"]


def change_cell(r, scale=100, unit="points", fmt="{:+.1f}"):
    """Paired clause-minus-no-clause change with its 95% CI. Green only if the CI is entirely below 0 (lower is better)."""
    d, lo, hi = r["diff"] * scale, r["lo"] * scale, r["hi"] * scale
    cls = "better" if hi < 0 else ("worse" if lo > 0 else "flat")
    txt = (fmt.format(d) + "&#8239;" + unit).replace("-", "&minus;")
    ci = ("95% CI [" + fmt.format(lo) + ", " + fmt.format(hi) + "]").replace("-", "&minus;")
    return f'<td class="num {cls}">{txt}<span class="sub">{ci}</span></td>'


_c = config.status_counts()

# ---------------------------------------------------------------- header
st.title("Do hurricane clauses create fiscal space?")
st.markdown('<p class="lede">A Monte Carlo debt model comparing no clause (A), a hurricane clause that defers debt '
            'service (B, with the actual Grenada repayment as B&#8242;), and outright debt relief as a benchmark (C). Adjust the terms in the sidebar.</p>'
            f'<p class="note">{ICON["warn"]}<span>Work in progress. Parameters: {_c.get("SOURCED", 0)} sourced, '
            f'{_c.get("CALIBRATED", 0)} calibrated by us, {_c.get("ASSUMPTION", 0)} modelling assumptions; none is '
            'group-verified yet. The high-debt scenario is stylised and unsourced.</span></p>',
            unsafe_allow_html=True)

# ---------------------------------------------------------------- verdict + risk table
st_ = PR["stress"]
_why = {"equal_instalments": f"Deferred amounts are repaid over {m_rep} years, against a normal run-off of M = {M:g} years.",
        "declining_balance": f"Deferred amounts run off at 1/{m_rep} of the balance per year.",
        "lump_at_horizon": f"The whole deferred balance falls due in one payment {m_rep} years after the strike.",
        "equal_to_horizon": f"Deferred amounts are repaid in equal instalments through year {m_rep} after the strike.",
        "lump_refinanced": f"The deferred balance is refinanced into ordinary debt {m_rep} years after the strike."}[repay_rule]
if st_["hi"] < 0:
    verdict = ("good", "The clause lowers financing-stress risk with these terms.",
               f"The paired change is {st_['diff']*100:+.1f} points (95% CI {st_['lo']*100:+.1f} to {st_['hi']*100:+.1f}). " + _why)
elif st_["lo"] > 0:
    verdict = ("bad", "The clause raises financing-stress risk with these terms.",
               f"The paired change is {st_['diff']*100:+.1f} points (95% CI {st_['lo']*100:+.1f} to {st_['hi']*100:+.1f}). " + _why)
else:
    verdict = ("flat", "The clause makes no distinguishable difference with these terms.",
               f"The paired change is {st_['diff']*100:+.1f} points; the 95% CI ({st_['lo']*100:+.1f} to {st_['hi']*100:+.1f}) includes zero.")
tw = PR["stress_tw"]
if (tw["diff"] > 0) != (st_["diff"] > 0) and (tw["lo"] > 0 or tw["hi"] < 0):
    verdict = (verdict[0], verdict[1], verdict[2] + f" Under the 3-point storm-window measure the sign is opposite ({tw['diff']*100:+.1f} points).")

with st.container(key="panel-risk"):
    st.markdown(
        '<div class="verdict" role="status">%s<div><b>%s</b><span>%s</span></div></div>'
        '<table class="risk"><thead><tr><th>Over %d years</th><th>No clause</th><th>With clause</th>'
        '<th>Change (paired)</th></tr></thead><tbody>'
        '<tr><td><span class="metric">Financing-stress episode</span><span class="sub">GFN more than %g points of GDP '
        'above the same regime\'s no-hurricane path in at least one year</span></td>'
        '<td class="num">%.1f%%</td><td class="num">%.1f%%</td>%s</tr>'
        '<tr><td><span class="metric">Stress, 3-point storm window</span><span class="sub">Threshold %g points in the strike '
        'year and the year after, %g points in other years</span></td>'
        '<td class="num">%.1f%%</td><td class="num">%.1f%%</td>%s</tr>'
        '<tr><td><span class="metric">GFN above %g%% of GDP</span><span class="sub">In at least one year (absolute level)</span></td>'
        '<td class="num">%.1f%%</td><td class="num">%.1f%%</td>%s</tr>'
        '<tr><td><span class="metric">Expected excess GFN</span><span class="sub">Sum over years of GFN above the no-hurricane '
        'path plus %g points, in points of GDP</span></td>'
        '<td class="num">%.1f</td><td class="num">%.1f</td>%s</tr>'
        '</tbody></table>'
        '<p class="foot">Change = with clause minus no clause on the same hurricane draws; the 95%% interval is the paired '
        'normal approximation at N = %s. Green: interval entirely below zero. Red: entirely above. Grey: includes zero.</p>'
        % (ICON[verdict[0]], verdict[1], verdict[2], T, PARAMS["GFN_margin"],
           PR["stress"]["mean_a"] * 100, PR["stress"]["mean_b"] * 100, change_cell(PR["stress"]),
           CFG3["storm_window_margin"], PARAMS["GFN_margin"],
           PR["stress_tw"]["mean_a"] * 100, PR["stress_tw"]["mean_b"] * 100, change_cell(PR["stress_tw"]),
           PARAMS["GFN_crit"], PR["gfn15"]["mean_a"] * 100, PR["gfn15"]["mean_b"] * 100, change_cell(PR["gfn15"]),
           PARAMS["GFN_margin"], PR["excess"]["mean_a"], PR["excess"]["mean_b"], change_cell(PR["excess"], 1, "pts", "{:+.1f}"),
           f"{n_paths:,}"),
        unsafe_allow_html=True)

# ---------------------------------------------------------------- charts
with plt.rc_context(CHART_RC):
    with st.container(key="panel-fan"):
        st.subheader("Debt/GDP paths")
        st.caption("Median debt path with 50% and 90% bands for each regime. Version 1: stocks of A and B are "
                   "identical, so only gross financing needs differ.")
        fig1, axes = plt.subplots(1, 3, figsize=(9.5, 3.1), sharey=True)
        for ax, r in zip(axes, "ABC"):
            plots.draw_fan(ax, data["q"][r], r, T, plots.LAB[r], ylabel=(r == "A"), legend=(r == "A"))
        fig1.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

    with st.container(key="panel-event"):
        st.subheader("Gross financing needs around a hurricane")
        st.caption(f"Average GFN in the years before and after a hit (t = 0). Set the repayment period below "
                   f"M = {M} to see the post-window hump; set it to M or above to see the clause help.")
        fig2, ax = plt.subplots(figsize=(8, 3.1))
        plots.draw_event(ax, data["ew"], f"b0={b0}, lambda={lam:.3f}", legend=True)
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

# ---------------------------------------------------------------- method notes
with st.expander("Definitions and method notes"):
    st.markdown(
        "- **Financing-stress episode** (formerly 'hurricane-attributable crisis'; definition unchanged): GFN exceeds the "
        f"*no-hurricane path of the same regime* by more than {PARAMS['GFN_margin']:g} points of GDP in at least one year of {T}.\n"
        f"- **3-point storm window**: the threshold is {CFG3['storm_window_margin']:g} points in the strike year and the year after "
        f"(when market access is most fragile) and {PARAMS['GFN_margin']:g} points in all other years. It can reverse the sign of the "
        "high-coverage effect under the baseline repayment (see docs/RESULTS_v3.md, Table 4).\n"
        "- **Expected excess GFN**: the mean over paths of the sum over years of max(0, GFN - no-hurricane GFN - 5), in points of GDP.\n"
        f"- **GFN above {PARAMS['GFN_crit']:g}% of GDP**: absolute level. In the high-debt end of the b0 slider it is 100% by "
        "construction, so the relative measures are the informative ones.\n"
        "- **B' (Grenada's actual repayment)**: deferred amortization is repaid from the year after the suspension ends, due "
        "strike year + 6 years (2030 bond maturity minus the 2024 strike). The sources disagree on the shape, so both are offered: "
        "one lump sum, or equal instalments. Skipped interest is capitalised into the covered stock as in the baseline.\n"
        f"- **Primary balance** is interpolated with initial debt: {pd_bar:+.1f}% of GDP here (positive = deficit).\n"
        "- **Common random numbers**: the same hurricane draws hit every regime, so differences come from the "
        "regime, not from luck; the interval on each change is paired on those draws.\n"
        "- **Rates and growth** are nominal (r = 2.4%, g = 4.8% for Grenada: concessional debt). The high-debt end of the b0 "
        "slider uses r = 5.8% (an assumption).\n"
        "- **Reproducibility**: at N = 10,000 and the defaults (high-coverage, equal instalments over 5 years, fiscal rule on, "
        "b0 = 65, lambda = 0.051, version 1, D_trig = 5) the stress probabilities equal Table 1 of docs/RESULTS_v3.md (23.1% / 24.7%); "
        "choosing B'-lump gives 52.3%.")
