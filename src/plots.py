"""Publication figures. Palette: Okabe-Ito colours, one fixed colour per regime in every figure
(A blue, B vermillion, C green; validated colour-blind-safe). Each figure carries a source/assumption caption."""
from __future__ import annotations
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from . import metrics, simulate

COL = {"A": "#0072B2", "B": "#D55E00", "C": "#009E73"}
LAB = {"A": "A: no clause", "B": "B: clause (deferral)", "C": "C: debt relief (benchmark)"}
DLAB = {"grenada_style": "Grenada-style clause", "barbados_style": "Barbados-style clause"}
SLAB = {"grenada_like": "grenada_like (liquidity)", "high_debt": "high_debt (solvency)",
        "grenada_like_lambda_010": "grenada_like, lambda=0.10"}
NOTE = ("Simulated, N={n:,} paths, T={T} yrs, seed {seed}, common random numbers across regimes. ALL parameters are "
        "PLACEHOLDER_VERIFY (unsourced).")
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5, "figure.dpi": 100,
                     "savefig.dpi": 200, "legend.frameon": False})
CAPTIONS: dict[str, str] = {}
QA: dict[str, list] = {}




def qa_figure(fig, name, caption, cap_artist=None):
    """Programmatic QA: axis labels, legend with regime names, titles inside the canvas, caption present."""
    issues = []
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    W, H = fig.bbox.width, fig.bbox.height
    axes = [a for a in fig.axes if a.get_label() != "<colorbar>" and not (a.get_xlabel() == "" and a.get_ylabel() == "" and a.get_title() == "" and not a.has_data())]
    rows = {}
    for a in axes:
        if not a.has_data() and not a.images:
            continue
        if not a.get_xlabel() and not any(b.get_xlabel() for b in a.get_shared_x_axes().get_siblings(a)):
            issues.append("axis without x-label")
        rows.setdefault(round(a.get_position().y0, 2), []).append(a)
        t = a.title.get_window_extent(rend)
        if t.x0 < -1 or t.x1 > W + 1 or t.y1 > H + 1:
            issues.append(f"clipped title: {a.get_title()[:40]!r}")
    for y, row in rows.items():
        if not any(a.get_ylabel() or any(b.get_ylabel() for b in a.get_shared_y_axes().get_siblings(a)) for a in row):
            issues.append("row without y-label")
    is_heat = name.startswith(("heatmap", "design_sensitivity"))
    has_legend = any(a.get_legend() for a in fig.axes)
    if not is_heat:
        if not has_legend: issues.append("no legend")
        else:
            labels = " ".join(t.get_text() for a in fig.axes if a.get_legend() for t in a.get_legend().get_texts())
            if not name.startswith(("fan",)) and "A: no clause" not in labels: issues.append("legend lacks regime labels")
        if not any(("clause" in a.get_title().lower()) for a in fig.axes):
            issues.append("no design label in any title")
    if is_heat and not any(ax.get_ylabel() for ax in fig.axes if ax.get_label() == "<colorbar>"):
        issues.append("colorbar without unit label")
    if not caption.strip() or "PLACEHOLDER_VERIFY" not in caption: issues.append("caption missing or lacks placeholder note")
    if cap_artist is not None:
        bb = cap_artist.get_window_extent(rend)
        if bb.x1 > W - 2 or bb.x0 < 0 or bb.y1 > H * 0.30: issues.append("caption clipped or too tall")
    QA[name] = issues


def _save(fig, outdir, name, caption):
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    import textwrap
    wrapped = textwrap.fill(caption, width=int(fig.get_figwidth() * 15.5))
    nlines = wrapped.count("\n") + 1
    fig.tight_layout(rect=(0, (0.12 + 0.115 * nlines) / fig.get_figheight(), 1, 1))
    cap_artist = fig.text(0.01, 0.005, wrapped, fontsize=6.5, color="#444", ha="left", va="bottom")
    qa_figure(fig, name, caption, cap_artist)
    fig.savefig(outdir / f"{name}.png"); plt.close(fig)
    CAPTIONS[name] = caption


