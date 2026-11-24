"""Figure 1 (v3). Same style as src/plots.py (Okabe-Ito, A blue / B vermillion, 11-in wide, 3 panels) at 300 dpi."""
from __future__ import annotations
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from . import plots
from .v3 import COUNTRY

COL = plots.COL
LIGHT_B = "#F0B58A"   # lighter vermillion: the low-coverage (Grenada-style) clause


def _row(grid, scenario, design, version, schedule):
    r = grid[(grid.scenario == scenario) & (grid.design == design) & (grid.version == version) & (grid.schedule == schedule)]
    assert len(r) == 1
    return r.iloc[0]


def _label(ax, xs, ys, texts, dy, fs=6.5):
    """Text `texts` (the point estimates) placed at height ys + dy."""
    for x, y, t in zip(xs, ys, texts):
        ax.text(x, y + dy, t, ha="center", va="bottom", fontsize=fs)


def figure1(grid, eqb, n, T, seed, path, version=1):
    plt.rcParams["savefig.dpi"] = 300
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    scens = list(COUNTRY)
    # ---------------------------------------------------------------- Panel A: mean peak GFN, high-coverage clause
    ax = axes[0]
    w = 0.38
    groups = [(s, k) for s in scens for k in (2, 6)]
    for i, (reg, col, lab) in enumerate((("A", COL["A"], "No clause"), ("B", COL["B"], "Clause (5-yr repayment)"))):
        vals = [_row(grid, s, "barbados_style", version, "5yr")[f"peak{k}_{reg}"] for s, k in groups]
        xs = np.arange(len(groups)) + (i - 0.5) * w
        ax.bar(xs, vals, w * 0.94, color=col, label=lab)
        _label(ax, xs, vals, [f"{v:.1f}" for v in vals], 0.3)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([f"{COUNTRY[s]}\n{'strike yr + next' if k == 2 else 'strike yr + 5'}" for s, k in groups], fontsize=6.5)
    ax.set_ylabel("mean peak GFN after a strike (% of GDP)")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.08)
    ax.set_title("A. Mean peak GFN, high-coverage clause", fontsize=8)
    ax.legend(fontsize=7, loc="upper left")
    # ------------------------------------------------------- Panel B: P(financing-stress episode) with 95% CI on every bar
    ax = axes[1]
    bars = [("No clause", COL["A"], None, "grenada_style", "5yr", "a"),
            ("Grenada-style clause", LIGHT_B, None, "grenada_style", "5yr", "b"),
            ("High-coverage clause", COL["B"], None, "barbados_style", "5yr", "b"),
            ("High-coverage clause, B'-lump", COL["B"], "////", "barbados_style", "lump", "b")]
    w = 0.2
    for i, (lab, col, hatch, design, sk, side) in enumerate(bars):
        vals, errs = [], []
        for s in scens:
            r = _row(grid, s, design, version, sk)
            p = r[f"stress_mean_{side}"]
            vals.append(100 * p)
            errs.append(100 * 1.96 * np.sqrt(p * (1 - p) / n))
        xs = np.arange(len(scens)) + (i - 1.5) * w
        ax.bar(xs, vals, w * 0.94, color=col, hatch=hatch, edgecolor="white" if hatch else col, linewidth=0, label=lab)
        ax.errorbar(xs, vals, yerr=errs, fmt="none", ecolor="black", elinewidth=0.8, capsize=2)
        _label(ax, xs, np.array(vals) + np.array(errs), [f"{v:.1f}" for v in vals], 0.4, 6)
    ax.set_xticks(range(len(scens)))
    ax.set_xticklabels([COUNTRY[s] for s in scens], fontsize=8)
    ax.set_xlabel("country (starting conditions)")
    ax.set_ylabel("P(financing-stress episode), %")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    ax.set_title("B. P(financing-stress episode), 95% CI", fontsize=8)
    ax.legend(fontsize=6.3, loc="upper left")
    # --------------------------------------------------------------- Panel C: equal-instalment break-evens (high-coverage)
    ax = axes[2]
    items = [(s, v) for s in scens for v in (1, 2)]
    vals = []
    for s, v in items:
        r = eqb[(eqb.scenario == s) & (eqb.version == v)].iloc[0]
        vals.append(r.switch_years if np.isfinite(r.switch_years) else np.nan)
    xs = np.arange(len(items))
    ax.bar(xs, np.nan_to_num(vals), 0.6, color=[COL["B"]] * len(items))
    for x, v in zip(xs, vals):
        ax.text(x, (0 if np.isnan(v) else v) + 0.15, "undefined" if np.isnan(v) else f"{v:.1f}", ha="center", va="bottom", fontsize=7)
    ax.axhline(5, color="black", lw=0.9, ls="--", label="contractual 5-yr repayment")
    ax.legend(fontsize=6.5, loc="upper left")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{COUNTRY[s]}\nV{v}" for s, v in items], fontsize=7)
    ax.set_ylabel("break-even repayment period (years)")
    ax.set_xlabel("V1 = fixed r, V2 = risk premium")
    ax.set_ylim(0, max(np.nanmax(vals), 5) * 1.18)
    ax.set_title("C. Equal-instalment break-evens", fontsize=8)
    fig.suptitle(None)
    fig.text(0.01, 0.005, f"Simulated, N={n:,} paths, T={T} yrs, seed {seed}, common random numbers across regimes. Panels A-B: Version 1 "
             "(fixed r), 5-yr equal-instalment repayment unless stated; panel B bars: marginal 95% CI of each probability (normal approx.). "
             "Financing-stress episode: GFN > 5 pp of GDP above the same regime's no-hurricane path in at least one year.",
             fontsize=5.8, va="bottom", wrap=True)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300)
    plt.close(fig)


