__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

import os
import re
import yaml
import pandas as pd
import numpy as np
from pandas.plotting import register_matplotlib_converters
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
from matplotlib import rcParams as rcParams
from matplotlib import gridspec
import matplotlib.dates as mdates

import oemof.solph as solph
import oemof.outputlib as outputlib
import helpers

register_matplotlib_converters()


def plot_heat_demand(demand_heat, label, filename):
    # Plot demand of building1038:25
    fig, ax = plt.subplots(2, 1)
    demand_heat.iloc[0:1000].sum(axis=1).plot(ax=ax[0],
                                 linewidth=1,
                                 c='r')
    ax[0].set_xlabel("Date")
    ax[0].set_ylabel("Heat demand in MW")
    ax[0].set_title('Heat demand {}'.format(label))
    demand_heat.iloc[0:1000].plot(ax=ax[1],
                     linewidth=1,
                     c='r')
    plt.savefig(filename, bbox_inches='tight')


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
    plt.figure()
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


def stacked_bar_plot(ax, data, color=None):
    data_cum_sum = data.cumsum(axis=1)
    if color is not None:
        color_i = color[0]
    else:
        color_i = None
    ax.fill_between(data_cum_sum.index,
                    0,
                    data_cum_sum[data.columns[0]],
                    step='mid',
                    label=data.columns[0],
                    color=color_i)
    for i in range(1, len(data.columns)):
        first = data.columns[i - 1]
        next = data.columns[i]
        if color is not None:
            color_i = color[i]
        else:
            color_i = None
        ax.fill_between(data_cum_sum.index,
                        data_cum_sum[first],
                        data_cum_sum[next],
                        linewidth=0,
                        step='mid',
                        label=next,
                        color=color_i)


def plot_dispatch(timeseries, start_1, end_1, start_2, end_2, color_dict, label_dict, label, filename):
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
                                   and bool(re.search('tes', component[1]))]
    feedin_heat_central = [component for component in timeseries.columns
                           if bool(re.search('bus_th_central', component[1]))
                           and not bool(re.search('behind', component[1]))]
    feedin_heat_central.append(('tes_central', 'bus_th_central_behind_storage', 'flow'))
    storage_heat_charge_decentral = [component for component in timeseries.columns
                                     if bool(re.search('bus_th', component[0]))
                                     and bool(re.search('tes_decentral', component[1]))]
    feedin_heat_decentral = [component for component in timeseries.columns
                             if bool(re.search('bus_th_decentral', component[1]))
                             and not bool(re.search('pipe', component[0]))
                             and not bool(re.search('behind', component[1]))]
    feedin_heat_decentral.extend([component for component in timeseries.columns
                                  if bool(re.search('tes_decentral', component[0]))
                                  and bool(re.search('bus_th_decentral_behind', component[1]))])
    electricity_sold = [component for component in timeseries.columns
                        if component[1]=='sold_el']
    feedin_heat_decentral = sorted(feedin_heat_decentral, key=lambda x: re.sub('subnet-._', '', x[0]))
    storage_heat_charge = [*storage_heat_charge_central, *storage_heat_charge_decentral]
    feedin_heat = [*feedin_heat_central, *feedin_heat_decentral]
    demand_heat = [component for component in timeseries.columns
                   if bool(re.search('demand', component[1]))]

    # resample
    df_resam = timeseries.copy()
    # df_resam = df_resam.resample('24H').mean()

    # invert heat to storage
    df_resam[storage_heat_charge] *= -1

    # aggregate decentral
    group_subnets = lambda x: re.sub('subnet-._', '', x[0])
    feedin_aggregated = df_resam[feedin_heat].groupby(group_subnets, axis=1).agg(sum)
    feedin_aggregated = feedin_aggregated.loc[:, (feedin_aggregated != 0).any(axis=0)]
    group_subnets = lambda x: re.sub('subnet-._', '', x[1])
    charge_aggregated = df_resam[storage_heat_charge].groupby(group_subnets, axis=1).agg(sum)
    charge_aggregated = charge_aggregated.loc[:, (charge_aggregated != 0).any(axis=0)]
    demand_heat = df_resam[demand_heat].sum(axis=1)


    # prepare colors
    colors_feedin_heat = [color_dict[label] for label in feedin_aggregated]
    color_storage_heat_charge = [color_dict[label] for label in charge_aggregated]

    fig = plt.figure(figsize=(12, 8))
    gs = plt.GridSpec(4, 2)

    ax1 = (fig.add_subplot(gs[:3, 0]), fig.add_subplot(gs[:3, 1]))
    ax2 = (fig.add_subplot(gs[3, 0]), fig.add_subplot(gs[3, 1]))

    ax1[0].set_title('Winter')
    ax1[1].set_title('Summer')
    for i, limits in enumerate([[start_1, end_1], [start_2, end_2]]):
        stacked_bar_plot(ax1[i],
                         feedin_aggregated.loc[limits[0]:limits[1]],
                         color=colors_feedin_heat)
        stacked_bar_plot(ax1[i],
                         charge_aggregated.loc[limits[0]:limits[1]],
                         color=color_storage_heat_charge)
        ax1[i].plot(demand_heat.loc[limits[0]:limits[1]],
                linewidth='1.5',
                color='r')
        ax1[i].set_ylim(-50, 105)
        ax1[i].grid(axis='y')

        stacked_bar_plot(ax2[i],
                         df_resam[electricity_sold].loc[limits[0]:limits[1]],
                         color=[color_dict['chp']])


    ax1[0].set_ylabel('Heat output [MW]')
    ax2[0].set_ylabel('Electrical power \n [MW]')
    ax2[0].set_xlabel('Time')
    ax2[1].set_xlabel('Time')

    # plt.suptitle('Heat generation dispatch {}'.format(label))

    # save figure
    # ax1[1].legend(loc='center left', bbox_to_anchor=(1.0, 0.8))  # place legend outside of plot
    fig.subplots_adjust(hspace=0.1)
    fig.subplots_adjust(wspace=0)
    for i in [0 ,1]:
        ax2[i].xaxis.set_major_locator(mdates.WeekdayLocator())
        ax2[i].xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

    plt.setp([a.get_xticklabels() for a in [ax1[0], ax1[1]]], visible=False)
    plt.setp([a.get_yticklabels() for a in [ax1[1], ax2[1]]], visible=False)

    fig.savefig(filename, bbox_inches='tight', dpi=500)
    return None


