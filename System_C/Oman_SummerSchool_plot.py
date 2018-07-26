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

data = pd.read_csv('data_input/Oman3.csv', sep=';',)

energysystem = solph.EnergySystem()
energysystem.restore(dpath="C:\Git_clones\oemof_heat\Dumps",
                     filename="Oman_SS20180726-1613.oemof")

sp = start_of_plot = 0
ep = end_of_plot = 50

results_strings = outputlib.views.convert_keys_to_strings(energysystem.results['main'])
# print(energysystem.results)
print(results_strings.keys())
logging.info('results received')

#########################
# Work with the results #
#########################

cool_bus = outputlib.views.node(energysystem.results['main'], 'cool')
heat_bus = outputlib.views.node(energysystem.results['main'], 'heat')
waste_bus = outputlib.views.node(energysystem.results['main'], 'waste')
el_bus = outputlib.views.node(energysystem.results['main'], 'electricity')
gas_bus = outputlib.views.node(energysystem.results['main'], 'gas')

cool_seq = cool_bus['sequences']
heat_seq = heat_bus['sequences']
waste_seq = waste_bus['sequences']
el_seq = el_bus['sequences']
gas_seq = gas_bus['sequences']

cool_seq_resample = cool_seq.iloc[sp:ep]
heat_seq_resample = heat_seq.iloc[sp:ep]
waste_seq_resample = waste_seq.iloc[sp:ep]
el_seq_resample = el_seq.iloc[sp:ep]
gas_seq_resample = gas_seq.iloc[sp:ep]

### Calculate and show results ###

Cooling_demand = results_strings[('cool', 'cool_demand')]['sequences'].sum()
Ergebnisse_KKM = results_strings[('compression_chiller', 'cool')]['sequences']
Cooling_from_CCM = Ergebnisse_KKM.sum()
Betriebsstunden_KKM = Ergebnisse_KKM[Ergebnisse_KKM['flow'] > 0.01].count()
Ergebnisse_AKM = results_strings[('absorpion_chiller', 'cool')]['sequences']
Cooling_from_ACM = Ergebnisse_AKM.sum()
Betriebsstunden_AKM = Ergebnisse_AKM[Ergebnisse_AKM['flow'] > 0.01].count()
Demand = data['Cooling load kW'][sp:ep].sum()
Anteil = Cooling_demand/Demand
Anteil_CCM = Cooling_from_CCM/Cooling_demand
Anteil_ACM = Cooling_from_ACM/Cooling_demand
gas_verb = results_strings[('naturalgas', 'gas')]['sequences'].sum()
Strom_Input = results_strings[('el_grid', 'electricity')]['sequences'].sum()
Strom_Output = results_strings[('electricity', 'el_output')]['sequences'].sum()
Strom_Diff = Strom_Input-Strom_Output
if Strom_Output.all() != 0:
    Strombilanz = Strom_Input/Strom_Output
else:
    Strombilanz = 0



print("Bedarf: %f" % Demand)
# print("gedeckter Bedarf: %f" % Cooling_demand)
print("Anteil des Bedarfs, der gedeckt wird: %f" % Anteil)
# print("durch KKM gedeckter Bedarf: %f" % Cooling_from_CCM)
# print("durch AKM gedeckter Bedarf: %f" % Cooling_from_ACM)
print("Anteil KKM am gedeckten Bedarf: %f" % Anteil_CCM)
print("Anteil AKM am gedeckten Bedarf: %f" % Anteil_ACM)
print("Betriebsstunden KKM: %f" % Betriebsstunden_KKM)
print("Betriebsstunden AKM: %f" % Betriebsstunden_AKM)
print("verbrauchtes Gas: %f" % gas_verb)
print("Strom rein: %f" % Strom_Input)
print("Strom raus: %f" % Strom_Output)
print("Strom Differenz: %f" % Strom_Diff)
print("Strom Bilanz: %f" % Strombilanz)



### Print results in csv  ###

cool_seq.to_csv('data_output/results.csv')

