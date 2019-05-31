import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
import oedialect
from sqlalchemy.orm import sessionmaker
import pandas as pd
import getpass

Base = declarative_base()

def connect_oep(user=None, token=None):
    """ Creates engine/metadata and connects the engine to OEP

    Parameters
    ----------
    user : string
        OEP username
    token : string
        OEP API-token (can be retrieved in OEP under
        'Your Security Information')

    Returns
    -------
    engine and metadata

    Note
    ----
    If none attributes are given, then this function asks user the OEP-username
    and the OEP-API-token via input() and getpass()

    """
    if user is None or token is None:
        user = input('Enter OEP-username:')
        token = getpass.getpass('Token:')

    # Create Engine:
    OEP_URL = 'openenergy-platform.org'
    OED_STRING = f'postgresql+oedialect://{user}:{token}@{OEP_URL}'

    engine = sa.create_engine(OED_STRING)
    metadata = sa.MetaData(bind=engine)
    engine = engine.connect()

    return engine, metadata


def upload_to_oep(df, Table, engine, metadata):
    """ Opens session for uploading data and uploads data to OEP

    Parameters
    ----------
    df : pandas dataframe
        data which is planned to upload
    Table : sqlalchemy table object
        structure of the data, contains also OEP table and schema name
    engine : sqlalchemy engine object
        engine which is created by connect_oep()
    metadata : sqlalchemy metadata object
        metadata which is created by connect_oep()

    Returns
    -------
    Table

    Note
    ----
    Table.name should not include UPPERCASE letters
    Table.name should not include '.'

    """
    table_name = Table.name
    schema_name = Table.schema

    if not engine.dialect.has_table(engine, table_name, schema_name):
        Table.create()
        print('Created table')
    else:
        print('Table already exists')

    Session = sessionmaker(bind=engine)
    session = Session()
    # insert data
    try:
        dtype = {key: Table.columns[key].type for key in Table.columns.keys()}
        df.to_sql(table_name, engine,
                          schema=schema_name,
                          if_exists='replace',
                          dtype=dtype)
        print('Inserted to ' + table_name)
    except Exception as e:
        session.rollback()
        session.close()
        raise
        print('Insert incomplete!')
    finally:
        session.close()

    return Table


def get_df(engine, table):
    """ Downloads the data from the OEP as pandas dataframe

    Parameters
    ----------
    engine : sqlalchemy engine object
        engine which is created by connect_oep()
    table : sqlalchemy table object
        structure of the data, contains also OEP table and schema name

    Returns
    -------
    df

    """
    Session = sessionmaker(bind=engine)
    session = Session()
    df = pd.DataFrame(session.query(table).all())
    session.close()

    return df
