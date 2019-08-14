"""
Determine the following quantities on each technology and save them in a dataframe:

Variable costs
Summed operating hours
Summed Production
Mean Production during operation hours
Maximal Production
Minimal Production
Full load hours
Start count


The following quantities concern the energy system as a whole:

Coverage through renewables
Summed Excess, max Excess
Summed import, max import
Emissions
"""

__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

import os
import re
import pandas as pd
import yaml

import oemof.solph as solph
import oemof.outputlib as outputlib
import helpers


def get_param_scalar(energysystem):
    param = energysystem.results['param']
    param = outputlib.processing.convert_keys_to_strings(param)
    scalars = {k: v['scalars'] for k, v in param.items()}
    component = []
    var_name = []
    var_value = []
    for comp, series in scalars.items():
        if not series.empty:
            for name, value in series.iteritems():
                component.append(comp)
                var_name.append(name)
                var_value.append(value)
    param_scalars = pd.DataFrame({'component': component, 'var_name': var_name, 'var_value': var_value})
    return param_scalars


def get_results_scalar(energysystem):
    results = energysystem.results['main']
    results = outputlib.processing.convert_keys_to_strings(results)
    scalars = {k: v['scalars'] for k, v in results.items()}
    component = []
    var_name = []
    var_value = []
    for comp, series in scalars.items():
        if not series.empty:
            for name, value in series.iteritems():
                component.append(comp)
                var_name.append(name)
                var_value.append(value)
    results_scalar = pd.DataFrame({'component': component, 'var_name': var_name, 'var_value': var_value})
    return results_scalar


def get_results_flows(energysystem):
    results = energysystem.results['main']
    results = outputlib.processing.convert_keys_to_strings(results)
    flows = {k: v['sequences'] for k, v in results.items()}
    flows = pd.concat(flows, axis=1)
    return flows


def get_derived_results_timeseries_emissions(energysystem):
    param_scalar = get_param_scalar(energysystem)
    flows = get_results_flows(energysystem)

    emission_specific = param_scalar.loc[param_scalar['var_name']=='emission_specific']
    flows_with_emission_specific = flows[[(*component, 'flow') for component in emission_specific['component']]]
    flows_with_emission_specific.columns = flows_with_emission_specific.columns.remove_unused_levels()
    def func(x):
        factor = emission_specific.loc[emission_specific['component']==x.name[:2]]['var_value'].squeeze()
        return x*factor
    timeseries_emission = flows_with_emission_specific.apply(func, axis=0)
    timeseries_emission.columns = timeseries_emission.columns.set_levels(['emission'], level=2)
    return timeseries_emission


def get_derived_results_timeseries_costs_variable(energysystem):
    param_scalar = get_param_scalar(energysystem)
    flows = get_results_flows(energysystem)

    cost_variable = param_scalar.loc[param_scalar['var_name']=='variable_costs']
    flows_with_cost_variable = flows[[(*component, 'flow') for component in cost_variable['component']]]
    flows_with_cost_variable.columns = flows_with_cost_variable.columns.remove_unused_levels()
    def func(x):
        factor = cost_variable.loc[cost_variable['component']==x.name[:2]]['var_value'].squeeze()
        return x*factor
    timeseries_cost_variable = flows_with_cost_variable.apply(func, axis=0)
    timeseries_cost_variable.columns = timeseries_cost_variable.columns.set_levels(['cost_variable'], level=2)
    return timeseries_cost_variable


