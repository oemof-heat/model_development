import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(os.path.dirname(currentdir))
sys.path.append(parentdir)
import pandas as pd
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import connection_oep as coep
import xlrd


""" DOCUMENTATION FOR upload.py

load data
---------
Creates an empty dictionary. Imports the data from 'data_public', and adds it
to the empty dictionary. Every file ends with '.csv' is considered. The empty
cells are changed with 'None', instead of pandas 'NaN'.

load data (timeseries)
----------------------
Same as load data, however this time the data is imported from excel file.

create tables for OEP & create tables for OEP (timeseries)
----------------------------------------------------------
Creates sqlalchemy tables in order to prepare the OEP for upload. Sqlalchemy
table contains the data type of the individual columns in the data.
'index' is always the primary key and its type is integer.
Column names should be written in lowercase letters and divided by '_'
instead of ' '.

upload & upload (timeseries)
----------------------------
Uploads the data to OEP via upload_to_oep()

---THIS SHOULD BE MOVED SOMEWHERE ELSE---
download & download (timeseries)
--------------------------------
Downloads the data from OEP via get_df()
Note: for timeseries the download code is missing
---THIS SHOULD BE MOVED SOMEWHERE ELSE---

"""

# establish connection to oep
engine, metadata = coep.connect_oep()
print('Connection established')

# load data
df = {}
for file in os.listdir('data_public'):
    if file.endswith('.csv'):
        df[file[:-4]] = pd.read_csv('data_public/'+file, encoding='utf8', sep=',')
        df[file[:-4]] = df[file[:-4]].where((pd.notnull(df[file[:-4]])), None)
    else:
        continue

# load data (timeseries)
for file in os.listdir('data_public_timeseries'):
    if file.endswith('.xlsx'):
        df[file[:-5]] = pd.ExcelFile('data_public_timeseries/'+file).parse('Daten')
        df[file[:-5]] = df[file[:-5]].where((pd.notnull(df[file[:-5]])), None)
    else:
        continue


# create tables for OEP
table = {}
for file in os.listdir('data_public'):
    if file.endswith('.csv'):
        table[file[:-4]] = sa.Table(
            ('flexchp_sysopt_'+file[:-4]).lower(),
            metadata,
            sa.Column('index', sa.Integer, primary_key=True, autoincrement=True,
                      nullable=False),
            sa.Column('id', sa.Integer),
            sa.Column('var_name', sa.VARCHAR(50)),
            sa.Column('value', sa.Float()),
            sa.Column('unit', sa.VARCHAR(50)),
            sa.Column('component', sa.VARCHAR(50)),
            schema='model_draft')
    else:
        continue

# create tables for OEP (timeseries)
for file in os.listdir('data_public_timeseries'):
    if file.endswith('.xlsx') and file[:-5] == 'district_heating_load_profile':
        table[file[:-5]] = sa.Table(
            ('flexchp_sysopt_'+file[:-5]).lower(),
            metadata,
            sa.Column('index', sa.Integer, primary_key=True, autoincrement=True,
                      nullable=False),
            sa.Column('timestamp', sa.DATETIME),
            sa.Column('district_heating_profile', sa.Float()),
            schema='model_draft')
    elif file.endswith('.xlsx') and file[:-5] == 'power_statistics_timeseries_60min':
        table[file[:-5]] = sa.Table(
            ('flexchp_sysopt_'+file[:-5]).lower(),
            metadata,
            sa.Column('index', sa.Integer, primary_key=True, autoincrement=True,
                      nullable=False),
            sa.Column('timestamp', sa.DATETIME),
            sa.Column('de_load_entsoe_power_statistics', sa.Integer),
            sa.Column('de_solar_generation_actual', sa.Integer),
            sa.Column('de_solar_profile', sa.Float()),
            sa.Column('de_wind_generation_actual', sa.Integer),
            sa.Column('de_wind_profile', sa.Float()),
            schema='model_draft')
    else:
        continue

# upload
for file in os.listdir('data_public'):
    if file.endswith('.csv'):
        table[file[:-4]] = coep.upload_to_oep(df[file[:-4]],
                                              table[file[:-4]],
                                              engine, metadata)
    else:
        continue

# upload (timeseries)
for file in os.listdir('data_public_timeseries'):
    if file.endswith('.xlsx'):
        table[file[:-5]] = coep.upload_to_oep(df[file[:-5]],
                                              table[file[:-5]],
                                              engine, metadata)
    else:
        continue

# download
"""
data = {}
for file in os.listdir('data_public'):
    if file.endswith('.csv'):
        data[file[:-4]] = coep.get_df(engine, table[file[:-4]])
        data[file[:-4]] = data[file[:-4]].drop(columns='index')
    else:
        continue
"""
