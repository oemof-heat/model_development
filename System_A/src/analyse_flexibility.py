

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Colors
beuth_red = (227 / 255, 35 / 255, 37 / 255)
beuth_col_1 = (223 / 255, 242 / 255, 243 / 255)
beuth_col_2 = (178 / 255, 225 / 255, 227 / 255)
beuth_col_3 = (0 / 255, 152 / 255, 161 / 255)

zeitreihen_a1 = pd.read_csv('../results/data_postprocessed/zeitreihen_A1.csv')
zeitreihen_a2 = pd.read_csv('../results/data_postprocessed/zeitreihen_A2.csv')
zeitreihen_a3 = pd.read_csv('../results/data_postprocessed/zeitreihen_A3.csv')

# print(data_a1.head())

fig, ax = plt.subplots()
ax.scatter(x=zeitreihen_a1['Waermebedarf'],
           y=zeitreihen_a1['Strombedarf'])
# ax.scatter(x=zeitreihen['CHPs_th'].add(zeitreihen['Kessel']),
#            y=zeitreihen['CHPs_el'])
max_power = 940
min_heat = 240

ax.scatter(x=zeitreihen_a1['CHPs_th'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
                                                     zeitreihen_a1['CHPs_th'] > min_heat)],
           y=zeitreihen_a1['CHPs_el'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
                                                     zeitreihen_a1['CHPs_th'] > min_heat)])
ax.scatter(x=zeitreihen_a2['CHPs_th'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
                                                     zeitreihen_a1['CHPs_th'] > min_heat)],
           y=zeitreihen_a2['CHPs_el'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
                                                     zeitreihen_a1['CHPs_th'] > min_heat)]
           , marker="x")

# ax.scatter(x=zeitreihen_a1['CHPs_th'][np.logical_and(zeitreihen_a1['CHPs_el'] > 750, zeitreihen_a1['CHPs_th'] > 300)],
#            y=zeitreihen_a1['CHPs_el'][np.logical_and(zeitreihen_a1['CHPs_el'] > 750, zeitreihen_a1['CHPs_th'] > 300)])
# ax.scatter(x=zeitreihen_a2['CHPs_th'][np.logical_and(zeitreihen_a1['CHPs_el'] > 750, zeitreihen_a1['CHPs_th'] > 300)],
#            y=zeitreihen_a2['CHPs_el'][np.logical_and(zeitreihen_a1['CHPs_el'] > 750, zeitreihen_a1['CHPs_th'] > 300)]
#            , marker="x")
plt.savefig('scatter_plot_P_high.png', dpi=300)


fig2, ax2 = plt.subplots(1,2)
ax2[0].scatter(x=zeitreihen_a1['Waermebedarf'],
           y=zeitreihen_a1['Strombedarf'])
max_power = 940
min_heat = 300
ax2[0].scatter(x=zeitreihen_a1['CHPs_th'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
                                                     zeitreihen_a1['CHPs_th'] > min_heat)],
           y=zeitreihen_a1['CHPs_el'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
                                                     zeitreihen_a1['CHPs_th'] > min_heat)])
ax2[0].scatter(x=zeitreihen_a2['CHPs_th'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
                                                     zeitreihen_a1['CHPs_th'] > min_heat)],
           y=zeitreihen_a2['CHPs_el'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
                                                     zeitreihen_a1['CHPs_th'] > min_heat)]
           , marker="x")
ax2[1].scatter(x=zeitreihen_a2['Fuellstand_Waermespeicher_relativ'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
                                                     zeitreihen_a1['CHPs_th'] > min_heat)],
           y=zeitreihen_a2['CHPs_el'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
                                                     zeitreihen_a1['CHPs_th'] > min_heat)], marker='d')
ax2[1].set_ylim([-50, 1050])
ax2[0].set_ylabel('Elektrische Leistung in MW_el')
ax2[0].set_xlabel('Wärmeleistung in MW_th')
ax2[1].set_xlabel('Füllstand Wärmespeicher in %')
# plt.gca().set_aspect('equal', adjustable='box')
plt.savefig('scatter_plot_speicher.png', dpi=300)


