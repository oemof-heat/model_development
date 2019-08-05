__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import os
import yaml
import logging

import oemof
import oemof.outputlib as outputlib
from oemof.tools import logger
from oemof.solph import (Source, Sink, Transformer, Bus, Flow,
                         Model, EnergySystem)
from oemof.solph.components import GenericStorage
import oemof.graph as graph


def run_model(config_path, results_dir):
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

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # Set timeindex
    if cfg['debug']:
        periods = 20
    else:
        periods = 8760
    datetimeindex = pd.date_range('1/1/2019', periods=periods, freq='H')

    # Create data
    x = np.arange(periods)
    demand = np.zeros(20)
    demand[-3:] = 2
    wind = np.zeros(20)
    wind[:3] = 3

    timeseries = pd.DataFrame()

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

    sold_el = Sink(label='sold_el', inputs={b_el: Flow()})

    chp = Transformer(label='chp',
                      inputs={b_gas: Flow()},
                      outputs={b_heat_1: Flow(),
                               b_el: Flow()}, 
                      conversion_factors={b_heat_1: 1,
                                          b_el: 1})
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
                             actual_value=demand,
                             fixed=True)})

    energysystem.add(b_el, b_heat_1, b_heat_2, b_gas, chp, sold_el,
                     pth_central, tes_central, dhn, 
                     pth_decentral, tes_decentral, demand_th)

    #####################################################################
    logging.info('Solve the optimization problem')
    #####################################################################

    om = Model(energysystem)
    om.solve(solver=cfg['solver'], solve_kwargs={'tee': True}, cmdline_options={'AllowableGap=': '0.01'})

    if cfg['debug']:
        filename = os.path.join(
            oemof.tools.helpers.extend_basic_path('lp_files'),
            'app_district_heating.lp')
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
        graph_file_name = os.path.join(results_dir, '/plot_data/energysystem_graph.pkl')
        nx.readwrite.write_gpickle(G=energysystem_graph, path=graph_file_name)
    
    
    save_es_graph(energysystem, results_dir)

    return energysystem.results