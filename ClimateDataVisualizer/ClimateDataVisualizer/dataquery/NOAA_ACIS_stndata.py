#######################################################################################################
#
# Functions for querying NOAA ACIS station data from https://xmacis.rcc-acis.org/ 
#
#######################################################################################################

import numpy as np
import pandas as pd
import json, urllib
from warnings import simplefilter
from ClimateDataVisualizer.dataquery import NOAA_ACIS_stnmeta as stnmeta
from ClimateDataVisualizer.dataquery import NOAA_ACIS_stndata as stndata

######################################################################################################
#
# SINGLE STATION QUERY FUNCTION
#
######################################################################################################

#======================================================================================================
# Query daily data from a single station from NOAA ACIS and returns as float array      
#======================================================================================================

def singlestn_daily(elem: str, sid: str, sdate: str, edate: str,

                    # Optional parameters for all elems
                    M: float = float('NaN'),

                    # Optional parameters for elems 'pcpn' and 'snow'
                    T: float = 0.00001, mdr: int = 50, mdr_opt: str = 'avg', 
                    mdr_A: str = 'equal', mdr_S: str = '0',

                    # Optional parameters for printing results
                    print_results: bool = True, print_md: bool = True

                    ):

    '''
    Creates float array of daily data from a single station from NOAA ACIS. Requires the station ID 
    (sids) and requested starting date (sdate) and ending date (edate). Find sids, sdate, and edate
    by using metadata query functions in 'query_stnmeta.py' or by using the xmACIS2 site search at:
    https://xmacis.rcc-acis.org/ 

    Required Parameters
    --------------------
    elem
     class: 'string', Single variable element to include. Example: 'maxt'
                      Possible options are 'maxt','mint','avgt','pcpn','snow','snwd'.

    sid
     class: 'string', Station ID, also known as sids. This is required for identifying the station
                      from which data is queried. 

    sdate
     class: 'string', Starting date for queried data in form 'YYYY-DD-MM'.  

    edate 
     class: 'string', Ending date for queried data in form 'YYYY-DD-MM'.

    Optional parameters for all elems
    ----------------------------------
    M                Default = float('NaN')
     class: 'float', Value to which missing values ('M') are converted.

    Optional parameters for elems 'pcpn' and 'snow'
    -----------------------------------------------
    T                Default = 0.00001 
     class: 'float', Value to which trace values ('T') are converted.

    mdr                Default = 50 
     class: 'integer', Multi-day range, the number of days this script will search from S=0 to find
                       the final multi-day even with form '[sum]A'.  

    mdr_opt           Default = 'avg' 
     class: 'string', Option for handling multi-day events. Currently, this script only supports
                      placing the average daily value of the multi-day event into each day within
                      the event (e.g., 3 day event that totaled 0.9 inches, each day's value will
                      equal 0.3 inches).

    mdr_A             Default = 'equal'
     class: 'string', Option for handling special data cases where 'A' exists without a preceding 'S'.
                      Currently, this script only supports 'equal', which sets the daily value equal
                      to the value next to the 'A' (e.g., 2.3A becomes 2.3). These special cases are
                      shown if 'print_result' = True.

    mdr_S             Default = '0' 
     class: 'string', Option for handling special data cases where 'S' exists without a following 'A'.
                      Currently, this script only supports '0', which sets these values to 0. These
                      special cases are shown if 'print_result' = True. 

    Optional parameters for printing results in real-time
    -----------------------------------------------------
    print_results   Default = True
     class: 'bool', Print real-time results of station query to interface.

    print_md        Default = True
     class: 'bool', Print information about multi-day event processing if found while querying data.

    Returns
    ---------------------
    output: class: 'numpy.ndarray'
    '''

    #-------------------------------------------------------------------------------------------------
    # Query raw data from json request    
    #-------------------------------------------------------------------------------------------------

    # Input dictionary of station id, start date, and end date 
    input_dict = {'sid': sid,'elems': elem,'sdate':sdate,'edate':edate}

    # Get json data from url
    json_response = urllib.request.urlopen(urllib.request.Request('http://data.rcc-acis.org/StnData',
                                           urllib.parse.urlencode({'params':json.dumps(input_dict)}
                                           ).encode('utf-8'),{'Accept':'application/json'})).read()
    raw = json.loads(json_response)

    #-------------------------------------------------------------------------------------------------
    # Read in data to pd DataFrame and process missing and trace values
    #-------------------------------------------------------------------------------------------------
    
    # pd.DataFrame named 'Station' contains raw data 
    Station = pd.DataFrame(raw['data'],columns=['Date',elem])
    
    # Set M to specified value 
    Station[elem] = np.where(Station[elem] == 'M', M, Station[elem])

    #-------------------------------------------------------------------------------------------------
    # Further processing if elem is 'pcpn' or 'snow' or 'snwd' 
    #-------------------------------------------------------------------------------------------------

    if elem == 'pcpn' or elem == 'snow' or elem == 'snwd':

     # Set T to specified value
     Station[elem] = np.where(Station[elem] == 'T', T, Station[elem])

     #-------------------------------------------------------------------------------------------------
     # Process multi-day events (i.e., when data shows a value like 'S' ... '2.0A') 
     #-------------------------------------------------------------------------------------------------

     # Process normal multi-day events, where data shows S->A

     for sa in range(len(Station[elem])):
      if Station[elem].iloc[sa] == 'S':
       # First, control for multi-day range (mdr) extending beyond bounds of record
       if (len(Station[elem]) - Station[elem].index[sa]) < mdr:
        for x in range(len(Station[elem]) - Station[elem].index[sa]):
         if ('A' in str(Station[elem].iloc[sa+x])) == True:
          if mdr_opt == 'avg':
           # Set pcpn/snow values from S->A as average of A value across all relevant days
           Station[elem].iloc[sa:sa+x+1] = float(Station[elem].iloc[sa+x].replace('A','')) / (x+1)
          break
       # Next, calculate all other multi-day range (mdr) events 
       else:
        for x in range(mdr):                          # check next n days for the A
         if ('A' in str(Station[elem].iloc[sa+x])) == True:
          if mdr_opt == 'avg':
           # Set pcpn/snow values from S->A as average of A value across all relevant days
           Station[elem].iloc[sa:sa+x+1] = float(Station[elem].iloc[sa+x].replace('A','')) / (x+1)
          break
                         
     # Process where any 'A' values remain, which means there was no 'S' before  

     if Station[elem].str.contains('A').any() == True:
      if mdr_A == 'equal':
         if print_md == True:
          print(sid+' has standalone A, setting equal to that days value')
         Aind = Station[elem].index[Station[elem].str.contains('A') == True].values
         # Manage if the station has more than one of these special data cases
         if len(Aind) > 0:
          for Aelem in range(len(Aind)):
           if print_md == True:
            Adate = pd.date_range(start=sdate,end=edate,freq='D')[Aind][Aelem].date() # find date of standalone
            print(str(Adate)+': '+Station[elem][int(Aind[Aelem])]+'->'+\
                             str(np.float64(Station[elem][int(Aind[Aelem])].replace('A',''))))
           Station[elem][Aind[Aelem]] = np.float64(Station[elem][Aind[Aelem]].replace('A',''))

     # Process where any 'S' values remain, which means there is no 'A' afterwards 

     if Station[elem].str.contains('S').any() == True:
      if print_md == True:   
       print(sid+' has standalone S, setting to 0')
      Sind = Station[elem].index[Station[elem].str.contains('S') == True].values
      # Manage if the station has more than one of these special data cases
      if len(Sind) > 0:
       for Selem in range(len(Sind)):
        if print_md == True:
         Sdate = pd.date_range(start=sdate,end=edate,freq='D')[Sind][Selem].date() # find date of standalone   
         print(str(Sdate)+': '+Station[elem][int(Sind[Selem])]+'->0')
        Station[elem][Sind[Selem]] = 0

    #-------------------------------------------------------------------------------------------------
    # Output final array as a float array
    #-------------------------------------------------------------------------------------------------

    return np.float32(Station[elem])

