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

abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

energysystem = solph.EnergySystem()
energysystem.restore(dpath=abs_path + '/results', filename='es.dump')
energysystem_graph = graph.create_nx_graph(energysystem)

def plot_heat_demand():
    # Plot demand of building
    demand = pd.read_csv(abs_path + '/data/' + 'demand_heat.csv')
    plt.figure()
    ax = demand.plot()
    ax.set_xlabel("Date")
    ax.set_ylabel("Heat demand in MW")
    plt.savefig(abs_path + '/plots/heat_demand.pdf', dpi=100, bbox_inches='tight')

def hierarchy_pos(G, root, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5,
                  pos = None, parent = None):
    '''If there is a cycle that is reachable from root, then this will see infinite recursion.
       G: the graph
       root: the root node of current branch
       width: horizontal space allocated for this branch - avoids overlap with other branches
       vert_gap: gap between levels of hierarchy
       vert_loc: vertical location of root
       xcenter: horizontal location of root
       pos: a dict saying where all nodes go if they have been assigned
       parent: parent of this branch.'''
    if pos == None:
        pos = {root:(xcenter,vert_loc)}
    else:
        pos[root] = (xcenter, vert_loc)
    neighbors = list(G.neighbors(root))
    # if parent != None:   #this should be removed for directed graphs.
    #     neighbors.remove(parent)  #if directed, then parent not in neighbors.
    if len(neighbors)!=0:
        dx = width/len(neighbors)
        nextx = xcenter - width/2 - dx/2
        for neighbor in neighbors:
            nextx += dx
            pos = hierarchy_pos(G,neighbor, width = dx, vert_gap = vert_gap,
                                vert_loc = vert_loc-vert_gap, xcenter=nextx, pos=pos,
                                parent = root)
    return pos

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
    print('ee', labeldict)

    # draw graph
    plt.figure(figsize=(12, 6))
    pos = nx.drawing.nx_agraph.graphviz_layout(grph, prog='dot', args="-Grankdir=LR")
    nx.draw(grph, pos=pos, labels=labeldict, **options)

    # add edge labels for all edges
    # if edge_labels is True and plt:
    #     labels = nx.get_edge_attributes(grph, 'weight')
    #     nx.draw_networkx_edge_labels(grph, pos=pos, edge_labels=labels)

    if store is True:
        plt.savefig(filename, dpi=100, bbox_inches='tight')

    # show output
    if plot is True:
        plt.show()


def create_dispatch_plot():
    node_results_bel = outputlib.views.node(energysystem.results['main'], 'heat_prim')

    df = node_results_bel['sequences']
    heat_in = [key for key in df.keys() if key[0][1] == 'heat_prim']

    df_resam = df.resample('1D').mean()
    fig = plt.figure(figsize=(13, 5))
    ax = fig.add_subplot(1, 1, 1)
    df_resam[heat_in].plot(ax=ax, kind='bar', stacked=True, color=['g','r','b','y'], linewidth=0, width=1, use_index=False)
    (-1 * df_resam[(('heat_prim', 'storage_heat'), 'flow')]).plot(ax=ax, kind='bar', color='k', stacked=True, linewidth=0, width=1, use_index=False)
    print(-1 * df_resam[(('heat_prim', 'storage_heat'), 'flow')])
    # df_resam[(('heat_prim', 'demand_heat'), 'flow')].plot(ax=ax, color='r', linewidth=3, use_index=False)
    ax.set_xlabel('Time [h]')
    ax.set_ylabel('Energy [MWh]')
    ax.set_title('Flows into and out of bel')
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5)) # place legend outside of plot
    # ax.set_xticks(range(0, len(df_resam.index)-1, int(len(df_resam.index)/10)), minor=False)
    # ax.set_xticklabels([1,2,3], minor=False)
    print(df_resam.index)
    # ax.set_xticklabels(
    #     [item.strftime(date_format)
    #      for item in dates.tolist()[0::tick_distance]],
    #     rotation=0, minor=False)
    ax.set_ylabel('Power in kW')
    ax.set_xlabel('2014')
    ax.set_title("Heat bus")
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5)) # place legend outside of plot

    # save figure
    fig.savefig(abs_path  + '/plots/' + 'dispatch_stack_plot.pdf', bbox_inches='tight', figsize=(12, 6), dpi=100)


def create_plots():
    plot_heat_demand()
    draw_graph(energysystem_graph, plot=False, store=True, filename=abs_path + '/plots/' + 'es_graph.pdf',
               node_size=5000, edge_color='k',
               node_color={
                   'natural gas': '#19A8B8',
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
                   'demand_heat': '#eeac7e'})


    rcParams['figure.figsize'] = [10.0, 10.0]
    create_dispatch_plot()

if __name__ == '__main__':
    create_plots()