def plot_load_duration_curves(timeseries, color_dict, label, filename):
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
                                   and bool(re.search('tes', component[1]))]
    feedin_heat_central = [component for component in timeseries.columns
                           if bool(re.search('bus_th_central', component[1]))
                           and not bool(re.search('behind', component[1]))]
    feedin_heat_central.append(('tes_central', 'bus_th_central_behind_storage', 'flow'))
    storage_heat_charge_decentral = [component for component in timeseries.columns
                                     if bool(re.search('bus_th', component[0]))
                                     and bool(re.search('tes_decentral', component[1]))]
    feedin_heat_decentral = [component for component in timeseries.columns
                             if bool(re.search('bus_th_decentral', component[1]))
                             and not bool(re.search('pipe', component[0]))
                             and not bool(re.search('behind', component[1]))]
    feedin_heat_decentral.extend([component for component in timeseries.columns
                                  if bool(re.search('tes_decentral', component[0]))
                                  and bool(re.search('bus_th_decentral_behind', component[1]))])
    feedin_heat_decentral = sorted(feedin_heat_decentral, key=lambda x: re.sub('subnet-._', '', x[0]))
    storage_heat_charge = [*storage_heat_charge_central, *storage_heat_charge_decentral]
    feedin_heat = [*feedin_heat_central, *feedin_heat_decentral]

    # resample
    df_resam = timeseries.copy()
    # df_resam = df_resam.resample('24H').mean()

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

    group_subnets = lambda x: re.sub('subnet-._', '', x[0])
    feedin_aggregated = sorted_df[feedin_heat].groupby(group_subnets, axis=1).agg(sum)
    charge_aggregated = sorted_df[storage_heat_charge].groupby(group_subnets, axis=1).agg(sum)
    feedin_aggregated = feedin_aggregated.loc[:, (feedin_aggregated != 0).any(axis=0)]

    # plot
    fig, ax = plt.subplots(figsize=(8,6))
    charge_aggregated.plot(ax=ax,
                           linewidth=5)
    feedin_aggregated.plot(ax=ax,
                           color=colors,
                           linewidth=5)
    ax.set_ylim(-20, 110)
    ax.grid(axis='y')

    # set title, labels and legend
    ax.set_ylabel('Power in MW')
    ax.set_xlabel('Time (days)')
    ax.set_title('Heat generation load duration curves {}'.format(label))
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))  # place legend outside of plot

    # save figure
    fig.savefig(filename, bbox_inches='tight')
    return None


def plot_storage_level(timeseries, color_dict, label, filename):
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
                                   and bool(re.search('tes', component[1]))]
    storage_heat_charge_decentral = [component for component in timeseries.columns
                                     if bool(re.search('bus_th', component[0]))
                                     and bool(re.search('tes_decentral', component[1]))]

    storage_heat_discharge_central = [component for component in timeseries.columns
                                      if bool(re.search('bus_th_central', component[1]))
                                      and bool(re.search('tes', component[0]))]
    storage_heat_discharge_decentral = [component for component in timeseries.columns
                                        if bool(re.search('bus_th', component[1]))
                                        and bool(re.search('tes_decentral', component[0]))]
    storage_heat_level_central = [component for component in timeseries.columns
                                  if bool(re.search('tes', component[0]))
                                  and component[1]=='None']
    storage_heat_level_decentral = [component for component in timeseries.columns
                                    if bool(re.search('tes_decentral', component[0]))
                                    and component[1]=='None']
    storage_heat_charge = [*storage_heat_charge_central, *storage_heat_charge_decentral]
    storage_heat_discharge = [*storage_heat_discharge_central, *storage_heat_discharge_decentral]
    storage_heat_level = [*storage_heat_level_central, *storage_heat_level_decentral]

    # resample
    df_resam = timeseries.copy()
    df_resam = df_resam.round(5)

    # invert heat to storage
    df_resam[storage_heat_charge] *= -1

    # prepare colors
    labels = [re.sub('subnet-._', '', i[0]) for i in storage_heat_charge]
    colors_charge = [color_dict[label] for label in labels]
    labels = [re.sub('subnet-._', '', i[0]) for i in storage_heat_discharge]
    colors_discharge = [color_dict[label] for label in labels]
    labels = [re.sub('subnet-._', '', i[0]) for i in storage_heat_level]
    colors_level = [color_dict[label] for label in labels]

    group_subnets = lambda x: re.sub('subnet-._', '', x[0])
    aggregated_charge = df_resam[storage_heat_charge].groupby(group_subnets, axis=1).agg(sum)
    aggregated_discharge = df_resam[storage_heat_discharge].groupby(group_subnets, axis=1).agg(sum)
    aggregated_level = df_resam[storage_heat_level].groupby(group_subnets, axis=1).agg(sum)

    # plot
    fig, ax = plt.subplots(2, 1)
    aggregated_charge.plot.area(ax=ax[0], color=colors_charge)
    aggregated_discharge.plot.area(ax=ax[0], color=colors_discharge)
    aggregated_level.plot.area(ax=ax[1], color=colors_level, alpha=0.3)

    ax[0].set_ylim(-40, 40)
    ax[0].grid(axis='y', color='b')
    ax[1].set_ylim(0, 2000)
    ax[1].grid(axis='y', color='k')

    # set title, labels and legend
    ax[0].set_ylabel('Power in MW')
    ax[1].set_ylabel('Storage level in MWh')
    ax[1].set_xlabel('Time')
    ax[0].set_title('Storage level, charge and discharge {}'.format(label))
    ax[0].legend(loc='upper left', bbox_to_anchor=(1.1, 0.5))  # place legend outside of plot
    ax[1].legend(loc='lower left', bbox_to_anchor=(1.1, 0.5))  # place legend outside of plot

    fig.savefig(filename, bbox_inches='tight')
    return None


