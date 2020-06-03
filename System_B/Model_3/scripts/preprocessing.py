import logging
import os

from oemof.tools.logger import define_logging
from oemof.tabular.datapackage import building

from helper import get_experiment_dirs


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

    preprocess_data()
    infer_metadata('name', dirs['preprocessed'])


if __name__ == '__main__':
    main()
