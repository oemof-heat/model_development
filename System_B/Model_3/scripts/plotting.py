import os

import matplotlib.pyplot as plt
import pandas as pd

from helper import get_experiment_dirs


def bar_plot():
    pass

def plot_capacities(capacities, destination):
    print('######### plotting capacities #########')
    print(capacities)

    idx = pd.IndexSlice

    cap_heat_dec = capacities.loc[idx[:, 'heat_decentral', :], :]
    cap_heat_cen = capacities.loc[idx[:, 'heat_central', :], :]
    cap_electricty = capacities.loc[idx[:, 'electricity', :], :]

    for cap in [cap_heat_dec, cap_heat_cen, cap_electricty]:
        cap.index = cap.index.droplevel(['to', 'tech', 'carrier'])

    fig, axs = plt.subplots(2, 1)
    cap_heat_cen.plot.bar(ax=axs[0])
    cap_heat_dec.plot.bar(ax=axs[1])

    # plt.tight_layout()

    plt.savefig(destination)


def plot_dispatch(bus, destination):
    start = '2017-02-01'
    end = '2017-03-01'

    bus = bus[start:end]

    demand = bus['heat-demand']
    bus = bus.drop('heat-distribution', axis=1)
    bus_wo_demand = bus.drop('heat-demand', axis=1)
    bus_wo_demand_pos = bus_wo_demand.copy()
    bus_wo_demand_pos.loc[bus_wo_demand_pos['heat_central-tes'] < 0, 'heat_central-tes'] = 0
    bus_wo_demand_pos.loc[bus_wo_demand_pos['heat_decentral-tes'] < 0, 'heat_decentral-tes'] = 0
    bus_wo_demand_neg = bus_wo_demand.copy()[['heat_central-tes', 'heat_decentral-tes']]
    bus_wo_demand_neg.loc[bus_wo_demand['heat_central-tes'] >= 0, 'heat_central-tes'] = 0
    bus_wo_demand_neg.loc[bus_wo_demand['heat_decentral-tes'] >= 0, 'heat_decentral-tes'] = 0

    fig, ax = plt.subplots(figsize=(12, 5))
    # bus_wo_demand_pos.plot.area(ax=ax)
    # bus_wo_demand_neg.plot.area(ax=ax)
    demand.plot.line(c='r', linewidth=2)
    ax.set_title('Dispatch')
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
    plt.tight_layout()
    plt.savefig(destination)


def plot_yearly_production(yearly_production, destination):
    print('\n######### plotting yearly_production #########')
    print(yearly_production)

    fig, ax = plt.subplots()
    yearly_production.plot.bar(ax=ax)
    ax.set_title('Yearly production')
    plt.tight_layout()
    plt.savefig(destination)

def main():
    dirs = get_experiment_dirs()

    capacities = pd.read_csv(
        os.path.join(dirs['postprocessed'], 'capacities.csv'),
        index_col=[0,1,2,3,4]
    )

    heat_central = pd.read_csv(
        os.path.join(dirs['postprocessed'], 'heat_central.csv'),
        index_col=0
    )

    heat_decentral = pd.read_csv(
        os.path.join(dirs['postprocessed'], 'heat_decentral.csv'),
        index_col=0
    )

    yearly_heat_sum = pd.read_csv(
        os.path.join(dirs['postprocessed'], 'heat_yearly_sum.csv'),
        index_col=0
    )

    plot_capacities(capacities, os.path.join(dirs['plots'], 'capacities.svg'))

    plot_dispatch(pd.concat([heat_central, heat_decentral], 1), os.path.join(dirs['plots'], 'heat_bus.svg'))

    yearly_production= yearly_heat_sum.drop('heat-demand')
    plot_yearly_production(yearly_production, os.path.join(dirs['plots'], 'heat_yearly_production.svg'))


if __name__ == '__main__':
    main()
