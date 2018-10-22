# -*- coding: utf-8 -*-
"""
Created on Wed May  2 11:54:15 2018

@author: Franziska Pleissner

System C: concrete example: Plot of the cooling process with a solar collector
"""

############
# Preamble #
############

# Import packages
from oemof.tools import economics
import oemof.solph as solph

import oemof.outputlib as outputlib
import oemof_visio as oev

import logging
import pandas as pd

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

#####################################
# Input and Creating of raw results #
#####################################

# file to Import:
file_imp = 'Oman_SS20181011-1000.oemof'

# Weighted average cost of capital
wacc = 0.07

# investcosts without chillers and cooling tower:
ic_pv = 650  # Euro/kW_p
ic_collector = 100  # Euro/m^2
ic_boiler = 100  # Euro/kW_heat
ic_cool = 40  # Euro/kWh
ic_heat = 20  # Euro/kWh
ic_elec_kWh = 165   # Euro/kWh
ic_elec_kW = 50  # Euro/kW

# lifetimes [years]:
lt_pv = 25
lt_collector = 25
lt_ACM = 18
lt_CCM = 15
lt_boiler = 20
lt_cool = 25
lt_heat = 25
lt_ct = 25
lt_elec_kWh = 20
lt_elec_kW = 20

# OPEX [% of ic]:
op_pv = 0.015
op_collector = 0.02
op_ACM = 0.015
op_CCM = 0.02
op_boiler = 0.02
op_cool = 0.02
op_heat = 0.02
op_ct = 0.02
op_elec_kWh = 0
op_elec_kW = 0

# Emission factors
H_gas = 10  # (kWh/m^3)
Em_CO2_el = 403.2  # g/kWh
Em_CO2_gas = 201.6  # g/kWh

# water price
p_water = 1  # Euro/m^3

# Plotting time
sp = start_of_plot = 5523
ep = end_of_plot = sp + 48

# restoring the system and creating results
energysystem = solph.EnergySystem()
energysystem.restore(dpath="Dumps",
                     filename = file_imp)

results_strings = outputlib.views.convert_keys_to_strings(energysystem.results['main'])
results_strings_param = outputlib.views.convert_keys_to_strings(energysystem.results['param'])

logging.info('results received')

# get data from the import
nv_pv = (results_strings_param['pv', 'elec']['scalars']['nominal_value'])
nv_collector = (results_strings_param['collector', 'heat']['scalars']
                ['nominal_value'])
nv_ACM = (results_strings_param['absorpion_chiller', 'cool']['scalars']
          ['nominal_value'])
nv_CCM = (results_strings_param['compression_chiller', 'cool']['scalars']
          ['nominal_value'])
nv_boiler = (results_strings_param['boiler', 'heat']['scalars']
             ['nominal_value'])
nv_ct = (results_strings_param['waste', 'cooling_tower']['scalars']
         ['nominal_value'])
nc_cool = (results_strings_param['storage_cool', 'None']['scalars']
           ['nominal_capacity'])
nc_heat = (results_strings_param['storage_heat', 'None']['scalars']
           ['nominal_capacity'])
nc_elec = (results_strings_param['storage_el', 'None']['scalars']
           ['nominal_capacity'])
p_elec_b = (results_strings_param['el_grid', 'elec']['scalars']
           ['variable_costs'])
p_elec_s = (results_strings_param['elec', 'el_output']['scalars']
           ['variable_costs'])
p_gas_b = (results_strings_param['naturalgas', 'gas']['scalars']
           ['variable_costs'])

#print(nv_pv)
#print(nv_collector)
#print(nv_ACM)
#print(nv_CCM)
#print(nv_boiler)
#print(nv_ct)
#print(nc_cool)
#print(nc_heat)
#print(nc_elec)
#print(p_elec_b)
#print(p_elec_s)
#print(p_gas_b)

if nv_CCM < 25:
    ic_CCM = 650
else:
    if nv_CCM < 50:
        ic_CCM = 600
    else:
        if nv_CCM < 75:
            ic_CCM = 400
        else:
            if nv_CCM < 100:
                ic_CCM = 325
            else:
                ic_CCM = 200