######################################################################################################
#
# MULTI STATION QUERY FUNCTIONS
#
######################################################################################################

#======================================================================================================
# Query daily data from multiple stations from NOAA ACIS within a specified bounding box, return as 
# Pandas DataFrame with each station represented by a new column      
#======================================================================================================

def bbox_multistn_daily(elem: str, slat: float, nlat: float, wlon: float, elon: float,
                   
                        # Optional parameters for size of data query
                        stn_size: int = 1000,
 
                        # Optional parameters for all elems
                        M: float = float('NaN'),

                        # Optional parameters for elems 'pcpn', 'snow', and 'snwd'
                        T: float = 0.00001, mdr: int = 50, mdr_opt: str = 'avg',
                        mdr_A: str = 'equal', mdr_S: str = '0',

                        # Optional parameters for printing results
                        print_results: bool = True, print_md: bool = True,

                        # Optional parameters for outputing variables to excel
                        stn_excel: bool = False, meta_excel: bool = False,
                        folderpath: str = ''

                        ):

    '''
    Creates Pandas DataFrame for the entire observational record for all stations from NOAA ACIS 
    within a bounded box. Each individual station is represented by a new column. All days where a 
    station did not collect data are set to NaN.  

    Required Parameters
    --------------------
    elem
     class: 'string', Single variable element to include. Example: 'maxt'
                      Possible options are 'maxt','mint','avgt','pcpn','snow','snwd'.

    slat, nlat, wlon, elon
     class: 'float', Bounding latitude and longitude coordinates for querying metadata from all
                     stations within the box. Negative values correspond to °S and °W while positive
                     values correspond to °N and °E. Any number of decimal places may be specified. 
                     Example: slat = 37, nlat = 37.567, wlon = -90.01, elon = -89.5

    Optional parameters for size of data query 
    -------------------------------------------
    stn_size           Default = 1000
     class: 'integer', If the bbox returns more than this many stations, data will not be queried
                       and script will exit.

    Optional parameters for all elems
    ----------------------------------
    M                Default = float('NaN')
     class: 'float', Value to which missing values ('M') are converted.

    Optional parameters for elems 'pcpn', 'snow', and 'snwd'
    ---------------------------------------------------------
    T                Default = 0.00001 
     class: 'float', Value to which trace values ('T') are converted.

    mdr                Default = 50 
     class: 'integer', Multi-day range, the number of days this script will search from S=0 to find
                       the final multi-day even with form '[sum]A'.  

    mdr_opt           Default = 'avg' 
     class: 'string', Option for handling multi-day events. Currently, this script only supports
                      placing the average daily value of the multi-day event into each day within
                      the event (e.g., 3 day event that totaled 0.9 inches, each day's value will
                      equal 0.3 inches).

    mdr_A             Default = 'equal'
     class: 'string', Option for handling special data cases where 'A' exists without a preceding 'S'.
                      Currently, this script only supports 'equal', which sets the daily value equal
                      to the value next to the 'A' (e.g., 2.3A becomes 2.3). These special cases are
                      shown if 'print_result' = True.

    mdr_S             Default = '0' 
     class: 'string', Option for handling special data cases where 'S' exists without a following 'A'.
                      Currently, this script only supports '0', which sets these values to 0. These
                      special cases are shown if 'print_result' = True. 

    Optional parameters for printing results in real-time
    -----------------------------------------------------
    print_results   Default = True
     class: 'bool', Print real-time results of station query to interface.

    print_md        Default = True
     class: 'bool', Print information about multi-day event processing if found while querying data.

    Optional parameters for outputing variables to excel
    ----------------------------------------------------
    stn_excel       Default = False
     class: 'bool', If True, saves 'stations' dataframe to an Excel file. 
                    WARNING: If querying a large amount of data, this file may become very large.
                    If 'meta_excel' = True, metadata will be saved in same Excel file under different
                    sheet name.

    meta_excel      Default = False
     class: 'bool', If True, saves 'metadata' dataframe to an Excel file. 
                    If 'stn_excel' = True, station data will be saved in same Excel file under 
                    different sheet name.

    folderpath        Default = '' (current directory)
     class: 'string', If 'dataviz' = True or 'to_excel' = True, the output file(s) will be saved to the 
                      folder as specified by this parameter. The default will place the file(s) in 
                      the current working directory.

    Returns
    ---------------------
    output: class: 'pandas.DataFrame'
    '''

    #-------------------------------------------------------------------------------------------------
    # Use metadata to find all station IDs within bounded box
    #-------------------------------------------------------------------------------------------------

    # Only pull metadata on required parameters
    metadata = stnmeta.bbox_metadata(elem=elem,items='name,state,sids,ll,valid_daterange',
                                                  slat=slat,nlat=nlat,wlon=wlon,elon=elon)

    #-------------------------------------------------------------------------------------------------
    # Assess size of data query, continue if less than maximum allowable number of stations
    #-------------------------------------------------------------------------------------------------

    if len(metadata) < stn_size: 

       #-------------------------------------------------------------------------------------------------
       # Define range of dates from earliest to latest station dates available based on metadata 
       #-------------------------------------------------------------------------------------------------
   
       dates = pd.date_range(str(min(pd.to_datetime(metadata['sdate'])).date()), # earliest date
                             str(max(pd.to_datetime(metadata['edate'])).date()), # latest date 
                                                                       freq='d') # daily frequency
   
       #-------------------------------------------------------------------------------------------------
       # Define Pandas DataFrame from sdate to edate that will be filled with station data in a loop 
       #-------------------------------------------------------------------------------------------------
   
       STATIONS = pd.DataFrame({'Date': dates})
   
       # Add feature here that says if # of stations exceeds a certain value, query is exited and not run
   
       # Loop through all stations within bounded box
       for i in range(len(metadata)):
   
        # Show station information if permitted
        if print_results == True:
         if i == 0:
            print(str(elem)+': Reading in '+str(len(metadata))+' total stations (station id: name, state) ...')
         print('#'+str(i+1)+'. '+metadata['sids'][i]+': '+metadata['name'][i]+', '+metadata['state'][i])
   
        # Use metadata to read in each station individually
        station_values = stndata.singlestn_daily(elem=elem, sid=metadata['sids'][i], 
                                                 sdate=metadata['sdate'][i], edate=metadata['edate'][i], 
                                                 M=M, T=T, mdr=mdr, mdr_opt=mdr_opt, 
                                                 mdr_A=mdr_A, mdr_S=mdr_S, 
                                                 print_results=print_results, print_md=print_md        )
   
        #-------------------------------------------------------------------------------------------------
        # Append data to STATIONS DataFrame based on corresponding dates, make all else equal to NaN 
        #-------------------------------------------------------------------------------------------------
   
        # Ignore unnecessary Pandas warnings
        pd.options.mode.chained_assignment = None
        simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
   
        # Make new column in STATIONS for new station and set all values to NaN first 
        STATIONS[str(metadata['sids'][i]+': '+metadata['name'][i]+', '+metadata['state'][i])] = float('NaN')
   
        # Define start and end date indices for each Station ID to insert data based on appropriate dates
        sdate_ind = STATIONS['Date'].index[STATIONS['Date'] == metadata['sdate'][i]][0]
        edate_ind = STATIONS['Date'].index[STATIONS['Date'] == metadata['edate'][i]][0]
   
        # Fill data between start and end dates in corresponding column in STATIONS DataFrame
        STATIONS[str(metadata['sids'][i]+': '+metadata['name'][i]+', '+metadata['state'][i])].iloc[
                                                                  sdate_ind:edate_ind+1] = station_values
   
       #--------------------------------------------------------------------------------------------------
       # Save stations and metadata to Excel
       #--------------------------------------------------------------------------------------------------
   
       if stn_excel == True or meta_excel == True:
   
        print('Saving data to Excel: Depending on data size, this may take a few minutes...')
   
        # Write output file name first
        w = pd.ExcelWriter('./'+folderpath+'/'+str(elem)+'_query_bbox_wlon_'+str(wlon)+'_elon_'+str(elon)+\
                                                    '_slat_'+str(slat)+'_nlat_'+str(nlat)+'.xlsx')
   
        # Output STATIONS to Excel
        if stn_excel == True:
   
         # Set new dataframe from STATIONS, make dates dtype=string so they show up in Excel
         df = STATIONS
         df['Date'] = pd.DataFrame(STATIONS['Date'],dtype='string')
   
         # Output dataframe to Excel as sheet name 'stations'
         df.to_excel(w,sheet_name='stations',index=False)
   
        # Output metadata to Excel
        if meta_excel == True:
   
         # Rewrite dataframe as metadata
         df = metadata
   
         # Output dataframe to Excel as sheet name 'metadata'
         df.to_excel(w,sheet_name='metadata',index=False)
   
        # Save Excel writer, saves Excel file with both sheets specified above
        w.save()
   
       #--------------------------------------------------------------------------------------------------
       # Return Pandas DataFrame 
       #--------------------------------------------------------------------------------------------------
   
       return STATIONS, metadata

    else:

       print(f'ERROR: Bounding box has more than maximum ({stn_size}) number of queried stations. '+
              'Choose smaller bounding box.')
       raise SystemExit()

