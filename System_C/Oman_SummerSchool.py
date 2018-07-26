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

bh = solph.Bus(label='heat')
bc = solph.Bus(label="cool")
bwh = solph.Bus(label="waste")
bel = solph.Bus(label="electricity")
bgas = solph.Bus(label="gas")

energysystem.add(bh, bc, bwh, bel, bgas)

# Sources and sinks

pv = solph.Source(
        label='pv',
        outputs={bel: solph.Flow(fixed=True,
                                 actual_value=data['solar gain kWprom2'],
                                 nominal_value=100)})

collector = solph.Source(label='collector', outputs={bh: solph.Flow(
                            fixed=True, actual_value=data['solar gain kWprom2'],
                            nominal_value=100)})         # investment muss raus
gas_grid = solph.Source(
        label='naturalgas', outputs={bgas: solph.Flow(variable_costs=100)})

el_grid = solph.Source(
        label='el_grid', outputs={bel: solph.Flow(variable_costs=100)})

demand = solph.Sink(
        label='cool_demand',
        inputs={bc: solph.Flow(fixed=True, actual_value=data['Cooling load kW'],
                               nominal_value=1)})

cool_tower = solph.Sink(
        label='cool_tower', inputs={bwh: solph.Flow(variable_costs=10)})

el_output = solph.Sink(
        label='el_output', inputs={bel: solph.Flow(variable_costs=-5)})

energysystem.add(pv, collector, gas_grid, el_grid, demand, cool_tower)

# Transformers

ACM = solph.Transformer(
        label='absorpion_chiller',
        inputs={bh: solph.Flow()},
        outputs={bc: solph.Flow(investment=solph.Investment(ep_costs=10)), bwh: solph.Flow()},
        conversion_factors={bc: 0.3, bwh: 0.7})

CCM = solph.Transformer(
        label='compression_chiller',
        inputs={bel: solph.Flow()},
        outputs={bc: solph.Flow(investment=solph.Investment(ep_costs=100)), bwh: solph.Flow()},
        conversion_factors={bc: 3, bwh: 0.5})

boiler = solph.Transformer(
        label='boiler',
        inputs={bgas: solph.Flow()},
        outputs={bh: solph.Flow(investment=solph.Investment(ep_costs=100))},
        conversion_factors={bgas: 0.95})

energysystem.add(ACM, CCM, boiler)

# storages

stor_cool = solph.components.GenericStorage(
        label='storage_cool',
        inputs={bc: solph.Flow()},
        outputs={bc: solph.Flow()},
        capacity_loss=0.005,
        nominal_input_capacity_ratio=1/6,
        nominal_output_capacity_ratio=1/6,
        inflow_conversion_factor=0.9,
        outflow_conversion_factor=0.9,
        investment=solph.Investment(ep_costs=29.05))

stor_heat = solph.components.GenericStorage(
        label='storage_heat',
        inputs={bh: solph.Flow()},
        outputs={bh: solph.Flow()},
        capacity_loss=0.005,
        nominal_input_capacity_ratio=1/6,
        nominal_output_capacity_ratio=1/6,
        inflow_conversion_factor=0.9,
        outflow_conversion_factor=0.9,
        investment=solph.Investment(ep_costs=0.0001)
        )

battery = solph.components.GenericStorage(
        label='storage_el',
        inputs={bel: solph.Flow()},
        outputs={bel: solph.Flow()},
        capacity_loss=0.005,
        nominal_input_capacity_ratio=1/6,
        nominal_output_capacity_ratio=1/6,
        inflow_conversion_factor=0.9,
        outflow_conversion_factor=0.9,
        investment=solph.Investment(ep_costs=0.0001)
        )

energysystem.add(stor_cool, battery, stor_heat)


########################################
# Create a model and solve the problem #
########################################

# Initialise the operational model (create problem) with constrains
om = solph.Model(energysystem)

### Add own constrains ###
# Get value for components withouta name

# Create a block and add it to the system
# myconstrains = po.Block()
# om.add_component('MyBlock', myconstrains)
# Add the constrains to the created block


# Set tee to True to get the solver output
om.solve(solver='cbc', solve_kwargs={'tee': True})

energysystem.results['main'] = outputlib.processing.results(om)
energysystem.results['meta'] = outputlib.processing.meta_results(om)
energysystem.results['param'] = outputlib.processing.param_results(om)

# store the results to plot them in other file
timestr = time.strftime("%Y%m%d-%H%M")
energysystem.dump(dpath="C:\Git_clones\oemof_heat\Dumps",
                  filename="Oman_SS"+timestr+".oemof")

print(energysystem.results['main'])
print("done")
