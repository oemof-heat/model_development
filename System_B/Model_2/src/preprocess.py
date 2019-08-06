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
    electricity_spot_price = pd.read_csv(input_filename, sep=';', decimal=',')
    electricity_spot_price = electricity_spot_price['Deutschland/Österreich/Luxemburg[Euro/MWh]'].rename('electricity_spot_price')
    if not os.path.exists(os.path.dirname(output_filename)):
        os.makedirs(os.path.dirname(output_filename))
    electricity_spot_price.to_csv(output_filename, header=True)
    return None


def prepare_timeseries_demand_heat(year, bdew_parameters,
                                   temperature, output_filename):
    """
    Create synthetic heat profiles using the BDEW method.
    """
    # get holidays for germany
    cal = Germany()
    holidays = dict(cal.holidays(year))

    # create a DataFrame to hold the timeseries
    demand = pd.DataFrame(index=temperature.index)

    for key, param in bdew_parameters.items():
        demand[key] = bdew.HeatBuilding(
                demand.index, holidays=holidays, temperature=temperature,
                shlp_type=key,
                building_class=param['building_class'],
                wind_class=param['wind_class'],
                annual_heat_demand=param['annual_demand'],
                name=key).get_bdew_profile()

    # save heat demand time series
    if not os.path.exists(os.path.dirname(output_filename)):
        os.makedirs(os.path.dirname(output_filename))
    demand.sum(axis=1).rename('demand_heat').to_csv(output_filename, header=True)
    return None


def preprocess(config_path, results_dir):
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    with open(config_path, 'r') as ymlfile:
        config = yaml.load(ymlfile)

    # load timeseries data
    timeseries_reference = os.path.join(abs_path, config['data_raw']['timeseries'])
    files = pd.read_csv(timeseries_reference).groupby('parameter_name')
    files_temperature = files.get_group('temperature')
    files_electricity_spot_price = files.get_group('electricity_spot_price')

    for i, file in files_temperature.iterrows():
        input_filename = os.path.join(abs_path, 'data', file['path'])
        output_filename = os.path.join(results_dir,
                                       'data_preprocessed',
                                       *file[['scenario', 'parameter_name']].values,
                                       f'{"_".join(map(str, file[["parameter_name", "year"]].values))}.csv')
        temperature = prepare_timeseries_temperature(input_filename, output_filename)

        # # bdew_parameters = config['data_raw']['scalars']['bdew_parameters']
        bdew_parameters = {'efh': {'annual_demand': 0.357205 * 232000000, 'building_class': 4, 'wind_class': 1},
                           'mfh': {'annual_demand': 0.642795 * 232000000, 'building_class': 4, 'wind_class': 1}}
        output_filename = os.path.join(results_dir,
                                       'data_preprocessed',
                                       file['scenario'],
                                       'demand_heat',
                                       f'{"_".join(["demand_heat", str(file["year"])])}.csv')
        prepare_timeseries_demand_heat(file['year'], bdew_parameters, temperature, output_filename)

    for i, file in files_electricity_spot_price.iterrows():
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
