# -*- coding: utf-8 -*-
"""

Date: 27,05,2020

@author: Franziska Pleissner

System C: concrete example: Model of cooling process with absorption chiller,
                            using thermal solar collector


             input/output     gas   thermal  electr.  cool   waste   ambient(
                                                                    /ground)

naturalgas         |---------->|       |       |       |       |
                   |           |       |       |       |       |
grid_el            |-------------------------->|       |       |
                   |           |       |       |       |       |
pv                 |-------------------------->|       |       |
                   |           |       |       |       |       |
collector          |------------------>|       |       |       |
                   |           |       |       |       |       |
boiler             |           |------>|       |       |       |
                   |           |       |       |       |       |
                   |<------------------|       |       |       |
absorption_chiller |<--------------------------|       |       |
                   |---------------------------------->|       |
                   |------------------------------------------>|
                   |           |       |       |       |       |
cooling_tower      |<------------------------------------------|
                   |<--------------------------|       |       |       |
                   |-------------------------------------------------->|
                   |           |       |       |       |       |
aquifer            |<------------------------------------------|
                   |<--------------------------|       |       |       |
                   |-------------------------------------------------->|
                   |           |       |       |       |       |
storage_thermal    |------------------>|       |       |       |
                   |<------------------|       |       |       |
                   |           |       |       |       |       |
storage_electricity|-------------------------->|       |       |
                   |<--------------------------|       |       |
                   |           |       |       |       |       |
storage_cool       |---------------------------------->|       |
                   |<----------------------------------|       |
                   |           |       |       |       |       |
demand             |<----------------------------------|       |
                   |           |       |       |       |       |
excess             |<------------------|       |       |       |


"""

############
# Preamble #
############

# Import packages
from oemof.tools import logger, economics
import oemof.solph as solph
import oemof.outputlib as outputlib
from oemof.thermal.solar_thermal_collector import flat_plate_precalc

import logging
import os
import yaml
import pandas as pd
import pyomo.environ as po

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


def ep_costs_func(capex, n, opex, wacc):
    ep_costs = economics.annuity(capex, n, wacc) + capex * opex
    return ep_costs


