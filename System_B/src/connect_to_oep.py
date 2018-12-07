import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../..')))
import connection_oep as coep
import pandas as pd
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import yaml
import helpers


def define_tables(engine, metadata):
    r"""
    Define hardcoded tables

    Returns
    -------
    tables : dict
        Dictionary containing tables.
    """
    tables = {}
    tables['input_param_table'] = sa.Table(
        'oemof_heat_system_b_input_parameter',
        metadata,
        sa.Column('component', sa.String(50)),
        sa.Column('var_name', sa.String(50)),
        sa.Column('var_value', sa.Float(50)),
        sa.Column('var_unit', sa.String(10)),
        sa.Column('reference', sa.String(10)),
        sa.Column('comment', sa.String(50)),
        sa.Column('tags', sa.String(50)),
        schema='sandbox')

    tables['timeseries_table'] = sa.Table(
        'oemof_heat_system_b_timeseries_temperature',
        metadata,
        sa.Column('timestamp', sa.String(50)),
        sa.Column('T', sa.Float(50)),
        schema='sandbox')

    return tables


def upload_data_to_oep(tables, engine, metadata):
    r"""
    Upload data to oep

    Parameters
    ----------
    tables : dict
        Dictionary containing tables
        to download.

    engine : sqlalchemy.Engine

    metadata : sqlalchemy.MetaData

    Returns
    -------
    engine : sqlalchemy.Engine

    metadata : sqlalchemy.MetaData
    """
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    input_parameters = pd.read_csv(os.path.join(abs_path, 'data_raw/oep_data/input_parameter.csv'))
    timeseries = pd.read_csv(os.path.join(abs_path, 'data_raw/oep_data/weather_data.csv'))

    coep.upload_to_oep(input_parameters, tables['input_param_table'], engine, metadata)
    coep.upload_to_oep(timeseries, tables['timeseries_table'], engine, metadata)

    return engine, metadata


def download_data_from_oep(tables, engine, metadata):
    r"""
    Gets data from oep.

    Parameters
    ----------
    tables : dict
        Dictionary containing tables
        to download.

    engine : sqlalchemy.Engine

    metadata : sqlalchemy.MetaData

    Returns
    -------
    data : dict
        Dictionary containing dataframes.
    """
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    # download
    data = {}
    for table_name, table in tables.items():
        data[table_name] = coep.get_df(engine, table)

    # save
    for key, value in data.items():
        save_as = os.path.join(abs_path, 'data_raw/oep_data',f'{key}.csv')
        value.to_csv(save_as)
        print('Saved as ', save_as)

    return data

def connect_to_oep(config_path, results_dir):
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    if 'oep_download' in cfg and cfg['oep_download']:
        with open('../oep_cred.yml', 'r') as oep_cred:
            cred = yaml.load(oep_cred)

        engine, metadata = coep.connect_oep(cred['username'], cred['token'])
        print('Connection established')
        tables = define_tables(engine, metadata)
        # upload_data_to_oep(tables, engine, metadata)
        download_data_from_oep(tables, engine, metadata)

if __name__ == '__main__':
    config_path, results_dir = helpers.setup_experiment()
    connect_to_oep(config_path=config_path, results_dir=results_dir)
