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
    def func(x):
        factor = emission_specific.loc[emission_specific['component']==x.name[:2]]['var_value'].squeeze()
        return x*factor
    timeseries_emission_specific = flows_with_emission_specific.apply(func, axis=0)
    return timeseries_emission_specific


def get_derived_results_timeseries_costs_variable(energysystem):
    param_scalar = get_param_scalar(energysystem)
    flows = get_results_flows(energysystem)

    cost_variable = param_scalar.loc[param_scalar['var_name']=='variable_costs']
    flows_with_cost_variable = flows[[(*component, 'flow') for component in cost_variable['component']]]
    def func(x):
        factor = cost_variable.loc[cost_variable['component']==x.name[:2]]['var_value'].squeeze()
        return x*factor
    timeseries_cost_variable = flows_with_cost_variable.apply(func, axis=0)
    return timeseries_cost_variable


def get_derived_results_scalar(energysystem):
    return pd.DataFrame()


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
    results_flows = get_results_flows(energysystem)
    results_flows.to_csv(os.path.join(dir_postproc, 'timeseries/results_flows.csv'))

    # Calculate derived results
    get_derived_results_timeseries_emissions(energysystem)\
        .to_csv(os.path.join(dir_postproc,
                             'timeseries/' +
                              'results_timeseries_emissions_variable.csv'))
    get_derived_results_timeseries_costs_variable(energysystem)\
        .to_csv(os.path.join(dir_postproc,
                             'timeseries/' +
                             'results_timeseries_costs_variable.csv'))
    get_derived_results_scalar(energysystem)\
        .to_csv(os.path.join(dir_postproc,
                             'results_scalar_derived.csv'))


if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    postprocess(config_path, results_dir)
