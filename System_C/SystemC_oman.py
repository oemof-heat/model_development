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

number_of_time_steps = 50

# initiate the logger
logger.define_logging(logfile='oemof_example.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

logging.info('Initialize the energy system')

date_time_index = pd.date_range('1/1/2017', periods=number_of_time_steps,
                                freq='H')

# Read data file
# Import  PV and demand data
data = pd.read_csv('data_input/Oman3.csv', sep=';',)

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

collector = solph.Source(label='solar', outputs={bth: solph.Flow(
                            fixed=True, actual_value=data['Solar gain from collector Wprom2'],
                            investment=solph.Investment(ep_costs=329.05))})
gas_grid = solph.Source(
        label='naturalgas', outputs={bgas: solph.Flow(variable_costs=100)})
#grid = solph.Source(
#        label='grid', outputs={bel: solph.Flow(variable_costs=10)})

demand = solph.Sink(
        label='demand', inputs={bco: solph.Flow(
        fixed=True, actual_value=data['Cooling load kW'], nominal_value=1)})

aquifer = solph.Sink(
        label='aquifer', inputs={bwh: solph.Flow(variable_costs=100)})

cooling_tower = solph.Sink(
        label='tower', inputs={bwh: solph.Flow(variable_costs=10)})
    
energysystem.add(collector, gas_grid, demand, aquifer, cooling_tower)

# Transformers

chil = solph.Transformer(
        label='Chiller',
        inputs={bth: solph.Flow()},
        outputs={bco: solph.Flow(investment=solph.Investment(ep_costs=200)), bwh: solph.Flow()},
        conversion_factors={bco: 0.3, bwh: 0.7})

boiler = solph.Transformer(
        label='boiler',
        inputs={bgas: solph.Flow()},
        outputs={bth: solph.Flow(investment=solph.Investment(ep_costs=0.0001))},
        conversion_factors={bgas: 0.95})

energysystem.add(chil, boiler)

# storages

stor_co = solph.components.GenericStorage(
        label='storage_cool',
        inputs={bco: solph.Flow()},
        outputs={bco: solph.Flow()},
        capacity_loss=0.005,
        nominal_input_capacity_ratio=1/6,
        nominal_output_capacity_ratio=1/6,
        inflow_conversion_factor=0.9,
        outflow_conversion_factor=0.9,
        investment=solph.Investment(ep_costs=29.05))
        

stor_thermal = solph.components.GenericStorage(
        label='storage_thermal',
        inputs={bth: solph.Flow()},
        outputs={bth: solph.Flow()},
        capacity_loss=0.005,
        nominal_input_capacity_ratio=1/6,
        nominal_output_capacity_ratio=1/6,
        inflow_conversion_factor=0.9,
        outflow_conversion_factor=0.9,
        investment=solph.Investment(ep_costs=0.0001)
        )

baterie = solph.components.GenericStorage(
        label='storage_elec',
        inputs={bel: solph.Flow()},
        outputs={bel: solph.Flow()},
        capacity_loss=0.005,
        nominal_input_capacity_ratio=1/6,
        nominal_output_capacity_ratio=1/6,
        inflow_conversion_factor=0.9,
        outflow_conversion_factor=0.9,
        investment=solph.Investment(ep_costs=0.0001)
        )

energysystem.add(stor_co, baterie, stor_thermal)


########################################
# Create a model and solve the problem #
########################################

# Initialise the operational model (create problem) with constrains
om = solph.Model(energysystem)

### Add own constrains ###
# Get value for components withouta name

# Create a block and add it to the system
#myconstrains = po.Block()
#om.add_component('MyBlock', myconstrains)
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

print(energysystem.results['main'])