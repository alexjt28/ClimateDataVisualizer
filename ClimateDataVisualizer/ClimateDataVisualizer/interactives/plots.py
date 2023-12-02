#######################################################################################################
#
# Functions for generating standalone plots
#
#######################################################################################################

# Use this to read in packages from other directories ---------
import sys, os 
sys.path.append(os.path.dirname(os.getcwd())) # one dir back
#--------------------------------------------------------------
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Rectangle
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import cartopy, cartopy.mpl.geoaxes, cartopy.io.img_tiles
import xarray as xr
import geocat.viz.util as gv
import urllib, json, cmaps, math
from ClimateDataVisualizer.dataquery import NOAA_ACIS_stnmeta as stnmeta
from ClimateDataVisualizer.dataquery import NOAA_ACIS_stndata as stndata
from ClimateDataVisualizer.processing.bbox_dy import bbox_avg_dy
from ClimateDataVisualizer.processing.bbox_my import bbox_avg_my, bbox_max_my, bbox_min_my
from ClimateDataVisualizer.inset_axes.inset_axes import inset_map, inset_timeseries
import warnings

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
# ANNUAL CYCLE PLOTS
#
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#================================================================================================================
# annualcycle_tmax_plot
#================================================================================================================

def annualcycle_tmax_plot(var,meta,location_name,nlat,slat,wlon,elon,syr,eyr,num_stn,iyr,minbuff,maxbuff,
                          majtick,mintick,incl_hist,incl_year,incl_info,incl_map,img_tile,lbl_buff,ext_buff):

    ############################################################################################################# 
    # Average data by day and year 
    ############################################################################################################# 

    # List of leap years from 1800 to 2100
    leapyears = [1800 + i * 4 for i in range((2100 - 1800) // 4 + 1)]
    isleap = False if iyr not in leapyears else True

    # Apply NaN filter to the dataframe based on minimum number of stations collecting data on a given day
    var_filt = var.copy()
    var_filt.loc[var_filt.iloc[:,1:].count(axis=1) < num_stn, var_filt.columns[1:]] = np.nan

    # Create dataframe of every day of the every year
    var_dy = bbox_avg_dy(var_filt,leap=isleap)

    ############################################################################################################# 
    # Auto-select dates based on parameters 
    ############################################################################################################# 

    # If earliest, take earliest year with data
    if syr == 'earliest':
        try:
           syr = int(np.min(var_dy.dropna(axis=1,how='all').columns[2:]))
        except:
           print('ERROR: There are no years with this many stations collecting data simultaneously.')

    # If latest, take latest year (but not this year) with fewer than 365 NaN values   
    if eyr == 'latest':
        for c in range(2,len(var_dy)+1):
            if var_dy[var_dy.columns[-c]].isna().sum() < 365:
                eyr = int(var_dy.columns[-c])
                break

    # Define back-end plotting year based on whether current year is a leap year or not
    plt_yr = 2020 if iyr in leapyears else 2022

    ############################################################################################################# 
    # Define figure 
    ############################################################################################################# 

    fig, ax = plt.subplots(figsize=[8,4],dpi=300)

    # Define x-axis time interval
    xtime = pd.date_range(start=str(plt_yr)+'-01-01', end=str(plt_yr)+'-12-31', freq='D') 

    ############################################################################################################# 
    # PLOT HISTORICAL DATA 
    ############################################################################################################# 

    if incl_hist == True:

        # MEAN
        var_avg = np.nanmean(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                          var_dy.columns.get_loc(str(eyr))+1],axis=1)

        # 5th and 95th percentiles
        var_05 = np.nanpercentile(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                                var_dy.columns.get_loc(str(eyr))+1],5,axis=1)
        var_95 = np.nanpercentile(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                                var_dy.columns.get_loc(str(eyr))+1],95,axis=1)

        # Min and Max
        var_min = np.nanmin(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                                var_dy.columns.get_loc(str(eyr))+1],axis=1)
        var_max = np.nanmax(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                                var_dy.columns.get_loc(str(eyr))+1],axis=1)

        # Plot historical data
        ax.plot(xtime,var_avg,'-',c='k',lw=1.5,alpha=0.5,zorder=100)
        ax.fill_between(xtime,var_05,var_95,color='tab:red',alpha=0.2,edgecolor=None,zorder=1)
        ax.fill_between(xtime,var_max,var_95,color='tab:red',alpha=0.05,edgecolor=None,zorder=1)
        ax.fill_between(xtime,var_05,var_min,color='tab:red',alpha=0.05,edgecolor=None,zorder=1)
        ax.plot(xtime,var_max,':',c='tab:red',lw=0.25,alpha=0.75,zorder=10)
        ax.plot(xtime,var_min,':',c='tab:red',lw=0.25,alpha=0.75,zorder=10)

        # Text indicators
        leg_hist = ax.legend([mpl.patches.Patch(facecolor='tab:red', alpha=0.2, edgecolor=None)],
                             (r' $\bf{HISTORICAL \ DATA \ PERIOD :}$'+' {}-{}'.format(syr,eyr),''),
                             fontsize=8,framealpha=0.,bbox_to_anchor=(0,0,0.59,0.08))
        ax.add_artist(leg_hist)

        # How to read historical data
        leg = fig.add_axes([0.5, 0.2, 0.1, 0.16])
        leg.set_xticklabels([]), leg.set_xticks([]), leg.set_yticklabels([]), leg.set_yticks([]);
        randomness,mult,last,leg_var = 0.5+0.5*np.random.rand(10),[10,5,0.01,-5,-10],[9,5,0,-5,-9],np.zeros((5,10))
        for i in range(5):
            leg_var[i,:],leg_var[i,-1] = mult[i]*np.ones(10)*randomness, last[i]
        leg.plot(np.arange(10),leg_var[2,:],'-',c='k',lw=1.5,alpha=0.5,zorder=100)
        leg.fill_between(np.arange(10),leg_var[3,:],leg_var[1,:],color='tab:red',alpha=0.2,edgecolor=None,zorder=1)
        leg.fill_between(np.arange(10),leg_var[4,:],leg_var[3,:],color='tab:red',alpha=0.05,edgecolor=None,zorder=1)
        leg.fill_between(np.arange(10),leg_var[1,:],leg_var[0,:],color='tab:red',alpha=0.05,edgecolor=None,zorder=1)
        leg.plot(np.arange(10),leg_var[0,:],':',c='tab:red',lw=0.25,alpha=0.75,zorder=10)
        leg.plot(np.arange(10),leg_var[4,:],':',c='tab:red',lw=0.25,alpha=0.75,zorder=10)
        tags = ['MAX','95$^{th}$','MEAN','5$^{th}$','MIN']
        for i in range(5):
            leg.text(10,leg_var[i,:][-1],tags[i],fontsize=6,alpha=0.5,weight='bold',ha='left',va='center')
        leg.set_title('How to read\nhistorical data',loc='center',fontsize=8,weight='bold',alpha=0.6);

    ############################################################################################################# 
    # PLOT INDIVIDUAL YEAR 
    ############################################################################################################# 

    if incl_year == True:
        ax.plot(pd.date_range(start=str(plt_yr)+'-01-01',end=str(plt_yr)+'-12-31',freq='D'),
                var_dy[str(iyr)],'-',c='r',lw=1,zorder=1000)
        leg_year = ax.legend([mpl.lines.Line2D([0],[0],c='tab:red',lw=1.5)],(str(iyr),''),
                             framealpha=0.,bbox_to_anchor=(0,0,0.13,0.08),
                             prop={'weight': 'bold', 'size': 8})

    ############################################################################################################# 
    # Features to include? Can toggle on and off in parameters
    ############################################################################################################# 

    if incl_info == True:
        larger = (var_dy[str(iyr)] > var_avg).sum()
        smaller = (var_dy[str(iyr)] < var_avg).sum()
        ax.text(0.18,0.89,r'$\bf{'+str(iyr)+':}$ '+'\n'+r'$\bf{'+str(larger)+'}$'+' days above '+
                str(syr)+'-'+str(eyr)+' mean \n'+r'$\bf{'+str(smaller)+'}$'+' days below '+
                str(syr)+'-'+str(eyr)+' mean',ha='center',va='center',fontsize=8,transform=ax.transAxes)

    if incl_map == True:
        inset_map(ax=ax,meta=meta,var=var,width=0.7,height=0.8,markercolor='k',incl_year=incl_year,iyr=iyr,
                  iyr_col='tab:red',slat=slat,nlat=nlat,wlon=wlon,elon=elon,bbox_to_anchor=(0,0,1,0.97),
                  lbl_buff=lbl_buff,proj=cartopy.crs.PlateCarree(),ext_buff=ext_buff,img_tile=img_tile)

    ############################################################################################################# 
    # Title and text
    ############################################################################################################# 

    ax.text(0.75,0.02,r'$\bf{IMAGE:}$ Alex Thompson (@ajtclimate)'+'\n'+r'$\bf{DATA:}$'+
                   ' NOAA ACIS (http://data.rcc-acis.org)',ha='left',fontsize=5,transform=ax.transAxes)
    ax.set_title('Daily High Temperature in '+location_name,loc='center',fontsize=14,pad=5,
                 weight='bold');

    ############################################################################################################# 
    # Axes specs 
    ############################################################################################################# 

    ax.set_xticks([str(plt_yr)+'-'+'{:02}'.format(month) for month in range(1, 13)])
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
    ax.set_ylabel('Region Mean (°F)')
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(majtick))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(mintick))
    ax.grid(alpha=0.05)
    ax.set_xlim([pd.to_datetime(str(plt_yr-1)+'-12-30'),pd.to_datetime(str(plt_yr+1)+'-01-01')])
    ax.set_ylim([np.nanmin(var_min)-minbuff,np.nanmax(var_max)+maxbuff]);
    ax.spines[['right','top']].set_visible(False)

    return fig, var_dy, var_max, var_95, var_avg, var_05, var_min

#================================================================================================================
# annualcycle_tmin_plot
#================================================================================================================

