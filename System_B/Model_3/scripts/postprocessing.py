import copy
import os

import numpy as np
import pandas as pd

from oemof.solph import EnergySystem, Bus, Sink
from oemof.solph.components import GenericStorage
from oemof.outputlib import views, processing

from oemof.tabular import facades
from oemof.tabular.tools.postprocessing import component_results, supply_results,\
    demand_results, bus_results

from helper import get_experiment_dirs, get_scenario_assumptions


def write_results(
    es, output_path, raw=False, summary=True, scalars=True, **kwargs
):
    """
    """

    def save(df, name, path=output_path):
        """ Helper for writing csv files
        """
        df.to_csv(os.path.join(path, name + ".csv"))

    sequences = {}

    buses = [b.label for b in es.nodes if isinstance(b, Bus)]

    link_results = component_results(es, es.results).get("link")
    if link_results is not None and raw:
        save(link_results, "links")
        sequences.update({'links': link_results})

    imports = pd.DataFrame()
    for b in buses:
        supply = supply_results(results=es.results, es=es, bus=[b], **kwargs)
        supply.columns = supply.columns.droplevel([1, 2])

        demand = demand_results(results=es.results, es=es, bus=[b])

        excess = component_results(es, es.results, select="sequences").get(
            "excess"
        )

        if link_results is not None and es.groups[b] in list(
            link_results.columns.levels[0]
        ):
            ex = link_results.loc[
                :, (es.groups[b], slice(None), "flow")
            ].sum(axis=1)
            im = link_results.loc[
                :, (slice(None), es.groups[b], "flow")
            ].sum(axis=1)

            net_import = im - ex
            net_import.name = es.groups[b]
            imports = pd.concat([imports, net_import], axis=1)

            supply["import"] = net_import

        if es.groups[b] in demand.columns:
            _demand = demand.loc[:, (es.groups[b], slice(None), "flow")]
            _demand.columns = _demand.columns.droplevel([0, 2])
            supply = pd.concat([supply, _demand], axis=1)
        if excess is not None:
            if es.groups[b] in excess.columns:
                _excess = excess.loc[:, (es.groups[b], slice(None), "flow")]
                _excess.columns = _excess.columns.droplevel([0, 2])
                supply = pd.concat([supply, _excess], axis=1)
        save(supply, os.path.join('sequences', b))
        sequences.update({str(b): supply})
        # save(excess, "excess")
        # save(imports, "import")

    bresults = bus_results(es, es.results, concat=True)
    # check if storages exist in energy system nodes
    if [n for n in es.nodes if isinstance(n, GenericStorage)]:
        filling_levels = views.node_weight_by_type(es.results, GenericStorage)
        filling_levels.columns = filling_levels.columns.droplevel(1)
        save(filling_levels, os.path.join('sequences', 'filling_levels'))
        sequences.update({'filling_levels': filling_levels})

    return sequences


def get_capacities(es):
    r"""
    Calculates the capacities of all components.

    Adapted from oemof.tabular.tools.postprocessing.write_results()

    Parameters
    ----------
    es : oemof.solph.EnergySystem
        EnergySystem containing the results.

    Returns
    -------
    capacities : pd.DataFrame
        DataFrame containing the capacities.
    """
    try:
        all = bus_results(es, es.results, select="scalars", concat=True)

        all.name = "var_value"

        endogenous = all.reset_index()

        endogenous.drop(['from', 'to'], axis=1, inplace=True)

        endogenous["name"] = [
            getattr(t, "label", np.nan) for t in all.index.get_level_values(0)
        ]
        endogenous["type"] = [
            getattr(t, "type", np.nan) for t in all.index.get_level_values(0)
        ]
        endogenous["carrier"] = [
            getattr(t, "carrier", np.nan)
            for t in all.index.get_level_values(0)
        ]
        endogenous["tech"] = [
            getattr(t, "tech", np.nan) for t in all.index.get_level_values(0)
        ]
        endogenous["var_name"] = "invest"
        endogenous.set_index(
            ["name", "type", "carrier", "tech", "var_name"], inplace=True
        )

    except ValueError:
        endogenous = pd.DataFrame()

    d = dict()
    for node in es.nodes:
        if not isinstance(node, (Bus, Sink, facades.Shortage)):
            if getattr(node, "capacity", None) is not None:
                if isinstance(node, facades.TYPEMAP["link"]):
                    pass
                else:
                    key = (
                        node.label,
                        # [n for n in node.outputs.keys()][0],
                        node.type,
                        node.carrier,
                        node.tech,  # tech & carrier are oemof-tabular specific
                        'capacity'
                    )  # for oemof logic
                    d[key] = {'var_value': node.capacity}
    exogenous = pd.DataFrame.from_dict(d).T  # .dropna()

    if not exogenous.empty:
        exogenous.index = exogenous.index.set_names(
            ['name', 'type', 'carrier', 'tech', 'var_name']
        )

    try:
        all = component_results(es, es.results, select='scalars')['storage']
        all.name = 'var_value'

        storage = all.reset_index()
        storage.columns = ['name', 'to', 'var_name', 'var_value']
        storage['type'] = [
            getattr(t, "type", np.nan) for t in all.index.get_level_values(0)
        ]
        storage['carrier'] = [
            getattr(t, "carrier", np.nan) for t in all.index.get_level_values(0)
        ]
        storage['tech'] = [
            getattr(t, "tech", np.nan) for t in all.index.get_level_values(0)
        ]
        storage = storage.loc[storage['to'].isna()]
        storage.drop('to', 1, inplace=True)
        storage = storage[['name', 'type', 'carrier', 'tech', 'var_name', 'var_value']]
        storage.replace(
            ['init_cap', 'invest'],
            ['storage_capacity', 'storage_capacity_invest'],
            inplace=True
        )
        storage.set_index(
            ["name", "type", "carrier", "tech", "var_name"], inplace=True
        )

    except ValueError:
        storage = pd.DataFrame()

    capacities = pd.concat([endogenous, exogenous, storage])

    capacities = capacities.groupby(level=[0, 1, 2, 3, 4]).sum()

    return capacities


