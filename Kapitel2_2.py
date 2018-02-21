# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 09:44:06 2017
@author: Tillmann Bors
Kapitel 2 (V2 angepasst)
"""

#Initialisierung
import pandas as pd  
import pprint as pp  
import matplotlib.pyplot as plt

from oemof import solph  
from oemof import outputlib  

pp.pprint('Import complete')

# Data Import  
data = pd.read_csv('data_input/example_data.csv', sep=',')  
pp.pprint('Data read')

#Energysystem
date_time_index = pd.date_range('1/1/2017', periods=168,  
	 	freq='H')  
energysystem = solph.EnergySystem(timeindex=date_time_index)

#Busses    
bgas = solph.Bus(label="natural_gas")    
bel = solph.Bus(label="electricity")  

#Sinks  
solph.Sink(label='demand', inputs={bel: solph.Flow(  
	 	fixed=True, actual_value=data['demand_el'],  
	 		nominal_value=5460)})  
solph.Sink(label='excess', inputs={bel: solph.Flow()})  

#Sources  
solph.Source(label='pv', outputs={bel: solph.Flow(fixed=True,  
	 	actual_value=data['pv'], nominal_value=15000)})  
solph.Source(label='rgas', outputs={bgas: solph.Flow(  
	 	nominal_value=194397000, summed_max=1000000)})  
solph.Source(label='shortage', outputs={bel: solph.Flow(  
 	variable_costs=5000)})  

#Transformer  
solph.LinearTransformer(  
	 label='pp_gas',  
	 inputs={bgas: solph.Flow()},  
	 outputs={bel: solph.Flow(nominal_value=2500,  
	 variable_costs=50,  
	 fixed_costs=1000)},  
	 conversion_factors={bel: 0.58})

pp.pprint('System defined')

#Create Problem and Solve  
om = solph.OperationalModel(energysystem)  
om.solve(solver='cbc', solve_kwargs={'tee': True})  

pp.pprint('System solved')

#Data output
pp.pprint('Data Output')
results = outputlib.DataFramePlot(energy_system=energysystem)  
  
pv = results.slice_by(obj_label='pv', type='to_bus',  
                           date_from='2017-01-01 00:00:00',  
                          date_to='2017-01-07 23:00:00')  

demand = results.slice_by(obj_label='demand',  
                          date_from='2017-01-01 00:00:00',  
                          date_to='2017-01-07 23:00:00')  

pp.pprint({  
    'res_share': pv.sum()/demand.sum(),  
    'objective': energysystem.results.objective  
	    })  


pp.pprint('Plots')

myplot = outputlib.DataFramePlot(energy_system=energysystem)  
# Plotting the balance around the electricity plot for one week using a  
# combined stacked plot  

cdict = {'pv': 'gold',
         'demand': 'black',
         'excess': 'red',
         'shortage':'beige',
         'pp_gas':'silver'}

fig = plt.figure(figsize=(24, 14))  
plt.rc('legend', **{'fontsize': 19})  
plt.rcParams.update({'font.size': 19})  
plt.style.use('grayscale')  
   
handles, labels = myplot.io_plot(  
	    bus_label='electricity',cdict=cdict,  
	    barorder=['pv', 'pp_gas', 'shortage'],  
	    lineorder=['demand','excess'],  
	    line_kwa={'linewidth': 4},  
	    ax=fig.add_subplot(2, 1, 1),  
	    date_from="2017-01-01 00:00:00",  
	    date_to="2017-01-07 23:00:00",  
	    )  
myplot.ax.set_ylabel('Power in kW')  
myplot.ax.set_xlabel('Date')  
myplot.ax.set_title("Electricity bus")  
myplot.set_datetime_ticks(tick_distance=24, date_format='%d-%m-%Y')  
myplot.outside_legend(handles=handles, labels=labels)  
plt.show()  

pp.pprint('Write Files')

#write the "raw" plot Dataframe         
myplot.to_csv('data_output/plot_data.csv')    
    
#manipulate the plot multi-index dataframe to get a Dataframe with only two indexes: “datetime” and “obj_label”   
#csvdata=pd.pivot_table(myplot, index='datetime', values='val', columns='obj_label', aggfunc='sum')    
#csvdata.to_csv('data_output/export_data.csv') 

pp.pprint('Plot data written')
pp.pprint('End')