# ======================================================================================================== Figure 1, v4
def figure_data(grid, eqb, n, version=1):
    """The numbers printed on Figure 1 (v4), one-decimal strings included: the figure and RESULTS_v4.md both read this."""
    scens = list(COUNTRY)
    A = []   # panel A: (country, window, schedule-key, value)
    for s in scens:
        for k in (2, 6):
            a = _row(grid, s, "barbados_style", version, "5yr")
            l = _row(grid, s, "barbados_style", version, "lump")
            for lab, v in (("No clause", a[f"peak{k}_A"]), ("Clause, five-year instalments", a[f"peak{k}_B"]), ("Clause, lump sum (B'-lump)", l[f"peak{k}_B"])):
                A.append({"country": COUNTRY[s], "window": "strike yr + next" if k == 2 else "strike yr + 5", "bar": lab, "value": float(v)})
    B = []   # panel B: (country, bar, P %, CI half-width %)
    for s in scens:
        for lab, design, sk, side in (("No clause", "grenada_style", "5yr", "a"), ("Grenada-style clause", "grenada_style", "5yr", "b"),
                                      ("High-coverage clause", "barbados_style", "5yr", "b"), ("High-coverage clause, B'-lump", "barbados_style", "lump", "b")):
            p = _row(grid, s, design, version, sk)[f"stress_mean_{side}"]
            B.append({"country": COUNTRY[s], "bar": lab, "value": 100 * p, "ci_half": 100 * 1.96 * float(np.sqrt(p * (1 - p) / n))})
    C = []
    for s in scens:
        for v in (1, 2):
            r = eqb[(eqb.scenario == s) & (eqb.version == v)].iloc[0]
            C.append({"country": COUNTRY[s], "version": f"V{v}", "value": float(r.switch_years) if np.isfinite(r.switch_years) else np.nan})
    return {"A": A, "B": B, "C": C}