if nv_ACM < 25:
    ic_ACM = 1000
else:
    if nv_ACM < 50:
        ic_ACM = 900
    else:
        if nv_ACM < 75:
            ic_ACM = 625
        else:
            if nv_ACM < 100:
                ic_ACM = 550
            else:
                ic_ACM = 400

if nv_ct < 100:
    ic_ct = 55
else:
    if nv_ct < 200:
        ic_ct = 40
    else:
        if nv_ct < 400:
            ic_ct = 32.5
        else:
            ic_ct = 28
          
#print(ic_ACM)
#print(ic_CCM)
#print(ic_ct)
            
#########################
# Work with the results #
#########################

cool_bus = outputlib.views.node(energysystem.results['main'], 'cool')
heat_bus = outputlib.views.node(energysystem.results['main'], 'heat')
waste_bus = outputlib.views.node(energysystem.results['main'], 'waste')
el_bus = outputlib.views.node(energysystem.results['main'], 'elec')
gas_bus = outputlib.views.node(energysystem.results['main'], 'gas')
storage_cool_res = outputlib.views.node(energysystem.results['main'], 'storage_cool')

cool_seq = cool_bus['sequences']
heat_seq = heat_bus['sequences']
waste_seq = waste_bus['sequences']
el_seq = el_bus['sequences']
gas_seq = gas_bus['sequences']
storage_cool_seq = storage_cool_res['sequences']

### Calculations ###

# demand
cooling_demand = results_strings[('cool', 'demand')]['sequences'].sum()
covered_demand = (cooling_demand -
                  results_strings[('shortage', 'cool')]['sequences'].sum())
fraction_covered = covered_demand/cooling_demand

# chillers
results_CCM = results_strings[('compression_chiller', 'cool')]['sequences']
cooling_from_CCM = results_CCM.sum()
hoo_CCM = results_CCM[results_CCM['flow'] > 0.01].count()
results_ACM = results_strings[('absorpion_chiller', 'cool')]['sequences']
cooling_from_ACM = results_ACM.sum()
hoo_ACM = results_ACM[results_ACM['flow'] > 0.01].count()
if (cooling_from_CCM+cooling_from_ACM).all() == 0:
    fraction_CCM = 0
    fraction_ACM = 0
else:
    fraction_CCM = cooling_from_CCM/(cooling_from_CCM+cooling_from_ACM)
    fraction_ACM = cooling_from_ACM/(cooling_from_CCM+cooling_from_ACM)

# heat
heat_total_in = (results_strings[('boiler', 'heat')]['sequences'].sum() +
                 results_strings[('collector', 'heat')]['sequences'].sum())
if heat_total_in.all() == 0:
    fraction_boiler = 0
    fraction_collector = 0
else:
    fraction_boiler = ((results_strings[('boiler', 'heat')]
                       ['sequences'].sum()) / heat_total_in)
    fraction_collector = ((results_strings[('collector', 'heat')]
                          ['sequences'].sum()) / heat_total_in)

# gas
gas_Energy = results_strings[('naturalgas', 'gas')]['sequences'].sum()  # kWh
gas_vol = gas_Energy/H_gas  # m^3
gas_CO2 = gas_Energy*Em_CO2_gas  # g

# electricity
electricity_input = results_strings[('el_grid', 'elec')]['sequences'].sum()
electricity_CO2 = electricity_input*Em_CO2_el  # g
electricity_output = results_strings[('elec', 'el_output')]['sequences'].sum()
electricity_Diff = electricity_input-electricity_output
elec_total_in = (results_strings[('el_grid', 'elec')]['sequences'].sum() +
                 results_strings[('pv', 'elec')]['sequences'].sum())
if elec_total_in.all() == 0:
    fraction_el_grid = 0
    fraction_pv = 0
else:
    fraction_el_grid = ((results_strings[('el_grid', 'elec')]
                        ['sequences'].sum()) / elec_total_in)
    fraction_pv = ((results_strings[('pv', 'elec')]
                   ['sequences'].sum()) / elec_total_in)

