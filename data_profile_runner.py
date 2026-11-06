import os
#from matplotlib.pyplot import table
from data_profile_spreadsheet import DataProfileSpreadsheets
from PortalConnector import PortalConnector
# from PortalExporter import DatabaseConnector
import yaml


datasets =  [
        {'census_year': 2024,
        'census_product': 'acs1',
        'specifications': {
            "DP02": {'short_title': 'Social Characteristics Data Profle', 
                    'long_title':'ACS Data Profile: Social Characteristics, ACS 2024 1-Year Data'},
            "DP03": {'short_title': 'Economic Data Profle', 
                    'long_title':'ACS Data Profile: Economic Characteristics, ACS 2024 1-Year Data' },
            "DP04": {'short_title': 'Housing Data Profle', 
                    'long_title':'ACS Data Profile: Housing Characteristics, ACS 2024 1-Year Data' },
            "DP05": {'short_title': 'Demographic Data Profle', 
                    'long_title':'ACS Data Profile: Demographic Characteristics, ACS 2024 1-Year Data' }    
                }
        }
]


agol_user = os.getenv('AGOL_ADMIN_USERNAME')
agol_pw = os.getenv('AGOL_ADMIN_PW')

# with open(r'Config\\auth.yml') as file:
# 	auth = yaml.load(file, Loader=yaml.FullLoader)
# portal_conn = PortalConnector(
# 	portal_username=auth['arc_gis_online']['username'],
# 	portal_pw=auth['arc_gis_online']['pw'])
portal_conn = PortalConnector(
	portal_username=agol_user,
	portal_pw=agol_pw)
gis = portal_conn.gis

for data_group in datasets:
    c_year = data_group['census_year']
    c_prod = data_group['census_product']
    for table_code in data_group['specifications'].keys():
        specs = data_group['specifications'][table_code]
        census_year = c_year
        census_product = c_prod
        long_title = specs['long_title']
        short_title = specs['short_title']
        data_prof = DataProfileSpreadsheets(census_year, 
                                            census_product, 
                                            table_code, 
                                            short_title, 
                                            long_title)
        data_prof.create_workbooks()
