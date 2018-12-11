
"""

Date: 22nd of November 2018
Author: Jakob Wolf (jakob.wolf@beuth-hochschule.de)

"""


import os
from model_flex_chp import run_model_flexchp
from preprocessing import preprocess_timeseries
from analyse import analyse_energy_system
from plot_and_analyse_results_flexCHP import analyse_storages
import yaml
import timeit


def main():

    # Choose configuration file to run model with
    exp_cfg_file_name = 'experiment_1.yml'
    config_file_path = os.path.abspath('../experiment_config/' + exp_cfg_file_name)
    with open(config_file_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    start_time = timeit.default_timer()

    run_single_scenario = cfg['run_single_scenario']
    if run_single_scenario:
        if cfg['run_preprocessing']:
            preprocess_timeseries(config_path=config_file_path)
        if cfg['run_model']:
            run_model_flexchp(config_path=config_file_path, scenario_nr=cfg['scenario_number'])
        if cfg['run_postprocessing']:
            analyse_energy_system(config_path=config_file_path, scenario_nr=cfg['scenario_number'])
            analyse_storages(config_path=config_file_path, scenario_nr=cfg['scenario_number'])
    else:
        scenarios = [1, 2, 3]
        for scenario in scenarios:
            if cfg['run_preprocessing']:
                preprocess_timeseries(config_path=config_file_path)
            if cfg['run_model']:
                print('\n*** Scenario {0}***'.format(scenario))
                run_model_flexchp(config_path=config_file_path, scenario_nr=scenario)
            if cfg['run_postprocessing']:
                analyse_energy_system(config_path=config_file_path, scenario_nr=scenario)
                # analyse_storages(config_path=config_file_path, scenario_nr=cfg['scenario_number'])
            print('')

    stop_time = timeit.default_timer()
    run_time_in_sec = stop_time - start_time
    print("***Run Time***")
    if run_time_in_sec < 60:
        print("%6.2f" % run_time_in_sec, "seconds")
    elif run_time_in_sec >= 60:
        run_time_in_min = run_time_in_sec / 60
        residual_seconds = run_time_in_sec % 60
        print("%6.0f" % run_time_in_min, "min,", "%6.0f" % residual_seconds, "s")
    else:
        print("%12.2f" % run_time_in_sec, "seconds")


main()
