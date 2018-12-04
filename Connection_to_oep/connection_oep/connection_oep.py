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


def upload_to_oep(example_df, table_name, schema_name, engine, metadata):
    # create table

    ExampleTable = sa.Table(
        table_name,
        metadata,
        sa.Column('index', sa.Integer, primary_key=True, autoincrement=True,
                  nullable=False),
        sa.Column('variable', sa.VARCHAR(50)),
        sa.Column('unit', sa.VARCHAR(50)),
        sa.Column('year', sa.INTEGER),
        sa.Column('value', sa.FLOAT(50)),
        schema=schema_name
    )

    if not engine.dialect.has_table(engine, table_name, schema_name):
        ExampleTable.create()
        print('Created table')
    else:
        print('Table already exists')

    # insert data
    try:
        example_df.to_sql(table_name, engine, schema='sandbox', if_exists='replace')
        print('Inserted to ' + table_name)
    except Exception as e:
        Session = sessionmaker(bind=engine)
        session = Session()
        session.rollback()
        session.close()
        raise
        print('Insert incomplete!')

    return ExampleTable


def upload_parameters_to_oep(df, table_name, schema_name, engine, metadata):
    # create table
    table = sa.Table(
        table_name,
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
        schema=schema_name)

    if not engine.dialect.has_table(engine, table_name, schema_name):
        table.create()
        print('Created table')
    else:
        print('Table already exists')

    # insert data
    try:
        df.to_sql(table_name, engine, schema='sandbox', if_exists='replace')
        print('Inserted to ' + table_name)
    except Exception as e:
        Session = sessionmaker(bind=engine)
        session = Session()
        session.rollback()
        session.close()
        raise
        print('Insert incomplete!')

    return table

def upload_timeseries_to_oep(df, table_name, schema_name, engine, metadata):
    # create table
    table = sa.Table(
        table_name,
        metadata,
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True,
                  nullable=False),
        sa.Column('time', sa.String(50)),
        sa.Column('price_el', sa.Float(50)),
        schema=schema_name)

    if not engine.dialect.has_table(engine, table_name, schema_name):
        table.create()
        print('Created table')
    else:
        print('Table already exists')

    # insert data
    try:
        df.to_sql(table_name, engine, schema='sandbox', if_exists='replace')
        print('Inserted to ' + table_name)
    except Exception as e:
        Session = sessionmaker(bind=engine)
        session = Session()
        session.rollback()
        raise
        print('Insert incomplete!')

    return table

def get_df(engine, table):
    Session = sessionmaker(bind=engine)
    session = Session()
    df = pd.DataFrame(session.query(table).all())
    session.close()
    print(df)