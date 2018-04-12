# -*- coding: utf-8 -*-
"""
Created on Wed Mar  7 11:01:36 2018

@author: Franziska Pleissner

System C: concrete example: Plot of the desalination with multi effect
desalination and concentrating solar power plant
"""

############
# Preamble #
############

# Import packages
from oemof.tools import logger
import oemof.solph as solph

import oemof.outputlib as outputlib
import oemof_visio as oev

import logging
import pandas as pd
import pprint as pp

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

energysystem = solph.EnergySystem()
energysystem.restore(dpath="C:\Git_clones\oemof_heat\Dumps",
                     filename="MED_CSP.oemof")

results_strings = outputlib.views.convert_keys_to_strings(energysystem.results['main'])
#print(results_strings.keys())
water_bus = outputlib.views.node(energysystem.results['main'], 'water')
electricity_bus = outputlib.views.node(energysystem.results['main'], 'electricity')
thermalh_bus = outputlib.views.node(energysystem.results['main'], 'thermal_high')
thermall_bus = outputlib.views.node(energysystem.results['main'], 'thermal_low')

logging.info('results received')

#########################
# Work with the results #
#########################

water_seq = water_bus['sequences']
electricity_seq = electricity_bus['sequences']
thermalh_seq = thermalh_bus['sequences']
thermall_seq = thermall_bus['sequences']

# print(water_bus.keys())
# print(electricity_seq.head(5))
water_scal = water_bus['scalars']
electricity_scal = electricity_bus['scalars']
thermalh_scal = thermalh_bus['scalars']
thermall_scal = thermall_bus['scalars']

### Plot results ###


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

cdict = {
    (('Collector', 'thermal_high'), 'flow'): '#ffde32',
    (('thermal_high', 'storage_thh'), 'flow'): '#555555',
    (('storage_thh', 'thermal_high'), 'flow'): '#555555',
    (('thermal_high', 'PB'), 'flow'): '#ff0000',
    (('thermal_high', 'TT'), 'flow'): '#87ceeb',
    (('PB', 'electricity'), 'flow'): '#ffde32',
    (('electricity', 'storageel'), 'flow'): '#42c77a',
    (('storageel', 'electricity'), 'flow'): '#42c77a',
    (('electricity', 'Desal'), 'flow'): '#0000ff',
    (('electricity', 'elec_output'), 'flow'): '#555555',
    (('PB', 'thermal_low'), 'flow'): '#ff0000',
    (('TT', 'thermal_low'), 'flow'): '#ffde32',
    (('thermal_low', 'Desal'), 'flow'): '#0000ff',
    (('Desal', 'water'), 'flow'): '#87ceeb',
    (('storagewat', 'water'), 'flow'): '#42c77a',
    (('water', 'storagewat'), 'flow'): '#42c77a',
    (('water', 'demand'), 'flow'): '#ff0000'}

# define order of inputs and outputs
inorderthh = [(('Collector', 'thermal_high'), 'flow'),
              (('storage_thh', 'thermal_high'), 'flow'),
              (('thh_shortage', 'thermal_high'), 'flow')]
outorderthh = [(('thermal_high', 'PB'), 'flow'),
               (('thermal_high', 'storage_thh'), 'flow'),
               (('thermal_high', 'TT'), 'flow')]
inorderel = [(('grid', 'electricity'), 'flow'),
             (('PB', 'electricity'), 'flow'),
             (('storageel', 'electricity'), 'flow')]
outorderel = [(('electricity', 'Desal'), 'flow'),
              (('electricity', 'storageel'), 'flow'),
              (('electricity', 'elec_output'), 'flow')]
inorderthl = [(('PB', 'thermal_low'), 'flow'),
              (('TT', 'thermal_low'), 'flow')]
outorderthl = [(('thermal_low', 'Desal'), 'flow')]
inorderwat = [(('Wat_shortage', 'water'), 'flow'),
              (('Desal', 'water'), 'flow'),
              (('storagewat', 'water'), 'flow')]
outorderwat = [(('water', 'demand'), 'flow'),
               (('water', 'storagewat'), 'flow'),
               (('water', 'excesswat'), 'flow')]

fig = plt.figure(figsize=(10, 20))

# plot thermal energy, high temperature
my_plot_thh = oev.plot.io_plot(
        'thermal_high', thermalh_seq, cdict=cdict, inorder=inorderthh,
        outorder=outorderthh, ax=fig.add_subplot(4, 1, 1), smooth=False)

ax_thh = shape_legend('thermal_high', **my_plot_thh)
oev.plot.set_datetime_ticks(ax_thh, thermalh_seq.index, tick_distance=48,
                            date_format='%d-%m-%H', offset=12)

ax_thh.set_ylabel('Power in kW')
ax_thh.set_xlabel('2017')
ax_thh.set_title("thermal bus high temperature")

# plot electric energy
my_plot_el = oev.plot.io_plot(
        'electricity', electricity_seq, cdict=cdict, inorder=inorderel,
        outorder=outorderel, ax=fig.add_subplot(4, 1, 2), smooth=False)

ax_el = shape_legend('electricity', **my_plot_el)
oev.plot.set_datetime_ticks(ax_el, electricity_seq.index, tick_distance=48,
                            date_format='%d-%m-%H', offset=12)

ax_el.set_ylabel('Power in kW')
ax_el.set_xlabel('2017')
ax_el.set_title("Electricity bus")

# plot thermal energy, low temperature
my_plot_thl = oev.plot.io_plot(
        'thermal_low', thermall_seq, cdict=cdict, inorder=inorderthl,
        outorder=outorderthl, ax=fig.add_subplot(4, 1, 3), smooth=False)

ax_thl = shape_legend('thermal_low', **my_plot_thl)
oev.plot.set_datetime_ticks(ax_thl, thermall_seq.index, tick_distance=48,
                            date_format='%d-%m-%H', offset=12)

ax_thl.set_ylabel('Power in kW')
ax_thl.set_xlabel('2017')
ax_thl.set_title("thermal bus low temperature")

# plot water
my_plot_wat = oev.plot.io_plot(
        'water', water_seq, cdict=cdict, inorder=inorderwat,
        outorder=outorderwat, ax=fig.add_subplot(4, 1, 4), smooth=False)

ax_wat = shape_legend('water', **my_plot_wat)
oev.plot.set_datetime_ticks(ax_wat, water_seq.index, tick_distance=48,
                            date_format='%d-%m-%H', offset=12)

ax_wat.set_ylabel('Amount of water in m3/h')
ax_wat.set_xlabel('2017')
ax_wat.set_title("water bus")

### Print values ###

print(thermalh_scal)
print(water_scal)
print(electricity_scal)
print(thermall_scal)

### Write results in csv ###