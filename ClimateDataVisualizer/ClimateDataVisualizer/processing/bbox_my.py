#######################################################################################################
#
# Functions for processing variables queried from a bounding box and returning as my (month of year)
#
#######################################################################################################

import numpy as np
import pandas as pd

#======================================================================================================
# Read in Pandas output from stndata function and return as Pandas DataFrame of months by year
#======================================================================================================

def bbox_max_my(df: pd.DataFrame):

    '''
    Reads in Pandas dataframe output from stndata functions (includes Date and stations as columns) 
    and calculates the maximum individual station value across all stations within the bounding box
    for every month of the year and for every year in the historical period. The final output 
    dataframe has month of year as rows and each year as a separate column.

    Parameters
    -------------
    df
     class: 'pandas.DataFrame', Pandas df output from stndata function. Must contain 'Date' as 
                                left-most column.

    '''

    #------------------------------------------------------------------------------------------------
    # 
    #------------------------------------------------------------------------------------------------

    # Initialize variable
    df_my = pd.DataFrame({'Month': np.arange(1,13)})

    # Loop through years and calculate maximum individual station value for every month of that year
    for yr in range(df['Date'].min().year,df['Date'].max().year+1):

     # Extract max for each month for the given year
     yr_df_init = pd.DataFrame({'Val': df.drop('Date',axis=1).loc[df['Date'].dt.year == yr].max(
                                                                   axis=1).reset_index(drop=True)})
    
     # Add 'Year' and 'Month' 
     yr_df_init['Year'] = df['Date'].loc[df['Date'].dt.year == yr].reset_index(drop=True).dt.year
     yr_df_init['Month'] = df['Date'].loc[df['Date'].dt.year == yr].reset_index(drop=True).dt.month
    
     # Use groupby to find the max for each month and save to df_my
     yr_df_vals = yr_df_init.groupby(['Year', 'Month'])['Val'].max().values

     # Data is full year
     if len(yr_df_vals) == 12:
       yr_df = yr_df_vals

     # Data for beginning of year only - i.e., if last year in record does not end at Dec. 31
     if yr == df['Date'].max().year and df['Date'].loc[df['Date'].dt.year == yr].dt.month.iloc[-1] != 12 or \
                                        df['Date'].loc[df['Date'].dt.year == yr].dt.day.iloc[-1] != 31:
        yr_df = pd.Series(pd.concat([pd.Series(yr_df_vals),pd.Series([np.nan]*(12-len(yr_df_vals)))],
                                    axis=0).reset_index(drop=True),dtype=float)

     # Data for end of year only - i.e., if first year in record does not start on Jan. 1
     if yr == df['Date'].min().year and df['Date'].loc[df['Date'].dt.year == yr].dt.month.iloc[0] != 1 or \
                                        df['Date'].loc[df['Date'].dt.year == yr].dt.day.iloc[0] != 1:
        yr_df = pd.Series(pd.concat([pd.Series([np.nan]*(12-len(yr_df_vals))),pd.Series(yr_df_vals)],
                                    axis=0).reset_index(drop=True),dtype=float)

     df_my[str(yr)] = yr_df

    #------------------------------------------------------------------------------------------------
    # Return final variable 
    #------------------------------------------------------------------------------------------------

    return df_my

