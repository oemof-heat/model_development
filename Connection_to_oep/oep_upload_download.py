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
# upload
ExampleTable = coep.upload_to_oep(example_df, 'example_dialect_table_5', 'sandbox', engine, metadata)

# load data
input_parameters = pd.read_csv('Daten_Beispiel/data_thermal_energy_storage.csv')
print(input_parameters.columns)
# upload
ip_table = coep.upload_parameters_to_oep(input_parameters, 'example_oea_parameters', 'sandbox', engine, metadata)

# load data
timeseries = pd.read_csv('Daten_Beispiel/Electricity_price_spot_market_2016.csv')
print(timeseries.columns)
# upload
ts_table = coep.upload_timeseries_to_oep(timeseries, 'example_oea_timeseries', 'sandbox', engine, metadata)

data = coep.get_df(engine, ExampleTable)
data = coep.get_df(engine, ip_table)
data = coep.get_df(engine, ts_table)