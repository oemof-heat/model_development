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
import oemof_visio as oev

import networkx as nx

abs_path = os.path.dirname(os.path.abspath(__file__))

energysystem = solph.EnergySystem()
energysystem.restore(dpath=abs_path, filename='es.dump')
energysystem_graph = graph.create_nx_graph(energysystem)

def plot_heat_demand():
    # Plot demand of building
    demand = pd.read_csv(abs_path + '/data/' + 'demand_heat.csv')
    plt.figure()
    ax = demand.plot()
    ax.set_xlabel("Date")
    ax.set_ylabel("Heat demand in MW")
    plt.savefig('plots/heat_demand.png', dpi=100, bbox_inches='tight')

# plot_heat_demand()

def draw_graph(grph, filename, edge_labels=True, node_color='#AFAFAF',
               edge_color='#CFCFCF', plot=True, store=False,
               node_size=2000, with_labels=True, arrows=True,
               layout='neato'):
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
        'prog': 'dot',
        'with_labels': with_labels,
        'node_color': node_color,
        'edge_color': edge_color,
        'node_size': node_size,
        'arrows': arrows
    }

    # draw graph
    plt.figure()
    pos = nx.drawing.nx_agraph.graphviz_layout(grph, prog=layout)

    nx.draw(grph, pos=pos, **options)

    # add edge labels for all edges
    if edge_labels is True and plt:
        labels = nx.get_edge_attributes(grph, 'weight')
        nx.draw_networkx_edge_labels(grph, pos=pos, edge_labels=labels)

    if store is True:
        plt.savefig(filename, dpi=100, bbox_inches='tight')

    # show output
    if plot is True:
        plt.show()


# draw_graph(energysystem_graph, plot=False, store=True, filename=abs_path+'/plots/'+'es_graph.png', layout='neato', node_size=3000,
#            node_color={
#                'b_0': '#cd3333',
#                'b_1': '#7EC0EE',
#                'b_2': '#eeac7e'})

# rcParams['figure.figsize'] = [10.0, 10.0]

def create_dispatch_plot():
    print(energysystem.results['main'].keys())
    node_results_bel = outputlib.views.node(energysystem.results['main'], 'heat')
    # print(node_results_bel)
    df = node_results_bel['sequences']

    # inorder = [(('pp_chp', 'bel'), 'flow'),
    #              (('pp_coal', 'bel'), 'flow'),
    #              (('pp_gas', 'bel'), 'flow'),
    #              (('pp_lig', 'bel'), 'flow'),
    #              (('pp_oil', 'bel'), 'flow'),
    #              (('pv', 'bel'), 'flow'),
    #              (('wind', 'bel'), 'flow')]

    # outorder = [(('bel', 'demand_el'), 'flow'),
    #              (('bel', 'excess_el'), 'flow'),
    #              (('bel', 'heat_pump'), 'flow')]

    # cdict = {(('pp_chp', 'bel'), 'flow'): '#eeac7e',
    #         (('pp_coal', 'bel'), 'flow'): '#0f2e2e',
    #         (('pp_gas', 'bel'), 'flow'): '#c76c56',
    #         (('pp_lig', 'bel'), 'flow'): '#56201d',
    #         (('pp_oil', 'bel'), 'flow'): '#494a19',
    #         (('pv', 'bel'), 'flow'): '#ffde32',
    #         (('wind', 'bel'), 'flow'): '#4ca7c3',
    #         (('bel', 'demand_el'), 'flow'): '#ce4aff',
    #         (('bel', 'excess_el'), 'flow'): '#555555',
    #         (('bel', 'heat_pump'), 'flow'): '#42c77a'}

    # df = df.head(3000)
    print(int(len(df.index)/10))
    fig = plt.figure(figsize=(13, 5))
    ax = fig.add_subplot(1, 1, 1)
    df.plot(ax=ax, kind='bar', stacked=True, linewidth=0, width=1)
    ax.set_xlabel('Time [h]')
    ax.set_ylabel('Energy [MWh]')
    ax.set_title('Flows into and out of bel')
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5)) # place legend outside of plot
    ax.set_xticks(range(0, len(df.index)-1, int(len(df.index)/10)), minor=False)
    # ax.set_xticklabels()
    ax.set_ylabel('Power in MW')
    ax.set_xlabel('2012')
    ax.set_title("Electricity bus")
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5)) # place legend outside of plot

    # save figure
    fig.savefig(abs_path  + '/plots/' + 'myplot.png', bbox_inches='tight')

create_dispatch_plot()
    
