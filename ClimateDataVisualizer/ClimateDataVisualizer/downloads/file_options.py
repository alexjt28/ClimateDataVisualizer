#######################################################################################################
#
# Functions for downloading files within the widget 
#
#######################################################################################################

# Use this to read in packages from other directories ---------
import sys, os
sys.path.append(os.path.dirname(os.getcwd())) # one dir back
import pandas as pd
from io import BytesIO
from base64 import b64encode
from IPython.display import HTML

#================================================================================================================
# PDF Options     
#================================================================================================================

def pdf_opts(fig,pdf_output,pdf_filename='figure.pdf'):
   with BytesIO() as byte:
       fig.savefig(byte,format='pdf')
       byte.seek(0)
       content_b64 = b64encode(byte.read()).decode()
   data_url = f'data:application/pdf;base64,{content_b64}'
   js_code = f"""var a = document.createElement('a');
                 a.setAttribute('download', '{pdf_filename}');
                 a.setAttribute('href', '{data_url}');
                 a.click();"""
   with pdf_output: display(HTML(f'<script>{js_code}</script>'))

#================================================================================================================
# Excel Options     
#================================================================================================================

def xcl_opts(xcl_output,xcl_filename='data.xlsx'):
   with open(xcl_filename, 'rb') as excel_file:
       excel_data = excel_file.read()
       excel_base64 = b64encode(excel_data).decode()
   data_url = f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_base64}' 
   js_code = f"""var a = document.createElement('a');
                 a.setAttribute('download', 'data.xlsx');
                 a.setAttribute('href', '{data_url}');
                 a.click();"""
   with xcl_output: display(HTML(f'<script>{js_code}</script>'))