# ----------------------------------------------------------------------------------------- data collection
def event_windows(sim, d_trig, pre=2, post=5):
    """Average GFN from t-pre to t+post around qualifying hits that have a complete window; also the 'clean' variant
    with no other qualifying hit inside the window."""
    D = sim["D"]; gfn = sim["gfn"][:, 1:]; N, T = D.shape
    H = D >= d_trig
    acc = {"all": np.zeros(pre + post + 1), "clean": np.zeros(pre + post + 1)}
    cnt = {"all": 0, "clean": 0}
    for t in range(1 + pre, T - post + 1):                 # year t; zero-based index t-1
        ev = H[:, t - 1]
        win = gfn[:, t - 1 - pre:t + post]
        n_hits = H[:, t - 1 - pre:t + post].sum(axis=1)
        for k, m in (("all", ev), ("clean", ev & (n_hits == 1))):
            acc[k] += win[m].sum(axis=0); cnt[k] += int(m.sum())
    return {k: (acc[k] / max(cnt[k], 1), cnt[k]) for k in acc}


def pick_sample_path(D, d_trig):
    """First path with exactly two qualifying hits at least 3 years apart, each >= 10% of GDP (else first with a hit)."""
    H = D >= d_trig
    for i in range(D.shape[0]):
        yrs = np.flatnonzero(H[i])
        if len(yrs) == 2 and yrs[1] - yrs[0] >= 3 and (D[i, yrs] >= 10).all() and 3 <= yrs[0] + 1 <= 12:
            return i
    return int(np.argmax(H.any(axis=1)))


def collect(params, scenario, version, draws, n_paths, horizon, baseline):
    runs = simulate.run_regimes(params, scenario, version, draws=draws, n_paths=n_paths, horizon=horizon)
    out = {"q": {}, "ew": {}, "m": {}, "path": {}}
    i = pick_sample_path(runs["A"]["D"], params["D_trig"])
    for r, sim in runs.items():
        b = sim["b"]
        out["q"][r] = np.percentile(b, [5, 25, 50, 75, 95], axis=0)
        out["ew"][r] = event_windows(sim, params["D_trig"])
        m = metrics.summarize(sim, params, baseline[r] if isinstance(baseline, dict) else baseline)
        out["m"][r] = {k: m[k] for k in ("p_crisis_any", "p_hcrisis_any", "p_bT_gt100")}
        out["path"][r] = {"b": b[i], "gfn": sim["gfn"][i], "susp": sim["suspended"][i]}
    out["path"]["D"] = runs["A"]["D"][i]
    out["path"]["idx"] = i
    return out


# ------------------------------------------------------------------------------------------------- panels
def _logify(ax, ticks=(10, 20, 50, 100, 200, 500, 1000, 2000)):
    """Log y-axis with plain-number tick labels (used when a spiral makes the linear scale unreadable)."""
    from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
    ax.set_yscale("log")
    lo, hi = ax.get_ylim()
    t = [v for v in ticks if lo <= v <= hi]
    ax.yaxis.set_major_locator(FixedLocator(t)); ax.yaxis.set_major_formatter(FixedFormatter([f"{v:g}" for v in t]))
    ax.yaxis.set_minor_locator(NullLocator())


def draw_fan(ax, q, r, T, title, ylabel=True, legend=False, logy=False):
    """One fan-chart panel: median plus 50% and 90% bands of debt/GDP for regime r."""
    x = np.arange(T + 1)
    ax.fill_between(x, q[0], q[4], color=COL[r], alpha=0.15, lw=0, label="90% band")
    ax.fill_between(x, q[1], q[3], color=COL[r], alpha=0.30, lw=0, label="50% band")
    ax.plot(x, q[2], color=COL[r], lw=2, label="median")
    ax.axhline(100, color="#777", lw=0.8, ls=":")
    ax.set_title(title, fontsize=8.5); ax.set_xlabel("year (t)")
    ax.set_ylabel("debt, % of GDP" if ylabel else "")
    if legend: ax.legend(loc="upper left", fontsize=7)
    if logy:
        _logify(ax)
        ax.set_ylabel("debt, % of GDP (log scale)" if ylabel else "")


