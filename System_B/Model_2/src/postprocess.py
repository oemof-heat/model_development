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
    param_scalars.set_index(pd.MultiIndex.from_tuples(param_scalars['component']), inplace=True)
    param_scalars = param_scalars.drop(columns='component')
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
    flows_with_emission_specific = flows[[(*ll, 'flow') for ll in emission_specific.index]]
    flows_with_emission_specific.columns = flows_with_emission_specific.columns.remove_unused_levels()
    def func(x):
        factor = emission_specific.loc[x.name[:2]]['var_value']
        return x*factor
    timeseries_emission = flows_with_emission_specific.apply(func, axis=0)
    timeseries_emission.columns = timeseries_emission.columns.set_levels(['emission'], level=2)
    return timeseries_emission


def get_derived_results_timeseries_costs_variable(energysystem):
    param_scalar = get_param_scalar(energysystem)
    flows = get_results_flows(energysystem)

    cost_variable = param_scalar.loc[param_scalar['var_name']=='variable_costs']
    flows_with_cost_variable = flows[[(*ll, 'flow') for ll in cost_variable.index]]
    flows_with_cost_variable.columns = flows_with_cost_variable.columns.remove_unused_levels()
    def func(x):
        factor = cost_variable.loc[x.name[:2]]['var_value']
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
    * energy_consumed_gas_sum
    * energy_consumed_electricity_sum
    * fraction_renewables

    Whole system cost
    * cost_operation_sum
    * cost_investment_sum
    * cost_specific_heat_mean
    """
    # Production
    producers_heat = [component for component in results_timeseries_flows.columns
                      if bool(re.search('bus_th', component[1]))
                      and not bool(re.search('storage', component[0]))
                      and not bool(re.search('pipe', component[0]))]

    energy_thermal_produced_sum = results_timeseries_flows[producers_heat].sum()
    energy_thermal_produced_sum.index = energy_thermal_produced_sum.index.\
        remove_unused_levels().\
        set_levels(['energy_thermal_produced_sum'], level=2)

    power_thermal_max = results_timeseries_flows[producers_heat].max()
    power_thermal_max.index = power_thermal_max.index. \
        remove_unused_levels().\
        set_levels(['power_thermal_max'], level=2)

    power_thermal_min = results_timeseries_flows[producers_heat].min()
    power_thermal_min.index = power_thermal_min.index. \
        remove_unused_levels().\
        set_levels(['power_thermal_min'], level=2)

    operating = (results_timeseries_flows[producers_heat] > 0)
    operating.columns = operating.columns.\
        remove_unused_levels()\
        .set_levels(['status_operating'], level=2)

    power_thermal_during_operation_mean = results_timeseries_flows[producers_heat][operating].mean()
    power_thermal_during_operation_mean.index = power_thermal_during_operation_mean.index.\
        remove_unused_levels().\
        set_levels(['power_thermal_during_operation_mean'], level=2)

    hours_operating_sum = operating.sum()
    hours_operating_sum.index = hours_operating_sum.index.\
        remove_unused_levels().\
        set_levels(['hours_operating_sum'], level=2)

    number_starts = (operating[:-1].reset_index(drop=True) < operating[1:].reset_index(drop=True)).sum()
    number_starts.index = number_starts.index.\
        remove_unused_levels().\
        set_levels(['number_starts'], level=2)
    installed_production_capacity = param_scalar.loc[[key[:2] for key in producers_heat]]
    installed_production_capacity = installed_production_capacity.loc[installed_production_capacity['var_name']=='nominal_value']

    installed_production_capacity = pd.DataFrame(installed_production_capacity)
    installed_production_capacity['variable_name'] = 'installed_production_capacity'
    installed_production_capacity.set_index('variable_name', append=True, inplace=True)
    installed_production_capacity = installed_production_capacity['var_value']
    hours_full_load = energy_thermal_produced_sum * 1/installed_production_capacity
    hours_full_load = pd.DataFrame(hours_full_load)
    hours_full_load['variable_name'] = 'hours_full_load'
    hours_full_load.set_index('variable_name', append=True, inplace=True)
    hours_full_load = hours_full_load[0]

    # Storage operation
    storage_discharge = [component for component in results_timeseries_flows.columns
                         if component[1]!='None'
                         and bool(re.search('storage', component[0]))]
    energy_heat_storage_discharge_sum = results_timeseries_flows[storage_discharge].sum()
    energy_heat_storage_discharge_sum.index = energy_heat_storage_discharge_sum.index.\
        remove_unused_levels().\
        set_levels(['energy_heat_storage_discharge_sum'], level=2)
    # TODO: number_storage_cycles = 0 # equivalent full cycles?

    # Heat pump operation
    # TODO: seasonal_performance_factor_heat_pumps_mean = 0 # heat produced / electricity consumed

    # DHN operation
    pipes = [component[0] for component in results_timeseries_flows.columns
             if bool(re.search('_pipe', component[0]))]
    energy_losses_heat_dhn = results_timeseries_flows.loc[:, (slice(None), pipes, slice(None))].sum(axis=1)\
        - results_timeseries_flows.loc[:, (pipes, slice(None), slice(None))].sum(axis=1)
    energy_losses_heat_dhn_sum = pd.Series(energy_losses_heat_dhn.sum(),
                                           index=pd.MultiIndex.from_tuples([('dhn', 'None', 'energy_losses_heat_dhn_sum')],
                                           names=[None,None,'variable_name']))
    # TODO: energy_consumed_pump_sum = 0

    # Whole system energy
    energy_consumed_gas_sum = results_timeseries_flows.loc[:, ('gas', slice(None), slice(None))].sum()
    energy_consumed_gas_sum.index = energy_consumed_gas_sum.index.\
        remove_unused_levels().\
        set_levels(['energy_consumed_sum'], level=2)

    # TODO: Correct
    energy_consumed_electricity_sum = results_timeseries_flows.loc[:, ('bus_el_import', slice(None), slice(None))].sum()
    energy_consumed_electricity_sum.index = energy_consumed_electricity_sum.index.\
        remove_unused_levels().\
        set_levels(['energy_consumed_sum'], level=2)

    # TODO: fraction_renewable_energy_thermal = 0 # renewable energy / total energy consumed

    # Whole system cost
    cost_variable_sum = derived_results_timeseries_costs_variable.sum()
    cost_vom_sum = 0
    cost_fom = 0
    cost_capital = 0
    cost_total_system = cost_variable_sum #  + cost_vom_sum + cost_fom + cost_capital
    cost_total_system.index = cost_total_system.index.\
        remove_unused_levels().\
        set_levels(['cost_total_system'], level=2)
    cost_specific_heat_mean = 0 # Durchschnittliche Waermegestehungskosten

    # Emissions
    emissions_sum = derived_results_timeseries_emissions.sum()

    derived_results_scalar = pd.concat([energy_thermal_produced_sum,
                                        power_thermal_max,
                                        power_thermal_min,
                                        power_thermal_during_operation_mean,
                                        hours_operating_sum,
                                        number_starts,
                                        installed_production_capacity,
                                        hours_full_load,
                                        energy_consumed_gas_sum,
                                        energy_consumed_electricity_sum,
                                        cost_variable_sum,
                                        energy_heat_storage_discharge_sum,
                                        energy_losses_heat_dhn_sum,
                                        cost_total_system,
                                        emissions_sum])
    derived_results_scalar.name = 'var_value'
    return derived_results_scalar


def postprocess(config_path, results_dir):
    r'''
    Runs the whole postprocessing pipeline and saves the results.
    '''
    # open config
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # restore energysystem
    energysystem = solph.EnergySystem()
    energysystem.restore(dpath=results_dir + '/optimisation_results', filename='es.dump')
    dir_postproc = os.path.join(results_dir, 'data_postprocessed')

    # Collect primary results
    param_scalar = get_param_scalar(energysystem)
    param_scalar.to_csv(os.path.join(dir_postproc, cfg['data_postprocessed']['scalars']['parameters']))
    results_scalar = get_results_scalar(energysystem)
    results_scalar.to_csv(os.path.join(dir_postproc,  cfg['data_postprocessed']['scalars']['results']))
    results_timeseries_flows = get_results_flows(energysystem)
    results_timeseries_flows.to_csv(os.path.join(dir_postproc, cfg['data_postprocessed']['timeseries']['timeseries']))

    # Calculate derived results
    derived_results_timeseries_emissions = get_derived_results_timeseries_emissions(energysystem)
    derived_results_timeseries_emissions.to_csv(os.path.join(dir_postproc,
                                                             cfg['data_postprocessed']['timeseries']['emissions']))
    derived_results_timeseries_costs_variable = get_derived_results_timeseries_costs_variable(energysystem)
    derived_results_timeseries_costs_variable.to_csv(os.path.join(dir_postproc,
                                                                  cfg['data_postprocessed']['timeseries']['cost_variable']))
    derived_results_scalar = get_derived_results_scalar(param_scalar,
                                                        results_scalar,
                                                        results_timeseries_flows,
                                                        derived_results_timeseries_costs_variable,
                                                        derived_results_timeseries_emissions)
    derived_results_scalar.to_csv(os.path.join(dir_postproc,
                                               cfg['data_postprocessed']['scalars']['derived']), header=True)


if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    postprocess(config_path, results_dir)
