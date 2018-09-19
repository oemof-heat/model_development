# -*- coding: utf-8 -*-

"""
General description
-------------------

Modeling a combined heat and power (CHP) plant with a thermal energy storage to increase its flexibility.
The system also comes with an electric heater, a so called Power-2-Heat (P2H) unit,
to provide electricity consumption as electricity grid service (The grid itself is not modeled!) in times when
negative electricity demand (so called 'negative residual load') occurs.
In some scenarios the system is extended by an electricity storage (battery).

The following energy system is modeled:

                input/output  bgas     bel      bth
                     |          |        |       |
 gas(Commodity)      |--------->|        |       |
                     |          |        |       |
 demand_el(Sink)     |<------------------|       |
                     |          |        |       |
 demand_th(Sink)     |<--------------------------|
                     |          |        |       |
 neg. residual load  |------------------>|       |
                     |          |        |       |
 P2H                 |          |        |------>|
                     |          |        |       |
                     |<---------|        |       |
 CHP(Transformer)    |------------------>|       |
                     |-------------------------->|
                     |          |        |       |
 storage_th(Storage) |<--------------------------|
                     |-------------------------->|
                     |          |        |       |
 O p t i o n a l
 battery (Storage)   |<------------------|       |
                     |------------------>|       |


Data
----
demand_profile_A_nominal.20180912.csv


Installation requirements
-------------------------

This example requires the version v0.2.3 of oemof. Install by:

    pip install 'oemof>=0.2.3,<0.3'

Optional:

    pip install matplotlib

"""


###############################################################################
# imports
###############################################################################

# Default logger of oemof
from oemof.tools import logger
from oemof.tools import helpers

import oemof.solph as solph
import oemof.outputlib as outputlib
import oemof.graph as grph
import networkx as nx

import logging
import os
import pandas as pd
import pprint as pp
import timeit
start_time = timeit.default_timer()

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

solver = 'cbc'
debug = False  # Set number_of_timesteps to 3 to get a readable lp-file.
number_of_time_steps = 8760 # 24*7*8  # 8 weeks, every hour
solver_verbose = False  # show/hide solver output

# initiate the logger (see the API docs for more information)
logger.define_logging(logfile='flex_CHB_A1.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

logging.info('Initialize the energy system')
date_time_index = pd.date_range('1/1/2030', periods=number_of_time_steps,
                                freq='H')

energysystem = solph.EnergySystem(timeindex=date_time_index)

# Read data file
try:
    filename = os.path.join(os.path.dirname(__file__), 'demand_profile_A_nominal_20180912.csv')
except:
    print('ERROR: __file__ is not defined')
    filename = 'demand_profile_A_nominal_20180912.csv'
data = pd.read_csv(filename)

##########################################################################
# Create oemof object
##########################################################################

logging.info('Create oemof objects')

bgas = solph.Bus(label="natural_gas")
bel = solph.Bus(label="electricity")
bth = solph.Bus(label='heat')

energysystem.add(bgas, bel, bth)

energysystem.add(solph.Sink(label='excess_bel', inputs={bel: solph.Flow(variable_costs=0)}))
energysystem.add(solph.Sink(label='excess_bth', inputs={bth: solph.Flow(variable_costs=0)}))
energysystem.add(solph.Source(label='shortage_bel', outputs={bel: solph.Flow(variable_costs=100)}))
energysystem.add(solph.Source(label='shortage_bth', outputs={bth: solph.Flow(variable_costs=100)}))
energysystem.add(solph.Source(label='rgas', outputs={bgas: solph.Flow(
    nominal_value=100000, summed_max=1e8, variable_costs=22)}))  # [MWh_th], [EUR/MWh_th]
energysystem.add(solph.Source(label='residual_el', outputs={bel: solph.Flow(
    actual_value=data['neg_residual'], nominal_value=150, fixed=True)}))  # [MW_el], [EUR/MWh_el]
energysystem.add(solph.Sink(label='demand_el', inputs={bel: solph.Flow(
    actual_value=data['demand_el'], fixed=True, nominal_value=1200)}))  # [MW_el]
energysystem.add(solph.Sink(label='demand_th', inputs={bth: solph.Flow(
    actual_value=data['demand_th'], fixed=True, nominal_value=1000)}))  # [MW_th]

energysystem.add(solph.Transformer(
    label="CHP",
    inputs={bgas: solph.Flow()},
    outputs={bel: solph.Flow(nominal_value=1200, variable_costs=1),  # [MW_th], [-]
             bth: solph.Flow(nominal_value=650, variable_costs=1)},  # [MW_el], [-]
    conversion_factors={bel: 0.60, bth: 0.25}))  # eta_el=60% und Brennstoffausnutzungsgrad omega = 85% --> eta_th=25%

energysystem.add(solph.Transformer(
    label='boiler',
    inputs={bgas: solph.Flow()},
    outputs={bth: solph.Flow(nominal_value=650, variable_costs=1)},  # [MW_th], [-]
    conversion_factors={bth: 0.9}))

energysystem.add(solph.Transformer(
    label='P2H',
    inputs={bel: solph.Flow()},
    outputs={bth: solph.Flow(nominal_value=150, variable_costs=0)},  # [MW_th], [-]
    conversion_factors={bth: 0.99}))

storage_th = solph.components.GenericStorage(
    nominal_capacity=500,  # [MWh_th]
    label='storage_th',
    inputs={bth: solph.Flow(nominal_value=500, variable_costs=0)},  # [MW_th]
    outputs={bth: solph.Flow(nominal_value=500)},  # [MW_th]
    capacity_loss=0.001, initial_capacity=0,
    inflow_conversion_factor=1, outflow_conversion_factor=0.99)

energysystem.add(storage_th)

##########################################################################
# Optimise the energy system and plot the results
##########################################################################

logging.info('Optimise the energy system')

model = solph.Model(energysystem)

if debug:
    filename = os.path.join(
        helpers.extend_basic_path('lp_files'), 'flexCHB_A1.lp')
    logging.info('Store lp-file in {0}.'.format(filename))
    model.write(filename, io_options={'symbolic_solver_labels': True})

# if tee_switch is true solver messages will be displayed
logging.info('Solve the optimization problem')
model.solve(solver=solver, solve_kwargs={'tee': solver_verbose})

logging.info('Store the energy system with the results.')

energysystem.results['main'] = outputlib.processing.results(model)
energysystem.results['meta'] = outputlib.processing.meta_results(model)

energysystem.dump(dpath="dumps", filename="flexCHB_A1_dumps.oemof")

stop_time = timeit.default_timer()
run_time_in_sec = stop_time - start_time
print("***Run Time***")
if run_time_in_sec < 60:
    print("%6.2f" %run_time_in_sec, "seconds")
elif run_time_in_sec >= 60:
    run_time_in_min = run_time_in_sec/60
    residual_seconds = run_time_in_sec%60
    print("%6.2f" %run_time_in_min, "minuts and","%6.2f" %residual_seconds, "seconds")
else:
    print("%12.2f" %run_time_in_sec, "seconds")

