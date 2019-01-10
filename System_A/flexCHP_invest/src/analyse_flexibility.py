

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Colors
beuth_red = (227 / 255, 35 / 255, 37 / 255)
beuth_col_1 = (223 / 255, 242 / 255, 243 / 255)
beuth_col_2 = (178 / 255, 225 / 255, 227 / 255)
beuth_col_3 = (0 / 255, 152 / 255, 161 / 255)

zeitreihen_a1 = pd.read_csv('../results/data_postprocessed/zeitreihen_A1.csv')
# zeitreihen_a2 = pd.read_csv('../results/data_postprocessed/zeitreihen_A2.csv')
# zeitreihen_a3 = pd.read_csv('../results/data_postprocessed/zeitreihen_A3.csv')

# print(data_a1.head())

# fig, ax = plt.subplots()
# ax.scatter(x=zeitreihen_a1['Waermebedarf'],
#            y=zeitreihen_a1['Strombedarf'])
# # ax.scatter(x=zeitreihen['CHPs_th'].add(zeitreihen['Kessel']),
# #            y=zeitreihen['CHPs_el'])
# max_power = 940
# min_heat = 240

# ax.scatter(x=zeitreihen_a1['CHPs_th'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
#                                                      zeitreihen_a1['CHPs_th'] > min_heat)],
#            y=zeitreihen_a1['CHPs_el'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
#                                                      zeitreihen_a1['CHPs_th'] > min_heat)])
# ax.scatter(x=zeitreihen_a2['CHPs_th'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
#                                                      zeitreihen_a1['CHPs_th'] > min_heat)],
#            y=zeitreihen_a2['CHPs_el'][np.logical_and(zeitreihen_a1['CHPs_el'] < max_power,
#                                                      zeitreihen_a1['CHPs_th'] > min_heat)]
#            , marker="x")
#
# plt.savefig('scatter_plot_P_high.png', dpi=300)
#
# fig3, ax3 = plt.subplots(1,3, sharey=True, figsize=(12,6))
# # ax3[0].scatter(x=zeitreihen_a1['Waermebedarf'],
# #            y=zeitreihen_a1['Strombedarf'],
# #                 marker='.',
# #                 c=[beuth_col_2],
# #                 zorder=9,
# #                 label='ohne Speicher')
# max_power_3 = 1050
# min_heat_3 = 0
# fuellstand = 0.1  # in Prozent [0...100]
# ax3[0].scatter(x=zeitreihen_a1['CHPs_th'],
#                 y=zeitreihen_a1['CHPs_el'],
#                 marker='.',
#                 c=[beuth_col_3],
#                 zorder=10,
#                 label='ohne Speicher')
# ax3[0].grid(color='grey',  # beuth_col_2,
#          linestyle='-',
#          linewidth=0.5,
#          zorder=1)
# ax3[1].scatter(x=zeitreihen_a2['CHPs_th'],
#                 y=zeitreihen_a2['CHPs_el'],
#                 marker='.',
#                 c=[beuth_col_3],
#                 zorder=10,
#                 label='mit Wärmespeicher')
# ax3[1].grid(color='grey',  # beuth_col_2,
#          linestyle='-',
#          linewidth=0.5,
#          zorder=1)
# ax3[2].scatter(x=zeitreihen_a3['CHPs_th'],
#                 y=zeitreihen_a3['CHPs_el'],
#                 marker='.',
#                 c=[beuth_col_3],
#                 zorder=10,
#                 label='mit Stromspeicher')
# ax3[2].grid(color='grey',  # beuth_col_2,
#          linestyle='-',
#          linewidth=0.5,
#          zorder=1)
# ax3[0].set_ylim([-20, 1020])
# # ax3[0].set_xlim([-20, 520])
# # ax3[0].set_xlim([0, 1000])
# # ax3.legend(loc=4, fontsize=12)
# ax3[0].tick_params(axis = 'both', which = 'major', labelsize = 16)
# ax3[1].tick_params(axis = 'both', which = 'major', labelsize = 16)
# ax3[2].tick_params(axis = 'both', which = 'major', labelsize = 16)
# # ax3[0].tick_params(axis = 'both', which = 'minor', labelsize = 12)
# ax3[0].set_ylabel('Elektrische Leistung in $\mathrm{MW_{el}}$', fontsize=20)
# ax3[1].set_xlabel('Wärmeleistung in $\mathrm{MW_{th}}$', fontsize=20)
# plt.savefig('scatter_plot_all3_2.png', dpi=300)
#



