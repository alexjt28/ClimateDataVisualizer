#######################################################################################################
# 
# Functions for generating standalone widgets
#
#######################################################################################################

# Use this to read in packages from other directories ---------
import sys, os
sys.path.append(os.path.dirname(os.getcwd())) # one dir back
#--------------------------------------------------------------
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Rectangle
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import cartopy, cartopy.mpl.geoaxes, cartopy.io.img_tiles
from ClimateDataVisualizer.dataquery import NOAA_ACIS_stnmeta as stnmeta
from ClimateDataVisualizer.dataquery import NOAA_ACIS_stndata as stndata
from ClimateDataVisualizer.processing.bbox_dy import bbox_avg_dy
from ClimateDataVisualizer.inset_axes.inset_axes import inset_map, inset_timeseries
from ClimateDataVisualizer.interactives import plots
from ClimateDataVisualizer.downloads.file_options import pdf_opts, xcl_opts         
import ipywidgets as ipyw
from IPython.display import display, HTML, clear_output

# URLs to use for user help guides, needs double quotes
url_annualcycle = "https://sites.google.com/view/ajtclimate/climate-data-viz/help-annual-cycle"
url_timeseries  = "https://sites.google.com/view/ajtclimate/climate-data-viz/help-time-series"
url_cumulative  = "https://sites.google.com/view/ajtclimate/climate-data-viz/help-cumulative"
url_spatialmap  = "https://sites.google.com/view/ajtclimate/climate-data-viz/help-spatial-map"
url_map         = "https://sites.google.com/view/ajtclimate/climate-data-viz/help-map-of-stations"
url_yaxis       = "https://sites.google.com/view/ajtclimate/climate-data-viz/help-y-axis"

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
# ANNUAL CYCLE WIDGETS
#
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#======================================================================================================
# annualcycle_tmax_widget
#======================================================================================================

def annualcycle_tmax_widget(var,meta,location_name,nlat,slat,wlon,elon):

    #----------------------------------------------------------------------------------------------
    # Set up parameters to toggle
    #----------------------------------------------------------------------------------------------

    # Define years for historical range
    txt_hist = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_annualcycle} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Define years for historical range</a></h3>')
    text_hist = ipyw.Label(value='Include historical climate?',layout=ipyw.Layout(width='165px'))
    incl_hist = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='60px'))
    text_syr = ipyw.Label(value='Starting Year',layout=ipyw.Layout(width='125px'))
    text_eyr = ipyw.Label(value='Ending Year',layout=ipyw.Layout(width='125px'))
    text_stn = ipyw.Label(value='Minimum number of stations',layout=ipyw.Layout(width='175px'))
    syr = ipyw.Dropdown(options=['earliest',*np.sort(var['Date'].dt.year.unique())[:-1]],
                        value='earliest',layout=ipyw.Layout(width='100px'))
    eyr = ipyw.Dropdown(options=['latest',*np.sort(var['Date'].dt.year.unique())[::-1][1:]],
                        value='latest',layout=ipyw.Layout(width='100px'))
    if len(var.columns) == 2: # 'Date' and 1 data column
       num_stn = ipyw.Dropdown(options=[1],value=1,layout=ipyw.Layout(width='50px'))
    else:
       num_stn = ipyw.Dropdown(options=np.arange(1,len(var.columns)-1),value=1,
                               layout=ipyw.Layout(width='50px'))

    # Plot individual year
    txt_indv = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_annualcycle} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Plot individual year</a></h3>')
    text_year = ipyw.Label(value='Include individual year?',layout=ipyw.Layout(width='150px'))
    incl_year = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='70px'))
    text_iyr = ipyw.Label(value='Year Displayed',layout=ipyw.Layout(width='90px'))
    iyr = ipyw.Dropdown(options=var['Date'].dt.year.unique()[::-1],
                        value=var['Date'].dt.year.unique()[-1],layout=ipyw.Layout(width='70px'))

    # Map
    txt_map   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_map} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Map of stations</a></h3>')
    text_map  = ipyw.Label(value='Include map?',layout=ipyw.Layout(width='100px'))
    incl_map  = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='80px'))
    text_lyr  = ipyw.Label(value='Image tile',layout=ipyw.Layout(width='100px'))
    img_tile  = ipyw.Dropdown(options=['QuadtreeTiles','GoogleTiles','OpenStreetMap','grey'],
                              value='QuadtreeTiles',layout=ipyw.Layout(width='80px'))
    text_lbl = ipyw.Label(value='Label distance',layout=ipyw.Layout(width='100px'))
    lbl_buff = ipyw.Dropdown(options=[('10%',0.1),('20%',0.2),('30%',0.3),('40%',0.4),('50%',0.5),
                                       ('60%',0.6),('70%',0.7),('80%',0.8),('90%',0.9),('None',1.5)],
                              value=0.3,layout=ipyw.Layout(width='80px'))
    text_ext = ipyw.Label(value='Lat/lon buffer',layout=ipyw.Layout(width='100px'))
    ext_buff = ipyw.Dropdown(options=[('0.1°',0.1),('0.25°',0.25),('0.5°',0.5),('1°',1.),('5°',5.)],
                              value=0.5,layout=ipyw.Layout(width='80px'))

    # Y-axis buffer
    txt_buff  = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis buffer</a></h3>')
    maxb_desc = ipyw.Label(value='Buffer above y-axis',layout=ipyw.Layout(width='120px'))
    maxbuff   = ipyw.FloatText(value=20.,layout=ipyw.Layout(width='60px'))
    maxb_unit = ipyw.Label(value='°F')
    minb_desc = ipyw.Label(value='Buffer below y-axis',layout=ipyw.Layout(width='120px'))
    minbuff   = ipyw.FloatText(value=20.,layout=ipyw.Layout(width='60px'))
    minb_unit = ipyw.Label(value='°F')

    # Y-axis tick stride
    txt_tick   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis tick stride</a></h3>')
    majtk_desc = ipyw.Label(value='Major tick stride',layout=ipyw.Layout(width='120px'))
    majtick    = ipyw.FloatText(value=20.,layout=ipyw.Layout(width='60px'))
    majtk_unit = ipyw.Label(value='°F')
    mintk_desc = ipyw.Label(value='Minor tick stride',layout=ipyw.Layout(width='120px'))
    mintick    = ipyw.FloatText(value=5.,layout=ipyw.Layout(width='60px'))
    mintk_unit = ipyw.Label(value='°F')    
    
    # Extras     
    txt_xtra  = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_annualcycle} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Extras</a></h3>')
    text_info = ipyw.Label(value='Include info for year?',layout=ipyw.Layout(width='130px'))
    incl_info = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='70px'))

    #----------------------------------------------------------------------------------------------
    # Layout for dropdowns
    #----------------------------------------------------------------------------------------------

    ui = ipyw.VBox([
                    # FIRST ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Define years for historical range
                                 ipyw.HBox([txt_hist],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_hist,incl_hist],layout=ipyw.Layout(
                                                                        justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_syr,syr]),
                                                       ipyw.HBox([text_eyr,eyr]),
                                                       ipyw.HBox([text_stn,num_stn])])],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Plot individual year
                                 ipyw.HBox([txt_indv],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_year,incl_year],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_iyr,iyr],
                                           layout=ipyw.Layout(justify_content='space-between'))]),
                               ipyw.VBox([
                                 # Map 
                                 ipyw.HBox([txt_map],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_map,incl_map]),
                                                       ipyw.HBox([text_lyr,img_tile]),
                                                       ipyw.HBox([text_lbl,lbl_buff]),
                                                       ipyw.HBox([text_ext,ext_buff])])])])],                                   
                               layout=ipyw.Layout(justify_content='space-around')),            
                    # SECOND ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Y-axis buffer
                                 ipyw.HBox([txt_buff],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([maxb_desc,maxbuff,maxb_unit]),
                                                       ipyw.HBox([minb_desc,minbuff,minb_unit])])],
                                           layout=ipyw.Layout(flex='1 1 auto',
                                                              justify_content='center'))]),
                               ipyw.VBox([
                                 # Y-axis tick stride
                                 ipyw.HBox([txt_tick],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([majtk_desc,majtick,majtk_unit]),
                                                       ipyw.HBox([mintk_desc,mintick,mintk_unit])])],
                                            layout=ipyw.Layout(flex='1 1 auto',
                                                               justify_content='space-between'))]),
                               ipyw.VBox([
                                 # Extras
                                 ipyw.HBox([txt_xtra],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_info,incl_info],
                                           layout=ipyw.Layout(justify_content='center'))])],
                               layout=ipyw.Layout(justify_content='space-around'))
                     ])

    #----------------------------------------------------------------------------------------------
    # Display interactive plot
    #----------------------------------------------------------------------------------------------

    # Define function with only interactive components that runs widget.plot function
    def plot_fig(syr,eyr,num_stn,iyr,minbuff,maxbuff,majtick,mintick,incl_hist,incl_year,
                 incl_info,incl_map,img_tile,lbl_buff,ext_buff):
        fig,var_dy,var_max,var_95,var_avg,var_05,var_min = plots.annualcycle_tmax_plot(
                     var=var,meta=meta,location_name=location_name,nlat=float(nlat),
                     slat=float(slat),wlon=float(wlon),elon=float(elon),syr=syr,eyr=eyr,
                     num_stn=num_stn,iyr=iyr,minbuff=minbuff,maxbuff=maxbuff,majtick=majtick,
                     mintick=mintick,incl_hist=incl_hist,incl_year=incl_year,incl_info=incl_info,
                     incl_map=incl_map,img_tile=img_tile,lbl_buff=lbl_buff,ext_buff=ext_buff)

        # Create a button widget to download the figure as PDF
        pdf_output = ipyw.Output()
        def download_pdf(button):
           pdf_filename = 'figure.pdf'
           pdf_opts(fig=fig,pdf_output=pdf_output,pdf_filename=pdf_filename)
        pdf_but = ipyw.Button(description='Download Figure', layout={'width': '140px'})
        pdf_but.on_click(download_pdf)

        # Create a button widget to download data as Excel
        xcl_output = ipyw.Output()
        def download_xcl(button):
            with xcl_output: print('Download initiated. Can take more than a minute if over 100 stations '+
                                   'are queried. Do not click download button again.')
            xcl_filename = 'data.xlsx'
            with pd.ExcelWriter(xcl_filename) as w:
                var.assign(**{var.columns[0]: var.iloc[:,0].astype(str)}).to_excel(w,sheet_name='stations',index=False)
                meta.to_excel(w,sheet_name='metadata',index=False)
                if incl_hist == True:
                   pd.concat([pd.DataFrame({'month':var_dy['month'],'day':var_dy['day'],'max':var_max,'95th':var_95,
                                            'mean':var_avg,'5th':var_05,'min':var_min}),var_dy.iloc[:,2:]],axis=1
                             ).to_excel(w,sheet_name='historical',index=False)
                if incl_year == True:
                   pd.DataFrame({'month':var_dy['month'],'day':var_dy['day'],str(iyr):var_dy[str(iyr)]}
                                ).to_excel(w,sheet_name=str(iyr),index=False)
            xcl_opts(xcl_filename=xcl_filename,xcl_output=xcl_output)
        xcl_but = ipyw.Button(description='Download Data',layout=ipyw.Layout(width='140px'))
        xcl_but.on_click(download_xcl)

        # Display download buttons together
        button_box = ipyw.VBox([ipyw.HBox([pdf_but,xcl_but],layout=ipyw.Layout(justify_content='center'))])
        display(button_box,pdf_output,xcl_output)

    # Interactive output with only interactive components in dictionary
    out = ipyw.interactive_output(plot_fig,{'syr':syr,'eyr':eyr,'num_stn':num_stn,'iyr':iyr,
                                            'minbuff':minbuff,'maxbuff':maxbuff,'majtick':majtick,
                                            'mintick':mintick,'incl_hist':incl_hist,'incl_year':incl_year,
                                            'incl_info':incl_info,'incl_map':incl_map,'img_tile':img_tile,
                                            'lbl_buff':lbl_buff,'ext_buff':ext_buff})
    display(ui,out)

#======================================================================================================
# annualcycle_tmin_widget
#======================================================================================================

