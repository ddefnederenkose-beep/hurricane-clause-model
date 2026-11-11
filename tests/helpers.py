import numpy as np
from src import config

PARAMS, SIM, _ = config.load_calibration()
SCEN, _ = config.load_scenarios()
GREN, HIGH = SCEN["grenada_like"], SCEN["high_debt"]


def P(**kw):
    return {**PARAMS, **kw}
