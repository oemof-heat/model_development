"""
This application models a district heating system with
a natural gas fired gas turbine supplying to the main network and
decentralized power-to-heat supplying to the sub network.

Usage: app_district_heating.py [options]

Options:

  -d, --debug              Sets timesteps to 2 and writes the lp file
  -o, --solver=SOLVER      The solver to use. Should be one of
                           helpers "glpk", "cbc" or "gurobi". [default: cbc]
      --invest-pth         Invest optimize the power-to-heat plant.
      --invest-chp         Invest optimize the gas turbine.

"""

__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

from oemof.tools import logger, economics
import oemof.tools.helpers
import oemof.solph as solph
from oemof.outputlib import processing
import oemof.graph as graph
import networkx as nx
import logging
import os
import pandas as pd
import yaml
import helpers


logger.define_logging()


def run_model_dessau(config_path, results_dir):
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
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # load input parameter
    in_param = pd.read_csv(os.path.join(abs_path, cfg['input_parameter']), index_col=[1, 2])['var_value']
    wacc = in_param['general', 'wacc']

    # load timeseries
    demand_heat_timeseries = pd.read_csv(os.path.join(results_dir, cfg['timeseries']['timeseries_demand_heat']),
                                         index_col=0, names=['demand_heat'], sep=',')['demand_heat']
    print(demand_heat_timeseries.head())

    # create timeindex
    if cfg['debug']:
        number_timesteps = 200
    else:
        number_timesteps = 8760

    date_time_index = pd.date_range('1/1/2017',
                                    periods=number_timesteps,
                                    freq='H')

    logging.info('Initialize the energy system')
    energysystem = solph.EnergySystem(timeindex=date_time_index)

    #####################################################################
    logging.info('Create oemof objects')
    #####################################################################

    bgas = solph.Bus(label="natural_gas", balanced=False)
    bel = solph.Bus(label="electricity", balanced=False)
    bth_prim = solph.Bus(label="heat_prim")
    bth_sec = solph.Bus(label="heat_sec")
    bth_end = solph.Bus(label="heat_end")

    energysystem.add(bgas, bth_prim, bth_sec, bth_end, bel)

    # energysystem.add(solph.Sink(label='excess_heat',
    #     inputs={bth_prim: solph.Flow()}))

    energysystem.add(solph.Source(label='shortage_heat',
        outputs={bth_prim: solph.Flow(variable_costs=in_param['shortage_heat','var_costs'])}))

    # energysystem.add(solph.Source(label='rgas',
    #     outputs={bgas: solph.Flow(
    #         variable_costs=0)}))

    if cfg['chp_repr'] == 'option_1':
        bsteam = solph.Bus(label="steam", balanced=True)
        energysystem.add(bsteam)

        energysystem.add(solph.Transformer(
            label='gas_turbine',
            inputs={bgas: solph.Flow(variable_costs=in_param['bgas','price_gas'])},
            outputs={bel: solph.Flow(),
                     bsteam: solph.Flow()},
            conversion_factors={bel: 0.5, bsteam: 0.5}))

        energysystem.add(solph.Transformer(
            label='sde',
            inputs={bgas: solph.Flow(variable_costs=in_param['bgas','price_gas'])},
            outputs={bsteam: solph.Flow()},
            conversion_factors={bsteam: 0.5}))

        energysystem.add(solph.Transformer(
            label='steam_turbine',
            inputs={bsteam: solph.Flow()},
            outputs={bel: solph.Flow(),
                     bth_prim: solph.Flow()},
            conversion_factors={bel: 0.5, bth_prim: 0.5}))

    if cfg['chp_repr'] == 'option_2':
        energysystem.add(solph.Transformer(
            label='GuD',
            inputs={bgas: solph.Flow(variable_costs=in_param['bgas','price_gas'])},
            outputs={bel: solph.Flow(nominal_value=in_param['ccgt','nominal_value']),
                     bth_prim: solph.Flow(nominal_value=in_param['ccgt','nominal_value'])},
            conversion_factors={bel: 0.5, bth_prim: 0.5}))

        energysystem.add(solph.Transformer(
            label='SDEuD',
            inputs={bgas: solph.Flow(variable_costs=in_param['bgas','price_gas'])},
            outputs={bel: solph.Flow(nominal_value=in_param['ccgt','nominal_value']),
                     bth_prim: solph.Flow(nominal_value=in_param['ccgt','nominal_value'])},
            conversion_factors={bel: 0.5, bth_prim: 0.5}))

    if cfg['investment']['invest_pth']:
        energysystem.add(solph.Transformer(
            label='power_to_heat',
            inputs={bel: solph.Flow(variable_costs=in_param['bel','price_el'])},
            outputs={bth_prim: solph.Flow(
                investment=solph.Investment(
                    ep_costs=economics.annuity(
                        capex=in_param['power_to_heat','capex'], n=in_param['power_to_heat','inv_period'], wacc=wacc)),
                variable_costs=0)},
            conversion_factors={bth_prim: 1}))

    else:
        energysystem.add(solph.Transformer(label='power_to_heat',
            inputs={bel: solph.Flow(variable_costs=in_param['bel','price_el'])},
            outputs={bth_prim: solph.Flow(
                nominal_value=in_param['power_to_heat','nominal_value'],
                variable_costs=0)},
            conversion_factors={bth_prim: 1}))

    energysystem.add(solph.Transformer(label='hwe',
           inputs={bgas: solph.Flow(variable_costs=in_param['bgas','price_gas'])},
           outputs={bth_prim: solph.Flow(
               nominal_value=in_param['hwe', 'nominal_value'],
               variable_costs=0)},
           conversion_factors={bth_prim: 0.5}))

    energysystem.add(solph.Transformer(
        label='dhn_prim',
        inputs={bth_prim: solph.Flow()},
        outputs={bth_sec: solph.Flow()},
        conversion_factors={bth_sec: 1.}))

    energysystem.add(solph.Transformer(
        label='dhn_sec',
        inputs={bth_sec: solph.Flow()},
        outputs={bth_end: solph.Flow()},
        conversion_factors={bth_end: 1.}))

    energysystem.add(solph.Sink(
        label='demand_heat',
        inputs={bth_end: solph.Flow(
            actual_value=demand_heat_timeseries,
            fixed=True,
            nominal_value=1.,
            summed_min=1)}))

    energysystem.add(solph.components.GenericStorage(
        label='storage_heat',
        nominal_capacity=in_param['storage_heat','nominal_capacity'],
        inputs={bth_prim: solph.Flow(
            variable_costs=0,
            nominal_value=in_param['storage_heat','input_nominal_value'])},
        outputs={bth_prim: solph.Flow(
            nominal_value=in_param['storage_heat','output_nominal_value'])},
        capacity_loss=in_param['storage_heat','capacity_loss'],
        inflow_conversion_factor=1,
        outflow_conversion_factor=1))

    energysystem_graph = graph.create_nx_graph(energysystem)
    graph_file_name = os.path.join(results_dir, 'energysystem_graph.pkl')
    nx.readwrite.write_gpickle(G=energysystem_graph, path=graph_file_name)

    #####################################################################
    logging.info('Solve the optimization problem')


    om = solph.Model(energysystem)
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

    energysystem.results['main'] = processing.results(om)
    energysystem.results['meta'] = processing.meta_results(om)
    energysystem.results['param'] = processing.parameter_as_dict(om)
    energysystem.dump(dpath=results_dir + '/optimisation_results', filename='es.dump')

    return energysystem.results

if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    run_model_dessau(config_path=config_path, results_dir=results_dir)