def plot_price_el(price_el, label, filename):
    sorted_price_el = price_el.sort_values('variable_costs', ascending=False).reset_index(drop=True)
    # plot
    fig, ax = plt.subplots()
    ax.plot(price_el,
            c='k',
            label='Electricity spot price')
    ax.plot(sorted_price_el,
            label='Sorted electricity spot price')
    ax.set_ylim(-85, 170)
    ax.grid(axis='y',
            color='k',
            alpha=0.3)

    # set title, labels and legend
    ax.set_ylabel('Electricity price [Eur/MWh]')
    ax.set_xlabel('Hours')
    ax.set_title('Electricity price timeseries and duration curve {}'.format(label))
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))  # place legend outside of plot

    fig.savefig(filename, bbox_inches='tight')
    return None


def plot_p_q_diagram(timeseries, param_chp, capacity_installed_chp, color_dict, label, filename):
    supply_electricity = timeseries.loc[:, [key for key in timeseries.columns if key[1]=='sold_el']].iloc[:, 0]
    supply_electricity.name = 'supply_electricity'

    supply_heat = timeseries.loc[:, [key for key in timeseries.columns if bool(re.search('_demand', key[1]))]]\
        .sum(axis=1)
    supply_heat.name = 'supply_heat'

    operating_heat_pump = timeseries.loc[:, [key for key in timeseries.columns
                                             if bool(re.search('_pth_heat_pump_decentral', key[0]))]].sum(axis=1) > 0

    operating_heat_pump.name = 'heat_pump'
    operating_pth_resistive = timeseries.loc[:, [key for key in timeseries.columns
                                                 if bool(re.search('pth_resistive', key[0]))]].sum(axis=1) > 0

    operating_pth_resistive.name = 'pth_resistive'
    discharging_storage = timeseries.loc[:, [key for key in timeseries.columns
                                             if bool(re.search('tes', key[0]))
                                             and key[1]!='None']].sum(axis=1) > 0

    discharging_storage.name = 'discharging_storage'
    charging_storage = timeseries.loc[:, [key for key in timeseries.columns
                                          if bool(re.search('tes', key[1]))]].sum(axis=1) > 0
    charging_storage.name = 'charging_storage'

    df = pd.concat([supply_electricity,
                    supply_heat,
                    operating_pth_resistive,
                    operating_heat_pump,
                    charging_storage,
                    discharging_storage], axis=1)

    def func(row):
        sel = tuple(k for k, v in row.loc[['heat_pump',
                                      'pth_resistive',
                                      'charging_storage',
                                      'discharging_storage']].items() if v)
        col = {('heat_pump', 'pth_resistive', 'charging_storage', 'discharging_storage'): 'r',
               ('pth_resistive', 'charging_storage', 'discharging_storage'): 'r',
               ('heat_pump', 'charging_storage', 'discharging_storage'): 'r',
               ('charging_storage', 'discharging_storage'): 'r',
               ('heat_pump', 'pth_resistive', 'charging_storage'): 'g',
               ('heat_pump', 'pth_resistive', 'discharging_storage'): 'b',
               ('heat_pump', 'pth_resistive'): 'y',
               ('heat_pump', 'charging_storage'): 'g',
               ('pth_resistive', 'charging_storage'): 'g',
               ('pth_resistive', 'discharging_storage'): 'b',
               ('heat_pump', 'discharging_storage'): 'b',
               ('charging_storage',): 'g',
               ('discharging_storage',): 'b',
               ('pth_resistive',): 'y',
               ('heat_pump',): 'y',
               (): 'k'}
        return col[sel]

    df['color'] = df.apply(func, axis=1)

    fig = plt.figure(figsize=(10, 10))
    gs = plt.GridSpec(4, 4)

    ax_joint = fig.add_subplot(gs[1:4, 0:3])
    ax_marg_x = fig.add_subplot(gs[0, 0:3], sharex=ax_joint)
    ax_marg_y = fig.add_subplot(gs[1:4, 3], sharey=ax_joint)

    labels = {'y': 'PtH',
              'g': 'charging_storage',
              'b': 'discharging_storage',
              'r': 'error',
              'k': 'only CHP'}

    for name, group in df.groupby('color'):
        ax_joint.scatter(group['supply_heat'],
                         group['supply_electricity'],
                         marker='.',
                         color=group['color'],
                         label=labels[name],
                         s=200,
                         alpha=0.1)

    def plot_operation_range_chp():
        x = np.array([0, capacity_installed_chp])
        backpressure_line = x * param_chp['conversion_factors_bus_el_export'] \
                              / param_chp['conversion_factors_bus_th_central']

        extraction_line = capacity_installed_chp\
                          * param_chp['conversion_factor_full_condensation_bus_el_export'] \
                          / param_chp['conversion_factors_bus_th_central'] \
                          - x * (param_chp['conversion_factor_full_condensation_bus_el_export']
                          - param_chp['conversion_factors_bus_el_export']) \
                          / param_chp['conversion_factors_bus_th_central']
        ax_joint.plot(x, backpressure_line, linewidth=5, c='k', alpha=0.3)
        ax_joint.plot(x, extraction_line, linewidth=5, c='k', alpha=0.3)

    plot_operation_range_chp()

    ax_marg_x.hist(supply_heat.values,
                   bins=80,
                   color='k')

    ax_marg_y.hist(supply_electricity.values,
                   bins=80,
                   color='k',
                   orientation="horizontal")

    # Turn off tick labels on marginals
    plt.setp(ax_marg_x.get_xticklabels(), visible=False)
    plt.setp(ax_marg_y.get_yticklabels(), visible=False)

    # Set labels on joint
    ax_joint.set_xlabel('Joint x label')
    ax_joint.set_ylabel('Joint y label')

    # Set labels on marginals
    ax_marg_y.set_xlabel('Power histogram')
    ax_marg_x.set_ylabel('Heat output histogram')

    ax_joint.grid('x', alpha=0.7)
    ax_joint.set_ylabel('Power in MW')
    ax_joint.set_xlabel('Heat flow in MW')
    legend = ax_joint.legend(loc='upper left', bbox_to_anchor=(1.1, 1.3))
    for lh in legend.legendHandles:
        lh.set_alpha(1)
    plt.tight_layout()
    ax_marg_x.set_title('Electricity vs. heat output {}'.format(label))
    fig.savefig(filename, bbox_inches='tight', dpi=500)
    return None


