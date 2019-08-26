"""
Create and save plots of

* heat demand data
* energy system graph

"""

__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

import os
import re
import yaml
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import rcParams as rcParams
from matplotlib import gridspec
import oemof.solph as solph
import helpers

register_matplotlib_converters()


def plot_heat_demand(df, filename):
    # Plot demand of building
    fig, ax = plt.subplots(figsize=(12, 6))
    df.plot(ax=ax, linewidth=1)
    ax.set_xlabel("Date")
    ax.set_ylabel("Heat demand in MW")
    plt.savefig(filename, figsize=(12, 6), bbox_inches='tight')


def draw_graph(grph, filename, edge_labels=True, node_color='#AFAFAF',
               edge_color='#CFCFCF', plot=True, store=False,
               node_size=2000, node_shape='o', with_labels=True, arrows=True):
    """
    Draw a graph. This function will be removed in future versions.

    Parameters
    ----------
    grph : networkxGraph
        A graph to draw.
    edge_labels : boolean
        Use nominal values of flow as edge label
    node_color : dict or stringh
        Hex color code oder matplotlib color for each node. If string, all
        colors are the same.

    edge_color : string
        Hex color code oder matplotlib color for edge color.

    plot : boolean
        Show matplotlib plot.

    node_size : integer
        Size of nodes.

    with_labels : boolean
        Draw node labels.

    arrows : boolean
        Draw arrows on directed edges. Works only if an optimization_model has
        been passed.
    layout : string
        networkx graph layout, one of: neato, dot, twopi, circo, fdp, sfdp.
    """
    if type(node_color) is dict:
        node_color = [node_color.get(g, '#AFAFAF') for g in grph.nodes()]

    # set drawing options
    options = {
        #'prog': 'dot',
        'with_labels': with_labels,
        'node_color': node_color,
        'edge_color': edge_color,
        'node_size': node_size,
        'node_shape': node_shape,
        'arrows': arrows
    }

    labeldict = {node: node.replace('_', '\n') for node in grph.nodes}

    # draw graph
    plt.figure(figsize=(12, 6))
    pos = nx.drawing.nx_agraph.graphviz_layout(grph, prog='dot', args="-Grankdir=LR")
    nx.draw(grph, pos=pos, labels=labeldict, **options)

    # add edge labels for all edges
    if edge_labels is True and plt:
        labels = nx.get_edge_attributes(grph, 'weight')
        nx.draw_networkx_edge_labels(grph, pos=pos, edge_labels=labels)

    if store is True:
        plt.savefig(filename, dpi=100, bbox_inches='tight')

    # show output
    if plot is True:
        plt.show()


def plot_dispatch(timeseries, color_dict, filename):
    r"""
    Creates and saves a plot of the heat dispatch.

    Parameters
    ----------
    df: DataFrame
        Containing flows from and to
        heat bus.

    filename: path
        Path to store plot.

    Returns
    -------
    None
    """
    storage_heat_charge_central = [component for component in timeseries.columns
                                   if bool(re.search('bus_th_central', component[0]))
                                   and bool(re.search('storage', component[1]))]
    feedin_heat_central = [component for component in timeseries.columns
                           if bool(re.search('bus_th_central', component[1]))]
    storage_heat_charge_decentral = [component for component in timeseries.columns
                                     if bool(re.search('bus_th', component[0]))
                                     and bool(re.search('storage_decentral', component[1]))]
    feedin_heat_decentral = [component for component in timeseries.columns
                             if bool(re.search('bus_th_decentral', component[1]))
                             and not bool(re.search('pipe', component[0]))]
    feedin_heat_decentral = sorted(feedin_heat_decentral, key=lambda x: re.sub('subnet-._', '', x[0]))
    storage_heat_charge = [*storage_heat_charge_central, *storage_heat_charge_decentral]
    feedin_heat = [*feedin_heat_central, *feedin_heat_decentral]

    # resample
    df_resam = timeseries.copy()
    df_resam = df_resam.resample('24H').mean()

    # invert heat to storage
    df_resam[storage_heat_charge] *= -1

    # prepare colors
    labels = [re.sub('subnet-._', '', i[0]) for i in feedin_heat]
    colors_heat_feedin = [color_dict[label] for label in labels]
    colors = colors_heat_feedin + ['k']

    # plot
    def stacked_bar_plot(ax, data, color=None):
        data_cum_sum = data.cumsum(axis=1)
        ax.fill_between(data_cum_sum.index, 0, data_cum_sum[data.columns[0]], step='mid', label=data.columns[0])
        for i in range(1, len(data.columns)):
            first = data.columns[i - 1]
            next = data.columns[i]
            if color!=None:
                color_i = color[i]
            else:
                color_i = None
            ax.fill_between(data_cum_sum.index, data_cum_sum[first], data_cum_sum[next],
                        step='mid', label=next)#, color=color_i)

    fig, ax = plt.subplots(figsize=(12, 6))
    stacked_bar_plot(ax, df_resam[storage_heat_charge])
    stacked_bar_plot(ax, df_resam[feedin_heat], color=colors)
    ax.set_ylim(-50, 200)
    ax.grid(axis='y')

    # set title, labels and legend
    ax.set_ylabel('Power in MW')
    ax.set_xlabel('Time')
    ax.set_title('Heat generation dispatch')
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))  # place legend outside of plot

    # save figure
    fig.savefig(filename, bbox_inches='tight', figsize=(12, 6))
    return None


