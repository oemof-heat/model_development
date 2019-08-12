__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

import pandas as pd
import numpy as np
import networkx as nx
import os
import yaml
import logging

import oemof
import oemof.outputlib as outputlib
from oemof.tools import logger
from oemof.solph import (Source, Sink, Transformer, Bus, Flow,
                         Model, EnergySystem)
from oemof.solph.components import GenericStorage, GenericCHP
import oemof.graph as graph
import helpers


def model(input_parameter, demand_heat, price_electricity, results_dir, solver='cbc', debug=True):
    r"""
    Create the energy system and run the optimisation model.

    Parameters
    ----------
    config_path : Path to experiment config
    results_dir : Directory for results

    Returns
    -------
    energysystem.results : Dict containing results
    """
    logger.define_logging()

    # Set timeindex
    if debug:
        periods = 20
    else:
        periods = 8760
    datetimeindex = pd.date_range('1/1/2019', periods=periods, freq='H')

    demand_heat = demand_heat['demand_1']

    # Set up EnergySystem
    logging.info('Initialize the energy system')
    energysystem = EnergySystem(timeindex=datetimeindex)

    #####################################################################
    logging.info('Create oemof objects')
    #####################################################################

    b_el = Bus(label='electricity')
    b_heat_1 = Bus(label='heat_1')
    b_heat_2 = Bus(label='heat_2')
    b_gas = Bus(label='gas', balanced=False)

    sold_el = Sink(label='sold_el', inputs={b_el: Flow(variable_costs=-1*price_electricity)})

    chp = Transformer(label='chp',
                      inputs={b_gas: Flow()},
                      outputs={b_heat_1: Flow(),
                               b_el: Flow()},
                      conversion_factors={b_heat_1: 1,
                                          b_el: 1})

    # chp = GenericCHP(
    #         label='chp',
    #         fuel_input={b_gas: Flow(
    #             H_L_FG_share_max=[0.19]*periods,
    #             variable_costs=[0.2]*periods)},
    #         electrical_output={b_el: Flow(
    #             P_max_woDH=[25]*periods,
    #             P_min_woDH=[12.5]*periods,
    #             Eta_el_max_woDH=[0.53]*periods,
    #             Eta_el_min_woDH=[0.43]*periods)},
    #         heat_output={b_heat_1: Flow(
    #             Q_CW_min=[0]*periods)},
    #         Beta=[0]*periods,
    #         back_pressure=True)

    pth_central = Source(label='pth_central', outputs={b_heat_1: Flow(variable_costs=1e6)})

    tes_central = GenericStorage(label='storage_central',
                          inputs={b_heat_1: Flow(variable_costs=0.0001)},
                          outputs={b_heat_1: Flow()},
                          nominal_storage_capacity=15,
                          initial_storage_level=0.75,
                          #min_storage_level=0.4,
                          #max_storage_level=0.9,
                          loss_rate=0.1,
                          loss_constant=0.,
                          inflow_conversion_factor=1.,
                          outflow_conversion_factor=1.)

    dhn = Transformer(label='dhn',
                      inputs={b_heat_1: Flow()},
                      outputs={b_heat_2: Flow()}, 
                      conversion_factors={b_heat_2: 1})

    pth_decentral = Source(label='pth_decentral', outputs={b_heat_2: Flow(variable_costs=1e6)})

    tes_decentral = GenericStorage(label='storage_decentral',
                                   inputs={b_heat_2: Flow(variable_costs=0.0001)},
                                   outputs={b_heat_2: Flow()},
                                   nominal_storage_capacity=15,
                                   initial_storage_level=0.75,
                                   #min_storage_level=0.4,
                                   #max_storage_level=0.9,
                                   loss_rate=0.1,
                                   loss_constant=0.,
                                   inflow_conversion_factor=1.,
                                   outflow_conversion_factor=1.)

    demand_th = Sink(label='demand_th',
                     inputs={b_heat_2: Flow(nominal_value=1,
                             actual_value=demand_heat,
                             fixed=True)})

    energysystem.add(b_el, b_heat_1, b_heat_2, b_gas, chp, sold_el,
                     pth_central, tes_central, dhn, 
                     pth_decentral, tes_decentral, demand_th)

    #####################################################################
    logging.info('Solve the optimization problem')
    #####################################################################

    om = Model(energysystem)
    om.solve(solver=solver, solve_kwargs={'tee': True}, cmdline_options={'AllowableGap=': '0.01'})

    if debug:
        abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
        filename = os.path.join(
            abs_path,
            results_dir,
            'optimisation_results',
            'model.lp')
        logging.info('Store lp-file in {0}.'.format(filename))
        om.write(filename, io_options={'symbolic_solver_labels': True})


    #####################################################################
    logging.info('Check the results')
    #####################################################################

    energysystem.results['main'] = outputlib.processing.results(om)
    energysystem.results['meta'] = outputlib.processing.meta_results(om)
    energysystem.results['param'] = outputlib.processing.parameter_as_dict(om)
    energysystem.dump(dpath=results_dir + '/optimisation_results', filename='es.dump')

    def save_es_graph(energysystem, results_dir):
        energysystem_graph = graph.create_nx_graph(energysystem)
        graph_file_name = os.path.join(results_dir, 'data_plots/energysystem_graph.pkl')
        nx.readwrite.write_gpickle(G=energysystem_graph, path=graph_file_name)
    
    
    save_es_graph(energysystem, results_dir)

    return energysystem.results


def run_model(config_path, results_dir):
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # Load data
    # load input parameter
    file_input_parameter = os.path.join(abs_path, cfg['data_raw']['scalars']['parameters'])
    input_parameter = pd.read_csv(file_input_parameter, index_col=[1, 2])['var_value']

    # load timeseries
    file_timeseries_demand_heat = os.path.join(results_dir,
                                               'data_preprocessed',
                                               'scenario_basic',  # TODO: variable instead of fixed
                                               cfg['data_preprocessed']['timeseries']['demand_heat'])
    demand_heat = pd.read_csv(file_timeseries_demand_heat, index_col=0, sep=',')

    file_timeseries_price_electricity = os.path.join(results_dir,
                                                     'data_preprocessed',
                                                     'scenario_basic', # TODO: variable instead of fixed
                                                     cfg['data_preprocessed']['timeseries']['price_electricity_spot'])
    price_electricity = pd.read_csv(file_timeseries_price_electricity, index_col=0)['price_electricity_spot'].values
    solver = cfg['solver']
    debug = cfg['debug']
    results = model(input_parameter, demand_heat, price_electricity, results_dir, solver, debug)
    return results

if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    run_model(config_path, results_dir)

