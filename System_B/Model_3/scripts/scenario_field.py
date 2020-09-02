import os
import yaml

import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np
import pandas as pd

from helper import get_experiment_dirs, get_scenario_assumptions, get_config_file


idx = pd.IndexSlice


def get_scenario_paths(scenario_assumptions):
    scenario_paths = {}

    for scenario in scenario_assumptions['scenario']:
        path = get_experiment_dirs(scenario)['postprocessed']

        scenario_paths.update({scenario: path})

    return scenario_paths


def get_scenario_dfs(scenario_paths, file_name):
    scenario_df = {}

    for scenario, path in scenario_paths.items():
        file_path = os.path.join(path, file_name)

        df = pd.read_csv(file_path)

        scenario_df.update({scenario: df})

    return scenario_df


def combine_scalars(scenario_dfs):
    for scenario, df in scenario_dfs.items():
        df.insert(0, 'scenario', scenario)

    all_scalars = pd.concat(scenario_dfs.values(), 0)

    all_scalars.set_index(
        ['scenario', 'name', 'type', 'carrier', 'tech', 'var_name'],
        inplace=True
    )

    return all_scalars


def plot_scenario_field(scalars, scenario_assumptions):
    n = 4
    m = 6

    scalars_and_assumptions = scalars.reset_index().merge(scenario_assumptions, on="scenario")

    var_value = scalars_and_assumptions.loc[
        (scalars_and_assumptions['name'] == 'electricity-hp') &
        (scalars_and_assumptions['var_name'] == 'invest')
    ]
    print(scalars_and_assumptions)
    var_value['ratio'] = var_value['charges_tax_levies_gas'] / var_value['charges_tax_levies_el']

    var_value = var_value[['ratio', 'standard_dev_el', 'charges_tax_levies_gas', 'charges_tax_levies_el', 'var_value']]

    var_value = var_value.set_index(['ratio', 'standard_dev_el'])

    print(var_value)

    fig, ax = plt.subplots()

    image = ax.imshow(
        np.array(var_value['var_value']).reshape(n, m)[::-1,:],
        cmap='Blues'
    )

    labels = var_value.index

    xticklabels = [round(l[0]*100) for l in labels[0:n + 2]]

    yticklabels = [l[1] for l in labels[0::m]]

    print(len(xticklabels), yticklabels)

    ax.set_xticks(np.arange(len(xticklabels)))

    ax.set_yticks(np.arange(len(yticklabels)))

    ax.set_xticklabels(xticklabels)

    ax.set_yticklabels(yticklabels[::-1])

    ax.set_title('Investment in heat pump capacity [MW_th]')

    ax.set_xlabel('Taxes, charges and levies ratio gas/electricity [%]')

    ax.set_ylabel('Standard deviation of electricity prices')

    # colorbar_ax = fig.add_axes([0.7, 0.1, 0.05, 0.8])
    fig.colorbar(image)


def main(scenario_assumptions):
    print("Combining scenario results")

    dirs = get_experiment_dirs('all_scenario_field')

    scenario_paths = get_scenario_paths(scenario_assumptions)

    scenario_dfs = get_scenario_dfs(scenario_paths, 'scalars.csv')

    all_scalars = combine_scalars(scenario_dfs)

    file_path = os.path.join(dirs['postprocessed'], 'scalars.csv')

    all_scalars.to_csv(file_path)

    print(f"Saved scenario results to {file_path}")

    plot_scenario_field(all_scalars, scenario_assumptions)

    plt.savefig(os.path.join(dirs['plots'], 'scenario_field.pdf'))


if __name__ == '__main__':
    scenario_assumptions = get_scenario_assumptions()

    scenario_assumptions = scenario_assumptions.loc[
        scenario_assumptions['scenario'].str.contains('scenario_field')
    ]

    main(scenario_assumptions)
