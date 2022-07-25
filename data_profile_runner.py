#from matplotlib.pyplot import table
from data_profile_spreadsheet import DataProfileSpreadsheets

datasets = {
    "DP02": {'short_title': 'Social Characteristics Data Profle', 'long_title':'Social Characteristics Data Profile, ACS 2020 5-Year Data'  },
    "DP03": {'short_title': 'Economic Data Profle', 'long_title':'Economic Characteristics Data Profile, ACS 2020 5-Year Data' },
    "DP04": {'short_title': 'Housing Data Profle', 'long_title':'Housing Characteristics Data Profile, ACS 2020 5-Year Data' },
    "DP05": {'short_title': 'Demographic Data Profle', 'long_title':'Demographic Characteristics Data Profile, ACS 2020 5-Year Data' }    
}
datasets = {
    "DP04": {'short_title': 'test dp', 'long_title':'Housing Characteristics Data Profile, ACS 2020 5-Year Data' }
}

for table_code in datasets.keys():
    census_year = 2019
    census_product = 'acs5'
    long_title = datasets[table_code]['long_title']
    short_title = datasets[table_code]['short_title']
    data_prof = DataProfileSpreadsheets(census_year, 
                                        census_product, 
                                        table_code, 
                                        short_title, 
                                        long_title)
    data_prof.create_workbooks()