def bbox_min_my(df: pd.DataFrame):

    '''
    Reads in Pandas dataframe output from stndata functions (includes Date and stations as columns) 
    and calculates the minimum individual station value across all stations within the bounding box
    for every month of the year and for every year in the historical period. The final output 
    dataframe has month of year as rows and each year as a separate column.

    Parameters
    -------------
    df
     class: 'pandas.DataFrame', Pandas df output from stndata function. Must contain 'Date' as 
                                left-most column.

    '''

    #------------------------------------------------------------------------------------------------
    # 
    #------------------------------------------------------------------------------------------------

    # Initialize variable
    df_my = pd.DataFrame({'Month': np.arange(1,13)})

    # Loop through years and calculate minimum individual station value for every month of that year
    for yr in range(df['Date'].min().year,df['Date'].max().year+1):

     # Extract min for each month for the given year
     yr_df_init = pd.DataFrame({'Val': df.drop('Date',axis=1).loc[df['Date'].dt.year == yr].min(
                                                                   axis=1).reset_index(drop=True)})

     # Add 'Year' and 'Month' 
     yr_df_init['Year'] = df['Date'].loc[df['Date'].dt.year == yr].reset_index(drop=True).dt.year
     yr_df_init['Month'] = df['Date'].loc[df['Date'].dt.year == yr].reset_index(drop=True).dt.month

     # Use groupby to find the min for each month and save to df_my
     yr_df_vals = yr_df_init.groupby(['Year', 'Month'])['Val'].min().values

     # Data is full year
     if len(yr_df_vals) == 12:
       yr_df = yr_df_vals

     # Data for beginning of year only - i.e., if last year in record does not end at Dec. 31
     if yr == df['Date'].max().year and df['Date'].loc[df['Date'].dt.year == yr].dt.month.iloc[-1] != 12 or \
                                        df['Date'].loc[df['Date'].dt.year == yr].dt.day.iloc[-1] != 31:
        yr_df = pd.Series(pd.concat([pd.Series(yr_df_vals),pd.Series([np.nan]*(12-len(yr_df_vals)))],
                                    axis=0).reset_index(drop=True),dtype=float)

     # Data for end of year only - i.e., if first year in record does not start on Jan. 1
     if yr == df['Date'].min().year and df['Date'].loc[df['Date'].dt.year == yr].dt.month.iloc[0] != 1 or \
                                        df['Date'].loc[df['Date'].dt.year == yr].dt.day.iloc[0] != 1:
        yr_df = pd.Series(pd.concat([pd.Series([np.nan]*(12-len(yr_df_vals))),pd.Series(yr_df_vals)],
                                    axis=0).reset_index(drop=True),dtype=float)

     df_my[str(yr)] = yr_df

    #------------------------------------------------------------------------------------------------
    # Return final variable 
    #------------------------------------------------------------------------------------------------

    return df_my



def bbox_avg_my(df: pd.DataFrame):

    '''
    Reads in Pandas dataframe output from stndata functions (includes Date and stations as columns) 
    and calculates the average value that integrates all stations within the bounding box
    for every month of the year and for every year in the historical period. The final output 
    dataframe has month of year as rows and each year as a separate column.

    Parameters
    -------------
    df
     class: 'pandas.DataFrame', Pandas df output from stndata function. Must contain 'Date' as 
                                left-most column.

    '''

    #------------------------------------------------------------------------------------------------
    # 
    #------------------------------------------------------------------------------------------------

    # Initialize variable
    df_my = pd.DataFrame({'Month': np.arange(1,13)})

    # Loop through years and calculate mean value for every month of that year
    for yr in range(df['Date'].min().year,df['Date'].max().year+1):

     # Extract mean for each month for the given year
     yr_df_init = pd.DataFrame({'Val': df.drop('Date',axis=1).loc[df['Date'].dt.year == yr].mean(
                                                                   axis=1).reset_index(drop=True)})

     # Add 'Year' and 'Month' 
     yr_df_init['Year'] = df['Date'].loc[df['Date'].dt.year == yr].reset_index(drop=True).dt.year
     yr_df_init['Month'] = df['Date'].loc[df['Date'].dt.year == yr].reset_index(drop=True).dt.month

     # Use groupby to find the mean for each month and save to df_my
     yr_df_vals = yr_df_init.groupby(['Year', 'Month'])['Val'].mean().values

     # Data is full year
     if len(yr_df_vals) == 12:
       yr_df = yr_df_vals

     # Data for beginning of year only - i.e., if last year in record does not end at Dec. 31
     if yr == df['Date'].max().year and df['Date'].loc[df['Date'].dt.year == yr].dt.month.iloc[-1] != 12 or \
                                        df['Date'].loc[df['Date'].dt.year == yr].dt.day.iloc[-1] != 31:
        yr_df = pd.Series(pd.concat([pd.Series(yr_df_vals),pd.Series([np.nan]*(12-len(yr_df_vals)))],
                                    axis=0).reset_index(drop=True),dtype=float)

     # Data for end of year only - i.e., if first year in record does not start on Jan. 1
     if yr == df['Date'].min().year and df['Date'].loc[df['Date'].dt.year == yr].dt.month.iloc[0] != 1 or \
                                        df['Date'].loc[df['Date'].dt.year == yr].dt.day.iloc[0] != 1:
        yr_df = pd.Series(pd.concat([pd.Series([np.nan]*(12-len(yr_df_vals))),pd.Series(yr_df_vals)],
                                    axis=0).reset_index(drop=True),dtype=float)

     df_my[str(yr)] = yr_df

    #------------------------------------------------------------------------------------------------
    # Return final variable 
    #------------------------------------------------------------------------------------------------

    return df_my


