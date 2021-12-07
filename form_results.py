import numpy as np
import pandas as pd
import os
import yaml
from pathlib import Path
import shutil

class FormResults(object):
    """
    The results spreadsheet from the Data Portal metadata forms

    Inputs:
        in_file_name: the name for the Excel spreadsheet downloaded from the 
          "Initial PSRC Metadata Collection Form" (Microsoft form)
        in_file_dir: the full path specification for in_file_name
        config_dir: the full directory path to the config files that determine the export behavior for each layer
    """
    def __init__(self, 
        in_file_name,
        in_file_dir = r'C:\Users\cpeak\OneDrive - Puget Sound Regional Council\Projects\2021\data_portal\metadata_pipeline', 
        config_dir = r'.\Config\run_files',
        shared_column_def_path = r'C:\Users\cpeak\OneDrive - Puget Sound Regional Council\Question 1'
        ):
        try:
            # self.path = metadata_dir
            self.form_results_path = in_file_dir + '\\' + in_file_name
            self.shared_column_def_path = shared_column_def_path
            self.df = pd.read_excel(self.form_results_path)
            self.set_column_dict()
            self.config_dir = config_dir
            self.rename_columns()

        except Exception as e:
            print(e.args[0])
            raise


    def rename_columns(self):
        try:
            new_colnames = []
            for c in self.df.columns:
                newname = self.column_dict[c]
                new_colnames.append(newname)
            self.df.columns = new_colnames

        except Exception as e:
            print(e.args[0])
            raise


    def yamlize(self, in_series):
        """
        in_series = a row from self.df
        """
        ser = in_series
        out_yaml = yaml.load("""
        dataset:
            layer_params:
                title: {}
                tags: {}
                allow_edits: False
                spatial_data: True
                share_level: everyone
                accessInformation: {}
                licenseInfo: some text here
                metadata:
                    contact_name: {}
                    contact_email: {}
                    description: {}
                    data_source: {}
                    date_last_updated: {}
                    constraints: {}
                    data_lineage: {}
                    assessment: {}
                    summary_purpose: {}
        """.format(ser['Title'],
                    ser['Tags'],
                    ser['Abstract'],
                    ser['ContactName'],
                    ser['ContactEmail'],
                    ser['Abstract'],
                    ser['DataSource'],
                    ser['DateLastUpdated'],
                    ser['Assessment'], #is this in the form?
                    ser['DataLineage'],
                    ser['Assessment'],
                    'summary purpose'
                    ),
                yaml.FullLoader)
        
        return out_yaml        


    def set_column_dict(self):
        self.column_dict = {
            'ID': 'ID',
            'Start time': 'Starttime',
            'Completion time': 'Timestamp',
            'Email': 'Email',
            'Name': 'Name',
            'Dataset Name': 'Title',
            'Abstract': 'Abstract',
            'Time period covered by the data': 'TimePeriod',
            'Link to PSRC webpage': 'Webpage',
            'Links to background information or technical notes': 'TechNoteLink',
            'Name of data contact': 'ContactName',
            'Email address of data contact': 'ContactEmail',
            'Phone number of data contact': 'ContactPhone',
            'When was the dataset last updated?': 'DateLastUpdated',
            'How often is the dataset updated?': 'UpdateCadence',
            'What is the data source?': 'DataSource',
            'Description of the data collection process': 'DataLineage',
            'Assessment of the data': 'Assessment',
            'Internal location of GIS dataset': 'InternalLocation',
            'Category': 'Category',
            'Tags': 'Tags',
            'Field Definitions': 'FieldDefinitions',
            'Suggestions for improving the dataset.': 'Suggestions'
            }

    def mergedict(self, source, destination):
        """
        cribbed from stackoverflow user vincent
        https://stackoverflow.com/questions/20656135/python-deep-merge-dictionary-data
        
        run me with nosetests --with-doctest file.py
        
        merge two dictionaries into one, unioning their contents
            > a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
            > b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
            > merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
        True
        """
        try:
            for key, value in source.items():
                if isinstance(value, dict):
                    # get node or create one
                    node = destination.setdefault(key, {})
                    self.mergedict(value, node)
                else:
                    destination[key] = value

            return destination   

        except Exception as e:
            print(e.args[0])
            raise

    def find_config_file(self, target_title):
        """look through yaml files in run_files directory.
        If one is found, returns a dict with two keys:
            filepath (the path to the yaml file)
            yamldict (the contents of that yaml file, in dictionary form)
        If not, return False 
        """
        try:
            ret_value = False
            dir = self.config_dir
            for yfile in os.listdir(dir):
                dir_path = Path(dir)
                fpath = dir_path / yfile
                with open(fpath) as file:
                    my_yaml = yaml.load(file, Loader=yaml.FullLoader)
                y_title = my_yaml['dataset']['layer_params']['title']
                if y_title == target_title:
                    ret_dict = {}
                    ret_dict['filepath'] = fpath
                    ret_dict['yamldict'] = my_yaml
                    ret_value = ret_dict
                #print(y_title)
            return ret_value

        except Exception as e:
            print(e.args[0])
            raise


    def fields_path(self, excel_name):
        try:
            dir_path = self.shared_column_def_path
            f_name = excel_name.replace(" ","_")
            yaml_path = dir_path + '\\' + excel_name
            return yaml_path

        except Exception as e:
            print(e.args[0])
            raise


    def df_to_list_of_dicts(self, in_df):
        """
        from a field-definitions dataframe,
        create a list of dictionaries for the field names and definitions
        """
        try:
            field_list = []
            for i, r in in_df.iterrows():
                if r.Remove_Field != 'Yes':
                    f_dict = {'title': r['Field_Name'], 'description': r['Description ']}
                    field_list.append(f_dict)
            return field_list

        except Exception as e:
            print(e.args[0])
            raise


    def get_field_data(self, row):
        """
        given a series (row) with a column FieldDefinitions listing a path to a field spreadsheet,
        return the field definitions as a list of dicitonaries
        """
        try:
            url = row.FieldDefinitions
            l = url.split('&file=')[1]
            l = l.split('&action=')[0]
            l = l.replace('%20',' ')
            fpath = self.fields_path(l)
            print(fpath)
            df_fields = pd.read_excel(fpath)
            field_list = self.df_to_list_of_dicts(df_fields)
            return field_list

        except Exception as e:
            print(e.args[0])
            raise


    def integrate_fields(self):
        """
        # for each record in metadata form output
        #   creata a dictionary meta_dict from the row
        #   if there is a matching YAML config file
        #      merge meta_dict into the config file
        #   else:
        #      create a new config file
        """
        try:
            for i, r in self.df.iterrows():
                new_metadata = self.yamlize(r)
                # MOREMORE add field definitions to new_metadata
                fd = self.get_field_data(r)
                new_metadata['dataset']['layer_params']['metadata']['fields'] = fd
                title = new_metadata['dataset']['layer_params']['title']
                print('title: {}'.format(title))
                config_file = self.find_config_file(title)
                if config_file:
                    config_yaml = config_file['yamldict']
                    merged_yaml = self.mergedict(new_metadata, config_yaml)
                    with open(config_file['filepath'], 'w') as file:
                        #dictlist = config_file['yamldict']
                        doc = yaml.dump(merged_yaml, file)
                    print ("merged with {} and written to file.".format(config_file['filepath']))
                    #print("yaml: {}".format(merged_yaml))
                else:
                    print('no matching config file.  Writing new one...')
                    config_yaml = new_metadata
                    dir_path = Path(self.config_dir)
                    config_filename = title + '.yml'
                    fpath = dir_path / config_filename
                    with open(fpath, 'w') as file:
                        doc = yaml.dump(config_yaml, file)
                    print('{} written'.format(config_filename))


        except Exception as e:
            print(e.args[0])
            raise
