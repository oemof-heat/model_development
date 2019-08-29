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
import numpy as np

import oemof.solph as solph
import oemof.outputlib as outputlib
from oemof.tools import economics
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


def get_derived_results_timeseries_costs_variable(energysystem):  # TODO: Check
    param_scalar = get_param_scalar(energysystem)
    flows = get_results_flows(energysystem)
    cost_variable = param_scalar.loc[(param_scalar['var_name']=='variable_costs')]
    cost_variable.loc[:, 'var_value'] = pd.to_numeric(cost_variable.loc[:, 'var_value'])
    cost_variable = cost_variable.loc[cost_variable['var_value']>0]
    cost_variable.index = cost_variable.index.remove_unused_levels()
    flows_with_cost_variable = flows[[(*ll, 'flow') for ll in cost_variable.index]]
    flows_with_cost_variable.columns = flows_with_cost_variable.columns.remove_unused_levels()
    def func(x):
        factor = cost_variable.loc[x.name[:2]]['var_value']
        return x*factor
    timeseries_cost_variable = flows_with_cost_variable.apply(func, axis=0)
    timeseries_cost_variable.columns = timeseries_cost_variable.columns.set_levels(['cost_variable'], level=2)
    return timeseries_cost_variable


def get_derived_results_scalar(input_parameter,
                               param_scalar,
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
    def map_keys(df):
        data = df.copy()
        keys = [key for key in param_scalar.index.unique()]
        key_mapping = {}
        for key in keys:
            if bool(re.search('bus', key[0])):
                if key[1]=='None':
                    key_mapping[key] = key[0]
                else:
                    key_mapping[key] = key[1]
            else:
                key_mapping[key] = key[0]
        data = data.reset_index(level=[0, 1, 2])
        data['component'] = data.apply(lambda x: key_mapping[(x['level_0'], x['level_1'])], axis=1)
        data = data.set_index(['component', 'variable_name'])
        data = data.drop(columns=['level_0', 'level_1'])
        return data

    def format_results(data, var_name, var_unit):
        data.index = data.index.\
            remove_unused_levels().\
            set_levels([var_name], level=2)
        data = pd.DataFrame(data, columns=['var_value'])
        data['var_unit'] = var_unit
        data = map_keys(data)
        return data

    # Production
    producers_heat = [component for component in results_timeseries_flows.columns
                      if bool(re.search('bus_th', component[1]))
                      and not bool(re.search('tes', component[0]))
                      and not bool(re.search('pipe', component[0]))]

    energy_thermal_produced_sum = results_timeseries_flows[producers_heat].sum()
    energy_thermal_produced_sum = format_results(energy_thermal_produced_sum,
                                                 'energy_thermal_produced_sum',
                                                 'MWh')

    power_thermal_max = results_timeseries_flows[producers_heat].max()
    power_thermal_max = format_results(power_thermal_max,
                                       'power_thermal_max',
                                       'MW')

    power_thermal_min = results_timeseries_flows[producers_heat].min()
    power_thermal_min = format_results(power_thermal_min,
                                       'power_thermal_min',
                                       'MW')

    operating = (results_timeseries_flows[producers_heat] > 0)
    operating.columns = operating.columns\
        .remove_unused_levels()\
        .set_levels(['status_operating'], level=2)

    power_thermal_during_operation_mean = results_timeseries_flows[producers_heat][operating].mean()
    power_thermal_during_operation_mean = format_results(power_thermal_during_operation_mean,
                                                         'power_thermal_during_operation_mean',
                                                         'MW')

    hours_operating_sum = operating.sum()
    hours_operating_sum = format_results(hours_operating_sum,
                                         'hours_operating_sum',
                                         'h')

    number_starts = (operating[:-1].reset_index(drop=True) < operating[1:].reset_index(drop=True)).sum()
    number_starts = format_results(number_starts,
                                   'number_starts',
                                   '')

    installed_production_capacity = param_scalar.loc[[key[:2] for key in producers_heat]]
    installed_production_capacity = installed_production_capacity.\
        loc[installed_production_capacity['var_name']=='nominal_value']
    installed_production_capacity = pd.DataFrame(installed_production_capacity).drop(columns=['var_name'])
    installed_production_capacity['variable_name'] = 'installed_production_capacity'
    installed_production_capacity.set_index('variable_name', append=True, inplace=True)
    installed_production_capacity.index = installed_production_capacity.index.droplevel(1)
    installed_production_capacity['var_unit'] = 'MW'

    hours_full_load = energy_thermal_produced_sum['var_value'].reset_index(level=1, drop=True)\
        * 1/installed_production_capacity['var_value'].reset_index(level=[1], drop=True)
    hours_full_load = pd.DataFrame(hours_full_load, columns=['var_value'])
    hours_full_load['variable_name'] = 'hours_full_load'
    hours_full_load['var_unit'] = 'h'
    hours_full_load.set_index('variable_name', append=True, inplace=True)

    # Storage operation
    storage_discharge = [component for component in results_timeseries_flows.columns
                         if component[1]!='None'
                         and bool(re.search('tes', component[0]))]
    energy_heat_storage_discharge_sum = results_timeseries_flows[storage_discharge].sum()
    energy_heat_storage_discharge_sum = format_results(energy_heat_storage_discharge_sum,
                                                       'energy_heat_storage_discharge_sum',
                                                       'MW')
    # TODO: number_storage_cycles = 0 # equivalent full cycles?

    # Heat pump operation
    # TODO: seasonal_performance_factor_heat_pumps_mean = 0 # heat produced / electricity consumed

    # DHN operation
    pipes = [component[0] for component in results_timeseries_flows.columns
             if bool(re.search('_pipe', component[0]))]
    energy_losses_heat_dhn = results_timeseries_flows.loc[:, (slice(None), pipes, slice(None))].sum(axis=1)\
        - results_timeseries_flows.loc[:, (pipes, slice(None), slice(None))].sum(axis=1)
    energy_losses_heat_dhn_sum = pd.DataFrame({'var_value': energy_losses_heat_dhn.sum(), 'var_unit': 'MWh'},
                                              index=pd.MultiIndex.from_tuples([('dhn', 'None', 'energy_losses_heat_dhn_sum')],
                                              names=[None,None,'variable_name']))

    # TODO: energy_consumed_pump_sum = 0

    # Whole system energy
    energy_consumed_gas_sum = results_timeseries_flows.loc[:, ('bus_gas', slice(None), slice(None))].sum()
    energy_consumed_gas_sum = format_results(energy_consumed_gas_sum,
                                             'energy_consumed_sum',
                                             'MWh')

    energy_consumed_electricity_sum = results_timeseries_flows.loc[:, ('bus_el_import', slice(None), slice(None))].sum()
    energy_consumed_electricity_sum = format_results(energy_consumed_electricity_sum,
                                                     'energy_consumed_sum',
                                                     'MWh')

    # TODO: fraction_renewable_energy_thermal = 0 # renewable energy / total energy consumed

    # Costs
    cost_variable_sum = derived_results_timeseries_costs_variable.sum()
    cost_variable_sum = format_results(cost_variable_sum,
                                       'cost_variable_sum',
                                       'Eur')

    cost_fix = input_parameter.loc[slice(None), ['capacity_installed', 'overnight_cost', 'lifetime', 'fom'], :]
    cost_fix = cost_fix.unstack(1)
    cost_fix.loc[[key for key in cost_fix.index if bool(re.search('subnet-._tes', key))],
                 ['fom', 'lifetime', 'overnight_cost']] = cost_fix.loc['tes_decentral',
                                                                      ['fom', 'lifetime', 'overnight_cost']].values
    cost_fix.loc[[key for key in cost_fix.index if bool(re.search('subnet-._heat_pump', key))],
                 ['fom', 'lifetime', 'overnight_cost']] = cost_fix.loc['pth_heat_pump_decentral',
                                                                      ['fom', 'lifetime', 'overnight_cost']].values
    cost_fix.loc[[key for key in cost_fix.index if bool(re.search('subnet-._pth', key))],
                 ['fom', 'lifetime', 'overnight_cost']] = cost_fix.loc['pth_resistive_decentral',
                                                                      ['fom', 'lifetime', 'overnight_cost']].values
    cost_fix = cost_fix.drop(['pth_heat_pump_decentral', 'pth_resistive_decentral'])

    wacc = 0.03  # TODO get from input parameter
    cost_fix['annuity'] = cost_fix.apply(lambda x: economics.annuity(x['overnight_cost'], x['lifetime'], wacc), axis=1)
    cost_fix['capex'] = cost_fix.apply(lambda x: x['capacity_installed'] * x['annuity'],axis=1)
    cost_fix['fom_abs'] = cost_fix.apply(lambda x: x['capacity_installed'] * x['fom'],axis=1)
    cost_fix = cost_fix.loc[:, ['capex','fom_abs'] ].stack()
    cost_fix = pd.DataFrame(cost_fix, columns=['var_value'])
    cost_fix.index.names = ['component', 'variable_name']
    cost_fix['var_unit'] = 'Eur'

    cost_total_system = pd.concat([cost_variable_sum, cost_fix], axis=0).groupby('component').agg(sum)
    cost_total_system = cost_total_system.reset_index()
    cost_total_system['var_name'] = 'cost_total_system'
    cost_total_system = cost_total_system.set_index(['component', 'var_name'])

    cost_specific_heat_mean = 0  # TODO: Durchschnittliche Waermegestehungskosten

    # Emissions
    emissions_sum = derived_results_timeseries_emissions.sum()
    emissions_sum = format_results(emissions_sum,
                                   'emissions_sum',
                                   'tCO2')

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
                                        cost_fix,
                                        energy_heat_storage_discharge_sum,
                                        energy_losses_heat_dhn_sum,
                                        cost_total_system,
                                        emissions_sum], sort=True)
    derived_results_scalar.index.rename('var_name',
                                        'variable_name',
                                        inplace=True)

    def aggregate_decentral(derived_results_scalar):
        keys_decentral = [key[0] for key in derived_results_scalar.index
                          if bool(re.search('subnet-.', key[0]))]
        results_decentral = derived_results_scalar.loc[(keys_decentral, slice(None)), :]
        regex = re.compile(r"subnet-._")
        remove_subnet = lambda str: re.sub(regex, '', str)
        results_decentral = results_decentral.rename(index={key: remove_subnet(key) for key in keys_decentral})

        def func(x):
            to_sum = ['energy_heat_storage_discharge_sum',
                      'energy_consumed_sum',
                      'energy_thermal_produced_sum',
                      'energy_thermal_produced_sum',
                      'installed_production_capacity',
                      'cost_total_system',
                      'cost_variable_sum']
            if x.index[0][1] in to_sum:
                return sum(x)
            else:
                return np.mean(x)

        aggregated_decentral = results_decentral.groupby(['component', 'var_name']).agg(func)
        results_central = derived_results_scalar.drop(keys_decentral, level=0)
        aggregated_results = pd.concat([aggregated_decentral,
                                        results_central],
                                        axis=0, sort=True).sort_index()
        return aggregated_results

    aggregated_results = aggregate_decentral(derived_results_scalar)
    return aggregated_results


