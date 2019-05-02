from oemof import solph


def create_model(i):
    """
    A basic model for new heat components
    """
    return i


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
    model = create_model(None)
    print(model)
