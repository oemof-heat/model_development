"""
This script creates time series input for
optimise_district_heating.py

* heat demand time series
* electricity price time series
* 

"""

__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"


import pandas as pd
import demandlib.bdew as bdew
import matplotlib
import matplotlib.pyplot as plt
import datetime
import os
from workalendar.europe import Germany
import yaml
import helpers

abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

def prepare_timeseries_temperature(config_path, results_dir):
    """
    convert raw temperature data to appropriate format.
    """
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # load temperature data
    output_file = os.path.join(results_dir, cfg['timeseries']['timeseries_temperature'])
    filename = os.path.join(abs_path, 'data_raw', cfg['raw']['temperature'])
    temperature = pd.read_csv(filename,
                              index_col=0,
                              usecols=['timestamp','T'],
                              parse_dates=True)
    temperature['T'] -= 273.15
    temperature.to_csv(output_file)

    return temperature

def prepare_timeseries_demand_heat(year, bdew_parameters, temperature,
                                   output_file):
    """
    Creates synthetic heat profiles using the BDEW method.
    """
    # get holidays for germany
    cal = Germany()
    holidays = dict(cal.holidays(year))

    # create a DataFrame to hold the timeseries
    demand = pd.DataFrame(
        index=pd.date_range(pd.datetime(year, 1, 1, 0),
                            periods=8760, freq='H'))
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
    demand.sum(axis=1).to_csv(output_file)

def prepare_timeseries_price_gas():
    # prepare gas price time series
    ger_day_ahead_prices_2006_2018 = pd.read_csv(abs_path +'/data/opsd-time_series-2018-06-30/time_series_60min_singleindex.csv', index_col='cet_cest_timestamp')['DE_price_day_ahead']
    print(ger_day_ahead_prices_2006_2018)
    ger_day_ahead_prices_2014 = ger_day_ahead_prices_2006_2018.loc['2014-01-01T00:00:00+0100':'2014-12-31T23:00:00+0100']
    ger_day_ahead_prices_2006_2018.to_csv(abs_path+'/data/'+'day_ahead_price_el_2006_2018.csv')
    ger_day_ahead_prices_2014.to_csv(abs_path+'/data/'+'day_ahead_price_el_2014.csv')

def prepare_timeseries_price_electricity():
    # prepare electricity price time series
    pass

def prepare_timeseries(config_path, results_dir):
    # open config
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # temperature
    temperature = prepare_timeseries_temperature(config_path, results_dir)

    # heat demand
    bdew_parameters = {'efh':{'annual_demand': 0.357205 * 232000000, 'building_class': 4, 'wind_class': 1},
                       'mfh':{'annual_demand': 0.642795 * 232000000, 'building_class': 4, 'wind_class': 1}}

    prepare_timeseries_demand_heat(2014, bdew_parameters, temperature,
                                   os.path.join(results_dir, cfg['timeseries']['timeseries_demand_heat']))

if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    prepare_timeseries(config_path, results_dir)
