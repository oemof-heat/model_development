# -*- coding: utf-8 -*-
"""
Created on Wed May  2 11:54:15 2018

@author: Franziska Pleissner

System C: concrete example: Plot ocooling process with a solar collector
"""

############
# Preamble #
############

# Import packages
from oemof.tools import logger
import oemof.solph as solph

import oemof.outputlib as outputlib
import oemof_visio as oev

import os
import logging
import pandas as pd
import pprint as pp

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

energysystem = solph.EnergySystem()
energysystem.restore(dpath=(abs_path + '/dumps'),
                     filename='Oman_thermal.oemof')

start_of_plot = 0
end_of_plot = 100
sp = start_of_plot
ep = end_of_plot

results_strings = outputlib.views.convert_keys_to_strings(energysystem.results['main'])
# print(energysystem.results['meta'])
thermal_bus = outputlib.views.node(energysystem.results['main'], 'thermal')
# print(thermal_bus)
#print(outputlib.views.node(energysystem.results['main'], 'thermal')['sequences'][(('thermal', 'absorption_chiller'), 'flow')])
print(outputlib.views.node(energysystem.results['main'], 'thermal')['scalars'])
print(outputlib.views.node(energysystem.results['main'], 'cool')['scalars'])
# print(outputlib.views.node(energysystem.results['main'], 'cool')['sequences'][(('cool', 'demand'), 'flow')])
# print(outputlib.views.node(energysystem.results['main'], 'storage_thermal'))
logging.info('results received')

#########################
# Work with the results #
#########################


thermal_bus = outputlib.views.node(energysystem.results['main'], 'thermal')
cool_bus = outputlib.views.node(energysystem.results['main'], 'cool')
waste_bus = outputlib.views.node(energysystem.results['main'], 'waste')
el_bus = outputlib.views.node(energysystem.results['main'], 'electricity')
gas_bus = outputlib.views.node(energysystem.results['main'], 'gas')
storage_cool_res = outputlib.views.node(energysystem.results['main'], 'storage_cool')

thermal_seq = thermal_bus['sequences']
cool_seq = cool_bus['sequences']
waste_seq = waste_bus['sequences']
el_seq = el_bus['sequences']
gas_seq = gas_bus['sequences']
storage_cool_seq = storage_cool_res['sequences']

print(type(thermal_seq))
print(thermal_seq.index)
print(thermal_seq.columns)
#print(thermal_seq['2017-01-01 00:00:00'])
#print(type(thermal_seq[(('boiler', 'thermal'), 'flow')]))
#print(thermal_seq[(('boiler', 'thermal'), 'flow')])
mydf = pd.DataFrame()
mydf[('boiler', 'thermal'), 'flow'] = thermal_seq[(('boiler', 'thermal'), 'flow')]
mydf.append(thermal_seq, ignore_index=True, sort=True)

mydf3=pd.merge(thermal_seq, cool_seq, left_index=True, right_index=True)
print(mydf3.index)
print(mydf3.columns)

mydf3.to_csv(abs_path + '/test2.csv')

########################
# Plotting the results #
########################

cool_seq_resample = cool_seq.iloc[sp:ep]
thermal_seq_resample = thermal_seq.iloc[sp:ep]
waste_seq_resample = waste_seq.iloc[sp:ep]
el_seq_resample = el_seq.iloc[sp:ep]
gas_seq_resample = gas_seq.iloc[sp:ep]
storage_cool_seq_resample = storage_cool_seq.iloc[sp:ep]


def shape_legend(node, reverse=False, **kwargs):  # just copied
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

    parameter['bbox_to_anchor'] = kwargs.get('bbox_to_anchor', (1, 1))
    parameter['loc'] = kwargs.get('loc', 'upper left')
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


cdict = {
    (('collector', 'thermal'), 'flow'): '#ffde32',
    (('boiler', 'thermal'), 'flow'): '#ff0000',
    (('thermal', 'absorpion_chiller'), 'flow'): '#4682b4',
    (('thermal', 'storage_thermal'), 'flow'): '#9acd32',
    (('storage_thermal', 'thermal'), 'flow'): '#9acd32',
    (('grid_el', 'electricity'), 'flow'): '#999999',
    (('pv', 'electricity'), 'flow'): '#ffde32',
    (('storage_electricity', 'electricity'), 'flow'): '#9acd32',
    (('electricity', 'storage_electricity'), 'flow'): '#9acd32',
#    (('electricity', 'compression_chiller'), 'flow'): '#87ceeb',
#    (('electricity', 'el_output'), 'flow'): '#555555',
    (('electricity', 'cooling_tower'), 'flow'): '#ff0000',
#    (('compression_chiller', 'cool'), 'flow'): '#87ceeb',
    (('absorpion_chiller', 'cool'), 'flow'): '#4682b4',
    (('shortage', 'cool'), 'flow'): '#555555',
    (('cool', 'demand'), 'flow'): '#cd0000',
    (('cool', 'storage_cool'), 'flow'): '#9acd32',
    (('storage_cool', 'None'), 'capacity'): '#555555',
    (('storage_cool', 'cool'), 'flow'): '#9acd32',
    (('naturalgas', 'gas'), 'flow'): '#42c77a',
    (('gas', 'boiler'), 'flow'): '#42c77a',
#    (('compression_chiller', 'waste'), 'flow'): '#87ceeb',
    (('absorpion_chiller', 'waste'), 'flow'): '#4682b4',
    (('waste', 'cool_tower'), 'flow'): '#42c77a'}


