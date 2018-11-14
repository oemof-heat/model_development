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

import logging
import pandas as pd
import pprint as pp

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

energysystem = solph.EnergySystem()
energysystem.restore(dpath='dumps',
                     filename='Oman.oemof')

start_of_plot = 000
end_of_plot = 100
sp = start_of_plot
ep = end_of_plot

results_strings = outputlib.views.convert_keys_to_strings(energysystem.results['main'])
print(energysystem.results['meta'])
thermal_bus = outputlib.views.node(energysystem.results['main'], 'thermal')
print(thermal_bus)
print(outputlib.views.node(energysystem.results['main'], 'thermal')['sequences'][(('storage_thermal', 'thermal'), 'flow')])
print(outputlib.views.node(energysystem.results['main'], 'thermal')['scalars'])
# print(outputlib.views.node(energysystem.results['main'], 'cool')['sequences'][(('cool', 'demand'), 'flow')])
# print(outputlib.views.node(energysystem.results['main'], 'storage_thermal'))
logging.info('results received')

#########################
# Work with the results #
#########################


thermal_bus = outputlib.views.node(energysystem.results['main'], 'cool')

thermal_seq = thermal_bus['sequences']

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
    (('solar', 'thermal_high'), 'flow'): '#ffde32',
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
#
# fig = plt.figure(figsize=(20, 20))
#
# # plot thermal energy, high temperature
# thermal_seq_resample = thermal_seq.iloc[sp:ep]
# my_plot_th = oev.plot.io_plot(
#         'thermal_high', thermal_seq_resample, cdict=cdict,
#         ax=fig.add_subplot(4, 1, 1), smooth=False)
#
# ax_thh = shape_legend('thermal_high', **my_plot_th)
# oev.plot.set_datetime_ticks(ax_thh, thermal_seq_resample.index, tick_distance=148,
#                             date_format='%d-%m-%H', offset=1)
#
# ax_thh.set_ylabel('Power in kW')
# ax_thh.set_xlabel('2017')
# ax_thh.set_title("thermal bus")