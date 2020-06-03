import logging
import os

import pandas as pd

from oemof.tools.logger import define_logging
from oemof.tabular.datapackage import building

from helper import get_experiment_dirs


TIMEINDEX = pd.date_range('1/1/2017', periods=8760, freq='H')


def prepare_electricity_price_profiles(raw_price, destination):
    def save(df, name):
        df.to_csv(os.path.join(destination, name))

    raw_price = pd.read_csv(raw_price, index_col=0)

    marginal_cost_profile = raw_price['price_electricity_spot']
    marginal_cost_profile.index = TIMEINDEX
    marginal_cost_profile.index.name = 'timeindex'
    marginal_cost_profile.name = 'electricity-selling'
    save(marginal_cost_profile, 'marginal_cost_profile.csv')

    carrier_cost_profile = marginal_cost_profile.copy()
    carrier_cost_profile.name = 'electricity-buying'
    save(carrier_cost_profile, 'carrier_cost_profile.csv')


def prepare_heat_demand_profile(heat_demand_profile, destination):
    def save(df, name):
        df.to_csv(os.path.join(destination, name))

    heat_demand_profile = pd.read_csv(heat_demand_profile, index_col='timestamp')
    heat_demand_profile = heat_demand_profile.sum(axis=1)
    heat_demand_profile.index = TIMEINDEX
    heat_demand_profile.index.name = 'timeindex'
    heat_demand_profile.name = 'heat-demand-01'

    save(heat_demand_profile, 'heat-demand_profile.csv')


def infer_metadata(name, preprocessed):
    r"""Infer the metadata of the datapackage"""
    logging.info("Inferring the metadata of the datapackage")
    building.infer_metadata(
        package_name=name,
        foreign_keys={
            'bus': [
                'heat-demand',
                'heat-storage',
                'heat-shortage',
            ],
            'profile': [
                'heat-demand',
            ],
            'carrier_cost': [
                'electricity-hp',
                'electricity-respth',
            ],
            'marginal_cost': [
                'gas-chp',
            ],
            'from_to_bus': [
                'gas-hob',
                'electricity-hp',
                'electricity-respth',
                'heat-distribution',
            ],
            'chp': [
                'gas-chp',
            ],
        },
        path=preprocessed
    )


def main():
    print('Preprocessing')

    dirs = get_experiment_dirs()

    prepare_heat_demand_profile(
        os.path.join(dirs['raw'], 'demand_heat_2017.csv'),
        os.path.join(dirs['preprocessed'], 'data', 'sequences')
    )

    prepare_electricity_price_profiles(
        os.path.join(dirs['raw'], 'price_electricity_spot_2017.csv'),
        os.path.join(dirs['preprocessed'], 'data', 'sequences')
    )

    infer_metadata('name', dirs['preprocessed'])


if __name__ == '__main__':
    main()
