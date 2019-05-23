import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(os.path.dirname(currentdir))
sys.path.append(parentdir)
import pandas as pd
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import connection_oep as coep



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

# upload
for file in os.listdir('data_public'):
    if file.endswith('.csv'):
        table[file[:-4]] = coep.upload_to_oep(df[file[:-4]],
                                              table[file[:-4]],
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
