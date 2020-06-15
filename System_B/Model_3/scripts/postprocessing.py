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

from helper import get_experiment_dirs


def write_results(
    es, output_path, raw=False, summary=True, scalars=True, **kwargs
):
    """
    """

    def save(df, name, path=output_path):
        """ Helper for writing csv files
        """
        df.to_csv(os.path.join(path, name + ".csv"))

    buses = [b.label for b in es.nodes if isinstance(b, Bus)]

    link_results = component_results(es, es.results).get("link")
    if link_results is not None and raw:
        save(link_results, "links-oemof")

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
        save(supply, b)
        # save(excess, "excess")
        save(imports, "import")

    try:
        all = bus_results(es, es.results, select="scalars", concat=True)
        all.name = "value"
        endogenous = all.reset_index()
        endogenous["tech"] = [
            getattr(t, "tech", np.nan) for t in all.index.get_level_values(0)
        ]
        endogenous["carrier"] = [
            getattr(t, "carrier", np.nan)
            for t in all.index.get_level_values(0)
        ]
        endogenous.set_index(
            ["from", "to", "type", "tech", "carrier"], inplace=True
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
                        node,
                        [n for n in node.outputs.keys()][0],
                        "capacity",
                        node.tech,  # tech & carrier are oemof-tabular specific
                        node.carrier,
                    )  # for oemof logic
                    d[key] = {"value": node.capacity}
    exogenous = pd.DataFrame.from_dict(d).T  # .dropna()

    if not exogenous.empty:
        exogenous.index = exogenous.index.set_names(
            ["from", "to", "type", "tech", "carrier"]
        )

    capacities = pd.concat([endogenous, exogenous])

    capacities = pd.concat([endogenous, exogenous])

    save(capacities, "capacities")

    bresults = bus_results(es, es.results, concat=True)
    # check if storages exist in energy system nodes
    if [n for n in es.nodes if isinstance(n, GenericStorage)]:
        filling_levels = views.node_weight_by_type(es.results, GenericStorage)
        filling_levels.columns = filling_levels.columns.droplevel(1)
        save(filling_levels, "filling_levels")


def write_yearly_sum(output_path):
    heat_central = pd.read_csv(
        os.path.join(output_path, 'heat_central.csv'),
        index_col=0
    )
    heat_decentral = pd.read_csv(
        os.path.join(output_path, 'heat_decentral.csv'),
        index_col=0
    )

    yearly_sum = pd.concat([heat_central, heat_decentral], 1).sum()
    yearly_sum = yearly_sum.drop('heat-distribution')

    yearly_sum.to_csv(os.path.join(output_path, 'heat_yearly_sum.csv'))


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


def write_capacity_cost(es, output_path):
    capacity_cost = multiply_param_with_variable(es.params, es.results, 'investment_ep_costs', 'invest')
    capacity_cost = pd.Series(capacity_cost)

    capacity_cost.to_csv(os.path.join(output_path, 'capacity_cost.csv'))


def write_carrier_cost(es, output_path):
    variable_costs = multiply_param_with_variable(es.params, es.results, 'variable_costs', 'flow')
    carrier_cost = {k: v.sum() for k, v in variable_costs.items() if isinstance(k[0], Bus)}
    carrier_cost = pd.Series(carrier_cost)

    carrier_cost.to_csv(os.path.join(output_path, 'carrier_cost.csv'))


def write_marginal_cost(es, output_path):
    variable_costs = multiply_param_with_variable(es.params, es.results, 'variable_costs', 'flow')
    marginal_cost = {k: v.sum() for k, v in variable_costs.items() if isinstance(k[1], Bus)}
    marginal_cost = pd.Series(marginal_cost)

    marginal_cost.to_csv(os.path.join(output_path, 'marginal_cost.csv'))


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


def main():
    print('Postprocessing')
    dirs = get_experiment_dirs()

    # restore EnergySystem with results
    es = EnergySystem()
    es.restore(dirs['optimised'])

    write_results(es, dirs['postprocessed'])

    write_capacity_cost(es, dirs['postprocessed'])

    write_carrier_cost(es, dirs['postprocessed'])

    write_marginal_cost(es, dirs['postprocessed'])

    write_total_cost(dirs['postprocessed'])

    write_yearly_sum(dirs['postprocessed'])


if __name__ == '__main__':
    main()
