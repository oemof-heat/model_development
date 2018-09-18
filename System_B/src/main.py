"""
This script runs the whole workflow of the analysis

"""

from oemof.tools import logger
import logging
import os


from model_dessau import run_model_dessau
import create_plots

abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

logger.define_logging(logpath=abs_path + '/results')

# Preproccessing
logging.info('Preprocess data')

# Load config file for scenario
logging.info('Load config file')

# Run the optimisation model
logging.info('Run optimisation model')
run_model_dessau()

# Postprocessing
logging.info('Postprocess data')

# Plotting
logging.info('Create plots')
create_plots.create_plots()

# Rebuild the reports


