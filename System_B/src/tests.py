import os
from main import main


def test_run_debug():
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    config_path = os.path.join(abs_path, 'experiment_configs/debug.yml')

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

    main(config_path, results_dir)


if __name__ == '__main__':
    test_run_debug()