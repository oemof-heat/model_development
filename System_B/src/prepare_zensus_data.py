import pandas as pd
import requests
import os
import numpy as np

# Amtlicher Gemeindeschluessel:
# https://www.riserid.eu/data/user_upload/downloads/info-pdf.s/Diverses/Liste-Amtlicher-Gemeindeschluessel-AGS-2015.pdf
# Dessau Rosslau: 15001000

abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

def download_zensus_data():
    """
    Queries the zensus database and saves the result to data_raw
    """
    try:
        url = 'https://ergebnisse.zensus2011.de/auswertungsdb/download?csv=dynTable&tableHash=statUnit=WOHNUNG;absRel=ANZAHL;ags=150010000000;agsAxis=X;yAxis=BAUJAHR_MZ,ZAHLWOHNGN_HHG,WOHNFLAECHE_10S&locale=DE'
        r = requests.get(url)
        open(abs_path + '/data_raw/zensus_alter_anzahlwohnungen_flaeche_anzahl.csv', 'wb').write(r.content)
    except:
        print('Download failed')


def calculate_area_statistics():
    """
    Calculates the total area by building type and age

    """
    zensus_data = pd.read_csv(abs_path + '/data_raw/zensus_alter_anzahlwohnungen_flaeche_anzahl.csv',
                                  delimiter=';', skiprows=6, skipfooter=7, encoding='ISO-8859-14',
                                  names=['Baujahr', 'Gebauede_Anzahl_Wohnungen', 'Groesse_m2', 'Anzahl'])

    # clean data
    zensus_data['Groesse_m2'] = zensus_data['Groesse_m2'].str[-3:].replace(['ehr','amt'], np.nan).astype('float')
    zensus_data['Anzahl'] = zensus_data['Anzahl'].str.replace('(', '').str.replace(')', '').replace(['-'], np.nan).astype('float')
    # calculate total area
    zensus_data['area'] = zensus_data['Anzahl'] * zensus_data['Groesse_m2']
    # save the result
    zensus_data.to_csv(abs_path + '/data_raw/area.csv')
    print(zensus_data.groupby(['Baujahr', 'Gebauede_Anzahl_Wohnungen'])['area'].sum())
    print(zensus_data.groupby(['Baujahr', 'Gebauede_Anzahl_Wohnungen'])['area'].sum().unstack())
    print(zensus_data['Baujahr'].unique())


def calculate_annual_heat_demand():
    heat_demand_per_area = pd.read_csv(abs_path + '/data_raw/dena_heat_demand_per_area.csv', index_col='year')
    print(heat_demand_per_area)


download_zensus_data()
calculate_area_statistics()
calculate_annual_heat_demand()


# filename = '/home/local/RL-INSTITUT/jann.launer/Desktop/oemof_repos/oemof_heat/System_B/data/raw/csv_GebaudeWohnungen/Zensus11_Datensatz_Gebaeude.csv'
# zensus = pd.read_csv(filename, delimiter=';', na_values='-')
# for i in zensus.columns:
#     print(i)
# print('aa', zensus.loc[zensus['AGS_12']==150010000000][['WHG_3.1','WHG_3.2','WHG_3.3']])

# #
# filename = '/home/local/RL-INSTITUT/jann.launer/Desktop/oemof_repos/oemof_heat/System_B/data/raw/csv_Haushalte_100m_Gitter/Haushalte100m.csv'
# gitter = pd.read_csv(filename, delimiter=',', na_values='-').head(1000)
# print(gitter['Merkmal'].unique())
# print(gitter.head(100))