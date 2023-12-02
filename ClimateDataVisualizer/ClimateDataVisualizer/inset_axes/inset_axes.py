#######################################################################################################
#
# Functions for plotting an inset figures within the main figure 
#
#######################################################################################################

import numpy as np
import pandas as pd 
import matplotlib as mpl
from matplotlib.patches import Rectangle
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import cartopy, cartopy.mpl.geoaxes, cartopy.io.img_tiles

#======================================================================================================
# Plot inset map on main figure 
#======================================================================================================

def inset_map(ax: mpl.axes.Axes, meta: pd.DataFrame, var: pd.DataFrame, width: float, height: float,  
              slat: float, nlat: float, wlon: float, elon: float, bbox_to_anchor: tuple = (0,0,1,1), 
              proj: cartopy.crs.Projection = cartopy.crs.PlateCarree(), ext_buff: float = 0.5, 
              img_tile: str = 'QuadtreeTiles', markersize: float = 1., markercolor: str = 'r', 
              rectcolor: str = 'k', rectlw: float = 0.5, txtsz: float = 4., lbl_buff: float = 0.3, 
              incl_year: bool = False, iyr: int = None, iyr_col: str = 'r'
              ):

   ''' 
   Plots an inset map on the main figure. Inset map contains locations of all stations passed via
   the metadata dataframe as points and the bounding box as a rectangle. 

   Required Parameters
   -------------------- 
   ax
    class: 'matplotlib.axes.Axes', Main axes on which to plot inset map.

   meta
    class: 'pandas.DataFrame', Pandas DataFrame containing metadata with at least the latitude and
                               longitude coordinates (column names 'lat' and 'lon') for each station 
                               to be plotted on the inset map. If iyr != None, meta must also have 
                               columns for station start and end dates ('sdate' and 'edate').

   var
    class: pandas.DataFrame', Pandas DataFrame from stndata function. Must contain 'Date' at 
                              left-most column.

   width, height
    class: 'float', Size of the inset map axes in inches. Can also be string in relative units, 
                    e.g., '40%'.

   slat, nlat, wlon, elon 
    class: 'float', Latitude and longitude bounds of bounding box. Used for drawing rectangle and 
                    setting map extent. 

   Optional Parameters
   --------------------
   bbox_to_anchor: class 'tuple', Bbox that the inset axes will be anchored to. Tuple is [left, bottom, 
                                  width, height]. Default = (0,0,1,1) 
   proj: class 'cartopy.crs.Projection', Projection of inset map. Default = cartopy.crs.PlateCarree()
   ext_buff: class 'float', Buffer in lat/lon coordinates between bounding box and map extent. 
                            Default = 0.5 
   img_tile: class 'string', String indicating option for map background. Options are:
                             'QuadtreeTiles': Microsoft WTS quadkey coordinate system (Default). 
                             'GoogleTiles': Google Maps street tiles.
                             'OpenStreetMap': OpenStreetMap free wiki world map.
                             'grey': Land area shaded as grey.
                             Stamen maps have been deprecated, but are still included in this function.
   markersize: class 'float', Marker size of station dots. Default = 1.
   markercolor: class 'string', Color of station dots. Default = 'r'
   rectcolor: class 'string', Color of bounding box rectangle. Default = 'k'
   rectlw: class 'float', Line width of bounding box rectangle. Default = 0.5
   txtsz: class 'float', Font size of text displaying lat/lon of bbox. Default = 4.
   lbl_buff: class 'float, Buffer proportion for spacing of bbox text. Default = 0.3 (i.e., 30%)
   incl_year: class 'bool', Boolean indicating if individual year will be shown on map. 
                            Default = False
   iyr: class 'int', Individual year plotted on map - shows stations collecting data during iyr if
                     specified. Default = None
   iyr_col: class 'str', Marker color of stations collecting data during iyr. Default = 'r' 
   '''

   # Define inset axis and extract its boundaries
   axm = inset_axes(ax,width=width,height=height,axes_class=cartopy.mpl.geoaxes.GeoAxes, 
                    axes_kwargs=dict(projection=proj),bbox_transform=ax.transAxes,
                    bbox_to_anchor=bbox_to_anchor,borderpad=0)
   axm_pos = axm.get_position()

   # Set map extent
   axm.set_extent([wlon-ext_buff,elon+ext_buff,slat-ext_buff,nlat+ext_buff],proj) 

   # Determine map background as specified
   if img_tile == 'QuadtreeTiles':
    axm.add_image(cartopy.io.img_tiles.QuadtreeTiles(),8,alpha=0.8)    
   if img_tile == 'GoogleTiles':
    axm.add_image(cartopy.io.img_tiles.GoogleTiles(),8,alpha=0.8)
   if img_tile == 'OpenStreetMap':
    axm.add_image(cartopy.io.img_tiles.OSM(),8,alpha=0.8)
   if img_tile == 'grey':
    axm.add_feature(cartopy.feature.LAND,facecolor='k',alpha=0.05)

   # Stamen maps have been deprecated but these options are still included here
   if img_tile == 'Stamen_terrain-background':
    axm.add_image(cartopy.io.img_tiles.Stamen('terrain-background'),8,alpha=0.8)
   if img_tile == 'Stamen_terrain-labels':
    axm.add_image(cartopy.io.img_tiles.Stamen('terrain'),8,alpha=0.8)

   # Coast, country, and US state borders
   axm.add_feature(cartopy.feature.STATES,edgecolor='k',linewidths=0.5)
   axm.add_feature(cartopy.feature.BORDERS,edgecolor='k',linewidths=0.5)
   axm.add_feature(cartopy.feature.COASTLINE,edgecolor='k',linewidths=0.5)

   # Plot sites and overlay iyr if specified
   sids_iyr = list(var.iloc[:,1:].loc[var['Date'].dt.year == iyr].columns[var.iloc[:,1:].loc[
                   var['Date'].dt.year == iyr].notna().any()].str.split(':').str[0])
   axm.plot(meta['lon'],meta['lat'],'.',markersize=markersize,c=markercolor)
   if incl_year == True:
      axm.plot(meta['lon'].loc[meta['sids'].isin(sids_iyr)],meta['lat'].loc[meta['sids'].isin(sids_iyr)],
               '.',markersize=markersize,c=iyr_col,zorder=100)

   # Draw data query bounding box and extract its boundaries
   rec = axm.add_patch(Rectangle((wlon,slat),abs(wlon)-abs(elon),abs(nlat)-abs(slat),zorder=3,
                           linestyle='-',facecolor='None',edgecolor=rectcolor,linewidth=rectlw))
   rec_pos = rec.get_window_extent(renderer=mpl.pyplot.gcf().canvas.get_renderer()).transformed(
                                                                        ax.transData.inverted())

   # Set text above and below inset map
   stn_txt = ' stations' if len(meta['lon']) > 1 else ' station'
   stntxt = axm.text(0.5,-0.05,str(len(meta['lon']))+stn_txt,transform=axm.transAxes,fontsize=6,
                     color=markercolor,ha='center',va='top')
   if incl_year == True:
      if len(meta['lon']) > 1:
         y_iyr = stntxt.get_position()[1]-0.14*(abs(nlat-slat)/abs(wlon-elon))**-0.2 # power law
         axm.text(0.5,y_iyr,str(len(sids_iyr))+' in '+str(iyr),transform=axm.transAxes,fontsize=5.5,
                  color=iyr_col,ha='center',va='top')
   axm.set_title('Data query box',fontsize=6,loc='center',pad=3)

   # Add bounding box coordinates to left of map
   if lbl_buff <= 1.:
     axm.text(0.5,rec_pos.y1+lbl_buff*(1.-rec_pos.y1),f'{nlat}°N',fontsize=txtsz,zorder=2,
              transform=axm.transAxes,bbox=dict(boxstyle='square',pad=0.05,edgecolor='none',facecolor='w'),
              ha='center',va='center')
     axm.text(0.5,rec_pos.y0-lbl_buff*(rec_pos.y0-0.),f'{slat}°N',fontsize=txtsz,zorder=2,
              transform=axm.transAxes,bbox=dict(boxstyle='square',pad=0.05,edgecolor='none',facecolor='w'),
              ha='center',va='center')
     axm.text(rec_pos.x0-lbl_buff*(rec_pos.x0-0.),0.5,f'{str(wlon)[1:]}°W',fontsize=txtsz,zorder=2,
              transform=axm.transAxes,bbox=dict(boxstyle='square',pad=0.05,edgecolor='none',facecolor='w'),
              ha='center',va='center',rotation=90)
     axm.text(rec_pos.x1+lbl_buff*(1-rec_pos.x1),0.5,f'{str(elon)[1:]}°W',fontsize=txtsz,zorder=2,
              transform=axm.transAxes,bbox=dict(boxstyle='square',pad=0.05,edgecolor='none',facecolor='w'),
              ha='center',va='center',rotation=90) 

