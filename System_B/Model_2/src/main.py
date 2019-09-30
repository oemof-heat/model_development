"""
This script runs the whole analysis pipeline.

"""

__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

import time
import logging
import warnings

from oemof.tools import logger
from helpers import setup_experiment
from preprocess import preprocess
from scenario import create_list_model_runs
from model import run_model
from postprocess import postprocess
from plot import create_plots


def main(config_path, results_dir):
    r"""
    This function runs the whole analysis pipeline

    Parameters
    ----------

    config_path : str
        path to yaml config file

    results_dir : str
        path to store results

    """
    warnings.filterwarnings("ignore", message="numpy.dtype size changed")
    warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

    starttime = time.time()

    logger.define_logging(logpath=results_dir + '/optimisation_results')

    # Preprocess
    logging.info('Preprocess data')
    preprocess(config_path, results_dir)
    create_list_model_runs(config_path, results_dir)

    # Run the optimisation model
    logging.info('Run optimisation model')
    run_model(config_path, results_dir)

    # Postprocess
    logging.info('Postprocess results')
    postprocess(config_path, results_dir)

    # Plot
    logging.info('Create plots')
    create_plots(config_path, results_dir)

    endtime = time.time()

    logging.info(f'Analysis lastet {endtime-starttime} sec.')
    return True


if __name__ == '__main__':
    config_path, results_dir = setup_experiment()
    main(config_path, results_dir)
