"""
This script runs the whole workflow of the analysis

"""

from oemof.tools import logger
import logging
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")
import subprocess
from connect_to_oep import connect_to_oep
from preprocess import prepare_timeseries
from preprocess_closed_data import preprocess_closed_data
from model_dessau import run_model_dessau
from postprocess import postprocess
from plot import create_plots
import helpers
import time


def main(config_path, results_dir):
    r"""
    This function runs the whole analysis pipeline

    """
    starttime = time.time()

    logger.define_logging(logpath=results_dir + '/optimisation_results')

    # Preproccessing
    logging.info('Preprocess data')
    connect_to_oep(config_path=config_path, results_dir=results_dir)
    prepare_timeseries(config_path=config_path, results_dir=results_dir)
    preprocess_closed_data(config_path=config_path, results_dir=results_dir)

    # Run the optimisation model
    logging.info('Run optimisation model')
    run_model_dessau(config_path=config_path, results_dir=results_dir)

    # Postprocessing
    logging.info('Postprocess data')
    postprocess(config_path=config_path, results_dir=results_dir)

    # Plotting
    logging.info('Create plots')
    create_plots(config_path=config_path, results_dir=results_dir)

    # Build a report
    # cmd = ['pdflatex', '-interaction=nonstopmode', '--output-directory={0}/presentation/build'.format(abs_path), '{0}/presentation/report.tex'.format(results_dir)]
    # process = subprocess.call(cmd) # , stdout=open(os.devnull, 'wb'))

    endtime = time.time()

    logging.info(f'Analysis lastet {endtime-starttime} sec.')

    return True

if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    main(config_path, results_dir)