def annualcycle_tmin_widget(var,meta,location_name,nlat,slat,wlon,elon):

    #----------------------------------------------------------------------------------------------
    # Set up parameters to toggle
    #----------------------------------------------------------------------------------------------

    # Define years for historical range
    txt_hist = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_annualcycle} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Define years for historical range</a></h3>')
    text_hist = ipyw.Label(value='Include historical climate?',layout=ipyw.Layout(width='165px'))
    incl_hist = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='60px'))
    text_syr = ipyw.Label(value='Starting Year',layout=ipyw.Layout(width='125px'))
    text_eyr = ipyw.Label(value='Ending Year',layout=ipyw.Layout(width='125px'))
    text_stn = ipyw.Label(value='Minimum number of stations',layout=ipyw.Layout(width='175px'))
    syr = ipyw.Dropdown(options=['earliest',*np.sort(var['Date'].dt.year.unique())[:-1]],
                        value='earliest',layout=ipyw.Layout(width='100px'))
    eyr = ipyw.Dropdown(options=['latest',*np.sort(var['Date'].dt.year.unique())[::-1][1:]],
                        value='latest',layout=ipyw.Layout(width='100px'))
    if len(var.columns) == 2: # 'Date' and 1 data column
       num_stn = ipyw.Dropdown(options=[1],value=1,layout=ipyw.Layout(width='50px'))
    else:
       num_stn = ipyw.Dropdown(options=np.arange(1,len(var.columns)-1),value=1,
                               layout=ipyw.Layout(width='50px'))

    # Plot individual year
    txt_indv = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_annualcycle} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Plot individual year</a></h3>')
    text_year = ipyw.Label(value='Include individual year?',layout=ipyw.Layout(width='150px'))
    incl_year = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='70px'))
    text_iyr = ipyw.Label(value='Year Displayed',layout=ipyw.Layout(width='90px'))
    iyr = ipyw.Dropdown(options=var['Date'].dt.year.unique()[::-1],
                        value=var['Date'].dt.year.unique()[-1],layout=ipyw.Layout(width='70px'))

    # Map
    txt_map   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_map} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Map of stations</a></h3>')
    text_map  = ipyw.Label(value='Include map?',layout=ipyw.Layout(width='100px'))
    incl_map  = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='80px'))
    text_lyr  = ipyw.Label(value='Image tile',layout=ipyw.Layout(width='100px'))
    img_tile  = ipyw.Dropdown(options=['QuadtreeTiles','GoogleTiles','OpenStreetMap','grey'],
                              value='QuadtreeTiles',layout=ipyw.Layout(width='80px'))
    text_lbl = ipyw.Label(value='Label distance',layout=ipyw.Layout(width='100px'))
    lbl_buff = ipyw.Dropdown(options=[('10%',0.1),('20%',0.2),('30%',0.3),('40%',0.4),('50%',0.5),
                                       ('60%',0.6),('70%',0.7),('80%',0.8),('90%',0.9),('None',1.5)],
                              value=0.3,layout=ipyw.Layout(width='80px'))
    text_ext = ipyw.Label(value='Lat/lon buffer',layout=ipyw.Layout(width='100px'))
    ext_buff = ipyw.Dropdown(options=[('0.1°',0.1),('0.25°',0.25),('0.5°',0.5),('1°',1.),('5°',5.)],
                              value=0.5,layout=ipyw.Layout(width='80px'))

    # Y-axis buffer
    txt_buff  = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis buffer</a></h3>')
    maxb_desc = ipyw.Label(value='Buffer above y-axis',layout=ipyw.Layout(width='120px'))
    maxbuff   = ipyw.FloatText(value=20.,layout=ipyw.Layout(width='60px'))
    maxb_unit = ipyw.Label(value='°F')
    minb_desc = ipyw.Label(value='Buffer below y-axis',layout=ipyw.Layout(width='120px'))
    minbuff   = ipyw.FloatText(value=20.,layout=ipyw.Layout(width='60px'))
    minb_unit = ipyw.Label(value='°F')

    # Y-axis tick stride
    txt_tick   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis tick stride</a></h3>')
    majtk_desc = ipyw.Label(value='Major tick stride',layout=ipyw.Layout(width='120px'))
    majtick    = ipyw.FloatText(value=20.,layout=ipyw.Layout(width='60px'))
    majtk_unit = ipyw.Label(value='°F')
    mintk_desc = ipyw.Label(value='Minor tick stride',layout=ipyw.Layout(width='120px'))
    mintick    = ipyw.FloatText(value=5.,layout=ipyw.Layout(width='60px'))
    mintk_unit = ipyw.Label(value='°F')

    # Extras     
    txt_xtra  = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_annualcycle} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Extras</a></h3>')
    text_info = ipyw.Label(value='Include info for year?',layout=ipyw.Layout(width='130px'))
    incl_info = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='70px'))

    #----------------------------------------------------------------------------------------------
    # Layout for dropdowns
    #----------------------------------------------------------------------------------------------

    ui = ipyw.VBox([
                    # FIRST ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Define years for historical range
                                 ipyw.HBox([txt_hist],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_hist,incl_hist],layout=ipyw.Layout(
                                                                        justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_syr,syr]),
                                                       ipyw.HBox([text_eyr,eyr]),
                                                       ipyw.HBox([text_stn,num_stn])])],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Plot individual year
                                 ipyw.HBox([txt_indv],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_year,incl_year],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_iyr,iyr],
                                           layout=ipyw.Layout(justify_content='space-between'))]),
                               ipyw.VBox([
                                 # Map 
                                 ipyw.HBox([txt_map],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_map,incl_map]),
                                                       ipyw.HBox([text_lyr,img_tile]),
                                                       ipyw.HBox([text_lbl,lbl_buff]),
                                                       ipyw.HBox([text_ext,ext_buff])])])])],
                               layout=ipyw.Layout(justify_content='space-around')),

                    # SECOND ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Y-axis buffer
                                 ipyw.HBox([txt_buff],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([maxb_desc,maxbuff,maxb_unit]),
                                                       ipyw.HBox([minb_desc,minbuff,minb_unit])])],
                                           layout=ipyw.Layout(flex='1 1 auto',
                                                              justify_content='center'))]),
                               ipyw.VBox([
                                 # Y-axis tick stride
                                 ipyw.HBox([txt_tick],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([majtk_desc,majtick,majtk_unit]),
                                                       ipyw.HBox([mintk_desc,mintick,mintk_unit])])],
                                            layout=ipyw.Layout(flex='1 1 auto',
                                                               justify_content='space-between'))]),
                               ipyw.VBox([
                                 # Extras
                                 ipyw.HBox([txt_xtra],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_info,incl_info],
                                           layout=ipyw.Layout(justify_content='center'))])],
                               layout=ipyw.Layout(justify_content='space-around'))
                     ])

    #----------------------------------------------------------------------------------------------
    # Display interactive plot
    #----------------------------------------------------------------------------------------------

    # Define function with only interactive components that runs widget.plot function
    def plot_fig(syr,eyr,num_stn,iyr,minbuff,maxbuff,majtick,mintick,incl_hist,incl_year,
                 incl_info,incl_map,img_tile,lbl_buff,ext_buff):
        fig,var_dy,var_max,var_95,var_avg,var_05,var_min = plots.annualcycle_tmin_plot(
                     var=var,meta=meta,location_name=location_name,nlat=float(nlat),
                     slat=float(slat),wlon=float(wlon),elon=float(elon),syr=syr,eyr=eyr,
                     num_stn=num_stn,iyr=iyr,minbuff=minbuff,maxbuff=maxbuff,majtick=majtick,
                     mintick=mintick,incl_hist=incl_hist,incl_year=incl_year,incl_info=incl_info,
                     incl_map=incl_map,img_tile=img_tile,lbl_buff=lbl_buff,ext_buff=ext_buff)

        # Create a button widget to download the figure as PDF
        pdf_output = ipyw.Output()
        def download_pdf(button):
           pdf_filename = 'figure.pdf'
           pdf_opts(fig=fig,pdf_output=pdf_output,pdf_filename=pdf_filename)
        pdf_but = ipyw.Button(description='Download Figure', layout={'width': '140px'})
        pdf_but.on_click(download_pdf)

        # Create a button widget to download data as Excel
        xcl_output = ipyw.Output()
        def download_xcl(button):
            with xcl_output: print('Download initiated. Can take more than a minute if over 100 stations '+
                                   'are queried. Do not click download button again.')
            xcl_filename = 'data.xlsx'
            with pd.ExcelWriter(xcl_filename) as w:
                var.assign(**{var.columns[0]: var.iloc[:,0].astype(str)}).to_excel(w,sheet_name='stations',index=False)
                meta.to_excel(w,sheet_name='metadata',index=False)
                if incl_hist == True:
                   pd.concat([pd.DataFrame({'month':var_dy['month'],'day':var_dy['day'],'max':var_max,'95th':var_95,
                                            'mean':var_avg,'5th':var_05,'min':var_min}),var_dy.iloc[:,2:]],axis=1
                             ).to_excel(w,sheet_name='historical',index=False)
                if incl_year == True:
                   pd.DataFrame({'month':var_dy['month'],'day':var_dy['day'],str(iyr):var_dy[str(iyr)]}
                                ).to_excel(w,sheet_name=str(iyr),index=False)
            xcl_opts(xcl_filename=xcl_filename,xcl_output=xcl_output)
        xcl_but = ipyw.Button(description='Download Data',layout=ipyw.Layout(width='140px'))
        xcl_but.on_click(download_xcl)

        # Display download buttons together
        button_box = ipyw.VBox([ipyw.HBox([pdf_but,xcl_but],layout=ipyw.Layout(justify_content='center'))])
        display(button_box,pdf_output,xcl_output)



    # Interactive output with only interactive components in dictionary
    out = ipyw.interactive_output(plot_fig,{'syr':syr,'eyr':eyr,'num_stn':num_stn,'iyr':iyr,
                                            'minbuff':minbuff,'maxbuff':maxbuff,'majtick':majtick,
                                            'mintick':mintick,'incl_hist':incl_hist,'incl_year':incl_year,
                                            'incl_info':incl_info,'incl_map':incl_map,'img_tile':img_tile,
                                            'lbl_buff':lbl_buff,'ext_buff':ext_buff})
    display(ui,out)

#======================================================================================================
# annualcycle_rain_widget
#======================================================================================================

def annualcycle_pcpn_widget(var,meta,location_name,nlat,slat,wlon,elon):

    #----------------------------------------------------------------------------------------------
    # Set up parameters to toggle
    #----------------------------------------------------------------------------------------------

    # What type of rainfall data?
    txt_rain = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_annualcycle} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>What type of rainfall data?</a></h3>')
    text_type = ipyw.Label(value='Select type',layout=ipyw.Layout(width='80px'))
    rain_type = ipyw.Dropdown(options=[('All days','all'),('Rain days (>0)','rain'),
                                       ('Wettest N Days','wetNday')],value='rain',
                              layout=ipyw.Layout(width='120px'))
    text_nday = ipyw.Label(value='N Days (if selected)',layout=ipyw.Layout(width='120px'))
    nday      = ipyw.Dropdown(options=list(np.arange(1,101)),value=5,
                              layout=ipyw.Layout(width='80px'))
    
    # Define years for historical range
    txt_hist = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_annualcycle} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Define years for historical range</a></h3>')
    text_hist = ipyw.Label(value='Include historical climate?',layout=ipyw.Layout(width='165px'))
    incl_hist = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='60px'))
    text_syr = ipyw.Label(value='Starting Year',layout=ipyw.Layout(width='125px'))
    text_eyr = ipyw.Label(value='Ending Year',layout=ipyw.Layout(width='125px'))
    text_stn = ipyw.Label(value='Minimum number of stations',layout=ipyw.Layout(width='175px'))
    syr = ipyw.Dropdown(options=['earliest',*np.sort(var['Date'].dt.year.unique())[:-1]],
                        value='earliest',layout=ipyw.Layout(width='100px'))
    eyr = ipyw.Dropdown(options=['latest',*np.sort(var['Date'].dt.year.unique())[::-1][1:]],
                        value='latest',layout=ipyw.Layout(width='100px'))
    if len(var.columns) == 2: # 'Date' and 1 data column
       num_stn = ipyw.Dropdown(options=[1],value=1,layout=ipyw.Layout(width='50px'))
    else:
       num_stn = ipyw.Dropdown(options=np.arange(1,len(var.columns)-1),value=1,
                               layout=ipyw.Layout(width='50px'))

    # Plot individual year
    txt_indv = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_annualcycle} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Plot individual year</a></h3>')
    text_year = ipyw.Label(value='Include individual year?',layout=ipyw.Layout(width='150px'))
    incl_year = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='70px'))
    text_iyr = ipyw.Label(value='Year Displayed',layout=ipyw.Layout(width='90px'))
    iyr = ipyw.Dropdown(options=var['Date'].dt.year.unique()[::-1],
                        value=var['Date'].dt.year.unique()[-1],layout=ipyw.Layout(width='70px'))

    # Y-axis buffer
    txt_buff  = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis buffer</a></h3>')
    maxb_desc = ipyw.Label(value='Buffer above y-axis',layout=ipyw.Layout(width='120px'))
    maxbuff   = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    maxb_unit = ipyw.Label(value='in')
    minb_desc = ipyw.Label(value='Buffer below y-axis',layout=ipyw.Layout(width='120px'))
    minbuff   = ipyw.FloatText(value=0.,layout=ipyw.Layout(width='60px'))
    minb_unit = ipyw.Label(value='in')

    # Y-axis tick stride
    txt_tick   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis tick stride</a></h3>')
    majtk_desc = ipyw.Label(value='Major tick stride',layout=ipyw.Layout(width='120px'))
    majtick    = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    majtk_unit = ipyw.Label(value='in')
    mintk_desc = ipyw.Label(value='Minor tick stride',layout=ipyw.Layout(width='120px'))
    mintick    = ipyw.FloatText(value=0.5,layout=ipyw.Layout(width='60px'))
    mintk_unit = ipyw.Label(value='in')
    
    # Map
    txt_map   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_map} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Map of stations</a></h3>')
    text_map  = ipyw.Label(value='Include map?',layout=ipyw.Layout(width='100px'))
    incl_map  = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='80px'))
    text_lyr  = ipyw.Label(value='Image tile',layout=ipyw.Layout(width='100px'))
    img_tile  = ipyw.Dropdown(options=['QuadtreeTiles','GoogleTiles','OpenStreetMap','grey'],
                              value='QuadtreeTiles',layout=ipyw.Layout(width='80px'))
    text_lbl = ipyw.Label(value='Label distance',layout=ipyw.Layout(width='100px'))
    lbl_buff = ipyw.Dropdown(options=[('10%',0.1),('20%',0.2),('30%',0.3),('40%',0.4),('50%',0.5),
                                       ('60%',0.6),('70%',0.7),('80%',0.8),('90%',0.9),('None',1.5)],
                              value=0.3,layout=ipyw.Layout(width='80px'))
    text_ext = ipyw.Label(value='Lat/lon buffer',layout=ipyw.Layout(width='100px'))
    ext_buff = ipyw.Dropdown(options=[('0.1°',0.1),('0.25°',0.25),('0.5°',0.5),('1°',1.),('5°',5.)],
                              value=0.5,layout=ipyw.Layout(width='80px'))

    #----------------------------------------------------------------------------------------------
    # Layout for dropdowns
    #----------------------------------------------------------------------------------------------

    ui = ipyw.VBox([
                    # FIRST ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Define rainfall data
                                 ipyw.HBox([txt_rain],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_type,rain_type],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_nday,nday],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([ 
                                 # Define years for historical range
                                 ipyw.HBox([txt_hist],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_hist,incl_hist],layout=ipyw.Layout(
                                                                        justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_syr,syr]),
                                                       ipyw.HBox([text_eyr,eyr]),
                                                       ipyw.HBox([text_stn,num_stn])])],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Plot individual year
                                 ipyw.HBox([txt_indv],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_year,incl_year],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_iyr,iyr],
                                           layout=ipyw.Layout(justify_content='space-between'))])],
                               layout=ipyw.Layout(justify_content='space-around')),
                    # SECOND ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Y-axis buffer
                                 ipyw.HBox([txt_buff],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([maxb_desc,maxbuff,maxb_unit]),
                                                       ipyw.HBox([minb_desc,minbuff,minb_unit])])],
                                           layout=ipyw.Layout(flex='1 1 auto',
                                                              justify_content='center'))]),
                               ipyw.VBox([
                                 # Y-axis tick stride
                                 ipyw.HBox([txt_tick],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([majtk_desc,majtick,majtk_unit]),
                                                       ipyw.HBox([mintk_desc,mintick,mintk_unit])])],
                                            layout=ipyw.Layout(flex='1 1 auto',
                                                               justify_content='space-between'))]),
                               ipyw.VBox([
                                 # Map 
                                 ipyw.HBox([txt_map],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_map,incl_map]),
                                                       ipyw.HBox([text_lyr,img_tile]),
                                                       ipyw.HBox([text_lbl,lbl_buff]),
                                                       ipyw.HBox([text_ext,ext_buff])])])])],
                               layout=ipyw.Layout(justify_content='space-around'))
                     ])

    #----------------------------------------------------------------------------------------------
    # Display interactive plot
    #----------------------------------------------------------------------------------------------

    # Define function with only interactive components that runs widget.plot function
    def plot_fig(rain_type,nday,syr,eyr,num_stn,iyr,minbuff,maxbuff,majtick,mintick,incl_hist,
                 incl_year,incl_map,img_tile,lbl_buff,ext_buff):
        
        if rain_type == 'all' or rain_type == 'rain':
            fig,var_dy,var_max,var_95,var_avg = plots.annualcycle_pcpn_plot(
                     var=var,meta=meta,rain_type=rain_type,nday=nday,location_name=location_name,
                     nlat=float(nlat),slat=float(slat),wlon=float(wlon),elon=float(elon),
                     syr=syr,eyr=eyr,num_stn=num_stn,iyr=iyr,minbuff=minbuff,maxbuff=maxbuff,
                     majtick=majtick,mintick=mintick,incl_hist=incl_hist,incl_year=incl_year,
                     incl_map=incl_map,img_tile=img_tile,lbl_buff=lbl_buff,ext_buff=ext_buff)
        if rain_type == 'wetNday':
            fig,var_dy,var_max,var_min = plots.annualcycle_pcpn_plot(
                     var=var,meta=meta,rain_type=rain_type,nday=nday,location_name=location_name,
                     nlat=float(nlat),slat=float(slat),wlon=float(wlon),elon=float(elon),
                     syr=syr,eyr=eyr,num_stn=num_stn,iyr=iyr,minbuff=minbuff,maxbuff=maxbuff,
                     majtick=majtick,mintick=mintick,incl_hist=incl_hist,incl_year=incl_year,
                     incl_map=incl_map,img_tile=img_tile,lbl_buff=lbl_buff,ext_buff=ext_buff)

        # Create a button widget to download the figure as PDF
        pdf_output = ipyw.Output()
        def download_pdf(button):
           pdf_filename = 'figure.pdf'
           pdf_opts(fig=fig,pdf_output=pdf_output,pdf_filename=pdf_filename)
        pdf_but = ipyw.Button(description='Download Figure', layout={'width': '140px'})
        pdf_but.on_click(download_pdf)

        # Create a button widget to download data as Excel
        xcl_output = ipyw.Output()
        def download_xcl(button):
            with xcl_output: print('Download initiated. Can take more than a minute if over 100 stations '+
                                   'are queried. Do not click download button again.')
            xcl_filename = 'data.xlsx'
            with pd.ExcelWriter(xcl_filename) as w:
                var.assign(**{var.columns[0]: var.iloc[:,0].astype(str)}
                           ).to_excel(w,sheet_name='stations',index=False)
                meta.to_excel(w,sheet_name='metadata',index=False)
                if incl_hist == True:
                    if rain_type == 'all' or rain_type == 'rain':
                        pd.concat([pd.DataFrame({'month':var_dy['month'],'day':var_dy['day'],'max':var_max,
                                                 '95th':var_95,'mean':var_avg}),var_dy.iloc[:,2:]],axis=1
                                  ).to_excel(w,sheet_name='historical',index=False)
                    if rain_type == 'wetNday':
                        sup = 'st' if nday == 1 else ('nd' if nday == 2 else ('rd' if nday == 3 else 'th'))
                        pd.concat([pd.DataFrame({'month':var_dy['month'],'day':var_dy['day'],
                                                 'Wettest Day':var_max,str(nday)+f'{sup} Wettest Day':var_min}),
                                   var_dy.iloc[:,2:]],axis=1).to_excel(w,sheet_name='historical',index=False)
                if incl_year == True:
                    pd.DataFrame({'month':var_dy['month'],'day':var_dy['day'],str(iyr):var_dy[str(iyr)]}
                                ).to_excel(w,sheet_name=str(iyr),index=False)
            xcl_opts(xcl_filename=xcl_filename,xcl_output=xcl_output)
        xcl_but = ipyw.Button(description='Download Data',layout=ipyw.Layout(width='140px'))
        xcl_but.on_click(download_xcl)

        # Display download buttons together
        button_box = ipyw.VBox([ipyw.HBox([pdf_but,xcl_but],layout=ipyw.Layout(justify_content='center'))])
        display(button_box,pdf_output,xcl_output)

    # Interactive output with only interactive components in dictionary
    out = ipyw.interactive_output(plot_fig,{'rain_type':rain_type,'nday':nday,'syr':syr,'eyr':eyr,
                                            'num_stn':num_stn,'iyr':iyr,'minbuff':minbuff,
                                            'maxbuff':maxbuff,'majtick':majtick,'mintick':mintick,
                                            'incl_hist':incl_hist,'incl_year':incl_year,
                                            'incl_map':incl_map,'img_tile':img_tile,
                                            'lbl_buff':lbl_buff,'ext_buff':ext_buff})
    display(ui,out)

