from PortalConnector import PortalConnector
import yaml
import os
import shutil
from Layer import Layer
import importlib
# importlib.reload(Layer)


# Setup: construct connector, etc
with open(r'Config\\auth.yml') as file:
	auth = yaml.load(file, Loader=yaml.FullLoader)
portal_conn = portalconnector(
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
		source = config['dataset']['source']
		title = params['title']
		is_spatial = params['spatial_data']
		if is_spatial == True and source['is_simple'] == True:
			lyr = portal_conn.find_by_title(title)
			if lyr != 'no object':
				mdata_file = lyr.metadata
				elmergeo_layer_name = source['table_name']
				# layer_file_name = f.replace(".yml", "")
				m_path = f"{dest_path}{elmergeo_layer_name}_metadata.xml"
				shutil.copy(mdata_file, dest_path)
				new_path = f"{dest_path}/{elmergeo_layer_name}_metadata.xml"
				shutil.move(f"{dest_path}/metadata.xml", new_path)


# from pathlib import Path

# run_files = os.listdir('./Config/run_files/')
# for f in run_files:
# 	# f_path = Path('Config/run_files')/f
# 	f_path = f'Config/run_files/{f}'
# 	print(f_path)
# 	layer = Layer(f_path, metadata_path = r"./workspace/metadata2/")
# 	layer.get_metadata()
# 	layer.rename_metadata()