#======================================================================================================
# Query daily data from multiple stations from NOAA ACIS given a list of station ids (sids), return as 
# Pandas DataFrame with each station represented by a new column      
#======================================================================================================

def sids_multistn_daily(elem: str, sids: list,

                        # Optional parameters for all elems
                        M: float = float('NaN'),

                        # Optional parameters for elems 'pcpn', 'snow', 'snwd'
                        T: float = 0.00001, mdr: int = 50, mdr_opt: str = 'avg',
                        mdr_A: str = 'equal', mdr_S: str = '0',

                        # Optional parameters for printing results
                        print_results: bool = True, print_md: bool = True,

                        # Optional parameters for outputing variables to excel
                        stn_excel: bool = False, meta_excel: bool = False,
                        folderpath: str = ''

                        ):

    '''
    Creates Pandas DataFrame for the entire observational record for all stations from NOAA ACIS 
    given a list of station ids (sids). Each individual station is represented by a new column. All 
    days where a station did not collect data are set to NaN.  

    Required Parameters
    --------------------
    elem
     class: 'string', Single variable element to include. Example: 'maxt'
                      Possible options are 'maxt','mint','avgt','pcpn','snow','snwd'.

    sids
     class: 'list', List of station ids (sids) for which to query corresponding data. Each element
                    in the list must be type 'string'.

    Optional parameters for all elems
    ----------------------------------
    M                Default = float('NaN')
     class: 'float', Value to which missing values ('M') are converted.

    Optional parameters for elems 'pcpn', 'snow', and 'snwd'
    ---------------------------------------------------------
    T                Default = 0.00001 
     class: 'float', Value to which trace values ('T') are converted.

    mdr                Default = 50 
     class: 'integer', Multi-day range, the number of days this script will search from S=0 to find
                       the final multi-day even with form '[sum]A'.  

    mdr_opt           Default = 'avg' 
     class: 'string', Option for handling multi-day events. Currently, this script only supports
                      placing the average daily value of the multi-day event into each day within
                      the event (e.g., 3 day event that totaled 0.9 inches, each day's value will
                      equal 0.3 inches).

    mdr_A             Default = 'equal'
     class: 'string', Option for handling special data cases where 'A' exists without a preceding 'S'.
                      Currently, this script only supports 'equal', which sets the daily value equal
                      to the value next to the 'A' (e.g., 2.3A becomes 2.3). These special cases are
                      shown if 'print_result' = True.

    mdr_S             Default = '0' 
     class: 'string', Option for handling special data cases where 'S' exists without a following 'A'.
                      Currently, this script only supports '0', which sets these values to 0. These
                      special cases are shown if 'print_result' = True. 

    Optional parameters for printing results in real-time
    -----------------------------------------------------
    print_results   Default = True
     class: 'bool', Print real-time results of station query to interface.

    print_md        Default = True
     class: 'bool', Print information about multi-day event processing if found while querying data.

    Optional parameters for outputing variables to excel
    ----------------------------------------------------
    stn_excel       Default = False
     class: 'bool', If True, saves 'stations' dataframe to an Excel file. 
                    WARNING: If querying a large amount of data, this file may become very large.
                    If 'meta_excel' = True, metadata will be saved in same Excel file under different
                    sheet name.

    meta_excel      Default = False
     class: 'bool', If True, saves 'metadata' dataframe to an Excel file. 
                    If 'stn_excel' = True, station data will be saved in same Excel file under 
                    different sheet name.

    folderpath        Default = '' (current directory)
     class: 'string', If 'dataviz' = True or 'to_excel' = True, the output file(s) will be saved to the 
                      folder as specified by this parameter. The default will place the file(s) in 
                      the current working directory.

    Returns
    ---------------------
    output: class: 'pandas.DataFrame'
    '''

    #-------------------------------------------------------------------------------------------------
    # Use metadata to find all station IDs within bounded box
    #-------------------------------------------------------------------------------------------------

    # Confirm type of 'sids'
    sids = list(sids)

    # Only pull metadata on required parameters
    metadata = stnmeta.sids_metadata(elem=elem,items='name,state,sids,ll,valid_daterange',sids=sids)

    #-------------------------------------------------------------------------------------------------
    # Define range of dates from earliest to latest station dates available based on metadata 
    #-------------------------------------------------------------------------------------------------

    dates = pd.date_range(str(min(pd.to_datetime(metadata['sdate'])).date()), # earliest date
                          str(max(pd.to_datetime(metadata['edate'])).date()), # latest date 
                                                                    freq='d') # daily frequency

    #-------------------------------------------------------------------------------------------------
    # Define Pandas DataFrame from sdate to edate that will be filled with station data in a loop 
    #-------------------------------------------------------------------------------------------------

    STATIONS = pd.DataFrame({'Date': dates})

    # Loop through all stations within bounded box
    for i in range(len(metadata)):

     # Show station information if permitted
     if print_results == True:
      if i == 0:
         print(str(elem)+': Reading in '+str(len(metadata))+' total stations (station id: name, state) ...')
      print('#'+str(i+1)+'. '+metadata['sids'][i]+': '+metadata['name'][i]+', '+metadata['state'][i])

     # Use metadata to read in each station individually
     station_values = stndata.singlestn_daily(elem=elem, sid=metadata['sids'][i],
                                              sdate=metadata['sdate'][i], edate=metadata['edate'][i],
                                              M=M, T=T, mdr=mdr, mdr_opt=mdr_opt,
                                              mdr_A=mdr_A, mdr_S=mdr_S,
                                              print_results=print_results, print_md=print_md        )

     #-------------------------------------------------------------------------------------------------
     # Append data to STATIONS DataFrame based on corresponding dates, make all else equal to NaN 
     #-------------------------------------------------------------------------------------------------

     # Ignore unnecessary Pandas warnings
     pd.options.mode.chained_assignment = None
     simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

     # Make new column in STATIONS for new station and set all values to NaN first 
     STATIONS[str(metadata['sids'][i]+': '+metadata['name'][i]+', '+metadata['state'][i])] = float('NaN')

     # Define start and end date indices for each Station ID to insert data based on appropriate dates
     sdate_ind = STATIONS['Date'].index[STATIONS['Date'] == metadata['sdate'][i]][0]
     edate_ind = STATIONS['Date'].index[STATIONS['Date'] == metadata['edate'][i]][0]

     # Fill data between start and end dates in corresponding column in STATIONS DataFrame
     STATIONS[str(metadata['sids'][i]+': '+metadata['name'][i]+', '+metadata['state'][i])].iloc[
                                                               sdate_ind:edate_ind+1] = station_values

    #--------------------------------------------------------------------------------------------------
    # Save stations and metadata to Excel
    #--------------------------------------------------------------------------------------------------

    if stn_excel == True or meta_excel == True:

     print('Saving data to Excel: Depending on data size, this may take a few minutes...')

     # Write output file name first
     w = pd.ExcelWriter('./'+folderpath+'/'+str(elem)+'_query_bbox_wlon_'+str(wlon)+'_elon_'+str(elon)+\
                                                 '_slat_'+str(slat)+'_nlat_'+str(nlat)+'.xlsx')

     # Output STATIONS to Excel
     if stn_excel == True:

      # Set new dataframe from STATIONS, make dates dtype=string so they show up in Excel
      df = STATIONS
      df['Date'] = pd.DataFrame(STATIONS['Date'],dtype='string')

      # Output dataframe to Excel as sheet name 'stations'
      df.to_excel(w,sheet_name='stations',index=False)

     # Output metadata to Excel
     if meta_excel == True:

      # Rewrite dataframe as metadata
      df = metadata

      # Output dataframe to Excel as sheet name 'metadata'
      df.to_excel(w,sheet_name='metadata',index=False)

     # Save Excel writer, saves Excel file with both sheets specified above
     w.save()

    #--------------------------------------------------------------------------------------------------
    # Return Pandas DataFrame 
    #--------------------------------------------------------------------------------------------------

    return STATIONS, metadata

