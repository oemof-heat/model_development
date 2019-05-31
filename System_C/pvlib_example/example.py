import pandas as pd
import numpy as np
import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.tracking import SingleAxisTracker, singleaxis
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.irradiance import get_total_irradiance, dni

###############################################################################
# DEFINITIONS NEEDED FOR SOLPOS AND AOI
###############################################################################
# Define Location
loc = Location(name='Berlin', latitude=52.5200, longitude=13.4050,
               altitude=34, tz='Etc/GMT-2')

# Define Time
time = pd.DatetimeIndex(start='2018', end='2019', freq='1h')
time = time.tz_localize(loc.tz)

# Define Module and Inverter (needed for PV System)
sa_mod = pvlib.pvsystem.retrieve_sam('SandiaMod')
sa_inv = pvlib.pvsystem.retrieve_sam('cecinverter')
mod = sa_mod['Canadian_Solar_CS5P_220M___2009_']
inv = sa_inv['ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_']

###############################################################################
# SOLAR POSITION (1)
###############################################################################
# Get Solar Position
solpos = pvlib.solarposition.get_solarposition(time, loc.latitude,
                                               loc.longitude, loc.altitude)
# to check solar position at 12:00
print(solpos.loc['2018-05-23 12:00:00'])

###############################################################################
# GET CLEARSKY IRRADIATION
###############################################################################
# extra direct normal irradiation
dni_extra = pvlib.irradiance.get_extra_radiation(time)
# air-mass
airmass = pvlib.atmosphere.get_relative_airmass(solpos['apparent_zenith'])
# air-pressure
pressure = pvlib.atmosphere.alt2pres(loc.altitude)
# absolute air-mass
am_abs = pvlib.atmosphere.get_absolute_airmass(airmass, pressure)
# linke turbidity
tl = pvlib.clearsky.lookup_linke_turbidity(time, loc.latitude, loc.longitude)
# clearsky irradiation
cs = pvlib.clearsky.ineichen(solpos['apparent_zenith'], am_abs, tl,
                             dni_extra=dni_extra, altitude=loc.altitude)

###############################################################################
# WEATHER DATA FOR RUNNING MODELCHAIN
###############################################################################
w_data = {'ghi': cs['ghi'], 'dni': cs['dni'], 'dhi': cs['dhi'],
          'temp_air': 20, 'wind_speed': 5}
weather = pd.DataFrame(w_data)

###############################################################################
# PV SYSTEM WITHOUT TRACKING (2)
###############################################################################
system = PVSystem(name='Berlin PV-System', surface_tilt=30,
                  surface_azimuth=180, surface_type='urban',
                  module=mod, module_parameters=mod,
                  inverter=inv, inverter_parameters=inv)
mc = ModelChain(system, loc, name='Berlin ModelChain')
mc.run_model(times=weather.index, weather=weather)

# Get Angle of Incidence (theta)
aoi = mc.aoi

###############################################################################
# PV SYSTEM WITH TRACKING (2)
###############################################################################
sat_system = SingleAxisTracker(name='Berlin SAT-PV-System',
                               axis_tilt=0, axis_azimuth=0, max_angle=90,
                               module=mod, module_parameters=mod,
                               inverter=inv, inverter_parameters=inv)
sat_mc = ModelChain(sat_system, loc, name='Berlin SAT ModelChain')
sat_mc.run_model(times=weather.index, weather=weather)

# Alternative tracking.singleaxis()
# track = pvlib.tracking.singleaxis(solpos['apparent_zenith'],
#                                   solpos['azimuth'],
#                                   axis_tilt=0, axis_azimuth=0,
#                                   max_angle=90, backtrack=True,
#                                   gcr=2.0/7.0)

# Get Angle of Incidence (theta)
sat_aoi = sat_mc.aoi
# track_aoi = track['aoi']

###############################################################################
# POA DIRECT (3)
# Note: w/ tracking does not work, because sat_aoi has None values
###############################################################################
# Get POA Direct w/out tracking (3a)
poa_direct = np.maximum(cs['dni'] * np.cos(np.radians(mc.aoi)), 0)

# Alternative Get POA Direct w/out tracking (3a/b)
total_irrad = pvlib.irradiance.get_total_irradiance(system.surface_tilt,
													system.surface_azimuth,
													solpos['apparent_zenith'],
													solpos['azimuth'],
													cs['dni'], cs['ghi'], cs['dhi'],
													dni_extra=dni_extra,
                                                    model='haydavies')
poa_direct_alt = total_irrad['poa_direct']

# Another Alternative Get POA Direct w/out tracking (3b)
dni = pvlib.irradiance.dni(cs['ghi'], cs['dhi'], solpos['zenith'],
                           clearsky_dni=None, clearsky_tolerance=1.1,
                           zenith_threshold_for_zero_dni=88.0,
                           zenith_threshold_for_clearsky_limit=80.0)
poa_direct_alt_2 = np.maximum(dni * np.cos(np.radians(mc.aoi)), 0)
