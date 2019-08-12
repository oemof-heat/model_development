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
.experiment_configs/
|--experiment.yml
|--color_dict.yml
```

Preprocessing yields the following directory structure, contained within `results/<name of experiment_config>`:

```
.experiment_1/
|--data_preprocessed
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
.experiment_1/
|--data_postprocessed/
   |--timeseries/
      |--flows
      |--costs
      |--emissions
   |--parameters.csv
   |--timeseries.csv
   |--scenarios.csv
   |--model_runs.csv
```

`timeseries/` contains
* flows
* variable_costs
* emissions

`parameters.csv` contains:  
* hours_full_load
* hours_operating_sum
* number_starts
* energy_produced_sum
* energy_produced_max
* energy_produced_min
* energy_heat_storage_discharge_sum
* energy_losses_heat_dhn_sum
* energy_produced_during_operation_sum
* energy_excess_sum
* energy_excess_max
* energy_import_sum
* energy_import_max
* energy_consumed_gas_sum
* energy_consumed_electricity_sum
* energy_consumed_pump_sum
* cost_operation_sum
* cost_investment_sum
* cost_specific_heat_mean (Wärmegestehungskosten)
* seasonal_performance_factor_heat_pumps_mean
* fraction_renewables

### Plots

Run the plot scripts to produce plot data and plots:

```
data_plots/
plots/
```

* Load duration curves CHP und PtH
* Full load hours GuD und PtH