def plot_load_duration_curves(timeseries, color_dict, filename):
    r"""
    Creates and saves a plot of the heat dispatch.

    Parameters
    ----------
    df: DataFrame
        Containing flows from and to
        heat bus.

    filename: path
        Path to store plot.

    Returns
    -------
    None
    """
    storage_heat_charge_central = [component for component in timeseries.columns
                                   if bool(re.search('bus_th_central', component[0]))
                                   and bool(re.search('storage', component[1]))]
    feedin_heat_central = [component for component in timeseries.columns
                           if bool(re.search('bus_th_central', component[1]))]
    storage_heat_charge_decentral = [component for component in timeseries.columns
                                     if bool(re.search('bus_th', component[0]))
                                     and bool(re.search('storage_decentral', component[1]))]
    feedin_heat_decentral = [component for component in timeseries.columns
                             if bool(re.search('bus_th_decentral', component[1]))
                             and not bool(re.search('pipe', component[0]))]
    feedin_heat_decentral = sorted(feedin_heat_decentral, key=lambda x: re.sub('subnet-._', '', x[0]))
    storage_heat_charge = [*storage_heat_charge_central, *storage_heat_charge_decentral]
    feedin_heat = [*feedin_heat_central, *feedin_heat_decentral]

    # resample
    df_resam = timeseries.copy()
    df_resam = df_resam.resample('24H').mean()

    # Sort timeseries
    sorted_df = pd.DataFrame()
    for column in df_resam.columns:
        sorted_df[column] = sorted(df_resam[column], reverse=True)

    # invert heat to storage
    sorted_df[storage_heat_charge] *= -1

    # prepare colors
    labels = [re.sub('subnet-._', '', i[0]) for i in feedin_heat]
    colors_heat_feedin = [color_dict[label] for label in labels]
    colors = colors_heat_feedin + ['k']

    # plot
    fig, ax = plt.subplots(figsize=(12, 6))
    sorted_df[storage_heat_charge].plot(ax=ax)
    sorted_df[feedin_heat].plot(ax=ax, color=colors)
    ax.set_ylim(-50, 200)
    ax.grid(axis='y')

    # set title, labels and legend
    ax.set_ylabel('Power in MW')
    ax.set_xlabel('Time (days)')
    ax.set_title('Heat generation load duration curves')
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))  # place legend outside of plot

    # save figure
    fig.savefig(filename, bbox_inches='tight', figsize=(12, 6))
    return None


