import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import helpers

abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

def preprocess_heat_feedin_timeseries():
    r"""
    Cleans the heat feedin timeseries.

    Returns
    -------
    heat_profile_dessau
    """
    raw_heat_profile = pd.ExcelFile('data_raw/heat_demand/Primaer_Waermeleistung_17.xlsm')

    heat_profile_dessau = pd.DataFrame(columns = ['V:m3/h', 'Q:MW', 'At:°C'])

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
        heat_profile_dessau = pd.concat([heat_profile_dessau, heat_profile_month], sort=False)

    return heat_profile_dessau['Q:MW']


def plot_compare_heat_profiles(experiment_cfg, results_dir):
    r"""
    Creates a plot to compare to demandlib profile.

    Returns
    -------
    None
    """
    print(os.path.join(results_dir, 'data_preprocessed/demand_heat.csv'))
    demand_heat = pd.read_csv(os.path.join(results_dir, 'data_preprocessed/demand_heat.csv'), index_col=0,
        parse_dates=True)
    heat_profile = pd.read_csv(os.path.join(results_dir, 'data_preprocessed/heat_profile_dessau.csv'))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 5))
    ax1.plot(heat_profile['Q:MW'])
    ax2.plot(demand_heat['efh'].resample('1D').min())
    ax2.plot(demand_heat['efh'].resample('1D').max())
    plt.show()

    return None


def preprocess_closed_data(config_path, results_dir):
    r"""
    Runs the closed data preprocessing pipeline.

    Parameters
    ----------
    config_path: path

    results_dir: path

    Returns
    -------
    None

    """
    heat_profile_dessau = preprocess_heat_feedin_timeseries()
    heat_profile_dessau.to_csv(os.path.join(results_dir, 'data_preprocessed/heat_profile_dessau.csv'))

    # plot_compare_heat_profiles(config_path, results_dir)

    return None


if __name__ == '__main__':
    experiment_cfg, results_dir = helpers.setup_experiment()
    preprocess_closed_data(experiment_cfg, results_dir)
