import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import timeit

start_time = timeit.default_timer()

# xlsx = pd.ExcelFile('Data\Strom und Wärmedaten 2011 + Extrapolation_Rev9.xlsx')
xlsx = pd.ExcelFile('Strom und Wärmedaten 2011 + Extrapolation_Rev9.xlsx')
print(" ")
print("***Import Excel file***" )
print("Imported Excel file has", len(xlsx.sheet_names), "sheets:" )
for name in xlsx.sheet_names:
    print("-->",name)
df_Daten = pd.read_excel(xlsx, 'Berechnete Daten')

timestep_end = 8763  # first year only

col_index = [0,1,3,5,-5]
new_colnames = ["Timestep_abs","Date","Timestep_year","demand_th_rel","residual_el_abs"]
df_compact=df_Daten.iloc[3:timestep_end,col_index]
print(" ")
print("***created new DataFrame from columns:***")
for col_name in df_Daten.columns.values[col_index]:
    print(col_name)
print(" ")
print("***changing column names:***")
print("from old name --> to new name")
for col_name, col_name_new in zip(df_Daten.columns.values[col_index], new_colnames):
    print(col_name, " --> ", col_name_new)
df_compact.columns = new_colnames

# Add new column with relative heat demand.
df_compact["demand_th"] = df_compact["demand_th_rel"]/100  # [-]

# Add new column with relative electricity demand (only positive share of residual load).
demand_el_max = df_compact['residual_el_abs'].max()
df_compact['demand_el_A'] = df_compact['residual_el_abs'].clip(lower=0)/demand_el_max

# Add new column with relative negative residual load (only negative share of residual load).
# Values are turned positive and will be used as positive "source" in the oemof application
demand_el_min = df_compact['residual_el_abs'].min()
df_compact['neg_residual_el_A'] = df_compact['residual_el_abs'].clip(upper=0)/demand_el_min

def bedarfsprofil_B(x):
    """Define the positive share of load profile "Bedarfsprofil B". Unit: 1."""
    threshold_upper = 0.8
    threshold_lower = 0.2
    if x < threshold_lower:
        y = 0
    elif x > threshold_upper:
            y = 1
    else:
        y = 1/threshold_upper*x
    return y

# Calculate load profiles
print(" ")
print("***Start calculating load profils***")
df_compact['demand_el_B'] = df_compact['demand_el_A'].apply(bedarfsprofil_B)  # [-]
print("--> 50% Done!")
print(" " )
# Negative share of load profile "Bedarfsprofil_B"
df_compact['neg_residual_el_B'] = df_compact['neg_residual_el_A'].apply(bedarfsprofil_B)  # [-]
print("***Finish calculating load profils!***")

# Create dataframes with input data (load profils A and B) for oemof-application
coln_read_A =  ['Timestep_abs','demand_el_A','demand_th','neg_residual_el_A']
coln_read_B =  ['Timestep_abs','demand_el_B','demand_th','neg_residual_el_B']
coln_input = ['timestep','demand_el','demand_th','neg_residual']
df_input_A = pd.DataFrame()
df_input_B = pd.DataFrame()
df_input_A[coln_input] = df_compact[coln_read_A]
df_input_B[coln_input] = df_compact[coln_read_B]

# plt.plot(df_compact['demand_el_B'])
# plt.plot(df_compact['demand_el_A'])
# plt.scatter(df_compact['demand_el_A'], df_compact['demand_el_B'])
# plt.scatter(df_compact['neg_residual_el_A'], df_compact['neg_residual_el_B'])
# plt.show()

# Export data
df_input_A.to_csv("demand_profile_A_nominal.csv", encoding='utf-8', index=False)
df_input_B.to_csv("demand_profile_B_nominal.csv", encoding='utf-8', index=False)

print(" ")
print("***Finish writing demand profiles A and B to csv files***")
stop_time = timeit.default_timer()
run_time = stop_time - start_time
print(" " )
print("Info: Process took", "%6.2f" % run_time, "seconds to run.")
print(" " )
print("***END***")