def plot_demand_heat_vs_price_el(timeseries, price_el, color_dict, label, filename):
    demand_heat = timeseries.loc[:, [key for key in timeseries.columns
                                     if bool(re.search('demand', key[1]))]].sum(axis=1)
    demand_heat.name = 'demand_heat'

    price_el = price_el.iloc[:, 0]
    price_el.index = demand_heat.index
    price_el.name = 'price_electricity'

    heat_output_chp = timeseries.loc[:, [key for key in timeseries.columns
                                       if key[0]=='chp'
                                       and key[1]=='bus_th_central']].sum(axis=1)

    heat_output_chp.name = 'chp'
    heat_output_gas_boiler = timeseries.loc[:, [key for key in timeseries.columns
                                              if key[0] == 'gas_boiler_central']].sum(axis=1)

    heat_output_gas_boiler.name = 'gas_boiler_central'
    heat_output_heat_pump = timeseries.loc[:, [key for key in timeseries.columns
                                             if bool(re.search('_pth_heat_pump_decentral', key[0]))]].sum(axis=1)

    heat_output_heat_pump.name = 'heat_pump'
    heat_output_pth_resistive = timeseries.loc[:, [key for key in timeseries.columns
                                                 if bool(re.search('pth_resistive', key[0]))]].sum(axis=1)

    heat_output_pth_resistive.name = 'pth_resistive'
    discharge_storage = timeseries.loc[:, [key for key in timeseries.columns
                                           if bool(re.search('tes', key[0]))
                                           and key[1]!='None']].sum(axis=1)

    discharge_storage.name = 'discharge_storage'
    charge_storage = timeseries.loc[:, [key for key in timeseries.columns
                                          if bool(re.search('tes', key[1]))]].sum(axis=1)

    charge_storage.name = 'charge_storage'

    df = pd.concat([demand_heat,
                    price_el,
                    heat_output_chp,
                    heat_output_gas_boiler,
                    heat_output_pth_resistive,
                    heat_output_heat_pump,
                    discharge_storage],
                    axis=1)

    fig = plt.figure(figsize=(10, 10))
    gs = plt.GridSpec(4, 4)

    ax_joint = fig.add_subplot(gs[1:4, 0:3])
    ax_marg_x = fig.add_subplot(gs[0, 0:3], sharex=ax_joint)
    ax_marg_y = fig.add_subplot(gs[1:4, 3], sharey=ax_joint)

    ax_joint.scatter(df['demand_heat'],
                     df['price_electricity'],
                     marker='.',
                     # color=df['color'],
                     s=70,
                     edgecolors='none',
                     alpha=0.1)

    color_dict['heat_pump'] = color_dict['pth_heat_pump_decentral']
    color_dict['pth_resistive'] = color_dict['pth_resistive_decentral']
    color_dict['charge_storage'] = '#33a02c',
    color_dict['discharge_storage'] = 'k'

    sort_demand_heat = df.copy()
    sort_demand_heat['demand_heat'] = sort_demand_heat['demand_heat'].round(0)
    sort_demand_heat.set_index('demand_heat').sort_index()
    sort_demand_heat = sort_demand_heat.groupby('demand_heat').agg(sum).iloc[:, 1:6]
    # sort_demand_heat.plot(ax=ax_marg_x,
    #                       alpha=1,
    #                       linewidth=1)
    sort_demand_heat.plot.bar(ax=ax_marg_x,
                          alpha=1,
                          linewidth=1)
    ax_marg_x.legend().remove()

    sort_price_el = df.copy()
    sort_price_el['price_electricity'] = sort_price_el['price_electricity'].round(0)
    sort_price_el.set_index('price_electricity').sort_index()
    sort_price_el = sort_price_el.groupby('price_electricity').agg(sum).iloc[:, 1:6]
    base = plt.gca().transData
    rot = transforms.Affine2D().rotate_deg(90)
    ax_marg_y.plot(sort_price_el,
                   alpha=1,
                   linewidth=1,
                   transform= rot + base)

    # Turn off tick labels on marginals
    plt.setp(ax_marg_x.get_xticklabels(), visible=False)
    plt.setp(ax_marg_y.get_yticklabels(), visible=False)

    # Set labels on marginals
    ax_marg_y.set_xlabel('Heat vs electricity price')
    ax_marg_x.set_ylabel('Heat vs heat demand')
    ax_marg_x.set_title('Electricity price vs. heat demand {}'.format(label))

    ax_joint.grid('x', alpha=0.3)
    ax_joint.set_xlim(0, 120)
    ax_joint.set_ylim(-90, 250)
    ax_joint.set_ylabel('Electricity price [Eur/MWh]')
    ax_joint.set_xlabel('Heat demand [MW]')

    fig.savefig(filename, bbox_inches='tight', dpi=500)
    return None


