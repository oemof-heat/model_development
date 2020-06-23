import os

import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates

from helper import get_experiment_dirs, get_scenario_assumptions, get_config_file


idx = pd.IndexSlice

COLORS = get_config_file('colors.yml')

LABELS = get_config_file('labels.yml')


def c_list(data):
    if isinstance(data, pd.Series):
        return COLORS[data.name]

    if isinstance(data, pd.DataFrame):
        return [COLORS[k] for k in data.columns]


def map_label_list(handles=None, labels=None):
    if labels is None:
        current_axis = plt.gca()
        handles, labels = current_axis.get_legend_handles_labels()

    labels = [LABELS[k] for k in labels]

    l_h = {l: h for l, h in zip(labels, handles)}

    l_h = {l: l_h[l] for l in sorted(l_h.keys())}

    return l_h.values(), l_h.keys()


def bar_plot():
    pass


def multiplot_dispatch(ts_upper, ts_lower, destination):
    r"""

    Parameters
    ----------
    ts_upper: DataFrame
        Timeseries.

    ts_lower: DataFrame
        Timeseries

    destination: path
        Path to store plot.

    Returns
    -------
    None
    """
    # resample
    # df_resam = df_resam.resample('24H').mean()

    # invert heat to storage
    # df[storage_heat_charge] *= -1

    # aggregate decentral

    # prepare colors
    fig = plt.figure(figsize=(12, 9))
    gs = plt.GridSpec(4, 2)

    ax_upper = (fig.add_subplot(gs[:3, 0]), fig.add_subplot(gs[:3, 1]))
    ax_lower = (fig.add_subplot(gs[3, 0]), fig.add_subplot(gs[3, 1]))

    ax_upper[0].set_title('Winter')
    ax_upper[1].set_title('Summer')

    for i in range(2):
        stack_plot_with_negative_values(ts_upper[i], ax=ax_upper[i])
        ax_upper[i].set_ylim(-50, 105)
        ax_upper[i].grid(axis='y')

        stack_plot_with_negative_values(ts_lower[i], ax=ax_lower[i])

    ax_upper[0].set_ylabel('Heat output [MW]')
    ax_upper[0].set_ylabel('Electrical power \n [MW]')
    ax_lower[0].set_xlabel('Time')
    ax_lower[1].set_xlabel('Time')

    # plt.suptitle('Heat generation dispatch {}'.format(label))

    ax_upper[1].legend(loc='center left', bbox_to_anchor=(1.0, 0.8))  # place legend outside of plot

    fig.subplots_adjust(hspace=0.1)
    fig.subplots_adjust(wspace=0)

    for i in range(2):
        ax_lower[i].xaxis.set_major_locator(mdates.WeekdayLocator())
        ax_lower[i].xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

    plt.setp([a.get_xticklabels() for a in [ax_upper[0], ax_upper[1]]], visible=False)
    plt.setp([a.get_yticklabels() for a in [ax_upper[1], ax_lower[1]]], visible=False)

    fig.savefig(destination, bbox_inches='tight', dpi=500)

    return None


def stack_plot_with_negative_values(timeseries, ax):
    timeseries_pos = timeseries.copy()
    timeseries_pos[timeseries_pos < 0] = 0
    timeseries_pos = timeseries_pos.loc[:, (timeseries_pos != 0).any(axis=0)]

    timeseries_neg = timeseries.copy()
    timeseries_neg[timeseries_neg >= 0] = 0
    timeseries_neg = timeseries_neg.loc[:, (timeseries_neg != 0).any(axis=0)]

    if not timeseries_pos.empty:
        timeseries_pos.plot.area(ax=ax, color=c_list(timeseries_pos))
    if not timeseries_neg.empty:
        timeseries_neg.plot.area(ax=ax, color=c_list(timeseries_neg))
    return ax


def plot_dispatch(timeseries, demand, destination):
    fig, ax = plt.subplots(figsize=(12, 5))

    stack_plot_with_negative_values(timeseries, ax)

    demand.plot.line(ax=ax, c='r', linewidth=2)

    ax.set_ylim(-60, 125)
    ax.set_title('Dispatch')

    handles, labels = map_label_list()
    ax.legend(
        handles=handles,
        labels=labels,
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

    handles, labels = map_label_list()
    ax.set_title('Load duration')
    ax.legend(
        handles=handles,
        labels=labels,
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

    electricity = pd.read_csv(
        os.path.join(dirs['postprocessed'], 'sequences', 'electricity.csv'),
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
    end = '2017-02-14'

    plot_dispatch(
        supply[start:end], demand[start:end],
        os.path.join(dirs['plots'], 'heat_dispatch.pdf')
    )

    winter_a = '2017-02-01'
    winter_b = '2017-02-14'
    summer_a = '2017-06-01'
    summer_b = '2017-06-14'

    multiplot_dispatch(
        (supply[winter_a:winter_b], supply[summer_a:summer_b]),
        (electricity[winter_a:winter_b], electricity[summer_a:summer_b]),
        os.path.join(dirs['plots'], 'heat_el_dispatch.pdf')
    )
    # yearly_production= yearly_heat_sum.drop('heat-demand')
    # plot_yearly_production(yearly_production, os.path.join(dirs['plots'], 'heat_yearly_production.svg'))


if __name__ == '__main__':
    scenario_assumptions = get_scenario_assumptions().loc[0]
    main(**scenario_assumptions)
