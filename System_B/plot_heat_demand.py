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
data_dh = data.drop(['DH_DE_Rem', 'DH_DE_Ind'], axis=1)
data_dh_normalized = data_dh/data_dh.max()

plt.figure(figsize=(12,8))
plt.plot(data)
plt.title('heat demand of 10 district heating systems' +
        '+ rest of Germany (pink) + industry (grey)')
plt.legend(data.columns.values, loc='upper center')

plt.figure(figsize=(12,8))
plt.plot(data_dh)
plt.title('heat demand of 10 district heating systems')
plt.legend(data_dh.columns.values, loc='upper center')


plt.figure(figsize=(12,8))
plt.plot(data_dh_normalized)
plt.title('heat demand of 10 district heating systems normalized')
plt.legend(data_dh_normalized.columns.values, loc='upper center')

plt.show()
