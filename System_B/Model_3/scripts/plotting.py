import os

import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
from matplotlib import rcParams

from helper import get_experiment_dirs, get_scenario_assumptions, get_config_file


idx = pd.IndexSlice

COLORS = get_config_file('colors.yml')

LABELS = get_config_file('labels.yml')

COLORS_BY_LABEL = {LABELS[key]: value for key, value in COLORS.items()}

rcParams['font.size'] = 20


def c_list(data, colors):
    if isinstance(data, pd.Series):
        return [colors[data.name]]

    if isinstance(data, pd.DataFrame):
        return [colors[k] for k in data.columns]


def map_names_to_labels(component_list):
    return [LABELS[c] for c in component_list]


def map_handles_labels(handles=None, labels=None):
    if labels is None:
        current_axis = plt.gca()
        handles, labels = current_axis.get_legend_handles_labels()

    labels = map_names_to_labels(labels)

    l_h = {l: h for l, h in zip(labels, handles)}

    l_h = {l: l_h[l] for l in sorted(l_h.keys())}

    return l_h.values(), l_h.keys()


def darken_color(color, amount=0.5):
    import matplotlib.colors as mc
    import colorsys
    if isinstance(color, list):
        return [darken_color(c) for c in color]
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))

    return colorsys.hls_to_rgb(c[0], max(0, min(1, amount * c[1])), c[2])


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
    fig = plt.figure(figsize=(12, 9))
    gs = plt.GridSpec(4, 2)

    # relabel
    def relabel_df(df, axis, labels=LABELS):
        if axis == 0:
            df.index = [LABELS[c] for c in df.index]
        elif axis == 1:
            df.columns = [LABELS[c] for c in df.columns]
        return df

    for ts in [ts_upper, ts_lower]:
        for t in ts:
            relabel_df(t, axis=1)

    ax_upper = (fig.add_subplot(gs[:3, 0]), fig.add_subplot(gs[:3, 1]))
    ax_lower = (fig.add_subplot(gs[3, 0]), fig.add_subplot(gs[3, 1]))

    ax_upper[0].set_title('Winter')
    ax_upper[1].set_title('Summer')

    for i in range(2):
        stack_plot_with_negative_values(ts_upper[i], ax=ax_upper[i], colors=COLORS_BY_LABEL)
        ax_upper[i].set_ylim(-50, 105)
        ax_upper[i].grid(axis='y')

        stack_plot_with_negative_values(ts_lower[i], ax=ax_lower[i], colors=COLORS_BY_LABEL)

    ax_upper[0].set_ylabel('Heat output [MW]')
    ax_lower[0].set_ylabel('Electrical power \n [MW]')
    ax_lower[0].set_xlabel('Time')
    ax_lower[1].set_xlabel('Time')

    # plt.suptitle('Heat generation dispatch {}'.format(label))

    fig.subplots_adjust(hspace=0.1)
    fig.subplots_adjust(wspace=0)

    for i in range(2):
        ax_lower[i].xaxis.set_major_locator(mdates.WeekdayLocator())
        ax_lower[i].xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

        ax_upper[i].legend().remove()
        ax_lower[i].legend().remove()

    # ax_upper[0].legend(loc='center left', bbox_to_anchor=(2, 0.7))  # place legend outside of plot

    plt.setp([a.get_xticklabels() for a in [ax_upper[0], ax_upper[1]]], visible=False)
    [a.set_xlabel(None) for a in [ax_upper[0], ax_upper[1]]]
    plt.setp([a.get_yticklabels() for a in [ax_upper[1], ax_lower[1]]], visible=False)

    fig.savefig(destination, bbox_inches='tight', dpi=500)
    plt.close(fig)


def stack_plot_with_negative_values(timeseries, ax, colors):
    timeseries_pos = timeseries.copy()
    timeseries_pos[timeseries_pos < 0] = 0
    timeseries_pos = timeseries_pos.loc[:, (timeseries_pos != 0).any(axis=0)]

    timeseries_neg = timeseries.copy()
    timeseries_neg[timeseries_neg >= 0] = 0
    timeseries_neg = timeseries_neg.loc[:, (timeseries_neg != 0).any(axis=0)]

    if not timeseries_pos.empty:
        timeseries_pos.plot.area(ax=ax, color=c_list(timeseries_pos, colors))
    if not timeseries_neg.empty:
        timeseries_neg.plot.area(ax=ax, color=c_list(timeseries_neg, colors))
    return ax


