import numpy as np
from src import config

PARAMS, SIM, _ = config.load_calibration()
SCEN, _ = config.load_scenarios()
# tests drive lambda explicitly through the params dict, so drop the per-scenario lambda override
GREN = {k: v for k, v in SCEN["grenada_like"].items() if k != "lambda"}
HIGH = {k: v for k, v in SCEN["high_debt"].items() if k != "lambda"}
DESIGNS, _ = config.load_designs()


def P(**kw):
    return {**PARAMS, **kw}


def PD(**kw):
    """Params for the 'declining balance, repay over M' rule (the old default, the scope of experiment 4's identity)."""
    kw.setdefault("defer_repay_years", PARAMS["M"])
    return P(repay_rule="declining_balance", **kw)


def eff(p, scen):
    """Parameters as simulate() sees them (scenario overrides applied)."""
    return config.scenario_params(p, scen)
