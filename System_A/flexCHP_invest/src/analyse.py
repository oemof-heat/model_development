###############################################################################
# imports
###############################################################################

import oemof.solph as solph
import oemof.outputlib as outputlib
from oemof.outputlib import processing, views
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
    residual_load = string_results[('residual_el', 'electricity')]['sequences']
    # CHP_02_heat = string_results[('CHP_02', 'heat')]['sequences']
    # CHP_02_electricity = string_results[('CHP_02', 'electricity')]['sequences']
    boiler = string_results[('boiler', 'heat')]['sequences']
# # CHP_heat_share = CHP_heat/demand_th*100  # in [%]
# # boiler_share = boiler/demand_th*100  # in [%]
# # CHP_el_share = CHP_electricity/demand_el*100  # in [%]
# # P2H_el = string_results['electricity', 'P2H']['sequences']
    P2H_th = string_results['P2H', 'heat']['sequences']
# # P2H_el_share = P2H_el/demand_el*100  # in [%]
    TES_discharge = string_results['storage_th', 'heat']['sequences']
    TES_charge = string_results['heat', 'storage_th']['sequences']
    TES_soc = string_results['storage_th', 'None']['sequences']  # State of charge in [MWh_th]
    TES_soc_rel = string_results['storage_th', 'None']['sequences']/string_results['storage_th', 'None']['sequences'].max()*100  # State of charge in [%]
    battery_discharge = string_results['storage_el', 'electricity']['sequences']
    battery_charge = string_results['electricity', 'storage_el']['sequences']
    battery_soc = string_results['storage_el', 'None']['sequences']
    battery_soc_rel = string_results['storage_el', 'None']['sequences'] / string_results['storage_el', 'None'][
            'sequences'].max() * 100

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

    gas_consumption_CHP = string_results['natural_gas', 'CHP_01']['sequences']
    eta_el = string_results[('CHP_01', 'electricity')]['sequences']/gas_consumption_CHP
    omega_CHP = (string_results[('CHP_01', 'electricity')]['sequences']
                 + string_results[('CHP_01', 'heat')]['sequences'])/gas_consumption_CHP
    eta_el_sum = string_results[('CHP_01', 'electricity')]['sequences'].sum()/gas_consumption_CHP.sum()
    omega_CHP_sum = (string_results[('CHP_01', 'electricity')]['sequences'].flow.sum()
                  + string_results[('CHP_01', 'heat')]['sequences'].flow.sum())/gas_consumption_CHP.flow.sum()

    print('--- Wirkungsgrad und Co ---')
    print('Elektr. Nettowirkungsgrad des CHP: eta_min= {:2.4f}, eta_max= {:2.4f}'.format(eta_el.flow.min(), eta_el.flow.max()))
    print('Gesamtwirkungsgrad des CHP: omega_min= {:2.4f}, omega_max= {:2.4f}'.format(omega_CHP.flow.min(), omega_CHP.flow.max()))
    print('Jahresnutzungsgrad: {:2.4f}'.format(omega_CHP_sum))
    # print('max wärmeauskopplung', string_results[('CHP_01', 'heat')]['sequences'].flow.max())

    print('-- Anzahl der Stunden im betrachteten Zeitraum --')
    print(CHP_01_electricity.flow.count(), "h")
    print('-- Stunden mit eingeschränkter Versorgung (Strom) --')
    aux_shortage_df = shortage_heat.add(shortage_electricity)
    print('Hours of shortage:', aux_shortage_df[aux_shortage_df > 0].flow.count(), "h")
    # print('P_el CHP kleiner 100 MW:', CHP_01_electricity[CHP_01_electricity == 100].flow.count(), "h")
    print('-- Betriebsstunden im betrachteten Zeitraum --')
    aux_chp_01_df = CHP_01_heat.add(CHP_01_electricity)
    print('CHP_01:', aux_chp_01_df[aux_chp_01_df > 0].flow.count(), "h")
    print('Boiler:', boiler[boiler > 0].flow.count(), "h")
    print('-- Installed capacity of thermal energy storage (TES) --')
    storage_th_cap = outputlib.views.node(results, 'storage_th')['scalars'][(('storage_th', 'None'), 'invest')]
    print(storage_th_cap, "MWh")
    print("Maximum discharge capacity: ", TES_discharge.flow.max(), "MW_el")
    print('-- Installed capacity of electrical energy storage (EES) --')
    storage_el_cap = outputlib.views.node(results, 'storage_el')['scalars'][(('storage_el', 'None'), 'invest')]
    print(storage_el_cap, "MWh")
    print("Maximum discharge capacity: ", battery_discharge.flow.max(), "MW_el")
    print('-- Installed capacity of CHP --')
    # chp_cap = outputlib.views.node(results, 'CHP_01')['scalars'][(('CHP_01', 'electricity'), 'invest')]
    chp_cap = outputlib.views.node(results, 'CHP_01')['scalars'][(('natural_gas', 'CHP_01'), 'invest')]
    print(chp_cap*param_value['conv_factor_full_cond'], "MW_el")
    print('-- Installed capacity of conventional boiler --')
    boiler_cap = outputlib.views.node(results, 'boiler')['scalars'][(('boiler', 'heat'), 'invest')]
    print(boiler_cap, "MW_th")
    print('-- Installed capacity of P2H --')
    P2H_cap = outputlib.views.node(results, 'P2H')['scalars'][(('P2H', 'heat'), 'invest')]
    print(P2H_cap, "MW_th")
    print('*** End analysis  *** ')

    if cfg['run_single_scenario']:
        zeitreihen = pd.DataFrame()
        zeitreihen['Strombedarf'] = demand_el.flow
        zeitreihen['Waermebedarf'] = demand_th.flow
        zeitreihen['P2H_th'] = P2H_th.flow
        zeitreihen['CHP_01_th'] = CHP_01_heat.flow
        # zeitreihen['CHP_02_th'] = CHP_02_heat.flow
        zeitreihen['CHPs_th'] = CHP_01_heat
        zeitreihen['CHP_01_el'] = CHP_01_electricity
        # zeitreihen['CHP_02_el'] = CHP_02_electricity
        zeitreihen['CHPs_el'] = CHP_01_electricity
        zeitreihen['Kessel'] = boiler
        zeitreihen['negative_Residuallast_MW_el'] = residual_load.flow
        zeitreihen['Fuellstand_Waermespeicher_relativ'] = TES_soc_rel
        zeitreihen['Waermespeicher_beladung'] = TES_charge
        zeitreihen['Waermespeicher_entladung'] = TES_discharge
        zeitreihen['Fuellstand_Batterie_relativ'] = battery_soc_rel
        zeitreihen['batterie_beladen'] = battery_charge
        zeitreihen['batterie_entladen'] = battery_discharge

        fig, ax = plt.subplots()
        ax.scatter(x=zeitreihen['Waermebedarf'],
                   y=zeitreihen['Strombedarf'],
                   label='Bedarf')
        ax.scatter(x=zeitreihen['CHPs_th'].add(zeitreihen['Kessel'].add(zeitreihen['Waermespeicher_entladung'].add(
            zeitreihen['P2H_th']))),
                   y=zeitreihen['CHPs_el'],
                   label='CHP+Boiler+TES+P2H')
        ax.scatter(x=zeitreihen['CHPs_th'].add(zeitreihen['Kessel'].add(zeitreihen['Waermespeicher_entladung'])),
                   y=zeitreihen['CHPs_el'],
                   label='CHP+Boiler+TES')
        ax.scatter(x=zeitreihen['CHPs_th'].add(zeitreihen['Kessel']),
                   y=zeitreihen['CHPs_el'],
                   label='CHP+Boiler')
        ax.scatter(x=zeitreihen['CHPs_th'],
                   y=zeitreihen['CHPs_el'],
                   label='CHP')
        # ax.scatter(x=zeitreihen['Waermespeicher_beladung'],
        #            y=zeitreihen['CHPs_el'],
        #            label='TES charging',
        #            marker='d')
        ax.grid()
        ax.legend()
        plt.savefig('../results/plots/scatter_plot_scenario_{0}.png'.format(scenario_nr), dpi=300)

        zeitreihen.to_csv('../results/data_postprocessed/zeitreihen_A{0}.csv'.format(scenario_nr))