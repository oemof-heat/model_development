import pandas as pd
import requests
import os
import numpy as np
import helpers
import yaml

# Amtlicher Gemeindeschluessel:
# https://www.riserid.eu/data/user_upload/downloads/info-pdf.s/Diverses/Liste-Amtlicher-Gemeindeschluessel-AGS-2015.pdf
# Dessau Rosslau: 15001000

abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

def download_zensus_data(zensus_url):
    """
    Queries the zensus database and saves the result to data_raw.

    Returns
    -------
    None
    """
    try:
        url = zensus_url
        r = requests.get(url)
        open(abs_path + '/data_raw/heat_demand/zensus_alter_anzahlwohnungen_flaeche_anzahl.csv', 'wb').write(r.content)
    except ConnectionError as e:
        print(e)

def calculate_area_statistics():
    """
    Calculates the total area per building type and age.

    Returns
    -------
    zensus_data
    """
    zensus_data = pd.read_csv(abs_path + '/data_raw/zensus_alter_anzahlwohnungen_flaeche_anzahl.csv',
                                  delimiter=';', skiprows=6, skipfooter=7, encoding='ISO-8859-14',
                                  names=['Baujahr', 'Gebauede_Anzahl_Wohnungen', 'Groesse_m2', 'Anzahl'],
                                  engine='python')

    # clean data
    zensus_data['Groesse_m2'] = zensus_data['Groesse_m2']\
        .str[-3:]\
        .replace(['ehr','amt'], np.nan)\
        .astype('float')

    zensus_data['Anzahl'] = zensus_data['Anzahl']\
        .str.replace('(', '')\
        .str.replace(')', '')\
        .replace(['-'], np.nan)\
        .astype('float')

    # calculate total area
    zensus_data['area'] = zensus_data['Anzahl'] * zensus_data['Groesse_m2']

    # save the result
    zensus_data.to_csv(abs_path + '/data_raw/area.csv')

    return zensus_data

def calculate_annual_heat_demand(zensus_data, heat_demand_per_area):
    r"""

    Parameters
    ----------

    Returns
    -------
    annual_heat_demand : pandas DataFrame

    """
    # group
    zensus_part = zensus_data.groupby(['Gebauede_Anzahl_Wohnungen','Baujahr'])['area'].sum()
    print(zensus_data)
    # remove 'Insgesamt'
    for level in [0,1]:
        zensus_part = zensus_part.drop(labels='Insgesamt', level=level)

    zensus_part.index = zensus_part.index.remove_unused_levels()

    # unstack, sort and rename index
    heat_per_area_part = heat_demand_per_area.unstack()
    heat_per_area_part = heat_per_area_part.sort_index()
    heat_per_area_part.index.names = ['Gebauede_Anzahl_Wohnungen', 'Baujahr']

    # multiply heat demand per area with area to get heat demand
    annual_heat_demand = heat_per_area_part.multiply(zensus_part)
    annual_heat_demand.name = 'heat_demand'

    annual_heat_demand = annual_heat_demand.unstack().reset_index()

    # pool heat demand for efh and mfh
    is_efh = annual_heat_demand['Gebauede_Anzahl_Wohnungen'] == '1 Wohnung'
    is_mfh = annual_heat_demand['Gebauede_Anzahl_Wohnungen'].isin(['13 und mehr Wohnungen','2 Wohnungen',
                                                            '3 - 6 Wohnungen','7 - 12 Wohnungen'])
    annual_heat_demand_efh = annual_heat_demand[is_efh]
    annual_heat_demand_mfh = annual_heat_demand[is_mfh].sum(0)

    print(annual_heat_demand_efh.stack())
    print(annual_heat_demand_mfh)

    # map to Baualtersklassen
    #print(heat_demand.groupby(['Gebauede_Anzahl_Wohnungen']['heat_demand'].sum()))

    return annual_heat_demand

def prepare_zensus_data(config_path, results_dir):
    r"""
    Prepare heat demand data.

    Parameters
    ----------
    config_path : path
        path of experiment config

    results_dir : path
        path of results directoryconfig_path, results_dir)

    Returns
    -------
    None
    """
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    download_zensus_data(cfg['raw']['zensus_url'])
    zensus_data = calculate_area_statistics()
    heat_demand_per_area_interpolated = pd.read_csv(abs_path +
                                                    '/data_raw/heat_demand/dena_heat_demand_per_area_interpolated.csv',
                                                    index_col='year')
    annual_heat_demand = calculate_annual_heat_demand(zensus_data, heat_demand_per_area_interpolated)
    annual_heat_demand.to_csv(os.path.join(abs_path,cfg['raw']['annual_heat_demand']))

    return None


if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    prepare_zensus_data(config_path, results_dir)