def get_derived_results_scalar(param_scalar,
                               results_scalar,
                               results_timeseries_flows,
                               derived_results_timeseries_costs_variable,
                               derived_results_timeseries_emissions):
    r"""
    Parameters
    ----------
    energysystem : oemof.solph.EnergySystem

    Production (for each producer)
    * energy_thermal_produced_sum
    * power_thermal_max
    * power_thermal_min
    * power_thermal_during_operation_mean
    * hours_operating_sum
    * hours_full_load for each producer
    * number_starts

    Storage operation
    * energy_heat_storage_discharge_sum

    Heat pump operation
    * seasonal_performance_factor_heat_pumps_mean

    DHN operation
    * energy_losses_heat_dhn_sum
    * energy_consumed_pump_sum

    Whole system energy
    * energy_excess_sum
    * energy_excess_max
    * energy_import_sum
    * energy_import_max
    * energy_consumed_gas_sum
    * energy_consumed_electricity_sum
    * fraction_renewables

    Whole system cost
    * cost_operation_sum
    * cost_investment_sum
    * cost_specific_heat_mean
    """
    producers_heat = [component for component in results_timeseries_flows.columns
                      if component[1] in ['heat_1', 'heat_2']
                      and not bool(re.search('storage', component[0]))
                      and not bool(re.search('dhn', component[0]))]
    energy_thermal_produced_sum = results_timeseries_flows[producers_heat].sum()
    energy_thermal_produced_sum.index = energy_thermal_produced_sum.index.droplevel('variable_name')
    power_thermal_max = results_timeseries_flows[producers_heat].max()
    power_thermal_min = results_timeseries_flows[producers_heat].max()
    operating = (results_timeseries_flows[producers_heat] > 0)
    power_thermal_during_operation_mean = results_timeseries_flows[producers_heat][operating].mean()
    hours_operating_sum = operating.sum()
    number_starts = (operating[:-1].reset_index(drop=True) < operating[1:].reset_index(drop=True)).sum()

    installed_production_capacity = param_scalar.loc[param_scalar['var_name']=='nominal_value']

    # hours_full_load = energy_thermal_produced_sum * 1/installed_capacity

    installed_production_capacity.index = pd.MultiIndex.from_tuples(installed_production_capacity['component'])
    installed_production_capacity = installed_production_capacity['var_value']
    hours_full_load = energy_thermal_produced_sum * 1/installed_production_capacity
    return pd.Series()


def postprocess(config_path, results_dir):
    # # open config
    # abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    # with open(config_path, 'r') as ymlfile:
    #     cfg = yaml.load(ymlfile)

    # restore energysystem
    energysystem = solph.EnergySystem()
    energysystem.restore(dpath=results_dir + '/optimisation_results', filename='es.dump')
    dir_postproc = os.path.join(results_dir, 'data_postprocessed')

    # Collect primary results
    param_scalar = get_param_scalar(energysystem)
    param_scalar.to_csv(os.path.join(dir_postproc, 'parameters_scalar.csv'))
    results_scalar = get_results_scalar(energysystem)
    results_scalar.to_csv(os.path.join(dir_postproc, 'results_scalar.csv'))
    results_timeseries_flows = get_results_flows(energysystem)
    results_timeseries_flows.to_csv(os.path.join(dir_postproc, 'timeseries/results_timeseries.csv'))

    # Calculate derived results
    derived_results_timeseries_emissions = get_derived_results_timeseries_emissions(energysystem)
    derived_results_timeseries_emissions.to_csv(os.path.join(dir_postproc,
                                                             'timeseries/' +
                                                             'results_timeseries_emissions_variable.csv'))
    derived_results_timeseries_costs_variable = get_derived_results_timeseries_costs_variable(energysystem)
    derived_results_timeseries_costs_variable.to_csv(os.path.join(dir_postproc,
                             'timeseries/' +
                             'results_timeseries_costs_variable.csv'))
    derived_results_scalar = get_derived_results_scalar(param_scalar,
                                                        results_scalar,
                                                        results_timeseries_flows,
                                                        derived_results_timeseries_costs_variable,
                                                        derived_results_timeseries_emissions)
    derived_results_scalar.to_csv(os.path.join(dir_postproc,
                                               'results_scalar_derived.csv'), header=True)


if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    postprocess(config_path, results_dir)