def annualcycle_tmin_plot(var,meta,location_name,nlat,slat,wlon,elon,syr,eyr,num_stn,iyr,minbuff,maxbuff,
                          majtick,mintick,incl_hist,incl_year,incl_info,incl_map,img_tile,lbl_buff,ext_buff):

    ############################################################################################################# 
    # Average data by day and year 
    ############################################################################################################# 

    # List of leap years from 1800 to 2100
    leapyears = [1800 + i * 4 for i in range((2100 - 1800) // 4 + 1)]
    isleap = False if iyr not in leapyears else True

    # Apply NaN filter to the dataframe based on minimum number of stations collecting data on a given day
    var_filt = var.copy()
    var_filt.loc[var_filt.iloc[:,1:].count(axis=1) < num_stn, var_filt.columns[1:]] = np.nan

    # Create dataframe of every day of the every year
    var_dy = bbox_avg_dy(var_filt,leap=isleap)

    ############################################################################################################# 
    # Auto-select dates based on parameters 
    ############################################################################################################# 

    # If earliest, take earliest year with data
    if syr == 'earliest':
        try:
           syr = int(np.min(var_dy.dropna(axis=1,how='all').columns[2:]))
        except:
           print('ERROR: There are no years with this many stations collecting data simultaneously.')

    # If latest, take latest year (but not this year) with fewer than 365 NaN values   
    if eyr == 'latest':
        for c in range(2,len(var_dy)+1):
            if var_dy[var_dy.columns[-c]].isna().sum() < 365:
                eyr = int(var_dy.columns[-c])
                break

    # Define back-end plotting year based on whether current year is a leap year or not
    plt_yr = 2020 if iyr in leapyears else 2022

    ############################################################################################################# 
    # Define figure 
    ############################################################################################################# 

    fig, ax = plt.subplots(figsize=[8,4],dpi=300)

    # Define x-axis time interval
    xtime = pd.date_range(start=str(plt_yr)+'-01-01', end=str(plt_yr)+'-12-31', freq='D')

    ############################################################################################################# 
    # PLOT HISTORICAL DATA 
    ############################################################################################################# 

    if incl_hist == True:

        # MEAN
        var_avg = np.nanmean(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                          var_dy.columns.get_loc(str(eyr))+1],axis=1)

        # 5th and 95th percentiles
        var_05 = np.nanpercentile(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                                var_dy.columns.get_loc(str(eyr))+1],5,axis=1)
        var_95 = np.nanpercentile(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                                var_dy.columns.get_loc(str(eyr))+1],95,axis=1)

        # Min and Max
        var_min = np.nanmin(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                                var_dy.columns.get_loc(str(eyr))+1],axis=1)
        var_max = np.nanmax(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                                var_dy.columns.get_loc(str(eyr))+1],axis=1)

        # Plot historical data
        ax.plot(xtime,var_avg,'-',c='k',lw=1.5,alpha=0.5,zorder=100)
        ax.fill_between(xtime,var_05,var_95,color='tab:blue',alpha=0.2,edgecolor=None,zorder=1)
        ax.fill_between(xtime,var_max,var_95,color='tab:blue',alpha=0.05,edgecolor=None,zorder=1)
        ax.fill_between(xtime,var_05,var_min,color='tab:blue',alpha=0.05,edgecolor=None,zorder=1)
        ax.plot(xtime,var_max,':',c='tab:blue',lw=0.25,alpha=0.75,zorder=10)
        ax.plot(xtime,var_min,':',c='tab:blue',lw=0.25,alpha=0.75,zorder=10)

        # Text indicators
        leg_hist = ax.legend([mpl.patches.Patch(facecolor='tab:blue', alpha=0.2, edgecolor=None)],
                             (r' $\bf{HISTORICAL \ DATA \ PERIOD :}$'+' {}-{}'.format(syr,eyr),''),
                             fontsize=8,framealpha=0.,bbox_to_anchor=(0,0,0.59,0.08))
        ax.add_artist(leg_hist)

        # How to read historical data
        leg = fig.add_axes([0.5, 0.2, 0.1, 0.16])
        leg.set_xticklabels([]), leg.set_xticks([]), leg.set_yticklabels([]), leg.set_yticks([]);
        randomness,mult,last,leg_var = 0.5+0.5*np.random.rand(10),[10,5,0.01,-5,-10],[9,5,0,-5,-9],np.zeros((5,10))
        for i in range(5):
            leg_var[i,:],leg_var[i,-1] = mult[i]*np.ones(10)*randomness, last[i]
        leg.plot(np.arange(10),leg_var[2,:],'-',c='k',lw=1.5,alpha=0.5,zorder=100)
        leg.fill_between(np.arange(10),leg_var[3,:],leg_var[1,:],color='tab:blue',alpha=0.2,edgecolor=None,zorder=1)
        leg.fill_between(np.arange(10),leg_var[4,:],leg_var[3,:],color='tab:blue',alpha=0.05,edgecolor=None,zorder=1)
        leg.fill_between(np.arange(10),leg_var[1,:],leg_var[0,:],color='tab:blue',alpha=0.05,edgecolor=None,zorder=1)
        leg.plot(np.arange(10),leg_var[0,:],':',c='tab:blue',lw=0.25,alpha=0.75,zorder=10)
        leg.plot(np.arange(10),leg_var[4,:],':',c='tab:blue',lw=0.25,alpha=0.75,zorder=10)
        tags = ['MAX','95$^{th}$','MEAN','5$^{th}$','MIN']
        for i in range(5):
            leg.text(10,leg_var[i,:][-1],tags[i],fontsize=6,alpha=0.5,weight='bold',ha='left',va='center')
        leg.set_title('How to read\nhistorical data',loc='center',fontsize=8,weight='bold',alpha=0.6);

    ############################################################################################################# 
    # PLOT INDIVIDUAL YEAR 
    ############################################################################################################# 

    if incl_year == True:
        ax.plot(pd.date_range(start=str(plt_yr)+'-01-01',end=str(plt_yr)+'-12-31',freq='D'),
                var_dy[str(iyr)],'-',c='b',lw=1,zorder=1000)
        leg_year = ax.legend([mpl.lines.Line2D([0],[0],c='tab:blue',lw=1.5)],(str(iyr),''),
                             framealpha=0.,bbox_to_anchor=(0,0,0.13,0.08),
                             prop={'weight': 'bold', 'size': 8})

    ############################################################################################################# 
    # Features to include? Can toggle on and off in parameters
    ############################################################################################################# 

    if incl_info == True:
        larger = (var_dy[str(iyr)] > var_avg).sum()
        smaller = (var_dy[str(iyr)] < var_avg).sum()
        ax.text(0.18,0.89,r'$\bf{'+str(iyr)+':}$ '+'\n'+r'$\bf{'+str(larger)+'}$'+' days above '+
                str(syr)+'-'+str(eyr)+' mean \n'+r'$\bf{'+str(smaller)+'}$'+' days below '+
                str(syr)+'-'+str(eyr)+' mean',ha='center',va='center',fontsize=8,transform=ax.transAxes)

    if incl_map == True:
        inset_map(ax=ax,meta=meta,var=var,width=0.7,height=0.8,markercolor='k',incl_year=incl_year,iyr=iyr,
                  iyr_col='tab:red',slat=slat,nlat=nlat,wlon=wlon,elon=elon,bbox_to_anchor=(0,0,1,0.97),
                  lbl_buff=lbl_buff,proj=cartopy.crs.PlateCarree(),ext_buff=ext_buff,img_tile=img_tile)

    ############################################################################################################# 
    # Title and text
    ############################################################################################################# 

    ax.text(0.75,0.02,r'$\bf{IMAGE:}$ Alex Thompson (@ajtclimate)'+'\n'+r'$\bf{DATA:}$'+
                   ' NOAA ACIS (http://data.rcc-acis.org)',ha='left',fontsize=5,transform=ax.transAxes)
    ax.set_title('Daily Low Temperature in '+location_name,loc='center',fontsize=14,pad=5,
                 weight='bold');

    ############################################################################################################# 
    # Axes specs 
    ############################################################################################################# 

    ax.set_xticks([str(plt_yr)+'-'+'{:02}'.format(month) for month in range(1, 13)])
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
    ax.set_ylabel('Region Mean (°F)')
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(majtick))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(mintick))
    ax.grid(alpha=0.05)
    ax.set_xlim([pd.to_datetime(str(plt_yr-1)+'-12-30'),pd.to_datetime(str(plt_yr+1)+'-01-01')])
    ax.set_ylim([np.nanmin(var_min)-minbuff,np.nanmax(var_max)+maxbuff]);
    ax.spines[['right','top']].set_visible(False)

    return fig, var_dy, var_max, var_95, var_avg, var_05, var_min

#================================================================================================================
# annualcycle_rain_plot
#================================================================================================================

def annualcycle_pcpn_plot(var,meta,location_name,nlat,slat,wlon,elon,rain_type,nday,syr,eyr,num_stn,iyr,
              minbuff,maxbuff,majtick,mintick,incl_hist,incl_year,incl_map,img_tile,lbl_buff,ext_buff):
                         
    ###################################################################################################
    # Average data by day and year 
    ###################################################################################################

    # List of leap years from 1800 to 2100
    leapyears = [1800 + i * 4 for i in range((2100 - 1800) // 4 + 1)]
    isleap = False if iyr not in leapyears else True

    # Apply NaN filter to the dataframe based on minimum number of stations collecting data on a given day
    var_filt = var.copy()
    var_filt.loc[var_filt.iloc[:,1:].count(axis=1) < num_stn, var_filt.columns[1:]] = np.nan

    # Average by day and year
    if rain_type == 'all' :
        var_dy = bbox_avg_dy(var_filt,leap=isleap)
    elif rain_type == 'rain' or rain_type == 'wetNday':
        # Set 0.'s and trace values to NaN (need to remove 'Date' column to do this)
        var_filt_raindays = var_filt[[col for col in var_filt.columns if col != 'Date']].applymap(
                                             lambda x: x if x > 0.00001 else np.nan)
        # Add 'Date' column back 
        var_filt_raindays['Date'] = var_filt['Date']
        var_dy = bbox_avg_dy(var_filt_raindays,leap=isleap)

    ###################################################################################################
    # Auto-select dates based on parameters 
    ###################################################################################################

    # If earliest, take earliest year with data
    if syr == 'earliest':
        try:
           syr = int(np.min(var_dy.dropna(axis=1,how='all').columns[2:]))
        except:
           print('ERROR: There are no years with this many stations collecting data simultaneously.')

    # If latest, take latest year (but not this year) with fewer than 365 NaN values   
    if eyr == 'latest':
        for c in range(2,len(var_dy)+1):
            if var_dy[var_dy.columns[-c]].isna().sum() < 365:
                eyr = int(var_dy.columns[-c])
                break

    # Define back-end plotting year based on whether current year is a leap year or not
    plt_yr = 2020 if iyr in leapyears else 2022    

    ###################################################################################################
    # Define figure 
    ###################################################################################################

    fig, ax = plt.subplots(figsize=[8,4],dpi=300)

    # Define x-axis time interval
    xtime = pd.date_range(start=str(plt_yr)+'-01-01', end=str(plt_yr)+'-12-31', freq='D') 

    ############################################################################################################# 
    # PLOT HISTORICAL DATA 
    ############################################################################################################# 

    if incl_hist == True:

        if rain_type == 'all' or rain_type == 'rain':

            # MEAN
            var_avg = np.nanmean(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                              var_dy.columns.get_loc(str(eyr))+1],axis=1)

            # 95th percentile
            var_95 = np.nanpercentile(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                                    var_dy.columns.get_loc(str(eyr))+1],95,axis=1)

            # Max
            var_max = np.nanmax(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                                    var_dy.columns.get_loc(str(eyr))+1],axis=1)

            # Plot historical data
            ax.plot(xtime,var_avg,'-',c='k',lw=1.5,alpha=0.5,zorder=100)
            ax.fill_between(xtime,np.zeros(len(xtime)),var_95,color='tab:blue',alpha=0.2,edgecolor=None,zorder=1)
            ax.fill_between(xtime,var_max,var_95,color='tab:blue',alpha=0.05,edgecolor=None,zorder=1)
            ax.plot(xtime,var_max,':',c='tab:blue',lw=0.25,alpha=0.75,zorder=10)

            # How to read historical data
            leg = fig.add_axes([0.145, 0.54, 0.1, 0.12])
            leg.set_xticklabels([]), leg.set_xticks([]), leg.set_yticklabels([]), leg.set_yticks([]);
            randomness,mult,last,leg_var = 0.5+0.5*np.random.rand(10),[10,5,1],[9,5,1],np.zeros((3,10))
            for i in range(3):
                leg_var[i,:],leg_var[i,-1] = mult[i]*np.ones(10)*randomness, last[i]
            leg.plot(np.arange(10),leg_var[2,:],'-',c='k',lw=1.5,alpha=0.5,zorder=100)
            leg.fill_between(np.arange(10),np.zeros(10),leg_var[1,:],color='tab:blue',alpha=0.2,edgecolor=None,
                             zorder=1)
            leg.fill_between(np.arange(10),leg_var[1,:],leg_var[0,:],color='tab:blue',alpha=0.05,edgecolor=None,
                             zorder=1)
            leg.plot(np.arange(10),leg_var[0,:],':',c='tab:blue',lw=0.25,alpha=0.75,zorder=10)
            tags = ['MAX','95$^{th}$','MEAN']
            for i in range(3):
                leg.text(10,leg_var[i,:][-1],tags[i],fontsize=6,alpha=0.5,weight='bold',ha='left',va='center')
            leg.set_title('How to read\nhistorical data',loc='center',fontsize=8,weight='bold',alpha=0.6);

        elif rain_type == 'wetNday':

            # Find wettest N days in period and extract max/min for plotting
            #var_nday = var_dy.iloc[:, 2:].apply(lambda row: row.sort_values(ascending=False)[:nday].values,
            #                                    axis=1)
            var_nday = var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):var_dy.columns.get_loc(str(eyr))+1
                               ].apply(lambda row: row.sort_values(ascending=False)[:nday].values,axis=1)
            var_max = np.array([np.nanmax(d) for d in var_nday])
            var_min = np.array([np.nanmin(d) for d in var_nday])

            # Plot historical data
            ax.fill_between(xtime,var_max,var_min,color='tab:blue',alpha=0.2,edgecolor=None,zorder=1)
            ax.plot(xtime,var_max,':',c='tab:blue',lw=0.25,alpha=0.75,zorder=10)
            ax.plot(xtime,var_min,':',c='tab:blue',lw=0.25,alpha=0.75,zorder=10)

            # How to read historical data
            leg = fig.add_axes([0.145, 0.54, 0.1, 0.12])
            leg.set_xticklabels([]), leg.set_xticks([]), leg.set_yticklabels([]), leg.set_yticks([]);
            randomness,mult,last,leg_var = 0.5+0.5*np.random.rand(10),[8,2],[6,3],np.zeros((2,10))
            for i in range(2):
                leg_var[i,:],leg_var[i,-1] = mult[i]*np.ones(10)*randomness, last[i]
            leg.fill_between(np.arange(10),leg_var[0,:],leg_var[1,:],color='tab:blue',alpha=0.2,edgecolor=None,
                             zorder=1)
            leg.plot(np.arange(10),leg_var[0,:],':',c='tab:blue',lw=0.25,alpha=0.75,zorder=10)
            leg.plot(np.arange(10),leg_var[1,:],':',c='tab:blue',lw=0.25,alpha=0.75,zorder=10)
            sup = 'st' if nday == 1 else ('nd' if nday == 2 else ('rd' if nday == 3 else 'th')) 
            tags = ['WETTEST',f'{nday}$^{{{sup}}}$ WETTEST']
            for i in range(2):
                leg.text(10,leg_var[i,:][-1],tags[i],fontsize=6,alpha=0.5,weight='bold',ha='left',va='center')
            leg.set_title('How to read\nhistorical data',loc='center',fontsize=8,weight='bold',alpha=0.6);

        # Text indicator regardless of rain_type
        leg_hist = ax.legend([mpl.patches.Patch(facecolor='tab:blue', alpha=0.2, edgecolor=None)],
                     (r' $\bf{HISTORICAL \ DATA}$'+'\n'+r' $\bf{PERIOD :}$'+' {}-{}'.format(syr,eyr),''),
                                 fontsize=8,framealpha=0.,bbox_to_anchor=(0,0,0.274,0.94),handletextpad=0.48)
        ax.add_artist(leg_hist)                                           
        data_name = 'all days' if rain_type == 'all' else ('rain days > 0' if rain_type == 'rain' else (
                                                                             f'Wettest {nday} days over period'))
        ax.text(0.5,0.95,f'Historical Data: {data_name}',fontsize=9,ha='center',transform=ax.transAxes,
                weight='bold')

    ############################################################################################################# 
    # PLOT INDIVIDUAL YEAR 
    ############################################################################################################# 

    if incl_year == True:
        m,l,b = ax.stem(xtime,var_dy[str(iyr)],linefmt='tab:blue',basefmt=' ',markerfmt='o')
        plt.setp(m,markersize=1)
        plt.setp(l,linewidth=0.5)
        leg_year = ax.legend([mpl.lines.Line2D([0],[0],c='tab:blue',marker='o',linestyle='',markersize=4)],
                             (str(iyr),''),framealpha=0.,bbox_to_anchor=(0,0,0.13,1.0),
                             prop={'weight': 'bold', 'size': 8})

    ############################################################################################################# 
    # Features to include? Can toggle on and off in parameters
    ############################################################################################################# 

    if incl_map == True:
        inset_map(ax=ax,meta=meta,var=var,width=0.7,height=0.8,markercolor='k',incl_year=incl_year,iyr=iyr,
                  iyr_col='tab:red',slat=slat,nlat=nlat,wlon=wlon,elon=elon,bbox_to_anchor=(0,0,1,0.97),
                  lbl_buff=lbl_buff,proj=cartopy.crs.PlateCarree(),ext_buff=ext_buff,img_tile=img_tile)

    ############################################################################################################# 
    # Title and text
    ############################################################################################################# 

    ax.text(1.,-0.12,r'$\bf{DATA:}$'+' NOAA ACIS (http://data.rcc-acis.org)'+\
                     r'$\ \ \bf{IMAGE:}$ Alex Thompson (@ajtclimate)',
                     ha='right',va='center',fontsize=5,transform=ax.transAxes);
    ax.set_title('Daily Rainfall in '+location_name,loc='center',fontsize=14,pad=5,
                 weight='bold');

    ############################################################################################################# 
    # Axes specs 
    ############################################################################################################# 

    ax.set_xticks([str(plt_yr)+'-'+'{:02}'.format(month) for month in range(1, 13)])
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
    ax.set_ylabel('Region Mean (inches)')
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(majtick))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(mintick))
    ax.grid(alpha=0.05)
    ax.set_xlim([pd.to_datetime(str(plt_yr-1)+'-12-30'),pd.to_datetime(str(plt_yr+1)+'-01-01')])
    ax.set_ylim([0-np.nanmax(var_max)*0.02-minbuff,np.nanmax(var_max)+maxbuff]);
    ax.spines[['right','top']].set_visible(False)

    ############################################################################################################# 
    # Return relevant variables
    #############################################################################################################     

    if rain_type == 'all' or rain_type == 'rain':
       return fig, var_dy, var_max, var_95, var_avg

    if rain_type == 'wetNday':
       return fig, var_dy, var_max, var_min

