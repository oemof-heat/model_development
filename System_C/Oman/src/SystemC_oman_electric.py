# -*- coding: utf-8 -*-
"""
Created on Dez 06 2018

@author: Franziska Pleissner

System C: concrete example: Model of cooling process with a compression chiller and a pv modul


             input/output    electr.  cool   waste   ambient(/ground)

grid_el            |---------->|       |       |
                   |           |       |       |
pv                 |---------->|       |       |
                   |           |       |       |
                   |<----------|       |       |
compression_chiller|------------------>|       |
                   |-------------------------->|
                   |           |       |       |
cooling_tower      |<--------------------------|
                   |<----------|       |       |       |
                   |---------------------------------->|
                   |           |       |       |
aquifer            |<--------------------------|
                   |<----------|       |       |       |
                   |---------------------------------->|
                   |           |       |       |
storage_electricity|---------->|       |       |
                   |<----------|       |       |
                   |           |       |       |
storage_cool       |------------------>|       |
                   |<------------------|       |
                   |           |       |       |
demand             |<------------------|       |
                   |           |       |       |
excess             |<----------|       |       |


"""

############
# Preamble #
############

# Import packages
from oemof.tools import logger, helpers, economics
import oemof.solph as solph
import oemof.outputlib as outputlib

import logging
import os
import yaml
import pandas as pd
import pyomo.environ as po

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


def ep_costs_func(capex, n, opex, wacc):
    ep_costs = economics.annuity(capex, n, wacc) + capex * opex
    return ep_costs