def cap_el_to_cap_th(df):
    df_adapted = df.copy()

    df_adapted.loc['gas-chp', 'extraction', 'gas', 'chp', 'capacity'] *= 0.355/0.47

    return df_adapted


def get_flow_by_oemof_tuple(oemof_tuple):
    if isinstance(oemof_tuple[0], Bus):
        component = oemof_tuple[1]
        bus = oemof_tuple[0]

    elif isinstance(oemof_tuple[1], Bus):
        component = oemof_tuple[0]
        bus = oemof_tuple[1]

    else:
        return None

    flow = component.outputs[bus]

    return flow


def select_from_dict(dict, name):
    def has_var_name(v, name):
        return (name in v['scalars'].index) or (name in v['sequences'].columns)

    def get_var_value(v, name):
        if name in v['scalars'].index:
            return v['scalars'][name]
        elif name in v['sequences'].columns:
            return v['sequences'][name]

    selected_param_dict = copy.deepcopy({k: get_var_value(v, name) for k, v in dict.items() if has_var_name(v, name)})

    return selected_param_dict


def multiply_param_with_variable(params, results, param_name, var_name):
    def get_label(k):
        if isinstance(k, tuple):
            return tuple(map(str, k))
        return str(k)

    parameter = select_from_dict(params, param_name)

    variable = select_from_dict(results, var_name)

    intersection = processing.convert_keys_to_strings(parameter).keys()\
                   & processing.convert_keys_to_strings(variable).keys()

    product = {}
    for k, var in variable.items():
        if get_label(k) in intersection:
            par = processing.convert_keys_to_strings(parameter)[get_label(k)]

            if isinstance(par, pd.Series):
                par.index = var.index

            prod = var * par
            product.update({k: prod})

    return product


def index_tuple_to_pp_format(input_df, var_name):
    input_df.name = 'var_value'
    df = input_df.reset_index()

    def is_bus(index):
        return index.map(lambda x: isinstance(x, Bus))

    df['name'] = np.nan

    df['name'].loc[is_bus(input_df.index.get_level_values(0))] = df['level_1']

    df['name'].loc[is_bus(input_df.index.get_level_values(1))] = df['level_0']

    df['name'].loc[input_df.index.get_level_values(1).isna()] = df['level_0']

    df['type'] = [
        getattr(t, "type", np.nan) for t in df['name']
    ]
    df['carrier'] = [
        getattr(t, "carrier", np.nan) for t in df['name']
    ]
    df['tech'] = [
        getattr(t, "tech", np.nan) for t in df['name']
    ]
    df['var_name'] = var_name

    df = df[['name', 'type', 'carrier', 'tech', 'var_name', 'var_value']]

    df.set_index(['name', 'type', 'carrier', 'tech', 'var_name'], inplace=True)

    return df


def get_yearly_sum(heat_sequences):

    yearly_sum = heat_sequences.sum()

    yearly_sum.name = 'var_value'

    yearly_sum.index.name = 'name'

    yearly_sum = yearly_sum.reset_index()

    yearly_sum['type'] = [
        getattr(t, "type", np.nan) for t in yearly_sum['name']
    ]
    yearly_sum['carrier'] = [
        getattr(t, "carrier", np.nan) for t in yearly_sum['name']
    ]
    yearly_sum['tech'] = [
        getattr(t, "tech", np.nan) for t in yearly_sum['name']
    ]
    yearly_sum['var_name'] = 'yearly_heat'

    yearly_sum = yearly_sum[['name', 'type', 'carrier', 'tech', 'var_name', 'var_value']]

    yearly_sum.set_index(['name', 'type', 'carrier', 'tech', 'var_name'], inplace=True)

    return yearly_sum


def get_capacity_cost(es):
    capacity_cost = multiply_param_with_variable(es.params, es.results, 'investment_ep_costs', 'invest')
    capacity_cost = pd.Series(capacity_cost)

    capacity_cost = index_tuple_to_pp_format(capacity_cost, 'capacity_cost')

    capacity_cost = capacity_cost.groupby(level=[0,1,2,3,4]).sum()

    return capacity_cost


