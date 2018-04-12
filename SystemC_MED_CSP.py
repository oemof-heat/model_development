# -*- coding: utf-8 -*-
"""
Created on Wed Mar  7 11:01:36 2018

@author: Franziska Pleissner

System C: concrete example: Model of desalination with multi effect
desalination and concentrating solar power plant
"""

############
# Preamble #
############

# Import packages
from oemof.tools import logger
import oemof.solph as solph

import oemof.outputlib as outputlib

import logging
import pandas as pd

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

number_of_time_steps = 8760

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

# Create busses
bel = solph.Bus(label='electricity')
bwat = solph.Bus(label='water')
bsol = solph.Bus(label='solarenergy')
# Create 2 thermal busses, one with high, one with low temperature
bthl = solph.Bus(label='thermal_low')
bthh = solph.Bus(label='thermal_high')
# Add the buses to the energy system
energysystem.add(bwat, bel, bthl, bthh, bsol)

# Add demand of water and electric sink
energysystem.add(solph.Sink(label='demand', inputs={bwat: solph.Flow(
        fixed=True, actual_value=data['demand_wat'], nominal_value=61472.3)}))
energysystem.add(solph.Sink(label='elec_output', inputs={bel: solph.Flow(
        variable_costs=-4)}))
# excess sink  water
energysystem.add(solph.Sink(label='excesswat', inputs={bwat: solph.Flow()}))

# Add energy source
energysystem.add(solph.Source(label='solar', outputs={bsol: solph.Flow(
        fixed=True, actual_value=data['pv'],
        investment=solph.Investment(ep_costs=70.64))}))
energysystem.add(solph.Source(label='Wat_shortage', outputs={bwat: solph.Flow(
        variable_costs=10000)}))      # should be 0, just there to avoid an underdetermined system
energysystem.add(solph.Source(label='thh_shortage', outputs={bthh: solph.Flow(
        variable_costs=10000)}))

# Add Transformers
# Collector
Col = solph.Transformer(
        label='Collector',
        inputs={bsol: solph.Flow()},
        outputs={bthh: solph.Flow(investment=solph.Investment(ep_costs=529.05))},
        conversion_factors={bthh: 1})

# Power-Block
PB = solph.Transformer(
        label='PB',
        inputs={bthh: solph.Flow()},
        outputs={bthl: solph.Flow(investment=solph.Investment(ep_costs=0.0001)),
                 bel: solph.Flow()},
        conversion_factors={bthl: 0.714, bel: 0.286})
# Transformer to show the energy flow from the collectors to the desalination
TT = solph.Transformer(
        label='TT',
        inputs={bthh: solph.Flow()},
        outputs={bthl: solph.Flow(investment=solph.Investment(ep_costs=0))},
        conversion_factors={bthl: 1})

# Desalination
Desal = solph.Transformer(
        label='Desal',
        inputs={bthl: solph.Flow(), bel: solph.Flow()},
        outputs={bwat: solph.Flow(investment=solph.Investment(ep_costs=174.6),
                                  min=0.5)},
        conversion_factors={bthl: 0.981595, bel: 0.018405,
                            bwat: 0.01227})

energysystem.add(PB, TT, Desal, Col)

# Create Storages
storage_thh = solph.components.GenericStorage(
                label='storage_thh',
                inputs={bthh: solph.Flow()},
                outputs={bthh: solph.Flow()},
                capacity_loss=0.005,
                nominal_input_capacity_ratio=1/6,
                nominal_output_capacity_ratio=1/6,
                inflow_conversion_factor=0.9,
                outflow_conversion_factor=0.9,
                investment=solph.Investment(ep_costs=0.001)
                )

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
                investment=solph.Investment(maximum=100000, ep_costs=6.54)
                )

storage_el = solph.components.GenericStorage(
                label='storageel',
                inputs={bel: solph.Flow()},
                outputs={bel: solph.Flow()},
                capacity_loss=0,
                initial_capacity=0,
                nominal_input_capacity_ratio=1/6,
                nominal_output_capacity_ratio=1/6,
                inflow_conversion_factor=1,
                outflow_conversion_factor=0.95,
                investment=solph.Investment(maximum=750000, ep_costs=15.57)
                )

energysystem.add(storage_thh, storage_wat, storage_el)

########################################
# Create a model and solve the problem #
########################################

# Initialise the operational model (create problem) with constrains
om = solph.Model(energysystem)
ColGr = energysystem.groups['Collector']
PBGr = energysystem.groups['PB']
SpGr = energysystem.groups['storage_thh']
# nominal capacity (output) of the collectors = input of the Power Block:
solph.constraints.equate_variables(
    om,
    om.InvestmentFlow.invest[ColGr, bthh],
    om.InvestmentFlow.invest[PBGr, bthl],
    factor1=0.714)
# Storage of thermal energy: for 5h with max power
solph.constraints.equate_variables(
    om,
    om.InvestmentFlow.invest[ColGr, bthh],
    om.InvestmentFlow.invest[SpGr, bthh],
    factor1=5)


# Set tee to True to get the solver output
om.solve(solver='cbc', solve_kwargs={'tee': True})

energysystem.results['main'] = outputlib.processing.results(om)
energysystem.results['meta'] = outputlib.processing.meta_results(om)

# store the results to plot them in other file
energysystem.dump(dpath="C:\Git_clones\oemof_heat\Dumps",
                  filename="MED_CSP.oemof")