#================================================================================================================
# annualcycle_snow_plot
#================================================================================================================

def annualcycle_snow_plot(var,meta,location_name,nlat,slat,wlon,elon,snow_type,nday,syr,eyr,num_stn,iyr,
              minbuff,maxbuff,majtick,mintick,incl_hist,incl_year,incl_map,img_tile,lbl_buff,ext_buff):

    ###################################################################################################
    # Average data by day and year 
    ###################################################################################################

    # List of leap years from 1800 to 2100
    leapyears = [1800 + i * 4 for i in range((2100 - 1800) // 4 + 1)]
    isleap = False if iyr not in leapyears else True

    # Apply NaN filter to the dataframe based on minimum number of stations collecting data on a given day
    var_filt = var.copy()
    var_filt.loc[var_filt.iloc[:,1:].count(axis=1) < num_stn, var_filt.columns[1:]] = np.nan

    # Average by day and year
    if snow_type == 'all' :
        var_dy = bbox_avg_dy(var_filt,leap=isleap)
    elif snow_type == 'snow' or snow_type == 'wetNday':
        # Set 0.'s and trace values to NaN (need to remove 'Date' column to do this)
        var_filt_snowdays = var_filt[[col for col in var_filt.columns if col != 'Date']].applymap(
                                             lambda x: x if x > 0.00001 else np.nan)
        # Add 'Date' column back 
        var_filt_snowdays['Date'] = var_filt['Date']
        var_dy = bbox_avg_dy(var_filt_snowdays,leap=isleap)

    ###################################################################################################
    # Auto-select dates based on parameters 
    ###################################################################################################

    # If earliest, take earliest year with data
    if syr == 'earliest':
        try:
           syr = int(np.min(var_dy.dropna(axis=1,how='all').columns[2:]))
        except:
           print('ERROR: There are no years with this many stations collecting data simultaneously.')

    # If latest, take latest year (but not this year) with fewer than 365 NaN values   
    if eyr == 'latest':
        for c in range(2,len(var_dy)+1):
            if var_dy[var_dy.columns[-c]].isna().sum() < 365:
                eyr = int(var_dy.columns[-c])
                break

    # Define back-end plotting year based on whether current year is a leap year or not
    plt_yr = 2020 if iyr in leapyears else 2022


    ###################################################################################################
    # Define figure 
    ###################################################################################################

    fig, ax = plt.subplots(figsize=[8,4],dpi=300)

    # Define x-axis time interval
    xtime = pd.date_range(start=str(plt_yr)+'-01-01', end=str(plt_yr)+'-12-31', freq='D')

    ############################################################################################################# 
    # PLOT HISTORICAL DATA 
    ############################################################################################################# 

    if incl_hist == True:
        
        if snow_type == 'all' or snow_type == 'snow':
    
            # MEAN
            var_avg = np.nanmean(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                              var_dy.columns.get_loc(str(eyr))+1],axis=1)
    
            # 95th percentile
            var_95 = np.nanpercentile(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                                    var_dy.columns.get_loc(str(eyr))+1],95,axis=1)
    
            # Max
            var_max = np.nanmax(var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):\
                                                    var_dy.columns.get_loc(str(eyr))+1],axis=1)
    
            # Plot historical data
            ax.plot(xtime,var_avg,'-',c='k',lw=1.5,alpha=0.5,zorder=100)
            ax.fill_between(xtime,np.zeros(len(xtime)),var_95,color='darkcyan',alpha=0.2,edgecolor=None,zorder=1)
            ax.fill_between(xtime,var_max,var_95,color='darkcyan',alpha=0.05,edgecolor=None,zorder=1)
            ax.plot(xtime,var_max,':',c='darkcyan',lw=0.25,alpha=0.75,zorder=10)
    
            # How to read historical data
            leg = fig.add_axes([0.48, 0.39, 0.1, 0.12])
            leg.set_xticklabels([]), leg.set_xticks([]), leg.set_yticklabels([]), leg.set_yticks([]);
            randomness,mult,last,leg_var = 0.5+0.5*np.random.rand(10),[10,5,1],[9,5,1],np.zeros((3,10))
            for i in range(3):
                leg_var[i,:],leg_var[i,-1] = mult[i]*np.ones(10)*randomness, last[i]
            leg.plot(np.arange(10),leg_var[2,:],'-',c='k',lw=1.5,alpha=0.5,zorder=100)
            leg.fill_between(np.arange(10),np.zeros(10),leg_var[1,:],color='darkcyan',alpha=0.2,edgecolor=None,
                             zorder=1)
            leg.fill_between(np.arange(10),leg_var[1,:],leg_var[0,:],color='darkcyan',alpha=0.05,edgecolor=None,
                             zorder=1)
            leg.plot(np.arange(10),leg_var[0,:],':',c='darkcyan',lw=0.25,alpha=0.75,zorder=10)
            tags = ['MAX','95$^{th}$','MEAN']
            for i in range(3):
                leg.text(10,leg_var[i,:][-1],tags[i],fontsize=6,alpha=0.5,weight='bold',ha='left',va='center')
            leg.set_title('How to read\nhistorical data',loc='center',fontsize=8,weight='bold',alpha=0.6);
    
        elif snow_type == 'wetNday':
            
            # Find wettest N days in period and extract max/min for plotting
            var_nday = var_dy.iloc[:,var_dy.columns.get_loc(str(syr)):var_dy.columns.get_loc(str(eyr))+1
                               ].apply(lambda row: row.sort_values(ascending=False)[:nday].values,axis=1)
            var_max = np.array([np.nanmax(d) for d in var_nday])
            var_min = np.array([np.nanmin(d) for d in var_nday])
            
            # Plot historical data
            ax.fill_between(xtime,var_max,var_min,color='darkcyan',alpha=0.2,edgecolor=None,zorder=1)
            ax.plot(xtime,var_max,':',c='darkcyan',lw=0.25,alpha=0.75,zorder=10)
            ax.plot(xtime,var_min,':',c='darkcyan',lw=0.25,alpha=0.75,zorder=10)
            
            # How to read historical data
            leg = fig.add_axes([0.48, 0.39, 0.1, 0.12])
            leg.set_xticklabels([]), leg.set_xticks([]), leg.set_yticklabels([]), leg.set_yticks([]);
            randomness,mult,last,leg_var = 0.5+0.5*np.random.rand(10),[8,2],[6,3],np.zeros((2,10))
            for i in range(2):
                leg_var[i,:],leg_var[i,-1] = mult[i]*np.ones(10)*randomness, last[i]
            leg.fill_between(np.arange(10),leg_var[0,:],leg_var[1,:],color='darkcyan',alpha=0.2,edgecolor=None,
                             zorder=1)
            leg.plot(np.arange(10),leg_var[0,:],':',c='darkcyan',lw=0.25,alpha=0.75,zorder=10)
            leg.plot(np.arange(10),leg_var[1,:],':',c='darkcyan',lw=0.25,alpha=0.75,zorder=10)
            sup = 'st' if nday == 1 else ('nd' if nday == 2 else ('rd' if nday == 3 else 'th')) 
            tags = ['HEAVIEST',f'{nday}$^{{{sup}}}$ HEAVIEST']
            for i in range(2):
                leg.text(10,leg_var[i,:][-1],tags[i],fontsize=6,alpha=0.5,weight='bold',ha='left',va='center')
            leg.set_title('How to read\nhistorical data',loc='center',fontsize=8,weight='bold',alpha=0.6);
            
        # Text indicator regardless of snow_type
        leg_hist = ax.legend([mpl.patches.Patch(facecolor='darkcyan', alpha=0.2, edgecolor=None)],
                     (r' $\bf{HISTORICAL \ DATA}$'+'\n'+r' $\bf{PERIOD :}$'+' {}-{}'.format(syr,eyr),''),
                                 fontsize=8,framealpha=0.,bbox_to_anchor=(0,0,0.669,0.77),handletextpad=0.48)
        ax.add_artist(leg_hist)
        data_name = 'all days' if snow_type == 'all' else ('snow days > 0' if snow_type == 'snow' else (
                                                                            f'Heaviest {nday} days over period'))
        ax.text(0.5,0.95,f'Historical Data: {data_name}',fontsize=9,ha='center',transform=ax.transAxes,
                weight='bold')

    ############################################################################################################# 
    # PLOT INDIVIDUAL YEAR 
    ############################################################################################################# 

    if incl_year == True:
        m,l,b = ax.stem(xtime,var_dy[str(iyr)],linefmt='darkcyan',basefmt=' ',markerfmt='o')
        plt.setp(m,markersize=1)
        plt.setp(l,linewidth=0.5)
        leg_year = ax.legend([mpl.lines.Line2D([0],[0],c='darkcyan',marker='o',linestyle='',markersize=4)],
                             (str(iyr),''),framealpha=0.,bbox_to_anchor=(0,0,0.525,0.85),
                             prop={'weight': 'bold', 'size': 8})

    ############################################################################################################# 
    # Features to include? Can toggle on and off in parameters
    ############################################################################################################# 

    if incl_map == True:
        inset_map(ax=ax,meta=meta,var=var,width=0.7,height=0.8,markercolor='k',incl_year=incl_year,iyr=iyr,
                  iyr_col='tab:red',slat=slat,nlat=nlat,wlon=wlon,elon=elon,bbox_to_anchor=(0,0,1,0.97),
                  lbl_buff=lbl_buff,proj=cartopy.crs.PlateCarree(),ext_buff=ext_buff,img_tile=img_tile)

    ############################################################################################################# 
    # Title and text
    ############################################################################################################# 

    ax.text(1.,-0.12,r'$\bf{DATA:}$'+' NOAA ACIS (http://data.rcc-acis.org)'+\
                     r'$\ \ \bf{IMAGE:}$ Alex Thompson (@ajtclimate)',
                     ha='right',va='center',fontsize=5,transform=ax.transAxes);
    ax.set_title('Daily Snowfall in '+location_name,loc='center',fontsize=14,pad=5,
                 weight='bold');

    ############################################################################################################# 
    # Axes specs 
    ############################################################################################################# 

    ax.set_xticks([str(plt_yr)+'-'+'{:02}'.format(month) for month in range(1, 13)])
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
    ax.set_ylabel('Region Mean (inches)')
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(majtick))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(mintick))
    ax.grid(alpha=0.05)
    ax.set_xlim([pd.to_datetime(str(plt_yr-1)+'-12-30'),pd.to_datetime(str(plt_yr+1)+'-01-01')])
    ax.set_ylim([0-np.nanmax(var_max)*0.02-minbuff,np.nanmax(var_max)+maxbuff]);
    ax.spines[['right','top']].set_visible(False)

    ############################################################################################################# 
    # Return relevant variables
    #############################################################################################################     

    if snow_type == 'all' or snow_type == 'snow':
       return fig, var_dy, var_max, var_95, var_avg

    if snow_type == 'wetNday':
       return fig, var_dy, var_max, var_min


