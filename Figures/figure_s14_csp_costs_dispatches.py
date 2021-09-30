# -*- coding: utf-8 -*-
"""
Created on Tue Jan 26 20:24:53 2021

@author: Kathleen
"""
##===============================================
# Dispatch Curves for range of CSP costs
##===============================================

import copy
import numpy as np

import pickle
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.pylab as pylab

import datetime
from matplotlib.dates import HourLocator, AutoDateLocator, DateFormatter, drange

PV_c = 'orange' 
wind_c = 'blue' 
pgp_c = 'pink' 
batt_c = 'purple'
dem_c = 'black'
csp_c = 'yellow'
tes_c = 'cyan'


##===========================================
#Supporting Functions
##===========================================
def func_time_conversion (input_data, window_size, operation_type = 'mean'):
    
    # NOTE: THIS FUNCTION HAS ONLY BEEN VERIFIED FOR PROPER WRAP-AROUND BEHAVIOR
    #       FOR 'mean'
    # For odd windows sizes, easy. For even need to consider ends where you have half hour of data.

    N_periods = len(input_data)
    input_data_x3 = np.concatenate((input_data,input_data,input_data))
    
    half_size = window_size / 2.
    half_size_full = int(half_size) # number of full things for the mean

    output_data = np.zeros(len(input_data))
    
    for ii in range(len(output_data)):
        if half_size != float (half_size_full): # odd number, easy
            if (operation_type == 'mean'):
                output_data[ii] = np.sum(input_data_x3[N_periods + ii - half_size_full : N_periods + ii + half_size_full + 1 ])/ float(window_size)
            elif(operation_type == 'min'):
                output_data[ii] = np.min(input_data_x3[N_periods + ii - half_size_full : N_periods + ii + half_size_full + 1 ])
            elif(operation_type == 'max'):
                output_data[ii] = np.max(input_data_x3[N_periods + ii - half_size_full : N_periods + ii + half_size_full  + 1])
            elif(operation_type == 'sum'):
                output_data[ii] = np.sum(input_data_x3[N_periods + ii - half_size_full : N_periods + ii + half_size_full  + 1])
        else: # even number need to include half of last ones
            if (operation_type == 'mean'):
                output_data[ii] = ( np.sum(input_data_x3[N_periods + ii - half_size_full : N_periods + ii + half_size_full ])  \
                        + input_data_x3[N_periods + ii - half_size_full -1 ] *0.5 +  input_data_x3[N_periods + ii + half_size_full + 1 ] *0.5) / window_size
            elif(operation_type == 'min'):
                output_data[ii] = np.min(input_data_x3[N_periods + ii - half_size_full -1 : N_periods + ii + half_size_full + 1 ])
            elif(operation_type == 'max'):
                output_data[ii] = np.max(input_data_x3[N_periods + ii - half_size_full -1 : N_periods + ii + half_size_full + 1 ])
            elif(operation_type == 'sum'):
                output_data[ii] = (
                        np.sum(input_data_x3[N_periods + ii - half_size_full : N_periods + ii + half_size_full ]) 
                        + input_data_x3[N_periods + ii - half_size_full -1 ] *0.5 +  input_data_x3[N_periods + ii + half_size_full + 1 ] *0.5
                        ) 
        
    return output_data

##===========================================
def func_find_period (input_data):
    
    window_size = input_data['window_size']
    eff_window_size = copy.deepcopy(window_size) # If even go up to next odd number
    if eff_window_size == 2 * int (eff_window_size /2 ):  # check if even
        eff_window_size = eff_window_size + 1             # if so, add 1
    data = input_data['data']
    search_option = input_data['search_option']
    print_option = input_data['print_option']
    
    # -------------------------------------------------------------------------
    
    # Get the down-scaled data
    data_in_window = func_time_conversion(data, eff_window_size, 'mean')
    
    # -------------------------------------------------------------------------
    
    if search_option == 'max':
        
        center_index = int(np.argmax(data_in_window))
        value = np.max(data_in_window)
        
    elif search_option == 'min':

        center_index = int(np.argmin(data_in_window))
        value = np.min(data_in_window)

    # -------------------------------------------------------------------------
    # If interval would go over boundary, then move inteval
    if center_index < int(eff_window_size/2):
        center_index = int(eff_window_size/2)
    if center_index > len(data)- int(eff_window_size/2) - 1:
        center_index = len(data) - 1 - int(eff_window_size/2)

    # The same algorithm as in func_time_conversion()

    left_index = center_index - int(eff_window_size/2)
    right_index = center_index + int(eff_window_size/2)

    # -------------------------------------------------------------------------

    # output
    if print_option == 1:
        
        print ( 'center index = {}, value = {}'.format(center_index, value))
        print ( 'left index = {}, right index = {}'.format(left_index, right_index))

    output = {
        'value':        value,
        'left_index':   left_index,
        'right_index':  right_index,
        'center_index': center_index,
        }

    return output

