# -*- coding: utf-8 -*-

"""
Date: 26.11.2018
Author: Franziska Pleissner

"""

from SystemC_oman_thermal_2 import run_model_thermal
from SystemC_oman_thermal_plot_2 import make_csv_and_plot
from SystemC_oman_electric_2 import run_model_electric
from SystemC_oman_electric_plot_2 import make_csv_and_plot_electric
# from SystemC_oman_plot import combine_results
import os
import yaml


def main(yaml_file):
    # Choose configuration file to run model with
    exp_cfg_file_name = yaml_file
    config_file_path = (
        os.path.abspath('../experiment_config/' + exp_cfg_file_name))
    with open(config_file_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    global df_all_var

    if type(cfg['parameters_variation']) == list:
        scenarios = range(len(cfg['parameters_variation']))
    elif type(cfg['parameters_system']) == list:
        scenarios = range(len(cfg['parameters_system']))
    else:
        scenarios = range(1)

    for scenario in scenarios:
        if cfg['run_model']:
            run_model_thermal(
                config_path=config_file_path,
                var_number=scenario)
        if cfg['run_model_electric']:
            run_model_electric(
                config_path=config_file_path,
                var_number=scenario)
        if cfg['run_postprocessing']:
            make_csv_and_plot(
                config_path=config_file_path,
                var_number=scenario)
        if cfg['run_postprocessing_electric']:
            make_csv_and_plot_electric(
                config_path=config_file_path,
                var_number=scenario)


main('experiment_test.yml')
