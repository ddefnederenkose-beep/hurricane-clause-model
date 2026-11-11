"""Streamlit demo for the video:  .venv/bin/streamlit run app.py
Runs off the same config/ and src/ code as run_all.py (no duplicated model logic)."""
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


def load_preset():
    d = DESIGNS[LABELS[st.session_state["preset"]]]["overrides"]
    st.session_state["s"], st.session_state["K"] = float(d["s"]), int(d["K"])
    st.session_state["m_rep"] = int(d["defer_repay_years"])


if "s" not in st.session_state:
    st.session_state["preset"] = "Barbados-style"
    load_preset()
    st.session_state["lam"] = float(SCEN["grenada_like"]["lambda"])

st.sidebar.header("Clause design")
st.sidebar.selectbox("Preset (loads s, K, repayment years)", list(LABELS), key="preset", on_change=load_preset)
s = st.sidebar.slider("Share of debt covered, s", 0.0, 1.0, step=0.05, key="s")
K = st.sidebar.slider("Deferral length K (years)", 0, 5, key="K")
m_rep = st.sidebar.slider("Deferred principal repaid over (years)  [M = %d = no hump]" % PARAMS["M"], 1, 15, key="m_rep")
d_trig = st.sidebar.slider("Trigger threshold D_trig (% of GDP damage)", 1, 30, int(PARAMS["D_trig"]))
st.sidebar.header("Country and hurricanes")
b0 = st.sidebar.slider("Initial debt b0 (% of GDP)", 40, 140, int(SCEN["grenada_like"]["b_0"]))
lam = st.sidebar.slider("Hurricane probability per year, lambda", 0.01, 0.30, step=0.001, key="lam", format="%.3f")
version = st.sidebar.radio("Model version", [1, 2], format_func=lambda v: "1: exogenous rate" if v == 1 else "2: endogenous risk premium")
n_paths = st.sidebar.select_slider("Simulated paths (more = smoother, slower)", [2000, 4000, 6000, 10000], value=10000)


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


data, pd_bar = run(s, K, m_rep, d_trig, b0, lam, version, n_paths)
st.title("Do hurricane clauses create fiscal space?")
st.warning("All parameters are PLACEHOLDER_VERIFY (unsourced): %d values in config/. Illustrative only." % (len(PH) + len(PH_S) + len(PH_D)))
st.caption(f"Primary balance interpolated with initial debt: {pd_bar:+.1f}% of GDP (positive = deficit). "
           f"Same hurricane draws in every regime (common random numbers).")

m = data["m"]
dh = m["A"]["p_hcrisis_any"] - m["B"]["p_hcrisis_any"]
se = np.sqrt(max(m["A"]["p_hcrisis_any"] * (1 - m["A"]["p_hcrisis_any"]), 1e-9) / n_paths)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Hurricane-attributable crisis: no clause", f"{m['A']['p_hcrisis_any']:.1%}",
          help="P(GFN_t exceeds this regime's own no-hurricane GFN path by more than GFN_margin = %g pp of GDP in at least one of %d years)." % (PARAMS["GFN_margin"], T))
c2.metric("... with the clause", f"{m['B']['p_hcrisis_any']:.1%}", f"{-dh*100:+.1f} pp", delta_color="inverse")
c3.metric("GFN above GFN_crit: no clause", f"{m['A']['p_crisis_any']:.1%}",
          help="P(GFN_t > GFN_crit = %g%% of GDP in at least one of %d years). An absolute threshold: a different (stricter) metric." % (PARAMS["GFN_crit"], T))
c4.metric("... with the clause", f"{m['B']['p_crisis_any']:.1%}", f"{-(m['A']['p_crisis_any'] - m['B']['p_crisis_any'])*100:+.1f} pp", delta_color="inverse")
st.caption(f"Simulation error on the hurricane-attributable rate is about +/-{1.96*se*100:.1f} pp at N = {n_paths:,}. "
           "At N = 10,000 and the defaults (Barbados-style, b0 = 65, lambda = 0.051, version 1, D_trig = 5) these numbers equal "
           "experiment 1's grenada_like rows exactly. The same hurricane draws hit every regime.")
with st.expander("Definitions"):
    st.markdown("- **Hurricane-attributable crisis**: GFN exceeds the *no-hurricane baseline path* of the same regime by more than "
                f"{PARAMS['GFN_margin']:g} pp of GDP in at least one year of {T}.\n"
                f"- **GFN above GFN_crit**: GFN exceeds {PARAMS['GFN_crit']:g}% of GDP in at least one year (absolute). "
                "In grenada_like the baseline GFN is only about 3-8% of GDP, so the attributable flag (baseline + 5 pp) trips "
                "far more often than the absolute one.")
if dh < -0.005:
    st.error("With these terms the clause is HARMFUL: repayment of deferred amounts comes faster than the normal 1/M run-off, "
             "creating a post-window hump in financing needs.")
elif dh > 0.005:
    st.success("With these terms the clause HELPS liquidity (lower hurricane-attributable crisis risk).")
else:
    st.info("With these terms the clause makes little difference.")

fig1, axes = plt.subplots(1, 3, figsize=(11, 3.3), sharey=True)
for ax, r in zip(axes, "ABC"):
    plots.draw_fan(ax, data["q"][r], r, T, plots.LAB[r], ylabel=(r == "A"), legend=(r == "A"))
fig1.tight_layout()
st.subheader("Debt/GDP fan charts")
st.pyplot(fig1)
fig2, ax = plt.subplots(figsize=(7, 3.6))
plots.draw_event(ax, data["ew"], f"b0={b0}, lambda={lam:.3f}", legend=True)
fig2.tight_layout()
st.subheader("Gross financing needs around a hurricane")
st.pyplot(fig2)
st.caption("Version 1: stocks of A and B are identical, so only GFN differs. Set repayment years below M to see the hump; "
           "set it to M or above to see the clause help.")
