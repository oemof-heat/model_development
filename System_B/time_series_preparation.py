"""
This application creates time series input for 
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

abs_path = os.path.dirname(os.path.abspath(__file__))
filename = abs_path + '/data/' + 'temperature_data.csv'

temperature = pd.read_csv(filename)["temperature"]


cal = Germany()
holidays = dict(cal.holidays(2010))
holidays

# create a DataFrame to hold the timeseries
demand = pd.DataFrame(
    index=pd.date_range(pd.datetime(2010, 1, 1, 0),
                        periods=8760, freq='H'))

# Single family house (efh: Einfamilienhaus)
demand['efh'] = bdew.HeatBuilding(
    demand.index, holidays=holidays, temperature=temperature,
    shlp_type='EFH',
    building_class=1, wind_class=1, annual_heat_demand=25000,
    name='EFH').get_bdew_profile()

# Multi family house (mfh: Mehrfamilienhaus)
demand['mfh'] = bdew.HeatBuilding(
    demand.index, holidays=holidays, temperature=temperature,
    shlp_type='MFH',
    building_class=2, wind_class=0, annual_heat_demand=80000,
    name='MFH').get_bdew_profile()

# Industry, trade, service (ghd: Gewerbe, Handel, Dienstleistung)
demand['ghd'] = bdew.HeatBuilding(
    demand.index, holidays=holidays, temperature=temperature,
    shlp_type='ghd', wind_class=0, annual_heat_demand=140000,
    name='ghd').get_bdew_profile()


# save demand time series
demand.to_csv(abs_path+'/data/'+'demand_heat.csv')