#////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
# CUMULATIVE PLOTS
#
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////


#================================================================================================================
# cumulative_rain_plot  
#================================================================================================================

def cumulative_pcpn_plot(var,meta,location_name,nlat,slat,wlon,elon,syr,eyr,stats,na_allwd,iyr,
             minbuff,maxbuff,majtick,mintick,incl_hist,incl_year,incl_map,img_tile,lbl_buff,ext_buff,
             mltyr=''):

    ###################################################################################################
    # Average data by day and year 
    ###################################################################################################

    # List of leap years from 1800 to 2100
    leapyears = [1800 + i * 4 for i in range((2100 - 1800) // 4 + 1)]
    isleap = False if iyr not in leapyears else True

    # Average by day and year
    var_dy = bbox_avg_dy(var,leap=isleap)

    # Cumulative sum of rainfall, fill all NaNs (except this year) with zeros
    var_cs = var_dy.apply(lambda col: col.fillna(0) if col.name != str(pd.Timestamp.today().year) else col)
    var_cs = var_cs.cumsum()
    var_cs['month'] = var_dy['month']
    var_cs['day']   = var_dy['day']

    # Make year all NaNs if it has more than the threshold - i.e., it won't be shown
    var_cs[var_cs.isna().sum()[var_cs.isna().sum() > na_allwd].iloc[:-1].index] = float('nan')

    ###################################################################################################
    # Auto-select dates based on parameters 
    ###################################################################################################

    # If earliest, take earliest year with enough data (applying allowable missing value limit)
    if syr == 'earliest':
        for c in range(2,len(var_dy)+1):
            if var_dy[var_dy.columns[c]].isna().sum() < na_allwd:
                syr = int(var_dy.columns[c])
                break

    # If latest, take latest year (but not this year) (applying allowable missing value limit)
    if eyr == 'latest':
        for c in range(2,len(var_dy)+1):
            if var_dy[var_dy.columns[-c]].isna().sum() < 365:
                eyr = int(var_dy.columns[-c])
                break

    # Define back-end plotting year based on whether current year is a leap year or not
    plt_yr = 2020 if iyr in leapyears else 2022    

    ###################################################################################################
    # Define figure 
    ###################################################################################################

    fig, ax = plt.subplots(figsize=[8,5],dpi=300)

    # Define x-axis time interval
    xtime = pd.date_range(start=str(plt_yr)+'-01-01', end=str(plt_yr)+'-12-31', freq='D') 

    ############################################################################################################# 
    # PLOT HISTORICAL DATA 
    ############################################################################################################# 

    if incl_hist == True:

        # Choose colormap
        colortable = 'coolwarm'
        colors = plt.get_cmap(colortable)(mpl.colors.Normalize()(range(syr,eyr+1)))

        # Plot each year's cumulative values as a different color
        for i, yr in enumerate(range(syr,eyr+1)):
            ax.plot(xtime,var_cs[str(yr)],'-',c=colors[i],lw=1,alpha=0.5,zorder=0.1)

        # Color bar
        sm = plt.cm.ScalarMappable(cmap=colortable, norm=mpl.colors.Normalize(vmin=syr,vmax=eyr))
        cbar = plt.colorbar(sm,ax=ax,orientation='horizontal',shrink=0.38,anchor=(0.28,7.66))
        cbar.set_ticks(range(syr, eyr+1))
        cbar.set_ticklabels(range(syr, eyr+1),fontsize=8)
        cbar.ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(20))
        minor_multlocator = 5 if eyr-syr > 40 else 1 # if period is <40, higher minor tick resolution
        cbar.ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(minor_multlocator))
        ax.text(0.17,0.93,r' $\bf{HISTORICAL \ DATA \ PERIOD :}$'+' {}-{}'.format(syr,eyr),
                fontsize=7,transform=ax.transAxes)

        # Plot stats of cumulative values
        if stats == 'Mean':
           var_stat = np.nanmean(var_cs.iloc[:,var_cs.columns.get_loc(str(syr)):\
                                               var_cs.columns.get_loc(str(eyr))+1],axis=1)
           stats_text = 'MEAN'
        if stats == 'Median':
           var_stat = np.nanmedian(var_cs.iloc[:,var_cs.columns.get_loc(str(syr)):\
                                                 var_cs.columns.get_loc(str(eyr))+1],axis=1)
           stats_text = 'MEDIAN'
        ax.plot(xtime,var_stat,'--',c='k',alpha=0.5,lw=1.5,zorder=10)
        ax.text(pd.to_datetime(str(plt_yr)+'-12-31'),var_stat[-1]+1,stats_text,ha='right',fontsize=8,
                weight='bold',alpha=0.75)

    ############################################################################################################# 
    # PLOT INDIVIDUAL YEAR 
    ############################################################################################################# 

    if incl_year == True:
        ax.plot(xtime,var_cs[str(iyr)],'-',c='k',lw=2,zorder=1000)

    if mltyr == '':
        # Make legend for iyr
        leg_year = ax.legend([mpl.lines.Line2D([0],[0],c='k',linestyle='-',lw=2)],
                             (str(iyr),''),framealpha=0.,loc='upper left',
                             prop={'weight': 'bold', 'size': 8})
        leg_year.set_bbox_to_anchor((0.16,0.77))
    else:
        # Add in-graph text for iyr
        ax.text(xtime[np.count_nonzero(~np.isnan(var_cs[str(iyr)]))]+pd.Timedelta(days=3),
                var_cs[str(iyr)].iloc[np.count_nonzero(~np.isnan(var_cs[str(iyr)]))-1],
                r'$\bf{'+str(iyr)+'}$',color='k',fontsize=9,zorder=1000)
        
        # Plot each additional year
        mltyr = mltyr.split(',')
        tab10 = [mpl.colormaps['tab10'](i) for i in range(mpl.colormaps['tab10'].N)]
        mltyr_col = [tab10[3],tab10[1],tab10[2],tab10[0]]+tab10[4:]
        for i in range(len(mltyr)):
            ax.plot(xtime,var_cs[mltyr[i]],'-',c=mltyr_col[i],lw=2,zorder=999)
            ax.text(pd.to_datetime(str(plt_yr)+'-12-31')+pd.Timedelta(days=3),var_cs[mltyr[i]].iloc[-1],
                    r'$\bf{'+str(mltyr[i])+'}$',color=mltyr_col[i],fontsize=8,zorder=999)

    ############################################################################################################# 
    # Features to include? Can toggle on and off in parameters
    ############################################################################################################# 
        
    if incl_map == True:
        inset_map(ax=ax,meta=meta,var=var,width=0.7,height=0.8,markercolor='k',incl_year=incl_year,iyr=iyr,
                  iyr_col='tab:red',slat=slat,nlat=nlat,wlon=wlon,elon=elon,bbox_to_anchor=(0,0,0.142,0.95),
                  lbl_buff=lbl_buff,proj=cartopy.crs.PlateCarree(),ext_buff=ext_buff,img_tile=img_tile)

    ############################################################################################################# 
    # Title and text
    ############################################################################################################# 

    ax.text(1.,0.025,r'$\bf{DATA:}$'+' NOAA ACIS (http://data.rcc-acis.org)'+\
                     r'$\ \ \bf{IMAGE:}$ Alex Thompson (@ajtclimate)',
                     ha='right',va='center',fontsize=5,transform=ax.transAxes);
    ax.set_title('Cumulative Rainfall in '+location_name,loc='center',fontsize=14,pad=5,
                 weight='bold');

    ############################################################################################################# 
    # Axes specs 
    ############################################################################################################# 

    ax.set_xticks([str(plt_yr)+'-'+'{:02}'.format(month) for month in range(1, 13)])
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
    ax.set_ylabel('Region Mean (inches)')
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(majtick))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(mintick))
    ax.grid(alpha=0.05)
    ax.set_xlim([pd.to_datetime(str(plt_yr-1)+'-12-30'),pd.to_datetime(str(plt_yr+1)+'-01-01')])
    ax.set_ylim([0-np.nanmax(var_cs.iloc[2:])*0.02-minbuff,np.nanmax(var_cs.iloc[2:])+maxbuff]);
    ax.spines[['right','top']].set_visible(False)

    return fig, var_cs

#================================================================================================================
# cumulative_snow_plot
#================================================================================================================

