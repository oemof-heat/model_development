# -*- coding: utf-8 -*-
"""
Created on Mon Apr 30 15:21:48 2018

@author: Franziska Pleissner

System C: concrete example: Model of cooling process with a solar collector
"""


############
# Preamble #
############

# Import packages
from oemof.tools import logger
import oemof.solph as solph
import oemof.outputlib as outputlib
import pyomo.environ as po

import time
import logging
import pandas as pd

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

number_of_time_steps = 100

# initiate the logger
logger.define_logging(logfile='oemof_example.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

logging.info('Initialize the energy system')

date_time_index = pd.date_range('1/1/2017', periods=number_of_time_steps,
                                freq='H')

# Read data file
# Import  PV and demand data
data = pd.read_csv('data_input/example_wat3.csv', sep=';',)

# Initialise the energysystem
energysystem = solph.EnergySystem(timeindex=date_time_index)

#######################
# Build up the system #
#######################

# Busses

bth = solph.Bus(label='thermal')
bco = solph.Bus(label="cool")
bwh = solph.Bus(label="waste")
bel = solph.Bus(label="electricity")
bgas = solph.Bus(label="gas")

energysystem.add(bth, bco, bwh, bel, bgas)

# Sinks and sources

Collector = solph.Source(label='solar', outputs={bth: solph.Flow(
                            fixed=True, actual_value=data['pv'],
                            investment=solph.Investment(ep_costs=100.05))})
gas_grid = solph.Source(
        label='naturalgas', outputs={bgas: solph.Flow(variable_costs=10)})
grid = solph.Source(
        label='naturalgas', outputs={bel: solph.Flow(variable_costs=10)})

demand = solph.Sink(
        label='demand', inputs={bwat: solph.Flow(
        fixed=True, actual_value=data['demand_wat'], nominal_value=)})

aquifer = solph.Sink(
        label='aquifer', inputs={bwat: solph.Flow()})

cooling_tower
    
energysystem.add(Collector, gas_grid, grid, demand)

# Transformers

chil = solph.Transformer(
        label='Chiller',
        inputs={bth: solph.Flow()},
        outputs={bco: solph.Flow(), bwh: solph.Flow()},
                         )

energysystem.add(chil,)

# storages

stor_co = solph.components.Genericstorage(
        label='storage_cool',
        inputs={bco: solph.Flow()},
        outputs={bco: solph.Flow()},
        capacity_loss=0.005,
        nominal_input_capacity_ratio=1/6,
        nominal_output_capacity_ratio=1/6,
        inflow_conversion_factor=0.9,
        outflow_conversion_factor=0.9,
        investment=solph.Investment(ep_costs=0.0001)
        )

stor_thermal = solph.components.Genericstorage(
        label='storage_thermal',
        inputs={bco: solph.Flow()},
        outputs={bco: solph.Flow()},
        capacity_loss=0.005,
        nominal_input_capacity_ratio=1/6,
        nominal_output_capacity_ratio=1/6,
        inflow_conversion_factor=0.9,
        outflow_conversion_factor=0.9,
        investment=solph.Investment(ep_costs=0.0001)
        )

baterie = solph.components.Genericstorage(
        label='storage_elec',
        inputs={bco: solph.Flow()},
        outputs={bco: solph.Flow()},
        capacity_loss=0.005,
        nominal_input_capacity_ratio=1/6,
        nominal_output_capacity_ratio=1/6,
        inflow_conversion_factor=0.9,
        outflow_conversion_factor=0.9,
        investment=solph.Investment(ep_costs=0.0001)
        )

energysystem.add(stor_co, stor_thermal, baterie)


########################################
# Create a model and solve the problem #
########################################

# Initialise the operational model (create problem) with constrains
om = solph.Model(energysystem)

### Add own constrains ###
# Get value for components withouta name

# Create a block and add it to the system
myconstrains = po.Block()
om.add_component('MyBlock', myconstrains)
# Add the constrains to the created block


# Set tee to True to get the solver output
om.solve(solver='cbc', solve_kwargs={'tee': True})

energysystem.results['main'] = outputlib.processing.results(om)
energysystem.results['meta'] = outputlib.processing.meta_results(om)
energysystem.results['param'] = outputlib.processing.param_results(om)

# store the results to plot them in other file
timestr = time.strftime("%Y%m%d-%H%M")
energysystem.dump(dpath="C:\Git_clones\oemof_heat\Dumps",
                  filename="Oman_"+timestr+".oemof")
