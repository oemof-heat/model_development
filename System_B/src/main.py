"""
This script runs the whole workflow of the analysis

"""

from oemof.tools import logger
import logging
import os
import sys
import subprocess
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

from preprocess import prepare_timeseries
from model_dessau import run_model_dessau
from postprocess import postprocess
from plot import create_plots

try:
    experiment_cfg = sys.argv[1]
except:
    print('Please specify which experiment config to run as a command line argument.')
    sys.exit(1)

# define path for results
abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
config_filename = os.path.split(experiment_cfg)[1]
results_dir = abs_path + '/model_runs/' + config_filename[:-4]

# create results directory if it does not exist
if not os.path.exists(results_dir):
    logging.info('Create directories')
    os.makedirs(results_dir + '/data_preprocessed')
    os.makedirs(results_dir + '/optimisation_results')
    os.makedirs(results_dir + '/postprocessed')
    os.makedirs(results_dir + '/plots')
    os.makedirs(results_dir + '/presentation')

logger.define_logging(logpath=results_dir + '/optimisation_results')

# Preproccessing
logging.info('Preprocess data')
prepare_timeseries(config_path=experiment_cfg, results_dir=results_dir)

# run tests
# logging.info('Perform tests')

# Run the optimisation model
logging.info('Run optimisation model')
run_model_dessau(config_path=experiment_cfg, results_dir=results_dir)

# Postprocessing
logging.info('Postprocess data')
postprocess(config_path=experiment_cfg, results_dir=results_dir)

# Plotting
logging.info('Create plots')
create_plots(config_path=experiment_cfg, results_dir=results_dir)

# Build a report
# cmd = ['pdflatex', '-interaction=nonstopmode', '--output-directory={0}/presentation/build'.format(abs_path), '{0}/presentation/report.tex'.format(results_dir)]
# process = subprocess.call(cmd) # , stdout=open(os.devnull, 'wb'))