def plot_heat_vs_heat_demand_and_price_el(timeseries, price_el, color_dict, label, filename):
    demand_heat = timeseries.loc[:, [key for key in timeseries.columns
                                     if bool(re.search('demand', key[1]))]].sum(axis=1)
    demand_heat.name = 'demand_heat'

    price_el = price_el.iloc[:, 0]
    price_el.index = demand_heat.index
    price_el.name = 'price_electricity'

    heat_output_chp = timeseries.loc[:, [key for key in timeseries.columns
                                         if key[0] == 'chp'
                                         and key[1] == 'bus_th_central']].sum(axis=1)

    heat_output_chp.name = 'chp'
    heat_output_gas_boiler = timeseries.loc[:, [key for key in timeseries.columns
                                                if key[0] == 'gas_boiler_central']].sum(axis=1)

    heat_output_gas_boiler.name = 'gas_boiler_central'
    heat_output_heat_pump = timeseries.loc[:, [key for key in timeseries.columns
                                               if bool(re.search('_pth_heat_pump_decentral', key[0]))]].sum(axis=1)

    heat_output_heat_pump.name = 'heat_pump'
    heat_output_pth_resistive = timeseries.loc[:, [key for key in timeseries.columns
                                                   if bool(re.search('pth_resistive', key[0]))]].sum(axis=1)

    heat_output_pth_resistive.name = 'pth_resistive'
    discharge_storage = timeseries.loc[:, [key for key in timeseries.columns
                                           if bool(re.search('tes', key[0]))
                                           and key[1] != 'None']].sum(axis=1)

    discharge_storage.name = 'discharge_storage'
    charge_storage = timeseries.loc[:, [key for key in timeseries.columns
                                        if bool(re.search('tes', key[1]))]].sum(axis=1)

    charge_storage.name = 'charge_storage'

    df = pd.concat([demand_heat,
                    price_el,
                    heat_output_chp,
                    heat_output_gas_boiler,
                    heat_output_pth_resistive,
                    heat_output_heat_pump,
                    discharge_storage],
                   axis=1)

    df.drop(columns=[col for col in df.columns if df[col].sum(axis=0) == 0], inplace=True)
    heat_binned = df.set_index('demand_heat')
    heat_binned.drop(columns='price_electricity', inplace=True)
    heat_binned = heat_binned.groupby(pd.cut(heat_binned.index,
                                             bins=np.arange(0, 150, 5))).sum()

    el_binned = df.set_index('price_electricity')
    el_binned.drop(columns='demand_heat', inplace=True)
    el_binned = el_binned.groupby(pd.cut(el_binned.index,
                                         bins=np.arange(-40, 250, 5))).sum()

    rcParams['font.size'] = 15
    fig, axs = plt.subplots(len(el_binned.columns), 2,
                            figsize=(6, 9))

    color_dict['pth_resistive'] = color_dict['pth_resistive_decentral']
    color_dict['heat_pump'] = color_dict['pth_heat_pump_decentral']
    color_dict['discharge_storage'] = color_dict['tes_central']

    label_dict = {'chp': 'CHP',
                  'gas_boiler_central': 'Gas boiler',
                  'pth_resistive': '',
                  'heat_pump': 'Heat pump',
                  'discharge_storage': 'Discharge storage'}
    n = 10
    ymax = [60000, 20000, 20000, 20000]
    for i, ax in enumerate(axs[:, 0]):
        color = color_dict[heat_binned.columns[i]]
        label = label_dict[heat_binned.columns[i]]
        heat_binned.iloc[:, i].plot.bar(alpha=1,
                                        ax=ax,
                                        width=1,
                                        label=label,
                                        color=color,
                                        linewidth=1,
                                        yticks=np.arange(0, 160000, 20000))
        ax.set_xlabel('Heat output [MW]')
        ax.set_ylabel('Heat [MWh]')
        ax.set_title(label)
        ax.set_ylim(0, ymax[i])

        ax.set_xticklabels([i.mid for i in heat_binned.index])
        ticks = ax.xaxis.get_ticklocs()
        ticklabels = [l.get_text() for l in ax.xaxis.get_ticklabels()]
        ax.xaxis.set_ticks(ticks[::n])
        ax.xaxis.set_ticklabels(ticklabels[::n])

    for i, ax in enumerate(axs[:, 1]):
        color = color_dict[el_binned.columns[i]]
        label = label_dict[el_binned.columns[i]]
        el_binned.iloc[:, i].plot.bar(alpha=1,
                                      ax=ax,
                                      width=1,
                                      color=color,
                                      linewidth=1)

        ax.set_xlabel('Electricity \n price [Eur/MWh]')
        ax.set_ylabel('Heat [MWh]')
        ax.set_title(label)
        ax.set_ylim(0, ymax[i])

        ax.set_xticklabels([i.mid for i in el_binned.index])
        ticks = ax.xaxis.get_ticklocs()
        ticklabels = [l.get_text() for l in ax.xaxis.get_ticklabels()]
        ax.xaxis.set_ticks(ticks[::n])
        ax.xaxis.set_ticklabels(ticklabels[::n])

    for ax in fig.get_axes():
        ax.label_outer()
    plt.tight_layout()
    plt.savefig(filename, dpi=500)
    return None


