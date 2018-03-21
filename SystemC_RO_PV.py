# -*- coding: utf-8 -*-
"""
Created on 26.02.2018

@author: Franziska P

System C, concrete example: Desalination with PV and RO
"""
########################################
# Preamble (copied from basic_example) #
########################################

# Default logger of oemof
from oemof.tools import logger

import oemof.solph as solph

# Outputlib
import oemof.outputlib as outputlib
import oemof_visio as oev

# import oemof base classes to create energy system objects
import logging
import os
import pandas as pd
import pprint as pp

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

# solver = 'cbc'  # 'glpk', 'gurobi',....
debug = False  # Set number_of_timesteps to 3 to get a readable lp-file.
number_of_time_steps = 24*365
# solver_verbose = False  # show/hide solver output

# Initiate the logger (see the API docs for more information)
logger.define_logging(logfile='oemof_example.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

logging.info('Initialize the energy system')

date_time_index = pd.date_range('1/1/2017', periods=number_of_time_steps,
                                freq='H')

# Read data file
# Import  PV and demand data
data = pd.read_csv('data_input/example_wat3.csv', sep=';',)

# initialisation of the energysystem
energysystem = solph.EnergySystem(timeindex=date_time_index)

#######################
# Build up the system #
#######################

# create an electricity bus
bel = solph.Bus(label='electricity')
# create a water bus
bwat = solph.Bus(label='water')
# adding the buses to the energy system
energysystem.add(bwat, bel)

# demand sink water
energysystem.add(solph.Sink(label='demand', inputs={bwat: solph.Flow(
        fixed=True, actual_value=data['demand_wat'],
        nominal_value=61472.3)}))

# excess sink  water
energysystem.add(solph.Sink(label='excesswat', inputs={bwat: solph.Flow()}))

# excess sink electricity
excess = solph.Sink(label='excess', inputs={bel: solph.Flow()},
                    variabel_costs=-0.04)
energysystem.add(excess)

# pv sources
energysystem.add(solph.Source(label='pvel', outputs={bel: solph.Flow(
        fixed=True, actual_value=data['pv'],
        investment=solph.Investment(ep_costs=70.64))}))

# shortage source
energysystem.add(solph.Source(label='shortage', outputs={bel: solph.Flow(
        variable_costs=15)}))

# Create Storages
# electricity storage
storage_el = solph.components.GenericStorage(
                label='storageel',
                inputs={bel: solph.Flow()},
                outputs={bel: solph.Flow()},
                capacity_loss=0,
                initial_capacity=0.5,
                nominal_input_capacity_ratio=1/4,
                nominal_output_capacity_ratio=1/4,
                inflow_conversion_factor=1,
                outflow_conversion_factor=0.98,
                investment=solph.Investment(ep_costs=16.81)
                )
# water storage
storage_wat = solph.components.GenericStorage(
                label='storagewat',
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
# Add storages
energysystem.add(storage_wat, storage_el)

# RO
energysystem.add(solph.Transformer(
        label='pp_wat',
        inputs={bel: solph.Flow()},
        outputs={bwat: solph.Flow(actual_value=1, fixed=True,
                 investment=solph.Investment(ep_costs=197.78))},
        conversion_factors={bwat: 0.23256}))

logging.info('System build')

######################################
# Create model and solve the problem #
######################################

# initialise the operational model (create problem)
om = solph.Model(energysystem)
# set tee to True to get the solver output
om.solve(solver='cbc', solve_kwargs={'tee': True})

logging.info('Modell erstellt')

energysystem.results['main'] = outputlib.processing.results(om)
energysystem.results['meta'] = outputlib.processing.meta_results(om)

logging.info('results received')

### Dump results ###

energysystem.dump(dpath="C:\Git_clones\oemof_heat\Dumps", filename="RO_PV.oemof")

#########################
# Work with the results #
#########################

# Done in other file (SystemC_RO_PV_plot)