# define order of inputs and outputs
inorderstor = [(('cool', 'storage_cool'), 'flow')]
outorderstor = [(('storage_cool', 'cool'), 'flow'),
                (('storage_cool', 'None'), 'capacity')]
inordercool = [(('absorpion_chiller', 'cool'), 'flow'),
#               (('compression_chiller', 'cool'), 'flow'),
               (('storage_cool', 'cool'), 'flow'),
               (('shortage', 'cool'), 'flow')]
outordercool = [(('cool', 'demand'), 'flow'),
                (('cool', 'storage_cool'), 'flow')]
inorderel = [(('pv', 'electricity'), 'flow'),
             (('storage_el', 'electricity'), 'flow'),
             (('el_grid', 'electricity'), 'flow')]
outorderel = [#(('electricity', 'compression_chiller'), 'flow'),
              (('electricity', 'storage_electricity'), 'flow'),
              (('electricity', 'cooling_tower'), 'flow')]
#              (('electricity', 'el_output'), 'flow')]
inorderthermal = [(('collector', 'thermal'), 'flow'),
                  (('storage_thermal', 'thermal'), 'flow'),
                  (('boiler', 'thermal'), 'flow')]
outorderthermal = [(('thermal', 'absorption_chiller'), 'flow'),
                   (('thermal', 'storage_thermal'), 'flow')]

fig = plt.figure(figsize=(15, 15))

# plot cooling energy
my_plot_cool = oev.plot.io_plot(
        'cool', cool_seq_resample, cdict=cdict,
        inorder=inordercool, outorder=outordercool,
        ax=fig.add_subplot(2, 2, 1), smooth=False)

ax_cool = shape_legend('cool', **my_plot_cool)
oev.plot.set_datetime_ticks(ax_cool, cool_seq_resample.index, tick_distance=14,
                            date_format='%d-%m-%H', offset=1)

ax_cool.set_ylabel('Power in kW')
ax_cool.set_xlabel('time')
ax_cool.set_title("cool")

# plot thermal energy
my_plot_thermal = oev.plot.io_plot(
        'thermal', thermal_seq_resample, cdict=cdict,
        inorder=inorderthermal, outorder=outorderthermal,
        ax=fig.add_subplot(2, 2, 2), smooth=False)

ax_thermal = shape_legend('thermal', **my_plot_thermal)
oev.plot.set_datetime_ticks(ax_thermal, thermal_seq_resample.index, tick_distance=14,
                            date_format='%d-%m-%H', offset=1)

ax_thermal.set_ylabel('Power in kW')
ax_thermal.set_xlabel('time')
ax_thermal.set_title("thermal")

# plot electric energy
my_plot_el = oev.plot.io_plot(
        'electricity', el_seq_resample, cdict=cdict,
        inorder=inorderel, outorder=outorderel,
        ax=fig.add_subplot(2, 2, 3), smooth=False)

ax_el = shape_legend('electricity', **my_plot_el)
oev.plot.set_datetime_ticks(ax_el, el_seq_resample.index, tick_distance=14,
                            date_format='%d-%m-%H', offset=1)

ax_el.set_ylabel('Power in kW')
ax_el.set_xlabel('time')
ax_el.set_title("electricity")


def shape_legend_stor(node, reverse=False, **kwargs):  # just copied
    handels = kwargs['handles']
    labels = kwargs['labels']
    axes = kwargs['ax']
    parameter = {}

    new_labels = []
    for label in labels:
        label = label.replace('(', '')
        label = label.replace('), flow)', '')
        label = label.replace('None', '')
        label = label.replace(')', '')
        label = label.replace('_'+str(node), '')
        label = label.replace(node, '')
        label = label.replace(',', '')
        label = label.replace(' ', '')
        label = label.replace('cool', 'input/output')
        if label not in new_labels:
            new_labels.append(label)
    labels = new_labels

    parameter['bbox_to_anchor'] = kwargs.get('bbox_to_anchor', (1, 1))
    parameter['loc'] = kwargs.get('loc', 'upper left')
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


# plot storage capacity
my_plot_stor = oev.plot.io_plot(
        'storage_cool', storage_cool_seq_resample, cdict=cdict,
        inorder=inorderstor, outorder=outorderstor,
        ax=fig.add_subplot(2, 2, 4), smooth=False)

ax_stor = shape_legend_stor('storage_cool', **my_plot_stor)
oev.plot.set_datetime_ticks(ax_stor, storage_cool_seq_resample.index,
                            tick_distance=14,
                            date_format='%d-%m-%H', offset=1)

ax_stor.set_ylabel('Power in kW and capacity in kWh')
ax_stor.set_xlabel('time')
ax_stor.set_title("cooling storage")

plt.show()
