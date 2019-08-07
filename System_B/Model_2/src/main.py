"""
This script runs the whole workflow of the analysis

"""

__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

import time
import logging
import warnings
import subprocess

from oemof.tools import logger
from helpers import setup_experiment, run_scenarios
from preprocess import preprocess
from model import run_model
from postprocess import postprocess
from plot import create_plots


def main(config_path, results_dir):
    r"""
    This function runs the whole analysis pipeline

    """
    warnings.filterwarnings("ignore", message="numpy.dtype size changed")
    warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

    starttime = time.time()

    logger.define_logging(logpath=results_dir + '/optimisation_results')

    # Preprocess
    logging.info('Preprocess data')
    preprocess(config_path, results_dir)

    # Run scenarios
    logging.info('Create scenarios')
    run_scenarios(run_model, config_path, results_dir)

    # Run the optimisation model
    logging.info('Run optimisation model')
    run_model(config_path, results_dir)

    # Postprocess
    logging.info('Postprocess results')
    postprocess(config_path, results_dir)

    # Plot
    logging.info('Create plots')
    create_plots(config_path, results_dir)

    # Build a report
    # cmd = ['pdflatex', '-interaction=nonstopmode', '--output-directory={0}/presentation/build'.format(abs_path), '{0}/presentation/report.tex'.format(results_dir)]
    # process = subprocess.call(cmd) # , stdout=open(os.devnull, 'wb'))

    endtime = time.time()

    logging.info(f'Analysis lastet {endtime-starttime} sec.')
    return True


if __name__ == '__main__':
    config_path, results_dir = setup_experiment()
    main(config_path, results_dir)