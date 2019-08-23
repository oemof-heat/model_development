import sys
import os
import yaml
import pandas as pd
import re

__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

def setup_experiment():
    r"""

    Returns
    -------
    config_path: path
        Relative path to experiment config file

    results_dir: path
        Absolute path to results directory

    """

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    # take command line arguments
    try:
        config_path = sys.argv[1]
    except:
        print('Please specify which experiment config to run as a command line argument.')
        sys.exit(1)

    # Get absolute path of config file.
    config_path = os.path.abspath(config_path)

    # define path for results
    config_filename = os.path.split(config_path)[1]
    results_dir = abs_path + '/results/' + config_filename[:-4]

    # create results directory if it does not exist
    list_dir = ['data_preprocessed',
                'optimisation_results',
                'data_postprocessed/timeseries',
                'data_plots',
                'plots',
                'presentation']
    for directory in [os.path.join(results_dir, dir) for dir in list_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)


    return config_path, results_dir


def load_input_parameter(filename):
    parameters = pd.read_csv(filename,
                            index_col=[0, 1, 2, 3],
                            usecols=[1, 2, 3, 4, 5, 6],
                            delimiter=';')

    filter_numeric = [key for key in parameters.index
                      if not bool(re.search(r'subnet-._demand_th', key[2]))]
    input_parameter = parameters.loc[filter_numeric, :]
    input_parameter.loc[:, 'var_value'] = input_parameter.loc[:, 'var_value'].astype('float')
    return input_parameter


def run_scenarios(run_model, config_path, results_dir):
    with open(config_path, 'r') as ymlfile:
        config = yaml.load(ymlfile)
    scenarios = pd.read_csv(config['data_raw']['scenarios'])
    print(scenarios)