fig4, ax4 = plt.subplots()
produktion_el_a1 = zeitreihen_a1['CHPs_el'].add(-1*zeitreihen_a1['negative_Residuallast_MW_el'].add(
    zeitreihen_a1['batterie_entladen']))
produktion_th_a1 = zeitreihen_a1['CHPs_th'].add(zeitreihen_a1['Kessel']).add(
    zeitreihen_a1['P2H_th']).add(zeitreihen_a1['Waermespeicher_entladung'])

ax4.scatter(x=produktion_th_a1,
                y=produktion_el_a1,
                marker='o',
                c=[beuth_col_2],
                zorder=1,
                label=None,
                alpha=1)
ax4.grid(color='grey',  # beuth_col_2,
         linestyle='-',
         linewidth=0.5,
         zorder=2)
ax4.scatter(x=produktion_th_a1[zeitreihen_a1['Waermespeicher_beladung'] > 0][:-10],
           y=produktion_el_a1[zeitreihen_a1['Waermespeicher_beladung'] > 0][:-10],
            marker='|',#'_',
            s=20,
            c=[beuth_col_3],
            zorder=10,
            alpha=1,#.6,
            label='ohne Speicher')
# ax4.scatter(x=produktion_th_a2[zeitreihen_a2['Waermespeicher_beladung'] > 0][:-10],
#            y=produktion_el_a2[zeitreihen_a2['Waermespeicher_beladung'] > 0][:-10],
#             marker='|',#'_',
#             s=20,
#             c=[beuth_red],#'g',
#             zorder=10,
#             alpha=1,
#             label='mit Wärmespeicher (beladen)')
ax4.set_ylim([-250, 1050])
# ax4[0].set_xlim([0, 1000])
ax4.legend(loc=4, fontsize=12)
ax4.set_ylabel('Elektrische Leistung in $\mathrm{MW_{el}}$', fontsize=12)
ax4.set_xlabel('Wärmeleistung in $\mathrm{MW_{th}}$', fontsize=12)
# plt.show()
plt.savefig('../results/plots/scatter_plot_TES_charge_influence.png', dpi=300)

fig5, ax5 = plt.subplots()
# produktion_el_a1 = zeitreihen_a1['CHPs_el'].add(-1*zeitreihen_a1['negative_Residuallast_MW_el'])
# produktion_th_a1 = zeitreihen_a1['CHPs_th'].add(zeitreihen_a1['Kessel']).add(
#     zeitreihen_a1['negative_Residuallast_MW_el']*0.99)

# ax5.scatter(x=produktion_th_a1,
#                 y=produktion_el_a1,
ax5.scatter(x=zeitreihen_a1['Waermebedarf'],
                y=zeitreihen_a1['Strombedarf'],
                marker='o',
                c=[beuth_col_2],
                zorder=1,
                label=None,
                alpha=1)
ax5.grid(color='grey',  # beuth_col_2,
         linestyle='-',
         linewidth=0.5,
         zorder=2)
# ax5.scatter(x=produktion_th_a1[zeitreihen_a1['Waermespeicher_entladung'] > 0][10:],
#            y=produktion_el_a1[zeitreihen_a1['Waermespeicher_entladung'] > 0][10:],
ax5.scatter(x=zeitreihen_a1['Waermebedarf'][zeitreihen_a1['Waermespeicher_entladung'] > 0][10:],
            y=zeitreihen_a1['Strombedarf'][zeitreihen_a1['Waermespeicher_entladung'] > 0][10:],
            marker='|',#'<',#'_',
            s=20,
            c=[beuth_col_3],
            zorder=10,
            alpha=1,#.6,
            label='Speicherentladung')
ax5.set_ylim([-250, 1050])
# ax5[0].set_xlim([0, 1000])
ax5.legend(loc=4, fontsize=12)
ax5.set_ylabel('Elektrische Leistung in $\mathrm{MW_{el}}$', fontsize=12)
ax5.set_xlabel('Wärmeleistung in $\mathrm{MW_{th}}$', fontsize=12)
# plt.show()
plt.savefig('../results/plots/scatter_plot_TES_discharge_influence.png', dpi=300)


#### Szeanrio 3 ###
fig6, ax6 = plt.subplots()
produktion_el_a1 = zeitreihen_a1['CHPs_el'].add(-1*zeitreihen_a1['negative_Residuallast_MW_el'])
produktion_th_a1 = zeitreihen_a1['CHPs_th'].add(zeitreihen_a1['Kessel']).add(
    zeitreihen_a1['negative_Residuallast_MW_el']*0.99)

ax6.scatter(x=produktion_th_a1,
                y=produktion_el_a1,
                marker='o',
                c=[beuth_col_2],
                zorder=1,
                label=None,
                alpha=1)
