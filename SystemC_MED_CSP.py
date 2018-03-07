# -*- coding: utf-8 -*-
"""
Created on Wed Mar  7 11:01:36 2018

@author: Franziska Pleissner

System C: concrete example: Desalination with multi effect desalination and
concentrating solar power plant

!! Doesn't work because of the Desalination: Problem with two thermal inputs !!
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

number_of_time_steps = 24*7

# initiate the logger
logger.define_logging(logfile='oemof_example.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

logging.info('Initialize the energy system')

date_time_index = pd.date_range('1/1/2017', periods=number_of_time_steps,
                                freq='H')

# Read data file
# Import  PV and demand data
data = pd.read_csv('data_input/example_wat2.csv', sep=';',)

# Initialise the energysystem
energysystem = solph.EnergySystem(timeindex=date_time_index)

#######################
# Build up the system #
#######################

# Create electricity and water bus
bel = solph.Bus(label='electricity')
bwat = solph.Bus(label='water')
# Create 2 thermal busses, one with high, one with low temperature
bthl = solph.Bus(label='thermal_low')
bthh = solph.Bus(label='thermal_high')
# Add the buses to the energy system
energysystem.add(bwat, bel, bthl, bthh)

# Add demand of water and electric sink
energysystem.add(solph.Sink(label='demand', inputs={bwat: solph.Flow(
        fixed=True, actual_value=data['demand_wat'], nominal_value=61472.3)}))
energysystem.add(solph.Sink(label='elec_output', inputs={bel: solph.Flow(
        variable_costs=-3)}))

# Add energy source
energysystem.add(solph.Source(label='solar', outputs={bthh: solph.Flow(
        fixed=True, actual_value=data['pv'],
        investment=solph.Investment(ep_costs=70.64))}))
energysystem.add(solph.Source(label='Wat_shortage', outputs={bwat: solph.Flow(
        variable_costs=400)}))      # should be 0, just there to avoid an underdetermined system
energysystem.add(solph.Source(label='grid', outputs={bel: solph.Flow(
        variable_costs=3)}))    # according to the case study should there be enough electricity from the PB.

# Add Transformers
# Power-Block
PB = solph.Transformer(
        label='PB',
        inputs={bthh: solph.Flow()},
        outputs={bthl: solph.Flow, bel: solph.Flow},
        conversion_factors={bel: 0.35, bthl: 0.45})
# Desalination
#Desal = solph.Transformer(
#        label='Desal',
#        inputs={bthh: solph.Flow(), bthl:solph.Flow(), bel: solph.Flow()},
#       outputs={bwat: solph.flow()},
#       conversion factors={bwat=})

# Create Storages
storage_thh = solph.components.GenericStorage(label='storage_thh',
                inputs={bthh: solph.Flow()},
                outputs={bthh: solph.Flow()},
                capacity_loss=0.005,
                nominal_input_capacity_ratio=1/6,
                nominal_output_capacity_ratio=1/6,
                inflow_conversion_factor=0.9,
                outflow_conversion_factor=0.9,
                investment=solph.Investment(ep_costs=9.07)
                )

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

storage_el = solph.components.GenericStorage(label='storageel',
                inputs={bel: solph.Flow()},
                outputs={bel: solph.Flow()},
                capacity_loss=0,
                initial_capacity=0,
                nominal_input_capacity_ratio=1/6,
                nominal_output_capacity_ratio=1/6,
                inflow_conversion_factor=1,
                outflow_conversion_factor=0.95,
                investment=solph.Investment(ep_costs=16.8)
                )
# Add storages to the energy system
energysystem.add(storage_thh, storage_wat, storage_el)

########################################
# Create a model and solve the problem #
########################################

# Initialise the operational model (create problem)
om = solph.Model(energysystem)
# Set tee to True to get the solver output
om.solve(solver='cbc', solve_kwargs={'tee': True})

results = outputlib.processing.results(om)
water_bus = outputlib.views.node(results, 'water')
electricity_bus = outputlib.views.node(results, 'electricity')
thermalh_bus = outputlib.views.node(results, 'thermal_high')
thermall_bus = outputlib.views.node(results, 'thermal_low')

logging.info('results received')

#########################
# Work with the results #
#########################

water_seq = water_bus['sequences']
electricity_seq = electricity_bus['sequences']
thermalh_seq = thermalh_bus['sequences']
thermall_seq = thermall_bus['sequences']

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


### Print values ###

### Write results in csv ###