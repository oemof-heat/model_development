"""Plotting the heat demand data.
"""

__copyright__ = "Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "c-moeller, jnnr"

import os
import pandas as pd
import matplotlib.pyplot as plt


full_filename = os.path.join(os.path.dirname(__file__),
    'heat_demand.csv')
data = pd.read_csv(full_filename, sep=",")
print(data)

plt.plot(data)
plt.legend(data.columns.values, loc='upper center')
plt.show()
