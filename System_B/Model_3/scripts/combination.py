import os
import yaml

import matplotlib.pyplot as plt
from matplotlib import rcParams
import pandas as pd

from helper import get_experiment_dirs, get_scenario_assumptions, get_config_file
from plotting import map_handles_labels, map_names_to_labels


idx = pd.IndexSlice

COLOR_DICT = get_config_file('colors.yml')

LABELS = get_config_file('labels.yml')

COLORS_BY_LABEL = {LABELS[key]: value for key, value in COLOR_DICT.items()}

rcParams['font.size'] = 16


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


def plot_stacked_bar(df, scenario_order, title=None, ylabel=None):
    df.index = df.index.droplevel([2, 3, 4])

    df = df.unstack(level=[1, 2])

    df = df.loc[scenario_order]

    # exclude values that are close to zero
    df = df.loc[:, (abs(df) > 1e-9).any(axis=0)]

    df.columns = df.columns.remove_unused_levels()

    df.columns = df.columns.set_levels(map_names_to_labels(df.columns.levels[1]), level=1)

    df = df.reindex(['CHP', 'HOB', 'TES cen.', 'HP', 'TES dec.'], level='name', axis=1)

    colors = [COLORS_BY_LABEL[i] for i in df.columns.get_level_values('name')]

    fig, ax = plt.subplots()
    ax.grid(axis='y')
    df.plot.bar(ax=ax, color=colors, stacked=True, rot=25)
    ax.set_title(title)
    ax.set_ylabel(ylabel)

    handles, labels = plt.gca().get_legend_handles_labels()

    ax.legend(
        handles=handles,
        labels=list(df.columns.get_level_values('name')),
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
        'SQ',
        'SQ_noHP_gastaxlevies=30',
        'FF',
    ]

    slicing = idx[scenario_paths.keys(), :, :, :, :, ['capacity', 'invest']]
    select = all_scalars.loc[slicing, :]
    plot_stacked_bar(
        select, scenario_order,
        'Existing and newly built capacity', 'Capacity [MWth]'
    )
    plt.savefig(os.path.join(dirs['plots'], 'capacities.pdf'))

    slicing = idx[scenario_paths.keys(), :, :, :, :, 'yearly_heat']
    select = all_scalars.loc[slicing, :]
    plot_stacked_bar(select, scenario_order, 'Yearly heat', 'Yearly heat [MWh]')
    plt.savefig(os.path.join(dirs['plots'], 'yearly_heat.pdf'))

    slicing = idx[scenario_paths.keys(), :, :, :, :, ['capacity_cost', 'carrier_cost']]
    select = all_scalars.loc[slicing, :]
    df = select / 300000  # Normalize to heat demand
    plot_stacked_bar(df, scenario_order, 'Costs', 'Costs [Eur/MWhth]')
    plt.savefig(os.path.join(dirs['plots'], 'costs.pdf'))

    plot_var_cost_assumptions(scenario_assumptions, scenario_order)
    plt.savefig(os.path.join(dirs['plots'], 'cost_assumptions.pdf'))


if __name__ == '__main__':
    scenario_assumptions = get_scenario_assumptions()
    main(scenario_assumptions)