def plot_storage_level(timeseries, color_dict, filename):
    r"""
    Creates and saves a plot of storage level, charge and discharge.

    Parameters
    ----------
    timeseries : DataFrame
        Containing flows from and to heat bus.

    color_dict : dict
        Defining colors for the plot

    filename : path
        Path to store plot.

    Returns
    -------
    None
    """
    storage_heat_charge_central = [component for component in timeseries.columns
                                   if bool(re.search('bus_th_central', component[0]))
                                   and bool(re.search('storage', component[1]))]
    storage_heat_charge_decentral = [component for component in timeseries.columns
                                     if bool(re.search('bus_th', component[0]))
                                     and bool(re.search('storage_decentral', component[1]))]

    storage_heat_discharge_central = [component for component in timeseries.columns
                                      if bool(re.search('bus_th_central', component[1]))
                                      and bool(re.search('storage', component[0]))]
    storage_heat_discharge_decentral = [component for component in timeseries.columns
                                        if bool(re.search('bus_th', component[1]))
                                        and bool(re.search('storage_decentral', component[0]))]
    storage_heat_level_central = [component for component in timeseries.columns
                                  if bool(re.search('storage', component[0]))
                                  and component[1]=='None']
    storage_heat_level_decentral = [component for component in timeseries.columns
                                    if bool(re.search('storage_decentral', component[0]))
                                    and component[1]=='None']
    storage_heat_charge = [*storage_heat_charge_central, *storage_heat_charge_decentral]
    storage_heat_discharge = [*storage_heat_discharge_central, *storage_heat_discharge_decentral]
    storage_heat_level = [*storage_heat_level_central, *storage_heat_level_decentral]

    # resample
    df_resam = timeseries.copy()

    # invert heat to storage
    df_resam[storage_heat_charge] *= -1

    # prepare colors
    labels = [re.sub('subnet-._', '', i[0]) for i in storage_heat_charge]
    colors_charge = [color_dict[label] for label in labels]
    labels = [re.sub('subnet-._', '', i[0]) for i in storage_heat_discharge]
    colors_discharge = [color_dict[label] for label in labels]
    labels = [re.sub('subnet-._', '', i[0]) for i in storage_heat_level]
    colors_level = [color_dict[label] for label in labels]

    # plot
    fig, ax = plt.subplots(2, 1, figsize=(12, 6))
    df_resam[storage_heat_charge].plot.area(ax=ax[0], color=colors_charge)
    df_resam[storage_heat_discharge].plot.area(ax=ax[0], color=colors_discharge)
    df_resam[storage_heat_level].plot.area(ax=ax[1], color=colors_level, alpha=0.3)

    ax[0].set_ylim(-50, 50)
    ax[0].grid(axis='y', color='b')
    ax[1].set_ylim(0, 500)
    ax[1].grid(axis='y', color='k')

    # set title, labels and legend
    ax[0].set_ylabel('Power in MW')
    ax[1].set_ylabel('Storage level in MWh')
    ax[1].set_xlabel('Time')
    ax[0].set_title('Storage level, charge and discharge')
    ax[0].legend(loc='upper left', bbox_to_anchor=(1.1, 0.5))  # place legend outside of plot
    ax[1].legend(loc='lower left', bbox_to_anchor=(1.1, 0.5))  # place legend outside of plot

    fig.savefig(filename, bbox_inches='tight', figsize=(12, 6))
    return None


