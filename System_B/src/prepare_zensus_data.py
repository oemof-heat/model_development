import pandas as pd
import requests
import os
import numpy as np
# Amtlicher Gemeindeschluessel:
# https://www.riserid.eu/data/user_upload/downloads/info-pdf.s/Diverses/Liste-Amtlicher-Gemeindeschluessel-AGS-2015.pdf
# Dessau Rosslau: 15001000


abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))


def get_zensus_data():
    # Einige Abfragen der zensus Datenbank:
    # get
    url = 'https://ergebnisse.zensus2011.de/auswertungsdb/download?csv=dynTable&tableHash=statUnit=GEBAEUDE;absRel=ANZAHL;ags=150010000000;agsAxis=X;yAxis=GEBAEUDEART_SYS,BAUJAHR_MZ,GEBTYPBAUWEISE,ZAHLWOHNGN_HHG&locale=DE'
    r = requests.get(url)
    open(abs_path + '/data/raw/zensus_1.csv', 'wb').write(r.content)

    # get
    url = 'https://ergebnisse.zensus2011.de/auswertungsdb/download?csv=dynTable&tableHash=statUnit=GEBAEUDE;absRel=ANZAHL;ags=150010000000;agsAxis=X;yAxis=HEIZTYP,BAUJAHR_MZ,GEBTYPGROESSE&locale=DE'
    r = requests.get(url)
    open(abs_path + '/data/raw/zensus_2.csv', 'wb').write(r.content)

    # get (this one is not the same as shown in the excel of Marcus)
    url = 'https://ergebnisse.zensus2011.de/#dynTable:statUnit=GEBAEUDE;absRel=ANZAHL;ags=15082,15091,150010000000;agsAxis=X;yAxis=ZAHLWOHNGN_HHG,BAUJAHR_MZ'
    r = requests.get(url)
    open(abs_path + '/data/raw/zensus_3.csv', 'wb').write(r.content)

    # get
    url = 'https://ergebnisse.zensus2011.de/#dynTable:statUnit=WOHNUNG;absRel=ANZAHL;ags=150010000000,150820005005,150820015015,150820180180,150820241241,150820256256,150820301301,150820340340,150820377377,150820430430,150820440440,150910010010,150910020020,150910060060,150910110110,150910145145,150910160160,150910241241,150910375375,150910391391;agsAxis=X;yAxis=BAUJAHR_MZ,WOHNFLAECHE_20S'
    r = requests.get(url)
    open(abs_path + '/data/raw/zensus_4.csv', 'wb').write(r.content)

    # get
    url = 'https://ergebnisse.zensus2011.de/auswertungsdb/download?csv=dynTable&tableHash=statUnit=WOHNUNG;absRel=ANZAHL;ags=150010000000;agsAxis=X;yAxis=BAUJAHR_MZ,ZAHLWOHNGN_HHG,WOHNFLAECHE_10S&locale=DE'
    r = requests.get(url)
    open(abs_path + '/data/raw/zensus_alter_anzahlwohnungen_flaeche_anzahl.csv', 'wb').write(r.content)

get_zensus_data()

zensus_shortcut = pd.read_csv(abs_path + '/data/raw/zensus_alter_anzahlwohnungen_flaeche_anzahl.csv', delimiter=';', skiprows=6, names=['Baujahr', 'Gebauede_Anzahl_Wohnungen', 'Groesse_m2', 'Anzahl'])
zensus_shortcut['area_per_flat'] = zensus_shortcut['Groesse_m2'].str[-3:].replace(['ehr','amt'], np.nan).astype('float')
zensus_shortcut['area'] = zensus_shortcut['Anzahl'].str.replace('(', '').str.replace(')', '').replace(['-'], np.nan).astype('float') * zensus_shortcut['area_per_flat']
print(zensus_shortcut)



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