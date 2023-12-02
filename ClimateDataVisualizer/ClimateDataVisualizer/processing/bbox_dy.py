#######################################################################################################
#
# Functions for processing variables queried from a bounding box and returning as dy (day of year)
#
#######################################################################################################

import numpy as np
import pandas as pd
import warnings

#######################################################################################################
#
# AVERAGING STATIONS IN BBOX FUNCTIONS
#
#######################################################################################################

#======================================================================================================
# Read in Pandas output from stndata function and return as Pandas DataFrame of days by year
#======================================================================================================

def bbox_avg_dy(df: pd.DataFrame, leap: bool = False):

    '''
    Reads in Pandas dataframe output from stndata functions (includes Date and stations as columns) 
    and calculates the average across all stations within the bounding box for every day of the year
    and for every year in the historical period. The final output dataframe has day of year as rows
    and each year as a separate column. 
    
    Parameters
    -------------
    df
     class: 'pandas.DataFrame', Pandas df output from stndata function. Must contain 'Date' as 
                                left-most column.

    leap
     class: 'bool', If True, includes leap days as a day of the year row. 
                    This script can currently only support leap = False. 

    '''
    #------------------------------------------------------------------------------------------------
    # Define time indexing arrays
    #------------------------------------------------------------------------------------------------

    # List of leap years 1800 - 2100
    leapyears = [1800 + i * 4 for i in range((2100 - 1800) // 4 + 1)]

    # Create arrays for month and day
    if leap == False: # Feb 29 not included
     month = np.repeat(np.arange(1,13), [31,28,31,30,31,30,31,31,30,31,30,31])
     day = np.concatenate([np.arange(1,m+1) for m in [31,28,31,30,31,30,31,31,30,31,30,31]])
    elif leap == True: # Feb 29 is included
     month = np.repeat(np.arange(1,13), [31,29,31,30,31,30,31,31,30,31,30,31])
     day = np.concatenate([np.arange(1,m+1) for m in [31,29,31,30,31,30,31,31,30,31,30,31]])

    #------------------------------------------------------------------------------------------------
    # Variables: average all stations by year for every day of the year
    #------------------------------------------------------------------------------------------------

    # Initialize variable                                     
    df_dy = pd.DataFrame({'month': month, 'day': day})

    # Loop through years and extract average for every day of that year
    for yr in range(df['Date'].min().year,df['Date'].max().year+1):
     
     # Extract mean for each day for the given year (axis=1 takes mean for each day across all stations)    
     yr_df_init = df.drop('Date',axis=1).loc[df['Date'].dt.year == yr].mean(axis=1).reset_index(drop=True)

     # If not a full year, fill in remaining days with NaN
     warnings.simplefilter(action='ignore',category=FutureWarning) # ignore future warning about pd.concat

     # Data for end of year only - i.e., if first year in record does not start on Jan. 1
     if yr == df['Date'].min().year and df['Date'].loc[df['Date'].dt.year == yr].dt.month.iloc[0] != 1 or \
                                        df['Date'].loc[df['Date'].dt.year == yr].dt.day.iloc[0] != 1:
       if yr not in leapyears: # fill in to 365 days
          yr_df_init = pd.Series(pd.concat([pd.Series([np.nan]*(365-len(yr_df_init))),yr_df_init],axis=0
                                 ).reset_index(drop=True),dtype=float)
       elif yr in leapyears: # fill in to 366 days
          yr_df_init = pd.Series(pd.concat([pd.Series([np.nan]*(366-len(yr_df_init))),yr_df_init],axis=0
                                 ).reset_index(drop=True),dtype=float)

     # Data for beginning of year only - i.e., if last year in record does not end at Dec. 31
     if yr == df['Date'].max().year and df['Date'].loc[df['Date'].dt.year == yr].dt.month.iloc[-1] != 12 or \
                                        df['Date'].loc[df['Date'].dt.year == yr].dt.day.iloc[-1] != 31:
        if yr not in leapyears: # fill in to 365 days
           yr_df_init = pd.Series(pd.concat([yr_df_init,pd.Series([np.nan]*(365-len(yr_df_init)))],axis=0,
                                  ).reset_index(drop=True),dtype=float)
        elif yr in leapyears: # fill in to 366 days
           yr_df_init = pd.Series(pd.concat([yr_df_init,pd.Series([np.nan]*(366-len(yr_df_init)))],axis=0
                                  ).reset_index(drop=True),dtype=float)

     # Manage if allowing leap days or not
     if leap == False: 

        # If year is leap year, average Feb. 29 (index 59) into Feb. 28 (index 58)
        if yr in leapyears and len(yr_df_init) == 366: # leap year with 366 values 
           # Remove leap day
           yr_df = yr_df_init.drop(59).reset_index(drop=True)
           # Average Feb. 29 and Feb. 28
           warnings.filterwarnings('ignore', category=RuntimeWarning) # mute 'mean of empty slice'
           yr_df[58] = np.nanmean([yr_df[58],yr_df_init[59]])
        # If year is not leap year, do nothing
        else: # non-leap year
           yr_df = yr_df_init

     elif leap == True:

        # If year is not a leap year, add NaN to Feb. 29
        if yr not in leapyears: 
           # Add NaN for Feb 29  
           yr_df = pd.Series([*yr_df_init[:59], np.nan, *yr_df_init[59:]])
        else: # leap year 
           yr_df = yr_df_init

        # Check for leap years not recorded in original data
        if yr in leapyears and len(yr_df) == 365:
           yr_df = pd.Series([*yr_df_init[:59], np.nan, *yr_df_init[59:]])

     # Pass along values
     df_dy[str(yr)] = yr_df.values

    #------------------------------------------------------------------------------------------------
    # Return final variable 
    #------------------------------------------------------------------------------------------------

    return df_dy

