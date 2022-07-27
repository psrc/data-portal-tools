from attr import NOTHING
import pandas as pd
import urllib
import pyodbc
import shutil
import openpyxl
import yaml
from copy import copy
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

class DataProfileSpreadsheets(object):
    def __init__(self, census_year, census_product, census_table_code, short_title, long_title):
        try:
            self.census_year = census_year
            self.census_product = census_product
            self.census_table_code = census_table_code
            self.short_title = short_title
            self.long_title = long_title
            self.index_sheet_name = 'Tab Index'
            self.geog_groups = {
                'State-County-MSA': ['State', 'County', 'MSA'],
                'City': ['City'],
                'CDP': ['CDP']            
            }
            self.decimal_estimate_vars = {
                'DP02': [],
                'DP03': [],
                'DP04': ['DP04_0004', 'DP04_0005', 'DP04_0037', 'DP04_0048', 'DP04_0049'],
                'DP05': []
            }

        except Exception as e:
            print(e.args[0])
            raise   
        

    def create_data_profile_df(self):
        try:
            conn_string = "DRIVER={ODBC Driver 17 for SQL Server}; SERVER=AWS-PROD-SQL\Sockeye; DATABASE=Elmer; trusted_connection=yes"
            sql_conn = pyodbc.connect(conn_string)
            sql_statement = "select * from data_portal.census_data_profile({}, '{}', '{}')".format(self.census_year, 
                                                                                                self.census_product, 
                                                                                                self.census_table_code)
            self.df = pd.read_sql(sql=sql_statement, con=sql_conn)
            sql_conn.close()
                
        except Exception as e:
            print(e.args[0])
            raise   
        
    
    def geogs_in_geog_type(self, geog_type):
        try:
            df = self.df
            geogs = df[df['geography_type'] == geog_type].geography_name.unique()
            return geogs
            
        except Exception as e:
            print(e.args[0])
            raise   
    
    def filtered_df(self, geog_type, geog):
        """
        Fiters self.df to geog_type and geog,
        and re-creates the index for the new recordset 
        to include sequential integers
        """
        try:
            df = self.df
            df = df[df['geography_type'] == geog_type]
            df = df[df['geography_name'] == geog]
            df = df[['variable_description', 'estimate', 'margin_of_error', 'estimate_percent', 'margin_of_error_percent', 'depth', 'variable_name', 'category']]
            df.columns=['Subject', 'Estimate', 'Margin of Error', 'Percent', 'Percent Margin of Error', 'depth', 'variable_name', 'category']
            df[['Estimate','Margin of Error', 'Percent', 'Percent Margin of Error']] = df[['Estimate','Margin of Error', 'Percent', 'Percent Margin of Error']].fillna('(x)')
            idx_range = range(0, len(df.index))
            ilist = []
            ilist.extend(idx_range)
            df.index = ilist
            return df
        
        except Exception as e:
            print(e.args[0])
            raise   
    
    
    def format_geo_name(self, geog, geog_type):
        try:
            if geog_type == 'CDP':
                geog = geog.replace(' CDP', '')
            if len(geog) > 30:
                geog = geog[0:30]
            return geog
            
        except Exception as e:
            print(e.args[0])
            raise   
    
    
    def prettify_geog_name(self, geog_name, geog_type):
        try: 
            if geog_type in ('MSA', 'State'):
                name = "{} {}".format(geog_name, geog_type)
            else:
                name = geog_name
            return name
       
        except Exception as e:
            print(e.args[0])
            raise   


    def insert_subheaders(self, ws, df):
        """
        insert line breaks whenever the CATEGORY value changes
        """
        try:
            start_row = 2
            # subheader_dict = self.subheader_vars
            # subhead_dict_len = len(subheader_dict)
            subheader_list_len = len(df.category.unique())
            end_row = len(df.index) + start_row + subheader_list_len
            for row in range(start_row, end_row):
                prev_cell_coord = 'H' + str(row-1)
                cell_coord = 'H' + str(row)
                this_cat = ws['I' + str(row)].value
                prev_cat = ws['I' + str(row-1)].value
                if this_cat != prev_cat and prev_cat is not None and this_cat is not None:
                    var_desc = ws['B' + str(row)].value
                    ws.insert_rows(row)
                    subheader_coord = 'A' + str(row)
                    ws[subheader_coord] = this_cat.upper()
                    ws[subheader_coord].font = Font(bold=True)
                
        except Exception as e:
            #print("Error! cell_coord = {}".format(cell_coord))
            print(e.args[0])
            raise   

    def clear_columns(self, ws, df, col_names):
        try:
            start_row = 1
            # subheader_dict = self.subheader_vars
            # subhead_dict_len = len(subheader_dict)
            subhead_list_len = len(df.category.unique())
            end_row = len(df.index) + start_row + subhead_list_len + 2
            for col_name in col_names:
                for row in range(start_row, end_row):
                    cell_coord = col_name + str(row)
                    ws[cell_coord] = None

        except Exception as e:
            #print("Error! cell_coord = {}".format(cell_coord))
            print(e.args[0])
            raise   
    
    def geog_ws(self, geog_type, geog_name, wb):
        """
        Create a new worksheet in the workbook (wb), 
            and fill it with the data profile data for this geog_name.
            Then format the page to make it pretty.
        """
        try: 
            df = self.df
            data_profile_name = self.long_title
            header_row_size = 1
            f_geog_name = self.format_geo_name(geog_name, geog_type)
            ws = wb.create_sheet(title=f_geog_name)
            filtereddf = self.filtered_df(geog_type, geog_name)
            #finaldf = filtereddf.drop(['depth', 'variable_name'], axis=1)
            for r in dataframe_to_rows(filtereddf, index=False, header=True):
                #self.add_section_header(r, filtereddf, ws)
                r.insert(0,'')
                ws.append(r)

            #format worksheet body
            col_widths = {'A':2, 'B':75, 'C':15, 'D':15, 'E':15, 'F':15}
            for cw in col_widths.keys():
                ws.column_dimensions[cw].width = col_widths[cw]
            max_row = len(filtereddf.index) + header_row_size + 1
            col_styles = {'C':{'align':'center', 'num':'0,##'}, 
                        'D':{'align':'center', 'num':'0,##'},
                        'E':{'align':'center', 'num':'0.0'},
                        'F':{'align':'center', 'num':'0.0'}}
            dec_vars = self.decimal_estimate_vars[self.census_table_code]
            for r in range(header_row_size + 1, max_row):
                if self.census_table_code == 'DP05':
                    indent_level = (filtereddf.depth[r - 2]) * 2
                else:
                    indent_level = (filtereddf.depth[r - 2] - 1) * 2
                ws['B'+str(r)].alignment = Alignment(indent = indent_level)
                for c in col_styles.keys():
                    cell = ws[c+str(r)]
                    cell.alignment = Alignment(horizontal=col_styles[c]['align']) 
                    if filtereddf.variable_name[r-2] in dec_vars:
                        cell.number_format = '0.00'
                    else:
                        cell.number_format = col_styles[c]['num']

            #format worksheet header
            ws.row_dimensions[1].height = 30
            cols = ['A','B','C','D','E','F']
            for c in cols:
                cell = ws[c+str(1)]
                cell.font = Font(bold=True)
                cell.alignment = Alignment(wrap_text=True, horizontal='center')
                cell.fill = PatternFill(fill_type='solid', start_color='D7E4BC')
                header_border = Side(border_style="thin", color="000000")
                cell.border = Border(top=header_border, 
                                    left=header_border, 
                                    right=header_border, 
                                    bottom=header_border)
            
            
            self.insert_subheaders(ws, filtereddf)
            self.clear_columns(ws, filtereddf, ['G','H','I'])
                
            #insert title row
            ws.insert_rows(1)
            title_cell = ws['A1']
            pretty_geog_name = self.prettify_geog_name(geog_name, geog_type)
            title_cell.value = "{}: {}".format(data_profile_name, pretty_geog_name)
            title_cell.font = Font(size=18, bold=True)

            self.merge_cells_a_and_b(ws)
            
        except Exception as e:
            print(e.args[0])
            print("r value: {}".format(r))
            raise   
    
    
    def merge_cells_a_and_b(self, ws):
        try:
            cell_a = ws['A2']
            cell_b = ws['B2']
            cell_a.value =  cell_b.value
            cell_a.border =  copy(cell_b.border)
            cell_a.alignment =  copy(cell_b.alignment)
            cell_a.fill =  copy(cell_b.fill)
            ws.merge_cells("A2:B2")

        except Exception as e:
            print(e.args[0])
            raise   
    
    
    
    def add_links_to_index(self, wb, geogs, geog_types, file_name):
        """
        Add a new worksheet, with hyperlinks to all the other sheets.
        """
        try:
            index_sheet_name = self.index_sheet_name
            index_sheet = wb[index_sheet_name]
            header_cell = index_sheet['A1']
            header_cell.value = "For summary data for a specific geography, click a link below:"
            index_row = 2
            for geog_type in geog_types:
                geogs = self.geogs_in_geog_type(geog_type)
                for g in geogs:
                    target_sheet_name = self.format_geo_name(g, geog_type)
                    pretty_geog_name = self.prettify_geog_name(g, geog_type)
                    link_ws = wb[index_sheet_name]
                    link = file_name + "#'{}'!A1".format(target_sheet_name)
                    cell = link_ws.cell(row=index_row, column=1)
                    cell.hyperlink = link
                    cell.value = pretty_geog_name
                    cell.style = "Hyperlink"
                    index_row += 1 

        except Exception as e:
            print(e.args[0])
            raise   
    
    
    def create_wb(self, geog_group_name, geog_types):
        try:
            data_profile_name = self.long_title
            filename_stub = self.short_title.replace(" ", "_")
            vintage = self.census_year
            census_table = self.census_table_code
            wb = Workbook()
            fname = "{}_{}_{}.xlsx".format(filename_stub, geog_group_name, vintage)
            index_sheet = wb["Sheet"]
            index_sheet.title = self.index_sheet_name
            for geog_type in geog_types:
                geogs = self.geogs_in_geog_type(geog_type)
                for geo in geogs:
                    self.geog_ws(geog_type, geo, wb)
            self.add_links_to_index(wb, geogs, geog_types, fname)

            wb.save(filename=fname)   
        
        except Exception as e:
            print(e.args[0])
            raise   

    
    def create_workbooks(self):
        """
        Create Excel workbooks for all geography groups (State-County-MSA, City, and CDP).
        Exports one workbook per geography group.
        """
        try:
            self.create_data_profile_df()
            df = self.df
            data_profile_name = self.long_title
            short_title = self.short_title
            vintage = self.census_year
            census_table = self.census_table_code
            geog_types = df.geography_type.unique()
            geog_groups = self.geog_groups
            geog_groups = {'County': ['County']} ## Testing only!!!  Comment this out for production.
            for g_group_name in geog_groups.keys():
                geog_types = geog_groups[g_group_name]
                self.create_wb(g_group_name, geog_types)

        except Exception as e:
            print(e.args[0])
            raise   