def draw_event(ax, ew, title, clean=False, ylabel=True, legend=False, logy=False):
    """Average GFN from t-2 to t+5 around a qualifying hit for the three regimes."""
    x = np.arange(-2, 6)
    for r in "ABC":
        y, cnt = ew[r]["clean" if clean else "all"]
        ax.plot(x, y, color=COL[r], lw=2, marker="o", ms=3.5, label=LAB[r])
    ax.axvline(0, color="#777", lw=0.8, ls=":")
    ax.set_title(f"{title} (n={cnt:,} events)", fontsize=8)
    ax.set_xlabel("years from hurricane hit (t = 0)")
    ax.set_ylabel("average GFN, % of GDP" if ylabel else "")
    if legend: ax.legend(fontsize=7)
    if logy:
        _logify(ax, ticks=(1, 2, 3, 5, 7, 10, 15, 20, 30, 40, 50, 60, 80, 100, 120, 150, 200))
        ax.set_ylabel("average GFN, % of GDP (log scale)" if ylabel else "")


# ------------------------------------------------------------------------------------------------- figures
def fan_charts(data, params, outdir, version, n, T, seed):
    """data[(scenario, design)] -> collect(). One figure per scenario: Regime A once (it does not depend on the clause
    design) in the left column, Regimes B and C for each design to its right. Log y-axis when a spiral makes the linear
    scale unreadable (95th percentile above 400% of GDP)."""
    scens = sorted({k[0] for k in data}); designs = sorted({k[1] for k in data})
    for sc in scens:
        spiral = max(data[(sc, d)]["q"][r][4].max() for d in designs for r in "ABC") > 400
        fig = plt.figure(figsize=(10, 3.4 * len(designs)))
        gs = fig.add_gridspec(len(designs), 3)
        axA = fig.add_subplot(gs[:, 0])
        draw_fan(axA, data[(sc, designs[0])]["q"]["A"], "A", T, LAB["A"] + "\n(same in both clause designs)", legend=True, logy=spiral)
        for i, d in enumerate(designs):
            for j, r in enumerate("BC"):
                ax = fig.add_subplot(gs[i, j + 1], sharey=axA)
                draw_fan(ax, data[(sc, d)]["q"][r], r, T, f"{LAB[r]}\n{DLAB[d]}", ylabel=False, logy=spiral)
                ax.tick_params(labelleft=True)
        cap = (f"Debt/GDP fan charts, {SLAB.get(sc, sc)}, model version {version} "
               f"({'exogenous rate' if version == 1 else 'endogenous risk premium, capped'}). Bands: 50% and 90% of paths; "
               "dotted line = 100% of GDP. " + ("Log y-axis (debt spiral). " if spiral else "") + NOTE.format(n=n, T=T, seed=seed))
        _save(fig, outdir, f"fan_{sc}_v{version}", cap)


def event_window_chart(data, outdir, version, n, T, seed, clean=False):
    scens = sorted({k[0] for k in data}); designs = sorted({k[1] for k in data})
    fig, axes = plt.subplots(len(designs), len(scens), figsize=(4.2 * len(scens), 3.2 * len(designs)), squeeze=False)
    logs = []
    for i, d in enumerate(designs):
        for j, sc in enumerate(scens):
            ew = data[(sc, d)]["ew"]
            logy = max(ew[r]["clean" if clean else "all"][0].max() for r in "ABC") > 60   # GFN spiral
            logs.append(logy)
            draw_event(axes[i, j], ew, f"{SLAB.get(sc, sc)} | {DLAB[d]}", clean=clean,
                       ylabel=(j == 0), legend=(i == 0 and j == 0), logy=logy)
    kind = ("CLEAN windows: no second qualifying hit between t-2 and t+5." if clean else
            "all qualifying hits with a complete t-2..t+5 window; windows may contain subsequent hits.")
    cap = (f"Average gross financing needs around a hurricane (damage >= D_trig), version {version}: the clause flattens "
           f"the spike; any repayment hump appears after the window. " + ("Panels with a GFN spiral use a log y-axis. " if any(logs) else "") + f"Events: {kind} " + NOTE.format(n=n, T=T, seed=seed))
    _save(fig, outdir, f"event_window{'_clean' if clean else ''}_v{version}", cap)


