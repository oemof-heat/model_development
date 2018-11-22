# -*- coding: utf-8 -*-
"""

Date: 22nd of November 2018
Author: Jakob Wolf (jakob.wolf@beuth-hochschule.de)

"""

import pandas as pd
import os
import yaml
import matplotlib.pyplot as plt

def preprocess_timeseries(config_path):

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    file_name_param = cfg['parameters_load_profile']
    file_path_param = abs_path + file_name_param
    param_df = pd.read_csv(file_path_param, index_col=1)
    param_value = param_df['value']

    file_path_ts_loads = abs_path + cfg['time_series_loads']

    data = pd.read_csv(file_path_ts_loads, parse_dates=['utc_timestamp'])
    load_and_profiles = pd.DataFrame()
    load_and_profiles_szenario2030 = pd.DataFrame()
    coln_time = ['utc_timestamp']
    load_and_profiles[coln_time] = (data[coln_time])
    coln = ['utc_timestamp', 'DE_load_entsoe_power_statistics', 'DE_solar_profile', 'DE_wind_profile']
    load_and_profiles[coln] = data[coln]  # Load in MW
    load_and_profiles_2011 = load_and_profiles[(load_and_profiles['utc_timestamp'] > '2010-12-31 23:00:00')
                                               & (load_and_profiles['utc_timestamp'] < '2012-01-01 00:00:00')]
    # Remove 29th of Feb
    load_and_profiles_2012_1 = load_and_profiles[(load_and_profiles['utc_timestamp'] > '2011-12-31 23:00:00')
                                               & (load_and_profiles['utc_timestamp'] < '2012-02-29 00:00:00')]
    load_and_profiles_2012_2 = load_and_profiles[(load_and_profiles['utc_timestamp'] > '2012-02-29 23:00:00')
                                               & (load_and_profiles['utc_timestamp'] < '2013-01-01 00:00:00')]

    load_and_profiles_2012 = pd.concat([load_and_profiles_2012_1, load_and_profiles_2012_2])

    load_and_profiles_2011.reset_index(inplace=True)
    load_and_profiles_2012.reset_index(inplace=True)

    # print(len(load_and_profiles_2011))
    # print(len(load_and_profiles_2012))
    # print(load_and_profiles_2012)
    # print(load_and_profiles_2011['DE_wind_profile'].head())
    # print(load_and_profiles_2011.tail())
    load_and_profiles_szenario2030['utc_timestamp'] = load_and_profiles_2012['utc_timestamp']
    load_and_profiles_szenario2030['load_MW'] = \
        load_and_profiles_2012['DE_load_entsoe_power_statistics']
    load_and_profiles_szenario2030['solar_generation_MW'] = \
        load_and_profiles_2012['DE_solar_profile']\
        *param_value['cap_inst_PV_2040']*1000
    load_and_profiles_szenario2030['wind_generation_MW'] = \
        load_and_profiles_2012['DE_wind_profile']\
        *(param_value['cap_inst_wind_onshore_2040'] + param_value['cap_inst_wind_offshore_2040'])*1000
    load_and_profiles_szenario2030['EE_generation_MW'] = \
        load_and_profiles_szenario2030['solar_generation_MW'] + load_and_profiles_szenario2030['wind_generation_MW']
    load_and_profiles_szenario2030['residual_load_MW'] = \
        load_and_profiles_szenario2030['load_MW'] - load_and_profiles_szenario2030['EE_generation_MW']
    # print(load_and_profiles_szenario2030.head())
    plt.plot(load_and_profiles_szenario2030['utc_timestamp'], load_and_profiles_szenario2030['residual_load_MW'])
    plt.xlabel('Zeit')
    plt.ylabel('Leistung in MW')
    plt.title('Residuallastverlauf (installierte Kapazitaeten nach Basisszenario 2040)')
    plt.suptitle('53,7% EE-Strom, 439h negative Residuallast')
    plt.savefig("../results/plots/Residuallastverlauf.png", dpi=300)
    # plt.show()
    print("")
    print(load_and_profiles_szenario2030.head())
    print(load_and_profiles_szenario2030['residual_load_MW'][(load_and_profiles_szenario2030['residual_load_MW'] < 0)].count(), " h")
    print("PV: ", load_and_profiles_szenario2030['solar_generation_MW'].sum()/1e6, " TWh")
    water_and_biomass_TWh = param_value['misc_renewables_gen_2040_TWh'] \
                            + param_value['biomass_gen_2040_TWh'] \
                            + param_value['biomass_CHP_gen_2040_TWh']
    print("EE gesamt: ", load_and_profiles_szenario2030['EE_generation_MW'].sum()/1e6+water_and_biomass_TWh, " TWh")
    print("Load DT: ", load_and_profiles_szenario2030['load_MW'].sum()/1e6, " TWh")
    print("Anteil EE an Stromproduktion ", (load_and_profiles_szenario2030['EE_generation_MW'].sum()+water_and_biomass_TWh*1e6)
    /load_and_profiles_szenario2030['load_MW'].sum(), " %")

    print("***Precrocessing: Finish!***")
