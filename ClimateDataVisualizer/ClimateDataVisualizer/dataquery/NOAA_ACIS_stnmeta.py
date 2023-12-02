#######################################################################################################
#
# Functions for querying NOAA ACIS station metadata from https://xmacis.rcc-acis.org/ 
#
#######################################################################################################

import numpy as np
import pandas as pd
import json, urllib
from warnings import simplefilter
from ClimateDataVisualizer.dataquery import NOAA_ACIS_stnmeta as stnmeta
from ClimateDataVisualizer.dataquery import NOAA_ACIS_stndata as stndata

#######################################################################################################
#
# METADATA FUNCTIONS
#
#######################################################################################################

#======================================================================================================
# Query metadata from NOAA ACIS given bounding box of coordinates and return as Pandas DataFrame
#======================================================================================================

def bbox_metadata(elem: str, items: str, slat: float, nlat: float, wlon: float, elon: float):

    '''
    Creates Pandas DataFrame with metadata for all NOAA ACIS stations within bounded coordinates
    for a single element (e.g., 'maxt').
    See https://www.rcc-acis.org/docs_webservices.html for information on querying metadata.

    Parameters
    -------------
    elem
     class: 'string', Single variable element to include. Example: 'maxt'
                      Possible options are 'maxt','mint','avgt','pcpn','snow','snwd'.

    items
     class: 'string', Metadata items to include in output dataframe. Add ',' in between each for 
                      multiple variables. Possible options are 'name','state','sids','sid_dates','ll',
                      'elev','uid','county','climdiv','valid_daterange'. 
                      Example: 'name,state,sids,ll,uid,valid_daterange'

    slat, nlat, wlon, elon
     class: 'float', Bounding latitude and longitude coordinates for querying metadata from all
                     stations within the box. Negative values correspond to °S and °W while positive
                     values correspond to °N and °E. Any number of decimal places may be specified. 
                     Example: slat = 37, nlat = 37.567, wlon = -90.01, elon = -89.5

    Returns
    ---------------------
    output: class: 'pandas.DataFrame'
            Returns dataframe of queried metadata with dimensions: 
            Rows (number of stations within bounded box) x Columns (number of items in 'items') 
    '''

    #-------------------------------------------------------------
    # Turn coordinates into bbox
    #-------------------------------------------------------------

    bbox = str(elon)+','+str(slat)+','+str(wlon)+','+str(nlat)

    #-------------------------------------------------------------
    # Input dictionary of metadata to include in query
    #-------------------------------------------------------------

    input_dict = {'bbox': bbox, 'elems': elem, 'meta': items}

    #-------------------------------------------------------------------------------------------------
    # Call json request
    #-------------------------------------------------------------------------------------------------

    metadata = stnmeta.json_req_metadata(input_dict=input_dict)

    #--------------------------------------
    # Output metadata as Pandas Dataframe
    #--------------------------------------

    return metadata

#======================================================================================================
# Query metadata from NOAA ACIS given list of station ids (sids) and return as Pandas DataFrame
#======================================================================================================

def sids_metadata(elem: str, items: str, sids: list):

    '''
    Creates Pandas DataFrame with metadata for all NOAA ACIS stations given a list of station ids
    (sids). See https://www.rcc-acis.org/docs_webservices.html for information on querying metadata.

    Parameters
    -------------
    elem
     class: 'string', Single variable element to include. Example: 'maxt'
                      Possible options are 'maxt','mint','avgt','pcpn','snow','snwd'.

    items
     class: 'string', Metadata items to include in output dataframe. Add ',' in between each for 
                      multiple variables. Possible options are 'name','state','sids','sid_dates','ll',
                      'elev','uid','county','climdiv','valid_daterange'. 
                      Example: 'name,state,sids,ll,uid,valid_daterange'

    sids
     class: 'list', List of station ids (sids) for which to find corresponding metadata. Each element
                    in the list must be type 'string'.

    Returns
    ---------------------
    output: class: 'pandas.DataFrame'
            Returns dataframe of queried metadata with dimensions: 
            Rows (number of elements in sids) x Columns (number of items in 'items') 
    '''

    #-------------------------------------------------------------
    # Turn list of strings into single delimited string 
    #-------------------------------------------------------------

    sids_delim = ','.join(sids) 

    #-------------------------------------------------------------
    # Input dictionary of metadata to include in query
    #-------------------------------------------------------------

    input_dict = {'elems': elem, 'meta': items, 'sids': sids_delim}

    #-------------------------------------------------------------------------------------------------
    # Call json request
    #-------------------------------------------------------------------------------------------------

    metadata = stnmeta.json_req_metadata(input_dict=input_dict)

    #--------------------------------------
    # Output metadata as Pandas Dataframe
    #--------------------------------------

    return metadata

