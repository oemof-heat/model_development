import logging
import os
import shutil

import pandas as pd

from oemof.tools.logger import define_logging
from oemof.tabular.datapackage import building
from oemof.tools.economics import annuity

from helper import get_experiment_dirs, get_scenario_assumptions


TIMEINDEX = pd.date_range('1/1/2017', periods=8760, freq='H')


def copy_base_scenario(source, destination):
    if os.path.exists(destination):
        shutil.rmtree(destination)

    shutil.copytree(source, destination)


def prepare_investment_cost(fix_costs_raw_file):
    wacc = 0.052
    fix_cost = pd.read_csv(fix_costs_raw_file)
    fix_cost['eq_cost'] = \
        fix_cost['overnight_cost'] * 0.01 * fix_cost['fixom']\
        + fix_cost.apply(lambda x: annuity(x['overnight_cost'], x['lifetime'], wacc), axis=1)
    # units are Eur/kW or Eur/kWh


def get_elements(dir):
    elements = {}

    for file in os.listdir(dir):
        key = file.split('.')[0]

        value = pd.read_csv(os.path.join(dir, file), index_col='name', delimiter=';')

        elements.update({key: value})

    return elements


def save_elements(elements, dir):
    for key, value in elements.items():
        filename = os.path.join(dir, key + '.csv')
        value.to_csv(filename, sep=';')


def set_gas_price(gas_price, elements_dir):
    elements = get_elements(elements_dir)

    elements['gas-chp']['carrier_cost'] = gas_price

    elements['gas-hob']['carrier_cost'] = gas_price

    save_elements(elements, elements_dir)


def prepare_electricity_price_profiles(
    market_price_el,
    charges_tax_levies_el,
    variance_el,
    chp_surcharge,
    raw_price,
    destination,
    timeindex=TIMEINDEX
):
    def save(df, name):
        df.to_csv(os.path.join(destination, name))

    raw_price = pd.read_csv(raw_price, index_col=0)

    base_cost_profile = raw_price['price_electricity_spot']
    base_cost_profile = base_cost_profile.iloc[:len(timeindex)]
    base_cost_profile.index = timeindex
    base_cost_profile.index.name = 'timeindex'

    marginal_cost_profile = base_cost_profile.copy()
    marginal_cost_profile += chp_surcharge
    marginal_cost_profile *= -1
    marginal_cost_profile.name = 'electricity-selling'
    save(marginal_cost_profile, 'marginal_cost_profile.csv')

    carrier_cost_profile = base_cost_profile.copy()
    carrier_cost_profile += charges_tax_levies_el
    carrier_cost_profile.name = 'electricity-buying'
    save(carrier_cost_profile, 'carrier_cost_profile.csv')


def prepare_heat_demand_profile(heat_demand_profile, destination, timeindex=TIMEINDEX):
    def save(df, name):
        df.to_csv(os.path.join(destination, name))

    heat_demand_profile = pd.read_csv(heat_demand_profile, index_col='timestamp')
    heat_demand_profile = heat_demand_profile.sum(axis=1)
    heat_demand_profile = heat_demand_profile.iloc[:len(timeindex)]
    heat_demand_profile.index = timeindex
    heat_demand_profile.index.name = 'timeindex'
    heat_demand_profile.name = 'heat-demand-01'

    save(heat_demand_profile, 'heat-demand_profile.csv')


def prepare_heat_pump_elements(overnight_cost_heat_pump, cop_heat_pump):
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
                'heat-distribution',
            ],
            'chp': [
                'gas-chp',
            ],
        },
        path=preprocessed
    )


def main(**scenario_assumptions):
    print('Preprocessing')

    timeindex = TIMEINDEX
    if scenario_assumptions['debug']:
        timeindex = timeindex[:3]

    dirs = get_experiment_dirs(scenario_assumptions['name'])
    elements_dir = os.path.join(dirs['preprocessed'], 'data', 'elements')

    copy_base_scenario(
        os.path.join(dirs['raw'], 'base_scenario'),
        os.path.join(dirs['preprocessed'])
    )

    prepare_investment_cost(
        os.path.join(dirs['raw'], 'fix_cost_assumptions.csv')
    )

    gas_price = scenario_assumptions['market_price_gas']\
                + scenario_assumptions['charges_tax_levies_gas']

    set_gas_price(gas_price, elements_dir)

    prepare_heat_demand_profile(
        os.path.join(dirs['raw'], 'demand_heat_2017.csv'),
        os.path.join(dirs['preprocessed'], 'data', 'sequences'),
        timeindex=timeindex
    )

    prepare_electricity_price_profiles(
        scenario_assumptions['market_price_el'],
        scenario_assumptions['charges_tax_levies_el'],
        scenario_assumptions['variance_el'],
        scenario_assumptions['chp_surcharge'],
        os.path.join(dirs['raw'], 'price_electricity_spot_2017.csv'),
        os.path.join(dirs['preprocessed'], 'data', 'sequences'),
        timeindex=timeindex
    )

    prepare_heat_pump_elements(
        scenario_assumptions['overnight_cost_heat_pump'],
        scenario_assumptions['cop_heat_pump']
    )

    infer_metadata('name', dirs['preprocessed'])


if __name__ == '__main__':
    scenario_assumptions = get_scenario_assumptions().loc[0]
    main(**scenario_assumptions)