##===========================================
#Read in pickle file
##===========================================

with open('C:/Users/Kathleen/Desktop/Temp/SensitivityCSP/CSP0.5x_TES1.0x_20210306-051844.pickle', 'rb') as handle:
            [[input_case,  input_tech,  input_time],
             [results_case, results_tech,  results_time]] = pickle.load(handle)

##===========================================================================================================
# Define Sources and Sinks
##============================================================================================================

# 5-day averaging
hours_to_avg = 5*24
sources = []
sinks = []
pal1 = []
pal2 = []
labels1 = []

demand_source = func_time_conversion(results_time['demand potential'], hours_to_avg)

try:
    wind_source = func_time_conversion(results_time['wind potential'], hours_to_avg)
    sources.append(wind_source)
    pal1.append(wind_c)
    labels1.append('Wind')
    wind_included = True
except: 
    print('No wind')
    wind_included = False

try:
    PV_source = func_time_conversion(results_time['PV potential'], hours_to_avg)
    sources.append(PV_source)
    pal1.append(PV_c)
    labels1.append('PV')
    PV_included = True
except: 
    print('No PV')
    PV_included = False

try:
    if results_tech['CSP_TES capacity'] > 0:
        tes_source = func_time_conversion(results_time['CSP_TES dispatch'], hours_to_avg) * 0.3774
        sources.append(tes_source)
        pal1.append(tes_c)
        labels1.append('TES')
        tes_included = True
    else:
        print('No TES')
        tes_included = False
except: 
    print('No TES')
    tes_included = False


try:
    csp_source = func_time_conversion(results_time['CSP_turbine dispatch'], hours_to_avg)
    csp_included = True
    if tes_included:
        csp_source = csp_source - tes_source
        sources.insert(-1, csp_source)
        pal1.insert(-1, csp_c)
        labels1.insert(-1, 'CSP')
    else:
        sources.append(csp_source)
        pal1.append(csp_c)
        labels1.append('CSP')
except: 
    print('No CSP')
    csp_included = False

try:
    if results_tech['battery capacity'] > 0:
        batt_source = func_time_conversion(results_time['battery dispatch'], hours_to_avg)
        sources.append(batt_source)
        pal1.append(batt_c)
        labels1.append('Battery')
        batt_included = True
    else:
        print('No Batteries')
        batt_included = False
except: 
    print('No Batteries')
    batt_included = False

try:
    pgp_source = func_time_conversion(results_time['from_PGP dispatch'], hours_to_avg)
    sources.append(pgp_source)
    pal1.append(pgp_c)
    labels1.append('PGP')
    pgp_included = True
except: 
    print('No PGP')
    pgp_included = False

demand_sink = np.multiply(func_time_conversion(results_time['demand potential'], hours_to_avg), -1)
sinks.append(demand_sink)
pal2.append(dem_c)
if tes_included:
    tes_sink = np.multiply(func_time_conversion(results_time['CSP_TES in dispatch'], hours_to_avg), -1) * 0.3774
    sinks.append(tes_sink)
    pal2.append(tes_c)

if batt_included:
    batt_sink = np.multiply(func_time_conversion(results_time['battery in dispatch'], hours_to_avg), -1)
    sinks.append(batt_sink)
    pal2.append(batt_c)

if pgp_included:
    pgp_sink = np.multiply(func_time_conversion(results_time['to_PGP dispatch'], hours_to_avg), -1)
    sinks.append(pgp_sink)
    pal2.append(pgp_c)

num_storage = tes_included + batt_included + pgp_included
num_cols = num_storage + 3

#=======================================================
# Plot dispatch curve
#=======================================================
params = {'legend.fontsize': 'large',
          'figure.figsize': (11.5, 15), 
         'axes.labelsize': 'x-large',
         'axes.titlesize':'x-large',
         'xtick.labelsize':'large',
         'ytick.labelsize':'large'}
pylab.rcParams.update(params)

date1 = datetime.datetime(input_case['year_start'], input_case['month_start'], 
                          input_case['day_start'], input_case['hour_start'] -1)
date2 = datetime.datetime(input_case['year_end'], input_case['month_end'], 
                          input_case['day_end'], input_case['hour_end'] -1)
