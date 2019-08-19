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
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import rcParams as rcParams
import oemof.solph as solph
import helpers


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
    df_resam = timeseries
    df_resam = df_resam.loc['2019-01-01 00:00:00':'2019-03-01 00:00:00']

    # invert heat to storage
    df_resam[storage_heat_charge] *= -1

    # prepare colors
    labels = [re.sub('subnet-._', '', i[0]) for i in feedin_heat]
    colors_heat_feedin = [color_dict[label] for label in labels]
    colors = colors_heat_feedin + ['k']

    # plot
    fig, ax = plt.subplots(figsize=(12, 6))
    df_resam[storage_heat_charge].plot.area(ax=ax)
    df_resam[feedin_heat].plot.area(ax=ax, color=colors)
    # df_resam[storage_discharge_heat].plot(ax=ax, color='r', linewidth=3)

    ax.set_ylim(-50, 200)
    ax.grid(axis='y')

    # set title, labels and legend
    ax.set_ylabel('Power in MW')
    ax.set_xlabel('Time')
    ax.set_title('Heat demand and generation')
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))  # place legend outside of plot

    # save figure
    fig.savefig(filename, bbox_inches='tight', figsize=(12, 6))
    return None


def create_plots(config_path, results_dir):
    r"""
    Runs the plot production pipeline.
    """
    # open config
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    dir_postproc = os.path.join(results_dir, 'data_postprocessed')

    with open(config_path, 'r') as config_file:
        cfg = yaml.load(config_file)

    with open(os.path.join(abs_path, 'experiment_configs/color_dict.yml'), 'r') as color_file:
        color_dict = yaml.load(color_file)

    energysystem = solph.EnergySystem()
    energysystem.restore(dpath=results_dir + '/optimisation_results', filename='es.dump')
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

    plot_dispatch(timeseries, color_dict, filename=results_dir + '/plots/' + 'dispatch_stack_plot.pdf')


if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    create_plots(config_path, results_dir)

