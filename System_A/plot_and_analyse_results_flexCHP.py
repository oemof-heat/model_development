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

# ****************************************************************************
# ********** PART 2 - Processing the results *********************************
# ****************************************************************************

make_plots=True
use_ggplot=True
show_plots=True
save_plots=True
print_slices=True
print_keys=True
print_meta=True
print_sums=True
analyse=True


# logging.info('Restore the energy system and the results.')
energysystem = solph.EnergySystem()
energysystem.restore(dpath="dumps", filename="flexCHB_A1_dumps.oemof")

# define an alias for shorter calls below (optional)
results = energysystem.results['main']
storage_th_comp = energysystem.groups['storage_th']
    
string_results = outputlib.views.convert_keys_to_strings(energysystem.results['main'])

if print_slices==True:
    ## print a time slice of the state of charge
    print('')
    print('********* State of Charge (slice) *********')
    print(results[(storage_th_comp, None)]['sequences']['2030-01-01 01:00:00':
                                                   '2030-01-01 02:00:00'])
    print('')

# get all variables of a specific component/bus
storage_th = outputlib.views.node(results, 'storage_th')
electricity_bus = outputlib.views.node(results, 'electricity')
heat_bus = outputlib.views.node(results, 'heat')
gas_bus = outputlib.views.node(results, 'natural_gas')
shortage_el = outputlib.views.node(results, 'shortage_bel')

# Collecting results for specific components and flows
CHP_heat = string_results[('CHP', 'heat')]['sequences']
CHP_electricity = string_results[('CHP', 'electricity')]['sequences']
demand_th = string_results[('heat', 'demand_th')]['sequences']
demand_el = string_results[('electricity', 'demand_el')]['sequences']
boiler = string_results[('boiler', 'heat')]['sequences']
CHP_heat_share = CHP_heat/demand_th.max()*100  # in [%]
boiler_share = boiler/demand_th.max()*100  # in [%]
storage_discharge = string_results['storage_th', 'heat']['sequences']
storage_charge = string_results['heat','storage_th']['sequences']
storage_soc = string_results['storage_th', 'None']['sequences']  # State of charge in [MWh_th]
storage_soc_rel = string_results['storage_th', 'None']['sequences']/string_results['storage_th', 'None']['sequences'].max()*100  # State of charge in [%]
shortage_electricity = string_results['shortage_bel', 'electricity']['sequences']
shortage_heat = string_results['shortage_bth', 'heat']['sequences']
excess_electricity = string_results['electricity', 'excess_bel']['sequences']
excess_heat = string_results['heat', 'excess_bth']['sequences']
residual_el = string_results['residual_el', 'electricity']['sequences']