ax6.grid(color='grey',  # beuth_col_2,
         linestyle='-',
         linewidth=0.5,
         zorder=2)
ax6.scatter(x=produktion_th_a1[zeitreihen_a1['batterie_beladen'] > 0][:-10],
           y=produktion_el_a1[zeitreihen_a1['batterie_beladen'] > 0][:-10],
            marker='_', #'>',#'_',
            s=20,
            c=[beuth_col_3],
            zorder=10,
            alpha=1,#.6,
            label='ohne Speicher')
ax6.scatter(x=produktion_th_a1[zeitreihen_a1['batterie_beladen'] > 0][:-10],
           y=produktion_el_a1[zeitreihen_a1['batterie_beladen'] > 0][:-10],
            marker='_',#'_',
            s=20,
            c=[beuth_red],#'g',
            zorder=10,
            alpha=1,
            label='mit Stromspeicher')
ax6.set_ylim([-250, 1050])
# ax6[0].set_xlim([0, 1000])
ax6.legend(loc=4, fontsize=12)
ax6.set_ylabel('Elektrische Leistung in $\mathrm{MW_{el}}$', fontsize=12)
ax6.set_xlabel('Wärmeleistung in $\mathrm{MW_{th}}$', fontsize=12)
# plt.show()
plt.savefig('../results/plots/scatter_plot_EES_charge_influence.png', dpi=300)

fig7, ax7 = plt.subplots()

ax7.scatter(x=produktion_th_a1,
                y=produktion_el_a1,
                marker='o',
                c=[beuth_col_2],
                zorder=1,
                label=None,
                alpha=1)
ax7.grid(color='grey',  # beuth_col_2,
         linestyle='-',
         linewidth=0.5,
         zorder=2)
ax7.scatter(x=produktion_th_a1[zeitreihen_a1['batterie_entladen'] > 0][10:],
           y=produktion_el_a1[zeitreihen_a1['batterie_entladen'] > 0][10:],
            marker='_',#'_',
            s=20,
            c=[beuth_col_3],
            zorder=10,
            alpha=1,#.6,
            label='ohne Speicher')
ax7.scatter(x=produktion_th_a1[zeitreihen_a1['batterie_entladen'] > 0][10:],
           y=produktion_el_a1[zeitreihen_a1['batterie_entladen'] > 0][10:],
            marker='_',#'_',
            s=20,
            c=[beuth_red],#'g',
            zorder=10,
            alpha=1,
            label='mit Stromspeicher')
ax7.set_ylim([-250, 1050])
# ax7[0].set_xlim([0, 1000])
ax7.legend(loc=4, fontsize=12)
ax7.set_ylabel('Elektrische Leistung in $\mathrm{MW_{el}}$', fontsize=12)
ax7.set_xlabel('Wärmeleistung in $\mathrm{MW_{th}}$', fontsize=12)
# plt.show()
plt.savefig('../results/plots/scatter_plot_EES_discharge_influence.png', dpi=300)

fig8, ax8 = plt.subplots()
ax8.scatter(x=produktion_th_a1,
                y=produktion_el_a1,
                marker='o',
                c=[beuth_col_2],
                zorder=1,
                label=None,
                alpha=1)
ax8.grid(color='grey',  # beuth_col_2,
         linestyle='-',
         linewidth=0.5,
         zorder=2)
ax8.scatter(x=produktion_th_a1[zeitreihen_a1['P2H_th'] > 0][10:],
           y=produktion_el_a1[zeitreihen_a1['P2H_th'] > 0][10:],
            marker='_',#'_',
            s=20,
            c=[beuth_red],
            zorder=10,
            alpha=1,#.6,
            label='Heat from P2H')
# ax8.scatter(x=produktion_th_a1[zeitreihen_a1['batterie_entladen'] > 0][10:],
#            y=produktion_el_a1[zeitreihen_a1['batterie_entladen'] > 0][10:],
#             marker='_',#'_',
#             s=20,
#             c=[beuth_red],#'g',
#             zorder=10,
#             alpha=1,
#             label='mit Stromspeicher')
ax8.set_ylim([-250, 1050])
# ax7[0].set_xlim([0, 1000])
ax8.legend(loc=4, fontsize=12)
ax8.set_ylabel('Elektrische Leistung in $\mathrm{MW_{el}}$', fontsize=12)
ax8.set_xlabel('Wärmeleistung in $\mathrm{MW_{th}}$', fontsize=12)
# plt.show()
plt.savefig('../results/plots/scatter_plot_P2H_operation.png', dpi=300)