def cumulative_snow_plot(var,meta,location_name,nlat,slat,wlon,elon,syr,eyr,stats,na_allwd,iyr,
             minbuff,maxbuff,majtick,mintick,incl_hist,incl_year,incl_map,img_tile,lbl_buff,ext_buff,
             mltyr=''):

    ###################################################################################################
    # Average data by day and year 
    ###################################################################################################

    # List of leap years from 1800 to 2100
    leapyears = [1800 + i * 4 for i in range((2100 - 1800) // 4 + 1)]
    isleap = False if iyr not in leapyears else True

    # Average by day and year
    var_dy = bbox_avg_dy(var,leap=isleap)

    # Cumulative sum of rainfall, fill all NaNs (except this year) with zeros
    var_cs = var_dy.apply(lambda col: col.fillna(0) if col.name != str(pd.Timestamp.today().year) else col)
    var_cs = var_cs.cumsum()
    var_cs['month'] = var_dy['month']
    var_cs['day']   = var_dy['day']

    # Make year all NaNs if it has more than the threshold - i.e., it won't be shown
    var_cs[var_cs.isna().sum()[var_cs.isna().sum() > na_allwd].iloc[:-1].index] = float('nan')

    ###################################################################################################
    # Auto-select dates based on parameters 
    ###################################################################################################

    # If earliest, take earliest year with enough data (applying allowable missing value limit)
    if syr == 'earliest':
        for c in range(2,len(var_dy)+1):
            if var_dy[var_dy.columns[c]].isna().sum() < na_allwd:
                syr = int(var_dy.columns[c])
                break

    # If latest, take latest year (but not this year) (applying allowable missing value limit)
    if eyr == 'latest':
        for c in range(2,len(var_dy)+1):
            if var_dy[var_dy.columns[-c]].isna().sum() < 365:
                eyr = int(var_dy.columns[-c])
                break

    # Define back-end plotting year based on whether current year is a leap year or not
    plt_yr = 2020 if iyr in leapyears else 2022

    ###################################################################################################
    # Define figure 
    ###################################################################################################

    fig, ax = plt.subplots(figsize=[8,5],dpi=300)

    # Define x-axis time interval
    xtime = pd.date_range(start=str(plt_yr)+'-01-01', end=str(plt_yr)+'-12-31', freq='D')

    ############################################################################################################# 
    # PLOT HISTORICAL DATA 
    ############################################################################################################# 

    if incl_hist == True:

        # Choose colormap
        colortable = 'coolwarm'
        colors = plt.get_cmap(colortable)(mpl.colors.Normalize()(range(syr,eyr+1)))

        # Plot each year's cumulative values as a different color
        for i, yr in enumerate(range(syr,eyr+1)):
            ax.plot(xtime,var_cs[str(yr)],'-',c=colors[i],lw=1,alpha=0.5,zorder=0.1)

        # Color bar
        sm = plt.cm.ScalarMappable(cmap=colortable, norm=mpl.colors.Normalize(vmin=syr,vmax=eyr))
        cbar = plt.colorbar(sm,ax=ax,orientation='horizontal',shrink=0.38,anchor=(0.28,7.66))
        cbar.set_ticks(range(syr, eyr+1))
        cbar.set_ticklabels(range(syr, eyr+1),fontsize=8)
        cbar.ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(20))
        minor_multlocator = 5 if eyr-syr > 40 else 1 # if period is <40, higher minor tick resolution
        cbar.ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(minor_multlocator))
        ax.text(0.17,0.93,r' $\bf{HISTORICAL \ DATA \ PERIOD :}$'+' {}-{}'.format(syr,eyr),
                fontsize=7,transform=ax.transAxes)

        # Plot stats of cumulative values
        if stats == 'Mean':
           var_stat = np.nanmean(var_cs.iloc[:,var_cs.columns.get_loc(str(syr)):\
                                               var_cs.columns.get_loc(str(eyr))+1],axis=1)
           stats_text = 'MEAN'
        if stats == 'Median':
           var_stat = np.nanmedian(var_cs.iloc[:,var_cs.columns.get_loc(str(syr)):\
                                                 var_cs.columns.get_loc(str(eyr))+1],axis=1)
           stats_text = 'MEDIAN'
        ax.plot(xtime,var_stat,'--',c='k',alpha=0.5,lw=1.5,zorder=10)
        ax.text(pd.to_datetime(str(plt_yr)+'-12-31'),var_stat[-1]+1,stats_text,ha='right',fontsize=8,
                weight='bold',alpha=0.75)

    ############################################################################################################# 
    # PLOT INDIVIDUAL YEAR 
    ############################################################################################################# 

    if incl_year == True:
        ax.plot(xtime,var_cs[str(iyr)],'-',c='k',lw=2,zorder=1000)

    if mltyr == '':
        # Make legend for iyr
        leg_year = ax.legend([mpl.lines.Line2D([0],[0],c='k',linestyle='-',lw=2)],
                             (str(iyr),''),framealpha=0.,loc='upper left',  
                             prop={'weight': 'bold', 'size': 8})
        leg_year.set_bbox_to_anchor((0.16,0.77))
    else:
        # Add in-graph text for iyr
        ax.text(xtime[np.count_nonzero(~np.isnan(var_cs[str(iyr)]))]+pd.Timedelta(days=3),
                var_cs[str(iyr)].iloc[np.count_nonzero(~np.isnan(var_cs[str(iyr)]))-1],
                r'$\bf{'+str(iyr)+'}$',color='k',fontsize=9,zorder=1000)

        # Plot each additional year
        mltyr = mltyr.split(',')
        tab10 = [mpl.colormaps['tab10'](i) for i in range(mpl.colormaps['tab10'].N)]
        mltyr_col = [tab10[3],tab10[1],tab10[2],tab10[0]]+tab10[4:]
        for i in range(len(mltyr)):
            ax.plot(xtime,var_cs[mltyr[i]],'-',c=mltyr_col[i],lw=2,zorder=999)
            ax.text(pd.to_datetime(str(plt_yr)+'-12-31')+pd.Timedelta(days=3),var_cs[mltyr[i]].iloc[-1],
                    r'$\bf{'+str(mltyr[i])+'}$',color=mltyr_col[i],fontsize=8,zorder=999)

    ############################################################################################################# 
    # Features to include? Can toggle on and off in parameters
    ############################################################################################################# 

    if incl_map == True:
        inset_map(ax=ax,meta=meta,var=var,width=0.7,height=0.8,markercolor='k',incl_year=incl_year,iyr=iyr,
                  iyr_col='tab:red',slat=slat,nlat=nlat,wlon=wlon,elon=elon,bbox_to_anchor=(0,0,0.142,0.95),
                  lbl_buff=lbl_buff,proj=cartopy.crs.PlateCarree(),ext_buff=ext_buff,img_tile=img_tile)

    ############################################################################################################# 
    # Title and text
    ############################################################################################################# 

    ax.text(1.,-0.12,r'$\bf{DATA:}$'+' NOAA ACIS (http://data.rcc-acis.org)'+\
                     r'$\ \ \bf{IMAGE:}$ Alex Thompson (@ajtclimate)',
                     ha='right',va='center',fontsize=5,transform=ax.transAxes);
    ax.set_title('Cumulative Snowfall in '+location_name,loc='center',fontsize=14,pad=5,
                 weight='bold');

    ############################################################################################################# 
    # Axes specs 
    ############################################################################################################# 

    ax.set_xticks([str(plt_yr)+'-'+'{:02}'.format(month) for month in range(1, 13)])
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
    ax.set_ylabel('Region Mean (inches)')
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(majtick))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(mintick))
    ax.grid(alpha=0.05)
    ax.set_xlim([pd.to_datetime(str(plt_yr-1)+'-12-30'),pd.to_datetime(str(plt_yr+1)+'-01-01')])
    ax.set_ylim([0-np.nanmax(var_cs.iloc[2:])*0.02-minbuff,np.nanmax(var_cs.iloc[2:])+maxbuff]);
    ax.spines[['right','top']].set_visible(False)

    return fig, var_cs

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
# TIME SERIES PLOTS
#
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#================================================================================================================
# timeseries_tmax_plot 
#================================================================================================================

def timeseries_tmax_plot(var,meta,location_name,nlat,slat,wlon,elon,month1,month2,num_days,num_mons,num_stns,
                         method,incl_tl,tl_syr,tl_eyr,minbuff,maxbuff,ymajtick,ymintick,xmajtick,xmintick,
                         incl_map,img_tile,lbl_buff,ext_buff):
        
    ############################################################################################################# 
    # Convert months string into list of months as integers
    #############################################################################################################
    
    # Lists of month strings
    month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    mon1 = month_names[month_names.index(month1):]      # all elements to the right (inclusive) of month1
    mon2 = month_names[:(month_names.index(month2)+1)]  # all elements to the left (inclusive) of month 2
    
    # Combine lists of months to create single list 
    if [i for i in mon1 if i in mon2] != []:  # there is overlap between lists
        mon_str = [i for i in mon1 if i in mon2]
    else:                                     # there is no overlap between lists
        mon_str = mon1 + mon2
    
    # Convert strings to integers
    monthi = [month_names.index(i)+1 for i in mon_str]
    
    ############################################################################################################# 
    # Create time series variable and apply data quality filters 
    #############################################################################################################
    
    # Mask var based on data quality standards (num_days, num_mons, num_stns)
    var_filt = var.copy()
    
    # Add 'Year' and 'Month' to filter
    if 'Year' not in var_filt.columns and 'Month' not in var_filt.columns:
        var_filt.insert(0,'Year',var_filt['Date'].dt.year),var_filt.insert(1,'Month',var_filt['Date'].dt.month)  
        
    months_that_pass = var_filt.groupby(['Year','Month']).apply(lambda x: x.iloc[:,3:].count()) >= num_days
    years_that_pass = months_that_pass.groupby(level='Year').sum() >= num_mons
    stns_that_pass = years_that_pass.sum(axis=1) >= num_stns
    
    # Apply data quality standards to year's average value
    var_mask = var.copy()
    var_mask.loc[var_mask['Date'].dt.year.isin(list(stns_that_pass[stns_that_pass == False].index)),:] = np.nan
    var_mask['Date'] = var['Date']
    
    # Find bbox's max, min, or mean for each month and apply months to processed variable
    if method == 'max':
        var_my = bbox_max_my(var_mask)
        ts_pre = var_my.iloc[:,1:].loc[var_my['Month'].isin(monthi)].max()
    if method == 'min':
        var_my = bbox_min_my(var_mask)
        ts_pre = var_my.iloc[:,1:].loc[var_my['Month'].isin(monthi)].min()
    if method == 'avg':
        var_my = bbox_avg_my(var_mask)
        
        # Not weighted by month
        #ts_pre = var_my.iloc[:,1:].loc[var_my['Month'].isin(monthi)].mean()
        
        # Weighted by month
        mnly_vals = var_my.iloc[:,1:].loc[var_my['Month'].isin(monthi)]
        mnly_wgts = np.array([0.08493151,0.076712325,0.08493151,0.08219178,0.08493151,0.08219178,
                              0.08493151,0.08493151, 0.08219178,0.08493151,0.08219178,0.08493151])
        wgts = mnly_wgts if len(monthi) == 12 else mnly_wgts[[m-1 for m in monthi]]/np.sum(
                                                                           mnly_wgts[[m-1 for m in monthi]])
        ts_pre = pd.Series(index=mnly_vals.columns,dtype='float')
        for i, c in enumerate(mnly_vals.columns):
            if mnly_vals[c].isna().any(): # if any of the monthly values is NaN
               ts_pre.iloc[i] = np.nan
            else:
               ts_pre.iloc[i] = (mnly_vals[c]*wgts).sum() / wgts.sum()
   
    # Remove NaN values
    ts_pre = ts_pre.loc[str(ts_pre.first_valid_index()):str(ts_pre.last_valid_index())] 
    ts = pd.DataFrame({'Year':np.array(ts_pre.index,dtype=int),'Value':ts_pre.reset_index(drop=True)})
 
    ############################################################################################################# 
    # Define figure 
    ############################################################################################################# 

    fig, ax = plt.subplots(figsize=[8,4],dpi=300)

    # Define x-axis years
    try: 
       xtime = pd.Series(pd.date_range(start=str(ts['Year'].iloc[0])+'-01-01',
                                         end=str(ts['Year'].iloc[-1])+'-01-01',freq='YS'))
    except IndexError:
       print('ERROR: No data exists at this high a data quality standard. Reduce one of the options for '+
             ' data quality')

    ############################################################################################################# 
    # PLOT TIME SERIES 
    ############################################################################################################# 

    ax.plot(xtime,ts['Value'],'o-',markersize=0.5,c='tab:red',lw=1)
    
    if incl_tl == True:
 
        # Determine years for trendline
        tl_syr = xtime.dt.year[0] if tl_syr == 'Start' else tl_syr
        tl_eyr = xtime.iloc[-1].year if tl_eyr == 'End' else tl_eyr

        # Extract subset of variables based on tl_syr/tl_eyr
        xtime_tl = xtime.loc[xtime.between(pd.to_datetime(str(tl_syr)+'-01-01'),
                                           pd.to_datetime(str(tl_eyr)+'-01-01'))].reset_index(drop=True)
        ts_tl = ts['Value'].loc[ts['Year'].between(int(tl_syr),int(tl_eyr))].reset_index(drop=True)

        # Account for NaNs when calculating polyfit
        ifinite = np.isfinite(np.array(xtime_tl)) & np.isfinite(np.array(ts_tl))
        m,b = np.polyfit(np.arange(len(xtime_tl))[ifinite],np.array(ts_tl)[ifinite],1)
        trendline = pd.Series(m * np.arange(len(xtime_tl)) + b)

        # Plot trendline and display slope as text on figure
        ax.plot(xtime_tl,trendline,'-',c='k',lw=0.5)
        sign = '+' if m > 0 else ''
        ax.text(xtime_tl.iloc[-1]+pd.Timedelta(days=365),trendline.iloc[-1],sign+str(round(m,3))+'°F/yr',
                fontsize=5,bbox=dict(boxstyle='square',pad=0.1,edgecolor='none',facecolor='w'))
    
    ############################################################################################################# 
    # Features to include? Can toggle on and off in parameters
    ############################################################################################################# 

    if incl_map != 'False':
        bbox_to_anchor = (0,0,1,0.94) if incl_map == 'True (right)' else (0,0,0.15,0.94)
        inset_map(ax=ax,meta=meta,var=var,width=0.7,height=0.8,markercolor='k',slat=slat,nlat=nlat,
                  wlon=wlon,elon=elon,bbox_to_anchor=bbox_to_anchor,lbl_buff=lbl_buff,
                  proj=cartopy.crs.PlateCarree(),ext_buff=ext_buff,img_tile=img_tile)

    ############################################################################################################# 
    # Title and text
    ############################################################################################################# 

    ax.text(1,0.015,r'$\bf{DATA:}$ NOAA ACIS (http://data.rcc-acis.org) '+
                   r' $\bf{IMAGE:}$ Alex Thompson (@ajtclimate)',ha='right',fontsize=5,transform=ax.transAxes)    
    season = f'{month1}-{month2}' if len(monthi) < 12 and month1 != month2 else (
                                                                        month1 if month1 == month2 else 'Annual')
    ax.set_title(season+' Daily High Temperature in '+location_name,loc='center',fontsize=14,pad=5,weight='bold');
    if method == 'max':
       method_text = "Maximum individual station's T$_\mathrm{MAX}$ within the bounding box"
    if method == 'min':
       method_text = "Minimum individual station's T$_\mathrm{MAX}$ within the bounding box"
    if method == 'avg':
       method_text = "Mean T$_\mathrm{MAX}$ for all stations within bounding box"        
    ax.text(0.5,0.95,method_text,fontsize=9,ha='center',transform=ax.transAxes)

    ############################################################################################################# 
    # Axes specs 
    ############################################################################################################# 

    ylabel_text = 'Region Max' if method == 'max' else ('Region Min' if method == 'min' else 'Region Mean')
    ax.set_ylabel(f'{ylabel_text} (°F)')
    ax.get_xaxis().set_major_locator(mpl.dates.YearLocator(base=xmajtick))
    ax.get_xaxis().set_minor_locator(mpl.dates.YearLocator(base=xmintick))
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(ymajtick))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(ymintick))
    ax.grid(alpha=0.05)
    ax.set_ylim([np.nanmin(ts['Value'])-minbuff,np.nanmax(ts['Value'])+maxbuff]);
    ax.spines[['right','top']].set_visible(False)

    return fig, var_my, ts

