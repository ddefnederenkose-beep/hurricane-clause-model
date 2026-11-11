"""Hurricane process.

Each year a major hurricane hits with probability lambda; damage D_t (% of GDP) is lognormal(mu_D, sigma_D),
capped at D_max. We separate the *random numbers* (draws) from the *parameters* so that the same draws
can be reused across policy regimes, model versions and parameter grids (common random numbers):
a hit occurs when u < lambda, so raising lambda only ADDS hits and leaves existing damages unchanged.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class HurricaneDraws:
    u: np.ndarray  # uniform(0,1), shape (N, T): hit if u < lambda
    z: np.ndarray  # standard normal, shape (N, T): damage = exp(mu + sigma z)


def draw_noise(seed: int, n_paths: int, horizon: int) -> HurricaneDraws:
    rng = np.random.default_rng(seed)
    return HurricaneDraws(u=rng.random((n_paths, horizon)), z=rng.standard_normal((n_paths, horizon)))


def damages(draws: HurricaneDraws, lam: float, mu: float, sigma: float, d_max: float) -> np.ndarray:
    """Damage array D[n, t-1] in % of GDP (0 if no hit)."""
    hit = draws.u < lam
    return np.where(hit, np.minimum(np.exp(mu + sigma * draws.z), d_max), 0.0)
