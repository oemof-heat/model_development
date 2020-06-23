import os
import yaml

import matplotlib.pyplot as plt
import pandas as pd

from helper import get_experiment_dirs, get_scenario_assumptions, get_config_file
from plotting import map_label_list


idx = pd.IndexSlice

COLOR_DICT = get_config_file('colors.yml')


def add_index(x, name, value):
    x[name] = value
    x.set_index(name, append=True, inplace=True)
    return x


def get_scenario_paths(scenario_assumptions):
    scenario_paths = {}

    for scenario in scenario_assumptions['name']:
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


def plot_stacked_bar(df, slicing, scenario_order, title=None):
    select = df.loc[slicing, :]
    select.index = select.index.droplevel([2, 3, 4])

    select = select.unstack(level=[1, 2])

    select = select.loc[scenario_order]

    colors = [COLOR_DICT[i] for i in select.columns.get_level_values('name')]

    fig, ax = plt.subplots()
    select.plot.bar(ax=ax, color=colors, stacked=True)
    ax.set_title(title)

    handles, labels = plt.gca().get_legend_handles_labels()

    handles, labels = map_label_list(handles, select.columns.get_level_values('name'))

    ax.legend(
        handles=handles,
        labels=labels,
        loc='center left',
        bbox_to_anchor=(1.0, 0.5)
    )
    plt.tight_layout()


def plot_var_cost_assumptions(df, scenarios, title=None):
    # colors = [COLOR_DICT[i] for i in df.columns.get_level_values('name')]

    def get_multi(c):
        carrier = str(c).split('_')[-1]
        var_name = '_'.join(str(c).split('_')[:-1])

        return (carrier, var_name)

    select = df.copy()

    select.index = select['name']

    select = select.loc[select['name'].isin(scenarios)]

    select = select[
        ['charges_tax_levies_gas', 'market_price_gas', 'charges_tax_levies_el', 'market_price_el']
    ]

    select.columns = pd.MultiIndex.from_tuples([get_multi(c) for c in select.columns])

    select = select.stack(0)

    select = select[select.columns[::-1]]

    fig, ax = plt.subplots()

    select.plot.bar(ax=ax, stacked=True)
    ax.set_title(title)

    ax.legend(
        loc='center left',
        bbox_to_anchor=(1.0, 0.5)
    )
    plt.tight_layout()


def main(scenario_assumptions):
    print("Combining scenario results")

    dirs = get_experiment_dirs('all_scenarios')

    scenario_paths = get_scenario_paths(scenario_assumptions)

    scenario_dfs = get_scenario_dfs(scenario_paths, 'scalars.csv')

    all_scalars = combine_scalars(scenario_dfs)

    file_path = os.path.join(dirs['postprocessed'], 'scalars.csv')
    all_scalars.to_csv(file_path)
    print(f"Saved scenario results to {file_path}")

    all_scalars.drop('heat-distribution', level='name', inplace=True)
    all_scalars.drop('heat-demand', level='name', inplace=True)
    all_scalars.drop('heat_decentral-shortage', level='name', inplace=True)

    # define the order of scenarios
    scenario_order = [
        'status_quo',
        'flexfriendly',
        'flexfriendly_taxlevies=80',
        'flexfriendly_taxlevies=77.5',
        'flexfriendly_taxlevies=75',
        'flexfriendly_taxlevies=70',
        'flexfriendly_taxlevies=60',
    ]

    slicing = idx[scenario_paths.keys(), :, :, :, :, ['capacity', 'invest']]
    plot_stacked_bar(all_scalars, slicing, scenario_order, 'Existing and newly built capacity')
    plt.savefig(os.path.join(dirs['plots'], 'capacities.pdf'))

    slicing = idx[scenario_paths.keys(), :, :, :, :, 'yearly_heat']
    plot_stacked_bar(all_scalars, slicing, scenario_order, 'Yearly heat')
    plt.savefig(os.path.join(dirs['plots'], 'yearly_heat.pdf'))

    slicing = idx[scenario_paths.keys(), :, :, :, :, ['capacity_cost', 'carrier_cost']]
    plot_stacked_bar(all_scalars, slicing, scenario_order, 'Costs')
    plt.savefig(os.path.join(dirs['plots'], 'costs.pdf'))

    plot_var_cost_assumptions(scenario_assumptions, scenario_order)
    plt.savefig(os.path.join(dirs['plots'], 'cost_assumptions.pdf'))


if __name__ == '__main__':
    scenario_assumptions = get_scenario_assumptions()
    main(scenario_assumptions)