def bar_charts(data, outdir, version, n, T, seed):
    scens = sorted({k[0] for k in data}); designs = sorted({k[1] for k in data})
    mets = [("p_crisis_any", "P(GFN > GFN_crit at least once)"),
            ("p_hcrisis_any", "P(hurricane-attributable crisis)"),
            ("p_bT_gt100", "P(terminal debt > 100% of GDP)")]
    fig, axes = plt.subplots(len(designs), 3, figsize=(11, 3.2 * len(designs)), squeeze=False, sharey=True)
    w = 0.26
    for i, d in enumerate(designs):
        for j, (mk, ml) in enumerate(mets):
            ax = axes[i, j]
            for k, r in enumerate("ABC"):
                vals = [data[(s, d)]["m"][r][mk] for s in scens]
                xs = np.arange(len(scens)) + (k - 1) * w
                ax.bar(xs, vals, w * 0.92, color=COL[r], label=LAB[r])
                for xx, v in zip(xs, vals): ax.text(xx, v + 0.015, f"{v:.0%}", ha="center", fontsize=6.5)
            ax.set_xticks(np.arange(len(scens))); ax.set_xticklabels([SLAB.get(s, s).split(" (")[0] for s in scens], fontsize=7)
            ax.set_title(f"{ml}\n{DLAB[d]}", fontsize=8); ax.set_ylim(0, 1.12); ax.set_xlabel("scenario (starting conditions)")
            ax.set_ylabel("probability") if j == 0 else None
            if i == 0 and j == 0: ax.legend(fontsize=7, loc="upper left")
    cap = (f"Liquidity and solvency risk by regime and scenario, version {version}. The absolute crisis flag is 100% in "
           "high_debt by construction (starting GFN above the threshold); the hurricane-attributable flag (GFN > no-hurricane "
           "baseline + margin) separates regimes. " + NOTE.format(n=n, T=T, seed=seed))
    _save(fig, outdir, f"bars_v{version}", cap)


def _heat(ax, M, xs, ys, title, vmax, cmap="BrBG"):
    im = ax.imshow(M, origin="lower", aspect="auto", cmap=cmap, vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(len(xs))); ax.set_xticklabels([f"{v:g}" if not isinstance(v, str) else v for v in xs], fontsize=7)
    ax.set_yticks(range(len(ys))); ax.set_yticklabels([f"{v:g}" if not isinstance(v, str) else v for v in ys], fontsize=7)
    ax.grid(False); ax.set_title(title, fontsize=8)
    return im


