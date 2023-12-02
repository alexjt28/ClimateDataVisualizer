#######################################################################################################
#
# Functions for running single variable widget
#
#######################################################################################################

import sys, os 
sys.path.append(os.path.dirname(os.getcwd()))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Rectangle
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import cartopy, cartopy.mpl.geoaxes, cartopy.io.img_tiles
import ipyleaflet as ipyl     
from ClimateDataVisualizer.dataquery import NOAA_ACIS_stnmeta as stnmeta
from ClimateDataVisualizer.dataquery import NOAA_ACIS_stndata as stndata
from ClimateDataVisualizer.processing.bbox_dy import bbox_avg_dy
from ClimateDataVisualizer.inset_axes.inset_axes import inset_map, inset_timeseries
from ClimateDataVisualizer.interactives import plots, widgets
import ipywidgets as ipyw # must be below v7.7
from IPython.display import display, HTML, clear_output, Javascript

# URLs, needs double quotes based on code below
url_how = "https://sites.google.com/view/ajtclimate/climate-data-viz/how-to-use-website"

# File paths
cdv = '/paleonas/ajthompson/pyscripts/ClimateDataVisualizer/'

def widget_single_variable(enable_js: bool=True, stn_size: int=1000):

   ####################################################################################################
   # Generate map and input features 
   ####################################################################################################

   # Title image
   image_header = ipyw.Image(value=open(cdv+'Extras/image_banner.jpg','rb').read(),format='jpg')

   # Add link to website for guide on how to use website
   txt_link = ipyw.HTML(value=f'<h3><a href={url_how} target="_blank" style="color: red;"'+
                               '>**Click here for a guide on how to use this website**</a></h3>')

   # Create dropdown for variable
   txt_var = ipyw.HTML(value='<h3>Choose variable</h3>',layout=ipyw.Layout(margin='-20px 0 0 0'))
   var_dpdn = ipyw.Dropdown(options=[('Tmax (Daily High Temperature)','maxt'),
                                     ('Tmin (Daily Low Temperature)','mint'),
                                     ('Rain (Daily Rainfall)','pcpn'),
                                     ('Snow (Daily Snowfall)','snow')],value='maxt', 
                            layout=ipyw.Layout(width='220px',margin='-10px 0 0 0'))
   
   # Create ipyleaflet map
   m = ipyl.Map(center=(39,-95),zoom=4,scroll_wheel_zoom=True,layout=ipyw.Layout(width='750px',
                                                                                 height='350px'))
   
   # Add draw toolbar and search options
   m.add_control(ipyl.DrawControl(polygon={},polyline={},circlemarker={},
                                  rectangle={'shapeOptions':{'color':'black','weight':1}}))
   m.add_control(ipyl.SearchControl(position="topleft",zoom=10,
                                    url='https://nominatim.openstreetmap.org/search?format=json&q={s}'))
   
   # Make auxiliary label with ipywidgets to display coordinates
   latlon_lbl = ipyw.Label(layout=ipyw.Layout(margin='-20px 0 -10px 0'))
   def handle_interaction(**kwargs):
       if kwargs.get('type') == 'mousemove':
           coordinates = kwargs.get('coordinates')
           lat, lon = round(coordinates[0],3), round(coordinates[1],3)
           latlon_lbl.value = f"lat = {lat},    lon = {lon}"
   m.on_interaction(handle_interaction)
   
   # Display map on widget page
   txt_M = ipyw.HTML(value='<h3>Define query region with map or enter values manually below</h3>')
   txt_m = ipyw.HTML(value='<h4 style="font-weight:normal;">1. Click on square in toolbar to'+
                     ' draw rectangle, then click button below to pass coordinates</h4>',
                     layout=ipyw.Layout(margin='-40px 0 0 0'))
   txt_x = ipyw.HTML(value='<h4 style="font-weight:normal;">2. To draw a new rectangle, delete original '+
                     'with the trash icon and repeat process</h4>',
                     layout=ipyw.Layout(margin='-40px 0 0 0'))
   map_output = ipyw.Output(layout=ipyw.Layout(width='100%'))
   with map_output: display(m)

   # Create coordinate transfer button
   coord_button = ipyw.Button(description='Add coordinates from rectangle to boxes below',
                              tooltip='Click here to transfer lat/lon coordinates from the drawn'+
                              ' rectangle to the query boxes below',layout=ipyw.Layout(width='350px'))

   # Create station plotting button
   stn_button = ipyw.Button(description='Show station locations near drawn region',
                            layout=ipyw.Layout(width='350px'))      
 
   # Define location and lat/lon bounds
   txt_query = ipyw.HTML(value='<h2>Define your query region</h2>',
                         layout=ipyw.Layout(margin='0 0 -10px 0'))
   location_name = ipyw.Text(placeholder='Location name (e.g., New York City)')
   nlat = ipyw.Text(placeholder='Northern latitude (e.g., 41.0)')
   slat = ipyw.Text(placeholder='Southern latitude (e.g., 40.5)')
   wlon = ipyw.Text(placeholder='Western longitude (e.g., -74.2)')
   elon = ipyw.Text(placeholder='Eastern longitude (e.g., -73.7)')
   
   # Create 'submit' button that will run the interactive map widget
   query_button = ipyw.Button(description='Submit (scroll down for content)',
                              tooltip='Click here to start querying data!',
                              style={'description_width': 'initial'},layout=ipyw.Layout(width='220px'))
   query_output = ipyw.Output()
 
   ####################################################################################################
   # Upon click, transfer rectangle's lat/lon from map to query prompts
   ####################################################################################################

   def on_coord_button_clicked(event):
       # Set nlat.value, etc. as the drawn rectangle's coordinates                              
       try: 
          nlat.value = str(round(m.controls[2].data[0]['geometry']['coordinates'][0][1][1],3))
          slat.value = str(round(m.controls[2].data[0]['geometry']['coordinates'][0][0][1],3))
          wlon.value = str(round(m.controls[2].data[0]['geometry']['coordinates'][0][0][0],3))
          elon.value = str(round(m.controls[2].data[0]['geometry']['coordinates'][0][2][0],3))
       except IndexError:
          print('No rectangle drawn yet. Use toolbar to the left to select rectangle.')

   ####################################################################################################
   # Upon click, stations within 1° of bbox will be displayed on map       
   ####################################################################################################
   
   def on_stn_button_clicked(event):
       # Clear previous markers - doesn't seem to be clearing
       for layer in m.layers:
           if isinstance(layer,ipyl.LayerGroup): 
              m.remove_layer(layer)
       # Read in data and process it 
       meta = pd.read_csv(f'{cdv}Extras/Metadata/{var_dpdn.value}.csv')
       stns = pd.DataFrame({'stn': meta.apply(lambda row: f"{row['sids']}: {row['name']}, {row['state']} "+
                             f"({row['sids_type']})\n{var_dpdn.value}: {row['sdate']}, {row['edate']}\n"
                             f"(lat) {row['lat']} (lon) {row['lon']}",axis=1),
                            'lat': meta['lat'],'lon': meta['lon']})
       # Set nlat.value, etc. as the drawn rectangle's coordinates                              
       try: 
           nlat_val = round(m.controls[2].data[0]['geometry']['coordinates'][0][1][1],3)
           slat_val = round(m.controls[2].data[0]['geometry']['coordinates'][0][0][1],3)
           wlon_val = round(m.controls[2].data[0]['geometry']['coordinates'][0][0][0],3)
           elon_val = round(m.controls[2].data[0]['geometry']['coordinates'][0][2][0],3)
       except IndexError:
           print('No rectangle drawn yet. Use toolbar to the left to select rectangle.')
       # Filter by lat/lon
       bbox_stns = stns[(stns['lat'] >= (slat_val - 0.5)) & (stns['lat'] <= (nlat_val + 0.5)) & 
                        (stns['lon'] >= (wlon_val - 1)) & (stns['lon'] <= (elon_val + 1))   ]
       # Add markers based on metadata
       markers = []
       for name, lat, lon in bbox_stns[['stn','lat','lon']].iloc[:,:].values:
           markers.append(ipyl.Marker(location=(lat,lon),draggable=False,title=name,alt=name))
       m.add_layer(ipyl.LayerGroup(layers=markers))

   ####################################################################################################
   # Upon click, interactive query will be activated         
   ####################################################################################################

   def on_query_button_clicked(event):
       with query_output:
           clear_output()
           # Query data
           try:
               var, meta = stndata.bbox_multistn_daily(elem=var_dpdn.value,nlat=nlat.value,slat=slat.value,
                                                       wlon=wlon.value,elon=elon.value,print_md=False, 
                                                       stn_size=stn_size)
           except TypeError:
               print('No stations in bounding box. Try again.')
           
           # Choose which widgets to employ based on variable
           if var_dpdn.value == 'maxt':
               wid_opts = ipyw.Dropdown(options=['Annual Cycle','Time Series'],value='Annual Cycle')
               txt_opts = ipyw.HTML(value='<h3>Plot options for T<sub>MAX</sub></h3>')
               def interactive_widget(opts):
                   if opts == 'Annual Cycle':
                       widgets.annualcycle_tmax_widget(var=var,meta=meta,location_name=location_name.value,
                                           nlat=nlat.value,slat=slat.value,wlon=wlon.value,elon=elon.value)
                   if opts == 'Time Series':
                       widgets.timeseries_tmax_widget(var=var,meta=meta,location_name=location_name.value,
                                           nlat=nlat.value,slat=slat.value,wlon=wlon.value,elon=elon.value)
 
           if var_dpdn.value == 'mint':
               wid_opts = ipyw.Dropdown(options=['Annual Cycle','Time Series'],value='Annual Cycle')
               txt_opts = ipyw.HTML(value='<h3>Plot options for T<sub>MIN</sub></h3>')
               def interactive_widget(opts):
                   if opts == 'Annual Cycle':
                       widgets.annualcycle_tmin_widget(var=var,meta=meta,location_name=location_name.value,
                                           nlat=nlat.value,slat=slat.value,wlon=wlon.value,elon=elon.value)
                   if opts == 'Time Series':
                       widgets.timeseries_tmin_widget(var=var,meta=meta,location_name=location_name.value,
                                           nlat=nlat.value,slat=slat.value,wlon=wlon.value,elon=elon.value)             
 
           if var_dpdn.value == 'pcpn':
               wid_opts = ipyw.Dropdown(options=['Annual Cycle','Cumulative','Time Series','Spatial Map (beta)'],
                                        value='Annual Cycle')
               txt_opts = ipyw.HTML(value='<h3>Plot options for Rain</h3>')
               def interactive_widget(opts):
                   if opts == 'Annual Cycle':
                       widgets.annualcycle_pcpn_widget(var=var,meta=meta,location_name=location_name.value,
                                           nlat=nlat.value,slat=slat.value,wlon=wlon.value,elon=elon.value)
                   if opts == 'Cumulative':
                       widgets.cumulative_pcpn_widget(var=var,meta=meta,location_name=location_name.value,
                                           nlat=nlat.value,slat=slat.value,wlon=wlon.value,elon=elon.value)
                   if opts == 'Time Series':                      
                       widgets.timeseries_pcpn_widget(var=var,meta=meta,location_name=location_name.value,
                                           nlat=nlat.value,slat=slat.value,wlon=wlon.value,elon=elon.value)
                   if opts == 'Spatial Map (beta)':
                       widgets.spatialmap_pcpn_widget(var=var,meta=meta,location_name=location_name.value,
                                           nlat=nlat.value,slat=slat.value,wlon=wlon.value,elon=elon.value)

           if var_dpdn.value == 'snow':
               wid_opts = ipyw.Dropdown(options=['Annual Cycle','Cumulative','Time Series'],
                                        value='Annual Cycle')
               txt_opts = ipyw.HTML(value='<h3>Plot options for Snow</h3>')
               def interactive_widget(opts):
                   if opts == 'Annual Cycle':
                       widgets.annualcycle_snow_widget(var=var,meta=meta,location_name=location_name.value,
                                           nlat=nlat.value,slat=slat.value,wlon=wlon.value,elon=elon.value)
                   if opts == 'Cumulative':
                       widgets.cumulative_snow_widget(var=var,meta=meta,location_name=location_name.value,
                                           nlat=nlat.value,slat=slat.value,wlon=wlon.value,elon=elon.value)
                   if opts == 'Time Series':                      
                       widgets.timeseries_snow_widget(var=var,meta=meta,location_name=location_name.value,
                                           nlat=nlat.value,slat=slat.value,wlon=wlon.value,elon=elon.value) 
   
           # Dropdown menu for plot types
           click_head = ipyw.HTML(value='<h3 style="font-weight:normal;">**Click on each widget header'+
                                  ' for more detail**</h3>',layout=ipyw.Layout(margin='-10px 0 0 0'))
           opts_dpdn = ipyw.VBox([txt_opts,wid_opts,click_head],layout=ipyw.Layout(align_items='center'))
           out = ipyw.interactive_output(interactive_widget,{'opts':wid_opts})
           display(opts_dpdn,out)

           # Define data summary button 
           dsum_button = ipyw.Button(description='Click here for a summary of the data',
                                     style={'description_width':'initial'},
                                     layout=ipyw.Layout(align_content='flex-start',width='300px'))
           dsum_output = ipyw.Output()

           # Define data summary event
           def data_summary(event):
              with dsum_output:
                 stndata.bbox_multistn_dataviz(elem=var_dpdn.value,stndata_df=var,stnmeta_df=meta,
                                               slat=float(slat.value), nlat=float(nlat.value),
                                               wlon=float(wlon.value), elon=float(elon.value), 
                                               map_background='QuadtreeTiles',map_buffer=0.25)
                 plt.show() 
           dsum_button.on_click(data_summary)
           vbox_dsum = ipyw.VBox([dsum_button,dsum_output],layout=ipyw.Layout(justify_content='center'))

           # Display button
           page_summary = ipyw.HBox([vbox_dsum],layout=ipyw.Layout(display='flex',flex_flow='row', 
                                                                   justify_content='flex-start'))
           display(page_summary) 

           # Display disclaimer
           txt_info = ipyw.HTML(value='<h4 style="font-weight:normal;">For questions or to report '+
                                      'errors or bugs that arise while using, please contact '+
                                      'ajthompson@wustl.edu</h4>')
           txt_disc = ipyw.HTML(value='<h4 style="font-weight:normal;">Disclaimer: The information '+
                                      'displayed is obtained from external sources and may contain '+
                                      "inaccuracies. The website's creator assumes no liability for "+
                                      'damages or losses arising from the use of this website.</h4>',
                                layout=ipyw.Layout(margin='-40px 0 0 0'))
           display(ipyw.HBox([ipyw.VBox([txt_info,txt_disc])]))

   ####################################################################################################           
   # Display features prior to submit button being clicked
   ####################################################################################################

   coord_button.on_click(on_coord_button_clicked)
   stn_button.on_click(on_stn_button_clicked)
   query_button.on_click(on_query_button_clicked)
   submit_box = ipyw.VBox([query_button,query_output],layout=ipyw.Layout(align_items='center'))
   page1 = ipyw.VBox([ipyw.VBox([image_header]),
                      ipyw.VBox([txt_link],layout=ipyw.Layout(align_items='center')),
                      ipyw.VBox([txt_var,var_dpdn],layout=ipyw.Layout(align_items='center')),
                      ipyw.VBox([txt_M,txt_m,txt_x,latlon_lbl,map_output],layout=ipyw.Layout(align_items='center')),
                      ipyw.VBox([ipyw.HBox([coord_button,stn_button])],layout=ipyw.Layout(align_items='center')),
                      ipyw.VBox([txt_query,location_name,nlat,slat,wlon,elon,submit_box],
                                layout=ipyw.Layout(align_items='center')),
                      ],layout=ipyw.Layout(display='flex',flex_flow='column',
                                           align_content='space-around',align_items='center'))
   display(page1)

