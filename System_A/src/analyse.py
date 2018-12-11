###############################################################################
# imports
###############################################################################

import oemof.solph as solph
import oemof.outputlib as outputlib
import oemof.tools.economics as eco

import os
import pandas as pd
import pprint as pp
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import yaml


def analyse_energy_system(config_path, scenario_nr):

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    file_path_param_01 = abs_path + cfg['parameters_energy_system'][scenario_nr-1]
    file_path_param_02 = abs_path + cfg['parameters_all_energy_systems']
    param_df_01 = pd.read_csv(file_path_param_01, index_col=1)
    param_df_02 = pd.read_csv(file_path_param_02, index_col=1)
    param_df = pd.concat([param_df_01, param_df_02])
    param_value = param_df['value']

    energysystem = solph.EnergySystem()
    energysystem.restore(dpath=abs_path + "/results/optimisation_results/dumps",
                         filename=cfg['filename_dumb'] + '_scenario_{0}.oemof'.format(scenario_nr))

    results = energysystem.results['main']

    print('\n *** Analysis of scenario {} *** '.format(scenario_nr))

    electricity_bus = outputlib.views.node(results, 'electricity')
    print('electricity bus: sums in GWh_el')
    print(electricity_bus['sequences'].sum(axis=0)/1e3)

    heat_bus = outputlib.views.node(results, 'heat')
    print('heat bus: sums in GWh_th')
    print(heat_bus['sequences'].sum(axis=0)/1e3)

    string_results = outputlib.views.convert_keys_to_strings(energysystem.results['main'])

    # Collecting results for specific components and flows
    CHP_01_heat = string_results[('CHP_01', 'heat')]['sequences']
    CHP_01_electricity = string_results[('CHP_01', 'electricity')]['sequences']
    # CHP_02_heat = string_results[('CHP_02', 'heat')]['sequences']
    # CHP_02_electricity = string_results[('CHP_02', 'electricity')]['sequences']
    boiler = string_results[('boiler', 'heat')]['sequences']
# # CHP_heat_share = CHP_heat/demand_th*100  # in [%]
# # boiler_share = boiler/demand_th*100  # in [%]
# # CHP_el_share = CHP_electricity/demand_el*100  # in [%]
# # P2H_el = string_results['electricity', 'P2H']['sequences']
    P2H_th = string_results['P2H', 'heat']['sequences']
# # P2H_el_share = P2H_el/demand_el*100  # in [%]
    if param_value['nom_capacity_storage_th'] > 0:
        TES_discharge = string_results['storage_th', 'heat']['sequences']
        TES_charge = string_results['heat', 'storage_th']['sequences']
        TES_soc = string_results['storage_th', 'None']['sequences']  # State of charge in [MWh_th]
        TES_soc_rel = string_results['storage_th', 'None']['sequences']/string_results['storage_th', 'None']['sequences'].max()*100  # State of charge in [%]
    if param_value['nom_capacity_storage_el'] > 0:
        battery_discharge = string_results['storage_el', 'electricity']['sequences']
        battery_soc_rel = string_results['storage_el', 'None']['sequences'] / string_results['storage_el', 'None'][
            'sequences'].max() * 100
    # if param_value['nom_capacity_storage_el'] > 0:

    shortage_electricity = string_results['shortage_bel', 'electricity']['sequences']
    shortage_heat = string_results['shortage_bth', 'heat']['sequences']
    excess_electricity = string_results['electricity', 'excess_bel']['sequences']
    excess_heat = string_results['heat', 'excess_bth']['sequences']
    gas_consumption = string_results['rgas', 'natural_gas']['sequences']
    demand_th = string_results['heat', 'demand_th']['sequences']
    demand_el = string_results['electricity', 'demand_el']['sequences']
#
    print('-- Consumption, Shortage and Excess Energy --')
    print("Total shortage electr.: {:.3f}".format(shortage_electricity.flow.sum()/1e3), "GWh_el")
    print("Total shortage heat:    {:.3f}".format(shortage_heat.flow.sum()/1e3), "GWh_el")
    print("Total excess electr.:   {:.2f}".format(excess_electricity.flow.sum()/1e3), "GWh_el")
    print("Total excess heat.:     {:.2f}".format(excess_heat.flow.sum()/1e3), "GWh_el")
    print("Total gas consumption:  {:.2f}".format(gas_consumption.flow.sum()/1e3), "GWh_th")
    print("Total el demand:  {:.2f}".format(demand_el.flow.sum()/1e3), "GWh_th")
    print("Total heat demand:  {:.2f}".format(demand_th.flow.sum()/1e3), "GWh_th")