### Plot results ###
#
#
#def shape_legend(node, reverse=False, **kwargs):  # just copied
#    handels = kwargs['handles']
#    labels = kwargs['labels']
#    axes = kwargs['ax']
#    parameter = {}
#
#    new_labels = []
#    for label in labels:
#        label = label.replace('(', '')
#        label = label.replace('), flow)', '')
#        label = label.replace(node, '')
#        label = label.replace(',', '')
#        label = label.replace(' ', '')
#        new_labels.append(label)
#    labels = new_labels
#
#    parameter['bbox_to_anchor'] = kwargs.get('bbox_to_anchor', (1, 0.5))
#    parameter['loc'] = kwargs.get('loc', 'center left')
#    parameter['ncol'] = kwargs.get('ncol', 1)
#    plotshare = kwargs.get('plotshare', 0.9)
#
#    if reverse:
#        handels = handels.reverse()
#        labels = labels.reverse()
#
#    box = axes.get_position()
#    axes.set_position([box.x0, box.y0, box.width * plotshare, box.height])
#
#    parameter['handles'] = handels
#    parameter['labels'] = labels
#    axes.legend(**parameter)
#    return axes
#
#cdict = {
#    (('collector', 'heat'), 'flow'): '#ffde32',
#    (('boiler', 'heat'), 'flow'): '#ff0000',
#    (('heat', 'chiller'), 'flow'): '#ff0000',
#    (('heat', 'storage_heat'), 'flow'): '#555555',
#    (('storage_heat', 'heat'), 'flow'): '#555555',
#    (('el_grid', 'electricity'), 'flow'): '#87ceeb',
#    (('pv', 'electricity'), 'flow'): '#ffde32',
#    (('electricity', 'storage_el'), 'flow'): '#42c77a',
#    (('storage_el', 'electricity'), 'flow'): '#42c77a',
#    (('electricity', 'el_output'), 'flow'): '#555555',
#    (('compression_chiller', 'cool'), 'flow'): '#ff0000',
#    (('absorpion_chiller', 'cool'), 'flow'): '#87ceeb',
#    (('cool', 'demand'), 'flow'): '#ffde32',
#    (('cool', 'storage_cool'), 'flow'): '#0000ff',
#    (('storage_cool', 'cool'), 'flow'): '#87ceeb',
#    (('naturalgas', 'gas'), 'flow'): '#42c77a',
#    (('gas', 'boiler'), 'flow'): '#42c77a',
#    (('chiller', 'waste'), 'flow'): '#ff0000',
#    (('waste', 'cool_tower'), 'flow'): '#42c77a'}
#
## define order of inputs and outputs
#
#fig = plt.figure(figsize=(20, 20))
#
## plot cooling energy
#my_plot_cool = oev.plot.io_plot(
#        'cool', cool_seq_resample, cdict=cdict,
#        ax=fig.add_subplot(3, 2, 1), smooth=False)
#
#ax_cool = shape_legend('cool', **my_plot_cool)
#oev.plot.set_datetime_ticks(ax_cool, cool_seq_resample.index, tick_distance=148,
#                            date_format='%d-%m-%H', offset=1)
#
#ax_cool.set_ylabel('Power in kW')
#ax_cool.set_xlabel('2017')
#ax_cool.set_title("cooling bus")
#
## plot heat energy
#my_plot_heat = oev.plot.io_plot(
#        'heat', heat_seq_resample, cdict=cdict,
#        ax=fig.add_subplot(3, 2, 2), smooth=False)
#
#ax_heat = shape_legend('heat', **my_plot_heat)
#oev.plot.set_datetime_ticks(ax_heat, heat_seq_resample.index, tick_distance=148,
#                            date_format='%d-%m-%H', offset=1)
#
#ax_heat.set_ylabel('Power in kW')
#ax_heat.set_xlabel('2017')
#ax_heat.set_title("heating bus")
#
## plot waste heat energy
#my_plot_waste = oev.plot.io_plot(
#        'waste', waste_seq_resample, cdict=cdict,
#        ax=fig.add_subplot(3, 2, 3), smooth=False)
#
#ax_waste = shape_legend('waste', **my_plot_waste)
#oev.plot.set_datetime_ticks(ax_waste, waste_seq_resample.index, tick_distance=148,
#                            date_format='%d-%m-%H', offset=1)
#
#ax_waste.set_ylabel('Power in kW')
#ax_waste.set_xlabel('2017')
#ax_waste.set_title("waste heat bus")
#
## plot electric energy
#my_plot_el = oev.plot.io_plot(
#        'electricity', el_seq_resample, cdict=cdict,
#        ax=fig.add_subplot(3, 2, 4), smooth=False)
#
#ax_el = shape_legend('el', **my_plot_el)
#oev.plot.set_datetime_ticks(ax_el, el_seq_resample.index, tick_distance=148,
#                            date_format='%d-%m-%H', offset=1)
#
#ax_el.set_ylabel('Power in kW')
#ax_el.set_xlabel('2017')
#ax_el.set_title("electrical bus")
#
## plot gas energy
#my_plot_gas = oev.plot.io_plot(
#        'gas', gas_seq_resample, cdict=cdict,
#        ax=fig.add_subplot(3, 2, 5), smooth=False)
#
#ax_gas = shape_legend('gas', **my_plot_gas)
#oev.plot.set_datetime_ticks(ax_gas, gas_seq_resample.index, tick_distance=148,
#                            date_format='%d-%m-%H', offset=1)
#
#ax_gas.set_ylabel('Power in kW')
#ax_gas.set_xlabel('2017')
#ax_gas.set_title("gas bus")
#
#plt.show()
