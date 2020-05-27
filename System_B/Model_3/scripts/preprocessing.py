import logging
import os

from oemof.tools.logger import define_logging
from oemof.tabular.datapackage import building

from helper import read_config


def preprocess_data():
    pass


def infer_metadata(name, preprocessed):
    r"""Infer the metadata of the datapackage"""
    logging.info("Inferring the metadata of the datapackage")
    building.infer_metadata(
        package_name=name,
        foreign_keys={
            'bus': [
                'heat-demand',
                'heat-storage',
            ],
            'profile': [
                'heat-demand',
            ],
            'efficiency': [
                'electricity-hp',
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
            ],
            'chp': [
                'gas-chp',
            ],
        },
        path=preprocessed
    )


def main():
    print('Preprocessing')

    abspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(abspath, 'config.yml')

    dirs = read_config(config_path)

    preprocess_data()
    infer_metadata('name', dirs['preprocessed'])


if __name__ == '__main__':
    main()