def get_carrier_cost(es):
    variable_costs = multiply_param_with_variable(es.params, es.results, 'variable_costs', 'flow')
    carrier_cost = {k: v.sum() for k, v in variable_costs.items() if isinstance(k[0], Bus)}
    carrier_cost = pd.Series(carrier_cost)

    carrier_cost = index_tuple_to_pp_format(carrier_cost, 'carrier_cost')

    return carrier_cost


def get_marginal_cost(es):
    variable_costs = multiply_param_with_variable(es.params, es.results, 'variable_costs', 'flow')
    marginal_cost = {k: v.sum() for k, v in variable_costs.items() if isinstance(k[1], Bus)}
    marginal_cost = pd.Series(marginal_cost)

    marginal_cost = index_tuple_to_pp_format(marginal_cost, 'marginal_cost')

    return marginal_cost


def get_full_load_hours(es):

    def index_to_str(df_in):
        df = df_in.copy()

        level_names = ['level_' + str(n) for n in range(len(df.index.names))]
        df.index.names = level_names

        df = df.reset_index()
        df[level_names] = df[level_names].astype(str)
        df = df.set_index(level_names)

        return df

    capacity = pd.Series(select_from_dict(es.params, 'nominal_value')).astype(float)
    invest = pd.Series(select_from_dict(es.results, 'invest'))
    total_capacity = capacity.add(invest, fill_value=0)
    total_capacity = index_tuple_to_pp_format(total_capacity, 'full_load_hours')

    flow = select_from_dict(es.results, 'flow')
    summed_flow = pd.Series({k: v.sum() for k, v in flow.items()})
    summed_flow = index_tuple_to_pp_format(summed_flow, 'full_load_hours')

    total_capacity = index_to_str(total_capacity)
    summed_flow = index_to_str(summed_flow)
    flh = summed_flow.divide(total_capacity)

    flh.index.names = ['name', 'type', 'carrier', 'tech', 'var_name']

    flh.replace([np.inf, -np.inf], np.nan, inplace=True)
    flh.dropna(inplace=True)

    return flh


def get_flh(capacities, yearly_sum):
    def index_to_str(df_in):
        df = df_in.copy()

        level_names = ['level_' + str(n) for n in range(len(df.index.names))]
        df.index.names = level_names

        df = df.reset_index()
        df[level_names] = df[level_names].astype(str)
        df = df.set_index(level_names)

        return df

    idx = pd.IndexSlice
    cap = index_to_str(capacities)
    heat = index_to_str(yearly_sum)
    cap = cap.loc[idx[:,:,:,:,['capacity', 'invest']],:]

    cap = cap.sum(axis=0, level=[0,1,2,3])
    heat.index = heat.index.droplevel(4)

    flh = heat.divide(cap)

    return flh


def write_total_cost(output_path):

    def add_index(x, name, value):
        x[name] = value
        x.set_index(name, append=True, inplace=True)
        return x

    capacity_cost = pd.read_csv(os.path.join(output_path, 'capacity_cost.csv'), index_col=[0,1])
    marginal_cost = pd.read_csv(os.path.join(output_path, 'marginal_cost.csv'), index_col=[0,1])
    carrier_cost = pd.read_csv(os.path.join(output_path, 'carrier_cost.csv'), index_col=[0,1])

    capacity_cost = add_index(capacity_cost, 'var_name', 'capacity_cost')
    marginal_cost = add_index(marginal_cost, 'var_name', 'marginal_cost')
    carrier_cost = add_index(carrier_cost, 'var_name', 'carrier_cost')
    total_cost = pd.concat([capacity_cost, carrier_cost, marginal_cost], 0)

    total_cost.to_csv(os.path.join(output_path, 'total_cost.csv'))


def main(**scenario_assumptions):
    print('Postprocessing')
    dirs = get_experiment_dirs(scenario_assumptions['scenario'])

    subdir = os.path.join(dirs['postprocessed'], 'sequences')
    if not os.path.exists(subdir):
        os.mkdir(subdir)

    # restore EnergySystem with results
    es = EnergySystem()
    es.restore(dirs['optimised'])

    sequences = write_results(es, dirs['postprocessed'])

    capacities = get_capacities(es)

    capacities = cap_el_to_cap_th(capacities)

    capacity_cost = get_capacity_cost(es)

    carrier_cost = get_carrier_cost(es)

    marginal_cost = get_marginal_cost(es)

    heat_sequences = pd.concat([sequences['heat_central'], sequences['heat_decentral']], 1)
    yearly_sum = get_yearly_sum(heat_sequences)

    # full_load_hours = get_flh(capacities, yearly_sum)

    scalars = pd.concat(
        [capacities, yearly_sum, capacity_cost, carrier_cost, marginal_cost], 0)
    scalars.to_csv(os.path.join(dirs['postprocessed'], 'scalars.csv'))


if __name__ == '__main__':
    scenario_assumptions = get_scenario_assumptions().loc[0]
    main(**scenario_assumptions)
