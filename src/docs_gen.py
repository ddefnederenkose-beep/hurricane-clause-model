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


def status_table(params=None, scenarios=None, designs=None):
    """Flat table of every parameter: name, value, source, status (for the console and outputs/tables)."""
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
    df["value"] = df["value"].map(str)   # exact values (no float rounding in the printout)
    return df
