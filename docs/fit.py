"""Fit of the damage distribution (mu_D, sigma_D) to the World Bank Grenada risk profile (2016).

Targets (docs/parameter_sourcing_register.md, Task 2): average annual loss (AAL) 0.9% of GDP and 250-year loss
(PML) 43.6% of GDP, damage capped at 200% of GDP, for a given hurricane frequency lambda:
    lambda * E[min(D, 200)] = 0.9            and        lambda * P(D > 43.6) = 1/250.
D | hit is lognormal. UNITS: the fit returns the MEDIAN damage in % of GDP; the model's mu_D is the LOG of the median
(src/hurricanes.py: D = exp(mu_D + sigma_D z)), so  mu_D = ln(median).

Run from the repo root:  .venv/bin/python docs/fit.py      (needs scipy: pip install scipy)
Cross-check A (IMF 2016 small states) is kept from the group's original script.
"""
import pathlib, sys
import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from src import config, hurricanes  # noqa: E402

CAP = 200.0


def tmean(m, s, cap=CAP):
    """E[min(D, cap)] for D ~ lognormal(log-mean m, log-sd s)."""
    z = (np.log(cap) - m) / s
    return np.exp(m + s * s / 2) * norm.cdf(z - s) + cap * (1 - norm.cdf(z))


def roots(target_mean, x, px):
    """(sigma, m=log-median) with P(D > x) = px and E[min(D, cap)] = target_mean; also the smallest attainable mean."""
    zq = norm.ppf(1 - px)
    out, ss = [], np.linspace(0.2, 3.5, 3301)
    f = [tmean(np.log(x) - zq * s, s) - target_mean for s in ss]
    for i in range(len(ss) - 1):
        if np.sign(f[i]) != np.sign(f[i + 1]):
            s = brentq(lambda s: tmean(np.log(x) - zq * s, s) - target_mean, ss[i], ss[i + 1])
            out.append((s, np.log(x) - zq * s))
    return out, min(f) + target_mean


def aal(lam, m, s):
    return lam * tmean(m, s)


def pml250(lam, m, s):
    """Loss x with annual exceedance probability 1/250:  lam * P(D > x) = 1/250."""
    return float(np.exp(m + s * norm.ppf(1 - (1 / 250) / lam)))


if __name__ == "__main__":
    print("A) cross-check, IMF 2016 small states: mean 13% of GDP, P(D >= 30%) = 9%")
    for s, m in roots(13, 30, 0.09)[0]:
        print(f"   sigma={s:.3f} median={np.exp(m):.2f}% GDP  P(D>100)={1 - norm.cdf((np.log(100) - m) / s):.3f}")
    print("\nB) World Bank Grenada profile: AAL 0.9% GDP, 250-yr PML 43.6% GDP (building losses), cap 200%")
    fits = {}
    for lam in (0.051, 0.10):
        (s, m), = roots(0.9 / lam, 43.6, (1 / 250) / lam)[0]
        fits[lam] = (s, m)
        print(f" lambda={lam}: sigma={s:.4f}  median={np.exp(m):.3f}% GDP  ->  mu_D = ln(median) = {m:.4f}")
    params, _, _ = config.load_calibration()
    print("\nC) Values ENTERED in config (rounded) reproduce the targets, analytically and through the model's own code")
    sets = {0.051: (params["mu_D"], params["sigma_D"]), 0.10: None}
    scn, _ = config.load_scenarios()
    sens = scn.get("grenada_like_lambda_010")
    if sens and "mu_D" in sens:
        sets[0.10] = (sens["mu_D"], sens["sigma_D"])
    draws = hurricanes.draw_noise(12345, 400_000, 1)
    for lam, ms in sets.items():
        if ms is None:
            continue
        mu, sg = ms
        D = hurricanes.damages(draws, lam, mu, sg, CAP)[:, 0]           # the model's own damage generator
        mc_aal = D.mean()                                               # = lambda * E[min(D,cap) | hit]
        q = np.quantile(D, 1 - 1 / 250)                                 # annual-loss 250-yr quantile (hit prob = lambda)
        print(f" lambda={lam}: entered mu_D={mu}, sigma_D={sg}")
        print(f"    analytic : AAL {aal(lam, mu, sg):.3f}% (target 0.900)   250-yr loss {pml250(lam, mu, sg):.1f}% (target 43.6)")
        print(f"    model MC : AAL {mc_aal:.3f}%                      250-yr loss {q:.1f}%   (N = 400,000 simulated years)")