def figure1_v4(grid, eqb, n, path, version=1):
    plt.rcParams["savefig.dpi"] = 300
    data = figure_data(grid, eqb, n, version)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    scens = list(COUNTRY)
    # ---- Panel A: three bars per group
    ax = axes[0]
    labs = ["No clause", "Clause, five-year instalments", "Clause, lump sum (B'-lump)"]
    styles = [(COL["A"], None), (COL["B"], None), (COL["B"], "////")]
    groups = [(s, w) for s in scens for w in ("strike yr + next", "strike yr + 5")]
    w3 = 0.27
    for i, (lab, (col, hatch)) in enumerate(zip(labs, styles)):
        vals = [next(d["value"] for d in data["A"] if d["country"] == COUNTRY[s] and d["window"] == w and d["bar"] == lab) for s, w in groups]
        xs = np.arange(len(groups)) + (i - 1) * w3
        ax.bar(xs, vals, w3 * 0.94, color=col, hatch=hatch, edgecolor="white" if hatch else col, linewidth=0, label=lab)
        _label(ax, xs, vals, [f"{v:.1f}" for v in vals], 0.3, 6)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([f"{COUNTRY[s]}\n{w}" for s, w in groups], fontsize=6.5)
    ax.set_ylabel("mean peak GFN after a strike (% of GDP)")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.22)
    ax.set_title("A. Mean peak GFN, high-coverage clause", fontsize=8)
    ax.legend(fontsize=6.3, loc="upper left")
    # ---- Panel B
    ax = axes[1]
    blabs = ["No clause", "Grenada-style clause", "High-coverage clause", "High-coverage clause, B'-lump"]
    bst = [(COL["A"], None), (LIGHT_B, None), (COL["B"], None), (COL["B"], "////")]
    wb = 0.2
    keys = ["No clause", "Grenada-style clause", "High-coverage clause", "High-coverage clause, B'-lump"]
    for i, (lab, (col, hatch)) in enumerate(zip(blabs, bst)):
        rows = [next(d for d in data["B"] if d["country"] == COUNTRY[s] and d["bar"] == keys[i]) for s in scens]
        vals, errs = [r["value"] for r in rows], [r["ci_half"] for r in rows]
        xs = np.arange(len(scens)) + (i - 1.5) * wb
        ax.bar(xs, vals, wb * 0.94, color=col, hatch=hatch, edgecolor="white" if hatch else col, linewidth=0, label=lab)
        ax.errorbar(xs, vals, yerr=errs, fmt="none", ecolor="black", elinewidth=0.8, capsize=2)
        _label(ax, xs, np.array(vals) + np.array(errs), [f"{v:.1f}" for v in vals], 0.4, 6)
    ax.set_xticks(range(len(scens)))
    ax.set_xticklabels([COUNTRY[s] for s in scens], fontsize=8)
    ax.set_xlabel("country (starting conditions)")
    ax.set_ylabel("P(financing-stress episode), %")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    ax.set_title("B. P(financing-stress episode), 95% CI", fontsize=8)
    ax.legend(fontsize=6.3, loc="upper left")
    # ---- Panel C
    ax = axes[2]
    vals = [d["value"] for d in data["C"]]
    xs = np.arange(len(vals))
    ax.bar(xs, np.nan_to_num(vals), 0.6, color=[COL["B"]] * len(vals))
    for x, v in zip(xs, vals):
        ax.text(x, (0 if np.isnan(v) else v) + 0.15, "undefined" if np.isnan(v) else f"{v:.1f}", ha="center", va="bottom", fontsize=7)
    ax.axhline(5, color="black", lw=0.9, ls="--", label="five-year instalments (assumed)")
    ax.legend(fontsize=6.5, loc="upper left")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{d['country']}\n{d['version']}" for d in data["C"]], fontsize=7)
    ax.set_ylabel("break-even repayment period (years)")
    ax.set_xlabel("V1 = fixed r, V2 = risk premium")
    ax.set_ylim(0, max(np.nanmax(vals), 5) * 1.18)
    ax.set_title("C. Equal-instalment break-evens", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return data
