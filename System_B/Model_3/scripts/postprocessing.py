import os

import numpy as np
import pandas as pd

from oemof.solph import EnergySystem, Bus, Sink
from oemof.solph.components import GenericStorage
from oemof.outputlib import views

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


def main():
    print('Postprocessing')
    dirs = get_experiment_dirs()

    # restore EnergySystem with results
    es = EnergySystem()
    es.restore(dirs['optimised'])

    write_results(es, dirs['postprocessed'])

    print(es)


if __name__ == '__main__':
    main()
