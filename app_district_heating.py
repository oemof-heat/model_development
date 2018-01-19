""" This is the docstring for the app_district_heating.py
application. This application models a district heating system with
a natural gas fired gas turbine supplying to the main network and
decentralized power-to-heat supplying to the sub network.

Usage: app_district_heating.py [options]

Options:

  -d, --debug              Sets timesteps to 2 and writes the lp file
  -o, --solver=SOLVER      The solver to use. Should be one of
                           "glpk", "cbc" or "gurobi". [default: cbc]
      --invest-pth         Invest optimize the power-to-heat plant.
      --invest-chp         Invest optimize the gas turbine.

"""

__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

from oemof.tools import logger, helpers, economics
import oemof.solph as solph
from oemof.outputlib import processing, views
import logging
import os
import pandas as pd
import numpy as np
from docopt import docopt

logger.define_logging()

arguments = docopt(__doc__)
print(arguments)

#####################################################################
logging.info('Initialize the energy system')
#####################################################################

if arguments['--debug']:
    number_timesteps = 2
else:
    number_timesteps = 8760

date_time_index = pd.date_range('1/1/2012', periods=number_timesteps,
                                freq='H')

energysystem = solph.EnergySystem(timeindex=date_time_index)

# random data
data = pd.DataFrame(np.random.randint(0, 100,
    size=(number_timesteps, 1)),
    columns=['demand_heat'])*1e-2

# full_filename = os.path.join(os.path.dirname(__file__),
#     'heat_demand.csv')
# data = pd.read_csv(full_filename, sep=",")


#####################################################################
logging.info('Create oemof objects')
#####################################################################

bgas = solph.Bus(label="natural_gas", balanced=False)
bel = solph.Bus(label="electricity", balanced=False)
bth = solph.Bus(label="heat")

energysystem.add(bgas, bth, bel)

# energysystem.add(solph.Sink(label='excess_heat',
    # inputs={bth: solph.Flow()}))

energysystem.add(solph.Source(label='shortage_heat',
    outputs={bth: solph.Flow(variable_costs=5000)}))

# energysystem.add(solph.Source(label='rgas',
#     outputs={bgas: solph.Flow(
#         variable_costs=0)}))

if arguments['--invest-chp']:
    energysystem.add(solph.Transformer(label='gasturbine',
        inputs={bgas: solph.Flow()},
        outputs={bth: solph.Flow(
            investment=solph.Investment(
                ep_costs=economics.annuity(
                    capex=1000, n=20, wacc=0.05)),
            variable_costs=0)},
        conversion_factors={bth: 0.5}))

else:
    energysystem.add(solph.Transformer(label='gasturbine',
        inputs={bgas: solph.Flow()},
        outputs={bth: solph.Flow(
            nominal_value=23000,
            variable_costs=0)},
        conversion_factors={bth: 0.5}))

if arguments['--invest-pth']:
    energysystem.add(solph.Transformer(label='power-to-heat',
        inputs={bel: solph.Flow()},
        outputs={bth: solph.Flow(
            investment=solph.Investment(
                ep_costs=economics.annuity(
                    capex=1000, n=20, wacc=0.05)),
            variable_costs=0)},
        conversion_factors={bth: 1}))

else:
    energysystem.add(solph.Transformer(label='power-to-heat',
        inputs={bel: solph.Flow()},
        outputs={bth: solph.Flow(
            nominal_value=5000,
            variable_costs=0)},
        conversion_factors={bth: 1}))

energysystem.add(solph.Sink(label='demand_heat',
    inputs={bth: solph.Flow(
        actual_value=data['demand_heat'],
        fixed=True,
        nominal_value=69e6,
        summed_min=1)}))

energysystem.add(solph.components.GenericStorage(label='heat_storage',
    nominal_capacity=600000,
    inputs={bth: solph.Flow(
        variable_costs=0)},
    outputs={bth: solph.Flow()},
    capacity_loss=0.00,
    initial_capacity=0,
    capacity_max=1,
    nominal_input_capacity_ratio=1,
    nominal_output_capacity_ratio=1,
    inflow_conversion_factor=1,
    outflow_conversion_factor=1))


#####################################################################
logging.info('Solve the optimization problem')
#####################################################################

om = solph.Model(energysystem)
om.solve(solver=arguments['--solver'], solve_kwargs={'tee': True})

if arguments['--debug']:
    filename = os.path.join(
        helpers.extend_basic_path('lp_files'),
        'app_district_heating.lp')
    logging.info('Store lp-file in {0}.'.format(filename))
    om.write(filename, io_options={'symbolic_solver_labels': True})


#####################################################################
logging.info('Check the results')
#####################################################################

results = processing.results(om)

