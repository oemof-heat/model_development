# -*- coding: utf-8 -*-
"""
Created on 26.02.2018

@author: Franziska P

System C, Konkretbeispiel Meerwasserentsalzung, Variante PV+RO
"""
###########################################
# Präambel (aus basic_example übernommen) #
###########################################

# Default logger of oemof
from oemof.tools import logger
from oemof.tools import helpers

import oemof.solph as solph

# Outputlib
import oemof.outputlib as outputlib
import oemof_visio as oev

# import oemof base classes to create energy system objects
import logging
import os
import pandas as pd
import pprint as pp
import numpy

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
      

#solver = 'cbc'  # 'glpk', 'gurobi',....
debug = False  # Set number_of_timesteps to 3 to get a readable lp-file.
number_of_time_steps = 24*7
#solver_verbose = False  # show/hide solver output
 
# initiate the logger (see the API docs for more information)
logger.define_logging(logfile='oemof_example.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

logging.info('Initialize the energy system')

date_time_index = pd.date_range('1/1/2017', periods=number_of_time_steps,  
	 	freq='H')

energysystem = solph.EnergySystem(timeindex=date_time_index)

# Read data file
# Import  PV and demand data  
data = pd.read_csv('data_input/example_wat2.csv', sep=';',)  

#initialisation of the energysystem
energysystem = solph.EnergySystem(timeindex=date_time_index)
	  
######################
# Aufbau des Systems #
######################

# create an electricity bus    
bel = solph.Bus(label="electricity")    
# create a water bus    
bwat = solph.Bus(label="water")  
# adding the buses to the energy system
energysystem.add(bwat, bel)

# demand sink water
energysystem.add(solph.Sink(label='demand', inputs={bwat: solph.Flow(  
	 	fixed=True, actual_value=data['demand_wat'],  
	 		nominal_value=61472.3)}))

# excess sink  water
energysystem.add(solph.Sink(label='excesswat', inputs={bwat: solph.Flow()}))

# excess sink electricity 
excess=solph.Sink(label='excess', inputs={bel: solph.Flow()}, variabel_costs=-0.04)
energysystem.add(excess)

# pv sources  
energysystem.add(solph.Source(label='pvel', outputs={bel: solph.Flow(fixed=True,  
	 	actual_value=data['pv'], investment=solph.Investment(ep_costs=70.64))})) 

# shortage source  
energysystem.add(solph.Source(label='shortage', outputs={bel: solph.Flow(
        variable_costs=15)}))  

# electricity storage
storage_el = solph.components.GenericStorage(label='storageel',  
	              inputs={bel: solph.Flow()},  
	              outputs={bel: solph.Flow()},  
	              capacity_loss=0,  
	              initial_capacity=0.5,  
	              nominal_input_capacity_ratio=1/6,  
	              nominal_output_capacity_ratio=1/6,  
	              inflow_conversion_factor=1,  
                  outflow_conversion_factor=0.98,  
	              investment=solph.Investment(ep_costs=16.81)  
	              )

# water storage
storage_wat = solph.components.GenericStorage(label='storagewat',  
	              inputs={bwat: solph.Flow()},  
	              outputs={bwat: solph.Flow()},  
	              capacity_loss=0,  
	              initial_capacity=0,  
	              nominal_input_capacity_ratio=1/6,  
	              nominal_output_capacity_ratio=1/6,  
	              inflow_conversion_factor=1,  
                  outflow_conversion_factor=1, 
 	              investment=solph.Investment(ep_costs=7.07)
	              )

#add storages
energysystem.add(storage_wat, storage_el)

# RO  
energysystem.add(solph.Transformer(  
	 label='pp_wat',  
	 inputs={bel: solph.Flow()},  
	 outputs={bwat: solph.Flow(actual_value=1, fixed=True, investment=solph.Investment(ep_costs=197.78))},  
	 conversion_factors={bwat: 0.23256}))

logging.info('System aufgebaut') 
    
##########################################
# Modell erstellen und System optimieren #
##########################################
   
    
# initialise the operational model (create problem)  
om = solph.Model(energysystem)  
# set tee to True to get the solver output  
om.solve(solver='cbc', solve_kwargs={'tee': True})  

logging.info('Modell erstellt')

results = outputlib.processing.results(om) 
water_bus = outputlib.views.node(results, 'water')
electricity_bus = outputlib.views.node(results, 'electricity')

logging.info('Ergebnisse erhalten')

#########################
# Ergebnisse darstellen #
#########################

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
    (('water', 'storagewat'), 'flow'): '#42c77a',}

inorder = [(('pvel', 'electricity'), 'flow'),
           (('storageel', 'electricity'), 'flow'),
           (('shortage', 'electricity'), 'flow')]

fig = plt.figure(figsize=(10, 5))
electricity_seq = outputlib.views.node(results, 'electricity')['sequences']
plot_slice = oev.plot.slice_df(electricity_seq,
                               date_from=pd.datetime(2017, 1, 1))
my_plot = oev.plot.io_plot('electricity', plot_slice, cdict=cdict,
                           inorder=inorder, ax=fig.add_subplot(1, 1, 1),
                           smooth=False)
ax = shape_legend('electricity', **my_plot)
oev.plot.set_datetime_ticks(ax, plot_slice.index, tick_distance=48,
                            date_format='%d-%m-%H', offset=12)

ax.set_ylabel('Power in kW')
ax.set_xlabel('2017')
ax.set_title("Electricity bus")


inorder = [(('pp_wat', 'water'), 'flow'),
           (('storagewat', 'water'), 'flow')]

fig = plt.figure(figsize=(10, 5))
water_seq = outputlib.views.node(results, 'water')['sequences']
plot_slice = oev.plot.slice_df(water_seq,
                               date_from=pd.datetime(2017, 1, 1))
my_plot = oev.plot.io_plot('water', plot_slice, cdict=cdict,
                           inorder=inorder, ax=fig.add_subplot(1, 1, 1),
                           smooth=False)
ax = shape_legend('water', **my_plot)
oev.plot.set_datetime_ticks(ax, plot_slice.index, tick_distance=48,
                            date_format='%d-%m-%H', offset=12)

ax.set_ylabel('Water in m3/h')
ax.set_xlabel('2017')
ax.set_title("Water bus") 

print("HIER ANFANG")
results_strings=outputlib.views.convert_keys_to_strings(results)
#print(results_strings.keys())
x=results_strings[('pvel', 'electricity')]['sequences'].sum()
y=x+10000000
print(y)
print("HIER ENDE")

my_results = water_bus['scalars']

# installed capacity of storage in GWh
my_results['storage_invest_GWh'] = (results[(storage_wat, None)]
                            ['scalars']['invest']/1e6)


pp.pprint(my_results)