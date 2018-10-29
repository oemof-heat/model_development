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
number_of_time_steps = 8760
periods = number_of_time_steps
solver_verbose = True  # show/hide solver output

# initiate the logger (see the API docs for more information)
logger.define_logging(logfile='flexCHB.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

logging.info('Initialize the energy system')
date_time_index = pd.date_range('1/1/2030', periods=number_of_time_steps,
                                freq='H')

energysystem = solph.EnergySystem(timeindex=date_time_index)

# Read data file
abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
filename = abs_path + '/data_raw/data_confidential/demand_profile_A_nominal_20180912.csv'
# try:
#     filename = os.path.join(os.path.dirname(__file__), 'demand_profile_A_nominal_20180912.csv')
# except:
#     print('ERROR: __file__ is not defined')
#     filename = '../data_raw/data_confidential/demand_profile_A_nominal_20180912.csv'
data = pd.read_csv(filename)

##########################################################################
# Read parameter values from data file
##########################################################################

filename_param = abs_path + '/data_raw/data_public/parameters_A1.csv'
param_df = pd.read_csv(filename_param, index_col=1)  # uses second column for indexing
param_value = param_df['value']

##########################################################################
# Create oemof object
##########################################################################

logging.info('Create oemof objects')

bgas = solph.Bus(label="natural_gas")
bel = solph.Bus(label="electricity")
bth = solph.Bus(label='heat')

energysystem.add(bgas, bel, bth)


# Sources and sinks
energysystem.add(solph.Sink(
    label='excess_bel',
    inputs={bel: solph.Flow(variable_costs=param_value['var_costs_excess_bel'])}))
energysystem.add(solph.Sink(
    label='excess_bth',
    inputs={bth: solph.Flow(variable_costs=param_value['var_costs_excess_bth'])}))
energysystem.add(solph.Source(
    label='shortage_bel',
    outputs={bel: solph.Flow(variable_costs=param_value['var_costs_shortage_bel'])}))
energysystem.add(solph.Source(
    label='shortage_bth',
    outputs={bth: solph.Flow(variable_costs=param_value['var_costs_shortage_bth'])}))
energysystem.add(solph.Source(
    label='rgas',
    outputs={bgas: solph.Flow(nominal_value=param_value['nom_val_gas'],
                              summed_max=param_value['sum_max_gas'],
                              variable_costs=param_value['var_costs_gas'])}))
energysystem.add(solph.Source(
    label='residual_el',
    outputs={bel: solph.Flow(actual_value=data['neg_residual'],
                             nominal_value=param_value['nom_val_neg_residual'],
                             fixed=True)}))
energysystem.add(solph.Sink(
    label='demand_el',
    inputs={bel: solph.Flow(actual_value=data['demand_el'],
                            nominal_value=param_value['nom_val_demand_el'],
                            fixed=True)}))

energysystem.add(solph.Sink(
    label='demand_th',
    inputs={bth: solph.Flow(actual_value=data['demand_th'],
                            nominal_value=param_value['nom_val_demand_th'],
                            fixed=True)}))

# energysystem.add(solph.components.ExtractionTurbineCHP(
#     label="CHP",
#     inputs={bgas: solph.Flow()},
#     outputs={bel: solph.Flow(nominal_value=param_value['nom_val_chp_out_el'],
#                              variable_costs=param_value['var_costs_chp_out_el']),
#              bth: solph.Flow(nominal_value=param_value['nom_val_chp_out_th'],
#                              variable_costs=param_value['var_costs_chp_out_th'])},
#     conversion_factors={bel: param_value['conversion_factor_chp_bel'], bth: param_value['conversion_factor_chp_bth']},
#     conversion_factor_full_condensation={bel: param_value['conv_factor_full_cond_chp']}))

#  combined_cycle_extraction_turbine
energysystem.add(solph.components.GenericCHP(
    label='CHP',
    fuel_input={bgas: solph.Flow(
        H_L_FG_share_max=[0.19 for p in range(0, periods)])},
    electrical_output={bel: solph.Flow(
        P_max_woDH=[200 for p in range(0, periods)],
        P_min_woDH=[80 for p in range(0, periods)],
        Eta_el_max_woDH=[0.53 for p in range(0, periods)],
        Eta_el_min_woDH=[0.43 for p in range(0, periods)])},
    heat_output={bth: solph.Flow(
        Q_CW_min=[30 for p in range(0, periods)])},
    Beta=[0.19 for p in range(0, periods)],
    back_pressure=False))

energysystem.add(solph.Transformer(
    label='boiler',
    inputs={bgas: solph.Flow()},
    outputs={bth: solph.Flow(nominal_value=param_value['nom_val_out_boiler'],
                             variable_costs=param_value['var_costs_boiler'])},
    conversion_factors={bth: param_value['conversion_factor_boiler']}))

energysystem.add(solph.Transformer(
    label='P2H',
    inputs={bel: solph.Flow()},
    outputs={bth: solph.Flow(nominal_value=param_value['nom_val_p2h_out_bth'],
                             variable_costs=param_value['var_costs_p2h_out_bth'])},
    conversion_factors={bth: param_value['conversion_factor_p2h']}))

storage_th = solph.components.GenericStorage(
    nominal_capacity=param_value['nom_capacity_storage_th'],
    label='storage_th',
    inputs={bth: solph.Flow(nominal_value=param_value['nom_val_input_bth_storage_th'],
                            variable_costs=param_value['var_costs_input_bth_storage_th'])},
    outputs={bth: solph.Flow(nominal_value=param_value['nom_val_output_bth_storage_th'],
                             variable_costs=param_value['var_costs_output_bth_storage_th'])},
    capacity_loss=param_value['capacity_loss_storage_th'],
    initial_capacity=param_value['init_capacity_storage_th'],
    inflow_conversion_factor=param_value['inflow_conv_factor_storage_th'],
    outflow_conversion_factor=param_value['outflow_conv_factor_storage_th'])

storage_el = solph.components.GenericStorage(
    nominal_capacity=param_value['nom_capacity_storage_el'],
    label='storage_el',
    inputs={bel: solph.Flow(nominal_value=param_value['nom_val_input_bel_storage_el'],
                            variable_costs=param_value['var_costs_input_bel_storage_el'])},
    outputs={bel: solph.Flow(nominal_value=param_value['nom_val_output_bel_storage_el'],
                             variable_costs=param_value['var_costs_output_bel_storage_el'])},
    capacity_loss=param_value['capacity_loss_storage_el'],
    initial_capacity=param_value['init_capacity_storage_el'],
    inflow_conversion_factor=param_value['inflow_conv_factor_storage_el'],
    outflow_conversion_factor=param_value['outflow_conv_factor_storage_el'])

energysystem.add(storage_th, storage_el)

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

energysystem.dump(dpath=abs_path + "/results/dumps", filename="flexCHB.oemof")

stop_time = timeit.default_timer()
run_time_in_sec = stop_time - start_time
print("***Run Time***")
if run_time_in_sec < 60:
    print("%6.2f" %run_time_in_sec, "seconds")
elif run_time_in_sec >= 60:
    run_time_in_min = run_time_in_sec/60
    residual_seconds = run_time_in_sec%60
    print("%6.0f" %run_time_in_min, "min,", "%6.0f" %residual_seconds, "s")
else:
    print("%12.2f" %run_time_in_sec, "seconds")

