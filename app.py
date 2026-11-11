"""Streamlit demo for the video:  .venv/bin/streamlit run app.py
Runs off the same config/ and src/ code as run_all.py (no duplicated model logic).
Visual theme lives in .streamlit/config.toml; the small CSS block below adds what the theme cannot."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from src import config, experiments, hurricanes, plots

st.set_page_config(page_title="Hurricane-clause model", layout="wide")
PARAMS, SIM, PH = config.load_calibration()
SCEN, PH_S = config.load_scenarios()
DESIGNS, PH_D = config.load_designs()
T, SEED = SIM["T"], SIM["seed"]
LABELS = {"Grenada-style": "grenada_style", "Barbados-style": "barbados_style"}
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


if "s" not in st.session_state:
    st.session_state["preset"] = "Barbados-style"
    load_preset()
    st.session_state["lam"] = float(SCEN["grenada_like"]["lambda"])

# ---------------------------------------------------------------- sidebar: inputs
st.sidebar.header("Clause design")
st.sidebar.selectbox("Preset", list(LABELS), key="preset", on_change=load_preset,
                     help="Loads s, K and the repayment period from config/designs.yaml.")
s = st.sidebar.slider("Share of debt covered (s)", 0.0, 1.0, step=0.05, key="s",
                      help="Fraction of debt service that the clause defers when it triggers.")
K = st.sidebar.slider("Deferral length K (years)", 0, 5, key="K",
                      help="How many years payments are deferred after a trigger.")
m_rep = st.sidebar.slider("Repayment period for deferred principal (years)", 1, 15, key="m_rep",
                          help=f"M = {M} is the normal debt run-off. Below M, deferred amounts are repaid faster "
                               "than normal and create a post-window hump in financing needs.")
d_trig = st.sidebar.slider("Trigger threshold D_trig (% of GDP damage)", 1, 30, int(PARAMS["D_trig"]),
                           help="Minimum hurricane damage, in % of GDP, that activates the clause.")
st.sidebar.header("Country and hurricanes")
b0 = st.sidebar.slider("Initial debt b0 (% of GDP)", 40, 140, int(SCEN["grenada_like"]["b_0"]))
lam = st.sidebar.slider("Hurricane probability per year (lambda)", 0.01, 0.30, step=0.001, key="lam", format="%.3f")
st.sidebar.header("Simulation")
version = st.sidebar.radio("Model version", [1, 2],
                           format_func=lambda v: "1: exogenous rate" if v == 1 else "2: endogenous risk premium")
n_paths = st.sidebar.select_slider("Simulated paths", [2000, 4000, 6000, 10000], value=10000,
                                   help="More paths give smoother estimates but run slower.")


@st.cache_resource
def get_draws(n):
    return hurricanes.draw_noise(SEED, n, T)


@st.cache_data(show_spinner=False)
def run(s, K, m_rep, d_trig, b0, lam, version, n):
    p = {**PARAMS, "s": s, "K": K, "defer_repay_years": m_rep, "D_trig": d_trig}
    scen = {**experiments.scenario_for_b0(b0, SCEN), "lambda": lam}
    base = experiments.baselines(p, scen, version, T)
    out = plots.collect(p, scen, version, get_draws(n), n, T, base)
    return out, scen["pd_bar"]


with st.spinner("Simulating..."):
    data, pd_bar = run(s, K, m_rep, d_trig, b0, lam, version, n_paths)
m = data["m"]
dh = m["A"]["p_hcrisis_any"] - m["B"]["p_hcrisis_any"]
se = np.sqrt(max(m["A"]["p_hcrisis_any"] * (1 - m["A"]["p_hcrisis_any"]), 1e-9) / n_paths)


def change_cell(a, b):
    """Change in crisis probability from A to B, in pp. Lower is better."""
    d = (b - a) * 100
    cls = "flat" if abs(d) < 0.05 else ("better" if d < 0 else "worse")
    return f'<td class="num {cls}">{d:+.1f}&#8239;pp</td>'.replace("-", "&minus;", 1)


# ---------------------------------------------------------------- header
st.title("Do hurricane clauses create fiscal space?")
st.markdown('<p class="lede">A Monte Carlo debt model comparing no clause (A), a hurricane clause that defers debt '
            'service (B), and outright debt relief as a benchmark (C). Adjust the terms in the sidebar.</p>'
            f'<p class="note">{ICON["warn"]}<span>Illustrative only. All {len(PH) + len(PH_S) + len(PH_D)} parameters '
            'in config/ are placeholders (PLACEHOLDER_VERIFY) still awaiting sources.</span></p>',
            unsafe_allow_html=True)

# ---------------------------------------------------------------- verdict + risk table
if dh < -0.005:
    verdict = ("bad", "The clause is harmful with these terms.",
               f"Deferred amounts are repaid faster than the normal 1/M run-off (M = {M}), creating a "
               "post-window hump in financing needs.")
elif dh > 0.005:
    verdict = ("good", "The clause helps liquidity with these terms.",
               f"It lowers the hurricane-attributable crisis risk by {dh*100:.1f} percentage points.")
else:
    verdict = ("flat", "The clause makes little difference with these terms.",
               "Hurricane-attributable crisis risk is about the same with and without it.")

with st.container(key="panel-risk"):
    st.markdown(
        f'<div class="verdict" role="status">{ICON[verdict[0]]}<div><b>{verdict[1]}</b><span>{verdict[2]}</span></div></div>'
        '<table class="risk"><thead><tr><th>Crisis risk over %d years</th><th>No clause</th><th>With clause</th>'
        '<th>Change</th></tr></thead><tbody>'
        '<tr><td><span class="metric">Hurricane-attributable crisis</span><span class="sub">GFN rises more than %g pp '
        'of GDP above the no-hurricane path in at least one year</span></td>'
        '<td class="num">%.1f%%</td><td class="num">%.1f%%</td>%s</tr>'
        '<tr><td><span class="metric">Absolute crisis</span><span class="sub">GFN above %g%% of GDP in at least one '
        'year</span></td><td class="num">%.1f%%</td><td class="num">%.1f%%</td>%s</tr>'
        '</tbody></table>'
        '<p class="foot">Simulation error on the hurricane-attributable rate is about &plusmn;%.1f pp at N = %s.</p>'
        % (T, PARAMS["GFN_margin"], m["A"]["p_hcrisis_any"] * 100, m["B"]["p_hcrisis_any"] * 100,
           change_cell(m["A"]["p_hcrisis_any"], m["B"]["p_hcrisis_any"]), PARAMS["GFN_crit"],
           m["A"]["p_crisis_any"] * 100, m["B"]["p_crisis_any"] * 100,
           change_cell(m["A"]["p_crisis_any"], m["B"]["p_crisis_any"]), 1.96 * se * 100, f"{n_paths:,}"),
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
        "- **Hurricane-attributable crisis**: GFN exceeds the *no-hurricane baseline path* of the same regime by more "
        f"than {PARAMS['GFN_margin']:g} pp of GDP in at least one year of {T}.\n"
        f"- **Absolute crisis**: GFN exceeds GFN_crit = {PARAMS['GFN_crit']:g}% of GDP in at least one year. "
        "In grenada_like the baseline GFN is only about 3-8% of GDP, so the attributable flag (baseline + 5 pp) trips "
        "far more often than the absolute one.\n"
        f"- **Primary balance** is interpolated with initial debt: {pd_bar:+.1f}% of GDP here (positive = deficit).\n"
        "- **Common random numbers**: the same hurricane draws hit every regime, so differences come from the "
        "regime, not from luck.\n"
        "- **Reproducibility**: at N = 10,000 and the defaults (Barbados-style, b0 = 65, lambda = 0.051, version 1, "
        "D_trig = 5) these numbers equal experiment 1's grenada_like rows exactly.")