delta = datetime.timedelta(hours=1)
quick_dates = drange(date1, date2, delta)
x = quick_dates


y1 = np.vstack(sources)
y2 = np.vstack(sinks)
labels2 = ["Demand"]


fig = plt.figure()
ax3 = plt.subplot2grid((6, 5), (0, 0), colspan=3, rowspan=2)
ax3.stackplot(x, y1, colors=pal1, labels=labels1)
ax3.stackplot(x, y2, colors=pal2, labels=labels2)
ax3.plot(x, demand_source, '-', color=dem_c, linewidth=1.2)
ax3.set_xlim(quick_dates[0], quick_dates[-1])
ax3.set_ylim(-2.7,2.5)
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)
ax3.xaxis.set_major_locator(AutoDateLocator())
ax3.xaxis.set_major_formatter(DateFormatter('%b'))
ax3.xaxis.set_tick_params(direction='out', which='both')
ax3.yaxis.set_tick_params(direction='out', which='both')
ax3.yaxis.set_major_locator(ticker.MultipleLocator(1))

##=====================================================
# Define sources and Sinks for Panels
##=====================================================

demand_source = results_time['demand potential']
if wind_included:
    wind_source = results_time['wind potential']
if PV_included:
    pv_source = results_time['PV potential']
if batt_included:
    batt_source = results_time['battery dispatch']
if tes_included:
    tes_source = results_time['CSP_TES dispatch'] * 0.3774
if csp_included:
    csp_source = results_time['CSP_turbine dispatch'] 
    if tes_included:
        csp_source = csp_source - tes_source
if pgp_included:
    pgp_source = results_time['from_PGP dispatch']

demand_sink = results_time['demand potential']
if batt_included:
    batt_sink = results_time['battery in dispatch']
if tes_included:
    tes_sink = results_time['CSP_TES in dispatch'] * 0.3774
if pgp_included:
    pgp_sink = results_time['to_PGP dispatch']

start_hours = []
end_hours = []
if tes_included:
    study_variable_dict_1 = {
        'window_size':      4*24,
        'data':             results_time['CSP_TES dispatch'], 
        'print_option':     0,
        'search_option':    'max'
        }
    study_output_1 = func_find_period(study_variable_dict_1)
    start_hours.append(study_output_1['left_index'])
    end_hours.append(study_output_1['right_index'])

if batt_included:
    study_variable_dict_2 = {
        'window_size':      4*24,
        'data':             results_time['battery dispatch'], 
        'print_option':     0,
        'search_option':    'max'
        }
    study_output_2 = func_find_period(study_variable_dict_2)
    start_hours.append(study_output_2['left_index'])
    end_hours.append(study_output_2['right_index'])

if pgp_included:
    study_variable_dict_3 = {
        'window_size':      4*24,
        'data':             results_time['from_PGP dispatch'], 
        'print_option':     0,
        'search_option':    'max'
        }
    study_output_3 = func_find_period(study_variable_dict_3)
    start_hours.append(study_output_3['left_index'])
    end_hours.append(study_output_3['right_index'])

##=================================================
# Loop to plot panels of max storage dispatch
##=================================================

for i in range(num_storage):
    start_hour = start_hours[i]
    end_hour = end_hours[i]

    delta1 = datetime.timedelta(hours=(start_hour-6)) # -6 converts UTC to CST
    delta2 = datetime.timedelta(hours=(end_hour-6))
    
    date1 = datetime.datetime(input_case['year_start'], 1, 1, 0) + delta1
    date2 = datetime.datetime(input_case['year_start'], 1, 1, 0) + delta2

    delta = datetime.timedelta(hours=1)
    dates = drange(date1, date2, delta)

    x = dates
    
    sources = []
    demand_source1 = demand_source[start_hour:end_hour]
    
    demand_sink1 = np.multiply(demand_sink[start_hour:end_hour],-1)
    sinks = [demand_sink1]
    
    
    if wind_included:
        wind_source1 = wind_source[start_hour:end_hour]
        sources.append(wind_source1)
    if PV_included:
        pv_source1 = pv_source[start_hour:end_hour]
        sources.append(pv_source1)
    if csp_included:
        csp_source1 = csp_source[start_hour:end_hour]
        sources.append(csp_source1)
    if tes_included:
        tes_source1 = tes_source[start_hour:end_hour]
        sources.append(tes_source1)
        tes_sink1 = np.multiply(tes_sink[start_hour:end_hour],-1)
        sinks.append(tes_sink1)
    if batt_included:
        batt_source1 = batt_source[start_hour:end_hour]
        sources.append(batt_source1)
        batt_sink1 = np.multiply(batt_sink[start_hour:end_hour],-1)
        sinks.append(batt_sink1)
    if pgp_included:
        pgp_source1 = pgp_source[start_hour:end_hour]
        sources.append(pgp_source1)
        pgp_sink1 = np.multiply(pgp_sink[start_hour:end_hour],-1)
        sinks.append(pgp_sink1)

    y1 = np.vstack(sources)
    y2 = np.vstack(sinks)
    
    ax = plt.subplot2grid((6, 5), (0, 3+i), colspan=1, rowspan=2)
    ax.stackplot(x, y1, colors=pal1, labels=labels1)
    ax.stackplot(x, y2, colors=pal2, labels=labels2)
    ax.plot(x, demand_source1, '-', color=dem_c, linewidth=1.2)

    ax.set_xlim(dates[0], dates[-1])
    ax.set_ylim(-2.7,2.5)
    
    ax.xaxis.set_major_locator(HourLocator(byhour=range(24),interval=24))
    ax.xaxis.set_major_formatter(DateFormatter('%b %d')) #This is CST!!! 7am
    plt.setp(ax.get_yticklabels(), visible=False)
    ax.yaxis.set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
    plt.xticks(rotation=30, ha='right')
    ax.xaxis.set_tick_params(direction='out', which='both')
    ax.yaxis.set_tick_params(direction='out', which='both')
 
