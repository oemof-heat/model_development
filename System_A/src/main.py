
from oemof.tools import logger
import logging
import os

from model_flex_chp import run_model_flexchp

experiment_cfg = 'experiment_1.yml'

abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

run_model_flexchp(config_path=abs_path + "/experiment_configs/" + experiment_cfg)