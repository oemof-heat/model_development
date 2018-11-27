# -*- coding: utf-8 -*-
"""
Created on Wed Mar 21 11:01:57 2018

@author: Franziska Pleissner

File to plot and process the results from the example
"""

import oemof.solph as solph
import oemof.outputlib as outputlib
import pickle
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, YearLocator, MonthLocator
import matplotlib
import oemof_visio as oev
import pprint as pp

energysystem = solph.EnergySystem()
energysystem.restore(dpath="C:\Git_clones\oemof_heat\Dumps", filename="RO_PV.oemof")
timeframe_to_plot=24*7

water_bus = outputlib.views.node(energysystem.results['main'], 'water')
electricity_bus = outputlib.views.node(energysystem.results['main'], 'electricity')


def shape_legend(node, reverse=False, **kwargs):
    handels = kwargs['handles']
    labels = kwargs['labels']
    axes = kwargs['ax']
    parameter = {}

    new_labels = []
    for label in labels:
        label = label.replace('(', '')
        label = label.replace('), flow)', '')
        label = label.replace(node, '')
        label = label.replace(',', '')
        label = label.replace(' ', '')
        new_labels.append(label)
    labels = new_labels

    parameter['bbox_to_anchor'] = kwargs.get('bbox_to_anchor', (1, 0.5))
    parameter['loc'] = kwargs.get('loc', 'center left')
    parameter['ncol'] = kwargs.get('ncol', 1)
    plotshare = kwargs.get('plotshare', 0.9)

    if reverse:
        handels = handels.reverse()
        labels = labels.reverse()

    box = axes.get_position()
    axes.set_position([box.x0, box.y0, box.width * plotshare, box.height])

    parameter['handles'] = handels
    parameter['labels'] = labels
    axes.legend(**parameter)
    return axes


# define colours
cdict = {
    (('electricity', 'excess'), 'flow'): '#555555',
    (('electricity', 'storageel'), 'flow'): '#42c77a',
    (('electricity', 'pp_wat'), 'flow'): '#0000ff',
    (('pvel', 'electricity'), 'flow'): '#ffde32',
    (('storageel', 'electricity'), 'flow'): '#42c77a',
    (('shortage', 'electricity'), 'flow'): '#ff0000',
    (('water', 'excesswat'), 'flow'): '#555555',
    (('water', 'demand'), 'flow'): '#ff0000',
    (('pp_wat', 'water'), 'flow'): '#87ceeb',
    (('storagewat', 'water'), 'flow'): '#42c77a',
    (('water', 'storagewat'), 'flow'): '#ffde32'}

# define order of inputs and outputs
inorder = [(('pvel', 'electricity'), 'flow'),
           (('storageel', 'electricity'), 'flow'),
           (('shortage', 'electricity'), 'flow')]
outorder = [(('electricity', 'pp_wat'), 'flow'),
            (('electricity', 'storageel'), 'flow'),
            (('electricity', 'excess'), 'flow')]

fig = plt.figure(figsize=(10, 10))

# Electricity Plot
electricity_seq = electricity_bus['sequences']
electricity_seq_resample=electricity_seq.head(timeframe_to_plot).resample('D').mean()
my_plot = oev.plot.io_plot(
        'electricity', electricity_seq_resample, cdict=cdict, inorder=inorder,
        outorder=outorder, ax=fig.add_subplot(2, 1, 1), smooth=True)

ax_elec = shape_legend('electricity', **my_plot)
oev.plot.set_datetime_ticks(ax_elec, electricity_seq_resample.index, tick_distance=1,
                            date_format='%d-%m-%H', offset=0)

ax_elec.set_ylabel('Power in kW')
ax_elec.set_xlabel('2017')
ax_elec.set_title("Electricity bus")

# Water Plot
inorder = [(('pp_wat', 'water'), 'flow'),
           (('storagewat', 'water'), 'flow')]

water_seq = water_bus['sequences']
water_seq_resample=water_seq.head(timeframe_to_plot) #.resample('D').mean()
my_plot_wat = oev.plot.io_plot('water', water_seq_resample, cdict=cdict,
                               inorder=inorder, ax=fig.add_subplot(2, 1, 2),
                               smooth=False)
ax = shape_legend('water', **my_plot_wat)
oev.plot.set_datetime_ticks(ax, water_seq_resample.index, tick_distance=48,
                            date_format='%d-%m-%H', offset=12)

ax.set_ylabel('Water in m3/h')
ax.set_xlabel('2017')
ax.set_title("Water bus")

plt.tight_layout()

### print values ### 

results_water = water_bus['scalars']
results_electricity = electricity_bus['scalars']

# add installed capacity of storages to the results
results_strings = outputlib.views.convert_keys_to_strings(energysystem.results['main'])
print(results_strings.keys())

results_water['storage_invest_m3'] = (results_strings[('storagewat', 'None')]['scalars']
                                      ['invest'])
results_electricity['storage_invest_MWh'] = (results_strings[('storageel', 'None')]
                                             ['scalars']['invest']/1e3)

pp.pprint(results_water)
pp.pprint(results_electricity)


grid = results_strings[('shortage', 'electricity')]['sequences'].sum()
sold_electricity = results_strings[('electricity', 'excess')]['sequences'].sum()
water_excess = results_strings[('water', 'excesswat')]['sequences'].sum()
water_demand = results_strings[('water', 'demand')]['sequences'].sum()
portion_water_excess = water_excess/(water_excess+water_demand)

print("zugekaufter Strom: %i" % grid)
print("verkaufter Strom: %i" % sold_electricity)
print("Überschüssiges Wasser: %i" % water_excess)
print("Wasserbedarf: %i" % water_demand)
print("Anteil des überschüssigen Wassers: %f" % portion_water_excess)

### Print results in csv  ###

water_seq.to_csv('data_output/RO_PV_results_wat.csv')
electricity_seq.to_csv('data_output/RO_PV_results_electricity.csv')