def run_model_electric(config_path, var_number):

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    if cfg['debug']:
        number_of_time_steps = 2
    else:
        number_of_time_steps = cfg['number_timesteps']

    solver = cfg['solver']
    debug = cfg['debug']
    solver_verbose = cfg['solver_verbose']  # show/hide solver output

    ### Read data and parameters ###

    # define the used directories
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    results_path = abs_path + '/results'
    data_ts_path = abs_path + '/data/data_confidential/'
    data_param_path = abs_path + '/data/data_public/'

    # Read parameter values from parameter file
    filename_param = data_param_path + cfg['parameters_file_name'][var_number]
    param_df = pd.read_csv(filename_param, index_col=1, sep=';')  # uses second column of csv-file for indexing
    param_value = param_df['value']

    # Import  PV and demand data
    data = pd.read_csv((data_ts_path + cfg['time_series_file_name']), sep=';')

    # redefine ep_costs_function:
    def ep_costs_f(capex, n, opex):
        return ep_costs_func(capex, n, opex, param_value['wacc'])

    # initiate the logger
    logger.define_logging(logfile='Oman_electric_{0}_{1}.log'.format(cfg['exp_number'], var_number),
                          logpath=results_path + '/logs',
                          screen_level=logging.INFO,
                          file_level=logging.DEBUG)

    date_time_index = pd.date_range('1/1/2017', periods=number_of_time_steps, freq='H')

    # Initialise the energysystem
    logging.info('Initialize the energy system')

    energysystem = solph.EnergySystem(timeindex=date_time_index)

    #######################
    # Build up the system #
    #######################

    # Busses

    bco = solph.Bus(label="cool")
    bwh = solph.Bus(label="waste")
    bel = solph.Bus(label="electricity")
    bam = solph.Bus(label="ambient")

    energysystem.add(bco, bwh, bel, bam)

    # Sinks and sources

    ambience = solph.Sink(label='ambience', inputs={bam: solph.Flow()})

    grid_el = solph.Source(label='grid_el', outputs={bel: solph.Flow(variable_costs=param_value['price_electr'])})

    pv = solph.Source(label='pv', outputs={bel: solph.Flow(
        fixed=True, actual_value=data['solar gain relativ'],
        investment=solph.Investment(ep_costs=ep_costs_f(param_value['invest_costs_pv_output_th_07616'],
                                                        param_value['lifetime_pv'],
                                                        param_value['opex_pv'])))})  # Einheit: 0,7616 kWpeak

    demand = solph.Sink(label='demand', inputs={bco: solph.Flow(
        fixed=True, actual_value=data['Cooling load kW'], nominal_value=1)})

    excess_el = solph.Sink(label='excess_el', inputs={bel: solph.Flow()})

    energysystem.add(ambience, grid_el, pv, demand, excess_el)

    # Transformers

    chil = solph.Transformer(
        label='compression_chiller',
        inputs={bel: solph.Flow()},
        outputs={bco: solph.Flow(investment=solph.Investment(
                    ep_costs=ep_costs_f(param_value['invest_costs_compression_output_cool'],
                                        param_value['lifetime_compression'], param_value['opex_compression']))),
                 bwh: solph.Flow()},
        conversion_factors={bco: param_value['conv_factor_compression_output_cool'],
                            bwh: param_value['conv_factor_compression_output_waste']})

    aqui = solph.Transformer(
        label='aquifer',
        inputs={bwh: solph.Flow(investment=solph.Investment(
                    ep_costs=ep_costs_f(param_value['invest_costs_aqui_input_th'], param_value['lifetime_aqui'],
                                        param_value['opex_aqui']))),
                bel: solph.Flow()},
        outputs={bam: solph.Flow()},
        conversion_factors={bwh: param_value['conv_factor_aquifer_input_waste'],
                            bel: param_value['conv_factor_aquifer_input_el']})

    towe = solph.Transformer(
        label='cooling_tower',
        inputs={bwh: solph.Flow(investment=solph.Investment(
                    ep_costs=ep_costs_f(param_value['invest_costs_tower_input_th'], param_value['lifetime_tower'],
                                        param_value['opex_tower']))),
                bel: solph.Flow()},
        outputs={bam: solph.Flow()},
        conversion_factors={bwh: param_value['conv_factor_tower_input_waste'],
                            bel: param_value['conv_factor_tower_input_el']})

    energysystem.add(chil, aqui, towe)

    # storages

    if param_value['nominal_capacitiy_stor_cool'] == 0:
        stor_co = solph.components.GenericStorage(
            label='storage_cool',
            inputs={bco: solph.Flow()},
            outputs={bco: solph.Flow()},
            capacity_loss=param_value['capac_loss_stor_cool'],
            # invest_relation_input_capacity=1 / 6,
            # invest_relation_output_capacity=1 / 6,
            inflow_conversion_factor=param_value['conv_factor_stor_cool_input'],
            outflow_conversion_factor=param_value['conv_factor_stor_cool_output'],
            investment=solph.Investment(
                ep_costs=ep_costs_f(param_value['invest_costs_stor_cool_capacity'], param_value['lifetime_stor_cool'],
                                    param_value['opex_stor_cool'])))
    else:
        stor_co = solph.components.GenericStorage(
            label='storage_cool',
            inputs={bco: solph.Flow()},
            outputs={bco: solph.Flow()},
            capacity_loss=param_value['capac_loss_stor_cool'],
            # invest_relation_input_capacity=1 / 6,
            # invest_relation_output_capacity=1 / 6,
            inflow_conversion_factor=param_value['conv_factor_stor_cool_input'],
            outflow_conversion_factor=param_value['conv_factor_stor_cool_output'],
            nominal_capacity=param_value['nominal_capacitiy_stor_cool'])

    if param_value['nominal_capacitiy_stor_el'] == 0:
        stor_el = solph.components.GenericStorage(
            label='storage_electricity',
            inputs={bel: solph.Flow()},
            outputs={bel: solph.Flow()},
            capacity_loss=param_value['capac_loss_stor_el'],
            # invest_relation_input_capacity=1 / 6,
            # invest_relation_output_capacity=1 / 6,
            inflow_conversion_factor=param_value['conv_factor_stor_el_input'],
            outflow_conversion_factor=param_value['conv_factor_stor_el_output'],
            investment=solph.Investment(
                ep_costs=ep_costs_f(param_value['invest_costs_stor_el_capacity'], param_value['lifetime_stor_el'],
                                    param_value['opex_stor_el'])))

    else:
        stor_el = solph.components.GenericStorage(
            label='storage_electricity',
            inputs={bel: solph.Flow()},
            outputs={bel: solph.Flow()},
            capacity_loss=param_value['capac_loss_stor_el'],
            # invest_relation_input_capacity=1 / 6,
            # invest_relation_output_capacity=1 / 6,
            inflow_conversion_factor=param_value['conv_factor_stor_el_input'],
            outflow_conversion_factor=param_value['conv_factor_stor_el_output'],
            nominal_capacity=param_value['nominal_capacitiy_stor_el'])

    energysystem.add(stor_co, stor_el)

    ########################################
    # Create a model and solve the problem #
    ########################################

    # Initialise the operational model (create the problem) with constrains
    model = solph.Model(energysystem)

    logging.info('Solve the optimization problem')
    model.solve(solver=solver, solve_kwargs={'tee': solver_verbose})

    if cfg['debug']:
        filename = results_path + '/lp_files/' + 'Oman_electric_{0}_{1}.lp'.format(cfg['exp_number'], var_number)
        logging.info('Store lp-file in {0}.'.format(filename))
        model.write(filename, io_options={'symbolic_solver_labels': True})

    logging.info('Store the energy system with the results.')

    energysystem.results['main'] = outputlib.processing.results(model)
    energysystem.results['meta'] = outputlib.processing.meta_results(model)
    energysystem.results['param'] = outputlib.processing.parameter_as_dict(model)

    energysystem.dump(dpath=(results_path + '/dumps'),
                      filename='oman_electric_{0}_{1}.oemof'.format(cfg['exp_number'], var_number))
