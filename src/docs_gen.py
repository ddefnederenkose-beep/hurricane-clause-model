"""Regenerates the parameter table (with sources/status) and software versions inside docs/METHODS.md."""
from __future__ import annotations
import pathlib, platform, sys
import numpy, pandas, matplotlib, yaml
from . import config

START, END = "<!-- PARAMS:START -->", "<!-- PARAMS:END -->"


def _rows(path, key):
    raw = yaml.safe_load(pathlib.Path(path).read_text())[key]
    return raw


def build_table() -> str:
    lines = ["| Parameter | Value | Meaning | Source | Status |", "|---|---|---|---|---|"]
    cal = _rows(config.CAL_PATH, "parameters")
    for k, v in cal.items():
        lines.append(f"| {k} | {v['value']} | {v['meaning']} | {v.get('source') or '(none yet)'} | {v['status']} |")
    for sname, d in _rows(config.SCN_PATH, "scenarios").items():
        for k in ("b_0", "pd_bar", "lambda"):
            if k in d:
                v = d[k]
                lines.append(f"| {sname}.{k} | {v['value']} | {v['meaning']} | {v.get('source') or '(none yet)'} | {v['status']} |")
    for dname, d in _rows(config.DES_PATH, "designs").items():
        for k, v in d["overrides"].items():
            lines.append(f"| {dname}.{k} | {v['value']} | {v['meaning']} | {v.get('source') or '(none yet)'} | {v['status']} |")
    ver = (f"\nSoftware: Python {platform.python_version()}, numpy {numpy.__version__}, pandas {pandas.__version__}, "
           f"matplotlib {matplotlib.__version__}, pyyaml {yaml.__version__}. Seed and sizes: see `simulation` in calibration.yaml.\n")
    return "\n".join(lines) + "\n" + ver


def update_methods(path):
    p = pathlib.Path(path)
    s = p.read_text()
    if START in s and END in s:
        a, b = s.index(START), s.index(END)
        p.write_text(s[:a + len(START)] + "\n" + build_table() + s[b:])


# Proposed classification (the group should adjust): "sourceable" = has an empirical / documentary counterpart that
# can be looked up or estimated; "judgment" = modelling or policy choice, robustness switch, or numerical backstop.
SOURCEABLE = {"lambda", "mu_D", "sigma_D", "D_max", "D_trig", "g_bar", "phi", "psi", "kappa", "R", "r_bar", "r_safe", "M",
              "s", "K", "defer_repay_years", "max_triggers", "GFN_crit", "grenada_like.b_0", "grenada_like.pd_bar",
              "grenada_like.lambda", "high_debt.b_0", "high_debt.pd_bar", "grenada_style.s", "grenada_style.K",
              "grenada_style.defer_repay_years", "barbados_style.s", "barbados_style.K", "barbados_style.defer_repay_years",
              "theta_b", "theta_G", "b_bar", "GFN_bar"}
NOTES = {"s": "global default; overridden by the designs in experiments", "K": "global default; overridden by the designs",
         "defer_repay_years": "global default; overridden by the designs", "lambda": "used only by high_debt (grenada_like has its own)",
         "r_safe": "Version 2 only", "theta_b": "Version 2 only", "theta_G": "Version 2 only", "b_bar": "Version 2 only",
         "GFN_bar": "Version 2 only", "x_max": "Version 2 only", "deferral_spread": "evaluated with the premium switch on",
         "rho": "off (0): relative sweep undefined", "GFN_crit": "enters only the absolute crisis flag, not this metric", "D_max": "cap is almost never reached with sigma_D = 1", "b_star": "inactive while rho = 0",
         "grenada_like_lambda_010.b_0": "sensitivity scenario, not in main experiments",
         "grenada_like_lambda_010.pd_bar": "sensitivity scenario", "grenada_like_lambda_010.lambda": "sensitivity scenario"}


def status_table(params=None, scenarios=None, designs=None, influence=None):
    """Every parameter: value, source, status, type (sourceable / judgment) and one-at-a-time +-25% influence on
    P(hurricane-attributable crisis) in Regime B. Sourceable parameters first, sorted by influence."""
    import pandas as pd
    rows = []
    for k, v in _rows(config.CAL_PATH, "parameters").items():
        rows.append((k, v["value"], v.get("source") or "", v["status"]))
    for sname, d in _rows(config.SCN_PATH, "scenarios").items():
        for k in ("b_0", "pd_bar", "lambda"):
            if k in d:
                rows.append((f"{sname}.{k}", d[k]["value"], d[k].get("source") or "", d[k]["status"]))
    for dname, d in _rows(config.DES_PATH, "designs").items():
        for k, v in d["overrides"].items():
            rows.append((f"{dname}.{k}", v["value"], v.get("source") or "", v["status"]))
    df = pd.DataFrame(rows, columns=["parameter", "value", "source", "status"])
    df["value"] = df["value"].map(str)          # exact values (no float rounding in the printout)
    df["type"] = ["sourceable" if p in SOURCEABLE else "judgment" for p in df["parameter"]]
    df["note"] = df["parameter"].map(NOTES).fillna("")
    if influence is not None:
        df = df.merge(influence, on="parameter", how="left")
    df["_o"] = (df["type"] != "sourceable").astype(int)
    key = "influence_pp" if "influence_pp" in df else "parameter"
    df = df.sort_values(["_o", key], ascending=[True, False], na_position="last").drop(columns="_o").reset_index(drop=True)
    return df