######################################################################################################
#
# PLOTTING FUNCTIONS
#
######################################################################################################

#=====================================================================================================
# Data visualization for bbox with multiple stations
#=====================================================================================================

def bbox_multistn_dataviz(elem: str, stndata_df: pd.DataFrame, stnmeta_df: pd.DataFrame, 
                          slat: float, nlat: float, wlon: float, elon: float,  
                          map_background: str = 'QuadtreeTiles', map_buffer: float = 0.5, 
                          marker_col: str = 'r', add_dates: list = [], add_values: list = [],
                          filesuf: str = '.pdf', folderpath: str = '', savefig: bool = False
                          ):

    '''
    Makes data visualization of 1) time series of all daily data for elem (contained in stndata_df),
    2) time series of total number of records with data for each day, 3) map showing bounding box and
    station locations within it.

    Parameters
    --------------------
    elem
     class: 'string', Single variable element to include. Example: 'maxt'
                      Possible options are 'maxt','mint','avgt','pcpn','snow','snwd'.

    stndata_df
     class: 'pandas.DataFrame', DataFrame containing all daily data with each column representing
                                each station. Left-most column should be 'Date'. Produce this 
                                DataFrame with i.e., bbox_multistn_daily(). 

    stnmeta_df
     class: 'pandas.DataFrame', DataFrame containing metadata for all stations contained within
                                stndata_df - must include sids/lat/lon. Produce this DataFrame
                                with i.e., bbox_multistn_daily(). 

    slat, nlat, wlon, elon
     class: 'float', Bounding latitude and longitude coordinates for querying metadata from all
                     stations within the box. Negative values correspond to °S and °W while positive
                     values correspond to °N and °E. Any number of decimal places may be specified. 
                     Example: slat = 37, nlat = 37.567, wlon = -90.01, elon = -89.5

    map_background    Default = 'QuadtreeTiles'
     class: 'string', String indicating option for map background. Options are:
                      'QuadtreeTiles': Microsoft WTS quadkey coordinate system..
                      'GoogleTiles': Google Maps street tiles.
                      'OpenStreetMap': OpenStreetMap free wiki world map.
                      'grey': Land area shaded as grey.

    map_buffer       Default = 0.5
     class: 'float', Buffer between bounding box and map extent, in lat/lon coordinates.  

    marker_col        Default = 'r'
     class: 'string', Color of markers on the map.

    add_dates       Default = []
     class: 'list', List of date strings ('YYYY-MM-DD') for adding additional data points to the plot.

    add_values      Default = []
     class: 'list', List of floats for adding additional data points to the plot.

    filesuf           Default = '.pdf'
     class: 'string', If 'dataviz' = True, this parameter specifies the type of file that will be 
                      output.

    folderpath        Default = '' (current directory)
     class: 'string', If 'dataviz' = True or 'to_excel' = True, the output file(s) will be saved to the 
                      folder as specified by this parameter. The default will place the file(s) in 
                      the current working directory.

    savefig         Default = False
     class: 'bool', If 'savefig' = True, then the figure will be saved in directory indicated by
                    'folderpath' with the file type indicated by 'filesuf'.
    '''

    print('Making data visualization: Depending on data size, this may take a few minutes...')

    #--------------------------------------------------------------------------------------------------
    # Import plotting packages 
    #--------------------------------------------------------------------------------------------------

    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from matplotlib.ticker import MaxNLocator
    import cartopy.io.img_tiles
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    #--------------------------------------------------------------------------------------------------
    # Define figures and axes
    #--------------------------------------------------------------------------------------------------

    fig = plt.figure(figsize=(10,10),dpi=300)
    gs = fig.add_gridspec(nrows=2,ncols=10)
    ax1 = fig.add_subplot(gs[0,:])
    ax2 = fig.add_subplot(gs[1,0:5])
    ax3 = fig.add_subplot(gs[1,5:10], projection=ccrs.PlateCarree())

    #--------------------------------------------------------------------------------------------------
    # 1. Loop through each station and plot as scatter
    #--------------------------------------------------------------------------------------------------

    for z in range(len(stndata_df.columns)-1):
        ax1.plot(stndata_df['Date'],stndata_df.iloc[:,z+1],'o',markersize=1,c='k')

    # Define y-axis label
    if elem == 'maxt' or elem == 'mint' or elem == 'avgt':
     ylabel = 'deg F'
    elif elem == 'pcpn' or elem == 'snow' or elem == 'snwd':
     ylabel = 'inches'
 
    ax1.set_ylabel(ylabel)
    ax1.set_title('Instrumental '+str(elem)+' record (wlon= '+str(wlon)+', elon= '+str(elon)+    \
                                                   ', slat= '+str(slat)+', nlat= '+str(nlat)+')')

    # Add additional data points if specified, like current extreme events
    if add_dates != [] and add_values != []:
      ax1.plot(pd.to_datetime(add_dates),add_values,'o',markersize=2,c='r')
      ax1.text(pd.to_datetime(add_dates[0]),add_values[0]-1.0,add_dates[0],c='r',fontsize=8,
                                                                           ha='center',va='center')

    #--------------------------------------------------------------------------------------------------
    # 2. Plot number of records for each day
    #--------------------------------------------------------------------------------------------------

    # Count number of active stations for each day
    numrecs = np.zeros(len(stndata_df['Date']),dtype=int)
    for rec in range(len(stndata_df['Date'])):
        numrecs[rec] = (len(stndata_df.columns)-1) - (np.sum(pd.isnull(stndata_df.iloc[rec,1:])))

    ax2.plot(stndata_df['Date'],numrecs,'-',c='k',lw=0.5)
    ax2.set_ylabel('Count')
    ax2.yaxis.set_major_locator(MaxNLocator(integer=True)) # only integers are allowed on y-axis 

    ax2.set_title('Number of records for each day')

    #--------------------------------------------------------------------------------------------------
    # 3. Plot map of locations of all records
    #--------------------------------------------------------------------------------------------------

    # Determine map background as specified
    if map_background == 'QuadtreeTiles':
     ax3.add_image(cartopy.io.img_tiles.QuadtreeTiles(),8,alpha=0.8)
    elif map_background == 'GoogleTiles':
     ax3.add_image(cartopy.io.img_tiles.GoogleTiles(),8,alpha=0.8)
    elif map_background == 'OpenStreetMap':
     ax3.add_image(cartopy.io.img_tiles.OSM(),8,alpha=0.8)
    elif map_background == 'grey':
     ax3.add_feature(cfeature.LAND,facecolor='k',alpha=0.05)

    # Coast, country, and US state borders
    ax3.add_feature(cfeature.COASTLINE,edgecolor='k',linewidths=0.5)
    ax3.add_feature(cfeature.BORDERS,edgecolor='k',linewidths=0.5)
    ax3.add_feature(cfeature.STATES,edgecolor='k',linewidths=0.5)

    ax3.plot(stnmeta_df['lon'],stnmeta_df['lat'],'.',c=marker_col,markersize=2)
    ax3.set_title('Locations of '+str(len(stnmeta_df['sids']))+' queried stations');

    # Coordinate buffer for lat/lon plot
    ax3.set_extent([wlon-map_buffer,elon+map_buffer,slat-map_buffer,nlat+map_buffer],ccrs.PlateCarree())
    ax3.add_patch(Rectangle((wlon,slat),abs(wlon)-abs(elon),abs(nlat)-abs(slat),
                            linestyle='-',facecolor='None',edgecolor='k',linewidth=0.25,zorder=0.1));

    # Add text for data source
    ax3.text(0.5,-0.05,'Data Source: NOAA ACIS (http://data.rcc-acis.org)\nImage: Alex Thompson (@ajtclimate)',
             ha='center',va='center',fontsize=8,transform=ax3.transAxes)

    #--------------------------------------------------------------------------------------------------
    # 4. Save output file
    #--------------------------------------------------------------------------------------------------
   
    if savefig == True:
     plt.savefig('./'+folderpath+'/'+str(elem)+'_query_bbox_wlon_'+str(wlon)+'_elon_'+str(elon)+\
                                                '_slat_'+str(slat)+'_nlat_'+str(nlat)+filesuf,
                                                bbox_inches='tight')

