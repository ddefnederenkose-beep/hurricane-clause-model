"""Config loading, unit sanity checks and the placeholder warning.

Every calibration value lives in YAML with value/source/status/meaning. Anything whose status is not
VERIFIED is reported every time the model runs, so unsourced numbers can never be mistaken for data.
"""
from __future__ import annotations
import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAL_PATH = ROOT / "config" / "calibration.yaml"
SCN_PATH = ROOT / "config" / "scenarios.yaml"
DES_PATH = ROOT / "config" / "designs.yaml"


def load_calibration(path=CAL_PATH):
    """Return (params, sim_settings, placeholders). params is a flat {name: value} dict."""
    raw = yaml.safe_load(pathlib.Path(path).read_text())
    params = {k: v["value"] for k, v in raw["parameters"].items()}
    placeholders = [k for k, v in raw["parameters"].items() if v.get("status") != "VERIFIED"]
    return params, dict(raw["simulation"]), placeholders


def load_scenarios(path=SCN_PATH):
    """Return ({name: {'b_0':..,'pd_bar':..}}, placeholders as 'scenario.param' strings)."""
    raw = yaml.safe_load(pathlib.Path(path).read_text())["scenarios"]
    out, ph = {}, []
    for name, d in raw.items():
        out[name] = {"name": name, "description": d.get("description", ""), "role": d.get("role", "main")}
        for k in ("b_0", "pd_bar", "lambda"):
            if k in d:
                out[name][k] = d[k]["value"]
                if d[k].get("status") != "VERIFIED":
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
        ph += [f"{name}.{k}" for k, v in d["overrides"].items() if v.get("status") != "VERIFIED"]
    return out, ph


def design_params(params: dict, design: dict) -> dict:
    return {**params, **design["overrides"]}


def placeholder_warning(placeholders) -> str:
    lines = ["=" * 78,
             "WARNING: the following parameters are PLACEHOLDER_VERIFY (not yet sourced).",
             "Do not cite results as empirical until every one is replaced:",
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