#======================================================================================================
# JSON request to pull metadata from NOAA ACIS given input dictionary
#======================================================================================================

def json_req_metadata(input_dict: dict):

    '''
    Performs json request of NOAA ACIS metadata based on supplied input dictionary. List of 'items'
    checked for in this script are: 'name', 'state', 'sids', 'll', 'elev', 'uid', 'county', 'climdiv',
    and 'valid_daterange'.

    Parameters
    -------------
    input_dict
     class: 'dict', Input dictionary of metadata to include in query 

    Returns
    ---------------------
    output: class: 'pandas.DataFrame'
            Returns dataframe of queried metadata 
    '''

    #--------------------------------------------
    # Extract variables from input dictionary
    #--------------------------------------------

    elem  = input_dict['elems']
    items = input_dict['meta']

    #-------------------------------------------------------------------------------------------------
    # Call json request
    #-------------------------------------------------------------------------------------------------

    params = urllib.parse.urlencode({'params':json.dumps(input_dict)}).encode('utf-8')
    json_response = urllib.request.urlopen(urllib.request.Request('http://data.rcc-acis.org/StnMeta',
                                           params,{'Accept':'application/json'})
                                           ).read()
    json_output = json.loads(json_response)

    #------------------------------------------
    # Convert json_output to Pandas DataFrame
    #------------------------------------------

    meta = pd.DataFrame(json_output['meta'])

    #----------------------------------------------------------------------------
    # Load each selected column into output DataFrame 
    #----------------------------------------------------------------------------

    # First column defines selected 'elem'
    metadata = pd.DataFrame({'elem': pd.Series([elem]*len(meta))})

    # If no data available, exit and return error message
    if metadata.empty:
     return ValueError('No data exist for this query') 

    # 'name' 
    if ('name' in items) == True:
     metadata = metadata.assign(name=pd.Series(meta['name']))

    # 'state'
    if ('state' in items) == True:
     metadata = metadata.assign(state=pd.Series(meta['state']))

    # 'sids'
    # NOTE: Any station ID in the list will supply accurate data when accompanied by the valid data 
    # range so we only extract the first sids here to pass to the metadata dataframe. The attached
    # station code and type are included in the results as well.
    if ('sids' in items) == True:
     sids = pd.Series(meta['sids'].str[0].str.split(' ', expand=True).iloc[:,0],dtype='string')
     # Include sids_code and sids_type as columns
     sids_station_id_type = pd.DataFrame({'code': [1,2,3,4,5,6,7,9,10,29],
                                          'type': ['wban','coop','faa','wmo','icao','ghcn','nwsli',
                                                   'thrdx','cocorahs','cadx']                      })
     sids_code = meta['sids'].str[0].str.split(' ', expand=True).iloc[:,1].astype(int)
     sids_type = pd.Series(sids_code.map(sids_station_id_type.set_index('code').type),dtype='string')
     metadata = metadata.assign(sids=sids,sids_code=sids_code,sids_type=sids_type)

    # 'sid_dates'
    # NOTE: These dates are not necessarily accurate. I recommend leaving this out of the metadata
    # dataframe and using 'valid_daterange' instead when choosing the dates from which to query.
    if ('sid_dates' in items) == True:
     sid_sdate = meta['sid_dates'].str[0].str[1] # start date
     sid_edate = meta['sid_dates'].str[0].str[2] # end date
     metadata = metadata.assign(sid_sdate=pd.Series(sid_sdate,dtype='string'),
                                sid_edate=pd.Series(sid_edate,dtype='string')  )

    # 'll'
    if ('ll' in items) == True:
     metadata = metadata.assign(lat=np.float32(meta['ll'].str[1]),lon=np.float32(meta['ll'].str[0]))

    # 'elev'
    if ('elev' in items) == True:
     metadata = metadata.assign(elev=pd.Series(meta['elev']))

    # 'uid'
    if ('uid' in items) == True:
     metadata = metadata.assign(uid=pd.Series(meta['uid'],dtype='string'))

    # 'county'
    if ('county' in items) == True:
     metadata = metadata.assign(county=pd.Series(meta['county'],dtype='string'))

    # 'climdiv'
    if ('climdiv' in items) == True:
     metadata = metadata.assign(climdiv=pd.Series(meta['climdiv'],dtype='string'))

    # 'valid_daterange'
    if ('valid_daterange' in items) == True:
     metadata = metadata.assign(sdate=pd.Series(meta['valid_daterange'].str[0].str[0],dtype='string'),
                               edate=pd.Series(meta['valid_daterange'].str[0].str[1],dtype='string')   )

    #--------------------------------------
    # Output metadata as Pandas Dataframe
    #--------------------------------------

    return metadata

#############################################################################################################
#
# Add to this module...
#
# Query metadata by state, county, climdiv, cwa, basin
#
############################################################################################################# 