# cooling tower
ct_energy = results_strings[('waste', 'cooling_tower')]['sequences'].sum()

## cost results

# invest annuities
ian_pv = economics.annuity(ic_pv, lt_pv, wacc)
ian_collector = economics.annuity(ic_collector, lt_collector, wacc)
ian_ACM = economics.annuity(ic_ACM, lt_ACM, wacc)
ian_CCM = economics.annuity(ic_CCM, lt_CCM, wacc)
ian_boiler = economics.annuity(ic_boiler, lt_boiler, wacc)
ian_cool = economics.annuity(ic_cool, lt_cool, wacc)
ian_heat = economics.annuity(ic_heat, lt_heat, wacc)
ian_ct = economics.annuity(ic_ct, lt_ct, wacc)
ian_elec_kWh = economics.annuity(ic_elec_kWh, lt_elec_kWh, wacc)
ian_elec_kW = economics.annuity(ic_elec_kW, lt_elec_kW, wacc)

# total annuities (invest + operational costs)
an_pv = ian_pv + op_pv * ic_pv
an_collector = ian_collector + op_collector * ic_collector
an_ACM = ian_ACM + op_ACM * ic_ACM
an_CCM = ian_CCM + op_CCM * ic_CCM
an_boiler = ian_boiler + op_boiler * ic_boiler
an_cool = ian_cool + op_cool * ic_cool
an_heat = ian_heat + op_heat * ic_heat
an_ct = ian_ct + op_ct * ic_ct
an_elec_kWh = ian_elec_kWh + op_elec_kWh * ic_elec_kWh
an_elec_kW = ian_elec_kW + op_elec_kW * ic_elec_kW

power_battery = max(el_seq[(('storage_el', 'elec'), 'flow')])

# calculating the costs
fixed_costs_pa = (nv_pv * an_pv + nv_collector * an_collector +
                  nv_ACM * an_ACM + nv_CCM * an_CCM + nv_boiler * an_boiler +
                  nv_ct * an_ct + nc_cool * an_cool + nc_heat * an_heat +
                  nc_elec * an_elec_kWh + an_elec_kW * power_battery)

total_invest_costs = (nv_pv * ic_pv + nv_collector * ic_collector + nv_ACM *
                      ic_ACM + nv_CCM * ic_CCM + nv_boiler * ic_boiler +
                      nv_ct * ic_ct + nc_cool * ic_cool + nc_heat * ic_heat +
                      nc_elec * ic_elec_kWh + ic_elec_kW * power_battery)

costs_gas = gas_Energy * p_gas_b
costs_el = electricity_input * p_elec_b
profits_el = electricity_output * p_elec_s
costs_water = ct_energy * 1.5 / 1000 * p_water  # kWh * l/kWh / l/m3 * Euro/m3 = Euro

total_costs_pa = (fixed_costs_pa + costs_gas + costs_el + profits_el
                  + costs_water)

lcoc = total_costs_pa / covered_demand  # levelised costs of cold

# utilization

lf_ACM = cooling_from_ACM / (nv_ACM * 8760)
lf_CCM = cooling_from_CCM / (nv_CCM * 8760)
max_load_ACM = results_ACM.max()
max_load_CCM = results_CCM.max()
stor_cool_max = results_strings[('storage_cool', 'None')]['sequences'].max()
stor_heat_max = results_strings[('storage_heat', 'None')]['sequences'].max()
stor_el_max = results_strings[('storage_el', 'None')]['sequences'].max()
stor_cool_max_fraction = stor_cool_max / nc_cool
stor_heat_max_fraction = stor_heat_max / nc_heat
stor_el_max_fraction = stor_el_max / nc_elec

if fraction_covered.all() > 0.99:
    is_covered = 'Yes'
else:
    is_covered = 'No'
    
### showing the results ###

print('')
print('*****************************************')
print('results No test')
print('')
print('*Demand*')
print("Cooling Demand: %.2f kWh" % cooling_demand)
# print("Demand covered: %.2f kWh" % covered_demand)
print("covered fraction of demand: %.2f %%" % (fraction_covered*100))

