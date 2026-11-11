"""Summary metrics for a simulated regime (all on years 1..T)."""
from __future__ import annotations
import numpy as np


def event_peak_gfn(sim: dict, d_trig: float, window: int = 2) -> np.ndarray:
    """Peak GFN over `window` years starting in the hit year (t..t+window-1), one value per qualifying
    event (D >= D_trig) pooled over paths. Events whose window runs past T are dropped."""
    gfn = sim["gfn"][:, 1:]
    D = sim["D"]
    T = D.shape[1]
    n_start = T - window + 1
    win = np.max(np.stack([gfn[:, w:w + n_start] for w in range(window)], axis=0), axis=0)
    return win[D[:, :n_start] >= d_trig]


def _peak_stats(peaks, tag):
    return {f"peak_gfn{tag}_mean": float(peaks.mean()) if peaks.size else np.nan,
            f"peak_gfn{tag}_p95": float(np.percentile(peaks, 95)) if peaks.size else np.nan}


def summarize(sim: dict, params: dict, baseline_gfn=None) -> dict:
    """baseline_gfn: no-hurricane (lambda=0) GFN path, shape (T+1,) or (N,T+1), for the hurricane-attributable
    crisis flag (GFN_t > baseline_t + GFN_margin)."""
    gfn = sim["gfn"][:, 1:]
    b = sim["b"][:, 1:]
    crisis = gfn > params["GFN_crit"]
    bT = b[:, -1]
    out = {"n_events": int(event_peak_gfn(sim, params["D_trig"], 2).size)}
    out.update(_peak_stats(event_peak_gfn(sim, params["D_trig"], 2), "2"))   # t..t+1 (clause window)
    out.update(_peak_stats(event_peak_gfn(sim, params["D_trig"], 6), "6"))   # t..t+5 (covers repayment hump)
    out.update({
        "p_crisis_any": float(crisis.any(axis=1).mean()),
        "mean_crisis_years": float(crisis.sum(axis=1).mean()),
    })
    if baseline_gfn is not None:
        hc = gfn > (np.asarray(baseline_gfn)[..., 1:] + params["GFN_margin"])
        out["p_hcrisis_any"] = float(hc.any(axis=1).mean())
        out["mean_hcrisis_years"] = float(hc.sum(axis=1).mean())
    out.update({
        "bT_mean": float(bT.mean()), "bT_median": float(np.median(bT)),
        "bT_p5": float(np.percentile(bT, 5)), "bT_p95": float(np.percentile(bT, 95)),
        "p_bT_gt100": float((bT > 100).mean()),
        "p_b_gt100_any": float((b > 100).any(axis=1).mean()),
        "share_paths_negative_debt": float((b < 0).any(axis=1).mean()),
        "share_pathyears_cap_binds": float(sim["x_bind"][:, 1:].mean()),
        "share_paths_cap_ever": float((sim["x_bind"][:, 1:] > 0).any(axis=1).mean()),
    })
    return out