def plot_dispatch(timeseries, demand, destination):
    fig, ax = plt.subplots(figsize=(12, 5))

    stack_plot_with_negative_values(timeseries, ax, COLORS)

    demand.plot.line(ax=ax, c='r', linewidth=2)

    ax.set_ylim(-60, 125)
    ax.set_title('Dispatch')

    handles, labels = map_handles_labels()
    ax.legend(
        handles=handles,
        labels=labels,
        loc='center left',
        bbox_to_anchor=(1.0, 0.5))

    current_handles, current_labels = plt.gca().get_legend_handles_labels()

    plt.tight_layout()
    plt.savefig(destination)
    plt.close(fig)


def plot_load_duration(timeseries, legend=True, plot_original=False, title=None, ylabel=None, **kwargs):
    fig, ax = plt.subplots(figsize=(5, 5))

    if plot_original:
        timeseries.plot.line(ax=ax, color=c_list(timeseries, COLORS), use_index=False, **kwargs)

    # sort timeseries
    if isinstance(timeseries, pd.DataFrame):
        sorted_ts = pd.DataFrame()
        for column in timeseries.columns:
            sorted_ts[column] = sorted(timeseries[column], reverse=True)

    elif isinstance(timeseries, pd.Series):
        sorted_ts = pd.DataFrame({timeseries.name: sorted(timeseries, reverse=True)})

    # keep only nonzero
    sorted_ts = sorted_ts.loc[:, (sorted_ts != 0).any(axis=0)]

    colors = c_list(sorted_ts, COLORS)
    if plot_original:
        colors = darken_color(colors)

    sorted_ts.plot.line(ax=ax, color=colors, **kwargs)

    ax.set_ylabel(ylabel)
    ax.set_title(title)

    if legend:
        handles, labels = map_handles_labels()
        ax.legend(
            handles=handles,
            labels=labels,
            loc='center left',
            bbox_to_anchor=(1.0, 0.5)
        )
    else:
        plt.legend().remove()

    plt.tight_layout()


def plot_yearly_production(yearly_production, destination):
    print('\n######### plotting yearly_production #########')
    print(yearly_production)

    fig, ax = plt.subplots()
    yearly_production.plot.bar(ax=ax)
    ax.set_title('Yearly production')
    plt.tight_layout()
    plt.savefig(destination)
    plt.close(fig)


def main(**scenario_assumptions):
    dirs = get_experiment_dirs(scenario_assumptions['scenario'])

    price_el = pd.read_csv(
        os.path.join(dirs['preprocessed'], 'data', 'sequences', 'carrier_cost_profile.csv'),
        index_col=0
    )

    electricity = pd.read_csv(
        os.path.join(dirs['postprocessed'], 'sequences', 'electricity.csv'),
        index_col=0,
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

    plot_load_duration(
        price_el,
        legend=False,
        plot_original=True,
        title='Electricity prices (buying)',
        ylabel='Hourly price [Eur/MWh]',
    )
    plt.savefig(os.path.join(dirs['plots'], 'price_el.pdf'))
    plt.close()

    plot_load_duration(
        demand,
        legend=False,
        plot_original=True,
        title = 'Heat demand',
        ylabel = 'Hourly heat demand [MWh]',
    )
    plt.savefig(os.path.join(dirs['plots'], 'heat_demand.pdf'))
    plt.close()

    plot_load_duration(
        supply,
        linewidth=10,
    )
    plt.savefig(os.path.join(dirs['plots'], 'heat_supply.pdf'))
    plt.close()

    start = '2017-02-01'
    end = '2017-02-14'

    plot_dispatch(
        supply[start:end], demand[start:end],
        os.path.join(dirs['plots'], 'heat_dispatch.pdf')
    )


    winter_a = '2017-01-10'
    winter_b = '2017-01-24'
    summer_a = '2017-06-01'
    summer_b = '2017-06-14'

    electricity_chp = pd.DataFrame(electricity['gas-chp'])

    multiplot_dispatch(
        (supply[winter_a:winter_b], supply[summer_a:summer_b]),
        (electricity_chp[winter_a:winter_b], electricity_chp[summer_a:summer_b]),
        os.path.join(dirs['plots'], 'heat_el_dispatch.pdf')
    )
    # yearly_production= yearly_heat_sum.drop('heat-demand')
    # plot_yearly_production(yearly_production, os.path.join(dirs['plots'], 'heat_yearly_production.svg'))


if __name__ == '__main__':
    scenario_assumptions = get_scenario_assumptions().loc[3]
    main(**scenario_assumptions)