print("cooling energy from CCM: %.2f kWh" % cooling_from_CCM)
print("cooling energy from ACM: %.2f kWh" % cooling_from_ACM)
print("fraction covered from CCM: %.2f %%" % (fraction_CCM*100))
print("fraction covered from ACM: %.2f %%" % (fraction_ACM*100))
# print("hours of operation of the CCM: %i h" % hoo_CCM)
# print("hours of operation of the ACM: %i h" % hoo_ACM)
print('')
print('*Energy consumption*')
print("fraction of produced heat covered from collectors: %.2f %%" % (fraction_collector*100))
print("fraction of produced electricity covered from pv: %.2f %%" % (fraction_pv*100))

print("used natural gas: %.2f m^3" % gas_vol)
print("electrical input: %.2f kWh" % electricity_input)
print("electrical output: %.2f kWh" % electricity_output)
print("electrical difference: %.2f kWh" % electricity_Diff)
print('')
print('*Emissions*')
print("CO2 output: %.2f kg" % ((gas_CO2+electricity_CO2)/1000))

# cool_stor = results_strings[('storage_cool', 'None')]['sequences']
print('')
print('*costs*')
print("total invest costs: %i €" % total_invest_costs)
print("total costs per year: %.2f €/a" % total_costs_pa)
print("levelised costs of cold: %.4f €/kWh" % lcoc)
print('')
print('*utilization*')
print('load factor absorption chilller: %.2f' % lf_ACM)
print('load factor compression chiller: %.2f' % lf_CCM)
print('maximum load of absorption chilller: %.2f' % max_load_ACM)
print('maximum load of compression chilller: %.2f' % max_load_CCM)
# print('maximum charging level of cold storage: %.2f' % stor_cool_max)
# print('maximum charging level of heat storage: %.2f' % stor_heat_max)
# print('maximum charging level of electricity storage: %.2f' % stor_el_max)
print('used fraction of cold storage capacity: %.2f %%' % (stor_cool_max_fraction*100))
print('used fraction of heat storage capacity: %.2f %%' % (stor_heat_max_fraction*100))
print('used fraction of electricity storage capacity: %.2f %%' % (stor_el_max_fraction*100))
print('')
print('*****************************************')
print('*summary*')
print('')
print('Is the demand covered? %s' % is_covered)
print("levelised costs of cold: %.4f €/kWh" % lcoc)
print("CO2 output: %.2f kg" % ((gas_CO2+electricity_CO2)/1000))
print('*****************************************')
print('')

### Results into csv  ###

# cool_seq.to_csv('data_output/results.csv')

########################
# Plotting the results #
########################

cool_seq_resample = cool_seq.iloc[sp:ep]
heat_seq_resample = heat_seq.iloc[sp:ep]
waste_seq_resample = waste_seq.iloc[sp:ep]
el_seq_resample = el_seq.iloc[sp:ep]
gas_seq_resample = gas_seq.iloc[sp:ep]
storage_cool_seq_resample = storage_cool_seq.iloc[sp:ep]


def shape_legend(node, reverse=False, **kwargs):  # just copied
    handels = kwargs['handles']
    labels = kwargs['labels']
    axes = kwargs['ax']
    parameter = {}

    new_labels = []
    for label in labels:
        label = label.replace('(', '')
        label = label.replace('), flow)', '')
        label = label.replace('None', '')
        label = label.replace(')', '')
        label = label.replace('_'+str(node), '')
        label = label.replace(node, '')
        label = label.replace(',', '')
        label = label.replace(' ', '')
        label = label.replace('_el', '')
        label = label.replace('el_', '')
        label = label.replace('_', ' ')
        new_labels.append(label)
    labels = new_labels

    parameter['bbox_to_anchor'] = kwargs.get('bbox_to_anchor', (1, 1))
    parameter['loc'] = kwargs.get('loc', 'upper left')
    parameter['ncol'] = kwargs.get('ncol', 1)
    plotshare = kwargs.get('plotshare', 0.9)

    if reverse:
        handels = handels.reverse()
        labels = labels.reverse()

    box = axes.get_position()
    axes.set_position([box.x0, box.y0, box.width * plotshare, box.height])

    parameter['handles'] = handels
    parameter['labels'] = labels
    axes.legend(**parameter)
    return axes