def plot_results_scalar_derived(results_scalar_derived, color_dict, filename):
    r"""
    Creates and saves an overview plot of derived results.

    Parameters
    ----------
    results_scalar_derived : DataFrame
        Containing derived results

    color_dict : dict
        Defining colors for the plot

    filename : path
        Path to store plot.

    Returns
    -------
    None
    """
    grouped = results_scalar_derived.groupby('var_name')
    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(3, 7)

    def stacked_single_bar(group, ax):
        data = grouped.get_group(group)['var_value']
        unit = grouped.get_group(group)['var_unit'][0]
        bottom = 0
        for i in range(len(data)):
            label = data.index[i][0]
            color = color_dict[re.sub('subnet-._', '', label)]
            ax.bar(0, data.iloc[i],
                   color=color,
                   label=label,
                   bottom=bottom)
            bottom += data.iloc[i].copy()
        ax.set_xticklabels([])
        ax.set_title(group.replace('_','\n')+f' [{unit}]')
        ax.legend(loc='lower center', bbox_to_anchor=(0, -0.2))

    def horizontal_bar(group, ax):
        data = grouped.get_group(group)['var_value']
        data.index = data.index.droplevel([1, 2])
        unit = grouped.get_group(group)['var_unit'][0]
        keys = [re.sub('subnet-._', '', key) for key in data.index]
        colors = [color_dict[key] for key in keys]
        data.plot(ax=ax,
                  kind='bar',
                  color=colors)
        ax.set_title(group+f' [{unit}]')

    ax = fig.add_subplot(gs[:, 0])
    stacked_single_bar('cost_total_system', ax)

    ax = fig.add_subplot(gs[:, 1])
    stacked_single_bar('installed_production_capacity', ax)

    ax = fig.add_subplot(gs[:, 2])
    stacked_single_bar('energy_thermal_produced_sum', ax)

    ax = fig.add_subplot(gs[:, 3])
    stacked_single_bar('energy_consumed_sum', ax)

    ax = fig.add_subplot(gs[:, 4])
    stacked_single_bar('emissions_sum', ax)

    ax = fig.add_subplot(gs[0, 5:])
    horizontal_bar('hours_full_load', ax)

    ax = fig.add_subplot(gs[1, 5:])
    horizontal_bar('hours_operating_sum', ax)

    ax = fig.add_subplot(gs[2, 5:])
    horizontal_bar('number_starts', ax)

    plt.tight_layout()
    plt.savefig(filename)


def create_plots(config_path, results_dir):
    r"""
    Runs the plot production pipeline.
    """
    # open config
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    with open(config_path, 'r') as config_file:
        cfg = yaml.load(config_file)

    with open(os.path.join(abs_path, 'experiment_configs/color_dict.yml'), 'r') as color_file:
        color_dict = yaml.load(color_file)

    # load model_runs
    model_runs = helpers.load_model_runs(results_dir, cfg)
    for index, input_parameter in model_runs.iterrows():
        label = "_".join(map(str, index))
        dir_postproc = os.path.join(results_dir, 'data_postprocessed', label)

        energysystem = solph.EnergySystem()
        energysystem.restore(dpath=results_dir + '/optimisation_results', filename=f'{label}_es.dump')
        energysystem_graph = nx.readwrite.read_gpickle(os.path.join(results_dir, 'data_plots/energysystem_graph.pkl'))

        draw_graph(energysystem_graph, plot=False, store=True, filename=results_dir + '/plots/' + 'es_graph.pdf',
                   node_size=5000, edge_color='k',
                   node_color=color_dict)

        rcParams['figure.figsize'] = [10.0, 10.0]

        # demand = pd.read_csv(os.path.join(results_dir, cfg['timeseries']['timeseries_demand_heat']))
        # plot_heat_demand(demand, filename=results_dir + '/plots/heat_demand.pdf')

        timeseries = pd.read_csv(os.path.join(results_dir,
                                              os.path.join(dir_postproc,
                                                           cfg['data_postprocessed']['timeseries']['timeseries'])),
                                 header=[0,1,2], index_col=0, parse_dates=True)

        results_scalar_derived = pd.read_csv(os.path.join(results_dir,
                                              os.path.join(dir_postproc,
                                                           cfg['data_postprocessed']['scalars']['derived'])),
                                 header=0, index_col=[0,1,2], parse_dates=True)

        dir_plot = os.path.join(results_dir, 'plots', label)
        if not os.path.exists(dir_plot):
            os.makedirs(os.path.join(dir_plot))

        plot_dispatch(timeseries, color_dict, os.path.join(dir_plot, 'dispatch_stack_plot.pdf'))
        plot_load_duration_curves(timeseries, color_dict, os.path.join(dir_plot, 'load_duration_curves.pdf'))
        plot_storage_level(timeseries, color_dict, os.path.join(dir_plot, 'storage_level.pdf'))
        plot_results_scalar_derived(results_scalar_derived,
                                    color_dict,
                                    os.path.join(dir_plot, 'results_scalar_derived.pdf'))


if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    create_plots(config_path, results_dir)