#======================================================================================================
# Plot inset time series on main figure 
#======================================================================================================

def inset_timeseries(ax: mpl.axes.Axes, bounds: list, x1: np.ndarray, y1: np.ndarray, df1: pd.DataFrame,
                     y1_c: str = 'tab:red', y1_lw: float = 1., y1_text: str = '', 
                     y1_yloc: str = 'left', y1_axc: str = 'k',
                     x_maj: float = 50., x_min: float = 10., y1_maj: float = 1., y1_min: float = 0.5,
                     x2: np.ndarray = None, y2: np.ndarray = None, df2: pd.DataFrame = None,
                     y2_c: str = 'tab:blue', y2_lw: float = 1., y2_text: str = '', y2_axc: str = 'k',
                     y2_maj: float = 1., y2_min: float = 0.5, 
                     num_days: int = 15, num_months: int = 12, num_stns: int = 1,
                     bckgrnd_col: str = 'w', labelsize: float = 7., rect_c: str = 'k',
                     rect_textloc: str = 'lower right', rect_textsize: float = 3.,
                     rect_text: str = 'Grey = Base Period', syear: int = None, eyear: int = None,
                     add_xgrid: bool = True, add_title: bool = True, title: str = '',
                     ttl_fontsize: float = 8., ttl_loc: str = 'center', rmv_spine: list = ['top']
                     ):

   '''
   Plots an inset time series on the main figure. Inset time series can have one or two (optional) 
   axes. Base period passed to function shown with background rectangle.

   Required Parameters
   --------------------
   ax
    class: 'matplotlib.axes.Axes', Main axes on which to plot inset time series.

   bounds
    class: 'list', Location and sizing parameters for inset time series. Values in list are as follow:
                   [x0,y0,width,height] - lower-left corner of inset axes and its width and height in
                   proportion of main axes. Example: [0.4,0.17,0.3,0.2] (0.4 -> lower-left begins at
                   40% across the x axes dimension (left to right), 0.17 -> lower-left begins at 17% 
                   across the y axes dimension (bottom to top), 0.3 -> inset fig width is 30% of main 
                   axes width, 0.2 -> inset fig height is 20% of main axes height)

   x1
    class: 'numpy.ndarray', X variable (i.e., time) for plotting time series. 

   y1
    class: 'numpy.ndarray', Y variable (i.e., Tmax) for plotting time series.

   df1
    class: 'pandas.DataFrame', Pandas DataFrame generated by NOAA ACIS query. Used to determine
                               quality of data for plotting in time series. df2 is the same but is
                               optional and only needed if x2 and y2 are specified. 

   Optional parameters
   --------------------
   y1_c (y2_c): class 'string', Color of y1 line (y2 optional). Default = y1 'tab:red', y2 'tab:blue'
   y1_lw (y2_lw): class 'float', Line width of y1 line (y2 optional). Default = 1. (both y1 and y2)
   y1_text (y2_text): class 'string', Text for y-axis label (y2 optional). 
   y1_yloc: class 'string', Location of the y-axis labels ('left' or 'right'). Default = 'left' 
   y1_axc (y2_axc): class 'string', Color of the y-axis (y2 optional). Default = 'k'
   x_maj, xmin: class 'float', X-axis tick stride for major and minor ticks. Default = 50. and 10.
   y1_maj, y1_min (y2_maj, y2_min): class 'float', Y-axis tick stride for major and minor ticks 
                                                   (optional y2). Default = 1. and 0.5 (both y1 and y2)
   x2, y2: class 'np.ndarray', X and Y variables for optional second line.
   num_days: class 'int', Number of allowable days in a month to pass criteria for plotting. 
                          Default = 15
   num_months: class 'int', Number of allowable months in a year to pass criteria for plotting. 
                            Default = 12
   num_stns: class 'int', Number of stations collecting data that meets quality criteria in every year.
                          Default = 1
   bckgrnd_col: class 'float', Background color of the inset figure. Default = 'w'
   labelsize: class 'float', Label size for all inset figure labels. Default = 7. 
   rect_c: class 'string', Color for rectangle with alpha=0.05 automatically applied. Default = 'k'
   rect_textloc: class 'string', Location of rectangle text. Options are 'lower left', 'lower right',
                                 'upper left', or 'upper right'. Default = 'lower right'
   rect_textsize: class 'float', Font size of rectangle text. Default = 3.
   rect_text: class 'string', Text to display describing rectangle. Default = 'Grey = Base Period'
   syear, eyear: class 'integer', Start and end year for plotting base period rectangle.
   add_xgrid: class 'boolean', Option to add vertical grid lines at major and minor x ticks. 
                               Default = True
   add_title: class 'boolean', Option to add title text to inset figure. Default = True
   title: class 'string', If add_title=True, text to display as title.
   ttl_fontsize: class 'float', If add_title=True, font size of title text. Default = 8.
   ttl_loc: class 'string', If add_title=True, location of title. Default = 'center'
   rmv_spine: class 'list', List of strings indicating which spines to remove. Default = ['top']
   '''

   # Define inset axis 
   axt = ax.inset_axes(bounds,zorder=10) # zorder puts inset figure in front of main figure
   axt.set_facecolor(bckgrnd_col)

   ### Set data quality criteria prior to plotting
   # Ensure datetime type, filter df1 by available years, and add 'Year' and 'Month' as new columns
   df1['Date'] = pd.to_datetime(df1['Date'])
   df1 = df1[df1['Date'].between(pd.to_datetime(str(x1.min())),pd.to_datetime(str(x1.max())))]
   df1['Year'], df1['Month'] = df1['Date'].dt.year, df1['Date'].dt.month
   
   # Count non-NaN values for each column for each month of each year and set boolean with criteria
   months_that_pass = df1.groupby(['Year','Month']).apply(lambda x: x.iloc[:, 2:].count()) >= num_days

   # Calculate for each year how many months meet the criteria
   years_that_pass = months_that_pass.groupby(level='Year').sum() >= num_months

   # Total number of stations that pass criteria in each year
   stns_that_pass = years_that_pass.drop(['Year','Month'], axis=1).sum(axis=1) >= num_stns

   # Apply boolean to y1
   y1 = np.where(stns_that_pass,y1,np.nan)

   # Perform again for y2 if plotting two variables
   if y2 is not None:
    df2['Date'] = pd.to_datetime(df2['Date'])
    df2 = df2[df2['Date'].between(pd.to_datetime(str(x2.min())),pd.to_datetime(str(x2.max())))]
    df2['Year'], df2['Month'] = df2['Date'].dt.year, df2['Date'].dt.month
    months_that_pass = df2.groupby(['Year','Month']).apply(lambda x: x.iloc[:, 2:].count()) >= num_days
    years_that_pass = months_that_pass.groupby(level='Year').sum() >= num_months
    stns_that_pass = years_that_pass.drop(['Year','Month'], axis=1).sum(axis=1) >= num_stns
    y2 = np.where(stns_that_pass,y2,np.nan)

   # Plot x1 vs. y1
   axt.plot(x1,y1,'-',c=y1_c,lw=y1_lw)

   # Inset fig specifications
   axt.set_ylabel(y1_text,fontsize=labelsize,labelpad=0.1,color=y1_axc)
   axt.tick_params(axis='both',labelsize=labelsize,pad=1)
   axt.tick_params(axis='y',which='both',colors=y1_axc)
   axt.get_xaxis().set_major_locator(mpl.ticker.MultipleLocator(x_maj))
   axt.get_xaxis().set_minor_locator(mpl.ticker.MultipleLocator(x_min))
   axt.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(y1_maj))
   axt.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(y1_min))
   if y1_yloc == 'left':
    axt.yaxis.tick_left()
    axt.yaxis.set_label_position('left')
   elif y1_yloc == 'right':
    axt.yaxis.tick_right()
    axt.yaxis.set_label_position('right')

   # If plotting second line, x2 vs. y2
   if y2 is not None:
    axtw = axt.twinx()
    axtw.plot(x2,y2,'-',c=y2_c,lw=y2_lw)
    axtw.set_ylabel(y2_text,fontsize=labelsize,labelpad=0.1,color=y2_axc)
    axtw.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(y2_maj))
    axtw.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(y2_min))
    axtw.tick_params(axis='both',labelsize=labelsize,pad=1)
    axtw.tick_params(axis='y',which='both',colors=y2_axc)

   # Add rectangle representing base (or reference) period for main figure 
   axt.add_patch(Rectangle((syear,np.nanmin(y1)),eyear-syear,np.nanmax(y1)-np.nanmin(y1),
                 facecolor=rect_c,alpha=0.05,zorder=0.1));
   if rect_textloc == 'lower right':
    axt.text(0.99,0.05,rect_text,fontsize=rect_textsize,transform=axt.transAxes,ha='right')
   elif rect_textloc == 'upper right':
    axt.text(0.99,0.94,rect_text,fontsize=rect_textsize,transform=axt.transAxes,ha='right')
   elif rect_textloc == 'lower left':
    axt.text(0.02,0.05,rect_text,fontsize=rect_textsize,transform=axt.transAxes,ha='left')
   elif rect_textloc == 'upper left':
    axt.text(0.02,0.94,rect_text,fontsize=rect_textsize,transform=axt.transAxes,ha='left')

   # Gridlines
   if add_xgrid == True:
    axt.grid(axis='x',which='both',alpha=0.1)

   # Set title of plot
   if add_title == True:
    axt.set_title(title,fontsize=ttl_fontsize,loc=ttl_loc,pad=0.)

   # Remove figure spines
   axt.spines[rmv_spine].set_visible(False)
   if y2 is not None:
    axtw.spines[rmv_spine].set_visible(False)