def heatmaps(grid, outdir, n, T, seed):
    """Benefit of the clause (A minus B; positive = clause helps) over initial debt x hurricane probability.
    Panels: (a) mean peak GFN, (b) hurricane-attributable crisis probability (informative everywhere), (c) absolute
    crisis probability, with cells masked (grey) where a crisis happens with certainty without the clause (A >= 99%).
    Colour scale winsorized at the 95th percentile of |benefit| per panel (true max printed in the caption)."""
    for v in sorted(grid.version.unique()):
        for d in sorted(grid.design.unique()):
            g = grid[(grid.version == v) & (grid.design == d)]
            fig, axes = plt.subplots(1, 3, figsize=(14, 3.8))
            notes = []
            panels = [("benefit_peak_gfn2_mean", "reduction in mean peak GFN (pp of GDP)", 1.0, False),
                      ("benefit_p_hcrisis_any", "reduction in P(hurricane-attributable crisis) (pp)", 100.0, False),
                      ("benefit_p_crisis_any", "reduction in P(GFN > GFN_crit) (pp)", 100.0, True)]
            for ax, (col, ttl, scale, mask) in zip(axes, panels):
                M = g.pivot(index="b_0", columns="lambda", values=col)
                vals = np.ma.masked_invalid(M.values * scale)
                if mask:
                    certain = g.pivot(index="b_0", columns="lambda", values="A_p_crisis_any").values >= 0.99
                    vals = np.ma.masked_where(certain, vals)
                vmax = float(np.nanpercentile(np.abs(vals.compressed()), 95)) or 1.0
                cm = plt.get_cmap("BrBG").copy(); cm.set_bad("#c8c8c8")
                im = ax.imshow(vals, origin="lower", aspect="auto", cmap=cm, vmin=-vmax, vmax=vmax)
                ax.set_xticks(range(M.shape[1])); ax.set_xticklabels([f"{c:g}" for c in M.columns], fontsize=7)
                ax.set_yticks(range(M.shape[0])); ax.set_yticklabels([f"{b:.0f}" for b in M.index], fontsize=7)
                ax.grid(False); ax.set_title(ttl, fontsize=8)
                hidden = np.ma.getmaskarray(vals)
                for a_ in range(vals.shape[0]):
                    for b_ in range(vals.shape[1]):
                        ax.text(b_, a_, "n/a" if hidden[a_, b_] else f"{vals[a_, b_]:.1f}", ha="center", va="center",
                                fontsize=5.5, color="#555" if hidden[a_, b_] else "k")
                ax.set_xlabel("annual hurricane probability lambda"); ax.set_ylabel("initial debt, % of GDP")
                fig.colorbar(im, ax=ax, shrink=0.85, extend="both", label="pp (positive = clause helps)")
                notes.append(f"{ttl}: true max {vals.max():.1f}, min {vals.min():.1f}, colour scale +/-{vmax:.1f}")
            cap = (f"Clause benefit, {DLAB[d]}, version {v}. The debt axis varies the fiscal stance jointly (primary balance "
                   "interpolated between the two scenarios), so it is a vulnerability gradient, not a pure debt gradient. "
                   "Positive = clause helps. Grey 'n/a' = GFN exceeds GFN_crit with certainty even without the clause (>= 99%), so the "
                   "absolute-crisis benefit is undefined; panel (b) is informative there. Colour scale winsorized at the 95th "
                   "percentile; " + "; ".join(notes) + ". " + NOTE.format(n=n, T=T, seed=seed))
            _save(fig, outdir, f"heatmap_{d}_v{v}", cap)


def design_heatmaps(sens, outdir, n, T, seed, metric="benefit_p_hcrisis_any", label="reduction in P(hurricane-attributable crisis) (pp)",
                    tag="hcrisis", scale=100.0):
    for v in sorted(sens.version.unique()):
        for d in sorted(sens.design.unique()):
            scens = sorted(sens.scenario.unique())
            fig, axes = plt.subplots(len(scens), 2, figsize=(9, 3.4 * len(scens)), squeeze=False)
            for i, sc in enumerate(scens):
                g = sens[(sens.version == v) & (sens.design == d) & (sens.scenario == sc)]
                m0 = g.defer_repay_years.mode()[0]; dt0 = g.D_trig.mode()[0]
                a = g[g.defer_repay_years == m0].pivot(index="K", columns="D_trig", values=metric) * scale
                b = g[g.D_trig == dt0].pivot(index="K", columns="defer_repay_years", values=metric) * scale
                vmax = float(np.nanpercentile(np.abs(np.r_[a.values.ravel(), b.values.ravel()]), 95)) or 1.0
                for ax, M, xl in ((axes[i, 0], a, "trigger threshold D_trig (% of GDP damage)"),
                                  (axes[i, 1], b, "deferred-principal repayment years")):
                    im = _heat(ax, M.values, list(M.columns), list(M.index), SLAB.get(sc, sc), vmax)
                    for (r_, c_), z in np.ndenumerate(M.values): ax.text(c_, r_, f"{z:.1f}", ha="center", va="center", fontsize=6)
                    ax.set_xlabel(xl); ax.set_ylabel("deferral length K (years)")
                    fig.colorbar(im, ax=ax, shrink=0.85, extend="both", label="pp (positive = clause helps)")
            cap = (f"Sensitivity to clause design, {DLAB[d]}, version {v}: {label}; positive = clause helps, negative = harmful "
                   "(fast catch-up creates a repayment hump). Colour scale winsorized at the 95th percentile. " + NOTE.format(n=n, T=T, seed=seed))
            _save(fig, outdir, f"design_sensitivity_{tag}_{d}_v{v}", cap)


