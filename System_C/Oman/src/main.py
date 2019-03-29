# -*- coding: utf-8 -*-

"""
Date: 26.11.2018
Author: Franziska Pleissner

"""

from SystemC_oman_thermal import run_model_thermal
from SystemC_oman_thermal_plot import make_csv_and_plot
from SystemC_oman_electric import run_model_electric
from SystemC_oman_electric_plot import make_csv_and_plot_electric
# from SystemC_oman_plot import combine_results
import os
import pandas as pd
import yaml


def main(yaml_file):
    # Choose configuration file to run model with
    exp_cfg_file_name = yaml_file
    config_file_path = os.path.abspath('../experiment_config/' + exp_cfg_file_name)
    with open(config_file_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    global df_all_var
    if cfg['run_model']:
        for n in range(cfg['number_of_variations']):
            run_model_thermal(config_path=config_file_path, var_number=n)
    #if cfg['run_model_electric']:
    #    for n in range(cfg['number_of_variations']):
    #        run_model_electric(config_path=config_file_path, var_number=n)
    if cfg['run_postprocessing']:
        for n in range(cfg['number_of_variations']):
            make_csv_and_plot(config_path=config_file_path, var_number=n)
    #if cfg['run_postprocessing_electric']:
    #    for n in range(cfg['number_of_variations']):
    #        make_csv_and_plot_electric(config_path=config_file_path, var_number=n)


main('experiment_61.yml')
