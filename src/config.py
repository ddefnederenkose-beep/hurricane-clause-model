"""Config loading, unit sanity checks and the placeholder warning.

Every calibration value lives in YAML with value/source/status/meaning. Anything whose status is not
VERIFIED is reported every time the model runs, so unsourced numbers can never be mistaken for data.
"""
from __future__ import annotations
import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Status vocabulary. PLACEHOLDER_VERIFY = value not yet sourced (reported at every run). SOURCED = number read from a
# source by the builder; CALIBRATED = our own calculation from sourced numbers; ASSUMPTION = our modelling choice.
# VERIFIED is reserved: set only by a group member after opening the source.
STATUSES = ("PLACEHOLDER_VERIFY", "SOURCED", "CALIBRATED", "ASSUMPTION", "VERIFIED")
# Parameters that a scenario may override (read by simulate() through scenario_params()).
SCN_PARAM_KEYS = ("mu_D", "sigma_D", "kappa", "r_bar", "r_safe")
CAL_PATH = ROOT / "config" / "calibration.yaml"
SCN_PATH = ROOT / "config" / "scenarios.yaml"
DES_PATH = ROOT / "config" / "designs.yaml"


def _check_status(name, entry):
    if entry.get("status") not in STATUSES:
        raise ValueError(f"{name}: status {entry.get('status')!r} must be one of {STATUSES}")


def load_calibration(path=CAL_PATH):
    """Return (params, sim_settings, placeholders). params is a flat {name: value} dict."""
    raw = yaml.safe_load(pathlib.Path(path).read_text())
    for k, v in raw["parameters"].items():
        _check_status(k, v)
    params = {k: v["value"] for k, v in raw["parameters"].items()}
    placeholders = [k for k, v in raw["parameters"].items() if v.get("status") == "PLACEHOLDER_VERIFY"]
    return params, dict(raw["simulation"]), placeholders


def load_scenarios(path=SCN_PATH):
    """Return ({name: {'b_0':..,'pd_bar':..}}, placeholders as 'scenario.param' strings)."""
    raw = yaml.safe_load(pathlib.Path(path).read_text())["scenarios"]
    out, ph = {}, []
    for name, d in raw.items():
        out[name] = {"name": name, "description": d.get("description", ""), "role": d.get("role", "main")}
        for k in ("b_0", "pd_bar", "lambda") + SCN_PARAM_KEYS:
            if k in d:
                _check_status(f"{name}.{k}", d[k])
                out[name][k] = d[k]["value"]
                if d[k].get("status") == "PLACEHOLDER_VERIFY":
                    ph.append(f"{name}.{k}")
    return out, ph


def main_scenarios(scenarios: dict) -> dict:
    """Scenarios used in every experiment (sensitivity scenarios are added to experiments 1-2 only)."""
    return {k: v for k, v in scenarios.items() if v.get("role", "main") == "main"}


def load_designs(path=DES_PATH):
    """Return ({design: {'description':.., 'overrides': {param: value}}}, placeholders as 'design.param')."""
    raw = yaml.safe_load(pathlib.Path(path).read_text())["designs"]
    out, ph = {}, []
    for name, d in raw.items():
        out[name] = {"name": name, "description": d.get("description", ""),
                     "overrides": {k: v["value"] for k, v in d["overrides"].items()}}
        for k, v in d["overrides"].items():
            _check_status(f"{name}.{k}", v)
        ph += [f"{name}.{k}" for k, v in d["overrides"].items() if v.get("status") == "PLACEHOLDER_VERIFY"]
    return out, ph


def design_params(params: dict, design: dict) -> dict:
    return {**params, **design["overrides"]}


def scenario_params(params: dict, scenario: dict) -> dict:
    """Calibration parameters with the scenario's own overrides (damage law, kappa, interest rates) applied."""
    return {**params, **{k: scenario[k] for k in SCN_PARAM_KEYS if k in scenario}}


def status_counts() -> dict:
    """Count of parameters by status over calibration, scenarios and designs."""
    from collections import Counter
    c = Counter()
    for v in yaml.safe_load(CAL_PATH.read_text())["parameters"].values():
        c[v["status"]] += 1
    for d in yaml.safe_load(SCN_PATH.read_text())["scenarios"].values():
        for k, v in d.items():
            if isinstance(v, dict) and "status" in v:
                c[v["status"]] += 1
    for d in yaml.safe_load(DES_PATH.read_text())["designs"].values():
        for v in d["overrides"].values():
            c[v["status"]] += 1
    return dict(c)


def placeholder_warning(placeholders) -> str:
    if not placeholders:
        counts = status_counts()
        return "\n".join(["=" * 78, "No PLACEHOLDER_VERIFY parameters remain. Status counts: " + str(counts),
                          "ASSUMPTION = modelling choices (not data); CALIBRATED = our calculations; VERIFIED is reserved for the group.",
                          "=" * 78])
    lines = ["=" * 78,
             "WARNING: the following parameters are still PLACEHOLDER_VERIFY (no source yet).",
             "Do not cite results that depend on them as empirical:",
             "  " + ", ".join(placeholders), "=" * 78]
    return "\n".join(lines)


def check_units(params: dict, scenario: dict | None = None) -> None:
    """Cheap guard against mixed units (e.g. 0.65 entered for debt, or 3 entered for a rate)."""
    for k in ("r_bar", "r_safe", "g_bar", "theta_b", "theta_G", "rho"):
        if abs(params[k]) >= 0.5:
            raise ValueError(f"{k}={params[k]} looks like a percentage; rates must be decimals (0.03 = 3%).")
    if scenario is not None and "lambda" in scenario and not 0 <= scenario["lambda"] <= 1:
        raise ValueError("scenario lambda must lie in [0, 1].")
    if not 0 <= params.get("deferral_spread", 0) < 0.05:
        raise ValueError("deferral_spread is a decimal rate (0.0025 = 25 bps).")
    for k in ("lambda", "s", "psi", "kappa"):
        if not 0 <= params[k] <= 1:
            raise ValueError(f"{k}={params[k]} must lie in [0, 1].")
    if params["D_max"] < params["D_trig"] or params["D_trig"] <= 0:
        raise ValueError("Need 0 < D_trig <= D_max (damages are in % of GDP, e.g. 5 means 5%).")
    if params["M"] < 1 or params["R"] < 1 or params["K"] < 0:
        raise ValueError("M and R must be >= 1 and K >= 0.")
    if scenario is not None and not (5 <= abs(scenario["b_0"]) <= 400):
        raise ValueError(f"b_0={scenario['b_0']} looks like a fraction; debt/GDP is in % of GDP (65 = 65%).")
    if scenario is not None and abs(scenario["pd_bar"]) > 30:
        raise ValueError("pd_bar must be in % of GDP.")
