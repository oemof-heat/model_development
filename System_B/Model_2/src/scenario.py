import pandas as pd
import os
import yaml
import numpy as np
from SALib.sample import latin
import helpers


def get_uncertain_parameters(scenario, input_parameter):
    uncertain_parameters = input_parameter.loc[(scenario,
                                                ['high', 'low'],
                                                slice(None),
                                                slice(None)), :]
    return uncertain_parameters


def get_certain_parameters(scenario, input_parameter):
    certain_parameters = input_parameter.loc[(scenario,
                                             'deterministic',
                                             slice(None),
                                             slice(None)), :]
    return certain_parameters


def get_samples(scenario, certain_parameters, uncertain_parameters, n_samples):
    bounds = uncertain_parameters.loc[scenario, 'var_value'].\
        unstack([2, 0]).values
    n_variables = len(uncertain_parameters) // 2
    problem = {
        'num_vars': n_variables,
        'names': uncertain_parameters.index,
        'bounds': bounds
    }
    samples = latin.sample(problem, n_samples)

    named_samples = []
    for uncert_sample_id in range(n_samples):
        configuration = samples[uncert_sample_id]  # TODO
        named_sample = [scenario, uncert_sample_id, *configuration]
        named_samples.append(named_sample)
    named_samples = pd.DataFrame(named_samples)
    named_samples = named_samples.reset_index().set_index(['index', 0, 1])
    named_samples.index.names = ['run_id', 'scenario', 'uncert_sample_id']
    named_samples.columns = uncertain_parameters.index.\
        droplevel([0, 1]).\
        unique().\
        set_names([None, None])
    return named_samples


def get_deterministic_run(scenario, input_parameters):
    df = input_parameters.loc[(scenario,
                               ['reference', 'deterministic'],
                               slice(None),
                               slice(None))]
    df.index = df.index.droplevel(1)
    df = df['var_value'].unstack(level=[1, 2])
    df.columns.names = ([None, None])
    df = df.reset_index(drop=True)
    df.index = pd.MultiIndex.from_tuples([(0, scenario, 0)],
                                         names=['run_id', 'scenario', 'uncert_sample_id'])
    return df


def create_list_model_runs(config_path, results_dir):
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    filename_input_parameter = os.path.join(abs_path, cfg['data_raw']['scalars']['parameters'])
    input_parameter = helpers.load_input_parameter(filename_input_parameter)

    file_timeseries_price_electricity = os.path.join(results_dir,
                                                     'data_preprocessed',
                                                     cfg['data_preprocessed']['timeseries']['price_electricity_spot'])
    price_electricity = pd.read_csv(file_timeseries_price_electricity, index_col=0)['price_electricity_spot'].values

    # scenarios = input_parameter.index.get_level_values('scenario').unique()
    # filename_scenarios = os.path.join(abs_path, cfg['data_raw']['scenarios'])
    # scenarios = pd.read_csv(filename_scenarios)['name']
    scenarios = ['scenario_basic']
    model_runs = pd.DataFrame()
    for scenario in scenarios:
        if cfg['uncertainty_sampling']:
            uncertain_parameters = get_uncertain_parameters(scenario, input_parameter)
            certain_parameters = get_certain_parameters(scenario, input_parameter)
            n_samples = 3  # TODO
            samples = get_samples(scenario, certain_parameters, uncertain_parameters, n_samples)
            model_runs = model_runs.append(samples)
        else:
            deterministic_run = get_deterministic_run(scenario, input_parameter)
            model_runs = model_runs.append(deterministic_run)
    #  TODO: Correct run_id
    model_runs.to_csv(os.path.join(results_dir,
                                   'data_preprocessed',
                                   cfg['data_preprocessed']
                                      ['scalars']
                                      ['model_runs']))


if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    create_list_model_runs(config_path, results_dir)