def plot_heat_feedin_price_el(timeseries, price_el, color_dict, label, filename):
    timeseries = timeseries.round(3)
    produced_pth_resistive = timeseries.loc[:, [key for key in timeseries.columns
                                                if bool(re.search('pth_resistive', key[0]))]].sum(axis=1)
    produced_pth_heat_pump = timeseries.loc[:, [key for key in timeseries.columns
                                               if bool(re.search('heat_pump', key[0]))]].sum(axis=1)
    produced_chp = timeseries.loc[:, [key for key in timeseries.columns
                                      if key[0]== 'chp'
                                      and key[1]=='bus_th_central']]
    produced_gas_boiler = timeseries.loc[:, [key for key in timeseries.columns
                                             if key[0]== 'gas_boiler_central'
                                             and key[1]=='bus_th_central']]
    storage_charge = timeseries.loc[:, [key for key in timeseries.columns
                                        if bool(re.search('bus_th', key[0]))
                                        and bool(re.search('tes', key[1]))]].sum(axis=1)

    storage_discharge = timeseries.loc[:, [key for key in timeseries.columns
                                           if bool(re.search('tes', key[0]))
                                           and bool(re.search('bus_th', key[1]))]].sum(axis=1)

    storage_charge_discharge = storage_charge - storage_discharge
    produced_pth = produced_pth_resistive + produced_pth_heat_pump

    with_pth = (produced_pth.sum()!=0)
    if with_pth:
        n_subplots = 4
    else:
        n_subplots = 3

    fig, axs = plt.subplots(n_subplots, 1, figsize=(6, 8))

    def plot_hist(x, y, ax, ylim=None, title=None):
        y = y.reset_index(drop=True)

        x = x.round(0)
        combine = pd.concat([x, y], axis=1)
        combine = combine.set_index('variable_costs').sort_index()
        combine = combine.groupby('variable_costs').agg(sum)
        combine.plot.area(ax=ax,
                          alpha=1,
                          linewidth=1)
        ax.set_ylabel('Heat flow [MW]')
        ax.set_ylim(ylim)
        ax.set_title(title)
        ax.get_legend().remove()

    axs2 = [ax1.twinx() for ax1 in axs]
    axs[0].scatter(price_el,
                   produced_chp,
                   color='r',
                   alpha=0.01,
                   edgecolors='none',
                   zorder=-1)
    axs[1].scatter(price_el,
                   produced_gas_boiler,
                   color='r',
                   alpha=0.01,
                   edgecolors='none',
                   zorder=-1)
    axs[2].scatter(price_el,
                   storage_charge_discharge,
                   color='r',
                   alpha=0.01,
                   edgecolors='none',
                   zorder=-1)
    if with_pth:
        axs[3].scatter(price_el,
                       produced_pth,
                       color='r',
                       alpha=0.01,
                       edgecolors='none',
                       zorder=-1)

    def center_spines(axis):  # TODO: Is this necessary?
        axis.spines['left'].set_position('zero')
        axis.spines['bottom'].set_position('zero')

    plot_hist(price_el,
              produced_chp,
              axs2[0],
              ylim=(0, 5000),
              title='CHP')
    center_spines(axs2[0])
    plot_hist(price_el,
              produced_gas_boiler,
              axs2[1],
              ylim=(0, 5000),
              title='Gas boiler')
    plot_hist(price_el,
              storage_charge,
              axs2[2])
    plot_hist(price_el,
              -1*storage_discharge,
              axs2[2],
              ylim=(-5000, 5000),
              title='Storage')
    if with_pth:
        plot_hist(price_el,
                  produced_pth,
                  axs2[3],
                  ylim=(0, 5000),
                  title='PtH')
    for ax in axs:
        ax.set_ylim()
        ax.set_ylabel('Heat \n output \n [MW]')

    for ax in axs2:
        center_spines(ax)
        ax.set_xlim(-50, 250)
        ax.set_ylabel('Heat \n [MWh]')
        ax.set_xlabel('Electricity price [Eur/MWh]')

    axs[0].set_title('Heat output vs. electricity price {}'.format(label))
    fig.savefig(filename, bbox_inches='tight', dpi=500)
    return None


def plot_results_scalar_derived(results_scalar_derived, color_dict, label_dict, label, filename):
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
    df = results_scalar_derived.copy()
    df.index = df.index.droplevel([0, 1, 2])
    grouped = df.groupby('var_name', level=1)

    fig = plt.figure()
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
                   label=label_dict[label],
                   bottom=bottom)
            bottom += data.iloc[i].copy()
        ax.set_xticklabels([])
        ax.set_title(group.replace('_','\n')+f' [{unit}]')
        # ax.legend().remove()


    def horizontal_bar(group, ax):
        data = grouped.get_group(group)['var_value']
        data.index = data.index.droplevel([1])
        unit = grouped.get_group(group)['var_unit'][0]
        keys = [re.sub('subnet-._', '', key) for key in data.index]
        labels = [label_dict[label] for label in data.index]
        colors = [color_dict[key] for key in keys]
        data.plot(ax=ax,
                  kind='bar',
                  color=colors)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_title(group+f' [{unit}]')

    ax = fig.add_subplot(gs[:, 0])
    stacked_single_bar('cost_total_system', ax)
    ax.legend(loc='center left', bbox_to_anchor=(0, -0.2))

    ax = fig.add_subplot(gs[:, 1])
    stacked_single_bar('installed_production_capacity', ax)

    ax = fig.add_subplot(gs[:, 2])
    stacked_single_bar('energy_thermal_produced_sum', ax)

    ax = fig.add_subplot(gs[:, 3])
    stacked_single_bar('energy_consumed_sum', ax)

    ax = fig.add_subplot(gs[:, 4])
    stacked_single_bar('emissions_sum', ax)
    ax.set_ylim(0, 150000)
    ax.legend(loc='center left', bbox_to_anchor=(0, -0.2))

    ax = fig.add_subplot(gs[0, 5:])
    horizontal_bar('hours_full_load', ax)
    ax.set_ylim(0, 7000)

    ax = fig.add_subplot(gs[1, 5:])
    horizontal_bar('hours_operating_sum', ax)

    ax = fig.add_subplot(gs[2, 5:])
    horizontal_bar('number_starts', ax)
    ax.set_ylim(0, 7000)

    plt.suptitle('Summary results {}'.format(label))
    gs.tight_layout(fig)
    plt.savefig(filename)