def run_model_thermal(config_path, var_number):

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    solver = cfg['solver']
    debug = cfg['debug']
    solver_verbose = cfg['solver_verbose']  # show/hide solver output

    if debug:
        number_of_time_steps = 3
    else:
        number_of_time_steps = cfg['number_timesteps']

    # ## Read data and parameters ## #
    # Define the used directories
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    results_path = abs_path + '/results'
    data_ts_path = abs_path + '/data/data_confidential/'
    data_param_path = abs_path + '/data/data_public/'

    # Read parameter values from parameter file
    if type(cfg['parameters_variation']) == list:
        file_path_param_01 = data_param_path + cfg['parameters_system']
        file_path_param_02 = data_param_path + cfg['parameters_variation'][
            var_number]
    elif type(cfg['parameters_system']) == list:
        file_path_param_01 = data_param_path + cfg['parameters_system'][
            var_number]
        file_path_param_02 = data_param_path + cfg['parameters_variation']
    else:
        file_path_param_01 = data_param_path + cfg['parameters_system']
        file_path_param_02 = data_param_path + cfg['parameters_variation']
    param_df_01 = pd.read_csv(file_path_param_01, index_col=1)
    param_df_02 = pd.read_csv(file_path_param_02, index_col=1, sep=';')
    param_df = pd.concat([param_df_01, param_df_02], sort=True)
    param_value = param_df['value']

    # Import weather and demand data
    data = pd.read_csv(data_ts_path + cfg['time_series_file_name'])

    # Calculate collector data
    collector_precalc_data = flat_plate_precalc(
        param_value['latitude'],
        param_value['longitude'],
        param_value['collector_tilt'],
        param_value['collector_azimuth'],
        param_value['eta_0'],
        param_value['a_1'],
        param_value['a_2'],
        param_value['temp_collector_inlet'],
        param_value['delta_temp_n'],
        irradiance_global=data['global_irradiance_kW_per_m2_TMY'],
        irradiance_diffuse=data['diffus_irradiance_kW_per_m2_TMY'],
        temp_amb=data['t_amb'],
    )

    # Redefine ep_costs_function:
    def ep_costs_f(capex, n, opex):
        return ep_costs_func(capex, n, opex, param_value['wacc'])

    # Initiate the logger
    logger.define_logging(
        logfile='Oman_thermal_Ires_{0}_{1}.log'.format(cfg['exp_number'],
                                                       var_number),
        logpath=results_path + '/logs',
        screen_level=logging.INFO,
        file_level=logging.DEBUG)

    date_time_index = pd.date_range('1/1/2017',
                                    periods=number_of_time_steps,
                                    freq='H')

    # Initialise the energysystem
    logging.info('Initialize the energy system')

    energysystem = solph.EnergySystem(timeindex=date_time_index)

    #######################
    # Build up the system #
    #######################

    # Busses

    bth = solph.Bus(label='thermal')
    bco = solph.Bus(label="cool")
    bwh = solph.Bus(label="waste")
    bel = solph.Bus(label="electricity")
    bga = solph.Bus(label="gas")
    bam = solph.Bus(label="ambient")

    energysystem.add(bth, bco, bwh, bel, bga, bam)

    # Sinks and Sources

    ambience = solph.Sink(
        label='ambience',
        inputs={bam: solph.Flow()})

    grid_ga = solph.Source(
        label='naturalgas',
        outputs={bga: solph.Flow(
            variable_costs=(param_value['price_gas']
                            * float(param_value['price_gas_variation'])))})

    grid_el = solph.Source(
        label='grid_el',
        outputs={bel: solph.Flow(
            variable_costs=(param_value['price_electr']
                            * float(param_value['price_electr_variation'])))})

    collector = solph.Source(
        label='collector',
        outputs={bth: solph.Flow(
            fixed=True,
            actual_value=collector_precalc_data['collectors_heat'],
            investment=solph.Investment(
                ep_costs=ep_costs_f(
                    param_value['invest_costs_collect_output_th'],
                    param_value['lifetime_collector'],
                    param_value['opex_collector'])))})  # Has to be developed

    pv = solph.Source(
        label='pv',
        outputs={bel: solph.Flow(
            fixed=True,
            actual_value=data['PV normiert'],
            investment=solph.Investment(
                ep_costs=ep_costs_f(
                    param_value['invest_costs_pv_output_el_09708'],
                    param_value['lifetime_pv'],
                    param_value['opex_pv'])))})  # Einheit: 0.970873786 kWpeak

    demand = solph.Sink(
        label='demand',
        inputs={bco: solph.Flow(
            fixed=True,
            actual_value=data['Cooling load kW'],
            nominal_value=1)})

    excess = solph.Sink(
        label='excess_thermal',
        inputs={bth: solph.Flow()})

    excess_el = solph.Sink(
        label='excess_el',
        inputs={bel: solph.Flow()})

    energysystem.add(
        ambience, grid_ga, grid_el, collector,
        pv, demand, excess, excess_el)

    # Transformers

    if param_value['nominal_value_boiler_output_thermal'] == 0:
        boil = solph.Transformer(
            label='boiler',
            inputs={bga: solph.Flow()},
            outputs={bth: solph.Flow(
                investment=solph.Investment(
                    ep_costs=ep_costs_f(
                        param_value['invest_costs_boiler_output_th'],
                        param_value['lifetime_boiler'],
                        param_value['opex_boiler'])))},
            conversion_factors={
                bth: param_value['conv_factor_boiler_output_thermal']})
    else:
        boil = solph.Transformer(
            label='boiler',
            inputs={bga: solph.Flow()},
            outputs={bth: solph.Flow(
                nominal_value=param_value[
                    'nominal_value_boiler_output_thermal'])},
            conversion_factors={
                bth: param_value['conv_factor_boiler_output_thermal']})

    chil = solph.Transformer(
        label='absorption_chiller',
        inputs={
            bth: solph.Flow(),
            bel: solph.Flow()},
        outputs={
            bco: solph.Flow(
                investment=solph.Investment(
                    ep_costs=ep_costs_f(
                        param_value['invest_costs_absorption_output_cool'],
                        param_value['lifetime_absorption'],
                        param_value['opex_absorption']))),
            bwh: solph.Flow()},
        conversion_factors={
            bco: param_value['conv_factor_absorption_output_cool'],
            bwh: param_value['conv_factor_absorption_output_waste'],
            bth: param_value['conv_factor_absorption_input_th'],
            bel: param_value['conv_factor_absorption_input_el']})

    # aqui = solph.Transformer(
    #     label='aquifer',
    #     inputs={
    #         bwh: solph.Flow(
    #             investment=solph.Investment(
    #                 ep_costs=ep_costs_f(
    #                     param_value['invest_costs_aqui_input_th'],
    #                     param_value['lifetime_aqui'],
    #                     param_value['opex_aqui']))),
    #         bel: solph.Flow()},
    #     outputs={
    #         bam: solph.Flow()},
    #     conversion_factors={
    #         bwh: param_value['conv_factor_aquifer_input_waste'],
    #         bel: param_value['conv_factor_aquifer_input_el']})

    towe = solph.Transformer(
        label='cooling_tower',
        inputs={
            bwh: solph.Flow(
                investment=solph.Investment(
                    ep_costs=ep_costs_f(
                        param_value['invest_costs_tower_input_th'],
                        param_value['lifetime_tower'],
                        param_value['opex_tower']))),
            bel: solph.Flow()},
        outputs={bam: solph.Flow()},
        conversion_factors={bwh: param_value['conv_factor_tower_input_waste'],
                            bel: param_value['conv_factor_tower_input_el']})

    energysystem.add(chil, boil, towe)

    # storages

    if param_value['nominal_capacitiy_stor_cool'] == 0:
        stor_co = solph.components.GenericStorage(
            label='storage_cool',
            inputs={bco: solph.Flow()},
            outputs={bco: solph.Flow()},
            loss_rate=param_value['capac_loss_stor_cool'],
            # invest_relation_input_capacity=1 / 6,
            # invest_relation_output_capacity=1 / 6,
            inflow_conversion_factor=param_value[
                'conv_factor_stor_cool_input'],
            outflow_conversion_factor=param_value[
                'conv_factor_stor_cool_output'],
            investment=solph.Investment(
                ep_costs=ep_costs_f(
                    param_value['invest_costs_stor_cool_capacity'],
                    param_value['lifetime_stor_cool'],
                    param_value['opex_stor_cool'])))
    else:
        stor_co = solph.components.GenericStorage(
            label='storage_cool',
            inputs={bco: solph.Flow()},
            outputs={bco: solph.Flow()},
            loss_rate=param_value['capac_loss_stor_cool'],
            # invest_relation_input_capacity=1 / 6,
            # invest_relation_output_capacity=1 / 6,
            inflow_conversion_factor=param_value[
                'conv_factor_stor_cool_input'],
            outflow_conversion_factor=param_value[
                'conv_factor_stor_cool_output'],
            nominal_capacity=param_value[
                'nominal_capacitiy_stor_cool'])

    if param_value['nominal_capacitiy_stor_thermal'] == 0:
        stor_th = solph.components.GenericStorage(
            label='storage_thermal',
            inputs={bth: solph.Flow()},
            outputs={bth: solph.Flow()},
            loss_rate=param_value['capac_loss_stor_thermal'],
            # invest_relation_input_capacity=1 / 6,
            # invest_relation_output_capacity=1 / 6,
            inflow_conversion_factor=param_value[
                'conv_factor_stor_thermal_input'],
            outflow_conversion_factor=param_value[
                'conv_factor_stor_thermal_output'],
            investment=solph.Investment(
                ep_costs=ep_costs_f(
                    param_value['invest_costs_stor_thermal_capacity'],
                    param_value['lifetime_stor_thermal'],
                    param_value['opex_stor_thermal'])))
    else:
        stor_th = solph.components.GenericStorage(
            label='storage_thermal',
            inputs={bth: solph.Flow()},
            outputs={bth: solph.Flow()},
            loss_rate=param_value['capac_loss_stor_thermal'],
            # invest_relation_input_capacity=1 / 6,
            # invest_relation_output_capacity=1 / 6,
            inflow_conversion_factor=param_value[
                'conv_factor_stor_thermal_input'],
            outflow_conversion_factor=param_value[
                'conv_factor_stor_thermal_output'],
            nominal_capacity=param_value['nominal_capacitiy_stor_thermal'])

    if param_value['nominal_capacitiy_stor_el'] == 0:
        stor_el = solph.components.GenericStorage(
            label='storage_electricity',
            inputs={bel: solph.Flow()},
            outputs={bel: solph.Flow()},
            loss_rate=param_value['capac_loss_stor_el'],
            # invest_relation_input_capacity=1 / 6,
            # invest_relation_output_capacity=1 / 6,
            inflow_conversion_factor=param_value[
                'conv_factor_stor_el_input'],
            outflow_conversion_factor=param_value[
                'conv_factor_stor_el_output'],
            investment=solph.Investment(
                ep_costs=ep_costs_f(
                    (param_value['invest_costs_stor_el_capacity']
                     * float(param_value['capex_stor_el_variation'])),
                    param_value['lifetime_stor_el'],
                    param_value['opex_stor_el'])))
    else:
        stor_el = solph.components.GenericStorage(
            label='storage_electricity',
            inputs={bel: solph.Flow()},
            outputs={bel: solph.Flow()},
            loss_rate=param_value['capac_loss_stor_el'],
            # invest_relation_input_capacity=1 / 6,
            # invest_relation_output_capacity=1 / 6,
            inflow_conversion_factor=param_value[
                'conv_factor_stor_el_input'],
            outflow_conversion_factor=param_value[
                'conv_factor_stor_el_output'],
            nominal_capacity=param_value['nominal_capacitiy_stor_el'])

    energysystem.add(stor_co, stor_th, stor_el)

    ########################################
    # Create a model and solve the problem #
    ########################################

    # Initialise the operational model (create the problem) with constrains
    model = solph.Model(energysystem)

    # ## Add own constrains ## #
    # Create a block and add it to the system
    myconstrains = po.Block()
    model.add_component('MyBlock', myconstrains)
    demand_sum = sum(data['Cooling load kW'])
    myconstrains.solar_constr = po.Constraint(
        expr=((sum(model.flow[boil, bth, t] for t in model.TIMESTEPS))
              <= (demand_sum * param_value['sol_fraction_thermal']
                  * float(param_value['sol_fraction_thermal_variation']))))

    logging.info('Solve the optimization problem')
    model.solve(solver=solver, solve_kwargs={'tee': solver_verbose})

    if debug:
        filename = (results_path + '/lp_files/'
                    + 'Oman_thermal_model_4_{0}_{1}.lp'.format(cfg['exp_number'],
                                                            var_number))
        logging.info('Store lp-file in {0}.'.format(filename))
        model.write(filename, io_options={'symbolic_solver_labels': True})

    logging.info('Store the energy system with the results.')

    energysystem.results['main'] = outputlib.processing.results(model)
    energysystem.results['meta'] = outputlib.processing.meta_results(model)
    energysystem.results['param'] = (
        outputlib.processing.parameter_as_dict(model))

    energysystem.dump(
        dpath=(results_path + '/dumps'),
        filename='oman_thermal_model_4_{0}_{1}.oemof'.format(
            cfg['exp_number'], var_number))