#======================================================================================================
# annualcycle_snow_widget
#======================================================================================================

def annualcycle_snow_widget(var,meta,location_name,nlat,slat,wlon,elon):

    #----------------------------------------------------------------------------------------------
    # Set up parameters to toggle
    #----------------------------------------------------------------------------------------------

    # What type of snowfall data?
    txt_snow = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_annualcycle} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>What type of snowfall data?</a></h3>')
    text_type = ipyw.Label(value='Select type',layout=ipyw.Layout(width='80px'))
    snow_type = ipyw.Dropdown(options=[('All days','all'),('Snow days (>0)','snow'),
                                       ('Heaviest N Days','wetNday')],value='snow',
                              layout=ipyw.Layout(width='120px'))
    text_nday = ipyw.Label(value='N Days (if selected)',layout=ipyw.Layout(width='120px'))
    nday      = ipyw.Dropdown(options=list(np.arange(1,101)),value=5,
                              layout=ipyw.Layout(width='80px'))

    # Define years for historical range
    txt_hist = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_annualcycle} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Define years for historical range</a></h3>')
    text_hist = ipyw.Label(value='Include historical climate?',layout=ipyw.Layout(width='165px'))
    incl_hist = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='60px'))
    text_syr = ipyw.Label(value='Starting Year',layout=ipyw.Layout(width='125px'))
    text_eyr = ipyw.Label(value='Ending Year',layout=ipyw.Layout(width='125px'))
    text_stn = ipyw.Label(value='Minimum number of stations',layout=ipyw.Layout(width='175px'))
    syr = ipyw.Dropdown(options=['earliest',*np.sort(var['Date'].dt.year.unique())[:-1]],
                        value='earliest',layout=ipyw.Layout(width='100px'))
    eyr = ipyw.Dropdown(options=['latest',*np.sort(var['Date'].dt.year.unique())[::-1][1:]],
                        value='latest',layout=ipyw.Layout(width='100px'))
    if len(var.columns) == 2: # 'Date' and 1 data column
       num_stn = ipyw.Dropdown(options=[1],value=1,layout=ipyw.Layout(width='50px'))
    else:
       num_stn = ipyw.Dropdown(options=np.arange(1,len(var.columns)-1),value=1,
                               layout=ipyw.Layout(width='50px'))

    # Plot individual year
    txt_indv = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_annualcycle} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Plot individual year</a></h3>')
    text_year = ipyw.Label(value='Include individual year?',layout=ipyw.Layout(width='150px'))
    incl_year = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='70px'))
    text_iyr = ipyw.Label(value='Year Displayed',layout=ipyw.Layout(width='90px'))
    iyr = ipyw.Dropdown(options=var['Date'].dt.year.unique()[::-1],
                        value=var['Date'].dt.year.unique()[-1],layout=ipyw.Layout(width='70px'))

    # Y-axis buffer
    txt_buff  = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis buffer</a></h3>')
    maxb_desc = ipyw.Label(value='Buffer above y-axis',layout=ipyw.Layout(width='120px'))
    maxbuff   = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    maxb_unit = ipyw.Label(value='in')
    minb_desc = ipyw.Label(value='Buffer below y-axis',layout=ipyw.Layout(width='120px'))
    minbuff   = ipyw.FloatText(value=0.,layout=ipyw.Layout(width='60px'))
    minb_unit = ipyw.Label(value='in')

    # Y-axis tick stride
    txt_tick   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis tick stride</a></h3>')
    majtk_desc = ipyw.Label(value='Major tick stride',layout=ipyw.Layout(width='120px'))
    majtick    = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    majtk_unit = ipyw.Label(value='in')
    mintk_desc = ipyw.Label(value='Minor tick stride',layout=ipyw.Layout(width='120px'))
    mintick    = ipyw.FloatText(value=0.5,layout=ipyw.Layout(width='60px'))
    mintk_unit = ipyw.Label(value='in')

    # Map
    txt_map   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_map} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Map of stations</a></h3>')
    text_map  = ipyw.Label(value='Include map?',layout=ipyw.Layout(width='100px'))
    incl_map  = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='80px'))
    text_lyr  = ipyw.Label(value='Image tile',layout=ipyw.Layout(width='100px'))
    img_tile  = ipyw.Dropdown(options=['QuadtreeTiles','GoogleTiles','OpenStreetMap','grey'],
                              value='QuadtreeTiles',layout=ipyw.Layout(width='80px'))
    text_lbl = ipyw.Label(value='Label distance',layout=ipyw.Layout(width='100px'))
    lbl_buff = ipyw.Dropdown(options=[('10%',0.1),('20%',0.2),('30%',0.3),('40%',0.4),('50%',0.5),
                                       ('60%',0.6),('70%',0.7),('80%',0.8),('90%',0.9),('None',1.5)],
                              value=0.3,layout=ipyw.Layout(width='80px'))
    text_ext = ipyw.Label(value='Lat/lon buffer',layout=ipyw.Layout(width='100px'))
    ext_buff = ipyw.Dropdown(options=[('0.1°',0.1),('0.25°',0.25),('0.5°',0.5),('1°',1.),('5°',5.)],
                              value=0.5,layout=ipyw.Layout(width='80px'))

    #----------------------------------------------------------------------------------------------
    # Layout for dropdowns
    #----------------------------------------------------------------------------------------------

    ui = ipyw.VBox([
                    # FIRST ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Define snowfall data
                                 ipyw.HBox([txt_snow],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_type,snow_type],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_nday,nday],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Define years for historical range
                                 ipyw.HBox([txt_hist],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_hist,incl_hist],layout=ipyw.Layout(
                                                                        justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_syr,syr]),
                                                       ipyw.HBox([text_eyr,eyr]),
                                                       ipyw.HBox([text_stn,num_stn])])],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Plot individual year
                                 ipyw.HBox([txt_indv],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_year,incl_year],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_iyr,iyr],
                                           layout=ipyw.Layout(justify_content='space-between'))])],
                               layout=ipyw.Layout(justify_content='space-around')),
                    # SECOND ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Y-axis buffer
                                 ipyw.HBox([txt_buff],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([maxb_desc,maxbuff,maxb_unit]),
                                                       ipyw.HBox([minb_desc,minbuff,minb_unit])])],
                                           layout=ipyw.Layout(flex='1 1 auto',
                                                              justify_content='center'))]),
                               ipyw.VBox([
                                 # Y-axis tick stride
                                 ipyw.HBox([txt_tick],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([majtk_desc,majtick,majtk_unit]),
                                                       ipyw.HBox([mintk_desc,mintick,mintk_unit])])],
                                            layout=ipyw.Layout(flex='1 1 auto',
                                                               justify_content='space-between'))]),
                               ipyw.VBox([
                                 # Map 
                                 ipyw.HBox([txt_map],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_map,incl_map]),
                                                       ipyw.HBox([text_lyr,img_tile]),
                                                       ipyw.HBox([text_lbl,lbl_buff]),
                                                       ipyw.HBox([text_ext,ext_buff])])])])],
                               layout=ipyw.Layout(justify_content='space-around'))
                     ])

    #----------------------------------------------------------------------------------------------
    # Display interactive plot
    #----------------------------------------------------------------------------------------------

    # Define function with only interactive components that runs widget.plot function
    def plot_fig(snow_type,nday,syr,eyr,num_stn,iyr,minbuff,maxbuff,majtick,mintick,incl_hist,
                 incl_year,incl_map,img_tile,lbl_buff,ext_buff):

        if snow_type == 'all' or snow_type == 'snow':
            fig,var_dy,var_max,var_95,var_avg = plots.annualcycle_snow_plot(
                     var=var,meta=meta,snow_type=snow_type,nday=nday,location_name=location_name,
                     nlat=float(nlat),slat=float(slat),wlon=float(wlon),elon=float(elon),
                     syr=syr,eyr=eyr,num_stn=num_stn,iyr=iyr,minbuff=minbuff,maxbuff=maxbuff,
                     majtick=majtick,mintick=mintick,incl_hist=incl_hist,incl_year=incl_year,
                     incl_map=incl_map,img_tile=img_tile,lbl_buff=lbl_buff,ext_buff=ext_buff)
        if snow_type == 'wetNday':
            fig,var_dy,var_max,var_min = plots.annualcycle_snow_plot(
                     var=var,meta=meta,snow_type=snow_type,nday=nday,location_name=location_name,
                     nlat=float(nlat),slat=float(slat),wlon=float(wlon),elon=float(elon),
                     syr=syr,eyr=eyr,num_stn=num_stn,iyr=iyr,minbuff=minbuff,maxbuff=maxbuff,
                     majtick=majtick,mintick=mintick,incl_hist=incl_hist,incl_year=incl_year,
                     incl_map=incl_map,img_tile=img_tile,lbl_buff=lbl_buff,ext_buff=ext_buff)

        # Create a button widget to download the figure as PDF
        pdf_output = ipyw.Output()
        def download_pdf(button):
           pdf_filename = 'figure.pdf'
           pdf_opts(fig=fig,pdf_output=pdf_output,pdf_filename=pdf_filename)
        pdf_but = ipyw.Button(description='Download Figure', layout={'width': '140px'})
        pdf_but.on_click(download_pdf)

        # Create a button widget to download data as Excel
        xcl_output = ipyw.Output()
        def download_xcl(button):
            with xcl_output: print('Download initiated. Can take more than a minute if over 100 stations '+
                                   'are queried. Do not click download button again.')
            xcl_filename = 'data.xlsx'
            with pd.ExcelWriter(xcl_filename) as w:
                var.assign(**{var.columns[0]: var.iloc[:,0].astype(str)}
                           ).to_excel(w,sheet_name='stations',index=False)
                meta.to_excel(w,sheet_name='metadata',index=False)
                if incl_hist == True:
                    if snow_type == 'all' or snow_type == 'snow':
                        pd.concat([pd.DataFrame({'month':var_dy['month'],'day':var_dy['day'],'max':var_max,
                                                 '95th':var_95,'mean':var_avg}),var_dy.iloc[:,2:]],axis=1
                                  ).to_excel(w,sheet_name='historical',index=False)
                    if snow_type == 'wetNday':
                        sup = 'st' if nday == 1 else ('nd' if nday == 2 else ('rd' if nday == 3 else 'th'))
                        pd.concat([pd.DataFrame({'month':var_dy['month'],'day':var_dy['day'],
                                                 'Wettest Day':var_max,str(nday)+f'{sup} Wettest Day':var_min}),
                                   var_dy.iloc[:,2:]],axis=1).to_excel(w,sheet_name='historical',index=False)
                if incl_year == True:
                    pd.DataFrame({'month':var_dy['month'],'day':var_dy['day'],str(iyr):var_dy[str(iyr)]}
                                ).to_excel(w,sheet_name=str(iyr),index=False)
            xcl_opts(xcl_filename=xcl_filename,xcl_output=xcl_output)
        xcl_but = ipyw.Button(description='Download Data',layout=ipyw.Layout(width='140px'))
        xcl_but.on_click(download_xcl)

        # Display download buttons together
        button_box = ipyw.VBox([ipyw.HBox([pdf_but,xcl_but],layout=ipyw.Layout(justify_content='center'))])
        display(button_box,pdf_output,xcl_output)

    # Interactive output with only interactive components in dictionary
    out = ipyw.interactive_output(plot_fig,{'snow_type':snow_type,'nday':nday,'syr':syr,'eyr':eyr,
                                            'num_stn':num_stn,'iyr':iyr,'minbuff':minbuff,
                                            'maxbuff':maxbuff,'majtick':majtick,'mintick':mintick,
                                            'incl_hist':incl_hist,'incl_year':incl_year,
                                            'incl_map':incl_map,'img_tile':img_tile,
                                            'lbl_buff':lbl_buff,'ext_buff':ext_buff})
    display(ui,out)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
# CUMULATIVE WIDGETS
#
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#======================================================================================================
# cumulative_rain_widget
#======================================================================================================