if make_plots==True:
    if use_ggplot==True:
        plt.style.use('ggplot')
        # colors for ggplot: red, bluisch and green = c("#CC6666", "#9999CC", "#66CC99")

    start = pd.to_datetime('01.01.2030 00:00:00', format='%d.%m.%Y %H:%M:%S')
    end = pd.to_datetime('31.12.2030 23:00:00', format='%d.%m.%Y %H:%M:%S')
    start_axes = pd.to_datetime('01.01.2030 00:00:00', format='%d.%m.%Y %H:%M:%S')
    end_axes = pd.to_datetime('31.12.2030 23:00:00', format='%d.%m.%Y %H:%M:%S')

    ### PLOT 1 ###
    fig1, (ax1, ax2, ax3) = plt.subplots(3, 1)
    fig1.subplots_adjust(hspace=0.3)  # make a little extra space between the subplots
    fig1.autofmt_xdate()  # tilted labels on x-axes

    ax1.set_title("Heating")
    ax1.plot(demand_th[start:end], label='Heating Demand')
    ax1.plot(boiler[start:end], label='Heat from Boiler')
    ax1.plot(CHP_heat[start:end], label='Heat form CHP')
    ax1.set_xlim(start_axes, end_axes)
    ax1.set_ylim(0,1000)
    # ax1.set_xlabel('Zeit')
    ax1.set_ylabel('Leistung in $\mathrm{MW}_{th}$')
    ax1.grid(True)
    ax1.legend()

    ax2.set_title('Wärmespeicher', size=12)
    ln1 = ax2.plot(storage_discharge[start:end], label='Discharge')
    ln2 = ax2.plot(storage_charge[start:end]*-1, label='Charge')
    ax22 = ax2.twinx()
    ln3 = ax22.plot(storage_soc_rel[start:end], c="#9999CC", label='State of Charge')
    ax2.set_ylim(-2000, 2000)
    ax22.set_ylim(-100, 100)
    ax2.set_xlim(start_axes, end_axes)
    ax2.set_ylabel('Leistung in $\mathrm{MW}_{th}$')
    ax22.set_ylabel('Füllstand in %')
    lns = ln1+ln2+ln3
    labs = [l.get_label() for l in lns]
    ax22.legend(lns, labs)
    # ax22.legend(loc=4)

    ax3.set_title('Anteil an der Wärmeversorgung (Deckungsgrad)', size=12)
    ax3.plot(boiler_share[start:end], label='Heat from boiler')
    ax3.plot(CHP_heat_share[start:end], label='Heat from CHP')
    ax3.set_xlim(start_axes, end_axes)
    ax3.set_ylim(0, 100)
    ax3.set_xlabel('Zeit in Stunden')
    ax3.set_ylabel('Anteil in %')
    ax3.legend()

    ### PLOT 2 ###
    fig2, (ax4, ax5, ax6) = plt.subplots(3, 1)
    fig2.subplots_adjust(hspace=0.3)  # make a little extra space between the subplots
    fig2.autofmt_xdate()  # tilted labels on x-axes

    ax4.set_title("Electricity")
    ax4.plot(demand_el[start:end], label='Electricity Demand')
    ax4.plot(shortage_electricity[start:end], label='Shortage')
    ax4.plot(CHP_electricity[start:end], label='Electricity form CHP')
    ax4.set_xlim(start_axes, end_axes)
    ax4.set_ylim(0, 1200)
    # ax4.set_ylabel('Leistung in $\mathrm{MW}_{el}$')
    ax4.grid(True)
    ax4.legend()

    ax5.set_title('Residuallast', size=12)
    ln4 = ax5.plot(residual_el[start:end], label='Residuallast')
    # ln5 = ax5.plot(storage_charge[start:end]*-1, label='Charge')
    # ax5 = ax5.twinx()
    # ln6 = ax55.plot(storage_soc_rel[start:end], c="#9999CC", label='State of Charge')
    # ax5.set_ylim(0, 500)
    # ax55.set_ylim(-100, 100)
    ax5.set_xlim(start_axes, end_axes)
    ax5.set_ylabel('Leistung in $\mathrm{MW}_{th}$')
    # ax55.set_ylabel('Füllstand in %')
    # lns2 = ln4+ln5+ln6
    # labs2 = [l.get_label() for l in lns2]
    # ax55.legend(lns2, labs2)
    ax5.legend()

    # ax6.set_title('Anteil an der Wärmeversorgung (Deckungsgrad)', size=12)
    # ax6.plot(boiler_share[start:end], label='Heat from boiler')
    # ax6.plot(CHP_heat_share[start:end], label='Heat from CHP')
    ax6.set_xlim(start_axes, end_axes)
    ax6.set_ylim(0, 100)
    ax6.set_xlabel('Zeit in Stunden')
    ax6.set_ylabel('Anteil in %')
    ax6.legend()

    plt.show()

if print_keys==True:
    print('********* Keys *********')
    for key, value in string_results.items():
        print(key)
if print_meta==True:
    # print the solver results
    print('********* Meta results *********')
    pp.pprint(energysystem.results['meta'])
    print('')

# print the sums of the flows around the electricity bus
if print_sums==True:
    print('********* Main results *********')
    print('-- electricity bus --')
    print(electricity_bus['sequences'].sum(axis=0))
    print('-- heat bus --')
    print(heat_bus['sequences'].sum(axis=0))
    print('-- gas bus --')
    print(gas_bus['sequences'].sum(axis=0))

if analyse==True:
    print('********* CHP operation analysis *********')
    print('-- Anzahl der Stunden im betrachteter Zeitraum --')
    print(CHP_heat.flow.count(), "h")
    print('-- Betriebsstunden im betrachteten Zeitraum --')
    aux_df = CHP_heat.add(CHP_electricity)
    print(aux_df[aux_df > 0].flow.count(), "h")
    print('-- Volllaststunden (Wärme) im betrachteten Zeitraum --')
    print("{:.2f}".format(CHP_heat.flow.sum()/500), "h")
    print('-- Shortage und Excess Energie --')
    print("Total shortage electr.: {:.2f}".format(shortage_electricity.flow.sum()), "MWh_el")
    print("Total shortage heat:    {:.2f}".format(shortage_heat.flow.sum()), "MWh_el")
    print("Total excess electr.:   {:.2f}".format(excess_electricity.flow.sum()), "MWh_el")
    print("Total excess heat.:     {:.2f}".format(excess_heat.flow.sum()), "MWh_el")
