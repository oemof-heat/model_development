import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

raw_heat_profile = pd.ExcelFile('/home/jann/ownCloud/oemof_heat/04_Konkrete_Systeme/B1/02_Input/Daten/Stadtwerke_Dessau/2018-11-19_Mail_von_Frau_Ewald/Primaer_Waermeleistung_17.xlsm')

heat_profile = pd.DataFrame(columns = ['V:m3/h', 'Q:MW', 'At:°C'])

for month in ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']:

    # parse month sheet from excel
    heat_profile_month = raw_heat_profile.parse(month, header=3, index_col=(0), usecols=(1,2,3,4,5,6,7,8,9,10))
    heat_profile_month.index.names = ['date']

    # stop at the last day of the month
    heat_profile_month = heat_profile_month[:-5]
    heat_profile_month = heat_profile_month.replace({'Linienstörung': np.nan})
    heat_profile_month = heat_profile_month.dropna(how='all')

    # rename columns
    heat_profile_month.columns = ['Zeit', 'V:m3/h', 'Q:MW', 'At:°C', 'Zeit.1', 'V:m3/h.1', 'Q:MW.1', 'At:°C.1', 'dAt:°C']

    # split min and max timeseries
    heat_profile_month_max = heat_profile_month[['Zeit', 'V:m3/h', 'Q:MW', 'At:°C']]
    heat_profile_month_min = heat_profile_month[['Zeit.1', 'V:m3/h.1', 'Q:MW.1', 'At:°C.1']]
    heat_profile_month_min.columns = ['Zeit', 'V:m3/h', 'Q:MW', 'At:°C']

    # convert index to datetimeindex
    dates = heat_profile_month_max.index.get_level_values('date')
    times = heat_profile_month_max['Zeit']
    heat_profile_month_max.index = pd.to_datetime(dates.astype(str) + ' ' + times.astype(str))

    dates = heat_profile_month_min.index.get_level_values('date')
    times = heat_profile_month_min['Zeit']
    heat_profile_month_min.index = pd.to_datetime(dates.astype(str) + ' ' + times.astype(str))

    # combine min and max timeseries
    heat_profile_month = pd.concat([heat_profile_month_min.drop('Zeit', axis=1), heat_profile_month_max.drop('Zeit', axis=1)], sort=False)
    heat_profile_month = heat_profile_month.sort_index()

    # add it to the year profile
    heat_profile = pd.concat([heat_profile, heat_profile_month], sort=False)

heat_profile.to_csv('/home/jann/ownCloud/oemof_heat/04_Konkrete_Systeme/B1/02_Input/Daten/Stadtwerke_Dessau/2018-11-19_Mail_von_Frau_Ewald/heat_profile.csv')

# heat_profile['Q:MW'].plot()
# plt.show()

# plot to compare to demandlib profile
demand_heat = pd.read_csv('/home/jann/Desktop/repos/oemof_heat/System_B/model_runs/experiment_1/data_preprocessed/demand_heat.csv', index_col=0)
print(demand_heat.columns)
fig, ax = plt.subplots(figsize=(12,5))
ax.plot(heat_profile['Q:MW'])
# ax.plot(demand_heat['efh'])
plt.show()