ax.legend(bbox_to_anchor=(1.02, 1.02),frameon=False)
chartBox = ax.get_position()
ax.set_position([chartBox.x0, chartBox.y0, chartBox.width*1, chartBox.height])

##===========================================
#Read in pickle file
##===========================================

with open('C:/Users/Kathleen/Desktop/Temp/SensitivityCSP/CSP0.25x_TES1.0x_20210306-013237.pickle', 'rb') as handle:
            [[input_case,  input_tech,  input_time],
             [results_case, results_tech,  results_time]] = pickle.load(handle)

##===========================================================================================================
# Define Sources and Sinks
##============================================================================================================

# 5-day averaging
hours_to_avg = 5*24
sources = []
sinks = []
pal1 = []
pal2 = []
labels1 = []

demand_source = func_time_conversion(results_time['demand potential'], hours_to_avg)

try:
    wind_source = func_time_conversion(results_time['wind potential'], hours_to_avg)
    sources.append(wind_source)
    pal1.append(wind_c)
    labels1.append('Wind')
    wind_included = True
except: 
    print('No wind')
    wind_included = False

try:
    PV_source = func_time_conversion(results_time['PV potential'], hours_to_avg)
    sources.append(PV_source)
    pal1.append(PV_c)
    labels1.append('PV')
    PV_included = True
except: 
    print('No PV')
    PV_included = False

try:
    if results_tech['CSP_TES capacity'] > 0:
        tes_source = func_time_conversion(results_time['CSP_TES dispatch'], hours_to_avg) * 0.3774
        sources.append(tes_source)
        pal1.append(tes_c)
        labels1.append('TES')
        tes_included = True
    else:
        print('No TES')
        tes_included = False
except: 
    print('No TES')
    tes_included = False


try:
    csp_source = func_time_conversion(results_time['CSP_turbine dispatch'], hours_to_avg)
    csp_included = True
    if tes_included:
        csp_source = csp_source - tes_source
        sources.insert(-1, csp_source)
        pal1.insert(-1, csp_c)
        labels1.insert(-1, 'CSP')
    else:
        sources.append(csp_source)
        pal1.append(csp_c)
        labels1.append('CSP')
except: 
    print('No CSP')
    csp_included = False

try:
    if results_tech['battery capacity'] > 0:
        batt_source = func_time_conversion(results_time['battery dispatch'], hours_to_avg)
        sources.append(batt_source)
        pal1.append(batt_c)
        labels1.append('Battery')
        batt_included = True
    else:
        print('No Batteries')
        batt_included = False
except: 
    print('No Batteries')
    batt_included = False

try:
    pgp_source = func_time_conversion(results_time['from_PGP dispatch'], hours_to_avg)
    sources.append(pgp_source)
    pal1.append(pgp_c)
    labels1.append('PGP')
    pgp_included = True
except: 
    print('No PGP')
    pgp_included = False

demand_sink = np.multiply(func_time_conversion(results_time['demand potential'], hours_to_avg), -1)
sinks.append(demand_sink)
pal2.append(dem_c)
if tes_included:
    tes_sink = np.multiply(func_time_conversion(results_time['CSP_TES in dispatch'], hours_to_avg), -1) * 0.3774
    sinks.append(tes_sink)
    pal2.append(tes_c)

