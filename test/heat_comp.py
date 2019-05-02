from oemof import solph, outputlib
from oemof.network import Node
import pandas as pd


def create_model(data, timesteps):
    """
    A basic model for new heat components
    """
    # Adjust Timesteps
    timesteps = pd.date_range('1/1/2019', periods=timesteps, freq='H')

    # Create Energy System
    es = solph.EnergySystem(timeindex=timesteps)
    Node.registry = es

    # Data Manipulation
    data = data

    # Create Busses
    b_gas = solph.Bus(label='b_gas')
    b_elec = solph.Bus(label='b_elec')

    # Create Sources
    s_gas = solph.Source(label='s_gas',
                         outputs={b_gas: solph.Flow(
                             nominal_value=200)})

    # Create Sink
    demand = solph.Sink(label='demand',
                        inputs={b_elec: solph.Flow(
                            actual_value=100,
                            fixed=True,
                            nominal_value=1)})

    # Create Transformer
    t_gas = solph.Transformer(label='t_gas',
                              inputs={b_gas: solph.Flow()},
                              outputs={b_elec: solph.Flow(
                                  variable_costs=50)},
                              conversion_factors={b_elec: 0.5})

    # Create Model
    m = solph.Model(es)

    # Solve Model
    m.solve(solver='cbc', solve_kwargs={'tee': False})

    # Save Results
    es.results['main'] = outputlib.processing.results(m)
    es.results['meta'] = outputlib.processing.meta_results(m)
    es.dump(dpath=None, filename=None)

    return m


# Component Link as Example
"""
>>> bel0 = solph.Bus(label="el0")
>>> bel1 = solph.Bus(label="el1")

>>> link = solph.custom.Link(
...    label="transshipment_link",
...    inputs={bel0: solph.Flow(), bel1: solph.Flow()},
...    outputs={bel0: solph.Flow(), bel1: solph.Flow()},
...    conversion_factors={(bel0, bel1): 0.92, (bel1, bel0): 0.99})

>>> print(sorted([x[1][5] for x in link.conversion_factors.items()]))
[0.92, 0.99]

>>> type(link)
<class 'oemof.solph.custom.Link'>

>>> sorted([str(i) for i in link.inputs])
['el0', 'el1']

>>> link.conversion_factors[(bel0, bel1)][3]
0.92
"""

if __name__ == '__main__':
    # Input Data & Timesteps
    data = None
    timesteps = 10

    # Create & Solve Model
    model = create_model(data, timesteps)

    # Get Results
    es = solph.EnergySystem()
    es.restore(dpath=None, filename=None)

    # Show Results
    b_gas = outputlib.views.node(es.results['main'], 'b_gas')
    b_elec = outputlib.views.node(es.results['main'], 'b_elec')

    print('-----------------------------------------------------')
    print('Bus Gas\n', b_gas['sequences'])
    print('-----------------------------------------------------')
    print('Bus Elec\n', b_elec['sequences'])
    print('-----------------------------------------------------')
