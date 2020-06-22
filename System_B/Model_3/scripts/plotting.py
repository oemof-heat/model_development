import os

import matplotlib.pyplot as plt
import pandas as pd

from helper import get_experiment_dirs, get_scenario_assumptions, get_config_file


idx = pd.IndexSlice

COLORS = get_config_file('colors.yml')

LABELS = get_config_file('labels.yml')


def c_list(data):
    if isinstance(data, pd.Series):
        return COLORS[data.name]

    if isinstance(data, pd.DataFrame):
        return [COLORS[k] for k in data.columns]


def map_label_list():
    current_axis = plt.gca()
    handles, labels = current_axis.get_legend_handles_labels()

    labels = [LABELS[k] for k in labels]

    return labels


def bar_plot():
    pass


def plot_dispatch(timeseries, demand, destination):
    fig, ax = plt.subplots(figsize=(12, 5))

    timeseries_pos = timeseries.copy()
    timeseries_pos[timeseries_pos < 0] = 0
    timeseries_pos = timeseries_pos.loc[:, (timeseries_pos != 0).any(axis=0)]

    timeseries_neg = timeseries.copy()
    timeseries_neg[timeseries_neg >= 0] = 0
    timeseries_neg = timeseries_neg.loc[:, (timeseries_neg != 0).any(axis=0)]

    timeseries_pos.plot.area(ax=ax, color=c_list(timeseries_pos))
    timeseries_neg.plot.area(ax=ax, color=c_list(timeseries_neg))

    demand.plot.line(ax=ax, c='r', linewidth=2)

    ax.set_ylim(-60, 125)
    ax.set_title('Dispatch')

    ax.legend(
        labels=map_label_list(),
        loc='center left',
        bbox_to_anchor=(1.0, 0.5))

    current_handles, current_labels = plt.gca().get_legend_handles_labels()

    plt.tight_layout()
    plt.savefig(destination)


def plot_load_duration(timeseries, destination, plot_original=False):
    fig, ax = plt.subplots(figsize=(12, 5))

    if plot_original:
        timeseries.plot.line(ax=ax, color=c_list(timeseries))

    # sort timeseries
    if isinstance(timeseries, pd.DataFrame):
        sorted_ts = pd.DataFrame()
        for column in timeseries.columns:
            sorted_ts[column] = sorted(timeseries[column], reverse=True)

    elif isinstance(timeseries, pd.Series):
        sorted_ts = timeseries.sort_values(ascending=False)

    sorted_ts.plot.line(ax=ax, color=c_list(sorted_ts), linewidth=2)

    ax.set_title('Load duration')
    ax.legend(
        labels=map_label_list(),
        loc='center left',
        bbox_to_anchor=(1.0, 0.5)
    )

    plt.tight_layout()
    plt.savefig(destination)


def plot_yearly_production(yearly_production, destination):
    print('\n######### plotting yearly_production #########')
    print(yearly_production)

    fig, ax = plt.subplots()
    yearly_production.plot.bar(ax=ax)
    ax.set_title('Yearly production')
    plt.tight_layout()
    plt.savefig(destination)


def main(**scenario_assumptions):
    dirs = get_experiment_dirs(scenario_assumptions['name'])

    price_el = pd.read_csv(
        os.path.join(dirs['preprocessed'], 'data', 'sequences', 'carrier_cost_profile.csv'),
        index_col=0
    )

    heat_central = pd.read_csv(
        os.path.join(dirs['postprocessed'], 'sequences', 'heat_central.csv'),
        index_col=0
    )

    heat_decentral = pd.read_csv(
        os.path.join(dirs['postprocessed'], 'sequences', 'heat_decentral.csv'),
        index_col=0
    )

    timeseries = pd.concat([heat_central, heat_decentral], 1)

    timeseries = timeseries.drop('heat-distribution', axis=1)

    timeseries = timeseries.drop('heat_decentral-shortage', axis=1)

    supply = timeseries.drop('heat-demand', axis=1)

    demand = timeseries['heat-demand']

    plot_load_duration(price_el, os.path.join(dirs['plots'], 'price_el.pdf'), plot_original=True)

    plot_load_duration(demand, os.path.join(dirs['plots'], 'heat_demand.pdf'), plot_original=True)

    plot_load_duration(supply, os.path.join(dirs['plots'], 'heat_supply.pdf'))

    start = '2017-02-01'
    end = '2017-03-01'

    plot_dispatch(
        supply[start:end], demand[start:end],
        os.path.join(dirs['plots'], 'heat_dispatch.pdf')
    )

    # yearly_production= yearly_heat_sum.drop('heat-demand')
    # plot_yearly_production(yearly_production, os.path.join(dirs['plots'], 'heat_yearly_production.svg'))


if __name__ == '__main__':
    scenario_assumptions = get_scenario_assumptions().loc[0]
    main(**scenario_assumptions)
