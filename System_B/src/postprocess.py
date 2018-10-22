"""
Determine the following quantities on each technology and save them in a dataframe:

Variable costs
Summed operating hours
Summed Production
Mean Production during operation hours
Maximal Production
Minimal Production
Full load hours
Start count


The following quantities concern the energy system as a whole:

Coverage through renewables
Summed Excess, max Excess
Summed import, max import
Emissions
"""

import os
import pandas as pd
import oemof.solph as solph
import oemof.outputlib as outputlib

abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))




# def get_variable_costs():
# def get_summed operating hours():
# def get_summed Production():
# def get_mean Production during operation hours():
# def get_maximal Production():
# def get_minimal Production():
# def get_full load hours():
# def get_start count():

# def get_load_duration_curves():
# def get_coverage_through_renewables():
# def get_summed_excess():
# def get_max_excess():
# def get_summed_import():
# def get_max_import():
# def get_emmission():


# Create a table of the scenario

def print_summed_heat(energysystem):
    heat_prim = outputlib.views.node(energysystem.results['main'], 'heat_prim')['sequences']
    heat_to_storage = (('heat_prim', 'storage_heat'), 'flow')
    heat_to_dhn = (('heat_prim', 'dhn_prim'), 'flow')
    print('heat_prim to dhn_prim', heat_prim[heat_to_dhn].sum())
    print('heat_prim to storage', heat_prim[heat_to_storage].sum())

    # print('dhn_prim to heat_sec', dhn_prim[(('dhn_prim', 'heat_sec'), 'flow')].sum())

    heat_sec = outputlib.views.node(energysystem.results['main'], 'heat_sec')['sequences']
    print('heat_sec to  dhn_sec', heat_sec[(('heat_sec', 'dhn_sec'), 'flow')].sum())


    sink = outputlib.views.node(energysystem.results['main'], 'demand_heat')['sequences']
    print('heat_end to demand_heat', sink[(('heat_end', 'demand_heat'), 'flow')].sum())


def get_param_as_dict(energysystem):
    param = energysystem.results['param']

def postprocess():
    energysystem = solph.EnergySystem()
    energysystem.restore(dpath=abs_path + '/model_runs/experiment_1' + '/optimisation_results', filename='es.dump')
    print_summed_heat(energysystem)
    get_param_as_dict(energysystem)

if __name__ == '__main__':
    postprocess()