def cumulative_pcpn_widget(var,meta,location_name,nlat,slat,wlon,elon):

    #----------------------------------------------------------------------------------------------
    # Set up parameters to toggle
    #----------------------------------------------------------------------------------------------

    # Define years for historical range
    txt_hist = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_cumulative} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Define years for historical range</a></h3>')
    text_hist = ipyw.Label(value='Include historical climate?',layout=ipyw.Layout(width='160px'))
    incl_hist = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='60px'))
    text_syr = ipyw.Label(value='Starting Year',layout=ipyw.Layout(width='120px'))
    text_eyr = ipyw.Label(value='Ending Year',layout=ipyw.Layout(width='120px'))
    syr = ipyw.Dropdown(options=['earliest',*np.sort(var['Date'].dt.year.unique())[:-1]],
                        value='earliest',layout=ipyw.Layout(width='100px'))
    eyr = ipyw.Dropdown(options=['latest',*np.sort(var['Date'].dt.year.unique())[::-1][1:]],
                        value='latest',layout=ipyw.Layout(width='100px'))
    text_stats = ipyw.Label(value='Display statistics',layout=ipyw.Layout(width='120px'))
    stats = ipyw.Dropdown(options=['Mean','Median'],value='Mean',layout=ipyw.Layout(width='100px'))

    # Plot individual year
    txt_indv = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_cumulative} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Plot individual year</a></h3>')
    text_year = ipyw.Label(value='Include individual year?',layout=ipyw.Layout(width='160px'))
    incl_year = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='70px'))
    text_iyr = ipyw.Label(value='Year Displayed',layout=ipyw.Layout(width='90px'))
    iyr = ipyw.Dropdown(options=var['Date'].dt.year.unique()[::-1],
                        value=var['Date'].dt.year.unique()[-1],layout=ipyw.Layout(width='70px'))
    text_mltyr = ipyw.Label(value='Add Years',layout=ipyw.Layout(width='65px'))
    mltyr = ipyw.Text(placeholder='e.g., 2022,2021 (max 9)',layout=ipyw.Layout(width='165px'),
                      value='',continuous_update=False)
    
    # Missing data allowed?
    txt_miss = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_cumulative} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Missing data allowed</a></h3>')
    text_md  = ipyw.Label(value='missing days per year',layout=ipyw.Layout(width='135px'))
    na_allwd = ipyw.Dropdown(options=list(np.arange(1,367)),value=100,
                             layout=ipyw.Layout(width='80px'))

    # Y-axis buffer
    txt_buff  = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis buffer</a></h3>')
    maxb_desc = ipyw.Label(value='Buffer above y-axis',layout=ipyw.Layout(width='120px'))
    maxbuff   = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    maxb_unit = ipyw.Label(value='in')
    minb_desc = ipyw.Label(value='Buffer below y-axis',layout=ipyw.Layout(width='120px'))
    minbuff   = ipyw.FloatText(value=0.,layout=ipyw.Layout(width='60px'))
    minb_unit = ipyw.Label(value='in')

    # Y-axis tick stride
    txt_tick   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis tick stride</a></h3>')
    majtk_desc = ipyw.Label(value='Major tick stride',layout=ipyw.Layout(width='120px'))
    majtick    = ipyw.FloatText(value=10.,layout=ipyw.Layout(width='60px'))
    majtk_unit = ipyw.Label(value='in')
    mintk_desc = ipyw.Label(value='Minor tick stride',layout=ipyw.Layout(width='120px'))
    mintick    = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    mintk_unit = ipyw.Label(value='in')

    # Map
    txt_map   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_map} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Map of stations</a></h3>')
    text_map  = ipyw.Label(value='Include map?',layout=ipyw.Layout(width='100px'))
    incl_map  = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='80px'))
    text_lyr  = ipyw.Label(value='Image tile',layout=ipyw.Layout(width='100px'))
    img_tile  = ipyw.Dropdown(options=['QuadtreeTiles','GoogleTiles','OpenStreetMap','grey'],
                              value='QuadtreeTiles',layout=ipyw.Layout(width='80px'))
    text_lbl = ipyw.Label(value='Label distance',layout=ipyw.Layout(width='100px'))
    lbl_buff = ipyw.Dropdown(options=[('10%',0.1),('20%',0.2),('30%',0.3),('40%',0.4),('50%',0.5),
                                       ('60%',0.6),('70%',0.7),('80%',0.8),('90%',0.9),('None',1.5)],
                              value=0.3,layout=ipyw.Layout(width='80px'))
    text_ext = ipyw.Label(value='Lat/lon buffer',layout=ipyw.Layout(width='100px'))
    ext_buff = ipyw.Dropdown(options=[('0.1°',0.1),('0.25°',0.25),('0.5°',0.5),('1°',1.),('5°',5.)],
                              value=0.5,layout=ipyw.Layout(width='80px'))
    
    #----------------------------------------------------------------------------------------------
    # Layout for dropdowns
    #----------------------------------------------------------------------------------------------

    ui = ipyw.VBox([
                    # FIRST ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Define years for historical range
                                 ipyw.HBox([txt_hist],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_hist,incl_hist],layout=ipyw.Layout(
                                                                        justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_syr,syr]),
                                                       ipyw.HBox([text_eyr,eyr])])],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_stats,stats],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Plot individual year
                                 ipyw.HBox([txt_indv],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_year,incl_year],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_iyr,iyr],
                                           layout=ipyw.Layout(justify_content='space-between')),
                                 ipyw.HBox([text_mltyr,mltyr])]),
                               ipyw.VBox([
                                 # Map 
                                 ipyw.HBox([txt_map],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_map,incl_map]),
                                                       ipyw.HBox([text_lyr,img_tile]),
                                                       ipyw.HBox([text_lbl,lbl_buff]),
                                                       ipyw.HBox([text_ext,ext_buff])])])])],
                               layout=ipyw.Layout(justify_content='space-around')),
                    # SECOND ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Missing data allowed per year
                                 ipyw.HBox([txt_miss],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([na_allwd,text_md],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Y-axis buffer
                                 ipyw.HBox([txt_buff],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([maxb_desc,maxbuff,maxb_unit]),
                                                       ipyw.HBox([minb_desc,minbuff,minb_unit])])],
                                           layout=ipyw.Layout(flex='1 1 auto',
                                                              justify_content='center'))]),
                               ipyw.VBox([
                                 # Y-axis tick stride
                                 ipyw.HBox([txt_tick],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([majtk_desc,majtick,majtk_unit]),
                                                       ipyw.HBox([mintk_desc,mintick,mintk_unit])])],
                                            layout=ipyw.Layout(flex='1 1 auto',
                                                               justify_content='space-between'))])],
                               layout=ipyw.Layout(justify_content='space-around'))
                     ])

    #----------------------------------------------------------------------------------------------
    # Display interactive plot
    #----------------------------------------------------------------------------------------------

    # Define function with only interactive components that runs widget.plot function
    def plot_fig(syr,eyr,stats,na_allwd,iyr,mltyr,minbuff,maxbuff,majtick,mintick,incl_hist,incl_year,
                 incl_map,img_tile,lbl_buff,ext_buff):

        fig,var_cs = plots.cumulative_pcpn_plot(
                     var=var,meta=meta,na_allwd=na_allwd,location_name=location_name,
                     nlat=float(nlat),slat=float(slat),wlon=float(wlon),elon=float(elon),
                     syr=syr,eyr=eyr,stats=stats,iyr=iyr,mltyr=mltyr,minbuff=minbuff,maxbuff=maxbuff,
                     majtick=majtick,mintick=mintick,incl_hist=incl_hist,incl_year=incl_year,
                     incl_map=incl_map,img_tile=img_tile,lbl_buff=lbl_buff,ext_buff=ext_buff)

        # Create a button widget to download the figure as PDF
        pdf_output = ipyw.Output()
        def download_pdf(button):
           pdf_filename = 'figure.pdf'
           pdf_opts(fig=fig,pdf_output=pdf_output,pdf_filename=pdf_filename)
        pdf_but = ipyw.Button(description='Download Figure', layout={'width': '140px'})
        pdf_but.on_click(download_pdf)

        # Create a button widget to download data as Excel
        xcl_output = ipyw.Output()
        def download_xcl(button):
            with xcl_output: print('Download initiated. Can take more than a minute if over 100 stations '+
                                   'are queried. Do not click download button again.')
            xcl_filename = 'data.xlsx'
            with pd.ExcelWriter(xcl_filename) as w:
                var.assign(**{var.columns[0]: var.iloc[:,0].astype(str)}
                           ).to_excel(w,sheet_name='stations',index=False)
                meta.to_excel(w,sheet_name='metadata',index=False)
                if incl_hist == True:
                    pd.concat([pd.DataFrame({'month':var_cs['month'],'day':var_cs['day']}),
                               var_cs.iloc[:,2:]],axis=1).to_excel(w,sheet_name='historical',index=False)
                if incl_year == True:
                    pd.DataFrame({'month':var_cs['month'],'day':var_cs['day'],str(iyr):var_cs[str(iyr)]}
                                ).to_excel(w,sheet_name=str(iyr),index=False)
            xcl_opts(xcl_filename=xcl_filename,xcl_output=xcl_output)
        xcl_but = ipyw.Button(description='Download Data',layout=ipyw.Layout(width='140px'))
        xcl_but.on_click(download_xcl)

        # Display download buttons together
        button_box = ipyw.VBox([ipyw.HBox([pdf_but,xcl_but],layout=ipyw.Layout(justify_content='center'))])
        display(button_box,pdf_output,xcl_output)

    # Interactive output with only interactive components in dictionary
    out = ipyw.interactive_output(plot_fig,{'syr':syr,'eyr':eyr,'stats':stats,'na_allwd':na_allwd,
                                            'iyr':iyr,'mltyr':mltyr,'minbuff':minbuff,'maxbuff':maxbuff,
                                            'majtick':majtick,'mintick':mintick,
                                            'incl_hist':incl_hist,'incl_year':incl_year,
                                            'incl_map':incl_map,'img_tile':img_tile,
                                            'lbl_buff':lbl_buff,'ext_buff':ext_buff})
    display(ui,out)

#======================================================================================================
# cumulative_snow_widget
#======================================================================================================

def cumulative_snow_widget(var,meta,location_name,nlat,slat,wlon,elon):

    #----------------------------------------------------------------------------------------------
    # Set up parameters to toggle
    #----------------------------------------------------------------------------------------------

    # Define years for historical range
    txt_hist = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_cumulative} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Define years for historical range</a></h3>')
    text_hist = ipyw.Label(value='Include historical climate?',layout=ipyw.Layout(width='160px'))
    incl_hist = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='60px'))
    text_syr = ipyw.Label(value='Starting Year',layout=ipyw.Layout(width='120px'))
    text_eyr = ipyw.Label(value='Ending Year',layout=ipyw.Layout(width='120px'))
    syr = ipyw.Dropdown(options=['earliest',*np.sort(var['Date'].dt.year.unique())[:-1]],
                        value='earliest',layout=ipyw.Layout(width='100px'))
    eyr = ipyw.Dropdown(options=['latest',*np.sort(var['Date'].dt.year.unique())[::-1][1:]],
                        value='latest',layout=ipyw.Layout(width='100px'))
    text_stats = ipyw.Label(value='Display statistics',layout=ipyw.Layout(width='120px'))
    stats = ipyw.Dropdown(options=['Mean','Median'],value='Mean',layout=ipyw.Layout(width='100px'))

    # Plot individual year
    txt_indv = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_cumulative} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Plot individual year</a></h3>')
    text_year = ipyw.Label(value='Include individual year?',layout=ipyw.Layout(width='160px'))
    incl_year = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='70px'))
    text_iyr = ipyw.Label(value='Year Displayed',layout=ipyw.Layout(width='90px'))
    iyr = ipyw.Dropdown(options=var['Date'].dt.year.unique()[::-1],
                        value=var['Date'].dt.year.unique()[-1],layout=ipyw.Layout(width='70px'))
    text_mltyr = ipyw.Label(value='Add Years',layout=ipyw.Layout(width='65px'))
    mltyr = ipyw.Text(placeholder='e.g., 2022,2021 (max 9)',layout=ipyw.Layout(width='165px'),
                      value='',continuous_update=False)

    # Missing data allowed?
    txt_miss = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_cumulative} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Missing data allowed</a></h3>')
    text_md  = ipyw.Label(value='missing days per year',layout=ipyw.Layout(width='135px'))
    na_allwd = ipyw.Dropdown(options=list(np.arange(1,367)),value=100,
                             layout=ipyw.Layout(width='80px'))

    # Y-axis buffer
    txt_buff  = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis buffer</a></h3>')
    maxb_desc = ipyw.Label(value='Buffer above y-axis',layout=ipyw.Layout(width='120px'))
    maxbuff   = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    maxb_unit = ipyw.Label(value='in')
    minb_desc = ipyw.Label(value='Buffer below y-axis',layout=ipyw.Layout(width='120px'))
    minbuff   = ipyw.FloatText(value=0.,layout=ipyw.Layout(width='60px'))
    minb_unit = ipyw.Label(value='in')

    # Y-axis tick stride
    txt_tick   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis tick stride</a></h3>')
    majtk_desc = ipyw.Label(value='Major tick stride',layout=ipyw.Layout(width='120px'))
    majtick    = ipyw.FloatText(value=10.,layout=ipyw.Layout(width='60px'))
    majtk_unit = ipyw.Label(value='in')
    mintk_desc = ipyw.Label(value='Minor tick stride',layout=ipyw.Layout(width='120px'))
    mintick    = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    mintk_unit = ipyw.Label(value='in')

    # Map
    txt_map   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_map} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Map of stations</a></h3>')
    text_map  = ipyw.Label(value='Include map?',layout=ipyw.Layout(width='100px'))
    incl_map  = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='80px'))
    text_lyr  = ipyw.Label(value='Image tile',layout=ipyw.Layout(width='100px'))
    img_tile  = ipyw.Dropdown(options=['QuadtreeTiles','GoogleTiles','OpenStreetMap','grey'],
                              value='QuadtreeTiles',layout=ipyw.Layout(width='80px'))
    text_lbl = ipyw.Label(value='Label distance',layout=ipyw.Layout(width='100px'))
    lbl_buff = ipyw.Dropdown(options=[('10%',0.1),('20%',0.2),('30%',0.3),('40%',0.4),('50%',0.5),
                                       ('60%',0.6),('70%',0.7),('80%',0.8),('90%',0.9),('None',1.5)],
                              value=0.3,layout=ipyw.Layout(width='80px'))
    text_ext = ipyw.Label(value='Lat/lon buffer',layout=ipyw.Layout(width='100px'))
    ext_buff = ipyw.Dropdown(options=[('0.1°',0.1),('0.25°',0.25),('0.5°',0.5),('1°',1.),('5°',5.)],
                              value=0.5,layout=ipyw.Layout(width='80px'))

    #----------------------------------------------------------------------------------------------
    # Layout for dropdowns
    #----------------------------------------------------------------------------------------------

    ui = ipyw.VBox([
                    # FIRST ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Define years for historical range
                                 ipyw.HBox([txt_hist],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_hist,incl_hist],layout=ipyw.Layout(
                                                                        justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_syr,syr]),
                                                       ipyw.HBox([text_eyr,eyr])])],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_stats,stats],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Plot individual year
                                 ipyw.HBox([txt_indv],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_year,incl_year],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_iyr,iyr],
                                           layout=ipyw.Layout(justify_content='space-between')),
                                 ipyw.HBox([text_mltyr,mltyr])]),
                               ipyw.VBox([
                                 # Map 
                                 ipyw.HBox([txt_map],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_map,incl_map]),
                                                       ipyw.HBox([text_lyr,img_tile]),
                                                       ipyw.HBox([text_lbl,lbl_buff]),
                                                       ipyw.HBox([text_ext,ext_buff])])])])],
                               layout=ipyw.Layout(justify_content='space-around')),
                    # SECOND ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Missing data allowed per year
                                 ipyw.HBox([txt_miss],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([na_allwd,text_md],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Y-axis buffer
                                 ipyw.HBox([txt_buff],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([maxb_desc,maxbuff,maxb_unit]),
                                                       ipyw.HBox([minb_desc,minbuff,minb_unit])])],
                                           layout=ipyw.Layout(flex='1 1 auto',
                                                              justify_content='center'))]),
                               ipyw.VBox([
                                 # Y-axis tick stride
                                 ipyw.HBox([txt_tick],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([majtk_desc,majtick,majtk_unit]),
                                                       ipyw.HBox([mintk_desc,mintick,mintk_unit])])],
                                            layout=ipyw.Layout(flex='1 1 auto',
                                                               justify_content='space-between'))])],
                               layout=ipyw.Layout(justify_content='space-around'))
                     ])

    #----------------------------------------------------------------------------------------------
    # Display interactive plot
    #----------------------------------------------------------------------------------------------

    # Define function with only interactive components that runs widget.plot function
    def plot_fig(syr,eyr,stats,na_allwd,iyr,mltyr,minbuff,maxbuff,majtick,mintick,incl_hist,
                 incl_year,incl_map,img_tile,lbl_buff,ext_buff):

        fig,var_cs = plots.cumulative_snow_plot(
                     var=var,meta=meta,na_allwd=na_allwd,location_name=location_name,
                     nlat=float(nlat),slat=float(slat),wlon=float(wlon),elon=float(elon),
                     syr=syr,eyr=eyr,stats=stats,iyr=iyr,mltyr=mltyr,minbuff=minbuff,maxbuff=maxbuff,
                     majtick=majtick,mintick=mintick,incl_hist=incl_hist,incl_year=incl_year,
                     incl_map=incl_map,img_tile=img_tile,lbl_buff=lbl_buff,ext_buff=ext_buff)

        # Create a button widget to download the figure as PDF
        pdf_output = ipyw.Output()
        def download_pdf(button):
           pdf_filename = 'figure.pdf'
           pdf_opts(fig=fig,pdf_output=pdf_output,pdf_filename=pdf_filename)
        pdf_but = ipyw.Button(description='Download Figure', layout={'width': '140px'})
        pdf_but.on_click(download_pdf)

        # Create a button widget to download data as Excel
        xcl_output = ipyw.Output()
        def download_xcl(button):
            with xcl_output: print('Download initiated. Can take more than a minute if over 100 stations '+
                                   'are queried. Do not click download button again.')
            xcl_filename = 'data.xlsx'
            with pd.ExcelWriter(xcl_filename) as w:
                var.assign(**{var.columns[0]: var.iloc[:,0].astype(str)}
                           ).to_excel(w,sheet_name='stations',index=False)
                meta.to_excel(w,sheet_name='metadata',index=False)
                if incl_hist == True:
                    pd.concat([pd.DataFrame({'month':var_cs['month'],'day':var_cs['day']}),
                               var_cs.iloc[:,2:]],axis=1).to_excel(w,sheet_name='historical',index=False)
                if incl_year == True:
                    pd.DataFrame({'month':var_cs['month'],'day':var_cs['day'],str(iyr):var_cs[str(iyr)]}
                                ).to_excel(w,sheet_name=str(iyr),index=False)
            xcl_opts(xcl_filename=xcl_filename,xcl_output=xcl_output)
        xcl_but = ipyw.Button(description='Download Data',layout=ipyw.Layout(width='140px'))
        xcl_but.on_click(download_xcl)

        # Display download buttons together
        button_box = ipyw.VBox([ipyw.HBox([pdf_but,xcl_but],layout=ipyw.Layout(justify_content='center'))])
        display(button_box,pdf_output,xcl_output)

    # Interactive output with only interactive components in dictionary
    out = ipyw.interactive_output(plot_fig,{'syr':syr,'eyr':eyr,'stats':stats,'na_allwd':na_allwd,
                                            'iyr':iyr,'mltyr':mltyr,'minbuff':minbuff,'maxbuff':maxbuff,
                                            'majtick':majtick,'mintick':mintick,
                                            'incl_hist':incl_hist,'incl_year':incl_year,
                                            'incl_map':incl_map,'img_tile':img_tile,
                                            'lbl_buff':lbl_buff,'ext_buff':ext_buff})
    display(ui,out)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
