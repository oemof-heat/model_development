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
import matplotlib
import matplotlib.pyplot as plt
import yaml

# ****************************************************************************
# ********** PART 2 - Processing the results *********************************
# ****************************************************************************
def analyse_storages(config_path, scenario_nr):

    make_plots = False
    use_ggplot = True
    show_plots = True
    save_plots = True
    print_keys = False
    print_meta = False
    print_sums = False
    analyse = True

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    file_path_param_01 = abs_path + cfg['parameters_energy_system'][scenario_nr-1]
    file_path_param_02 = abs_path + cfg['parameters_all_energy_systems']
    param_df_01 = pd.read_csv(file_path_param_01, index_col=1)
    param_df_02 = pd.read_csv(file_path_param_02, index_col=1)
    param_df = pd.concat([param_df_01, param_df_02], sort=True)
    param_value = param_df['value']

    # logging.info('Restore the energy system and the results.')
    energysystem = solph.EnergySystem()
    energysystem.restore(dpath=abs_path + "/results/optimisation_results/dumps",
                         filename=cfg['filename_dumb'] + '_scenario_{0}.oemof'.format(scenario_nr))

    # define an alias for shorter calls below (optional)
    results = energysystem.results['main']

    electricity_bus = outputlib.views.node(results, 'electricity')
    heat_bus = outputlib.views.node(results, 'heat')

    storage_th_comp = energysystem.groups['storage_th']
    # print('---')
    # print('********* State of Charge TES (slice) *********')
    #     # print(results[(storage_th_comp, None)]['sequences']['2040-01-01 00:00:00':
    #     #                                                '2040-01-02 00:00:00'])
    # print(results[(storage_th_comp, None)]['sequences'][0:5])
    # print(results[(storage_th_comp, None)]['sequences'][-5:])
    # storage_el_comp = energysystem.groups['storage_el']
    # print('')
    # print('********* State of Charge Battery (slice) *********')
    #     # print(results[(storage_el_comp, None)]['sequences']['2040-01-01 00:00:00':
    #     #                                                '2040-01-02 00:00:00'])
    # print(results[(storage_el_comp, None)]['sequences'][0:5])
    # print(results[(storage_el_comp, None)]['sequences'][-5:])
    # print('---')

    string_results = outputlib.views.convert_keys_to_strings(energysystem.results['main'])

    #
    # # get all variables of a specific component/bus
    # storage_th = outputlib.views.node(results, 'storage_th')
    # electricity_bus = outputlib.views.node(results, 'electricity')
    # heat_bus = outputlib.views.node(results, 'heat')
    # gas_bus = outputlib.views.node(results, 'natural_gas')
    # shortage_el = outputlib.views.node(results, 'shortage_bel')
    #
    # # Collecting results for specific components and flows
    # CHP_heat = string_results[('CHP', 'heat')]['sequences']
    # CHP_electricity = string_results[('CHP', 'electricity')]['sequences']
    # demand_th = string_results[('heat', 'demand_th')]['sequences']
    demand_el = string_results[('electricity', 'demand_el')]['sequences']
    # boiler = string_results[('boiler', 'heat')]['sequences']
    # CHP_heat_share = CHP_heat/demand_th*100  # in [%]
    # boiler_share = boiler/demand_th*100  # in [%]
    # CHP_el_share = CHP_electricity/demand_el*100  # in [%]
    # P2H_el = string_results['electricity', 'P2H']['sequences']
    # P2H_el_share = P2H_el/demand_el*100  # in [%]
    # storage_discharge = string_results['storage_th', 'heat']['sequences']
    # storage_charge = string_results['heat', 'storage_th']['sequences']
    # storage_soc = string_results['storage_th', 'None']['sequences']  # State of charge in [MWh_th]
    # battery_discharge = string_results['storage_el', 'electricity']['sequences']
    # battery_charge = string_results['electricity', 'storage_el']['sequences']
    # battery_soc = string_results['storage_el', 'None']['sequences']  # State of charge in [MWh_th]
    # storage_soc_rel = string_results['storage_th', 'None']['sequences']/string_results['storage_th', 'None']['sequences'].max()*100  # State of charge in [%]
    # shortage_electricity = string_results['shortage_bel', 'electricity']['sequences']
    # shortage_heat = string_results['shortage_bth', 'heat']['sequences']
    # excess_electricity = string_results['electricity', 'excess_bel']['sequences']
    # excess_heat = string_results['heat', 'excess_bth']['sequences']
    # residual_el = string_results['residual_el', 'electricity']['sequences']
    gas_consumption = string_results['rgas', 'natural_gas']['sequences']
    gas_consumption_CHP = string_results['natural_gas', 'CHP_01']['sequences']
    eta_el = string_results[('CHP_01', 'electricity')]['sequences']/gas_consumption_CHP
    omega_CHP = (string_results[('CHP_01', 'electricity')]['sequences']
                 + string_results[('CHP_01', 'heat')]['sequences'])/gas_consumption_CHP
    TES_discharge = string_results['storage_th', 'heat']['sequences']
    TES_charge = string_results['heat', 'storage_th']['sequences']
    TES_soc = string_results['storage_th', 'None']['sequences']  # State of charge in [MWh_th]
    TES_soc_rel = string_results['storage_th', 'None']['sequences']/string_results['storage_th', 'None']['sequences'].max()*100  # State of charge in [%]
    battery_discharge = string_results['storage_el', 'electricity']['sequences']
    battery_soc = string_results['storage_el', 'None']['sequences']
    # if make_plots==True:
    #     if use_ggplot==True:
    # plt.style.use('ggplot')
    # #         # colors for ggplot: red, bluisch and green = c("#CC6666", "#9999CC", "#66CC99")
    # #
    start = pd.to_datetime('29.04.2040 00:00:00', format='%d.%m.%Y %H:%M:%S')
    end = pd.to_datetime('29.04.2040 23:00:00', format='%d.%m.%Y %H:%M:%S')
    # #     start_axes = pd.to_datetime('01.01.2040 00:00:00', format='%d.%m.%Y %H:%M:%S')
    # #     end_axes = pd.to_datetime('31.01.2040 23:00:00', format='%d.%m.%Y %H:%M:%S')
    # #
    # #     ### PLOT 1 ###
    # fig1, (ax1, ax2, ax8, ax7, ax3) = plt.subplots(5, 1)
    # fig1.set_size_inches(10, 7)
    # plt.subplots_adjust(right=0.75)
    # fig1.subplots_adjust(hspace=0.3)  # make a little extra space between the subplots
    # fig1.autofmt_xdate()  # tilted labels on x-axes
    # fig1.suptitle("Heating", size=14)
    #
    # ax1.set_title("Demand and Supply", size=10)
    # # ax1.plot(demand_th[start:end], label='Heating Demand')
    # ax1.plot(demand_el[start:end], label='Electrical Demand')
    # # ax1.plot(boiler[start:end], label='Heat from Boiler')
    # ax1.plot(CHP_01_el[start:end], label='El form CHP_01')
    # ax1.plot(CHP_02_el[start:end], label='El form CHP_02')
    # ax1.set_xlim(start_axes, end_axes)
    # # ax1.set_ylim(0,1000)
    # # ax1.set_xlabel('Zeit')
    # ax1.set_ylabel('Leistung \nin $\mathrm{MW}_{el}$')
    # ax1.grid(True)
    # ax1.legend(bbox_to_anchor=(1.04,1), loc="upper left", borderaxespad=0)
    #
    # ax2.set_title('Battery', size=10)
    # ln1 = ax2.plot(battery_discharge[start:end], label='Discharge')
    # ln2 = ax2.plot(battery_charge[start:end], label='Charge')
    # # ax22 = ax2.twinx()
    # # ln3 = ax22.plot(storage_soc_rel[start:end], c="#9999CC", label='State of Charge')
    # # ax2.set_ylim(-4000, 4000)
    # # ax22.set_ylim(-100, 100)
    # ax2.set_xlim(start_axes, end_axes)
    # ax2.set_ylabel('Leistung \nin $\mathrm{MW}_{th}$')
    # # ax22.set_ylabel('Füllstand in %')
    # # lns = ln1+ln2+ln3
    # # labs = [l.get_label() for l in lns]
    # # ax22.legend(lns, labs)
    # # ax22.legend(loc=4)
    # ax2.legend(bbox_to_anchor=(1.04,1), loc="upper left", borderaxespad=0)

    # fig, ax = plt.subplots(figsize=(10, 5))
    # electricity_bus['sequences'].plot(ax=ax, kind='line', drawstyle='steps-post')
    # plt.legend(loc='upper center', prop={'size': 8}, bbox_to_anchor=(0.5, 1.3), ncol=2)
    # fig.subplots_adjust(top=0.8)
    # plt.show()
    bth_plt = heat_bus
    bth_plt['sequences']['CHPs'] = heat_bus['sequences'][(('CHP_01', 'heat'), 'flow')]


    bel_plt = electricity_bus
    # print(bel_plt.keys())

    # del bel_plt['sequences'][(('electricity', 'excess_bel'), 'flow')]
    fig, ax = plt.subplots(4, 1, figsize=(10, 5))
    fig.tight_layout()
    bel_plt['sequences'][(('electricity', 'demand_el'), 'flow')][start:end].plot(ax=ax[0])
    bel_plt['sequences'][(('CHP_01', 'electricity'), 'flow')][start:end].plot(ax=ax[0])

    bth_plt['sequences'][(('CHP_01', 'heat'), 'flow')][start:end].plot(ax=ax[1])
    bth_plt['sequences'][(('heat', 'demand_th'), 'flow')][start:end].plot(ax=ax[1])
    bth_plt['sequences'][(('boiler', 'heat'), 'flow')][start:end].plot(ax=ax[1])
        # bel_plt['sequences'][(('electricity', 'storage_el'), 'flow')][start:end].plot(ax=ax[3],
        #                                                                               label='Batterie Ladung')
        # battery_soc[start:end].plot(ax=ax[3])
    # results[(storage_el_comp, None)]['sequences'][start:end].plot(ax=ax[3])
        # battery_discharge[start:end].plot(ax=ax[3], label='Batterie Entladung')
    bth_plt['sequences'][(('heat', 'storage_th'), 'flow')][start:end].plot(ax=ax[3])
    results[(storage_th_comp, None)]['sequences'][start:end].plot(ax=ax[3])
    # bth_plt['sequences'][(('P2H', 'heat'), 'flow')][start:end].plot(ax=ax[2])
    eta_el[start: end].plot(ax=ax[2])
    omega_CHP[start: end].plot(ax=ax[2])
    # bel_plt['sequences'][(('electricity', 'demand_el'), 'flow')].plot.area(stacked=False)
    ax[0].legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
    ax[1].legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
    ax[2].legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
    ax[3].legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
    # plt.legend(loc='upper center', prop={'size': 8}, bbox_to_anchor=(0.5, 1.3), ncol=2)
    fig.subplots_adjust(top=0.8)
    plt.savefig('../results/plots/results_scenario_{0}.png'.format(scenario_nr), dpi=300)
    # plt.show()

    # plt.plot(TES_soc_rel)
    # plt.show()

    # print(electricity_bus['sequences'].keys())

