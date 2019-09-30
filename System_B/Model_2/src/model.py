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

import oemof.outputlib as outputlib
from oemof.tools import logger
from oemof.solph import (Source, Sink, Transformer, Bus, Flow, Model, EnergySystem)
from oemof.solph.components import GenericStorage, ExtractionTurbineCHP
import oemof.graph as graph

import helpers
from facades import Pipe


def model(index, input_parameter, demand_heat, price_electricity, results_dir, solver='cbc', debug=True):
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
    datetimeindex = pd.date_range('1/1/2018', periods=periods, freq='H')

    # Set up EnergySystem
    logging.info('Initialize the energy system')
    energysystem = EnergySystem(timeindex=datetimeindex)

    #####################################################################
    logging.info('Create oemof objects')
    #####################################################################

    b_el_export = Bus(label='bus_el_export')
    b_el_import = Bus(label='bus_el_import')
    b_th_central = Bus(label='bus_th_central')
    b_gas = Bus(label='bus_gas')

    scaling_factor = input_parameter['source_electricity']['spot_price'] - np.mean(price_electricity)
    variable_costs_el = scaling_factor + np.nan_to_num(price_electricity)\
                        + input_parameter['source_electricity']['tax_levys']

    source_el = Source(label='source_electricity',
                       outputs={b_el_import: Flow(variable_costs=variable_costs_el,
                                                  emission_specific=input_parameter['source_electricity']
                                                                                   ['emission_specific'])})

    variable_costs_el_flex = scaling_factor + np.nan_to_num(price_electricity)
    variable_costs_el_flex += input_parameter['source_electricity_flex']['tax_levys']  # TODO: Check
    price_el_negative = np.nan_to_num(price_electricity) <= 0

    source_el_flex = Source(label='source_electricity_flex',
                            outputs={b_el_import: Flow(nominal_value=1e6,
                                                       max=price_el_negative.astype(int),
                                                       variable_costs=variable_costs_el_flex,
                                                       emission_specific=input_parameter['source_electricity']
                                                                                        ['emission_specific'])})

    variable_costs_gas = input_parameter['source_gas']['carrier_price'] \
                       + input_parameter['source_gas']['co2_ets']
    variable_costs_gas += input_parameter['source_gas']['co2_fee']  # TODO: Check

    source_gas = Source(label='source_gas',
                        outputs={b_gas: Flow(variable_costs=variable_costs_gas,
                                             emission_specific=input_parameter['source_gas']
                                                                              ['emission_specific'])})

    revenue_sold_el = -1 * np.nan_to_num(price_electricity)
    revenue_sold_el -= input_parameter['chp', 'chp_surcharges']  # TODO: Check
    sold_el = Sink(label='sold_el', inputs={b_el_export: Flow(variable_costs=revenue_sold_el)})

    nominal_value_gas = input_parameter['chp', 'capacity_installed'] * 1/input_parameter['chp', 'efficiency_th']
    chp = ExtractionTurbineCHP(label='chp',
                               inputs={b_gas: Flow(nominal_value=nominal_value_gas,
                                                   variable_costs=input_parameter['chp', 'network_charges_WP'])},
                               outputs={b_th_central: Flow(nominal_value=input_parameter['chp',
                                                                                         'capacity_installed'],
                                                           variable_costs=input_parameter['chp', 'vom']),
                                        b_el_export: Flow()},
                               conversion_factors={b_th_central: input_parameter['chp', 'efficiency_th'],
                                                   b_el_export: input_parameter['chp', 'efficiency_el']},
                               conversion_factor_full_condensation={
                                   b_el_export: input_parameter['chp', 'efficiency_el_full_cond']})

    gas_boiler_central = Transformer(label='gas_boiler_central',
                                     inputs={b_gas: Flow(variable_costs=input_parameter['gas_boiler_central']
                                                                                       ['energy_tax']
                                                                      + input_parameter['gas_boiler_central']
                                                                                       ['network_charges_WP'])},
                                     outputs={b_th_central: Flow(nominal_value=input_parameter['gas_boiler_central']
                                                                                              ['capacity_installed'],
                                                                 variable_costs=input_parameter['gas_boiler_central']
                                                                                               ['vom'],)},
                                     conversion_factors={b_th_central: input_parameter['gas_boiler_central']
                                                                                      ['efficiency']})

    pth_central = Transformer(label='pth_resistive_central',
                              inputs={b_el_import: Flow(variable_costs=input_parameter['pth_resistive_central']
                                                                                      ['network_charges_WP'])},
                              outputs={b_th_central: Flow(nominal_value=input_parameter['pth_resistive_central']
                                                                                       ['capacity_installed'],
                                                          variable_costs=input_parameter['pth_resistive_central']
                                                                                        ['vom'],)},
                              conversion_factors={b_th_central: input_parameter['pth_resistive_central']
                                                                               ['efficiency']})

    b_th_central_behind_storage = Bus(label='bus_th_central_behind_storage')
    transformer_b_th_central = Transformer(label='transformer_bth_central',
                                           inputs={b_th_central: Flow()},
                                           outputs={b_th_central_behind_storage: Flow()},
                                           conversion_factors={b_th_central_behind_storage: 1.})
    tes_central = GenericStorage(label='tes_central',
                                 inputs={b_th_central: Flow(nominal_value=input_parameter['tes_central',
                                                                                          'power_charging'],
                                                            variable_costs=0.0001)},
                                 outputs={b_th_central_behind_storage: Flow(
                                     nominal_value=input_parameter['tes_central',
                                                                   'power_discharging'])},
                                 nominal_storage_capacity=input_parameter['tes_central', 'capacity_installed'],
                                 loss_rate=input_parameter['tes_central', 'rate_loss'],
                                 inflow_conversion_factor=input_parameter['tes_central', 'efficiency_charging'],
                                 outflow_conversion_factor=input_parameter['tes_central', 'efficiency_discharging'])

    list_bus_th_decentral = []
    list_bus_th_decentral_behind_storage = []
    list_transformer_bus_th_decentral = []
    list_pipes = []
    list_pth_decentral = []
    list_heat_pump_decentral = []
    list_tes_decentral = []
    list_demand_th = []
    regex = re.compile(r"^[^_]*")
    find_subnet = lambda str: re.search(regex, str).group(0)
    for column in demand_heat.columns:
        name_subnet = find_subnet(column)
        b_th_decentral = Bus(label=name_subnet+'_bus_th_decentral')
        pipe = Pipe(label=name_subnet+'_pipe',
                    inputs={b_th_central_behind_storage: Flow()},
                    outputs={b_th_decentral: Flow()},
                    losses_fixed=input_parameter[name_subnet+'_pipe']['losses_fixed'],
                    loss_factor=1).get_components()

        pth_decentral = Transformer(label=name_subnet+'_pth_resistive_decentral',
                                    inputs={b_el_import: Flow(variable_costs=input_parameter['pth_resistive_decentral']
                                                                                            ['network_charges_WP'])},
                                    outputs={b_th_decentral: Flow(
                                        nominal_value=input_parameter[name_subnet+'_pth_resistive_decentral']
                                                                     ['capacity_installed'],
                                        variable_costs=input_parameter['pth_resistive_decentral']
                                                                      ['vom'])},
                                    conversion_factors={b_th_decentral: input_parameter['pth_resistive_decentral']
                                                                                       ['efficiency']})
        heat_pump_decentral = Transformer(label=name_subnet+'_pth_heat_pump_decentral',
                                          inputs={b_el_import: Flow(variable_costs=input_parameter['pth_heat_pump_decentral']
                                                                                                  ['network_charges_WP'])},
                                          outputs={b_th_decentral:
                                                       Flow(nominal_value=input_parameter[name_subnet+'_pth_heat_pump_decentral']
                                                                                         ['capacity_installed'],
                                                            variable_costs=input_parameter['pth_heat_pump_decentral']
                                                                                          ['vom'])},
                                          conversion_factors={b_th_decentral: input_parameter['pth_heat_pump_decentral']
                                                                                             ['efficiency']})

        b_th_decentral_behind_storage = Bus(label=name_subnet+'_bus_th_decentral_behind_storage')
        transformer_b_th_decentral = Transformer(label=name_subnet+'_transformer_bth_decentral',
                                                 inputs={b_th_decentral: Flow()},
                                                 outputs={b_th_decentral_behind_storage: Flow()},
                                                 conversion_factors={b_th_central_behind_storage: 1.})
        tes_decentral = GenericStorage(label=name_subnet+'_tes_decentral',
                                       inputs={b_th_decentral:
                                                   Flow(nominal_value=input_parameter[name_subnet+'_tes_decentral']
                                                                                     ['power_charging'],
                                                            variable_costs=0.0001)},
                                       outputs={b_th_decentral_behind_storage:
                                                    Flow(nominal_value=input_parameter[name_subnet+'_tes_decentral']
                                                                                      ['power_discharging'])},
                                       nominal_storage_capacity=input_parameter[name_subnet+'_tes_decentral']
                                                                               ['capacity_installed'],
                                       loss_rate=input_parameter['tes_decentral']
                                                                ['rate_loss'],
                                       inflow_conversion_factor=input_parameter['tes_decentral']
                                                                               ['efficiency_charging'],
                                       outflow_conversion_factor=input_parameter['tes_decentral']
                                                                                ['efficiency_discharging'])

        if not ('global', 'factor_load_reduction_heat') in input_parameter.index:
            load_factor = 1

        elif input_parameter['global', 'factor_load_reduction_heat'] is None:
            load_factor = 1

        elif np.isnan(input_parameter['global', 'factor_load_reduction_heat']):
            load_factor = 1

        else:
            load_factor = input_parameter['global', 'factor_load_reduction_heat']

        print('load_factor: ', load_factor)
        load_factor = 1

        demand_th = Sink(label=name_subnet+'_demand_th',
                         inputs={b_th_decentral: Flow(nominal_value=load_factor,
                                              actual_value=demand_heat[column],
                                              fixed=True)})
        list_bus_th_decentral.append(b_th_decentral)
        list_bus_th_decentral_behind_storage.append(b_th_decentral_behind_storage)
        list_transformer_bus_th_decentral.append(transformer_b_th_decentral)
        list_pipes.extend(pipe)
        list_pth_decentral.append(pth_decentral)
        list_heat_pump_decentral.append(heat_pump_decentral)
        list_tes_decentral.append(tes_decentral)
        list_demand_th.append(demand_th)

    energysystem.add(b_el_export, b_el_import, b_th_central, b_gas,
                     transformer_b_th_central, b_th_central_behind_storage,
                     sold_el, source_gas, source_el, source_el_flex,
                     chp, gas_boiler_central, pth_central, tes_central,
                     *list_pipes, *list_bus_th_decentral, *list_pth_decentral,
                     *list_bus_th_decentral_behind_storage, *list_transformer_bus_th_decentral,
                     *list_heat_pump_decentral, *list_tes_decentral, *list_demand_th)

    #####################################################################
    logging.info('Solve the optimization problem')
    #####################################################################

    om = Model(energysystem)
    om.solve(solver=solver, solve_kwargs={'tee': True}, cmdline_options={'AllowableGap=': '0.0001'})

    if debug:
        abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
        filename = os.path.join(
            abs_path,
            results_dir,
            'optimisation_results',
            f'{"_".join(map(str, index))}_model.lp')
        logging.info('Store lp-file in {0}.'.format(filename))
        om.write(filename, io_options={'symbolic_solver_labels': True})


    #####################################################################
    logging.info('Check the results')
    #####################################################################

    energysystem.results['main'] = outputlib.processing.results(om)
    energysystem.results['meta'] = outputlib.processing.meta_results(om)
    energysystem.results['param'] = outputlib.processing.parameter_as_dict(om)
    energysystem.dump(dpath=results_dir + '/optimisation_results', filename=f'{"_".join(map(str, index))}_es.dump')

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

    model_runs = helpers.load_model_runs(results_dir, cfg)

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

    for index, input_parameter in model_runs.iterrows():
        results = model(index, input_parameter, demand_heat, price_electricity, results_dir, solver, debug)
    return results


if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    run_model(config_path, results_dir)
