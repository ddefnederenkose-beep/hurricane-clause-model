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


def summarize(sim: dict, params: dict, window: int = 2) -> dict:
    gfn = sim["gfn"][:, 1:]
    b = sim["b"][:, 1:]
    crisis = gfn > params["GFN_crit"]
    peaks = event_peak_gfn(sim, params["D_trig"], window)
    bT = b[:, -1]
    return {
        "n_events": int(peaks.size),
        "peak_gfn_mean": float(peaks.mean()) if peaks.size else np.nan,
        "peak_gfn_p95": float(np.percentile(peaks, 95)) if peaks.size else np.nan,
        "p_crisis_any": float(crisis.any(axis=1).mean()),
        "mean_crisis_years": float(crisis.sum(axis=1).mean()),
        "bT_mean": float(bT.mean()), "bT_median": float(np.median(bT)),
        "bT_p5": float(np.percentile(bT, 5)), "bT_p95": float(np.percentile(bT, 95)),
        "p_bT_gt100": float((bT > 100).mean()),
        "p_b_gt100_any": float((b > 100).any(axis=1).mean()),
        "share_paths_negative_debt": float((b < 0).any(axis=1).mean()),
    }