cdict = {
    (('collector', 'heat'), 'flow'): '#ffde32',
    (('boiler', 'heat'), 'flow'): '#ff0000',
    (('heat', 'absorpion_chiller'), 'flow'): '#4682b4',
    (('heat', 'storage_heat'), 'flow'): '#9acd32',
    (('storage_heat', 'heat'), 'flow'): '#9acd32',
    (('el_grid', 'elec'), 'flow'): '#999999',
    (('pv', 'elec'), 'flow'): '#ffde32',
    (('storage_el', 'elec'), 'flow'): '#9acd32',
    (('elec', 'storage_el'), 'flow'): '#9acd32',
    (('elec', 'compression_chiller'), 'flow'): '#87ceeb',
    (('elec', 'el_output'), 'flow'): '#555555',
    (('elec', 'cooling_tower'), 'flow'): '#ff0000',
    (('compression_chiller', 'cool'), 'flow'): '#87ceeb',
    (('absorpion_chiller', 'cool'), 'flow'): '#4682b4',
    (('shortage', 'cool'), 'flow'): '#555555',
    (('cool', 'demand'), 'flow'): '#cd0000',
    (('cool', 'storage_cool'), 'flow'): '#9acd32',
    (('storage_cool', 'None'), 'capacity'): '#555555',
    (('storage_cool', 'cool'), 'flow'): '#9acd32',
    (('naturalgas', 'gas'), 'flow'): '#42c77a',
    (('gas', 'boiler'), 'flow'): '#42c77a',
    (('compression_chiller', 'waste'), 'flow'): '#87ceeb',
    (('absorpion_chiller', 'waste'), 'flow'): '#4682b4',
    (('waste', 'cool_tower'), 'flow'): '#42c77a'}


# define order of inputs and outputs
inorderstor = [(('cool', 'storage_cool'), 'flow')]
outorderstor = [(('storage_cool', 'cool'), 'flow'),
                (('storage_cool', 'None'), 'capacity')]
inordercool = [(('absorpion_chiller', 'cool'), 'flow'),
               (('compression_chiller', 'cool'), 'flow'),
               (('storage_cool', 'cool'), 'flow'),
               (('shortage', 'cool'), 'flow')]
outordercool = [(('cool', 'demand'), 'flow'),
                (('cool', 'storage_cool'), 'flow')]
inorderel = [(('pv', 'elec'), 'flow'),
             (('storage_el', 'elec'), 'flow'),
             (('el_grid', 'elec'), 'flow')]
outorderel = [(('elec', 'compression_chiller'), 'flow'),
              (('elec', 'storage_el'), 'flow'),
              (('elec', 'cooling_tower'), 'flow'),
              (('elec', 'el_output'), 'flow')]
inorderheat = [(('collector', 'heat'), 'flow'),
               (('storage_heat', 'heat'), 'flow'),
               (('boiler', 'heat'), 'flow')]
outorderheat = [(('heat', 'absorpion_chiller'), 'flow'),
                (('heat', 'storage_heat'), 'flow')]

fig = plt.figure(figsize=(15, 15))

# plot cooling energy
my_plot_cool = oev.plot.io_plot(
        'cool', cool_seq_resample, cdict=cdict,
        inorder=inordercool, outorder=outordercool,
        ax=fig.add_subplot(2, 2, 1), smooth=False)

ax_cool = shape_legend('cool', **my_plot_cool)
oev.plot.set_datetime_ticks(ax_cool, cool_seq_resample.index, tick_distance=14,
                            date_format='%d-%m-%H', offset=1)

ax_cool.set_ylabel('Power in kW')
ax_cool.set_xlabel('time')
ax_cool.set_title("cool")

# plot heat energy
my_plot_heat = oev.plot.io_plot(
        'heat', heat_seq_resample, cdict=cdict,
        inorder=inorderheat, outorder=outorderheat,
        ax=fig.add_subplot(2, 2, 2), smooth=False)