# TIME SERIES WIDGETS
#
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#======================================================================================================
# timeseries_tmax_widget
#======================================================================================================

def timeseries_tmax_widget(var,meta,location_name,nlat,slat,wlon,elon):

    #----------------------------------------------------------------------------------------------
    # Set up parameters to toggle
    #----------------------------------------------------------------------------------------------

    # Specify months to include
    txt_monthi = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_timeseries} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Months to include</a></h3>')
    text_mon1 = ipyw.Label(value='From',layout=ipyw.Layout(width='50px'))
    month1    = ipyw.Dropdown(options=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct',
                                       'Nov','Dec'],value='Jan',layout=ipyw.Layout(width='80px'))
    text_mon2 = ipyw.Label(value='To',layout=ipyw.Layout(width='50px'))
    month2    = ipyw.Dropdown(options=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct',
                                       'Nov','Dec'],value='Dec',layout=ipyw.Layout(width='80px'))

    # Method and plot features
    txt_meth = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_timeseries} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Choose what to plot</a></h3>')
    text_meth = ipyw.Label(value='Method to use',layout=ipyw.Layout(width='120px'))
    method = ipyw.Dropdown(options=[('Mean','avg'),('Max','max'),('Min','min')],value='avg',
                           layout=ipyw.Layout(width='80px'))
    text_tl = ipyw.Label(value='Include trendline?',layout=ipyw.Layout(width='120px'))
    incl_tl = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='80px'))
    text_yr = ipyw.Label(value='Trendline Years',layout=ipyw.Layout(width='100px'))
    tl_syr = ipyw.Dropdown(options=['Start',*np.sort(var['Date'].dt.year.unique())[:-1]],
                           value='Start',layout=ipyw.Layout(width='60px'))
    tl_eyr = ipyw.Dropdown(options=['End',*np.sort(var['Date'].dt.year.unique())[::-1][1:]],
                           value='End',layout=ipyw.Layout(width='60px'))

    # Data quality standards
    txt_dq = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_timeseries} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Data quality</a></h3>')
    text_ndays = ipyw.Label(value='Number of days',layout=ipyw.Layout(width='120px'))
    num_days = ipyw.Dropdown(options=np.arange(28),value=15,layout=ipyw.Layout(width='60px'))
    text_nmons = ipyw.Label(value='Number of months',layout=ipyw.Layout(width='120px'))
    num_mons = ipyw.Dropdown(options=np.arange(13),value=12,layout=ipyw.Layout(width='60px'))
    text_stns = ipyw.Label(value='Number of stations',layout=ipyw.Layout(width='120px'))
    if len(meta) == 1:
       num_stns = ipyw.Dropdown(options=[1],value=1,layout=ipyw.Layout(width='60px'))
    else:
       num_stns = ipyw.Dropdown(options=np.arange(1,len(meta)),value=1,
                                layout=ipyw.Layout(width='60px'))

    # Tick stride
    txt_tick = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis tick stride</a></h3>')
    ymajtk_desc = ipyw.Label(value='Major Y tick stride',layout=ipyw.Layout(width='120px'))
    ymajtick    = ipyw.FloatText(value=3.,layout=ipyw.Layout(width='60px'))
    ymajtk_unit = ipyw.Label(value='°F')
    ymintk_desc = ipyw.Label(value='Minor Y tick stride',layout=ipyw.Layout(width='120px'))
    ymintick    = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    ymintk_unit = ipyw.Label(value='°F')
    xmajtk_desc = ipyw.Label(value='Major X tick stride',layout=ipyw.Layout(width='120px'))
    xmajtick    = ipyw.IntText(value=20,layout=ipyw.Layout(width='60px'))
    xmajtk_unit = ipyw.Label(value='years')
    xmintk_desc = ipyw.Label(value='Minor X tick stride',layout=ipyw.Layout(width='120px'))
    xmintick    = ipyw.IntText(value=5,layout=ipyw.Layout(width='60px'))
    xmintk_unit = ipyw.Label(value='years')

    # Y-axis buffer
    txt_buff = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis buffer</a></h3>')
    maxb_desc = ipyw.Label(value='Buffer above y-axis',layout=ipyw.Layout(width='120px'))
    maxbuff   = ipyw.FloatText(value=5.,layout=ipyw.Layout(width='60px'))
    maxb_unit = ipyw.Label(value='°F')
    minb_desc = ipyw.Label(value='Buffer below y-axis',layout=ipyw.Layout(width='120px'))
    minbuff   = ipyw.FloatText(value=2.,layout=ipyw.Layout(width='60px'))
    minb_unit = ipyw.Label(value='°F')

    # Map
    txt_map   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_map} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Map of stations</a></h3>')
    text_map  = ipyw.Label(value='Include map?',layout=ipyw.Layout(width='100px'))
    incl_map  = ipyw.Dropdown(options=['True (left)','True (right)','False'],value='True (left)',
                              layout=ipyw.Layout(width='90px'))
    text_lyr  = ipyw.Label(value='Image tile',layout=ipyw.Layout(width='100px'))
    img_tile  = ipyw.Dropdown(options=['QuadtreeTiles','GoogleTiles','OpenStreetMap','grey'],
                              value='QuadtreeTiles',layout=ipyw.Layout(width='80px'))
    text_lbl = ipyw.Label(value='Label distance',layout=ipyw.Layout(width='100px'))
    lbl_buff = ipyw.Dropdown(options=[('10%',0.1),('20%',0.2),('30%',0.3),('40%',0.4),('50%',0.5),
                                       ('60%',0.6),('70%',0.7),('80%',0.8),('90%',0.9),('None',1.5)],
                              value=0.3,layout=ipyw.Layout(width='90px'))
    text_ext = ipyw.Label(value='Lat/lon buffer',layout=ipyw.Layout(width='100px'))
    ext_buff = ipyw.Dropdown(options=[('0.1°',0.1),('0.25°',0.25),('0.5°',0.5),('1°',1.),('5°',5.)],
                              value=0.5,layout=ipyw.Layout(width='90px'))

    #----------------------------------------------------------------------------------------------
    # Layout for dropdowns
    #----------------------------------------------------------------------------------------------

    ui = ipyw.VBox([
                    # FIRST ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Specify months to include
                                 ipyw.HBox([txt_monthi],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_mon1,month1]),
                                                       ipyw.HBox([text_mon2,month2])])],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Method
                                 ipyw.HBox([txt_meth],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_meth,method]),
                                 ipyw.HBox([text_tl,incl_tl]),
                                 ipyw.HBox([text_yr,tl_syr,tl_eyr])]),
                               ipyw.VBox([
                                 # Data quality standards
                                 ipyw.HBox([txt_dq],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_ndays,num_days]),
                                                       ipyw.HBox([text_nmons,num_mons]),
                                                       ipyw.HBox([text_stns,num_stns])])])])],
                               layout=ipyw.Layout(justify_content='space-around')),
                    # SECOND ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Tick stride
                                 ipyw.HBox([txt_tick],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([ymajtk_desc,ymajtick,ymajtk_unit]),
                                                       ipyw.HBox([ymintk_desc,ymintick,ymintk_unit]),
                                                       ipyw.HBox([xmajtk_desc,xmajtick,xmajtk_unit]),
                                                       ipyw.HBox([xmintk_desc,xmintick,xmintk_unit])])],
                                            layout=ipyw.Layout(flex='1 1 auto',
                                                               justify_content='space-between'))]),
                               ipyw.VBox([
                                 # Y-axis buffer
                                 ipyw.HBox([txt_buff],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([maxb_desc,maxbuff,maxb_unit]),
                                                       ipyw.HBox([minb_desc,minbuff,minb_unit])])],
                                           layout=ipyw.Layout(flex='1 1 auto',
                                                              justify_content='center'))]),
                               ipyw.VBox([
                                  # Map 
                                 ipyw.HBox([txt_map],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_map,incl_map]),
                                                       ipyw.HBox([text_lyr,img_tile]),
                                                       ipyw.HBox([text_lbl,lbl_buff]),
                                                       ipyw.HBox([text_ext,ext_buff])])])])],
                               layout=ipyw.Layout(justify_content='space-around'))
                     ])

    #----------------------------------------------------------------------------------------------
    # Display interactive plot
    #----------------------------------------------------------------------------------------------

    # Define function with only interactive components that runs widget.plot function
    def plot_fig(month1,month2,num_days,num_mons,num_stns,method,incl_tl,tl_syr,tl_eyr,minbuff,
                 maxbuff,ymajtick,ymintick,xmajtick,xmintick,incl_map,img_tile,lbl_buff,ext_buff):

        fig,var_my,ts = plots.timeseries_tmax_plot(
                        var=var,meta=meta,location_name=location_name,nlat=float(nlat),
                        slat=float(slat),wlon=float(wlon),elon=float(elon),month1=month1,
                        month2=month2,num_days=num_days,num_mons=num_mons,num_stns=num_stns,
                        method=method,incl_tl=incl_tl,tl_syr=tl_syr,tl_eyr=tl_eyr,minbuff=minbuff,
                        maxbuff=maxbuff,ymajtick=ymajtick,ymintick=ymintick,xmajtick=xmajtick,
                        xmintick=xmintick,incl_map=incl_map,img_tile=img_tile,lbl_buff=lbl_buff,
                        ext_buff=ext_buff)

        # Create a button widget to download the figure as PDF
        pdf_output = ipyw.Output()
        def download_pdf(button):
           pdf_filename = 'figure.pdf'
           pdf_opts(fig=fig,pdf_output=pdf_output,pdf_filename=pdf_filename)
        pdf_but = ipyw.Button(description='Download Figure', layout={'width': '140px'})
        pdf_but.on_click(download_pdf)

        # Create a button widget to download data as Excel
        xcl_output = ipyw.Output()
        def download_xcl(button):
            with xcl_output: print('Download initiated. Can take more than a minute if over 100 stations '+
                                   'are queried. Do not click download button again.')
            xcl_filename = 'data.xlsx'
            with pd.ExcelWriter(xcl_filename) as w:
                var.assign(**{var.columns[0]: var.iloc[:,0].astype(str)}
                           ).to_excel(w,sheet_name='stations',index=False)
                meta.to_excel(w,sheet_name='metadata',index=False)
                var_my.to_excel(w,sheet_name='preprocessing',index=False)
                ts.rename(columns={'Value':method}).to_excel(w,sheet_name='timeseries',index=False)
            xcl_opts(xcl_filename=xcl_filename,xcl_output=xcl_output)
        xcl_but = ipyw.Button(description='Download Data',layout=ipyw.Layout(width='140px'))
        xcl_but.on_click(download_xcl)

        # Display download buttons together
        button_box = ipyw.VBox([ipyw.HBox([pdf_but,xcl_but],layout=ipyw.Layout(justify_content='center'))])
        display(button_box,pdf_output,xcl_output)

    # Interactive output with only interactive components in dictionary
    out = ipyw.interactive_output(plot_fig,{'month1':month1,'month2':month2,'num_days':num_days,
                                            'num_mons':num_mons,'num_stns':num_stns,'method':method,
                                            'incl_tl':incl_tl,'tl_syr':tl_syr,'tl_eyr':tl_eyr,
                                            'minbuff':minbuff,'maxbuff':maxbuff,'ymajtick':ymajtick,
                                            'ymintick':ymintick,'xmajtick':xmajtick,'xmintick':xmintick,
                                            'incl_map':incl_map,'img_tile':img_tile,'lbl_buff':lbl_buff,
                                            'ext_buff':ext_buff})
    display(ui,out)