def plot_results_scalar_derived_summary(results_scalar_derived_summary, color_dict, label_dict, filename):
    df = results_scalar_derived_summary.copy()
    df.index = df.index.droplevel([0, 2])
    grouped = df.groupby('var_name')

    def stacked_bar(group, ax):
        data = grouped.get_group(group)['var_value']\
            .unstack(level=1)
        unit = grouped.get_group(group)['var_unit'][0]
        data.plot.bar(ax=ax,
                      stacked=True,
                      color=[color_dict[col] for col in data.columns])
        # ax.set_xticklabels(data.index.get_level_values('scenario'))
        ax.set_xticklabels([2018, 2030, 2050])
        ax.set_title(label_dict[group])
        ax.set_xlabel('Scenario')
        ax.set_ylabel(label_dict[group] + f' [{unit}]')
        ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
        # ax.get_legend().remove()

    def horizontal_bar(group, ax):
        data = grouped.get_group(group)['var_value'].unstack(level=1)
        unit = grouped.get_group(group)['var_unit'][0]
        data.plot.bar(ax=ax,
                      color=[color_dict[col] for col in data.columns])
        # ax.set_xticklabels(data.index.get_level_values('scenario'))
        ax.set_xticklabels([2018, 2030, 2050])
        ax.set_title(label_dict[group])
        if type(unit)!=float:
            ax.set_ylabel(label_dict[group]+f' [{unit}]')
        else:
            ax.set_ylabel(label_dict[group])
        ax.set_xlabel('Scenario')
        ax.get_legend().remove()

    ylim = {'emissions_sum': (0, 130000),
            'number_starts': (0, 600)}
    for i, var in enumerate(['cost_total_system',
                             'installed_production_capacity',
                             'energy_thermal_produced_sum',
                             'energy_consumed_sum',
                             'emissions_sum',
                             'cost_specific_heat']):
        fig = plt.figure(figsize=(6, 5))
        ax = fig.add_subplot()
        stacked_bar(var, ax)
        plt.tight_layout()
        if var in ylim.keys():
            ax.set_ylim(ylim[var])
        f_name = '{0}_{2}.{1}'.format(*filename.split('.', 1) + [var])
        plt.savefig(f_name)

    for j, var in enumerate(['hours_full_load',
                             'hours_operating_sum',
                             'number_starts']):
        fig = plt.figure(figsize=(6, 5))
        ax = fig.add_subplot()
        horizontal_bar(var, ax)
        if var in ylim.keys():
            ax.set_ylim(ylim[var])
        plt.tight_layout()
        f_name = '{0}_{2}.{1}'.format(*filename.split('.', 1) + [var])
        plt.savefig(f_name, dpi=500)
    return None


def scenario_input_overview(parameter_changing, color_dict, filename):
    parameter_changing.index = parameter_changing.index.droplevel(['run_id', 'uncert_sample_id'])
    parameter_changing.reset_index(inplace=True)
    parameter_changing[['year', 'modus']] = parameter_changing.scenario.str.split('_', expand=True)
    parameter_changing = parameter_changing.set_index(['scenario', 'year', 'modus'])

    grouped = parameter_changing.groupby(axis=1, level=0)
    fig, ax = plt.subplots(len(grouped), 1)
    for i, group in enumerate(grouped):
        group[1].plot.bar(ax=ax[i], stacked=True)
        ax[i].set_xticklabels([])
        ax[i].set_title(group[0])
    #parameter_changing.plot.bar(ax=ax)
    #ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
    plt.tight_layout()
    plt.savefig(filename, dpi=500)
    return None


