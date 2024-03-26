import yaml
from PortalExporter import PortalResource
# from PortalExporter import PortalResource
#from PortalExporter import PortalSpatialResource
from PortalExporter import PortalConnector
from PortalExporter import DatabaseConnector
import os
import json
import shutil


##############################################################################
# Setup: construct connector (for Examples 1 and 2)
##############################################################################
with open(r'Config\\auth.yml') as file:
	auth = yaml.load(file, Loader=yaml.FullLoader)
portal_conn = PortalConnector(
	portal_username=auth['arc_gis_online']['username'],
	portal_pw=auth['arc_gis_online']['pw'])
elmer_conn = DatabaseConnector(
	db_server='AWS-PROD-SQL\Sockeye',
	database='Elmer')
elmergeo_conn = DatabaseConnector(
	db_server='AWS-PROD-SQL\Sockeye',
	database='ElmerGeo')

dest_path = "./workspace/metadata/"
run_files = os.listdir('./Config/run_files/')
root_dir = os.getcwd()

def find_layer( resource):
	try:
		return_item = "no item"
		title = resource.resource_properties['title']
		gis = resource.portal_connector.gis
		owner_clause = '; owner:{}'.format(gis.users.me.username)
		content_list = gis.content.search(
			query='title:{}{}'.format(title, owner_clause),
			)
		lyr = "no object"
		for item in content_list:
			if (item['title'] == title and 'Feature' in item['type']) :
				# return_item = item
				lyr = item
				break	
		return(lyr)
        
	except Exception as e:
		print(e.args[0])
		raise

for f in run_files:
	os.chdir(root_dir)
	if r'Displacement' not in f:
		f_path = './Config/run_files/' + f
		with open(f_path) as file:
			config = yaml.load(file, Loader=yaml.FullLoader)
			params = config['dataset']['layer_params']
			is_spatial = params['spatial_data']
			if is_spatial == True:
				source = config['dataset']['source']
				title = params['title']
				my_resource = PortalResource(
					p_connector=portal_conn,
					db_connector=elmergeo_conn,
					params=params,
					source=source
					)
				lyr = find_layer(my_resource)
				if lyr != 'no object':
					mdata_file = lyr.metadata
					
					layer_file_name = f.replace(".yml", "")
					m_path = f"{dest_path}{layer_file_name}_metadata.xml"
					shutil.copy(mdata_file, dest_path)
					new_path = f"{dest_path}/{layer_file_name}_metadata.xml"
					shutil.move(f"{dest_path}/metadata.xml", new_path)