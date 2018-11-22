# -*- coding: utf-8 -*-
"""
Created on Mon Apr 30 15:21:48 2018

@author: Franziska Pleissner

System C: concrete example: Model of cooling process with a solar collector
"""


############
# Preamble #
############

# Input nominal values and nominal capacities and prices
nv_pv =  90 # kW_peak
nv_collector = 360 # m^2
nv_ACM = 100  # kW_cool
nv_CCM = 120  # kW_cool
nv_boiler = 70  # kW_heat
nv_CT = 1000  # kW_input
nc_cool = 400  # kWh
nc_heat = 200  # kWh
nc_elec = 100  # kWh
p_elec_buy = 0.10  # Euro/kWh
p_elec_sell = 0  # Euro/kWh
p_gas = 0.04  # Euro/kWh

# Import packages
from oemof.tools import logger, helpers
import oemof.solph as solph
import oemof.outputlib as outputlib
import pyomo.environ as po

import time
import logging
import os
import pandas as pd

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

number_of_time_steps = 2

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
bwh2 = solph.Bus(label="waste2")
bel = solph.Bus(label="elec")
bgas = solph.Bus(label="gas")

energysystem.add(bh, bc, bwh, bwh2, bel, bgas)

# Sources and sinks

pv = solph.Source(
        label='pv',
        outputs={bel: solph.Flow(fixed=True,
                                 actual_value=data['PV Faktor'],
                                 nominal_value=nv_pv)})

collector = solph.Source(label='collector', outputs={bh: solph.Flow(
                            fixed=True,
                            actual_value=data['solar gain kWprom2'],
                            nominal_value=nv_collector)})
gas_grid = solph.Source(
        label='naturalgas', outputs={bgas: solph.Flow(variable_costs=p_gas)})

el_grid = solph.Source(
        label='el_grid', outputs={bel: solph.Flow(variable_costs=p_elec_buy)})

cool_shortage = solph.Source(
        label='shortage', outputs={bc: solph.Flow(variable_costs=10000)})

demand = solph.Sink(
        label='demand',
        inputs={bc: solph.Flow(fixed=True,
                               actual_value=data['Cooling load kW'],
                               nominal_value=1)})

ambience = solph.Sink(label='ambience', inputs={bwh2: solph.Flow()})

el_output = solph.Sink(
        label='el_output',
        inputs={bel: solph.Flow(variable_costs=p_elec_sell)})

excess_heat = solph.Sink(
        label='ex_heat',
        inputs={bh: solph.Flow()})

energysystem.add(pv, collector, gas_grid, el_grid, cool_shortage, demand,
                 ambience, excess_heat)

# Transformers

CT = solph.Transformer(
        label='cooling_tower',
        inputs={bwh: solph.Flow(nominal_value=nv_CT), bel: solph.Flow()},
        outputs={bwh2: solph.Flow()},
        conversion_factors={bwh: 0.988, bel: 0.012,
                            bwh2: 1})

ACM = solph.Transformer(
        label='absorpion_chiller',
        inputs={bh: solph.Flow()},
        outputs={bc: solph.Flow(nominal_value=nv_ACM), bwh: solph.Flow()},
        conversion_factors={bc: 0.7, bwh: 1.7})

CCM = solph.Transformer(
        label='compression_chiller',
        inputs={bel: solph.Flow()},
        outputs={bc: solph.Flow(nominal_value=nv_CCM), bwh: solph.Flow()},
        conversion_factors={bc: 3.5, bwh: 4.5})

boiler = solph.Transformer(
        label='boiler',
        inputs={bgas: solph.Flow()},
        outputs={bh: solph.Flow(nominal_value=nv_boiler)},
        conversion_factors={bgas: 0.95})

energysystem.add(CT, ACM, CCM, boiler)

# storages

stor_cool = solph.components.GenericStorage(
        label='storage_cool',
        inputs={bc: solph.Flow()},
        outputs={bc: solph.Flow()},
        capacity_loss=0.005,
        inflow_conversion_factor=0.95,
        outflow_conversion_factor=0.95,
        nominal_capacity=nc_cool,
        initial_capacity=0,
        )

stor_heat = solph.components.GenericStorage(
        label='storage_heat',
        inputs={bh: solph.Flow(nominal_value=(nc_heat/2))},
        outputs={bh: solph.Flow()},
        capacity_loss=0.01,
        inflow_conversion_factor=0.95,
        outflow_conversion_factor=0.95,
        nominal_capacity=nc_heat,
        initial_capacity=0,
        )

battery = solph.components.GenericStorage(
        label='storage_el',
        inputs={bel: solph.Flow()},
        outputs={bel: solph.Flow()},
        capacity_loss=0.0,
        inflow_conversion_factor=1,
        outflow_conversion_factor=0.9,
        nominal_capacity=nc_elec,
        initial_capacity=0,
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

filename = os.path.join(
        helpers.extend_basic_path('lp_files'),
        'app_district_heating.lp')
logging.info('Store lp-file in {0}.'.format(filename))
om.write(filename, io_options={'symbolic_solver_labels': True})

energysystem.results['main'] = outputlib.processing.results(om)
energysystem.results['meta'] = outputlib.processing.meta_results(om)
energysystem.results['param'] = outputlib.processing.param_results(om)

# store the results to plot them in other file
timestr = time.strftime("%Y%m%d-%H%M")
energysystem.dump(dpath="Dumps",
                  filename="Oman_SS"+timestr+".oemof")

# print(energysystem.results['main'])
print("done")