# fig3, ax3 = plt.subplots()
# ax3.scatter(x=zeitreihen_a1['Waermebedarf'],
#            y=zeitreihen_a1['Strombedarf'])
# max_power_3 = 1050
# min_heat_3 = 0
# fuellstand = 0.1  # in Prozent [0...100]
# ax3.scatter(x=zeitreihen_a2['CHPs_th'][np.logical_and(zeitreihen_a2['CHPs_el'] < max_power_3,
#                                                      zeitreihen_a2['CHPs_th'] > min_heat_3)],
#            y=zeitreihen_a2['CHPs_el'][np.logical_and(zeitreihen_a2['CHPs_el'] < max_power_3,
#                                                      zeitreihen_a2['CHPs_th'] > min_heat_3)])
# ax3.scatter(x=zeitreihen_a2['CHPs_th'][zeitreihen_a2['Fuellstand_Waermespeicher_relativ'] < fuellstand],
#            y=zeitreihen_a2['CHPs_el'][zeitreihen_a2['Fuellstand_Waermespeicher_relativ'] < fuellstand]
#            , marker="x")
# # ax3[1].scatter(x=zeitreihen_a2['Fuellstand_Waermespeicher_relativ'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power_3,
# #                                                      zeitreihen_a1['CHPs_th'] > min_heat_3)],
# #            y=zeitreihen_a2['CHPs_el'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power_3,
# #                                                      zeitreihen_a1['CHPs_th'] > min_heat_§)], marker='d')
#
# ax3.set_ylabel('Elektrische Leistung in MW_el')
# ax3.set_xlabel('Wärmeleistung in MW_th')
# plt.savefig('scatter_plot_3.png', dpi=300)

fig3, ax3 = plt.subplots(1,3, sharey=True)
# ax3.scatter(x=zeitreihen_a1['Waermebedarf'],
#            y=zeitreihen_a1['Strombedarf'])
max_power_3 = 1050
min_heat_3 = 0
fuellstand = 0.1  # in Prozent [0...100]
ax3[0].scatter(x=zeitreihen_a1['CHPs_th'],
                y=zeitreihen_a1['CHPs_el'],
                marker='.',
                c=[beuth_col_3],
                zorder=10,
                label='ohne Speicher')
ax3[0].grid(color='grey',  # beuth_col_2,
         linestyle='-',
         linewidth=0.5,
         zorder=1)
ax3[1].scatter(x=zeitreihen_a2['CHPs_th'],
                y=zeitreihen_a2['CHPs_el'],
                marker='.',
                c=[beuth_col_3],
                zorder=10,
                label='mit Wärmespeicher')
ax3[1].grid(color='grey',  # beuth_col_2,
         linestyle='-',
         linewidth=0.5,
         zorder=1)
ax3[2].scatter(x=zeitreihen_a3['CHPs_th'],
                y=zeitreihen_a3['CHPs_el'],
                marker='.',
                c=[beuth_col_3],
                zorder=10,
                label='mit Stromspeicher')
ax3[2].grid(color='grey',  # beuth_col_2,
         linestyle='-',
         linewidth=0.5,
         zorder=1)
# ax3.scatter(x=zeitreihen_a2['CHPs_th'][zeitreihen_a2['Waermespeicher_beladung'] > 0],
#            y=zeitreihen_a2['CHPs_el'][zeitreihen_a2['Waermespeicher_beladung'] > 0],
#             marker='x',
#             s=20,
#             c=[beuth_red],
#             zorder=10,
#             label='Betriebspunkte an denen Speicher beladen wird')
# ax3[1].scatter(x=zeitreihen_a2['Fuellstand_Waermespeicher_relativ'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power_3,
#                                                      zeitreihen_a1['CHPs_th'] > min_heat_3)],
#            y=zeitreihen_a2['CHPs_el'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power_3,
#                                                      zeitreihen_a1['CHPs_th'] > min_heat_§)], marker='d')
ax3[0].set_ylim([-250, 1050])
# ax3[0].set_xlim([0, 1000])
# ax3.legend(loc=4, fontsize=12)
ax3[0].set_ylabel('Elektrische Leistung in $\mathrm{MW_{el}}$', fontsize=12)
ax3[1].set_xlabel('Wärmeleistung in $\mathrm{MW_{th}}$', fontsize=12)
plt.savefig('scatter_plot_all3_2.png', dpi=300)