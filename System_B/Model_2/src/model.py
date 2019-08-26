__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

import os
import re
import logging
import yaml
import pandas as pd
import numpy as np
import networkx as nx

import oemof
import oemof.outputlib as outputlib
from oemof.tools import logger
from oemof.solph import (Source, Sink, Transformer, Bus, Flow,
                         Model, EnergySystem)
from oemof.solph.components import GenericStorage, ExtractionTurbineCHP, GenericCHP
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

    # Set up EnergySystem
    logging.info('Initialize the energy system')
    energysystem = EnergySystem(timeindex=datetimeindex)

    #####################################################################
    logging.info('Create oemof objects')
    #####################################################################

    b_el_export = Bus(label='bus_el_export')
    b_el_import = Bus(label='bus_el_import')
    b_th_central = Bus(label='bus_th_central')
    b_gas = Bus(label='gas')

    source_el = Source(label='source_electricity',
                       outputs={b_el_import: Flow(variable_costs=np.nan_to_num(price_electricity),
                                                  emission_specific=input_parameter['source_el']
                                                  ['emission_specific'])})

    source_gas = Source(label='source_gas',
                        outputs={b_gas: Flow(variable_costs=20,
                                             emission_specific=input_parameter['source_gas']
                                             ['emission_specific'])})

    sold_el = Sink(label='sold_el', inputs={b_el_export: Flow(variable_costs=-1*np.nan_to_num(price_electricity))})

    # chp = Transformer(label='chp',
    #                   inputs={b_gas: Flow()},
    #                   outputs={b_th_central: Flow(nominal_value=input_parameter['chp', 'capacity_installed_chp']),
    #                            b_el: Flow()},
    #                   conversion_factors={b_th_central: input_parameter['chp', 'efficiency_th'],
    #                                       b_el: input_parameter['chp', 'efficiency_el']})

    # heat_shortage = Source(outputs={b_th_central: Flow(variable_costs=10000)})
    # heat_excess = Sink(inputs={b_th_central: Flow(variable_costs=10000)})

    nominal_value_gas = input_parameter['chp', 'capacity_installed'] * 1/input_parameter['chp', 'efficiency_th']
    chp = ExtractionTurbineCHP(label='chp',
                               inputs={b_gas: Flow(nominal_value=nominal_value_gas)},
                               outputs={b_th_central: Flow(nominal_value=input_parameter['chp',
                                                                                         'capacity_installed'],
                                                           annuity_specific=1,
                                                           fom_specific=1),
                                        b_el_export: Flow()},
                               conversion_factors={b_th_central: input_parameter['chp', 'efficiency_th'],
                                                   b_el_export: input_parameter['chp', 'efficiency_el']},
                               conversion_factor_full_condensation={
                                   b_el_export: input_parameter['chp', 'efficiency_el_full_cond']})

    # chp = ExtractionTurbineCHP(label='chp',
    #                            inputs={b_gas: Flow(nominal_value=300)},
    #                            outputs={b_th_central: Flow(), b_el: Flow()},
    #                            conversion_factors={b_th_central: 0.5, b_el: 0.3},
    #                            conversion_factor_full_condensation={b_el: 0.5})

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

    pth_central = Transformer(label='pth_central',
                              inputs={b_el_import: Flow()},
                              outputs={b_th_central: Flow(nominal_value=2,
                                                          annuity_specific=1,
                                                          fom_specific=1,
                                                          variable_costs=1e6)},
                              conversion_factors={b_th_central: input_parameter['pth_resistive_central']
                                                                               ['efficiency']})

    tes_central = GenericStorage(label='storage_central',
                                 inputs={b_th_central: Flow(nominal_value=input_parameter['tes_central',
                                                                                          'power_charging'],
                                                            variable_costs=0.0001)},
                                 outputs={b_th_central: Flow(nominal_value=input_parameter['tes_central',
                                                                                           'power_discharging'])},
                                 nominal_storage_capacity=input_parameter['tes_central', 'capacity_installed'],
                                 initial_storage_level=input_parameter['tes_central', 'storage_level_initial'],
                                 # min_storage_level=0.4,
                                 # max_storage_level=0.9,
                                 loss_rate=input_parameter['tes_central', 'rate_loss'],
                                 # loss_constant=0.,
                                 inflow_conversion_factor=input_parameter['tes_central', 'efficiency_charging'],
                                 outflow_conversion_factor=input_parameter['tes_central', 'efficiency_discharging'])

    list_bus_th_decentral = []
    list_pipes = []
    list_pth_decentral = []
    list_tes_decentral = []
    list_demand_th = []
    regex = re.compile(r"^[^_]*")
    find_subnet = lambda str: re.search(regex, str).group(0)
    for column in demand_heat.columns:
        name_subnet = find_subnet(column)
        bus_th = Bus(label=name_subnet+'_bus_th_decentral')
        pipe = Transformer(label=name_subnet+'_pipe',
                           inputs={b_th_central: Flow()},
                           outputs={bus_th: Flow()},
                           conversion_factors={bus_th: input_parameter[name_subnet+'_pipe']['efficiency']})
        pth_decentral = Transformer(label=name_subnet+'_pth_decentral',
                                    inputs={b_el_import: Flow()},
                                    outputs={bus_th: Flow(
                                        nominal_value=input_parameter[name_subnet+'_pth']
                                                                     ['capacity_installed'],
                                        annuity_specific=1,
                                        fom_specific=1)},
                                    conversion_factors={bus_th: input_parameter[name_subnet+'_pth']
                                                                               ['efficiency']})
        tes_decentral = GenericStorage(label=name_subnet+'_storage_decentral',
                                       inputs={bus_th: Flow(variable_costs=0.0001)},
                                       outputs={bus_th: Flow()},
                                       nominal_storage_capacity=input_parameter[name_subnet+'_tes']
                                                                               ['capacity_installed'],
                                       annuity_specific=1,
                                       fom_specific=0,
                                       initial_storage_level=input_parameter[name_subnet+'_tes']
                                                                            ['storage_level_initial'],
                                       # min_storage_level=0.4,
                                       # max_storage_level=0.9,
                                       loss_rate=input_parameter[name_subnet+'_tes']
                                                                ['rate_loss'],
                                       loss_constant=0.,
                                       inflow_conversion_factor=input_parameter[name_subnet+'_tes']
                                                                               ['efficiency_charging'],
                                       outflow_conversion_factor=input_parameter[name_subnet+'_tes']
                                                                                ['efficiency_discharging'])
        demand_th = Sink(label=name_subnet+'_demand_th',
                         inputs={bus_th: Flow(nominal_value=1,
                                              actual_value=demand_heat[column],
                                              fixed=True)})
        list_bus_th_decentral.append(bus_th)
        list_pipes.append(pipe)
        list_pth_decentral.append(pth_decentral)
        list_tes_decentral.append(tes_decentral)
        list_demand_th.append(demand_th)

    energysystem.add(b_el_export, b_el_import, b_th_central, b_gas,
                     chp, sold_el, source_gas, source_el, pth_central, tes_central,
                     *list_pipes, *list_bus_th_decentral, *list_pth_decentral,
                     *list_tes_decentral, *list_demand_th)

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

    input_parameter = pd.read_csv(os.path.join(results_dir,
                                  'data_preprocessed',
                                  cfg['data_preprocessed']['scalars']['model_runs']),
                     index_col=[0, 1, 2], header=[0, 1])
    i = 0
    input_parameter = input_parameter.iloc[i]

    # load timeseries
    file_timeseries_demand_heat = os.path.join(results_dir,
                                               'data_preprocessed',
                                               cfg['data_preprocessed']['timeseries']['demand_heat'])
    demand_heat = pd.read_csv(file_timeseries_demand_heat, index_col=0, sep=',')

    file_timeseries_price_electricity = os.path.join(results_dir,
                                                     'data_preprocessed',
                                                     cfg['data_preprocessed']['timeseries']['price_electricity_spot'])
    price_electricity = pd.read_csv(file_timeseries_price_electricity, index_col=0)['price_electricity_spot'].values
    solver = cfg['solver']
    debug = cfg['debug']
    results = model(input_parameter, demand_heat, price_electricity, results_dir, solver, debug)
    return results


if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    run_model(config_path, results_dir)
