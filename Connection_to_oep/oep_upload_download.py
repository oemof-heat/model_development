# connection

import connection_oep as coep
import pandas as pd
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

# establish connection to oep
engine, metadata = coep.connect_oep()
print('Connection established')

# load data
example_df = pd.read_csv('Daten_Beispiel/TemplateData.csv', encoding='utf8', sep=';')
input_parameters = pd.read_csv('Daten_Beispiel/data_thermal_energy_storage.csv')
timeseries = pd.read_csv('Daten_Beispiel/Electricity_price_spot_market_2016.csv')

ExampleTable = sa.Table(
    'example_dialect_table_5',
    metadata,
    sa.Column('index', sa.Integer, primary_key=True, autoincrement=True,
              nullable=False),
    sa.Column('variable', sa.VARCHAR(50)),
    sa.Column('unit', sa.VARCHAR(50)),
    sa.Column('year', sa.INTEGER),
    sa.Column('value', sa.FLOAT(50)),
    schema='sandbox'
)

input_param_table = sa.Table(
    'example_oea_parameter',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True,
              nullable=False),
    sa.Column('component_id', sa.Integer),
    sa.Column('version', sa.Float(10)),
    sa.Column('var_name', sa.String(50)),
    sa.Column('var_value', sa.Float(50)),
    sa.Column('var_unit', sa.String(10)),
    sa.Column('updated', sa.String(10)),
    sa.Column('reference', sa.String(10)),
    schema='sandbox')

timeseries_table = sa.Table(
    'example_oea_timeseries',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True,
              nullable=False),
    sa.Column('time', sa.String(50)),
    sa.Column('price_el', sa.Float(50)),
    schema='sandbox')

# upload
ExampleTable = coep.upload_to_oep(example_df, ExampleTable, engine, metadata)
ip_table = coep.upload_to_oep(input_parameters, input_param_table, engine, metadata)
ts_table = coep.upload_to_oep(timeseries, timeseries_table, engine, metadata)

# download
data = {}
data['ExampleTable'] = coep.get_df(engine, ExampleTable)
data['input_parameters'] = coep.get_df(engine, ip_table)
data['timeseries'] = coep.get_df(engine, ts_table)

for key, value in data.items():
    print(value)