if batt_included:
    batt_sink = np.multiply(func_time_conversion(results_time['battery in dispatch'], hours_to_avg), -1)
    sinks.append(batt_sink)
    pal2.append(batt_c)

if pgp_included:
    pgp_sink = np.multiply(func_time_conversion(results_time['to_PGP dispatch'], hours_to_avg), -1)
    sinks.append(pgp_sink)
    pal2.append(pgp_c)

num_storage = tes_included + batt_included + pgp_included
num_cols = num_storage + 3

#=======================================================
# Plot dispatch curve
#=======================================================

date1 = datetime.datetime(input_case['year_start'], input_case['month_start'], 
                          input_case['day_start'], input_case['hour_start'] -1)
date2 = datetime.datetime(input_case['year_end'], input_case['month_end'], 
                          input_case['day_end'], input_case['hour_end'] -1)
delta = datetime.timedelta(hours=1)
quick_dates = drange(date1, date2, delta)
x = quick_dates


y1 = np.vstack(sources)
y2 = np.vstack(sinks)
labels2 = ["Demand"]

ax3 = plt.subplot2grid((6, 5), (2, 0), colspan=3, rowspan=2)
ax3.stackplot(x, y1, colors=pal1, labels=labels1)
ax3.stackplot(x, y2, colors=pal2, labels=labels2)
ax3.plot(x, demand_source, '-', color=dem_c, linewidth=1.2)
ax3.set_xlim(quick_dates[0], quick_dates[-1])
ax3.set_ylim(-2.7,2.5)
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)
ax3.xaxis.set_major_locator(AutoDateLocator())
ax3.xaxis.set_major_formatter(DateFormatter('%b'))
ax3.xaxis.set_tick_params(direction='out', which='both')
ax3.yaxis.set_tick_params(direction='out', which='both')
ax3.yaxis.set_major_locator(ticker.MultipleLocator(1))

##=====================================================
# Define sources and Sinks for Panels
##=====================================================

demand_source = results_time['demand potential']
if wind_included:
    wind_source = results_time['wind potential']
if PV_included:
    pv_source = results_time['PV potential']
if batt_included:
    batt_source = results_time['battery dispatch']
if tes_included:
    tes_source = results_time['CSP_TES dispatch'] * 0.3774
if csp_included:
    csp_source = results_time['CSP_turbine dispatch'] 
    if tes_included:
        csp_source = csp_source - tes_source
if pgp_included:
    pgp_source = results_time['from_PGP dispatch']

demand_sink = results_time['demand potential']
if batt_included:
    batt_sink = results_time['battery in dispatch']
if tes_included:
    tes_sink = results_time['CSP_TES in dispatch'] * 0.3774
if pgp_included:
    pgp_sink = results_time['to_PGP dispatch']

start_hours = []
end_hours = []
if tes_included:
    study_variable_dict_1 = {
        'window_size':      4*24,
        'data':             results_time['CSP_TES dispatch'], 
        'print_option':     0,
        'search_option':    'max'
        }
    study_output_1 = func_find_period(study_variable_dict_1)
    start_hours.append(study_output_1['left_index'])
    end_hours.append(study_output_1['right_index'])

if batt_included:
    study_variable_dict_2 = {
        'window_size':      4*24,
        'data':             results_time['battery dispatch'], 
        'print_option':     0,
        'search_option':    'max'
        }
    study_output_2 = func_find_period(study_variable_dict_2)
    start_hours.append(study_output_2['left_index'])
    end_hours.append(study_output_2['right_index'])

if pgp_included:
    study_variable_dict_3 = {
        'window_size':      4*24,
        'data':             results_time['from_PGP dispatch'], 
        'print_option':     0,
        'search_option':    'max'
        }
    study_output_3 = func_find_period(study_variable_dict_3)
    start_hours.append(study_output_3['left_index'])
    end_hours.append(study_output_3['right_index'])

##=================================================
# Loop to plot panels of max storage dispatch
##=================================================