#======================================================================================================
# timeseries_tmin_widget
#======================================================================================================

def timeseries_tmin_widget(var,meta,location_name,nlat,slat,wlon,elon):

    #----------------------------------------------------------------------------------------------
    # Set up parameters to toggle
    #----------------------------------------------------------------------------------------------

    # Specify months to include
    txt_monthi = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_timeseries} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Months to include</a></h3>')
    text_mon1 = ipyw.Label(value='From',layout=ipyw.Layout(width='50px'))
    month1    = ipyw.Dropdown(options=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct',
                                       'Nov','Dec'],value='Jan',layout=ipyw.Layout(width='80px'))
    text_mon2 = ipyw.Label(value='To',layout=ipyw.Layout(width='50px'))
    month2    = ipyw.Dropdown(options=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct',
                                       'Nov','Dec'],value='Dec',layout=ipyw.Layout(width='80px'))

    # Method and plot features
    txt_meth = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_timeseries} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Choose what to plot</a></h3>')
    text_meth = ipyw.Label(value='Method to use',layout=ipyw.Layout(width='120px'))
    method = ipyw.Dropdown(options=[('Mean','avg'),('Max','max'),('Min','min')],value='avg',
                           layout=ipyw.Layout(width='80px'))
    text_tl = ipyw.Label(value='Include trendline?',layout=ipyw.Layout(width='120px'))
    incl_tl = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='80px'))
    text_yr = ipyw.Label(value='Trendline Years',layout=ipyw.Layout(width='100px'))
    tl_syr = ipyw.Dropdown(options=['Start',*np.sort(var['Date'].dt.year.unique())[:-1]],
                           value='Start',layout=ipyw.Layout(width='60px'))
    tl_eyr = ipyw.Dropdown(options=['End',*np.sort(var['Date'].dt.year.unique())[::-1][1:]],
                           value='End',layout=ipyw.Layout(width='60px'))

    # Data quality standards
    txt_dq = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_timeseries} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Data quality</a></h3>')
    text_ndays = ipyw.Label(value='Number of days',layout=ipyw.Layout(width='120px'))
    num_days = ipyw.Dropdown(options=np.arange(28),value=15,layout=ipyw.Layout(width='60px'))
    text_nmons = ipyw.Label(value='Number of months',layout=ipyw.Layout(width='120px'))
    num_mons = ipyw.Dropdown(options=np.arange(13),value=12,layout=ipyw.Layout(width='60px'))
    text_stns = ipyw.Label(value='Number of stations',layout=ipyw.Layout(width='120px'))
    if len(meta) == 1:
       num_stns = ipyw.Dropdown(options=[1],value=1,layout=ipyw.Layout(width='60px'))
    else:
       num_stns = ipyw.Dropdown(options=np.arange(1,len(meta)),value=1,
                                layout=ipyw.Layout(width='60px'))

    # Tick stride
    txt_tick = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis tick stride</a></h3>')
    ymajtk_desc = ipyw.Label(value='Major Y tick stride',layout=ipyw.Layout(width='120px'))
    ymajtick    = ipyw.FloatText(value=3.,layout=ipyw.Layout(width='60px'))
    ymajtk_unit = ipyw.Label(value='°F')
    ymintk_desc = ipyw.Label(value='Minor Y tick stride',layout=ipyw.Layout(width='120px'))
    ymintick    = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    ymintk_unit = ipyw.Label(value='°F')
    xmajtk_desc = ipyw.Label(value='Major X tick stride',layout=ipyw.Layout(width='120px'))
    xmajtick    = ipyw.IntText(value=20,layout=ipyw.Layout(width='60px'))
    xmajtk_unit = ipyw.Label(value='years')
    xmintk_desc = ipyw.Label(value='Minor X tick stride',layout=ipyw.Layout(width='120px'))
    xmintick    = ipyw.IntText(value=5,layout=ipyw.Layout(width='60px'))
    xmintk_unit = ipyw.Label(value='years')

    # Y-axis buffer
    txt_buff = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis buffer</a></h3>')
    maxb_desc = ipyw.Label(value='Buffer above y-axis',layout=ipyw.Layout(width='120px'))
    maxbuff   = ipyw.FloatText(value=5.,layout=ipyw.Layout(width='60px'))
    maxb_unit = ipyw.Label(value='°F')
    minb_desc = ipyw.Label(value='Buffer below y-axis',layout=ipyw.Layout(width='120px'))
    minbuff   = ipyw.FloatText(value=2.,layout=ipyw.Layout(width='60px'))
    minb_unit = ipyw.Label(value='°F')

    # Map
    txt_map   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_map} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Map of stations</a></h3>')
    text_map  = ipyw.Label(value='Include map?',layout=ipyw.Layout(width='100px'))
    incl_map  = ipyw.Dropdown(options=['True (left)','True (right)','False'],value='True (left)',
                              layout=ipyw.Layout(width='90px'))
    text_lyr  = ipyw.Label(value='Image tile',layout=ipyw.Layout(width='100px'))
    img_tile  = ipyw.Dropdown(options=['QuadtreeTiles','GoogleTiles','OpenStreetMap','grey'],
                              value='QuadtreeTiles',layout=ipyw.Layout(width='80px'))
    text_lbl = ipyw.Label(value='Label distance',layout=ipyw.Layout(width='100px'))
    lbl_buff = ipyw.Dropdown(options=[('10%',0.1),('20%',0.2),('30%',0.3),('40%',0.4),('50%',0.5),
                                       ('60%',0.6),('70%',0.7),('80%',0.8),('90%',0.9),('None',1.5)],
                              value=0.3,layout=ipyw.Layout(width='90px'))
    text_ext = ipyw.Label(value='Lat/lon buffer',layout=ipyw.Layout(width='100px'))
    ext_buff = ipyw.Dropdown(options=[('0.1°',0.1),('0.25°',0.25),('0.5°',0.5),('1°',1.),('5°',5.)],
                              value=0.5,layout=ipyw.Layout(width='90px'))

    #----------------------------------------------------------------------------------------------
    # Layout for dropdowns
    #----------------------------------------------------------------------------------------------

    ui = ipyw.VBox([
                    # FIRST ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Specify months to include
                                 ipyw.HBox([txt_monthi],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_mon1,month1]),
                                                       ipyw.HBox([text_mon2,month2])])],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Method
                                 ipyw.HBox([txt_meth],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_meth,method]),
                                 ipyw.HBox([text_tl,incl_tl]),
                                 ipyw.HBox([text_yr,tl_syr,tl_eyr])]),
                               ipyw.VBox([
                                 # Data quality standards
                                 ipyw.HBox([txt_dq],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_ndays,num_days]),
                                                       ipyw.HBox([text_nmons,num_mons]),
                                                       ipyw.HBox([text_stns,num_stns])])])])],
                               layout=ipyw.Layout(justify_content='space-around')),
                    # SECOND ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Tick stride
                                 ipyw.HBox([txt_tick],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([ymajtk_desc,ymajtick,ymajtk_unit]),
                                                       ipyw.HBox([ymintk_desc,ymintick,ymintk_unit]),
                                                       ipyw.HBox([xmajtk_desc,xmajtick,xmajtk_unit]),
                                                       ipyw.HBox([xmintk_desc,xmintick,xmintk_unit])])],
                                            layout=ipyw.Layout(flex='1 1 auto',
                                                               justify_content='space-between'))]),
                               ipyw.VBox([
                                 # Y-axis buffer
                                 ipyw.HBox([txt_buff],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([maxb_desc,maxbuff,maxb_unit]),
                                                       ipyw.HBox([minb_desc,minbuff,minb_unit])])],
                                           layout=ipyw.Layout(flex='1 1 auto',
                                                              justify_content='center'))]),
                               ipyw.VBox([
                                  # Map 
                                 ipyw.HBox([txt_map],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_map,incl_map]),
                                                       ipyw.HBox([text_lyr,img_tile]),
                                                       ipyw.HBox([text_lbl,lbl_buff]),
                                                       ipyw.HBox([text_ext,ext_buff])])])])],
                               layout=ipyw.Layout(justify_content='space-around'))
                     ])

    #----------------------------------------------------------------------------------------------
    # Display interactive plot
    #----------------------------------------------------------------------------------------------

    # Define function with only interactive components that runs widget.plot function
    def plot_fig(month1,month2,num_days,num_mons,num_stns,method,incl_tl,tl_syr,tl_eyr,minbuff,
                 maxbuff,ymajtick,ymintick,xmajtick,xmintick,incl_map,img_tile,lbl_buff,ext_buff):

        fig,var_my,ts = plots.timeseries_tmin_plot(
                        var=var,meta=meta,location_name=location_name,nlat=float(nlat),
                        slat=float(slat),wlon=float(wlon),elon=float(elon),month1=month1,
                        month2=month2,num_days=num_days,num_mons=num_mons,num_stns=num_stns,
                        method=method,incl_tl=incl_tl,tl_syr=tl_syr,tl_eyr=tl_eyr,minbuff=minbuff,
                        maxbuff=maxbuff,ymajtick=ymajtick,ymintick=ymintick,xmajtick=xmajtick,
                        xmintick=xmintick,incl_map=incl_map,img_tile=img_tile,lbl_buff=lbl_buff,
                        ext_buff=ext_buff)

        # Create a button widget to download the figure as PDF
        pdf_output = ipyw.Output()
        def download_pdf(button):
           pdf_filename = 'figure.pdf'
           pdf_opts(fig=fig,pdf_output=pdf_output,pdf_filename=pdf_filename)
        pdf_but = ipyw.Button(description='Download Figure', layout={'width': '140px'})
        pdf_but.on_click(download_pdf)

        # Create a button widget to download data as Excel
        xcl_output = ipyw.Output()
        def download_xcl(button):
            with xcl_output: print('Download initiated. Can take more than a minute if over 100 stations '+
                                   'are queried. Do not click download button again.')
            xcl_filename = 'data.xlsx'
            with pd.ExcelWriter(xcl_filename) as w:
                var.assign(**{var.columns[0]: var.iloc[:,0].astype(str)}
                           ).to_excel(w,sheet_name='stations',index=False)
                meta.to_excel(w,sheet_name='metadata',index=False)
                var_my.to_excel(w,sheet_name='preprocessing',index=False)
                ts.rename(columns={'Value':method}).to_excel(w,sheet_name='timeseries',index=False)
            xcl_opts(xcl_filename=xcl_filename,xcl_output=xcl_output)
        xcl_but = ipyw.Button(description='Download Data',layout=ipyw.Layout(width='140px'))
        xcl_but.on_click(download_xcl)

        # Display download buttons together
        button_box = ipyw.VBox([ipyw.HBox([pdf_but,xcl_but],layout=ipyw.Layout(justify_content='center'))])
        display(button_box,pdf_output,xcl_output)

    # Interactive output with only interactive components in dictionary
    out = ipyw.interactive_output(plot_fig,{'month1':month1,'month2':month2,'num_days':num_days,
                                            'num_mons':num_mons,'num_stns':num_stns,'method':method,
                                            'incl_tl':incl_tl,'tl_syr':tl_syr,'tl_eyr':tl_eyr,
                                            'minbuff':minbuff,'maxbuff':maxbuff,'ymajtick':ymajtick,
                                            'ymintick':ymintick,'xmajtick':xmajtick,'xmintick':xmintick,
                                            'incl_map':incl_map,'img_tile':img_tile,'lbl_buff':lbl_buff,
                                            'ext_buff':ext_buff})
    display(ui,out)

#======================================================================================================
# timeseries_pcpn_widget
#======================================================================================================