#=====================================================================================================
# Data visualization for list of sids for multiple stations
#=====================================================================================================

def sids_multistn_dataviz(elem: str, stndata_df: pd.DataFrame, stnmeta_df: pd.DataFrame,
                          bbox_slat: float = None, bbox_nlat: float = None, 
                          bbox_wlon: float = None, bbox_elon: float = None,
                          map_background: str = 'QuadtreeTiles', map_buffer: float = 0.5,
                          add_dates: list = [], add_values: list = [],
                          filesuf: str = '.pdf', folderpath: str = '', savefig: bool = False
                          ):

    '''
    Makes data visualization of 1) time series of all daily data for elem (contained in stndata_df),
    2) time series of total number of records with data for each day, 3) map showing station locations 
    and (optional) bounding box around them.

    Parameters
    --------------------
    elem
     class: 'string', Single variable element to include. Example: 'maxt'
                      Possible options are 'maxt','mint','avgt','pcpn','snow','snwd'.

    stndata_df
     class: 'pandas.DataFrame', DataFrame containing all daily data with each column representing
                                each station. Left-most column should be 'Date'. Produce this 
                                DataFrame with i.e., bbox_multistn_daily(). 

    stnmeta_df
     class: 'pandas.DataFrame', DataFrame containing metadata for all stations contained within
                                stndata_df - must include sids/lat/lon. Produce this DataFrame
                                with i.e., bbox_multistn_daily(). 

    bbox_slat, bbox_nlat, bbox_wlon, bbox_elon    
     class: 'float', Bounding latitude and longitude coordinates (optional) for the purpose of the 
                     visualization. Negative values correspond to °S and °W while positive
                     values correspond to °N and °E. Any number of decimal places may be specified. 
                     Example: slat = 37, nlat = 37.567, wlon = -90.01, elon = -89.5
                     Default is None.

    map_background    Default = 'QuadtreeTiles'
     class: 'string', String indicating option for map background. Options are:
                      'QuadtreeTiles': Microsoft WTS quadkey coordinate system.
                      'GoogleTiles': Google Maps street tiles.
                      'OpenStreetMap': OpenStreetMap free wiki world map.
                      'grey': Land area shaded as grey.

    map_buffer       Default = 0.5
     class: 'float', Buffer between bounding box and map extent, in lat/lon coordinates. 

    add_dates       Default = []
     class: 'list', List of date strings ('YYYY-MM-DD') for adding additional data points to the plot.

    add_values      Default = []
     class: 'list', List of floats for adding additional data points to the plot.

    filesuf           Default = '.pdf'
     class: 'string', If 'dataviz' = True, this parameter specifies the type of file that will be 
                      output.

    folderpath        Default = '' (current directory)
     class: 'string', If 'dataviz' = True or 'to_excel' = True, the output file(s) will be saved to the 
                      folder as specified by this parameter. The default will place the file(s) in 
                      the current working directory.

    savefig         Default = False
     class: 'bool', If 'savefig' = True, then the figure will be saved in directory indicated by
                    'folderpath' with the file type indicated by 'filesuf'.
    '''

    print('Making data visualization: Depending on data size, this may take a few minutes...')

    #--------------------------------------------------------------------------------------------------
    # Import plotting packages
    #--------------------------------------------------------------------------------------------------

    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from matplotlib.ticker import MaxNLocator
    import cartopy.io.img_tiles
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    #--------------------------------------------------------------------------------------------------
    # Define figures and axes
    #--------------------------------------------------------------------------------------------------

    fig = plt.figure(figsize=(10,10),dpi=300)
    gs = fig.add_gridspec(nrows=2,ncols=10)
    ax1 = fig.add_subplot(gs[0,:])
    ax2 = fig.add_subplot(gs[1,0:5])
    ax3 = fig.add_subplot(gs[1,5:10], projection=ccrs.PlateCarree())

    #--------------------------------------------------------------------------------------------------
    # 1. Loop through each station and plot as scatter
    #--------------------------------------------------------------------------------------------------

    for z in range(len(stndata_df.columns)-1):
        ax1.plot(stndata_df['Date'],stndata_df.iloc[:,z+1],'o',markersize=1,c='k')

    # Define y-axis label
    if elem == 'maxt' or elem == 'mint' or elem == 'avgt':
     ylabel = 'deg F'
    elif elem == 'pcpn' or elem == 'snow' or elem == 'snwd':
     ylabel = 'inches'

    ax1.set_ylabel(ylabel)
    ax1.set_title('Instrumental '+str(elem)+' record')

    # Add additional data points if specified, like current extreme events
    if add_dates != [] and add_values != []:
      ax1.plot(pd.to_datetime(add_dates),add_values,'o',markersize=2,c='r')
      ax1.text(pd.to_datetime(add_dates[0]),add_values[0]-1.0,add_dates[0],c='r',fontsize=8,
                                                                           ha='center',va='center')

    #--------------------------------------------------------------------------------------------------
    # 2. Plot number of records for each day
    #--------------------------------------------------------------------------------------------------

    # Count number of active stations for each day
    numrecs = np.zeros(len(stndata_df['Date']),dtype=int)
    for rec in range(len(stndata_df['Date'])):
        numrecs[rec] = (len(stndata_df.columns)-1) - (np.sum(pd.isnull(stndata_df.iloc[rec,1:])))

    ax2.plot(stndata_df['Date'],numrecs,'-',c='k',lw=0.5)
    ax2.set_ylabel('Count')
    ax2.yaxis.set_major_locator(MaxNLocator(integer=True)) # only integers are allowed on y-axis 

    ax2.set_title('Number of records for each day')

    #--------------------------------------------------------------------------------------------------
    # 3. Plot map of locations of all records
    #--------------------------------------------------------------------------------------------------

    # Determine map background as specified
    if map_background == 'QuadtreeTiles':
     ax3.add_image(cartopy.io.img_tiles.QuadtreeTiles(),8,alpha=0.8)
    elif map_background == 'GoogleTiles':
     ax3.add_image(cartopy.io.img_tiles.GoogleTiles(),8,alpha=0.8)
    elif map_background == 'OpenStreetMap':
     ax3.add_image(cartopy.io.img_tiles.OSM(),8,alpha=0.8)
    elif map_background == 'grey':
     ax3.add_feature(cfeature.LAND,facecolor='k',alpha=0.05)

    # Coast, country, and US state borders
    ax3.add_feature(cfeature.COASTLINE,edgecolor='k',linewidths=0.5)
    ax3.add_feature(cfeature.BORDERS,edgecolor='k',linewidths=0.5)
    ax3.add_feature(cfeature.STATES,edgecolor='k',linewidths=0.5)

    ax3.plot(stnmeta_df['lon'],stnmeta_df['lat'],'.',c='r',markersize=1)
    ax3.set_title('Locations of '+str(len(stnmeta_df['sids']))+' queried stations');

    # Coordinate buffer for lat/lon plot
    ax3.set_extent([stnmeta_df['lon'].min()-map_buffer,stnmeta_df['lon'].max()+map_buffer,
                    stnmeta_df['lat'].min()-map_buffer,stnmeta_df['lat'].max()+map_buffer],ccrs.PlateCarree())
    if all(var != None for var in [bbox_slat,bbox_nlat,bbox_wlon,bbox_elon]):
     ax3.add_patch(Rectangle((bbox_wlon,bbox_slat),
                             abs(bbox_wlon)-abs(bbox_elon),abs(bbox_nlat)-abs(bbox_slat),
                             linestyle='-',facecolor='None',edgecolor='k',linewidth=0.25,zorder=0.1));

    # Add text for data source
    ax3.text(0.5,-0.05,'Data Source: NOAA ACIS (http://data.rcc-acis.org)\nImage: Alex Thompson (@ajtclimate)',
             ha='center',va='center',fontsize=8,transform=ax3.transAxes)

    #--------------------------------------------------------------------------------------------------
    # 4. Save output file
    #--------------------------------------------------------------------------------------------------
    
    if savefig == True:
     plt.savefig('./'+folderpath+'/'+str(elem)+'_query_sids_list'+filesuf,bbox_inches='tight')

