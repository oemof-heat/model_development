# -*- coding: utf-8 -*-
"""
Created on Dez 06 2018

@author: Franziska Pleissner

System C: concrete example: Plot ocooling process with a solar collector
"""

############
# Preamble #
############

# Import packages
from oemof.tools import logger
import oemof.solph as solph

import oemof.outputlib as outputlib
import oemof_visio as oev

import logging
import os
import yaml
import pandas as pd
from SystemC_oman_electric import ep_costs_func

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

df_all_var = pd.DataFrame()


def make_csv_and_plot_electric(config_path, var_number):
    global df_all_var

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # define the used directories
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    results_path = abs_path + '/results'
    csv_path = results_path + '/optimisation_results/'
    plot_path = results_path + '/plots/'

    energysystem = solph.EnergySystem()
    energysystem.restore(dpath=(results_path + '/dumps'),
                         filename='oman_electric_{0}_{1}.oemof'.format(cfg['exp_number'], var_number))

    sp = cfg['start_of_plot']
    ep = cfg['end_of_plot']

    logging.info('results received')

    #########################
    # Work with the results #
    #########################

    results_strings = outputlib.views.convert_keys_to_strings(energysystem.results['main'])

    cool_bus = outputlib.views.node(energysystem.results['main'], 'cool')
    waste_bus = outputlib.views.node(energysystem.results['main'], 'waste')
    el_bus = outputlib.views.node(energysystem.results['main'], 'electricity')
    ambient_res = outputlib.views.node(energysystem.results['main'], 'ambient')
    none_res = outputlib.views.node(energysystem.results['main'], 'None')

    # sequences:
    cool_seq = cool_bus['sequences']
    waste_seq = waste_bus['sequences']
    el_seq = el_bus['sequences']
    ambient_seq = ambient_res['sequences']

    # scalars
    cool_scal = cool_bus['scalars']
    waste_scal = waste_bus['scalars']
    el_scal = el_bus['scalars']
    # non_scal = none_res['scalars']
    none_scal_given = outputlib.views.node(energysystem.results['param'], 'None')['scalars']
    el_scal[(('pv', 'electricity'), 'invest')] = el_scal[(('pv', 'electricity'), 'invest')]*0.7616
    # Umrechnung, da das Invest-object der pv auf 0.7616 kWpeak normiert ist.

    # solarer Deckungsanteil
    # elektrisch:
    df_control_el = pd.DataFrame()
    df_control_el['grid_el'] = el_seq[(('grid_el', 'electricity'), 'flow')]
    df_control_el['excess'] = el_seq[(('electricity', 'excess_el'), 'flow')]
    df_control_el['Product'] = df_control_el['grid_el'] * df_control_el['excess']

    el_from_grid = el_seq[(('grid_el', 'electricity'), 'flow')].sum()
    el_from_pv = el_seq[(('pv', 'electricity'), 'flow')].sum()
    el_to_excess = el_seq[(('electricity', 'excess_el'), 'flow')].sum()
    el_pv_used = el_from_pv - el_to_excess
    sol_fraction_el = el_pv_used / (el_pv_used + el_from_grid)

    # Stromverbrauch:
    el_used = el_seq[(('grid_el', 'electricity'), 'flow')].sum()

    ### Kosten ###
    costs_total = energysystem.results['meta']['objective']
        # Speicherkosten müssen im Basisfall abgezogen werden, oder bei den anderen Beispielen hinzugerechnet werden.

    # für Basisfall:
    if cfg['exp_number'] == 20:
        costs_total_wo_stor = costs_total - ((none_scal[(('storage_electricity', 'None'), 'invest')]
                                              * none_scal_given[(('storage_electricity', 'None'), 'investment_ep_costs')]) +
                                             (none_scal[(('storage_cool', 'None'), 'invest')]
                                              * none_scal_given[(('storage_cool', 'None'), 'investment_ep_costs')]))
    # für alle anderen Fälle:
    else:
        # Kosten für die Investition müssen ermittelt werden. Dafür müssen die Parameter hier auch eignelesen werden.
        filename_param = abs_path + '/data/data_public/' + cfg['parameters_file_name'][var_number]
        param_df = pd.read_csv(filename_param, index_col=1, sep=';')  # uses second column of csv-file for indexing
        param_value = param_df['value']
        # Berechnung der ep_costs
        ep_costs_el_stor = ep_costs_func(param_value['invest_costs_stor_el_capacity'],
                           param_value['lifetime_stor_el'], param_value['opex_stor_el'], param_value['wacc'])
        ep_costs_cool_stor = ep_costs_func(param_value['invest_costs_stor_cool_capacity'],
                             param_value['lifetime_stor_cool'], param_value['opex_stor_cool'], param_value['wacc'])
        # Berechnung der Kosten der Variante inklusive der Speicher
        costs_total_w_stor = costs_total + ((none_scal_given[(('storage_cool', 'None'), 'nominal_capacity')]
                                            * ep_costs_cool_stor) +
                                            (none_scal_given[(('storage_electricity', 'None'), 'nominal_capacity')]
                                            * ep_costs_el_stor))

    ########################
    # Write results in csv #
    ########################

    # scalars:
    scalars_all = cool_scal.append(waste_scal).append(el_scal)
    for i in range(0, none_scal_given.count()):
        if 'nominal_capacity' in none_scal_given.index[i]:
            scalars_all = pd.concat([scalars_all, pd.Series([none_scal_given[i]], index=[none_scal_given.index[i]])])
    scalars_all = pd.concat([scalars_all, pd.Series([sol_fraction_el], index=["('solar fraction', 'electric'), ' ')"])])
    if df_control_el['Product'].sum() != 0:
        scalars_all = pd.concat([scalars_all, pd.Series([df_control_el['Product'].sum()], index=["Has to be 0!!!"])])
    scalars_all = pd.concat([scalars_all, pd.Series([el_used], index=["('grid_el', 'electricity'), 'summe')"])])
    if cfg['exp_number'] != 20:
        scalars_all = pd.concat(
            [scalars_all, pd.Series([costs_total_w_stor], index=["('costs', 'w_stor'), 'per year')"])])
    scalars_all = pd.concat([scalars_all, pd.Series([costs_total], index=["('costs', 'wo_stor'), 'per year')"])])
    if cfg['exp_number'] == 20:
        scalars_all = pd.concat(
            [scalars_all, pd.Series([costs_total_wo_stor], index=["('costs', 'wo stor'), 'per year')"])])
    scalars_all = pd.concat([scalars_all, pd.Series(['{0}_{1}'.format(cfg['exp_number'], var_number)], index=["('Exp', 'Var'), 'number')"])])

    scalars_all.to_csv(csv_path + 'Oman_electric_{0}_{1}_scalars.csv'.format(cfg['exp_number'], var_number))

    df_all_var = pd.concat([df_all_var, scalars_all], axis=1, sort=True)
    if var_number == (cfg['number_of_variations']-1):
        df_all_var.to_csv(csv_path + 'Oman_electric_{0}_scalars_all_variations.csv'.format(cfg['exp_number']))
        logging.info('Writing DF_all_variations into csv')

    # sequences:
        # If you just want to add some parts of the sequences, not all:
        #               mydf[('boiler', 'thermal'), 'flow'] = thermal_seq[(('boiler', 'thermal'), 'flow')]
    sequences_df = pd.merge(ambient_seq, waste_seq, left_index=True, right_index=True)
    sequences_df = pd.merge(sequences_df, el_seq, left_index=True, right_index=True)
    sequences_df = pd.merge(sequences_df, cool_seq, left_index=True, right_index=True)
    sequences_df.to_csv(csv_path + 'Oman_electric_{0}_{1}_sequences.csv'.format(cfg['exp_number'], var_number))

    ########################
    # Plotting the results #
    ########################

    cool_seq_resample = cool_seq.iloc[sp:ep]
    waste_seq_resample = waste_seq.iloc[sp:ep]
    el_seq_resample = el_seq.iloc[sp:ep]
    ambient_seq_resample = ambient_seq.iloc[sp:ep]

    def shape_legend(node, reverse=False, **kwargs):  # just copied
        handels = kwargs['handles']
        labels = kwargs['labels']
        axes = kwargs['ax']
        parameter = {}

        new_labels = []
        for label in labels:
            label = label.replace('(', '')
            label = label.replace('), flow)', '')
            label = label.replace(node, '')
            label = label.replace(',', '')
            label = label.replace(' ', '')
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
        (('absorption_chiller', 'cool'), 'flow'): '#4682b4',
        (('storage_cool', 'cool'), 'flow'): '#555555',
        (('cool', 'storage_cool'), 'flow'): '#9acd32',
        (('cool', 'demand'), 'flow'): '#cd0000',
        (('el_grid', 'electricity'), 'flow'): '#999999',
        (('pv', 'electricity'), 'flow'): '#ffde32',
        (('storage_el', 'electricity'), 'flow'): '#9acd32',
        (('electricity', 'storage_el'), 'flow'): '#9acd32',
        (('electricity', 'cooling_tower'), 'flow'): '#ff0000',
        (('electricity', 'aquifer'), 'flow'): '#555555',
        (('storage_cool', 'None'), 'capacity'): '#555555',
        (('storage_cool', 'cool'), 'flow'): '#9acd32',
        (('absorpion_chiller', 'waste'), 'flow'): '#4682b4',
        (('waste', 'cool_tower'), 'flow'): '#42c77a'}

    # define order of inputs and outputs
    inordercool = [(('absorption_chiller', 'cool'), 'flow'),
                   (('storage_cool', 'cool'), 'flow')]
    outordercool = [(('cool', 'demand'), 'flow'),
                    (('cool', 'storage_cool'), 'flow')]
    inorderel = [(('pv', 'electricity'), 'flow'),
                 (('storage_el', 'electricity'), 'flow'),
                 (('el_grid', 'electricity'), 'flow')]
    outorderel = [(('electricity', 'cooling_tower'), 'flow'),
                  (('electricity', 'aquifer'), 'flow'),
                  (('electricity', 'storage_electricity'), 'flow')]
    # inorderstor = [(('cool', 'storage_cool'), 'flow')]
    # outorderstor = [(('storage_cool', 'cool'), 'flow'),
    #                 (('storage_cool', 'None'), 'capacity')]

    fig = plt.figure(figsize=(15, 15))

    # plot electrical energy
    my_plot_el = oev.plot.io_plot(
            'electricity', el_seq_resample, cdict=cdict,
            inorder=inorderel, outorder=outorderel,
            ax=fig.add_subplot(2, 2, 1), smooth=False)

    ax_el = shape_legend('electricity', **my_plot_el)
    oev.plot.set_datetime_ticks(ax_el, el_seq_resample.index, tick_distance=14,
                                date_format='%d-%m-%H', offset=1)

    ax_el.set_ylabel('Power in kW')
    ax_el.set_xlabel('time')
    ax_el.set_title("electricity")

    #
    # def shape_legend_stor(node, reverse=False, **kwargs):  # just copied
    #     handels = kwargs['handles']
    #     labels = kwargs['labels']
    #     axes = kwargs['ax']
    #     parameter = {}
    #
    #     new_labels = []
    #     for label in labels:
    #         label = label.replace('(', '')
    #         label = label.replace('), flow)', '')
    #         label = label.replace('None', '')
    #         label = label.replace(')', '')
    #         label = label.replace('_'+str(node), '')
    #         label = label.replace(node, '')
    #         label = label.replace(',', '')
    #         label = label.replace(' ', '')
    #         label = label.replace('cool', 'input/output')
    #         if label not in new_labels:
    #             new_labels.append(label)
    #     labels = new_labels
    #
    #     parameter['bbox_to_anchor'] = kwargs.get('bbox_to_anchor', (1, 1))
    #     parameter['loc'] = kwargs.get('loc', 'upper left')
    #     parameter['ncol'] = kwargs.get('ncol', 1)
    #     plotshare = kwargs.get('plotshare', 0.9)
    #
    #     if reverse:
    #         handels = handels.reverse()
    #         labels = labels.reverse()
    #
    #     box = axes.get_position()
    #     axes.set_position([box.x0, box.y0, box.width * plotshare, box.height])
    #
    #     parameter['handles'] = handels
    #     parameter['labels'] = labels
    #     axes.legend(**parameter)
    #     return axes
    #
    #
    # # plot storage capacity
    # my_plot_stor = oev.plot.io_plot(
    #         'storage_cool', ambient_seq_resample, cdict=cdict,
    #         inorder=inorderstor, outorder=outorderstor,
    #         ax=fig.add_subplot(2, 2, 4), smooth=False)
    #
    # ax_stor = shape_legend_stor('storage_cool', **my_plot_stor)
    # oev.plot.set_datetime_ticks(ax_stor, ambient_seq_resample.index,
    #                             tick_distance=14,
    #                             date_format='%d-%m-%H', offset=1)
    #
    # ax_stor.set_ylabel('Power in kW and capacity in kWh')
    # ax_stor.set_xlabel('time')
    # ax_stor.set_title("cooling storage")

    plt.savefig(plot_path + 'Oman_electric_{0}_{1}.png'.format(cfg['exp_number'], var_number))
    csv_plot = pd.merge(el_seq_resample, cool_seq_resample, left_index=True, right_index=True)
    csv_plot = pd.merge(csv_plot, el_seq_resample, left_index=True, right_index=True)
    csv_plot.to_csv(plot_path + 'Oman_telectric_plot_{0}_{1}.csv'.format(cfg['exp_number'], var_number))

    # plt.show()

    return df_all_var