for i in range(num_storage):
    start_hour = start_hours[i]
    end_hour = end_hours[i]

    delta1 = datetime.timedelta(hours=(start_hour-6)) # -6 converts UTC to CST
    delta2 = datetime.timedelta(hours=(end_hour-6))
    
    date1 = datetime.datetime(input_case['year_start'], 1, 1, 0) + delta1
    date2 = datetime.datetime(input_case['year_start'], 1, 1, 0) + delta2

    delta = datetime.timedelta(hours=1)
    dates = drange(date1, date2, delta)

    x = dates
    
    sources = []
    demand_source1 = demand_source[start_hour:end_hour]
    
    demand_sink1 = np.multiply(demand_sink[start_hour:end_hour],-1)
    sinks = [demand_sink1]
    
    
    if wind_included:
        wind_source1 = wind_source[start_hour:end_hour]
        sources.append(wind_source1)
    if PV_included:
        pv_source1 = pv_source[start_hour:end_hour]
        sources.append(pv_source1)
    if csp_included:
        csp_source1 = csp_source[start_hour:end_hour]
        sources.append(csp_source1)
    if tes_included:
        tes_source1 = tes_source[start_hour:end_hour]
        sources.append(tes_source1)
        tes_sink1 = np.multiply(tes_sink[start_hour:end_hour],-1)
        sinks.append(tes_sink1)
    if batt_included:
        batt_source1 = batt_source[start_hour:end_hour]
        sources.append(batt_source1)
        batt_sink1 = np.multiply(batt_sink[start_hour:end_hour],-1)
        sinks.append(batt_sink1)
    if pgp_included:
        pgp_source1 = pgp_source[start_hour:end_hour]
        sources.append(pgp_source1)
        pgp_sink1 = np.multiply(pgp_sink[start_hour:end_hour],-1)
        sinks.append(pgp_sink1)

    y1 = np.vstack(sources)
    y2 = np.vstack(sinks)
    
    ax = plt.subplot2grid((6, 5), (2, 3+i), colspan=1, rowspan=2)
    ax.stackplot(x, y1, colors=pal1, labels=labels1)
    ax.stackplot(x, y2, colors=pal2, labels=labels2)
    ax.plot(x, demand_source1, '-', color=dem_c, linewidth=1.2)

    ax.set_xlim(dates[0], dates[-1])
    ax.set_ylim(-2.7,2.5)
    
    ax.xaxis.set_major_locator(HourLocator(byhour=range(24),interval=24))
    ax.xaxis.set_major_formatter(DateFormatter('%b %d')) #This is CST!!! 7am
    plt.setp(ax.get_yticklabels(), visible=False)
    ax.yaxis.set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
    plt.xticks(rotation=30, ha='right')
    ax.xaxis.set_tick_params(direction='out', which='both')
    ax.yaxis.set_tick_params(direction='out', which='both')
 
ax.legend(bbox_to_anchor=(1.02, 1.02),frameon=False)
chartBox = ax.get_position()
ax.set_position([chartBox.x0, chartBox.y0, chartBox.width*1, chartBox.height])

##===========================================
#Read in pickle file
##===========================================

with open('C:/Users/Kathleen/Desktop/Temp/SensitivityCSP/CSP0.125x_TES1.0x_20210306-001129.pickle', 'rb') as handle:
            [[input_case,  input_tech,  input_time],
             [results_case, results_tech,  results_time]] = pickle.load(handle)

##===========================================================================================================
# Define Sources and Sinks
##============================================================================================================

# 5-day averaging
hours_to_avg = 5*24
sources = []
sinks = []
pal1 = []
pal2 = []
labels1 = []

demand_source = func_time_conversion(results_time['demand potential'], hours_to_avg)

try:
    wind_source = func_time_conversion(results_time['wind potential'], hours_to_avg)
    sources.append(wind_source)
    pal1.append(wind_c)
    labels1.append('Wind')
    wind_included = True
except: 
    print('No wind')
    wind_included = False

try:
    PV_source = func_time_conversion(results_time['PV potential'], hours_to_avg)
    sources.append(PV_source)
    pal1.append(PV_c)
    labels1.append('PV')
    PV_included = True
except: 
    print('No PV')
    PV_included = False

try:
    if results_tech['CSP_TES capacity'] > 0:
        tes_source = func_time_conversion(results_time['CSP_TES dispatch'], hours_to_avg) * 0.3774
        sources.append(tes_source)
        pal1.append(tes_c)
        labels1.append('TES')
        tes_included = True
    else:
        print('No TES')
        tes_included = False
except: 
    print('No TES')
    tes_included = False


try:
    csp_source = func_time_conversion(results_time['CSP_turbine dispatch'], hours_to_avg)
    csp_included = True
    if tes_included:
        csp_source = csp_source - tes_source
        sources.insert(-1, csp_source)
        pal1.insert(-1, csp_c)
        labels1.insert(-1, 'CSP')
    else:
        sources.append(csp_source)
        pal1.append(csp_c)
        labels1.append('CSP')
except: 
    print('No CSP')
    csp_included = False

