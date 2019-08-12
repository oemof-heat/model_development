District heating model
----------------------

## Analysis pipeline

Raw data is contained in the folder `data` in the following structure:

```
.data
|--timeseries/
   |--el_spot_prices_smard/
   |--merra2_dessau/
   |--SRL_data
|--parameters.csv
|--timeseries.csv
|--scenarios.csv
```

To specify file paths for an experiment run, provide a config file in `.yml`-format in the directory `experiment_config`.
A `color_dict.yml` defines colors for plots.

```
experiment_configs/
|--experiment.yml
|--color_dict.yml
```

Preprocessing yields the following directory structure:

```
.data_preprocessed
|--timeseries/
   |--demand_heat
   |--price_electricity_spot
   |--temperature
|--parameters.csv
|--timeseries.csv
|--scenarios.csv
|--model_runs.csv
```
Postprocessing gives back the following:

```
.data_postprocessed
|--timeseries/
|--|--
|--parameters.csv
|--timeseries.csv
|--scenarios.csv
|--model_runs.csv
```

Run the plot scripts to produce plot data and plots:

```
data_plots/
plots/
```