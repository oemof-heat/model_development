# -*- coding: utf-8 -*-
"""
Created on Mon Apr 30 15:21:48 2018

@author: Franziska Pleissner

System C: concrete example: Model of cooling process with a solar collector


             input/output     gas    electr.  cool   waste   ambient(/ground)

grid_el            |------------------>|       |       |
                   |           |       |       |       |
pv                 |------------------>|       |       |
                   |           |       |       |       |
                   |<----------|       |       |       |
absorption_chiller |-------------------------->|       |
                   |---------------------------------->|
                   |           |       |       |       |
cooling_tower      |<----------------------------------|
                   |<------------------|       |       |       |
                   |------------------------------------------>|
                   |           |       |       |       |
aquifer            |<----------------------------------|
                   |<------------------|       |       |       |
                   |------------------------------------------>|
                   |           |       |       |       |
storage_electricity|------------------>|       |       |
                   |<------------------|       |       |
                   |           |       |       |       |
storage_cool       |-------------------------->|       |
                   |<--------------------------|       |
                   |           |       |       |       |
demand             |<--------------------------|       |


"""

############
# Preamble #
############

# Import packages
from oemof.tools import logger, helpers
import oemof.solph as solph
import oemof.outputlib as outputlib

import time
import logging
import os
import pandas as pd

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

solver = 'cbc'
debug = False  # Set number_of_timesteps to 2 to get a readable lp-file.  # should be in config-file (doesn't exist yet)
number_of_time_steps = 8760  # should be in the config-file (doesn't exist yet)
solver_verbose = False  # show/hide solver output

# initiate the logger
logger.define_logging(logfile='System_Oman.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

logging.info('Initialize the energy system')

date_time_index = pd.date_range('1/1/2017', periods=(2 if debug is True else number_of_time_steps), freq='H')

# Read data file

abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
results_dir = abs_path + '/model_runs/'
data_dir = abs_path + '/data/'

# Read parameter values from parameter file
filename_param = data_dir + 'data_public/parameters_experiment_1.csv'
param_df = pd.read_csv(filename_param, index_col=1, sep=';')  # uses second column of csv-file for indexing
param_value = param_df['value']

# Import  PV and demand data
data = pd.read_csv((data_dir + 'data_confidential/Oman3.csv'), sep=';')

# Initialise the energysystem
energysystem = solph.EnergySystem(timeindex=date_time_index)

#######################
# Build up the system #
#######################

# Busses

bco = solph.Bus(label="cool")
bwh = solph.Bus(label="waste")
bel = solph.Bus(label="electricity")
bga = solph.Bus(label="gas")
bam = solph.Bus(label="ambient")

energysystem.add(bth, bco, bwh, bel, bga, bam)

# Sinks and sources

ambience = solph.Sink(label='ambience', inputs={bam: solph.Flow()})

grid_el = solph.Source(label='grid_el', outputs={bel: solph.Flow(variable_costs=param_value['price_electr'])})

pv = solph.Source(label='pv', outputs={bel: solph.Flow(
    fixed=True, actual_value=data['PV Faktor'],
    investment=solph.Investment(ep_costs=param_value['invest_costs_pv_output_th']))})

demand = solph.Sink(label='demand', inputs={bco: solph.Flow(
    fixed=True, actual_value=data['Cooling load kW'], nominal_value=1)})

excess = solph.Sink(label='excess_electrical', inputs={bth: solph.Flow()})

energysystem.add(ambience, grid_el, pv, demand, excess)

# Transformers

chil = solph.Transformer(
    label='compression_chiller',
    inputs={bth: solph.Flow()},
    outputs={bco: solph.Flow(investment=solph.Investment(ep_costs=param_value['invest_costs_abs_output_cool'])),
             bwh: solph.Flow()},
    conversion_factors={bco: param_value['conv_factor_abs_cool'], bwh: param_value['conv_factor_abs_waste']})

aqui = solph.Transformer(
    label='aquifer',
    inputs={bwh: solph.Flow(investment=solph.Investment(ep_costs=param_value['invest_costs_aqui_input_th']),
                            variable_costs=param_value['var_costs_aquifer_input_waste']),
            bel: solph.Flow()},
    outputs={bam: solph.Flow()},
    conversion_factors={bwh: 0.95, bel: 0.05})

towe = solph.Sink(
    label='cooling_tower',
    inputs={bwh: solph.Flow(investment=solph.Investment(ep_costs=param_value['invest_costs_towe_input_th']),
                            variable_costs=param_value['var_costs_cool_tower_input_waste']),
            bel: solph.Flow()},
    outputs={bam: solph.Flow()},
    conversion_factors={bwh: 0.988, bel: 0.012})

energysystem.add(chil, aqui, towe)

# storages

stor_co = solph.components.GenericStorage(
    label='storage_cool',
    inputs={bco: solph.Flow()},
    outputs={bco: solph.Flow()},
    capacity_loss=0.005,
    invest_relation_input_capacity=1 / 6,
    invest_relation_output_capacity=1 / 6,
    inflow_conversion_factor=0.9,
    outflow_conversion_factor=0.9,
    investment=solph.Investment(ep_costs=29.05))

stor_el = solph.components.GenericStorage(
    label='storage_electricity',
    inputs={bel: solph.Flow()},
    outputs={bel: solph.Flow()},
    capacity_loss=0.005,
    invest_relation_input_capacity=1 / 6,
    invest_relation_output_capacity=1 / 6,
    inflow_conversion_factor=0.9,
    outflow_conversion_factor=0.9,
    investment=solph.Investment(ep_costs=12)
)

energysystem.add(stor_co, stor_el)

########################################
# Create a model and solve the problem #
########################################

# Initialise the operational model (create problem) with constrains
model = solph.Model(energysystem)

if debug:
    filename = os.path.join(
        helpers.extend_basic_path('lp_files'), 'app_Oman.lp')
    logging.info('Store lp-file in {0}.'.format(filename))
    model.write(filename, io_options={'symbolic_solver_labels': True})

logging.info('Solve the optimization problem')
model.solve(solver=solver, solve_kwargs={'tee': solver_verbose})

logging.info('Store the energy system with the results.')

energysystem.results['main'] = outputlib.processing.results(model)
energysystem.results['meta'] = outputlib.processing.meta_results(model)
energysystem.results['param'] = outputlib.processing.param_results(model)

timestr = time.strftime("%Y%m%d-%H%M")
energysystem.dump(dpath=(abs_path + '/dumps'),
                  filename="Oman_elec.oemof")

print('done')
