"""
This script runs the whole workflow of the analysis

"""

from oemof.tools import logger
import logging
import os
import subprocess

from preprocess import prepare_timeseries
from model_dessau import run_model_dessau
import plot


experiment_cfg = 'experiment_1.yml'

abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
results_dir = abs_path + '/model_runs/' + experiment_cfg.strip('.yml')


if not os.path.exists(results_dir):
    print('yes')
    os.makedirs(results_dir + '/data_preprocessed')
    os.makedirs(results_dir + '/optimisation_results')
    os.makedirs(results_dir + '/postprocessed')
    os.makedirs(results_dir + '/plots')
    os.makedirs(results_dir + '/presentation')

logger.define_logging(logpath=results_dir + '/optimisation_results')

# Preproccessing
logging.info('Preprocess data')
prepare_timeseries(results_dir)

# Load config file for scenario
logging.info('Load config file')

# run tests
# logging.info('Perform tests')

# Run the optimisation model
logging.info('Run optimisation model')
run_model_dessau(config_path="/experiment_configs/" + experiment_cfg, results_dir=results_dir)

# Postprocessing
logging.info('Postprocess data')

# Plotting
logging.info('Create plots')
plot.create_plots(results_dir)

# Create a table of the scenario


# Build the report
# cmd = ['pdflatex', '-interaction=nonstopmode', '--output-directory={0}/presentation/build'.format(abs_path), '{0}/presentation/report.tex'.format(results_dir)]
# process = subprocess.call(cmd) # , stdout=open(os.devnull, 'wb'))