def postprocess(config_path, results_dir):
    r'''
    Runs the whole postprocessing pipeline and saves the results.
    '''
    # open config
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # load model_runs
    model_runs = helpers.load_model_runs(results_dir, cfg)
    for index, input_parameter in model_runs.iterrows():
        label = "_".join(map(str, index))

        # restore energysystem
        energysystem = solph.EnergySystem()
        energysystem.restore(dpath=results_dir + '/optimisation_results', filename=f'{label}_es.dump')
        dir_postproc = os.path.join(results_dir, 'data_postprocessed', label)
        if not os.path.exists(dir_postproc):
            os.makedirs(os.path.join(dir_postproc, 'timeseries'))

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
        derived_results_scalar = get_derived_results_scalar(input_parameter,
                                                            param_scalar,
                                                            results_scalar,
                                                            results_timeseries_flows,
                                                            derived_results_timeseries_costs_variable,
                                                            derived_results_timeseries_emissions)
        derived_results_scalar = helpers.prepend_index(derived_results_scalar,
                                                       index,
                                                       ['run_id', 'scenario', 'uncert_sample_id'])
        derived_results_scalar.to_csv(os.path.join(dir_postproc,
                                                   cfg['data_postprocessed']['scalars']['derived']), header=True)


if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    postprocess(config_path, results_dir)
