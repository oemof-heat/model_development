import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
import oedialect
from sqlalchemy.orm import sessionmaker
import pandas as pd
import getpass

Base = declarative_base()

def connect_oep(user=None, token=None):
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
    table_name = Table.name
    schema_name = Table.schema

    if not engine.dialect.has_table(engine, table_name, schema_name):
        Table.create()
        print('Created table')
    else:
        print('Table already exists')

    # insert data
    try:
        dtype = {key: Table.columns[key].type for key in Table.columns.keys()}
        df.to_sql(table_name, engine,
                          schema='sandbox',
                          if_exists='replace',
                          dtype=dtype)
        print('Inserted to ' + table_name)
    except Exception as e:
        Session = sessionmaker(bind=engine)
        session = Session()
        session.rollback()
        session.close()
        raise
        print('Insert incomplete!')

    return Table


def get_df(engine, table):
    Session = sessionmaker(bind=engine)
    session = Session()
    df = pd.DataFrame(session.query(table).all())
    session.close()

    return df