def timeseries_pcpn_widget(var,meta,location_name,nlat,slat,wlon,elon):

    #----------------------------------------------------------------------------------------------
    # Set up parameters to toggle
    #----------------------------------------------------------------------------------------------

    # Specify months to include
    txt_monthi = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_timeseries} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Months to include</a></h3>')
    text_mon1 = ipyw.Label(value='From',layout=ipyw.Layout(width='50px'))
    month1    = ipyw.Dropdown(options=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct',
                                       'Nov','Dec'],value='Jan',layout=ipyw.Layout(width='80px'))
    text_mon2 = ipyw.Label(value='To',layout=ipyw.Layout(width='50px'))
    month2    = ipyw.Dropdown(options=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct',
                                       'Nov','Dec'],value='Dec',layout=ipyw.Layout(width='80px'))

    # Method and plot features
    txt_meth = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_timeseries} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Choose what to plot</a></h3>')
    text_meth = ipyw.Label(value='Method to use',layout=ipyw.Layout(width='100px'))
    method = ipyw.Dropdown(options=[('Max Rx1day','rx1day-max'), 
                                   #('Mean Rx1day','rx1day-mean'), # removing this option for now
                                    ('Mean of all days','alldays-mean'),
                                    ('Mean of rain days','raindays-mean')],value='rx1day-max',
                           layout=ipyw.Layout(width='125px'))
    text_tl = ipyw.Label(value='Include trendline?',layout=ipyw.Layout(width='120px'))
    incl_tl = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='80px'))
    text_yr = ipyw.Label(value='Trendline Years',layout=ipyw.Layout(width='100px'))
    tl_syr = ipyw.Dropdown(options=['Start',*np.sort(var['Date'].dt.year.unique())[:-1]],
                           value='Start',layout=ipyw.Layout(width='60px'))
    tl_eyr = ipyw.Dropdown(options=['End',*np.sort(var['Date'].dt.year.unique())[::-1][1:]],
                           value='End',layout=ipyw.Layout(width='60px'))

    # Data quality standards
    txt_dq = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_timeseries} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Data quality</a></h3>')
    text_ndays = ipyw.Label(value='Number of days',layout=ipyw.Layout(width='120px'))
    num_days = ipyw.Dropdown(options=np.arange(28),value=15,layout=ipyw.Layout(width='60px'))
    text_nmons = ipyw.Label(value='Number of months',layout=ipyw.Layout(width='120px'))
    num_mons = ipyw.Dropdown(options=np.arange(13),value=12,layout=ipyw.Layout(width='60px'))
    text_stns = ipyw.Label(value='Number of stations',layout=ipyw.Layout(width='120px'))
    if len(meta) == 1:
       num_stns = ipyw.Dropdown(options=[1],value=1,layout=ipyw.Layout(width='60px'))
    else:
       num_stns = ipyw.Dropdown(options=np.arange(1,len(meta)),value=1,
                                layout=ipyw.Layout(width='60px'))

    # Tick stride
    txt_tick = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis tick stride</a></h3>')
    ymajtk_desc = ipyw.Label(value='Major Y tick stride',layout=ipyw.Layout(width='120px'))
    ymajtick    = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    
    ymajtk_unit = ipyw.Label(value='inches')
    ymintk_desc = ipyw.Label(value='Minor Y tick stride',layout=ipyw.Layout(width='120px'))
    ymintick    = ipyw.FloatText(value=0.5,layout=ipyw.Layout(width='60px'))
    ymintk_unit = ipyw.Label(value='inches')
    xmajtk_desc = ipyw.Label(value='Major X tick stride',layout=ipyw.Layout(width='120px'))
    xmajtick    = ipyw.IntText(value=20,layout=ipyw.Layout(width='60px'))
    xmajtk_unit = ipyw.Label(value='years')
    xmintk_desc = ipyw.Label(value='Minor X tick stride',layout=ipyw.Layout(width='120px'))
    xmintick    = ipyw.IntText(value=5,layout=ipyw.Layout(width='60px'))
    xmintk_unit = ipyw.Label(value='years')

    # Y-axis buffer
    txt_buff = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis buffer</a></h3>')
    maxb_desc = ipyw.Label(value='Buffer above y-axis',layout=ipyw.Layout(width='120px'))
    maxbuff   = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    maxb_unit = ipyw.Label(value='inches')
    minb_desc = ipyw.Label(value='Buffer below y-axis',layout=ipyw.Layout(width='120px'))
    minbuff   = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    minb_unit = ipyw.Label(value='inches')

    # Map
    txt_map   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_map} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Map of stations</a></h3>')
    text_map  = ipyw.Label(value='Include map?',layout=ipyw.Layout(width='100px'))
    incl_map  = ipyw.Dropdown(options=['True (left)','True (right)','False'],value='True (left)',
                              layout=ipyw.Layout(width='90px'))
    text_lyr  = ipyw.Label(value='Image tile',layout=ipyw.Layout(width='100px'))
    img_tile  = ipyw.Dropdown(options=['QuadtreeTiles','GoogleTiles','OpenStreetMap','grey'],
                              value='QuadtreeTiles',layout=ipyw.Layout(width='80px'))
    text_lbl = ipyw.Label(value='Label distance',layout=ipyw.Layout(width='100px'))
    lbl_buff = ipyw.Dropdown(options=[('10%',0.1),('20%',0.2),('30%',0.3),('40%',0.4),('50%',0.5),
                                       ('60%',0.6),('70%',0.7),('80%',0.8),('90%',0.9),('None',1.5)],
                              value=0.3,layout=ipyw.Layout(width='90px'))
    text_ext = ipyw.Label(value='Lat/lon buffer',layout=ipyw.Layout(width='100px'))
    ext_buff = ipyw.Dropdown(options=[('0.1°',0.1),('0.25°',0.25),('0.5°',0.5),('1°',1.),('5°',5.)],
                              value=0.5,layout=ipyw.Layout(width='90px'))

    #----------------------------------------------------------------------------------------------
    # Layout for dropdowns
    #----------------------------------------------------------------------------------------------

    ui = ipyw.VBox([
                    # FIRST ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Specify months to include
                                 ipyw.HBox([txt_monthi],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_mon1,month1]),
                                                       ipyw.HBox([text_mon2,month2])])],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Method
                                 ipyw.HBox([txt_meth],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_meth,method]),
                                 ipyw.HBox([text_tl,incl_tl]),
                                 ipyw.HBox([text_yr,tl_syr,tl_eyr])]),
                               ipyw.VBox([
                                 # Data quality standards
                                 ipyw.HBox([txt_dq],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_ndays,num_days]),
                                                       ipyw.HBox([text_nmons,num_mons]),
                                                       ipyw.HBox([text_stns,num_stns])])])])],
                               layout=ipyw.Layout(justify_content='space-around')),
                    # SECOND ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Tick stride
                                 ipyw.HBox([txt_tick],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([ymajtk_desc,ymajtick,ymajtk_unit]),
                                                       ipyw.HBox([ymintk_desc,ymintick,ymintk_unit]),
                                                       ipyw.HBox([xmajtk_desc,xmajtick,xmajtk_unit]),
                                                       ipyw.HBox([xmintk_desc,xmintick,xmintk_unit])])],
                                            layout=ipyw.Layout(flex='1 1 auto',
                                                               justify_content='space-between'))]),
                               ipyw.VBox([
                                 # Y-axis buffer
                                 ipyw.HBox([txt_buff],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([maxb_desc,maxbuff,maxb_unit]),
                                                       ipyw.HBox([minb_desc,minbuff,minb_unit])])],
                                           layout=ipyw.Layout(flex='1 1 auto',
                                                              justify_content='center'))]),
                               ipyw.VBox([
                                  # Map 
                                 ipyw.HBox([txt_map],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_map,incl_map]),
                                                       ipyw.HBox([text_lyr,img_tile]),
                                                       ipyw.HBox([text_lbl,lbl_buff]),
                                                       ipyw.HBox([text_ext,ext_buff])])])])],
                               layout=ipyw.Layout(justify_content='space-around'))
                     ])

    #----------------------------------------------------------------------------------------------
    # Display interactive plot
    #----------------------------------------------------------------------------------------------

    # Update dropdown values to reflect magnitude change between methods
    def update_dropdowns(change):
        if change.new in ['rx1day-max', 'rx1day-mean']:
            ymajtick.value,ymintick.value,maxbuff.value,minbuff.value = 1., 0.5, 1., 1.
        elif change.new in ['alldays-mean', 'raindays-mean']:
            print('Hold tight while the widget readjusts itself...')
            ymajtick.value,ymintick.value,maxbuff.value,minbuff.value = 0.05, 0.01, 0.05, 0.05
    method.observe(update_dropdowns, names='value')
    
    # Define function with only interactive components that runs widget.plot function
    def plot_fig(month1,month2,num_days,num_mons,num_stns,method,incl_tl,tl_syr,tl_eyr,minbuff,
                 maxbuff,ymajtick,ymintick,xmajtick,xmintick,incl_map,img_tile,lbl_buff,ext_buff):
        
        fig,ts = plots.timeseries_pcpn_plot(
                        var=var,meta=meta,location_name=location_name,nlat=float(nlat),
                        slat=float(slat),wlon=float(wlon),elon=float(elon),month1=month1,
                        month2=month2,num_days=num_days,num_mons=num_mons,num_stns=num_stns,
                        method=method,incl_tl=incl_tl,tl_syr=tl_syr,tl_eyr=tl_eyr,minbuff=minbuff,
                        maxbuff=maxbuff,ymajtick=ymajtick,ymintick=ymintick,xmajtick=xmajtick,
                        xmintick=xmintick,incl_map=incl_map,img_tile=img_tile,lbl_buff=lbl_buff,
                        ext_buff=ext_buff)

        # Create a button widget to download the figure as PDF
        pdf_output = ipyw.Output()
        def download_pdf(button):
           pdf_filename = 'figure.pdf'
           pdf_opts(fig=fig,pdf_output=pdf_output,pdf_filename=pdf_filename)
        pdf_but = ipyw.Button(description='Download Figure', layout={'width': '140px'})
        pdf_but.on_click(download_pdf)

        # Create a button widget to download data as Excel
        xcl_output = ipyw.Output()
        def download_xcl(button):
            with xcl_output: print('Download initiated. Can take more than a minute if over 100 stations '+
                                   'are queried. Do not click download button again.')
            xcl_filename = 'data.xlsx'
            with pd.ExcelWriter(xcl_filename) as w:
                var.assign(**{var.columns[0]: var.iloc[:,0].astype(str)}
                           ).to_excel(w,sheet_name='stations',index=False)
                meta.to_excel(w,sheet_name='metadata',index=False)
                ts.rename(columns={'Value':method}).to_excel(w,sheet_name='timeseries',index=False)
            xcl_opts(xcl_filename=xcl_filename,xcl_output=xcl_output)
        xcl_but = ipyw.Button(description='Download Data',layout=ipyw.Layout(width='140px'))
        xcl_but.on_click(download_xcl)

        # Display download buttons together
        button_box = ipyw.VBox([ipyw.HBox([pdf_but,xcl_but],layout=ipyw.Layout(justify_content='center'))])
        display(button_box,pdf_output,xcl_output)

    # Interactive output with only interactive components in dictionary
    out = ipyw.interactive_output(plot_fig,{'month1':month1,'month2':month2,'num_days':num_days,
                                            'num_mons':num_mons,'num_stns':num_stns,'method':method,
                                            'incl_tl':incl_tl,'tl_syr':tl_syr,'tl_eyr':tl_eyr,
                                            'minbuff':minbuff,'maxbuff':maxbuff,'ymajtick':ymajtick,
                                            'ymintick':ymintick,'xmajtick':xmajtick,'xmintick':xmintick,
                                            'incl_map':incl_map,'img_tile':img_tile,'lbl_buff':lbl_buff,
                                            'ext_buff':ext_buff})
    display(ui,out)

#======================================================================================================
# timeseries_snow_widget
#======================================================================================================

def timeseries_snow_widget(var,meta,location_name,nlat,slat,wlon,elon):

    #----------------------------------------------------------------------------------------------
    # Set up parameters to toggle
    #----------------------------------------------------------------------------------------------

    # Specify months to include
    txt_monthi = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_timeseries} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Months to include</a></h3>')
    text_mon1 = ipyw.Label(value='From',layout=ipyw.Layout(width='50px'))
    month1    = ipyw.Dropdown(options=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct',
                                       'Nov','Dec'],value='Jan',layout=ipyw.Layout(width='80px'))
    text_mon2 = ipyw.Label(value='To',layout=ipyw.Layout(width='50px'))
    month2    = ipyw.Dropdown(options=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct',
                                       'Nov','Dec'],value='Dec',layout=ipyw.Layout(width='80px'))

    # Method and plot features
    txt_meth = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_timeseries} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Choose what to plot</a></h3>')
    text_meth = ipyw.Label(value='Method to use',layout=ipyw.Layout(width='100px'))
    method = ipyw.Dropdown(options=[('Max Rx1day','rx1day-max'), 
                                   #('Mean Rx1day','rx1day-mean'), # removing this option for now
                                    ('Mean of all days','alldays-mean'),
                                    ('Mean of snow days','snowdays-mean')],value='rx1day-max',
                           layout=ipyw.Layout(width='125px'))
    text_tl = ipyw.Label(value='Include trendline?',layout=ipyw.Layout(width='120px'))
    incl_tl = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='80px'))
    text_yr = ipyw.Label(value='Trendline Years',layout=ipyw.Layout(width='100px'))
    tl_syr = ipyw.Dropdown(options=['Start',*np.sort(var['Date'].dt.year.unique())[:-1]],
                           value='Start',layout=ipyw.Layout(width='60px'))
    tl_eyr = ipyw.Dropdown(options=['End',*np.sort(var['Date'].dt.year.unique())[::-1][1:]],
                           value='End',layout=ipyw.Layout(width='60px'))

    # Data quality standards
    txt_dq = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_timeseries} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Data quality</a></h3>')
    text_ndays = ipyw.Label(value='Number of days',layout=ipyw.Layout(width='120px'))
    num_days = ipyw.Dropdown(options=np.arange(28),value=15,layout=ipyw.Layout(width='60px'))
    text_nmons = ipyw.Label(value='Number of months',layout=ipyw.Layout(width='120px'))
    num_mons = ipyw.Dropdown(options=np.arange(13),value=12,layout=ipyw.Layout(width='60px'))
    text_stns = ipyw.Label(value='Number of stations',layout=ipyw.Layout(width='120px'))
    if len(meta) == 1:
       num_stns = ipyw.Dropdown(options=[1],value=1,layout=ipyw.Layout(width='60px'))
    else:
       num_stns = ipyw.Dropdown(options=np.arange(1,len(meta)),value=1,
                                layout=ipyw.Layout(width='60px'))

    # Tick stride
    txt_tick = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis tick stride</a></h3>')
    ymajtk_desc = ipyw.Label(value='Major Y tick stride',layout=ipyw.Layout(width='120px'))
    ymajtick    = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    
    ymajtk_unit = ipyw.Label(value='inches')
    ymintk_desc = ipyw.Label(value='Minor Y tick stride',layout=ipyw.Layout(width='120px'))
    ymintick    = ipyw.FloatText(value=0.5,layout=ipyw.Layout(width='60px'))
    ymintk_unit = ipyw.Label(value='inches')
    xmajtk_desc = ipyw.Label(value='Major X tick stride',layout=ipyw.Layout(width='120px'))
    xmajtick    = ipyw.IntText(value=20,layout=ipyw.Layout(width='60px'))
    xmajtk_unit = ipyw.Label(value='years')
    xmintk_desc = ipyw.Label(value='Minor X tick stride',layout=ipyw.Layout(width='120px'))
    xmintick    = ipyw.IntText(value=5,layout=ipyw.Layout(width='60px'))
    xmintk_unit = ipyw.Label(value='years')

    # Y-axis buffer
    txt_buff = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_yaxis} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Y-axis buffer</a></h3>')
    maxb_desc = ipyw.Label(value='Buffer above y-axis',layout=ipyw.Layout(width='120px'))
    maxbuff   = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    maxb_unit = ipyw.Label(value='inches')
    minb_desc = ipyw.Label(value='Buffer below y-axis',layout=ipyw.Layout(width='120px'))
    minbuff   = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='60px'))
    minb_unit = ipyw.Label(value='inches')

    # Map
    txt_map   = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_map} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Map of stations</a></h3>')
    text_map  = ipyw.Label(value='Include map?',layout=ipyw.Layout(width='100px'))
    incl_map  = ipyw.Dropdown(options=['True (left)','True (right)','False'],value='True (left)',
                              layout=ipyw.Layout(width='90px'))
    text_lyr  = ipyw.Label(value='Image tile',layout=ipyw.Layout(width='100px'))
    img_tile  = ipyw.Dropdown(options=['QuadtreeTiles','GoogleTiles','OpenStreetMap','grey'],
                              value='QuadtreeTiles',layout=ipyw.Layout(width='80px'))
    text_lbl = ipyw.Label(value='Label distance',layout=ipyw.Layout(width='100px'))
    lbl_buff = ipyw.Dropdown(options=[('10%',0.1),('20%',0.2),('30%',0.3),('40%',0.4),('50%',0.5),
                                       ('60%',0.6),('70%',0.7),('80%',0.8),('90%',0.9),('None',1.5)],
                              value=0.3,layout=ipyw.Layout(width='90px'))
    text_ext = ipyw.Label(value='Lat/lon buffer',layout=ipyw.Layout(width='100px'))
    ext_buff = ipyw.Dropdown(options=[('0.1°',0.1),('0.25°',0.25),('0.5°',0.5),('1°',1.),('5°',5.)],
                              value=0.5,layout=ipyw.Layout(width='90px'))

    #----------------------------------------------------------------------------------------------
    # Layout for dropdowns
    #----------------------------------------------------------------------------------------------

    ui = ipyw.VBox([
                    # FIRST ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Specify months to include
                                 ipyw.HBox([txt_monthi],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_mon1,month1]),
                                                       ipyw.HBox([text_mon2,month2])])],
                                           layout=ipyw.Layout(justify_content='center'))]),
                               ipyw.VBox([
                                 # Method
                                 ipyw.HBox([txt_meth],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_meth,method]),
                                 ipyw.HBox([text_tl,incl_tl]),
                                 ipyw.HBox([text_yr,tl_syr,tl_eyr])]),
                               ipyw.VBox([
                                 # Data quality standards
                                 ipyw.HBox([txt_dq],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_ndays,num_days]),
                                                       ipyw.HBox([text_nmons,num_mons]),
                                                       ipyw.HBox([text_stns,num_stns])])])])],
                               layout=ipyw.Layout(justify_content='space-around')),
                    # SECOND ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Tick stride
                                 ipyw.HBox([txt_tick],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([ymajtk_desc,ymajtick,ymajtk_unit]),
                                                       ipyw.HBox([ymintk_desc,ymintick,ymintk_unit]),
                                                       ipyw.HBox([xmajtk_desc,xmajtick,xmajtk_unit]),
                                                       ipyw.HBox([xmintk_desc,xmintick,xmintk_unit])])],
                                            layout=ipyw.Layout(flex='1 1 auto',
                                                               justify_content='space-between'))]),
                               ipyw.VBox([
                                 # Y-axis buffer
                                 ipyw.HBox([txt_buff],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([maxb_desc,maxbuff,maxb_unit]),
                                                       ipyw.HBox([minb_desc,minbuff,minb_unit])])],
                                           layout=ipyw.Layout(flex='1 1 auto',
                                                              justify_content='center'))]),
                               ipyw.VBox([
                                  # Map 
                                 ipyw.HBox([txt_map],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([ipyw.VBox([ipyw.HBox([text_map,incl_map]),
                                                       ipyw.HBox([text_lyr,img_tile]),
                                                       ipyw.HBox([text_lbl,lbl_buff]),
                                                       ipyw.HBox([text_ext,ext_buff])])])])],
                               layout=ipyw.Layout(justify_content='space-around'))
                     ])

    #----------------------------------------------------------------------------------------------
    # Display interactive plot
    #----------------------------------------------------------------------------------------------

    # Update dropdown values to reflect magnitude change between methods
    def update_dropdowns(change):
        if change.new in ['rx1day-max', 'rx1day-mean']:
            ymajtick.value,ymintick.value,maxbuff.value,minbuff.value = 1., 0.5, 1., 1.
        elif change.new in ['alldays-mean', 'snowdays-mean']:
            print('Hold tight while the widget readjusts itself...')
            ymajtick.value,ymintick.value,maxbuff.value,minbuff.value = 0.05, 0.01, 0.05, 0.05
    method.observe(update_dropdowns, names='value')
    
    # Define function with only interactive components that runs widget.plot function
    def plot_fig(month1,month2,num_days,num_mons,num_stns,method,incl_tl,tl_syr,tl_eyr,minbuff,
                 maxbuff,ymajtick,ymintick,xmajtick,xmintick,incl_map,img_tile,lbl_buff,ext_buff):
        
        fig,ts = plots.timeseries_snow_plot(
                        var=var,meta=meta,location_name=location_name,nlat=float(nlat),
                        slat=float(slat),wlon=float(wlon),elon=float(elon),month1=month1,
                        month2=month2,num_days=num_days,num_mons=num_mons,num_stns=num_stns,
                        method=method,incl_tl=incl_tl,tl_syr=tl_syr,tl_eyr=tl_eyr,minbuff=minbuff,
                        maxbuff=maxbuff,ymajtick=ymajtick,ymintick=ymintick,xmajtick=xmajtick,
                        xmintick=xmintick,incl_map=incl_map,img_tile=img_tile,lbl_buff=lbl_buff,
                        ext_buff=ext_buff)

        # Create a button widget to download the figure as PDF
        pdf_output = ipyw.Output()
        def download_pdf(button):
           pdf_filename = 'figure.pdf'
           pdf_opts(fig=fig,pdf_output=pdf_output,pdf_filename=pdf_filename)
        pdf_but = ipyw.Button(description='Download Figure', layout={'width': '140px'})
        pdf_but.on_click(download_pdf)

        # Create a button widget to download data as Excel
        xcl_output = ipyw.Output()
        def download_xcl(button):
            with xcl_output: print('Download initiated. Can take more than a minute if over 100 stations '+
                                   'are queried. Do not click download button again.')
            xcl_filename = 'data.xlsx'
            with pd.ExcelWriter(xcl_filename) as w:
                var.assign(**{var.columns[0]: var.iloc[:,0].astype(str)}
                           ).to_excel(w,sheet_name='stations',index=False)
                meta.to_excel(w,sheet_name='metadata',index=False)
                ts.rename(columns={'Value':method}).to_excel(w,sheet_name='timeseries',index=False)
            xcl_opts(xcl_filename=xcl_filename,xcl_output=xcl_output)
        xcl_but = ipyw.Button(description='Download Data',layout=ipyw.Layout(width='140px'))
        xcl_but.on_click(download_xcl)

        # Display download buttons together
        button_box = ipyw.VBox([ipyw.HBox([pdf_but,xcl_but],layout=ipyw.Layout(justify_content='center'))])
        display(button_box,pdf_output,xcl_output)

    # Interactive output with only interactive components in dictionary
    out = ipyw.interactive_output(plot_fig,{'month1':month1,'month2':month2,'num_days':num_days,
                                            'num_mons':num_mons,'num_stns':num_stns,'method':method,
                                            'incl_tl':incl_tl,'tl_syr':tl_syr,'tl_eyr':tl_eyr,
                                            'minbuff':minbuff,'maxbuff':maxbuff,'ymajtick':ymajtick,
                                            'ymintick':ymintick,'xmajtick':xmajtick,'xmintick':xmintick,
                                            'incl_map':incl_map,'img_tile':img_tile,'lbl_buff':lbl_buff,
                                            'ext_buff':ext_buff})
    display(ui,out)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#