#================================================================================================================
# timeseries_tmin_plot 
#================================================================================================================

def timeseries_tmin_plot(var,meta,location_name,nlat,slat,wlon,elon,month1,month2,num_days,num_mons,num_stns,
                         method,incl_tl,tl_syr,tl_eyr,minbuff,maxbuff,ymajtick,ymintick,xmajtick,xmintick,
                         incl_map,img_tile,lbl_buff,ext_buff):

    ############################################################################################################# 
    # Convert months string into list of months as integers
    #############################################################################################################

    # Lists of month strings
    month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    mon1 = month_names[month_names.index(month1):]      # all elements to the right (inclusive) of month1
    mon2 = month_names[:(month_names.index(month2)+1)]  # all elements to the left (inclusive) of month 2

    # Combine lists of months to create single list 
    if [i for i in mon1 if i in mon2] != []:  # there is overlap between lists
        mon_str = [i for i in mon1 if i in mon2]
    else:                                     # there is no overlap between lists
        mon_str = mon1 + mon2

    # Convert strings to integers
    monthi = [month_names.index(i)+1 for i in mon_str]

    ############################################################################################################# 
    # Create time series variable and apply data quality filters 
    #############################################################################################################

    # Mask var based on data quality standards (num_days, num_mons, num_stns)
    var_filt = var.copy()

    # Add 'Year' and 'Month' to filter
    if 'Year' not in var_filt.columns and 'Month' not in var_filt.columns:
        var_filt.insert(0,'Year',var_filt['Date'].dt.year),var_filt.insert(1,'Month',var_filt['Date'].dt.month)

    months_that_pass = var_filt.groupby(['Year','Month']).apply(lambda x: x.iloc[:,3:].count()) >= num_days
    years_that_pass = months_that_pass.groupby(level='Year').sum() >= num_mons
    stns_that_pass = years_that_pass.sum(axis=1) >= num_stns

    # Apply data quality standards to year's average value
    var_mask = var.copy()
    var_mask.loc[var_mask['Date'].dt.year.isin(list(stns_that_pass[stns_that_pass == False].index)),:] = np.nan
    var_mask['Date'] = var['Date']

    # Find bbox's max, min, or mean for each month and apply months to processed variable
    if method == 'max':
        var_my = bbox_max_my(var_mask)
        ts_pre = var_my.iloc[:,1:].loc[var_my['Month'].isin(monthi)].max()
    if method == 'min':
        var_my = bbox_min_my(var_mask)
        ts_pre = var_my.iloc[:,1:].loc[var_my['Month'].isin(monthi)].min()
    if method == 'avg':
        var_my = bbox_avg_my(var_mask)

        # Not weighted by month
        #ts_pre = var_my.iloc[:,1:].loc[var_my['Month'].isin(monthi)].mean()

        # Weighted by month
        mnly_vals = var_my.iloc[:,1:].loc[var_my['Month'].isin(monthi)]
        mnly_wgts = np.array([0.08493151,0.076712325,0.08493151,0.08219178,0.08493151,0.08219178,
                              0.08493151,0.08493151, 0.08219178,0.08493151,0.08219178,0.08493151])
        wgts = mnly_wgts if len(monthi) == 12 else mnly_wgts[[m-1 for m in monthi]]/np.sum(
                                                                           mnly_wgts[[m-1 for m in monthi]])
        ts_pre = pd.Series(index=mnly_vals.columns,dtype='float')
        for i, c in enumerate(mnly_vals.columns):
            if mnly_vals[c].isna().any(): # if any of the monthly values is NaN
               ts_pre.iloc[i] = np.nan
            else:
               ts_pre.iloc[i] = (mnly_vals[c]*wgts).sum() / wgts.sum()

    # Remove NaN values
    ts_pre = ts_pre.loc[str(ts_pre.first_valid_index()):str(ts_pre.last_valid_index())]
    ts = pd.DataFrame({'Year':np.array(ts_pre.index,dtype=int),'Value':ts_pre.reset_index(drop=True)})

    ############################################################################################################# 
    # Define figure 
    ############################################################################################################# 

    fig, ax = plt.subplots(figsize=[8,4],dpi=300)

    # Define x-axis years
    try:
       xtime = pd.Series(pd.date_range(start=str(ts['Year'].iloc[0])+'-01-01',
                                         end=str(ts['Year'].iloc[-1])+'-01-01',freq='YS'))
    except IndexError:
       print('ERROR: No data exists at this high a data quality standard. Reduce one of the options for '+
             ' data quality')

    ############################################################################################################# 
    # PLOT TIME SERIES 
    ############################################################################################################# 

    ax.plot(xtime,ts['Value'],'o-',markersize=0.5,c='tab:blue',lw=1)

    if incl_tl == True:

        # Determine years for trendline
        tl_syr = xtime.dt.year[0] if tl_syr == 'Start' else tl_syr
        tl_eyr = xtime.iloc[-1].year if tl_eyr == 'End' else tl_eyr

        # Extract subset of variables based on tl_syr/tl_eyr
        xtime_tl = xtime.loc[xtime.between(pd.to_datetime(str(tl_syr)+'-01-01'),
                                           pd.to_datetime(str(tl_eyr)+'-01-01'))].reset_index(drop=True)
        ts_tl = ts['Value'].loc[ts['Year'].between(int(tl_syr),int(tl_eyr))].reset_index(drop=True)

        # Account for NaNs when calculating polyfit
        ifinite = np.isfinite(np.array(xtime_tl)) & np.isfinite(np.array(ts_tl))
        m,b = np.polyfit(np.arange(len(xtime_tl))[ifinite],np.array(ts_tl)[ifinite],1)
        trendline = pd.Series(m * np.arange(len(xtime_tl)) + b)

        # Plot trendline and display slope as text on figure
        ax.plot(xtime_tl,trendline,'-',c='k',lw=0.5)
        sign = '+' if m > 0 else ''
        ax.text(xtime_tl.iloc[-1]+pd.Timedelta(days=365),trendline.iloc[-1],sign+str(round(m,3))+'°F/yr',
                fontsize=5,bbox=dict(boxstyle='square',pad=0.1,edgecolor='none',facecolor='w'))

    ############################################################################################################# 
    # Features to include? Can toggle on and off in parameters
    ############################################################################################################# 

    if incl_map != 'False':
        bbox_to_anchor = (0,0,1,0.94) if incl_map == 'True (right)' else (0,0,0.15,0.94)
        inset_map(ax=ax,meta=meta,var=var,width=0.7,height=0.8,markercolor='k',slat=slat,nlat=nlat,
                  wlon=wlon,elon=elon,bbox_to_anchor=bbox_to_anchor,lbl_buff=lbl_buff,
                  proj=cartopy.crs.PlateCarree(),ext_buff=ext_buff,img_tile=img_tile)

    ############################################################################################################# 
    # Title and text
    ############################################################################################################# 

    ax.text(1,0.015,r'$\bf{DATA:}$ NOAA ACIS (http://data.rcc-acis.org) '+
                   r' $\bf{IMAGE:}$ Alex Thompson (@ajtclimate)',ha='right',fontsize=5,transform=ax.transAxes)
    season = f'{month1}-{month2}' if len(monthi) < 12 and month1 != month2 else (
                                                                        month1 if month1 == month2 else 'Annual')
    ax.set_title(season+' Daily Low Temperature in '+location_name,loc='center',fontsize=14,pad=5,weight='bold');
    if method == 'max':
       method_text = "Maximum individual station's T$_\mathrm{MIN}$ within the bounding box"
    if method == 'min':
       method_text = "Minimum individual station's T$_\mathrm{MIN}$ within the bounding box"
    if method == 'avg':
       method_text = "Mean T$_\mathrm{MIN}$ for all stations within bounding box"
    ax.text(0.5,0.95,method_text,fontsize=9,ha='center',transform=ax.transAxes)

    ############################################################################################################# 
    # Axes specs 
    ############################################################################################################# 

    ylabel_text = 'Region Max' if method == 'max' else ('Region Min' if method == 'min' else 'Region Mean')
    ax.set_ylabel(f'{ylabel_text} (°F)')
    ax.get_xaxis().set_major_locator(mpl.dates.YearLocator(base=xmajtick))
    ax.get_xaxis().set_minor_locator(mpl.dates.YearLocator(base=xmintick))
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(ymajtick))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(ymintick))
    ax.grid(alpha=0.05)
    ax.set_ylim([np.nanmin(ts['Value'])-minbuff,np.nanmax(ts['Value'])+maxbuff]);
    ax.spines[['right','top']].set_visible(False)

    return fig, var_my, ts

#================================================================================================================
# timeseries_pcpn_plot 
#================================================================================================================
 
