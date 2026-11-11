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
