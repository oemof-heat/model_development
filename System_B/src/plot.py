"""
Create and save plots of

* heat demand data
* energy system graph

"""

__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams as rcParams
import oemof.graph as graph
import oemof.solph as solph
import oemof.outputlib as outputlib
import networkx as nx
import yaml
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


def plot_dispatch(df, filename):
    r"""
    Creates and saves a plot of the heat
    dispatch.

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

    # preprocessing
    heat_in = [key for key in df.keys() if key[0][1] == 'heat_prim']
    heat_to_storage = (('heat_prim', 'storage_heat'), 'flow')
    heat_to_dhn = (('heat_prim', 'dhn_prim'), 'flow')

    # round
    df = df.round(10)

    # resample
    df_resam = df.resample('1D').mean()

    # invert heat to storage
    df_resam[heat_to_storage] *= -1

    # plot
    fig, ax = plt.subplots(figsize=(12, 6))
    df_resam[heat_in + [heat_to_storage]].plot.area(ax=ax, color=['#19A8B8','#F9FF00','#FF0000','k','k'])
    df_resam[heat_to_dhn].plot(ax=ax, color='r', linewidth=3)

    # set title, labels and legend
    ax.set_ylabel('Power in kW')
    ax.set_xlabel('Time')
    ax.set_title('Heat demand and generation')
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5)) # place legend outside of plot

    # save figure
    fig.savefig(filename, bbox_inches='tight', figsize=(12, 6))

    return None


def create_plots(config_path, results_dir):
    r"""
    Runs the plot production pipeline.
    """
    # open config
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    energysystem = solph.EnergySystem()
    energysystem.restore(dpath=results_dir + '/optimisation_results', filename='es.dump')
    energysystem_graph = graph.create_nx_graph(energysystem)

    node_color = { 'natural gas': '#19A8B8',
                   'ccgt': '#19A8B8',
                   'electricity': '#F9FF00',
                   'power_to_heat': '#F9FF00',
                   'storage_heat': '#FF0000',
                   'heat_prim': '#FF0000',
                   'dhn_prim': '#686868',
                   'heat_sec': '#FF5300',
                   'dhn_sec': '#686868',
                   'heat_end': '#FF9900',
                   'shortage_heat': '#FF0000',
                   'demand_heat': '#eeac7e'}
    draw_graph(energysystem_graph, plot=False, store=True, filename=results_dir + '/plots/' + 'es_graph.pdf',
               node_size=5000, edge_color='k',
               node_color=node_color)
    rcParams['figure.figsize'] = [10.0, 10.0]

    demand = pd.read_csv(os.path.join(results_dir, cfg['timeseries']['timeseries_demand_heat']))
    plot_heat_demand(demand, filename=results_dir + '/plots/heat_demand.pdf')

    node_results_bel = outputlib.views.node(energysystem.results['main'], 'heat_prim')['sequences']
    plot_dispatch(node_results_bel, filename=results_dir + '/plots/' + 'dispatch_stack_plot.pdf')


if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    create_plots(config_path, results_dir)