try:
    if results_tech['battery capacity'] > 0:
        batt_source = func_time_conversion(results_time['battery dispatch'], hours_to_avg)
        sources.append(batt_source)
        pal1.append(batt_c)
        labels1.append('Battery')
        batt_included = True
    else:
        print('No Batteries')
        batt_included = False
except: 
    print('No Batteries')
    batt_included = False

try:
    pgp_source = func_time_conversion(results_time['from_PGP dispatch'], hours_to_avg)
    sources.append(pgp_source)
    pal1.append(pgp_c)
    labels1.append('PGP')
    pgp_included = True
except: 
    print('No PGP')
    pgp_included = False

demand_sink = np.multiply(func_time_conversion(results_time['demand potential'], hours_to_avg), -1)
sinks.append(demand_sink)
pal2.append(dem_c)
if tes_included:
    tes_sink = np.multiply(func_time_conversion(results_time['CSP_TES in dispatch'], hours_to_avg), -1) * 0.3774
    sinks.append(tes_sink)
    pal2.append(tes_c)

if batt_included:
    batt_sink = np.multiply(func_time_conversion(results_time['battery in dispatch'], hours_to_avg), -1)
    sinks.append(batt_sink)
    pal2.append(batt_c)

if pgp_included:
    pgp_sink = np.multiply(func_time_conversion(results_time['to_PGP dispatch'], hours_to_avg), -1)
    sinks.append(pgp_sink)
    pal2.append(pgp_c)

num_storage = tes_included + batt_included + pgp_included
num_cols = num_storage + 3

#=======================================================
# Plot dispatch curve
#=======================================================

date1 = datetime.datetime(input_case['year_start'], input_case['month_start'], 
                          input_case['day_start'], input_case['hour_start'] -1)
date2 = datetime.datetime(input_case['year_end'], input_case['month_end'], 
                          input_case['day_end'], input_case['hour_end'] -1)
delta = datetime.timedelta(hours=1)
quick_dates = drange(date1, date2, delta)
x = quick_dates


y1 = np.vstack(sources)
y2 = np.vstack(sinks)
labels2 = ["Demand"]

ax3 = plt.subplot2grid((6, 5), (4, 0), colspan=3, rowspan=2)
ax3.stackplot(x, y1, colors=pal1, labels=labels1)
ax3.stackplot(x, y2, colors=pal2, labels=labels2)
ax3.plot(x, demand_source, '-', color=dem_c, linewidth=1.2)
ax3.set_xlim(quick_dates[0], quick_dates[-1])
ax3.set_ylim(-2.7,2.5)
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)
ax3.xaxis.set_major_locator(AutoDateLocator())
ax3.xaxis.set_major_formatter(DateFormatter('%b'))
ax3.xaxis.set_tick_params(direction='out', which='both')
ax3.yaxis.set_tick_params(direction='out', which='both')
ax3.yaxis.set_major_locator(ticker.MultipleLocator(1))

##=====================================================
# Define sources and Sinks for Panels
##=====================================================

demand_source = results_time['demand potential']
if wind_included:
    wind_source = results_time['wind potential']
if PV_included:
    pv_source = results_time['PV potential']
if batt_included:
    batt_source = results_time['battery dispatch']
if tes_included:
    tes_source = results_time['CSP_TES dispatch'] * 0.3774
if csp_included:
    csp_source = results_time['CSP_turbine dispatch'] 
    if tes_included:
        csp_source = csp_source - tes_source
if pgp_included:
    pgp_source = results_time['from_PGP dispatch']

demand_sink = results_time['demand potential']
if batt_included:
    batt_sink = results_time['battery in dispatch']
if tes_included:
    tes_sink = results_time['CSP_TES in dispatch'] * 0.3774
if pgp_included:
    pgp_sink = results_time['to_PGP dispatch']

start_hours = []
end_hours = []
if tes_included:
    study_variable_dict_1 = {
        'window_size':      4*24,
        'data':             results_time['CSP_TES dispatch'], 
        'print_option':     0,
        'search_option':    'max'
        }
    study_output_1 = func_find_period(study_variable_dict_1)
    start_hours.append(study_output_1['left_index'])
    end_hours.append(study_output_1['right_index'])

if batt_included:
    study_variable_dict_2 = {
        'window_size':      4*24,
        'data':             results_time['battery dispatch'], 
        'print_option':     0,
        'search_option':    'max'
        }
    study_output_2 = func_find_period(study_variable_dict_2)
    start_hours.append(study_output_2['left_index'])
    end_hours.append(study_output_2['right_index'])