def timeseries_pcpn_plot(var,meta,location_name,nlat,slat,wlon,elon,month1,month2,num_days,num_mons,num_stns,
                         method,incl_tl,tl_syr,tl_eyr,minbuff,maxbuff,ymajtick,ymintick,xmajtick,xmintick,
                         incl_map,img_tile,lbl_buff,ext_buff):
        
    ############################################################################################################# 
    # Convert months string into list of months as integers
    #############################################################################################################

    # Lists of month strings
    month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    mon1 = month_names[month_names.index(month1):]      # all elements to the right (inclusive) of month1
    mon2 = month_names[:(month_names.index(month2)+1)]  # all elements to the left (inclusive) of month 2

    # Combine lists of months to create single list 
    if [i for i in mon1 if i in mon2] != []:  # there is overlap between lists
        mon_str = [i for i in mon1 if i in mon2]
    else:                                     # there is no overlap between lists
        mon_str = mon1 + mon2

    # Convert strings to integers
    monthi = [month_names.index(i)+1 for i in mon_str]

    ############################################################################################################# 
    # Create time series variable and apply data quality filters 
    #############################################################################################################

    # Mask var based on data quality standards (num_days, num_mons, num_stns)
    var_filt = var.copy()

    # Add 'Year' and 'Month' to filter
    if 'Year' not in var_filt.columns and 'Month' not in var_filt.columns:
        var_filt.insert(0,'Year',var_filt['Date'].dt.year),var_filt.insert(1,'Month',var_filt['Date'].dt.month)

    months_that_pass = var_filt.groupby(['Year','Month']).apply(lambda x: x.iloc[:,3:].count()) >= num_days
    years_that_pass = months_that_pass.groupby(level='Year').sum() >= num_mons
    stns_that_pass = years_that_pass.sum(axis=1) >= num_stns

    # Apply data quality standards to year's average value
    var_mask = var.copy()
    var_mask.loc[var_mask['Date'].dt.year.isin(list(stns_that_pass[stns_that_pass == False].index)),:] = np.nan
    var_mask['Date'] = var['Date']

    # dataframe is masked by this line, next lines are to decide which method to use

    # Determine which method to plot: rx1day methods
    if method == 'rx1day-max':
        var_my = bbox_max_my(var_mask)
        ts_pre = var_my.iloc[:,1:].loc[var_my['Month'].isin(monthi)].max()
    if method == 'rx1day-mean':
        # This way works but is slow - try to speed it up
        print('This method may take a few minutes...')
        warnings.filterwarnings('ignore',category=RuntimeWarning)
        ts_pre_col = pd.DataFrame({'Year':var['Date'].dt.year.unique()}) 
        for c in var_mask.columns[1:]:
            var_my_by_col = bbox_max_my(pd.DataFrame({'Date':var_mask['Date'],c:var_mask[c]}))
            ts_pre_col[c] = np.nanmax(var_my_by_col.iloc[:,1:].loc[var_my_by_col['Month'].isin(monthi)],axis=0)
        ts_pre = pd.Series(np.nanmean(ts_pre_col.iloc[:,1:],axis=1),index=np.array(ts_pre_col['Year']).flatten())

    # Determine which method to plot: region mean methods
    if method == 'alldays-mean':  # first part
        var_my = bbox_avg_my(var_mask)
    if method == 'raindays-mean': # first part
        var_mask_raindays = var_mask[[col for col in var_mask.columns if col != 'Date']].applymap(
                             lambda x: x if x > 0.00001 else np.nan) # set 0.'s and trace vals to NaN
        var_mask_raindays['Date'] = var_mask['Date'] # add 'Date' back in for bbox_avg_my
        var_my = bbox_avg_my(var_mask_raindays)
        
    if method == 'alldays-mean' or method == 'raindays-mean': # second part
        mnly_vals = var_my.iloc[:,1:].loc[var_my['Month'].isin(monthi)]
        mnly_wgts = np.array([0.08493151,0.076712325,0.08493151,0.08219178,0.08493151,0.08219178,
                              0.08493151,0.08493151, 0.08219178,0.08493151,0.08219178,0.08493151])
        wgts = mnly_wgts if len(monthi) == 12 else mnly_wgts[[m-1 for m in monthi]]/np.sum(
                                                                           mnly_wgts[[m-1 for m in monthi]])
        ts_pre = pd.Series(index=mnly_vals.columns,dtype='float')
        for i, c in enumerate(mnly_vals.columns):
            if mnly_vals[c].isna().any(): # if any of the monthly values is NaN
               ts_pre.iloc[i] = np.nan
            else:
               ts_pre.iloc[i] = (mnly_vals[c]*wgts).sum() / wgts.sum()
            
    # Remove NaN values
    ts_pre = ts_pre.loc[str(ts_pre.first_valid_index()):str(ts_pre.last_valid_index())]
    ts = pd.DataFrame({'Year':np.array(ts_pre.index,dtype=int),'Value':ts_pre.reset_index(drop=True)})
    
    ############################################################################################################# 
    # Define figure 
    ############################################################################################################# 

    fig, ax = plt.subplots(figsize=[8,4],dpi=300)

    # Define x-axis years
    try:
       xtime = pd.Series(pd.date_range(start=str(ts['Year'].iloc[0])+'-01-01',
                                         end=str(ts['Year'].iloc[-1])+'-01-01',freq='YS'))
    except IndexError:
       print('ERROR: No data exists at this high a data quality standard. Reduce one of the options for '+
             ' data quality')

    ############################################################################################################# 
    # PLOT TIME SERIES 
    ############################################################################################################# 

    ax.plot(xtime,ts['Value'],'o-',markersize=0.5,c='tab:blue',lw=1)

    if incl_tl == True:

        # Determine years for trendline
        tl_syr = xtime.dt.year[0] if tl_syr == 'Start' else tl_syr
        tl_eyr = xtime.iloc[-1].year if tl_eyr == 'End' else tl_eyr

        # Extract subset of variables based on tl_syr/tl_eyr
        xtime_tl = xtime.loc[xtime.between(pd.to_datetime(str(tl_syr)+'-01-01'),
                                           pd.to_datetime(str(tl_eyr)+'-01-01'))].reset_index(drop=True)
        ts_tl = ts['Value'].loc[ts['Year'].between(int(tl_syr),int(tl_eyr))].reset_index(drop=True)

        # Account for NaNs when calculating polyfit
        ifinite = np.isfinite(np.array(xtime_tl)) & np.isfinite(np.array(ts_tl))
        m,b = np.polyfit(np.arange(len(xtime_tl))[ifinite],np.array(ts_tl)[ifinite],1)
        trendline = pd.Series(m * np.arange(len(xtime_tl)) + b)

        # Plot trendline and display slope as text on figure
        ax.plot(xtime_tl,trendline,'-',c='k',lw=0.5)
        sign = '+' if m > 0 else ''
        ax.text(xtime_tl.iloc[-1]+pd.Timedelta(days=365),trendline.iloc[-1],sign+str(round(m,4))+' in/yr',
                fontsize=5,bbox=dict(boxstyle='square',pad=0.1,edgecolor='none',facecolor='w'))

    ############################################################################################################# 
    # Features to include? Can toggle on and off in parameters
    ############################################################################################################# 

    if incl_map != 'False':
        bbox_to_anchor = (0,0,1,0.94) if incl_map == 'True (right)' else (0,0,0.15,0.94)
        inset_map(ax=ax,meta=meta,var=var,width=0.7,height=0.8,markercolor='k',slat=slat,nlat=nlat,
                  wlon=wlon,elon=elon,bbox_to_anchor=bbox_to_anchor,lbl_buff=lbl_buff,
                  proj=cartopy.crs.PlateCarree(),ext_buff=ext_buff,img_tile=img_tile)

    ############################################################################################################# 
    # Title and text
    ############################################################################################################# 

    ax.text(1,0.015,r'$\bf{DATA:}$ NOAA ACIS (http://data.rcc-acis.org) '+
                   r' $\bf{IMAGE:}$ Alex Thompson (@ajtclimate)',ha='right',fontsize=5,transform=ax.transAxes)
    season = f'{month1}-{month2}' if len(monthi) < 12 and month1 != month2 else (
                                                                        month1 if month1 == month2 else 'Annual')
    ax.set_title(season+' Daily Rainfall in '+location_name,loc='center',fontsize=14,pad=5,weight='bold');
    if method == 'rx1day-max':
       method_text = "Maximum individual station's Rx1day within the bounding box"
    if method == 'rx1day-mean':
       method_text = "Mean Rx1day for all stations within the bounding box"
    if method == 'alldays-mean':
       method_text = "Mean rainfall for all days from stations within bounding box"
    if method == 'raindays-mean':
       method_text = "Mean rainfall for rain days (>0) from stations within bounding box"
    ax.text(0.5,0.95,method_text,fontsize=9,ha='center',transform=ax.transAxes)

    ############################################################################################################# 
    # Axes specs 
    ############################################################################################################# 

    ax.set_ylabel('inches')
    ax.get_xaxis().set_major_locator(mpl.dates.YearLocator(base=xmajtick))
    ax.get_xaxis().set_minor_locator(mpl.dates.YearLocator(base=xmintick))
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(ymajtick))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(ymintick))
    ax.grid(alpha=0.05)
    ax.set_ylim([np.nanmin(ts['Value'])-minbuff,np.nanmax(ts['Value'])+maxbuff]);
    ax.spines[['right','top']].set_visible(False)

    return fig, ts

#================================================================================================================
# timeseries_snow_plot 
#================================================================================================================
 
def timeseries_snow_plot(var,meta,location_name,nlat,slat,wlon,elon,month1,month2,num_days,num_mons,num_stns,
                         method,incl_tl,tl_syr,tl_eyr,minbuff,maxbuff,ymajtick,ymintick,xmajtick,xmintick,
                         incl_map,img_tile,lbl_buff,ext_buff):
        
    ############################################################################################################# 
    # Convert months string into list of months as integers
    #############################################################################################################

    # Lists of month strings
    month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    mon1 = month_names[month_names.index(month1):]      # all elements to the right (inclusive) of month1
    mon2 = month_names[:(month_names.index(month2)+1)]  # all elements to the left (inclusive) of month 2

    # Combine lists of months to create single list 
    if [i for i in mon1 if i in mon2] != []:  # there is overlap between lists
        mon_str = [i for i in mon1 if i in mon2]
    else:                                     # there is no overlap between lists
        mon_str = mon1 + mon2

    # Convert strings to integers
    monthi = [month_names.index(i)+1 for i in mon_str]

    ############################################################################################################# 
    # Create time series variable and apply data quality filters 
    #############################################################################################################

    # Mask var based on data quality standards (num_days, num_mons, num_stns)
    var_filt = var.copy()

    # Add 'Year' and 'Month' to filter
    if 'Year' not in var_filt.columns and 'Month' not in var_filt.columns:
        var_filt.insert(0,'Year',var_filt['Date'].dt.year),var_filt.insert(1,'Month',var_filt['Date'].dt.month)

    months_that_pass = var_filt.groupby(['Year','Month']).apply(lambda x: x.iloc[:,3:].count()) >= num_days
    years_that_pass = months_that_pass.groupby(level='Year').sum() >= num_mons
    stns_that_pass = years_that_pass.sum(axis=1) >= num_stns

    # Apply data quality standards to year's average value
    var_mask = var.copy()
    var_mask.loc[var_mask['Date'].dt.year.isin(list(stns_that_pass[stns_that_pass == False].index)),:] = np.nan
    var_mask['Date'] = var['Date']

    # dataframe is masked by this line, next lines are to decide which method to use

    # Determine which method to plot: rx1day methods
    if method == 'rx1day-max':
        var_my = bbox_max_my(var_mask)
        ts_pre = var_my.iloc[:,1:].loc[var_my['Month'].isin(monthi)].max()
    if method == 'rx1day-mean':
        # This way works but is slow - try to speed it up
        print('This method may take a few minutes...')
        warnings.filterwarnings('ignore',category=RuntimeWarning)
        ts_pre_col = pd.DataFrame({'Year':var['Date'].dt.year.unique()}) 
        for c in var_mask.columns[1:]:
            var_my_by_col = bbox_max_my(pd.DataFrame({'Date':var_mask['Date'],c:var_mask[c]}))
            ts_pre_col[c] = np.nanmax(var_my_by_col.iloc[:,1:].loc[var_my_by_col['Month'].isin(monthi)],axis=0)
        ts_pre = pd.Series(np.nanmean(ts_pre_col.iloc[:,1:],axis=1),index=np.array(ts_pre_col['Year']).flatten())

    # Determine which method to plot: region mean methods
    if method == 'alldays-mean':  # first part
        var_my = bbox_avg_my(var_mask)
    if method == 'snowdays-mean': # first part
        var_mask_snowdays = var_mask[[col for col in var_mask.columns if col != 'Date']].applymap(
                             lambda x: x if x > 0.00001 else np.nan) # set 0.'s and trace vals to NaN
        var_mask_snowdays['Date'] = var_mask['Date'] # add 'Date' back in for bbox_avg_my
        var_my = bbox_avg_my(var_mask_snowdays)
        
    if method == 'alldays-mean' or method == 'snowdays-mean': # second part
        mnly_vals = var_my.iloc[:,1:].loc[var_my['Month'].isin(monthi)]
        mnly_wgts = np.array([0.08493151,0.076712325,0.08493151,0.08219178,0.08493151,0.08219178,
                              0.08493151,0.08493151, 0.08219178,0.08493151,0.08219178,0.08493151])
        wgts = mnly_wgts if len(monthi) == 12 else mnly_wgts[[m-1 for m in monthi]]/np.sum(
                                                                           mnly_wgts[[m-1 for m in monthi]])
        ts_pre = pd.Series(index=mnly_vals.columns,dtype='float')
        for i, c in enumerate(mnly_vals.columns):
            if mnly_vals[c].isna().any(): # if any of the monthly values is NaN
               ts_pre.iloc[i] = np.nan
            else:
               ts_pre.iloc[i] = (mnly_vals[c]*wgts).sum() / wgts.sum()
            
    # Remove NaN values
    ts_pre = ts_pre.loc[str(ts_pre.first_valid_index()):str(ts_pre.last_valid_index())]
    ts = pd.DataFrame({'Year':np.array(ts_pre.index,dtype=int),'Value':ts_pre.reset_index(drop=True)})
    
    ############################################################################################################# 
    # Define figure 
    ############################################################################################################# 

    fig, ax = plt.subplots(figsize=[8,4],dpi=300)

    # Define x-axis years
    try:
       xtime = pd.Series(pd.date_range(start=str(ts['Year'].iloc[0])+'-01-01',
                                         end=str(ts['Year'].iloc[-1])+'-01-01',freq='YS'))
    except IndexError:
       print('ERROR: No data exists at this high a data quality standard. Reduce one of the options for '+
             ' data quality')

    ############################################################################################################# 
    # PLOT TIME SERIES 
    ############################################################################################################# 

    ax.plot(xtime,ts['Value'],'o-',markersize=0.5,c='darkcyan',lw=1)

    if incl_tl == True:

        # Determine years for trendline
        tl_syr = xtime.dt.year[0] if tl_syr == 'Start' else tl_syr
        tl_eyr = xtime.iloc[-1].year if tl_eyr == 'End' else tl_eyr

        # Extract subset of variables based on tl_syr/tl_eyr
        xtime_tl = xtime.loc[xtime.between(pd.to_datetime(str(tl_syr)+'-01-01'),
                                           pd.to_datetime(str(tl_eyr)+'-01-01'))].reset_index(drop=True)
        ts_tl = ts['Value'].loc[ts['Year'].between(int(tl_syr),int(tl_eyr))].reset_index(drop=True)

        # Account for NaNs when calculating polyfit
        ifinite = np.isfinite(np.array(xtime_tl)) & np.isfinite(np.array(ts_tl))
        m,b = np.polyfit(np.arange(len(xtime_tl))[ifinite],np.array(ts_tl)[ifinite],1)
        trendline = pd.Series(m * np.arange(len(xtime_tl)) + b)

        # Plot trendline and display slope as text on figure
        ax.plot(xtime_tl,trendline,'-',c='k',lw=0.5)
        sign = '+' if m > 0 else ''
        ax.text(xtime_tl.iloc[-1]+pd.Timedelta(days=365),trendline.iloc[-1],sign+str(round(m,4))+' in/yr',
                fontsize=5,bbox=dict(boxstyle='square',pad=0.1,edgecolor='none',facecolor='w'))

    ############################################################################################################# 
    # Features to include? Can toggle on and off in parameters
    ############################################################################################################# 

    if incl_map != 'False':
        bbox_to_anchor = (0,0,1,0.94) if incl_map == 'True (right)' else (0,0,0.15,0.94)
        inset_map(ax=ax,meta=meta,var=var,width=0.7,height=0.8,markercolor='k',slat=slat,nlat=nlat,
                  wlon=wlon,elon=elon,bbox_to_anchor=bbox_to_anchor,lbl_buff=lbl_buff,
                  proj=cartopy.crs.PlateCarree(),ext_buff=ext_buff,img_tile=img_tile)

    ############################################################################################################# 
    # Title and text
    ############################################################################################################# 

    ax.text(1,0.015,r'$\bf{DATA:}$ NOAA ACIS (http://data.rcc-acis.org) '+
                   r' $\bf{IMAGE:}$ Alex Thompson (@ajtclimate)',ha='right',fontsize=5,transform=ax.transAxes)
    season = f'{month1}-{month2}' if len(monthi) < 12 and month1 != month2 else (
                                                                        month1 if month1 == month2 else 'Annual')
    ax.set_title(season+' Daily Snowfall in '+location_name,loc='center',fontsize=14,pad=5,weight='bold');
    if method == 'rx1day-max':
       method_text = "Maximum individual station's Rx1day within the bounding box"
    if method == 'rx1day-mean':
       method_text = "Mean Rx1day for all stations within the bounding box"
    if method == 'alldays-mean':
       method_text = "Mean rainfall for all days from stations within bounding box"
    if method == 'raindays-mean':
       method_text = "Mean rainfall for rain days (>0) from stations within bounding box"
    ax.text(0.5,0.95,method_text,fontsize=9,ha='center',transform=ax.transAxes)

    ############################################################################################################# 
    # Axes specs 
    ############################################################################################################# 

    ax.set_ylabel('inches')
    ax.get_xaxis().set_major_locator(mpl.dates.YearLocator(base=xmajtick))
    ax.get_xaxis().set_minor_locator(mpl.dates.YearLocator(base=xmintick))
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(ymajtick))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(ymintick))
    ax.grid(alpha=0.05)
    ax.set_ylim([np.nanmin(ts['Value'])-minbuff,np.nanmax(ts['Value'])+maxbuff]);
    ax.spines[['right','top']].set_visible(False)

    return fig, ts

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
# SPATIAL MAP PLOTS
#
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#================================================================================================================
# spatialmap_tmax_plot 
#================================================================================================================


