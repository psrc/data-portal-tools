import yaml
from PortalExporter import PortalResource
# from PortalExporter import PortalResource
#from PortalExporter import PortalSpatialResource
from PortalExporter import PortalConnector
from PortalExporter import DatabaseConnector
import os


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

def export(config):
	try:
		layers = config.keys()

		for l in layers:
			params = config[l]['layer_params']
			title = params['title']
			source = config[l]['source']
			is_spatial = params['spatial_data']
			if is_spatial:
				db_conn = elmergeo_conn
			else:
				db_conn = elmer_conn
			my_pub = PortalResource(
				p_connector=portal_conn,
				db_connector=db_conn,
				params=params,
				source=source
				)
			if is_spatial:
				if source['is_simple']:
					my_pub.define_spatial_source_layer(
						layer_name=source['table_name'])
				else:
					my_pub.define_source_from_query(
						sql_query=source['sql_query']
					)
			else:	
				if source['is_simple']:
					my_pub.define_simple_source(
						in_schema=source['schema_name'],
						in_recordset_name=source['table_name'])
				else: 
					my_pub.define_source_from_query(
						sql_query=source['sql_query']
					)
			my_pub.export()
			print("exported {}".format(title))

	except Exception as e:
		print('Error for layer {}'.format(title))
		print(e.args[0])
		raise

##############################################################################
#Example 1: export tables and/or view using define_simple_source
#  Use the config info in config\config.yml
##############################################################################
# for each yaml file in folder
run_files = os.listdir('./Config/run_files/')
root_dir = os.getcwd()
for f in run_files:
	os.chdir(root_dir)
	if r'Regional_Bike_and_Pedestrian_Facilities.yml' in f:
	# if f in ['cities_2018_land_use_forecast_dashboard.yml',
    #       'control_2018_land_use_forecast_dashboard.yml',
    #       'control_hct_2018_land_use_forecast_dashboard.yml',
	#if 'Income_Restricted_Housing_Database_2021' in f:
		f_path = './Config/run_files/' + f
		with open(f_path) as file:
			config = yaml.load(file, Loader=yaml.FullLoader)
			export(config)