# SPATIAL MAP WIDGETS
#
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#======================================================================================================
# spatialmap_tmax_widget
#======================================================================================================


#======================================================================================================
# spatialmap_pcpn_widget
#======================================================================================================

def spatialmap_pcpn_widget(var,meta,location_name,nlat,slat,wlon,elon):
    
    #----------------------------------------------------------------------------------------------
    # Set up parameters to toggle
    #----------------------------------------------------------------------------------------------

    # Variables to define before setting ipywidget variables
    mon_str        = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    days_per_month = [31,29,31,30,31,30,31,31,30,31,30,31]
    tuple_str = [f'{m} {d}' for m,d in zip(np.repeat(mon_str,days_per_month),
                                           np.concatenate([np.arange(1,z+1) for z in days_per_month]))]
    tuple_num = [f'{str(m).zfill(2)}-{str(d).zfill(2)}' for m,d in zip(np.repeat(np.arange(1,13),
                        days_per_month),np.concatenate([np.arange(1,z+1) for z in days_per_month]))] 

    # Date(s) to plot
    txt_date = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_spatialmap} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Date(s) to plot</a></h3>')
    text_span = ipyw.Label(value='Time Span',layout=ipyw.Layout(width='70px'))
    timespan  = ipyw.Dropdown(options=['Single Day','Multiple Days'],value='Single Day',
                              layout=ipyw.Layout(width='120px'))
    text_sngl = ipyw.Label(value='If single day',layout=ipyw.Layout(width='80px'))
    sngl_md   = ipyw.Dropdown(options=list(zip(tuple_str,tuple_num)),value='09-01',
                              layout=ipyw.Layout(width='75px'))
    sngl_yr   = ipyw.Dropdown(options=np.arange(1950,datetime.now().year+1)[::-1],value=2023,
                              layout=ipyw.Layout(width='70px'))
    text_mult = ipyw.Label(value='If multiple days',layout=ipyw.Layout(width='90px'))
    text_to   = ipyw.Label(value='to',layout=ipyw.Layout(width='20px'))
    mult_md1  = ipyw.Dropdown(options=list(zip(tuple_str,tuple_num)),value='09-01',
                              layout=ipyw.Layout(width='75px'))
    mult_yr1  = ipyw.Dropdown(options=np.arange(1950,datetime.now().year+1)[::-1],value=2023,
                              layout=ipyw.Layout(width='70px'))
    mult_md2  = ipyw.Dropdown(options=list(zip(tuple_str,tuple_num)),value='09-02',
                              layout=ipyw.Layout(width='75px'))
    mult_yr2  = ipyw.Dropdown(options=np.arange(1950,datetime.now().year+1)[::-1],value=2023,
                              layout=ipyw.Layout(width='70px'))
    text_stats = ipyw.Label(value='Stats (if multiple days)',layout=ipyw.Layout(width='140px'))
    stats      = ipyw.Dropdown(options=['Mean','Sum'],value='Sum',layout=ipyw.Layout(width='80px'))
    
    # Display stations
    txt_stns = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_spatialmap} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Display stations</a></h3>')
    text_loc = ipyw.Label(value='Show locations on map',layout=ipyw.Layout(width='140px'))
    incl_loc = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='80px'))
    text_col = ipyw.Label(value='Colors of stations',layout=ipyw.Layout(width='140px'))
    stns_col = ipyw.Dropdown(options=[('Black','k'),('Red','r'),('White','w')],# will add colored by value later
                             value='k',layout=ipyw.Layout(width='80px'))
    text_dots = ipyw.Label(value='Station dot size',layout=ipyw.Layout(width='100px'))
    dot_size  = ipyw.IntSlider(value=3,min=1,max=10,step=1,orientation='horizontal',
                               layout=ipyw.Layout(width='140px'))

    # Map extent
    txt_coord = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_spatialmap} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Map extent</a></h3>')
    text_dist = ipyw.Label(value='Distance from query region',layout=ipyw.Layout(width='160px'))
    text_n    = ipyw.Label(value='North',layout=ipyw.Layout(width='40px'))
    text_s    = ipyw.Label(value='South',layout=ipyw.Layout(width='40px'))
    text_w    = ipyw.Label(value='West',layout=ipyw.Layout(width='40px'))
    text_e    = ipyw.Label(value='East',layout=ipyw.Layout(width='40px'))
    text_deg  = ipyw.Label(value='°',layout=ipyw.Layout(width='10px'))
    nlatbuf   = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='50px'))
    slatbuf   = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='50px'))
    wlonbuf   = ipyw.FloatText(value=1.5,layout=ipyw.Layout(width='50px'))
    elonbuf   = ipyw.FloatText(value=1.5,layout=ipyw.Layout(width='50px'))    

    # Map Properties
    txt_map = ipyw.HTML(value=f'<h3><a style="color: black; "href={url_spatialmap} target="_blank" ' +
                                'onmouseover="this.style.textDecoration=\'underline\'" '+
                                'onmouseout="this.style.textDecoration=\'none\'"'+
                                '>Map properties</a></h3>')
    text_cmap = ipyw.Label(value='Color Map',layout=ipyw.Layout(width='120px'))
    cmap      = ipyw.Dropdown(options=['Haxby','Blues','GreenBlue'],value='Haxby',
                              layout=ipyw.Layout(width='100px'))
    text_ticks = ipyw.Label(value='Show tick marks',layout=ipyw.Layout(width='120px'))
    incl_ticks = ipyw.Dropdown(options=[True,False],value=True,layout=ipyw.Layout(width='100px'))    
    text_stride = ipyw.Label(value='Tick stride',layout=ipyw.Layout(width='70px'))
    text_dlat   = ipyw.Label(value='° lat',layout=ipyw.Layout(width='30px'))
    text_dlon   = ipyw.Label(value='° lon',layout=ipyw.Layout(width='30px'))
    latstride   = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='50px'))
    lonstride   = ipyw.FloatText(value=1.,layout=ipyw.Layout(width='50px'))  
    
    #----------------------------------------------------------------------------------------------
    # Button to update figure
    #----------------------------------------------------------------------------------------------
    
    # Create button
    update_button = ipyw.Button(description='Update Figure',layout=ipyw.Layout(width='150px'))
 
    # Define function that is run when button is clicked
    def update_fig(button):
       
       print('Button click worked!')       
 
       # # Clear figure output and redisplay ipywidgets
       # clear_output(wait=True)
       # display(ui)             # ui is defined below
       # 
       # # Print message to users
       # if timespan.value == 'Multiple Days':
       #     print('Data is being retrieved! This process may take several minutes if query is large!')
       # 
       # # Run figure again
       # plots.spatialmap_pcpn_plot(var=var,meta=meta,location_name=location_name,nlat=float(nlat),
       #                            slat=float(slat),wlon=float(wlon),elon=float(elon),
       #                            timespan=timespan.value,sngl_md=sngl_md.value,sngl_yr=sngl_yr.value,
       #                            mult_md1=mult_md1.value,mult_yr1=mult_yr1.value,
       #                            mult_md2=mult_md2.value,mult_yr2=mult_yr2.value,stats=stats.value,
       #                            incl_loc=incl_loc.value,stns_col=stns_col.value,
       #                            dot_size=dot_size.value,cmap=cmap.value,incl_ticks=incl_ticks.value,
       #                            nlatbuf=nlatbuf.value,slatbuf=slatbuf.value,wlonbuf=wlonbuf.value,
       #                            elonbuf=elonbuf.value,latstride=latstride.value,
       #                            lonstride=lonstride.value)
        
    # On click
    update_button.on_click(update_fig)
 
    #----------------------------------------------------------------------------------------------
    # Layout for dropdowns
    #----------------------------------------------------------------------------------------------

    ui = ipyw.VBox([
                    # FIRST ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Date(s) to plot
                                 ipyw.HBox([txt_date],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_span,timespan],layout=ipyw.Layout(
                                                                        justify_content='center')),
                                 ipyw.HBox([text_sngl,sngl_md,sngl_yr],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_mult,mult_md1,mult_yr1,text_to,mult_md2,mult_yr2],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_stats,stats],layout=ipyw.Layout(
                                                                     justify_content='center'))]),
                               
                               ipyw.VBox([
                                 # Display stations
                                 ipyw.HBox([txt_stns],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_loc,incl_loc],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_col,stns_col],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_dots,dot_size],layout=ipyw.Layout(
                                                                       justify_content='center'))])],                                                                                
                               layout=ipyw.Layout(justify_content='space-around')),            
                    # SECOND ROW
                    ipyw.HBox([ipyw.VBox([
                                 # Map extent
                                 ipyw.HBox([txt_coord],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_dist],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_n,nlatbuf,text_deg,wlonbuf,text_deg,text_w],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_s,slatbuf,text_deg,elonbuf,text_deg,text_e],
                                           layout=ipyw.Layout(justify_content='center'))]),   
                               ipyw.VBox([
                                 # Map properties
                                 ipyw.HBox([txt_map],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_cmap,cmap],layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_ticks,incl_ticks],
                                           layout=ipyw.Layout(justify_content='center')),
                                 ipyw.HBox([text_stride,latstride,text_dlat,lonstride,text_dlon],
                                           layout=ipyw.Layout(justify_content='center'))])],
                               layout=ipyw.Layout(justify_content='space-around')),
                     # THIRD ROW
                     ipyw.HBox([update_button],layout=ipyw.Layout(justify_content='space-around'))
                     ])
    
    #----------------------------------------------------------------------------------------------
    # Display inital plot that gets updated with button click
    #----------------------------------------------------------------------------------------------
    
    # Initial display of ipywidgets
    display(ui)
    
    # Initial display of plot
    plots.spatialmap_pcpn_plot(var=var,meta=meta,location_name=location_name,nlat=float(nlat),
                               slat=float(slat),wlon=float(wlon),elon=float(elon),
                               timespan=timespan.value,sngl_md=sngl_md.value,sngl_yr=sngl_yr.value,
                               mult_md1=mult_md1.value,mult_yr1=mult_yr1.value,
                               mult_md2=mult_md2.value,mult_yr2=mult_yr2.value,stats=stats.value,
                               incl_loc=incl_loc.value,stns_col=stns_col.value,
                               dot_size=dot_size.value,cmap=cmap.value,incl_ticks=incl_ticks.value,
                               nlatbuf=nlatbuf.value,slatbuf=slatbuf.value,wlonbuf=wlonbuf.value,
                               elonbuf=elonbuf.value,latstride=latstride.value,lonstride=lonstride.value)