#================================================================================================================
# spatialmap_pcpn_plot 
#================================================================================================================

def spatialmap_pcpn_plot(var,meta,location_name,nlat,slat,wlon,elon,timespan,stats,incl_loc,stns_col,
                         dot_size,cmap,incl_ticks,nlatbuf,slatbuf,wlonbuf,elonbuf,latstride,lonstride,
                         # Lots of ways to input date range, if none specified then error message will appear
                         sdate=None,edate=None,      # straightforward starting and ending date
                         sngl_md=None,sngl_yr=None,  # single day query in parts for ipyw
                         mult_md1=None,mult_yr1=None,mult_md2=None,mult_yr2=None # multi day query in parts
                         ):
    
    ############################################################################################################# 
    # Perform json request for griddata
    ############################################################################################################# 
    
    # Determine input date range - this pieces together input parameters specified when calling function
    if timespan == 'Single Day':
        if sdate is not None:
            sdate, edate = sdate, sdate # set sdate and edate as same
        elif sngl_md is not None and sngl_yr is not None:
            sdate = str(sngl_yr)+'-'+str(sngl_md)
            edate = sdate
    if timespan == 'Multiple Days':
        if sdate is not None and edate is not None:
            sdate, edate = sdate, edate # pass sdate and edate through
        elif mult_md1 is not None and mult_yr1 is not None and mult_md2 is not None and mult_yr2 is not None:
            sdate, edate = str(mult_yr1)+'-'+str(mult_md1), str(mult_yr2)+'-'+str(mult_md2)
    
    # Perform json request
    try: 
        params = {'bbox':[wlon-wlonbuf,slat-slatbuf,elon+elonbuf,nlat+nlatbuf],'sdate':sdate,'edate':edate,
                  'grid':'1','elems':[{'name':'pcpn'}],'meta':'ll'} 
        json_response = urllib.request.urlopen(urllib.request.Request('http://data.rcc-acis.org/GridData',
                                urllib.parse.urlencode({'params':json.dumps(params)}).encode('utf-8'),
                                                       {'Accept':'application/json'})).read()
    except:
        print('Error in choosing date range to query. Check "timespan" and date range input parameters.')
    raw = json.loads(json_response)

    ############################################################################################################# 
    # Process griddata
    ############################################################################################################# 
    
    # Variables (regardless of time length)
    lats  = np.unique(np.array(raw['meta']['lat']).flatten())
    lons  = np.unique(np.array(raw['meta']['lon']).flatten())

    # Process based on length of days queried
    if timespan == 'Single Day':
        # Only one day is queried
        griddata = xr.DataArray(np.array(raw['data'][0][1]).flatten().reshape((len(lats),len(lons))),
                                dims=['lat','lon'],coords=dict(lat=lats,lon=lons))
    elif timespan == 'Multiple Days':
        # More than one day is queried
        date_str = list(dict(raw['data']).keys())                          # finds unique dates as strings
        times = pd.date_range(start=date_str[0],end=date_str[-1],freq='D') # converts strings to datetime64[ns]
        datatime = xr.DataArray(None,dims=['time','lat','lon'],coords=dict(time=times,lat=lats,lon=lons)
                                ).astype(float)
        for d in range(len(times)): # loops through each queried day
            datatime[d,:,:] = np.array(raw['data'][d][1]).flatten().reshape((len(lats),len(lons)))
        # Stats for multiple days
        if stats == 'Mean':
            griddata = datatime.mean(dim='time')
        elif stats == 'Sum':
            griddata = datatime.sum(dim='time')

    # Set missing values and negative values to NaN 
    griddata = griddata.where(griddata != -999, np.nan)
    
    ############################################################################################################# 
    # Define figure and color bars
    ############################################################################################################# 
    
    # Define figure 
    projection = cartopy.crs.PlateCarree() # can try to add more projections later
    fig, ax = plt.subplots(figsize=(8,6),dpi=300,subplot_kw={'projection':projection})
    
    # Define color bar (must unregister before registering)
    white_color = np.array([1.0, 1.0, 1.0, 1.0])  # RGBA values for white
    if cmap == 'Haxby':
        mpl.colormaps.unregister('cmp_haxby_r')
        colorp = cmaps.cmp_haxby_r
    if cmap == 'Blues':
        mpl.colormaps.unregister('MPL_Blues')
        MPL_Blues = cmaps.MPL_Blues(np.arange(10,129)) # 128 total colors
        colorp = mpl.colors.LinearSegmentedColormap.from_list('name', np.vstack([white_color,MPL_Blues]))
    if cmap == 'GreenBlue':
        mpl.colormaps.unregister('MPL_GnBu')
        MPL_GnBu = cmaps.MPL_GnBu(np.arange(30,128)) # 128 total colors
        colorp = mpl.colors.LinearSegmentedColormap.from_list('name', np.vstack([white_color,MPL_GnBu]))

    #############################################################################################################   
    # Plotting contours 
    #############################################################################################################       
    
    # Determine colorbar spacing values
    minval = 0. # colorbar starts at 0
    maxval = math.ceil(0.8*griddata.max()) if griddata.max() > 0. else 1. # colorbar ends at 80% of max value
    tksp = 0.5 if maxval <= 5. else (1. if maxval <= 15 else 5.) # colorbar ticks 
    sp50 = (maxval-minval) / 50 # unscaled colobar spacing value
    # Algorithm for keeping colorbar spacing value within confines of ticks
    if len(str(sp50)[str(sp50).index('.') + 1:]) > 1:
        z,y = str(sp50)[-1], str(sp50)[-2]
        add = 0 if int(z) < 5 else 1
        newy = str(int(str(sp50)[-2])+add) 
        spval = float(str(str(sp50)[0:-2])+str(newy)+'0')    
    else: spval = sp50
    if spval <= 0.: spval = 0.1 # spval cannot be zero or negative
    
    # Make contour plot
    cntr = griddata.plot.contourf(ax=ax,transform=projection,add_colorbar=False,add_labels=False,extend='max',
                                  cmap=colorp,levels=np.arange(minval,maxval+spval,spval))

    # Plotting color bar
    cbar_pad = 0.1 if incl_ticks == True else 0.02
    cbar = fig.colorbar(cntr,ax=ax,orientation='horizontal',shrink=0.7,ticks=mpl.ticker.MultipleLocator(tksp),
                        pad=cbar_pad,label='inches',extend='max',spacing='proportional')
    
    # Specifications for map 
    ax.set_extent([wlon-wlonbuf,elon+elonbuf,slat-slatbuf,nlat+nlatbuf])
    ax.add_feature(cartopy.feature.STATES,linewidths=0.5)
    ax.add_feature(cartopy.feature.COASTLINE,linewidths=0.5)
    ax.add_patch(mpl.patches.Rectangle((wlon,slat),abs(wlon)-abs(elon),abs(nlat)-abs(slat),linestyle='-',
                                       facecolor='none',edgecolor='k',linewidth=1,zorder=100))

    #############################################################################################################   
    # Plotting stations 
    #############################################################################################################   

    if incl_loc == True:
        ax.scatter(meta['lon'],meta['lat'],c=stns_col,s=dot_size,zorder=100)
        # Figuring this out later -------------------------------------------------------------------------------
        #if stns_col == 'Colored by value':
        #    # Find values from var
        #    #sdate, edate = '2022-07-26','2022-07-28'
        #    #print(var.loc[var['Date'].between(pd.to_datetime(sdate),pd.to_datetime(edate))])
        #    if timespan == 'Single Day':
        #        stn_vals = var.iloc[:,1:].loc[var['Date'] == pd.to_datetime(sdate)].values.flatten()
        #    ax.scatter(meta['lon'],meta['lat'],c=stn_vals,cmap=colorp,s=dot_size,edgecolors='k',lw=0.5)
        # Figuring this out later -------------------------------------------------------------------------------
    
    #############################################################################################################   
    # Sets map ticks and labels 
    #############################################################################################################   

    if incl_ticks == True:
        gv.set_axes_limits_and_ticks(ax,xlim=(wlon-wlonbuf,elon+elonbuf),ylim=(slat-slatbuf,nlat+nlatbuf),
                                     xticks=np.linspace(-180.,180.,int((360/lonstride)+1)),
                                     yticks=np.linspace(-90.,90.,int((180/latstride)+1)),
                                     xticklabels=[],yticklabels=[])
        gv.add_major_minor_ticks(ax,x_minor_per_major=2,y_minor_per_major=2)
        ax.tick_params(which='major',length=4)
        ax.tick_params(which='minor',length=2)
        gl = ax.gridlines(crs=projection,draw_labels=True,alpha=0.0,color=None,
                          xlim=(wlon-wlonbuf,elon+elonbuf),ylim=(slat-slatbuf,nlat+nlatbuf))
        gl.xlocator = mpl.ticker.MultipleLocator(lonstride)
        gl.ylocator = mpl.ticker.MultipleLocator(latstride)
        gl.top_labels = False
        gl.bottom_labels = True
        gl.left_labels = True
        gl.right_labels = False
        gl.xpadding = 10
        gl.ypadding = 10
        gl.xlabel_style = {'size': 12}
        gl.ylabel_style = {'size': 12}

    #############################################################################################################   
    # Title 
    #############################################################################################################   

    titletxt = stats+' of 24-hr rainfall from '+sdate+' to '+edate if timespan == 'Multiple Days' else \
               '24-hr rainfall on '+sdate
    ax.set_title(titletxt,pad=10,fontsize=12)