if pgp_included:
    study_variable_dict_3 = {
        'window_size':      4*24,
        'data':             results_time['from_PGP dispatch'], 
        'print_option':     0,
        'search_option':    'max'
        }
    study_output_3 = func_find_period(study_variable_dict_3)
    start_hours.append(study_output_3['left_index'])
    end_hours.append(study_output_3['right_index'])

##=================================================
# Loop to plot panels of max storage dispatch
##=================================================

for i in range(num_storage):
    start_hour = start_hours[i]
    end_hour = end_hours[i]

    delta1 = datetime.timedelta(hours=(start_hour-6)) # -6 converts UTC to CST
    delta2 = datetime.timedelta(hours=(end_hour-6))
    
    date1 = datetime.datetime(input_case['year_start'], 1, 1, 0) + delta1
    date2 = datetime.datetime(input_case['year_start'], 1, 1, 0) + delta2

    delta = datetime.timedelta(hours=1)
    dates = drange(date1, date2, delta)

    x = dates
    
    sources = []
    demand_source1 = demand_source[start_hour:end_hour]
    
    demand_sink1 = np.multiply(demand_sink[start_hour:end_hour],-1)
    sinks = [demand_sink1]
    
    
    if wind_included:
        wind_source1 = wind_source[start_hour:end_hour]
        sources.append(wind_source1)
    if PV_included:
        pv_source1 = pv_source[start_hour:end_hour]
        sources.append(pv_source1)
    if csp_included:
        csp_source1 = csp_source[start_hour:end_hour]
        sources.append(csp_source1)
    if tes_included:
        tes_source1 = tes_source[start_hour:end_hour]
        sources.append(tes_source1)
        tes_sink1 = np.multiply(tes_sink[start_hour:end_hour],-1)
        sinks.append(tes_sink1)
    if batt_included:
        batt_source1 = batt_source[start_hour:end_hour]
        sources.append(batt_source1)
        batt_sink1 = np.multiply(batt_sink[start_hour:end_hour],-1)
        sinks.append(batt_sink1)
    if pgp_included:
        pgp_source1 = pgp_source[start_hour:end_hour]
        sources.append(pgp_source1)
        pgp_sink1 = np.multiply(pgp_sink[start_hour:end_hour],-1)
        sinks.append(pgp_sink1)

    y1 = np.vstack(sources)
    y2 = np.vstack(sinks)
    
    ax = plt.subplot2grid((6, 5), (4, 3+i), colspan=1, rowspan=2)
    ax.stackplot(x, y1, colors=pal1, labels=labels1)
    ax.stackplot(x, y2, colors=pal2, labels=labels2)
    ax.plot(x, demand_source1, '-', color=dem_c, linewidth=1.2)

    ax.set_xlim(dates[0], dates[-1])
    ax.set_ylim(-2.7,2.5)
    
    ax.xaxis.set_major_locator(HourLocator(byhour=range(24),interval=24))
    ax.xaxis.set_major_formatter(DateFormatter('%b %d')) #This is CST!!! 7am
    plt.setp(ax.get_yticklabels(), visible=False)
    ax.yaxis.set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
    plt.xticks(rotation=30, ha='right')
    ax.xaxis.set_tick_params(direction='out', which='both')
    ax.yaxis.set_tick_params(direction='out', which='both')
 
ax.legend(bbox_to_anchor=(1.02, 1.02),frameon=False)
chartBox = ax.get_position()
ax.set_position([chartBox.x0, chartBox.y0, chartBox.width*1, chartBox.height])

fig.text(-.01, 0.5, 'Electricty sources and sinks (kW)', va='center', rotation='vertical', size=20 )
fig.text(0.45,0.99,'0.5x CSP, 1.0x TES',size='x-large')
fig.text(0.44,0.65,'0.25x CSP, 1.0x TES',size='x-large')
fig.text(0.44,0.32,'0.125x CSP, 1.0x TES',size='x-large')

fig.text(.05, 0.97, 'a)', size='x-large')
fig.text(.58, 0.97, 'b)', size='x-large')
fig.text(.75, 0.97, 'c)', size='x-large')
fig.text(.05, 0.63, 'd)', size='x-large')
fig.text(.58, 0.63, 'e)', size='x-large')
fig.text(.75, 0.63, 'f)', size='x-large')
fig.text(.05, 0.30, 'g)', size='x-large')
fig.text(.58, 0.30, 'h)', size='x-large')
fig.text(.75, 0.30, 'i)', size='x-large')

plt.tight_layout(True)
plt.savefig('PaperFigures/SI/figure_s13_csp_dispatches.jpg', dpi=300, bbox_inches='tight')
plt.show()