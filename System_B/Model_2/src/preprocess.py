"""
This script creates time series input for
optimise_district_heating.py

* heat demand time series
* electricity price time series

"""

__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

import os
import pandas as pd
from ast import literal_eval
# import datetime
from workalendar.europe import Germany
import yaml
import demandlib.bdew as bdew
import helpers


def prepare_timeseries_temperature(input_filename, output_filename):
    """
    Convert raw temperature data to appropriate format.
    """
    temperature = pd.read_csv(input_filename,
                              index_col=0,
                              usecols=['timestamp','T'],
                              parse_dates=True)
    temperature['T'] -= 273.15
    if not os.path.exists(os.path.dirname(output_filename)):
        os.makedirs(os.path.dirname(output_filename))
    temperature.to_csv(output_filename)
    return temperature


def prepare_timeseries_price_electricity(input_filename, output_filename):
    r"""
    Prepare electricity price time series
    """
    electricity_spot_price = pd.read_csv(input_filename, sep=';', decimal=',', na_values='-')
    electricity_spot_price = electricity_spot_price['Deutschland/Österreich/Luxemburg[Euro/MWh]'].rename('price_electricity_spot')
    if not os.path.exists(os.path.dirname(output_filename)):
        os.makedirs(os.path.dirname(output_filename))
    electricity_spot_price.to_csv(output_filename, header=True)
    return None


def prepare_timeseries_demand_heat(year, parameter_bdew,
                                   temperature, output_filename):
    """
    Create synthetic heat profiles using the BDEW method.
    """
    # get holidays for germany
    cal = Germany()
    holidays = dict(cal.holidays(year))

    # create a DataFrame to hold the timeseries
    demand = pd.DataFrame(index=temperature.index)
    for component, parameter_list in parameter_bdew.items():
        # print(component)
        component_demand = pd.DataFrame()
        for item in parameter_list:
            timeseries_demand = bdew.HeatBuilding(demand.index,
                                                  holidays=holidays,
                                                  temperature=temperature,
                                                  name=item['shlp_type'],
                                                  **item).get_bdew_profile()
            component_demand[item['shlp_type']] = timeseries_demand
        demand[component] = component_demand.sum(axis=1)
    # print(output_filename)
    # print(demand.head())
    if not os.path.exists(os.path.dirname(output_filename)):
        os.makedirs(os.path.dirname(output_filename))
    demand.to_csv(output_filename)
    return None


def preprocess(config_path, results_dir):
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    with open(config_path, 'r') as ymlfile:
        config = yaml.load(ymlfile)

    # load timeseries data
    timeseries_reference = os.path.join(abs_path, config['data_raw']['timeseries'])
    files = pd.read_csv(timeseries_reference).groupby('parameter_name')
    files_temperature = files.get_group('temperature')
    files_price_electricity_spot = files.get_group('price_electricity_spot')

    # Load bdew parameters
    filename_input_data = os.path.join(abs_path, config['data_raw']['scalars']['parameters'])
    input_parameter = pd.read_csv(filename_input_data)
    parameter_bdew = {}
    for label, group in input_parameter.groupby('component'):
        parameter_bdew[label] = []
        for i, row in group[['var_name', 'var_value']].iterrows():
            parameter_bdew[label].append({'shlp_type': row['var_name'], **literal_eval(row['var_value'])})

    for i, file in files_temperature.iterrows():
        # Create temperature profiles
        input_filename = os.path.join(abs_path, 'data', file['path'])
        output_filename = os.path.join(results_dir,
                                       'data_preprocessed',
                                       *file[['scenario', 'parameter_name']].values,
                                       f'{"_".join(map(str, file[["parameter_name", "year"]].values))}.csv')
        temperature = prepare_timeseries_temperature(input_filename, output_filename)

        # heat demand profiles for each temperature profile
        output_filename = os.path.join(results_dir,
                                       'data_preprocessed',
                                       file['scenario'],
                                       'demand_heat',
                                       f'{"_".join(["demand_heat", str(file["year"])])}.csv')
        prepare_timeseries_demand_heat(file['year'], parameter_bdew, temperature, output_filename)

    # Prepare spot market electricity price timeseries
    for i, file in files_price_electricity_spot.iterrows():
        input_filename = os.path.join(abs_path, 'data', file['path'])
        output_filename = os.path.join(results_dir,
                                       'data_preprocessed',
                                       *file[['scenario', 'parameter_name']].values,
                                       f'{"_".join(map(str, file[["parameter_name", "year"]].values))}.csv')
        prepare_timeseries_price_electricity(input_filename, output_filename)
    return None


if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    preprocess(config_path, results_dir)
