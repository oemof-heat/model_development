"""
This script runs the whole workflow of the analysis

"""

from oemof.tools import logger
import logging
import os
import subprocess

import prepare_time_series
from model_dessau import run_model_dessau
import create_plots

abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

logger.define_logging(logpath=abs_path + '/results')

# Preproccessing
logging.info('Preprocess data')
prepare_time_series

# Load config file for scenario
logging.info('Load config file')

# run tests
# logging.info('Perform tests')

# Run the optimisation model
logging.info('Run optimisation model')
run_model_dessau(config_path="/experiments/experiment_1.yml")

# Postprocessing
logging.info('Postprocess data')

# Plotting
logging.info('Create plots')
create_plots.create_plots()

# Create a table of the scenario


# Build the report
cmd = ['pdflatex', '-interaction=nonstopmode', '--output-directory={0}/presentation/build'.format(abs_path), '{0}/presentation/report.tex'.format(abs_path)]
process = subprocess.call(cmd) # , stdout=open(os.devnull, 'wb'))
# cmd = ['pdflatex', '-interaction', 'nonstopmode', 'cover.tex']
# proc = subprocess.Popen(cmd)
# proc.communicate()