def plot_timeseries_price_el(input_parameter, price_el, filename):
    r"""

    1. Plot: Timeseries of electricity import
    2. Plot: Timeseries of electricity import for flex friendly scenario

    Parameters
    ----------
    input_parameter : pd.DataFrame
    price_el : sequence
    filename : str
    """
    total_price_el = price_el.copy().rename(columns={'variable_costs': 'spot price'})
    total_price_el['tax_levys'] = input_parameter['source_electricity', 'tax_levys']
    total_price_el['network_charges'] = input_parameter['pth_resistive_decentral', 'network_charges_WP']
    total_price_el['spot price'] -= total_price_el['tax_levys'] + total_price_el['network_charges']
    total_price_el = total_price_el[total_price_el.columns[::-1]]

    lb, ub = 2500, 3000

    total_price_el_neg = total_price_el.copy().iloc[lb:ub]
    if input_parameter.name[1].split('_')[1]=='ff':
        total_price_el_neg.loc[:, 'tax_levys'] = input_parameter['source_electricity_flex', 'tax_levys']
        total_price_el_neg.loc[:, 'network_charges'] = 0
    total_price_el_neg.loc[total_price_el['spot price'] > 0] = 0

    total_price_el_pos = total_price_el.copy().iloc[lb:ub]
    total_price_el_pos.loc[total_price_el['spot price'] <= 0] = 0

    fig, ax = plt.subplots(figsize=(12, 6))
    stacked_bar_plot(ax, total_price_el.iloc[lb:ub], ['#c0504d', '#8064a2', '#4f81bd'])
    ax.set_ylim(-90, 150)
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))  # place legend outside of plot
    ax.set_title('Electricity price')
    plt.tight_layout()
    plt.savefig(filename)

    fig, ax = plt.subplots(figsize=(12, 6))
    stacked_bar_plot(ax, total_price_el_pos, color=['#c0504d', '#4bacc6', '#4f81bd'])
    # ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))  # place legend outside of plot
    ax.legend().remove()
    stacked_bar_plot(ax, total_price_el_neg, color=['#c0504d', '#4bacc6', '#4f81bd'])
    ax.set_ylim(-90, 150)

    ax.set_title('Electricity price flex')
    ax.set_ylabel('Electricity price [Eur/MWh]')
    ax.set_xlabel('Time [h]')
    plt.tight_layout()
    filename = filename.split('.')
    filename.insert(1, '_flex.')
    filename  = ''.join(filename)
    plt.savefig(filename, dpi=500)
    return None


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

    with open(os.path.join(abs_path, 'experiment_configs/label_dict.yml'), 'r') as label_file:
        label_dict = yaml.load(label_file)


    # load model_runs
    model_runs = helpers.load_model_runs(results_dir, cfg)
    for index, input_parameter in model_runs.iterrows():
        label = "_".join(map(str, index))
        dir_postproc = os.path.join(results_dir, 'data_postprocessed', label)
        energysystem = solph.EnergySystem()
        energysystem.restore(dpath=os.path.join(results_dir, 'optimisation_results'), filename=f'{label}_es.dump')

        rcParams['figure.figsize'] = [20.0, 10.0]
        rcParams['font.size'] = 15

        param = outputlib.processing.convert_keys_to_strings(energysystem.results['Param'])
        price_el = param['source_electricity', 'bus_el_import']['sequences']
        param_chp = param['chp', 'None']['scalars']
        capacity_installed_chp = param['chp', 'bus_th_central']['scalars']['nominal_value']

        demand_heat = pd.read_csv(os.path.join(results_dir,
                                               'data_preprocessed',
                                               cfg['data_preprocessed']['timeseries']['demand_heat']),
                                  header=0, index_col=0, parse_dates=True)

        timeseries = pd.read_csv(os.path.join(dir_postproc,
                                              cfg['data_postprocessed']['timeseries']['timeseries']),
                                 header=[0,1,2], index_col=0, parse_dates=True)

        results_scalar_derived = pd.read_csv(os.path.join(dir_postproc,
                                                          cfg['data_postprocessed']['scalars']['derived']),
                                             header=0, index_col=[0, 1, 2, 3, 4], parse_dates=True)

        dir_plot = os.path.join(results_dir, 'plots', label)
        if not os.path.exists(dir_plot):
            os.makedirs(os.path.join(dir_plot))

        plot_timeseries_price_el(input_parameter,
                                 price_el,
                                 os.path.join(dir_plot, 'timeseries_price_el.png'))

        plot_heat_demand(demand_heat,
                         label,
                         os.path.join(dir_plot, 'demand_heat.pdf'))
        plot_dispatch(timeseries,
                      '2017-12-10',
                      '2017-12-20',
                      '2017-06-20',
                      '2017-06-30',
                      color_dict,
                      label_dict,
                      label,
                      os.path.join(dir_plot, 'dispatch_stack_plot_summer.png'))
        plot_load_duration_curves(timeseries,
                                  color_dict,
                                  label,
                                  os.path.join(dir_plot, 'load_duration_curves.pdf'))
        plot_storage_level(timeseries,
                           color_dict,
                           label,
                           os.path.join(dir_plot, 'storage_level.pdf'))
        plot_p_q_diagram(timeseries,
                         param_chp,
                         capacity_installed_chp,
                         color_dict,
                         label,
                         os.path.join(dir_plot, 'pq_diagram.png'))
        plot_demand_heat_vs_price_el(timeseries,
                                     price_el,
                                     color_dict,
                                     label,
                                     os.path.join(dir_plot, 'plot_demand_heat_vs_price_el.png'))
        plot_heat_vs_heat_demand_and_price_el(timeseries,
                                              price_el,
                                              color_dict,
                                              label,
                                              os.path.join(dir_plot, 'plot_heat_vs_demand_heat_and_price_el.png'))
        plot_heat_feedin_price_el(timeseries,
                                  price_el,
                                  color_dict,
                                  label,
                                  os.path.join(dir_plot, 'heat_feedin_vs_price_el.pdf'))
        plot_results_scalar_derived(results_scalar_derived,
                                    color_dict,
                                    label_dict,
                                    label,
                                    os.path.join(dir_plot,'results_scalar_derived.pdf'))
        plt.close('all')

    energysystem_graph = nx.readwrite.read_gpickle(os.path.join(results_dir, 'data_plots/energysystem_graph.pkl'))
    draw_graph(energysystem_graph,
               plot=False,
               store=True,
               filename=os.path.join(results_dir, 'plots', 'es_graph.pdf'),
               node_size=5000, edge_color='k',
               node_color=color_dict)

    results_scalar_derived_all = pd.read_csv(os.path.join(results_dir,
                                                          'data_postprocessed',
                                                          'results_scalar_derived_all.csv'),
                                             header=0, index_col=[0, 1, 2, 3, 4])
    print(results_scalar_derived_all)
    results_scalar_derived_sq  = results_scalar_derived_all.loc[(slice(None),
                                                                ['hp-2018_sq', 'hp-2030_sq', 'hp-2050_sq'],
                                                                slice(None),
                                                                slice(None),
                                                                slice(None)), :]
    plot_results_scalar_derived_summary(results_scalar_derived_sq,
                                        color_dict,
                                        label_dict,
                                        os.path.join(results_dir, 'plots', 'results_scalar_derived_sq.png'))

    results_scalar_derived_ff  = results_scalar_derived_all.loc[(slice(None),
                                                                ['hp-2018_ff', 'hp-2030_ff', 'hp-2050_ff'],
                                                                slice(None),
                                                                slice(None),
                                                                slice(None)), :]
    plot_results_scalar_derived_summary(results_scalar_derived_ff,
                                        color_dict,
                                        label_dict,
                                        os.path.join(results_dir, 'plots', 'results_scalar_derived_ff.png'))

    results_scalar_derived_all.sort_index(inplace=True, level=1)
    print(results_scalar_derived_all)
    plot_results_scalar_derived_summary(results_scalar_derived_all,
                                        color_dict,
                                        label_dict,
                                        os.path.join(results_dir, 'plots', 'results_scalar_derived_all.png'))

    # parameter_changing = pd.read_csv(os.path.join(results_dir,
    #                                               'data_preprocessed',
    #                                               cfg['data_preprocessed']['scalars']['parameters_changing']),
    #                                  index_col=[0, 1, 2], header=[0, 1])
    # scenario_input_overview(parameter_changing,
    #                         color_dict,
    #                         os.path.join(results_dir, 'plots', 'scenario_input_overview.pdf'))

if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    create_plots(config_path, results_dir)