#
#     # if param_value['nom_capacity_storage_el'] > 0 && param_value['nom_capacity_storage_th'] == 0:
#     #
#     if param_value['nom_capacity_storage_th'] > 0 and param_value['nom_capacity_storage_el'] == 0:
#          total_heat_prod = TES_discharge.flow.sum() + CHP_01_heat.flow.sum() + CHP_02_heat.flow.sum() \
#              + P2H_th.flow.sum() + boiler.flow.sum()
#     elif param_value['nom_capacity_storage_th'] == 0 and param_value['nom_capacity_storage_el'] == 0:
#          total_heat_prod = CHP_01_heat.flow.sum() + CHP_02_heat.flow.sum() \
#              + P2H_th.flow.sum() + boiler.flow.sum()
#     elif param_value['nom_capacity_storage_th'] == 0 and param_value['nom_capacity_storage_el'] > 0:
#         total_heat_prod = CHP_01_heat.flow.sum() + CHP_02_heat.flow.sum() \
#                       + P2H_th.flow.sum() + boiler.flow.sum()
#     elif param_value['nom_capacity_storage_th'] > 0 and param_value['nom_capacity_storage_el'] > 0:
#         total_heat_prod = TES_discharge.flow.sum() + CHP_01_heat.flow.sum() + CHP_02_heat.flow.sum() \
#                           + P2H_th.flow.sum() + boiler.flow.sum()
#     else:
#         print('ERROR - Storages??')
#     print("Total heat production (incl TES):  {:.2f}".format(total_heat_prod/1e3), "GWh_th")
#     print("\tCHP_01:  {:.2f}".format(CHP_01_heat.flow.sum()/1e3), "GWh_th")
#     print("\tCHP_02:  {:.2f}".format(CHP_02_heat.flow.sum()/1e3), "GWh_th")
#     print("\tP2H:  {:.2f}".format(P2H_th.flow.sum()/1e3), "GWh_th")
#     print("\tboiler:  {:.2f}".format(boiler.flow.sum()/1e3), "GWh_th")
#     if param_value['nom_capacity_storage_th'] > 0:
#         print("\tTES discharge:  {:.2f}".format(TES_discharge.flow.sum()/1e3), "GWh_th")
#         # print(TES_soc_rel['capacity'])
#         print("TES SOC rel max:  {:.2f}".format(TES_soc_rel['capacity'].max()), " %")
#         print("TES SOC rel max:  {:.2f}".format(TES_soc_rel['capacity'].max()), " %")
# #
# #     print("*****Results*****")
# #
# #     var_costs_es = gas_consumption.flow.sum()*param_value['var_costs_gas'] \
# #                    + shortage_electricity.flow.sum()*param_value['var_costs_shortage_bel'] \
# #                    + shortage_heat.flow.sum()*param_value['var_costs_shortage_bth']
# #
# #     print("Total Costs of Energy System per Year: {:.2f}".format((var_costs_es+total_annuity) / 10e6), "Mio. €/a")
# #     print("\t -Annuity of Energy System: {:.2f}".format(total_annuity / 10e6), "Mio. €/a")
# #     print("\t -Variable Costs of Energy System: {:.2f}".format(var_costs_es / 10e6), "Mio. €/a")
# #
#     # em_co2 = gas_consumption.flow.sum()*param_value['emission_gas']  # [kg/MWh_th]
#     # print("CO2-Emission: {:.2f}".format(em_co2/10e6), "t/a")
#
    print('-- Anzahl der Stunden im betrachteten Zeitraum --')
    print(CHP_01_electricity.flow.count(), "h")
    print('-- Stunden mit eingeschränkter Versorgung (Strom) --')
    aux_shortage_df = shortage_heat.add(shortage_electricity)
    print('Hours of shortage:', aux_shortage_df[aux_shortage_df > 0].flow.count(), "h")
    # print('P_el CHP kleiner 100 MW:', CHP_01_electricity[CHP_01_electricity == 100].flow.count(), "h")
    print('-- Betriebsstunden im betrachteten Zeitraum --')
    aux_chp_01_df = CHP_01_heat.add(CHP_01_electricity)
    print('CHP_01:', aux_chp_01_df[aux_chp_01_df > 0].flow.count(), "h")

    # print('-- Stunden im Jahr mit mind. 20% Flexibilität  bei Stromproduktion --')
    # aux_chps_el = CHP_01_electricity
    # print('Flex_hours:', aux_chp_02_df[np.logical_and(aux_chps_el < 800, aux_chps_el > 400)].flow.count(), "h")

    print('*** End analysis of scenario {} *** '.format(scenario_nr))

    if cfg['run_single_scenario']:
        zeitreihen = pd.DataFrame()
        zeitreihen['Strombedarf'] = demand_el.flow
        zeitreihen['Waermebedarf'] = demand_th.flow
        zeitreihen['CHP_01_th'] = CHP_01_heat.flow
        # zeitreihen['CHP_02_th'] = CHP_02_heat.flow
        zeitreihen['CHPs_th'] = CHP_01_heat
        zeitreihen['CHP_01_el'] = CHP_01_electricity
        # zeitreihen['CHP_02_el'] = CHP_02_electricity
        zeitreihen['CHPs_el'] = CHP_01_electricity
        zeitreihen['Kessel'] = boiler
        fig, ax = plt.subplots()
        ax.scatter(x=zeitreihen['Waermebedarf'],
                   y=zeitreihen['Strombedarf'])
        ax.scatter(x=zeitreihen['CHPs_th'].add(zeitreihen['Kessel']),
                   y=zeitreihen['CHPs_el'])
        ax.scatter(x=zeitreihen['CHPs_th'],
                   y=zeitreihen['CHPs_el'])
        plt.savefig('../results/plots/scatter_plot_scenario_{0}.png'.format(scenario_nr), dpi=300)
        # zeitreihen['Fuellstand_Waermespeicher_relativ'] = TES_soc_rel
        #
        # zeitreihen.to_csv('../results/plots/zeitreihen_A{0}.csv'.format(scenario_nr))