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
energysystem.restore(dpath="C:\Git_clones\oemof_heat\Dumps",
                     filename="MED_CSP_20180430-1417.oemof")

start_of_plot = 000
end_of_plot = 500
sp = start_of_plot
ep = end_of_plot

results_strings = outputlib.views.convert_keys_to_strings(energysystem.results['main'])

logging.info('results received')

#########################
# Work with the results #
#########################

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