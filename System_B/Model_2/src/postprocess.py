"""
This script runs the postprocessing.

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

idx = pd.IndexSlice


def get_param_scalar(energysystem):
    r"""
    Get all scalar input parameters to the model as DataFrame.

    Parameters
    ----------
    energysystem : oemof.solph.EnergySystem
        EnergySystem as stored after optimization in src/model.py

    Returns
    -------
    param_scalars : pd.DataFrame
        DataFrame containing all scalar input parameters.
    """
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


def get_price_electricity(energysystem):
    r"""
    Get input timeseries to the model of electricity prices.

    Parameters
    ----------
    energysystem : oemof.solph.EnergySystem
        EnergySystem as stored after optimization in src/model.py

    Returns
    -------
    price_electricity : pd.DataFrame
        DataFrame containing input timeseries of electricity prices.
    """
    param = energysystem.results['param']
    param = outputlib.processing.convert_keys_to_strings(param)
    timeseries = {k: v['sequences'].reset_index(drop=True) for k, v in param.items() if not v['sequences'].empty}
    param_timeseries = pd.concat(timeseries, axis=1)
    price_electricity = param_timeseries.loc[:, (['bus_el_export', 'source_electricity', 'source_electricity_flex'],
                                                  slice(None),
                                                  slice(None))]

    return price_electricity


def get_results_scalar(energysystem):
    r"""
    Get all scalar results of the model as DataFrame.

    Parameters
    ----------
    energysystem : oemof.solph.EnergySystem
        EnergySystem as stored after optimization in src/model.py

    Returns
    -------
    results_scalar : pd.DataFrame
        DataFrame containing all scalar results.
    """
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


def get_results_timeseries(energysystem):
    r"""
    Get all timeseries results of the model as DataFrame.

    Parameters
    ----------
    energysystem : oemof.solph.EnergySystem
        EnergySystem as stored after optimization in src/model.py

    Returns
    -------
    results_scalar : pd.DataFrame
        DataFrame containing all timeseries results.
    """
    results = energysystem.results['main']
    results = outputlib.processing.convert_keys_to_strings(results)
    timeseries = {k: v['sequences'] for k, v in results.items()}
    timeseries = pd.concat(timeseries, axis=1)

    return timeseries


def get_derived_results_timeseries_emissions(energysystem):
    r"""
    Get resulting emission timeseries as DataFrame.

    Parameters
    ----------
    energysystem : oemof.solph.EnergySystem
        EnergySystem as stored after optimization in src/model.py

    Returns
    -------
    timeseries_emission : pd.DataFrame
        DataFrame containing resulting emission timeseries.
    """
    param_scalar = get_param_scalar(energysystem)
    timeseries = get_results_timeseries(energysystem)
    emission_specific = param_scalar.loc[param_scalar['var_name']=='emission_specific']
    flows_with_emission_specific = timeseries[[(*ll, 'flow') for ll in emission_specific.index]]
    flows_with_emission_specific.columns = flows_with_emission_specific.columns.remove_unused_levels()

    def func(x):
        factor = emission_specific.loc[x.name[:2]]['var_value']
        return x*factor

    timeseries_emission = flows_with_emission_specific.apply(func, axis=0)
    timeseries_emission.columns = timeseries_emission.columns.set_levels(['emission'], level=2)

    return timeseries_emission


def get_derived_results_timeseries_costs_variable(energysystem):  # TODO: Check
    r"""
    Get resulting emission timeseries as DataFrame.

    Parameters
    ----------
    energysystem : oemof.solph.EnergySystem
        EnergySystem as stored after optimization in src/model.py

    Returns
    -------
    timeseries_cost_variable : pd.DataFrame
        DataFrame containing resulting variable cost timeseries.
    """
    param = energysystem.results['param']
    param = outputlib.processing.convert_keys_to_strings(param)

    timeseries = get_results_timeseries(energysystem)

    variable_costs = {key: value[k]['variable_costs']
                      for key, value in param.items()
                      for k in ['scalars', 'sequences']
                      if 'variable_costs' in value[k]
                      and np.sum(value[k]['variable_costs'])!=0}

    def reallocate_variable_costs(variable_costs, flows, bus):
        costs_bus_inflow = {key: value for key, value in variable_costs.items() if key[1] == bus}

        bus_inflows_with_costs = flows[[(*ll, 'flow') for ll in costs_bus_inflow.keys()]]

        bus_outflows = flows[[key for key in flows.keys() if key[0] == bus]]

        # calculate average cost at the bus
        cost_bus = pd.DataFrame()
        for column in bus_inflows_with_costs.columns:
            var_cost = variable_costs[column[:2]]
            if type(var_cost) == pd.Series:
                var_cost = var_cost.values
            cost_bus[column[:2]] = bus_inflows_with_costs.loc[:, column] * var_cost
        cost_bus = cost_bus.sum(axis=1) / bus_inflows_with_costs.sum(axis=1)
        cost_bus = cost_bus.fillna(0)

        variable_costs_reallocated = {k: v for k, v in variable_costs.items() if k not in costs_bus_inflow.keys()}
        for column in bus_outflows.columns:
            variable_costs_reallocated[column[:2]] += cost_bus

        return variable_costs_reallocated

    variable_costs_reallocated = reallocate_variable_costs(variable_costs, timeseries, 'bus_el_import')
    variable_costs_reallocated = reallocate_variable_costs(variable_costs_reallocated, timeseries, 'bus_gas')
    flows_with_variable_costs = timeseries[[(*ll, 'flow') for ll in variable_costs_reallocated.keys()]]
    flows_with_variable_costs.columns = flows_with_variable_costs.columns.remove_unused_levels()

    timeseries_cost_variable = flows_with_variable_costs.copy()

    for column in flows_with_variable_costs.columns:
        var_cost = variable_costs_reallocated[column[:2]]
        if type(var_cost) == pd.Series:
            var_cost = var_cost.values
        timeseries_cost_variable.loc[:, column] *= var_cost

    timeseries_cost_variable.columns = timeseries_cost_variable.columns.set_levels(['cost_variable'], level=2)

    return timeseries_cost_variable


def get_derived_results_scalar(input_parameter,
                               param_scalar,
                               results_scalar,
                               results_timeseries,
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

    def get_producers_heat(results_timeseries):
        producers_heat = [component for component in results_timeseries.columns
                          if bool(re.search('bus_th', component[1]))
                          and not bool(re.search('behind', component[1]))
                          and not bool(re.search('tes', component[0]))
                          and not bool(re.search('pipe', component[0]))]

        return producers_heat

    def get_energy_thermal_produced_sum(results_timeseries):
        producers_heat = get_producers_heat(results_timeseries)
        energy_thermal_produced_sum = results_timeseries[producers_heat].sum()
        energy_thermal_produced_sum = format_results(energy_thermal_produced_sum,
                                                     'energy_thermal_produced_sum',
                                                     'MWh')

        return energy_thermal_produced_sum

    def get_energy_electricity_produced_sum(results_timeseries):
        producers_electricity = [component for component in results_timeseries.columns
                                 if bool(re.search('bus_el_export', component[1]))]
        energy_electricity_produced_sum = results_timeseries[producers_electricity].sum()
        energy_electricity_produced_sum = format_results(energy_electricity_produced_sum,
                                                        'energy_electricity_produced_sum',
                                                        'MWh')

        return energy_electricity_produced_sum

    def get_power_thermal_max_min(results_timeseries):
        producers_heat = get_producers_heat(results_timeseries)
        power_thermal_max = results_timeseries[producers_heat].max()
        power_thermal_max = format_results(power_thermal_max,
                                           'power_thermal_max',
                                           'MW')

        power_thermal_min = results_timeseries[producers_heat].min()
        power_thermal_min = format_results(power_thermal_min,
                                           'power_thermal_min',
                                           'MW')

        return power_thermal_max, power_thermal_min

    def get_operating(results_timeseries):
        producers_heat = get_producers_heat(results_timeseries)
        operating = (results_timeseries[producers_heat] > 0)
        operating.columns = operating.columns\
            .remove_unused_levels()\
            .set_levels(['status_operating'], level=2)

        return operating

    def get_power_thermal_during_operation_mean(results_timeseries):
        producers_heat = get_producers_heat(results_timeseries)
        power_thermal_during_operation_mean = results_timeseries[producers_heat][operating].mean()
        power_thermal_during_operation_mean = format_results(power_thermal_during_operation_mean,
                                                             'power_thermal_during_operation_mean',
                                                             'MW')
        return power_thermal_during_operation_mean

    def get_hours_operating_sum(operating):
        hours_operating_sum = operating.sum()
        hours_operating_sum = format_results(hours_operating_sum,
                                             'hours_operating_sum',
                                             'h')
        return hours_operating_sum

    def get_number_starts(operating):
        number_starts = (operating[:-1].reset_index(drop=True) < operating[1:].reset_index(drop=True)).sum()
        number_starts = format_results(number_starts,
                                       'number_starts',
                                       '')
        return number_starts

    def get_installed_production_capacity(param_scalar):
        installed_production_capacity = param_scalar.loc[[key[:2] for key in producers_heat]]
        installed_production_capacity = installed_production_capacity.\
            loc[installed_production_capacity['var_name']=='nominal_value']
        installed_production_capacity = pd.DataFrame(installed_production_capacity).drop(columns=['var_name'])
        installed_production_capacity['variable_name'] = 'installed_production_capacity'
        installed_production_capacity.set_index('variable_name', append=True, inplace=True)
        installed_production_capacity.index = installed_production_capacity.index.droplevel(1)
        installed_production_capacity['var_unit'] = 'MW'

        return installed_production_capacity

    def get_hours_full_load(energy_thermal_produced_sum):
        hours_full_load = energy_thermal_produced_sum['var_value'].reset_index(level=1, drop=True)\
            * 1/installed_production_capacity['var_value'].reset_index(level=[1], drop=True)
        hours_full_load = pd.DataFrame(hours_full_load, columns=['var_value'])
        hours_full_load['variable_name'] = 'hours_full_load'
        hours_full_load['var_unit'] = 'h'
        hours_full_load.set_index('variable_name', append=True, inplace=True)

        return hours_full_load

    def get_storage_discharge_sum(results_timeseries):
        storage_discharge = [component for component in results_timeseries.columns
                             if component[1] !='None'
                             and bool(re.search('tes', component[0]))]
        energy_heat_storage_discharge_sum = results_timeseries[storage_discharge].sum()
        energy_heat_storage_discharge_sum = format_results(energy_heat_storage_discharge_sum,
                                                           'energy_heat_storage_discharge_sum',
                                                           'MW')
        return energy_heat_storage_discharge_sum

    # TODO: number_storage_cycles = 0 # equivalent full cycles?
    # TODO: seasonal_performance_factor_heat_pumps_mean = 0 # heat produced / electricity consumed

    def get_energy_losses_heat_dhn_sum(results_timeseries):
        pipes = [component[0] for component in results_timeseries.columns
                 if bool(re.search('_pipe', component[0]))]
        energy_losses_heat_dhn = results_timeseries.loc[:, (slice(None), pipes, slice(None))].sum(axis=1) \
                                 - results_timeseries.loc[:, (pipes, slice(None), slice(None))].sum(axis=1)
        energy_losses_heat_dhn_sum = pd.DataFrame({'var_value': energy_losses_heat_dhn.sum(), 'var_unit': 'MWh'},
                                                  index=pd.MultiIndex.from_tuples([('dhn', 'None', 'energy_losses_heat_dhn_sum')],
                                                  names=[None,None,'variable_name']))
        return energy_losses_heat_dhn_sum

    # TODO: energy_consumed_pump_sum = 0

    def get_energy_consumed(results_timeseries):
        energy_consumed_gas_sum = results_timeseries.loc[:, ('bus_gas', slice(None), slice(None))].sum()
        energy_consumed_gas_sum = format_results(energy_consumed_gas_sum,
                                                 'energy_consumed_sum',
                                                 'MWh')

        energy_consumed_electricity_sum = results_timeseries.loc[:, ('bus_el_import', slice(None), slice(None))].sum()
        energy_consumed_electricity_sum = format_results(energy_consumed_electricity_sum,
                                                         'energy_consumed_sum',
                                                         'MWh')
        return energy_consumed_gas_sum, energy_consumed_electricity_sum

    # TODO: fraction_renewable_energy_thermal = 0 # renewable energy / total energy consumed

    def get_cost_variable_sum(derived_results_timeseries_costs_variable):
        cost_variable_sum = derived_results_timeseries_costs_variable.sum()
        cost_variable_sum = format_results(cost_variable_sum,
                                           'cost_variable_sum',
                                           'Eur')
        cost_variable_sum = cost_variable_sum.groupby(level=[0, 1]).aggregate({'var_value': np.sum,
                                                                               'var_unit': 'first'})
        cost_variable_sum.loc['chp', 'var_value'] = \
            (cost_variable_sum.loc['chp', 'var_value']
            + cost_variable_sum.loc['sold_el', 'var_value'])['cost_variable_sum']
        cost_variable_sum.drop('sold_el', inplace=True)

        return cost_variable_sum

    def get_cost_fix(input_parameter):
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
        cost_fix = cost_fix.drop(['pth_heat_pump_decentral', 'pth_resistive_decentral', 'tes_decentral'])

        wacc = input_parameter.loc['global', 'wacc']
        cost_fix['annuity'] = cost_fix.apply(lambda x: economics.annuity(x['overnight_cost'], x['lifetime'], wacc), axis=1)
        cost_fix['capex'] = cost_fix.apply(lambda x: x['capacity_installed'] * x['annuity'],axis=1)
        cost_fix['fom_abs'] = cost_fix.apply(lambda x: x['capacity_installed'] * x['overnight_cost'] * x['fom'],axis=1)
        cost_fix = cost_fix.loc[:, ['capex','fom_abs'] ].stack()
        cost_fix = pd.DataFrame(cost_fix, columns=['var_value'])
        cost_fix.index.names = ['component', 'variable_name']
        cost_fix['var_unit'] = 'Eur'

        return cost_fix

    def get_cost_total_system(cost_variable_sum, cost_fix):
        cost_total_system = pd.concat([cost_variable_sum, cost_fix], axis=0)  \
            .groupby('component').agg({'var_value': sum,
                                       'var_unit': 'first'})
        cost_total_system = cost_total_system.reset_index()
        cost_total_system['var_name'] = 'cost_total_system'
        cost_total_system = cost_total_system.set_index(['component', 'var_name'])

        return cost_total_system

    def get_cost_specific_heat(results_timeseries, cost_total_system):
        consumers_heat = [component for component in results_timeseries.columns
                          if bool(re.search('demand_th', component[1]))]
        energy_thermal_consumed = results_timeseries[consumers_heat].sum()

        cost_specific_heat = cost_total_system.copy()
        cost_specific_heat['var_value'] *= 1 / energy_thermal_consumed.sum()

        cost_specific_heat['var_unit'] = 'Eur/MWh'

        cost_specific_heat.index.set_levels(['cost_specific_heat'], level='var_name', inplace=True)

        return cost_specific_heat

    def get_emissions_sum(derived_results_timeseries_emissions):
        emissions_sum = derived_results_timeseries_emissions.sum()
        emissions_sum = format_results(emissions_sum,
                                       'emissions_sum',
                                       'tCO2')
        return emissions_sum

    def get_emissions_specific_heat(emissions_sum):
        emissions_heat_sum = emissions_sum.copy()
        emissions_heat_sum.loc[('chp', 'emissions_sum'), 'var_value'] = allocate_emissions(
            emissions_heat_sum.loc[('chp', 'emissions_sum'), 'var_value'],
            eta_el=0.3,
            eta_th=0.5,
            method='iea')[1]

        consumers_heat = [component for component in results_timeseries.columns
                          if bool(re.search('demand_th', component[1]))]

        energy_thermal_consumed = results_timeseries[consumers_heat].sum()

        emissions_specific_heat = emissions_heat_sum.copy()
        emissions_specific_heat['var_value'] = emissions_specific_heat['var_value'] * 1/energy_thermal_consumed.sum()

        emissions_specific_heat.index.set_levels(['emissions_specific_heat'], level='variable_name', inplace=True)
        emissions_specific_heat['var_unit'] = 'tCO2/MW_th'

        return emissions_specific_heat

    def collect_derived_results_scalar(*args):
        derived_results_scalar = pd.concat(args, sort=True)
        derived_results_scalar.index.rename('var_name',
                                            'variable_name',
                                            inplace=True)
        return derived_results_scalar

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

        aggregated_decentral = results_decentral.groupby(['component', 'var_name']).agg({'var_value': func,
                                                                                         'var_unit': 'first'})
        results_central = derived_results_scalar.drop(keys_decentral, level=0)
        aggregated_results = pd.concat([aggregated_decentral,
                                        results_central],
                                        axis=0, sort=True).sort_index()
        return aggregated_results

    energy_thermal_produced_sum = get_energy_thermal_produced_sum(results_timeseries)

    energy_electricity_produced_sum = get_energy_electricity_produced_sum(results_timeseries)

    power_thermal_max, power_thermal_min = get_power_thermal_max_min(results_timeseries)

    operating = get_operating(results_timeseries)

    producers_heat = get_producers_heat(results_timeseries)

    power_thermal_during_operation_mean = get_power_thermal_during_operation_mean(results_timeseries)

    hours_operating_sum = get_hours_operating_sum(operating)

    number_starts = get_number_starts(operating)

    installed_production_capacity = get_installed_production_capacity(param_scalar)

    hours_full_load = get_hours_full_load(energy_thermal_produced_sum)

    energy_heat_storage_discharge_sum = get_storage_discharge_sum(results_timeseries)

    energy_losses_heat_dhn_sum = get_energy_losses_heat_dhn_sum(results_timeseries)

    energy_consumed_gas_sum, energy_consumed_electricity_sum = get_energy_consumed(results_timeseries)

    cost_variable_sum = get_cost_variable_sum(derived_results_timeseries_costs_variable)

    cost_fix = get_cost_fix(input_parameter)

    cost_total_system = get_cost_total_system(cost_variable_sum, cost_fix)

    cost_specific_heat = get_cost_specific_heat(results_timeseries, cost_total_system)

    emissions_sum = get_emissions_sum(derived_results_timeseries_emissions)

    emissions_specific_heat = get_emissions_specific_heat(emissions_sum)

    derived_results_scalar = collect_derived_results_scalar(energy_thermal_produced_sum,
                                                            energy_electricity_produced_sum,
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
                                                            cost_specific_heat,
                                                            emissions_sum,
                                                            emissions_specific_heat)

    aggregated_results = aggregate_decentral(derived_results_scalar)

    return aggregated_results


def allocate_emissions(total_emissions, eta_el, eta_th, method, **kwargs):
    r"""
    Function to allocate emissions caused in cogeneration to the products electrical energy and heat according
    to specified method.

    Reference:

    Mauch, W., Corradini, R., Wiesmeyer, K., Schwentzek, M. (2010).
    Allokationsmethoden für spezifische CO2-Emissionen von Strom und Waerme aus KWK-Anlagen.
    Energiewirtschaftliche Tagesfragen, 55(9), 12–14.

    Parameters
    ----------
    total_emissions : numeric
        Total emissions to be allocated to electricity and heat.

    eta_el : numeric
        Electrical efficiency of the cogeneration.

    eta_th : numeric
        Thermal efficiency of the cogeneration.

    method : str
        Specification of method to use. Choose from ['iea', finnish', 'efficiency'].

    **kwargs
        For the finish method, `eta_el_ref` and `eta_th_ref` have to be passed.

    Returns
    -------
    allocated_emissions_electricity : numeric
        total emissions allocated to electricity according to specified `method`.

    allocated_emissions_heat : numeric
            total emissions allocated to heat according to specified `method`.

    """
    if method is 'iea':
        allocated_emissions_electricity = total_emissions * eta_el * 1/(eta_el + eta_th)
        allocated_emissions_heat = total_emissions * eta_th * 1/(eta_el + eta_th)

    elif method is 'efficiency':
        allocated_emissions_electricity = total_emissions * eta_th * 1/(eta_el + eta_th)
        allocated_emissions_heat = total_emissions * eta_el * 1/(eta_el + eta_th)

    elif method is 'finnish':
        if kwargs is not None and kwargs.keys() >= {'eta_el_ref', 'eta_th_ref'}:
            eta_el_ref = kwargs.get('eta_el_ref')
            eta_th_ref = kwargs.get('eta_th_ref')
        else:
            raise ValueError('Must specify eta_el_ref, eta_th_ref when using finnish method.')

        pee = 1 - 1/((eta_el/eta_el_ref) + (eta_th/eta_th_ref))
        allocated_emissions_electricity = total_emissions * (1 - pee) * (eta_el/eta_el_ref)
        allocated_emissions_heat = total_emissions * (1 - pee) * (eta_th/eta_th_ref)

    else:
        raise ValueError(f"Method '{method}' is not available. " +
                         "Please choose from ['iea', finnish', 'efficiency']")

    return allocated_emissions_electricity, allocated_emissions_heat


def postprocess(config_path, results_dir):
    r"""
    Runs the whole postprocessing pipeline and saves the results.

    """
    # open config
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # load model_runs
    model_runs = helpers.load_model_runs(results_dir, cfg)
    model_runs = model_runs.loc[:, 'var_value']
    list_results_scalar_derived = []
    collect_price_electricity = {}

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
        results_timeseries = get_results_timeseries(energysystem)
        results_timeseries.to_csv(os.path.join(dir_postproc, cfg['data_postprocessed']['timeseries']['timeseries']))

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
                                                            results_timeseries,
                                                            derived_results_timeseries_costs_variable,
                                                            derived_results_timeseries_emissions)
        derived_results_scalar = helpers.prepend_index(derived_results_scalar,
                                                       index,
                                                       ['run_id', 'scenario', 'uncert_sample_id'])
        derived_results_scalar.to_csv(os.path.join(dir_postproc,
                                                   cfg['data_postprocessed']['scalars']['derived']), header=True)
        list_results_scalar_derived.append(derived_results_scalar)
        price_electricity = get_price_electricity(energysystem)
        collect_price_electricity[label] = price_electricity

    price_electricity_all = pd.concat(collect_price_electricity, axis=1)
    price_electricity_all.to_csv(os.path.join(results_dir,
                                              'data_postprocessed',
                                              'price_electricity_all.csv'))
    results_scalar_derived_all = pd.concat(list_results_scalar_derived)
    results_scalar_derived_all.to_csv(os.path.join(results_dir,
                                                   'data_postprocessed',
                                                   'results_scalar_derived_all.csv'))


if __name__ == '__main__':
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'experiment_configs/production_run.yml')
    config_path = os.path.abspath(config_path)

    config_path, results_dir = helpers.setup_experiment(config_path=config_path)
    postprocess(config_path, results_dir)