def sample_path(data_one, params, outdir, name, title, T, seed):
    """One simulated history: hurricane hits marked, debt and GFN under each regime."""
    p = data_one["path"]; x = np.arange(T + 1)
    fig, axes = plt.subplots(2, 1, figsize=(8, 6.2), sharex=True)
    for r in "ABC":
        axes[0].plot(x, p[r]["b"], color=COL[r], lw=2 if r != "A" else 2.4, ls="-" if r != "B" else "--", label=LAB[r])
        axes[1].plot(x[1:], p[r]["gfn"][1:], color=COL[r], lw=2, ls="-" if r != "B" else "--", label=LAB[r])
    axes[1].axhline(params["GFN_crit"], color="#777", lw=0.8, ls=":"); axes[1].text(T, params["GFN_crit"], " GFN_crit", fontsize=7, va="bottom", ha="right", color="#555")
    for t, dmg in enumerate(p["D"], start=1):
        if dmg >= params["D_trig"]:
            for ax in axes: ax.axvline(t, color="#CC79A7", lw=1.2, alpha=0.8)
            axes[0].annotate(f"hurricane\n{dmg:.0f}% of GDP", (t, axes[0].get_ylim()[1]), fontsize=7, color="#CC79A7", ha="left", va="top")
    axes[0].set_ylabel("debt, % of GDP"); axes[1].set_ylabel("gross financing needs, % of GDP"); axes[1].set_xlabel("year")
    axes[0].legend(fontsize=7, loc="best"); axes[0].set_title(title, fontsize=9)
    cap = ("One simulated history (path #%d of the common draws); vertical lines mark qualifying hurricane hits. The clause (B) "
           "lowers GFN during the deferral window; debt equals A (version 1 stock identity) while C's debt falls. " % p["idx"]
           + f"seed {seed}; ALL parameters PLACEHOLDER_VERIFY.")
    _save(fig, outdir, name, cap)


def qa_report(outdir):
    """Write outputs/figures/QA_REPORT.md; also checks that every PNG has a caption entry. Returns (n_figs, n_issues)."""
    p = pathlib.Path(outdir)
    pngs = sorted(x.stem for x in p.glob("*.png"))
    missing = [n for n in pngs if n not in CAPTIONS]
    lines = ["# Figure QA (programmatic, auto-generated)\n"]
    for n in sorted(QA):
        lines.append(f"- **{n}**: " + ("OK" if not QA[n] else "; ".join(sorted(set(QA[n])))))
    if missing: lines.append(f"\nFigures without caption entry: {missing}")
    (p / "QA_REPORT.md").write_text("\n".join(lines) + "\n")
    return len(pngs), sum(len(v) for v in QA.values()) + len(missing)


def write_captions(outdir):
    p = pathlib.Path(outdir)
    p.mkdir(parents=True, exist_ok=True)
    (p / "CAPTIONS.md").write_text("# Figure captions (auto-generated by run_all.py)\n\n" +
                                   "\n".join(f"- **{k}.png**: {v}\n" for k, v in sorted(CAPTIONS.items())))