ax_heat = shape_legend('heat', **my_plot_heat)
oev.plot.set_datetime_ticks(ax_heat, heat_seq_resample.index, tick_distance=14,
                            date_format='%d-%m-%H', offset=1)

ax_heat.set_ylabel('Power in kW')
ax_heat.set_xlabel('time')
ax_heat.set_title("heat")

# plot electric energy
my_plot_el = oev.plot.io_plot(
        'elec', el_seq_resample, cdict=cdict,
        inorder=inorderel, outorder=outorderel,
        ax=fig.add_subplot(2, 2, 3), smooth=False)

ax_el = shape_legend('elec', **my_plot_el)
oev.plot.set_datetime_ticks(ax_el, el_seq_resample.index, tick_distance=14,
                            date_format='%d-%m-%H', offset=1)

ax_el.set_ylabel('Power in kW')
ax_el.set_xlabel('time')
ax_el.set_title("electricity")


def shape_legend_stor(node, reverse=False, **kwargs):  # just copied
    handels = kwargs['handles']
    labels = kwargs['labels']
    axes = kwargs['ax']
    parameter = {}

    new_labels = []
    for label in labels:
        label = label.replace('(', '')
        label = label.replace('), flow)', '')
        label = label.replace('None', '')
        label = label.replace(')', '')
        label = label.replace('_'+str(node), '')
        label = label.replace(node, '')
        label = label.replace(',', '')
        label = label.replace(' ', '')
        label = label.replace('cool', 'input/output')
        if label not in new_labels:
            new_labels.append(label)
    labels = new_labels

    parameter['bbox_to_anchor'] = kwargs.get('bbox_to_anchor', (1, 1))
    parameter['loc'] = kwargs.get('loc', 'upper left')
    parameter['ncol'] = kwargs.get('ncol', 1)
    plotshare = kwargs.get('plotshare', 0.9)

    if reverse:
        handels = handels.reverse()
        labels = labels.reverse()

    box = axes.get_position()
    axes.set_position([box.x0, box.y0, box.width * plotshare, box.height])

    parameter['handles'] = handels
    parameter['labels'] = labels
    axes.legend(**parameter)
    return axes

# plot storage capacity
my_plot_stor = oev.plot.io_plot(
        'storage_cool', storage_cool_seq_resample, cdict=cdict,
        inorder=inorderstor, outorder=outorderstor,
        ax=fig.add_subplot(2, 2, 4), smooth=False)

ax_stor = shape_legend_stor('storage_cool', **my_plot_stor)
oev.plot.set_datetime_ticks(ax_stor, storage_cool_seq_resample.index,
                            tick_distance=14,
                            date_format='%d-%m-%H', offset=1)

ax_stor.set_ylabel('Power in kW and capacity in kWh')
ax_stor.set_xlabel('time')
ax_stor.set_title("cooling storage")

'''
# plot gas energy
my_plot_gas = oev.plot.io_plot(
        'gas', gas_seq_resample, cdict=cdict,
        ax=fig.add_subplot(3, 2, 5), smooth=False)

ax_gas = shape_legend('gas', **my_plot_gas)
oev.plot.set_datetime_ticks(ax_gas, gas_seq_resample.index, tick_distance=148,
                            date_format='%d-%m-%H', offset=1)

ax_gas.set_ylabel('Power in kW')
ax_gas.set_xlabel('2017')
ax_gas.set_title("gas bus")

# plot waste heat energy
my_plot_waste = oev.plot.io_plot(
        'waste', waste_seq_resample, cdict=cdict,
        ax=fig.add_subplot(3, 2, 5), smooth=False)

ax_waste = shape_legend('waste', **my_plot_waste)
oev.plot.set_datetime_ticks(ax_waste,
                            waste_seq_resample.index,tick_distance=148,
                            date_format='%d-%m-%H', offset=1)

ax_waste.set_ylabel('Power in kW')
ax_waste.set_xlabel('2017')
ax_waste.set_title("waste heat bus")
'''

plt.subplots_adjust(right=0.87)
plt.subplots_adjust(wspace=0.6)
plt.show()
