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

    file_path_ts_loads_el = abs_path + cfg['time_series_loads_el']
    file_path_ts_loads_heat = abs_path + cfg['time_series_loads_heat']

    data = pd.read_csv(file_path_ts_loads_el, parse_dates=['utc_timestamp'])
    xls = pd.ExcelFile(file_path_ts_loads_heat)
    data_heat = pd.read_excel(xls, 'Daten', header=None, usecols='E', names=['district_heating_profile_2012'])  # [%]

    load_and_profiles = pd.DataFrame()
    demand_profiles = pd.DataFrame()

    load_and_profiles_szenario2040 = pd.DataFrame()
    coln_time = ['utc_timestamp']
    load_and_profiles[coln_time] = (data[coln_time])
    coln = ['utc_timestamp', 'DE_load_entsoe_power_statistics', 'DE_solar_profile', 'DE_wind_profile']
    load_and_profiles[coln] = data[coln]  # Load in MW
    load_and_profiles_2011 = load_and_profiles[(load_and_profiles['utc_timestamp'] > '2010-12-31 23:00:00')
                                               & (load_and_profiles['utc_timestamp'] < '2012-01-01 00:00:00')]
    remove_29th_Feb = False
    if remove_29th_Feb==True:
        load_and_profiles_2012_1 = load_and_profiles[(load_and_profiles['utc_timestamp'] > '2011-12-31 23:00:00')
                                                   & (load_and_profiles['utc_timestamp'] < '2012-02-29 00:00:00')]
        load_and_profiles_2012_2 = load_and_profiles[(load_and_profiles['utc_timestamp'] > '2012-02-29 23:00:00')
                                                   & (load_and_profiles['utc_timestamp'] < '2013-01-01 00:00:00')]

        load_and_profiles_2012 = pd.concat([load_and_profiles_2012_1, load_and_profiles_2012_2])
    else:
        load_and_profiles_2012 = load_and_profiles[(load_and_profiles['utc_timestamp'] > '2011-12-31 23:00:00')
                                                   & (load_and_profiles['utc_timestamp'] < '2013-01-01 00:00:00')]


    load_and_profiles_2011.reset_index(inplace=True)
    load_and_profiles_2012.reset_index(inplace=True)

    load_and_profiles_szenario2040['utc_timestamp'] = load_and_profiles_2012['utc_timestamp']
    load_and_profiles_szenario2040['load_MW'] = \
        load_and_profiles_2012['DE_load_entsoe_power_statistics']
    load_and_profiles_szenario2040['solar_generation_MW'] = \
        load_and_profiles_2012['DE_solar_profile']\
        *param_value['cap_inst_PV_2040']*1000
    load_and_profiles_szenario2040['wind_generation_MW'] = \
        load_and_profiles_2012['DE_wind_profile']\
        *(param_value['cap_inst_wind_onshore_2040'] + param_value['cap_inst_wind_offshore_2040'])*1000
    load_and_profiles_szenario2040['EE_generation_MW'] = \
        load_and_profiles_szenario2040['solar_generation_MW'] + load_and_profiles_szenario2040['wind_generation_MW']
    load_and_profiles_szenario2040['residual_load_MW'] = \
        load_and_profiles_szenario2040['load_MW'] - load_and_profiles_szenario2040['EE_generation_MW']

    # Colors
    beuth_red = (227/255, 35/255, 37/255)
    beuth_col_1 = (223/255, 242/255, 243/255)
    beuth_col_2 = (178/255, 225/255, 227/255)
    beuth_col_3 = (0/255, 152/255, 161/255)

    plt.plot(load_and_profiles_szenario2040['utc_timestamp'], load_and_profiles_szenario2040['residual_load_MW'])
    plt.xlabel('Zeit')
    plt.ylabel('Leistung in MW')
    plt.title('Residuallastverlauf (installierte Kapazitaeten nach Basisszenario 2040)')
    plt.suptitle('53,7% EE-Strom, 439h negative Residuallast')
    plt.savefig("../results/plots/Residuallastverlauf.png", dpi=300)
    # plt.show()

    print("")
    # print(load_and_profiles_szenario2040.head())
    print(load_and_profiles_szenario2040['residual_load_MW'][(load_and_profiles_szenario2040['residual_load_MW'] < 0)].count(), " h")
    print("PV: ", load_and_profiles_szenario2040['solar_generation_MW'].sum()/1e6, " TWh")
    water_and_biomass_TWh = param_value['misc_renewables_gen_2040_TWh'] \
                            + param_value['biomass_gen_2040_TWh'] \
                            + param_value['biomass_CHP_gen_2040_TWh']
    print("EE gesamt: ", load_and_profiles_szenario2040['EE_generation_MW'].sum()/1e6+water_and_biomass_TWh, " TWh")
    print("Load DT: ", load_and_profiles_szenario2040['load_MW'].sum()/1e6, " TWh")
    print("Anteil EE an Stromproduktion ", (load_and_profiles_szenario2040['EE_generation_MW'].sum()+water_and_biomass_TWh*1e6)
    /load_and_profiles_szenario2040['load_MW'].sum(), " %")

    # Relative heat demand
    demand_profiles["demand_th"] = data_heat['district_heating_profile_2012'] / 100  # [-]

    # Relative electricity demand (only positive share of residual load)
    demand_el_max = load_and_profiles_szenario2040['residual_load_MW'].max()
    demand_profiles['demand_el'] = load_and_profiles_szenario2040['residual_load_MW'].clip(lower=0) / demand_el_max

    # Relative negative residual load (only negative share of residual load)
    # Values are turned positive and will be used as positive "source" in the oemof application
    demand_el_min = load_and_profiles_szenario2040['residual_load_MW'].min()
    demand_profiles['neg_residual_el'] = load_and_profiles_szenario2040['residual_load_MW'].clip(upper=0) / demand_el_min

    demand_profiles.to_csv(abs_path + cfg['demand_time_series'], encoding='utf-8', index=False)

    fig, ax = plt.subplots()
    plt.grid(color='grey' ,#beuth_col_2,
             linestyle='-',
             linewidth=0.5,
             zorder=1)
    ax.scatter(x=demand_profiles['demand_th']*1000,
               y=(demand_profiles['demand_el']*1000).add(demand_profiles['neg_residual_el']*-150),
               marker='.',
               c=[beuth_col_3],
               zorder=10)
    ax.set_ylabel('Strombedarf in $\mathrm{MW_{el}}$', fontsize=12)
    ax.set_xlabel('Wärmebedarf in $\mathrm{MW_{th}}$', fontsize=12)
    ax.set_ylim([-250, 1050])
    # plt.show()
    plt.savefig(cfg['demand_scatter_plot'], dpi=300)
    print("***Precrocessing: Finish!***")
