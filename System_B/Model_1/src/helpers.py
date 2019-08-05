import sys
import os

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
    results_dir = abs_path + '/model_runs/' + config_filename[:-4]

    # create results directory if it does not exist
    if not os.path.exists(results_dir):
        os.makedirs(results_dir + '/data_preprocessed')
        os.makedirs(results_dir + '/optimisation_results')
        os.makedirs(results_dir + '/postprocessed')
        os.makedirs(results_dir + '/plots')
        os.makedirs(results_dir + '/presentation')

    return config_path, results_dir