import yaml
from PortalConnector import PortalConnector
import os
import shutil


# Setup: construct connector, etc
with open(r'Config\\auth.yml') as file:
	auth = yaml.load(file, Loader=yaml.FullLoader)
portal_conn = PortalConnector(
	portal_username=auth['arc_gis_online']['username'],
	portal_pw=auth['arc_gis_online']['pw'])

dest_path = "./workspace/metadata/"
run_files = os.listdir('./Config/run_files/')
root_dir = os.getcwd()


# For each run_file, search for the matching layer in the Data Portal and download the metadata
for f in run_files:
	os.chdir(root_dir)
	f_path = './Config/run_files/' + f
	with open(f_path) as file:
		config = yaml.load(file, Loader=yaml.FullLoader)
		params = config['dataset']['layer_params']
		title = params['title']
		is_spatial = params['spatial_data']
		if is_spatial == True:
			lyr = portal_conn.find_by_title(title)
			if lyr != 'no object':
				mdata_file = lyr.metadata
				layer_file_name = f.replace(".yml", "")
				m_path = f"{dest_path}{layer_file_name}_metadata.xml"
				shutil.copy(mdata_file, dest_path)
				new_path = f"{dest_path}/{layer_file_name}_metadata.xml"
				shutil.move(f"{dest_path}/metadata.xml", new_path)