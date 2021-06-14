from PortalExporter import PortalResource
#from PortalExporter import PortalSpatialResource
from PortalExporter import PortalConnector
from PortalExporter import DatabaseConnector
import yaml
import os


##############################################################################
# Setup: construct connector (for Examples 1 and 2)
##############################################################################
with open(r'Config\\auth.yml') as file:
	auth = yaml.load(file, Loader=yaml.FullLoader)
my_p_conn = PortalConnector(
	portal_username=auth['arc_gis_online']['username'],
	portal_pw=auth['arc_gis_online']['pw'])
my_db_conn = DatabaseConnector(
	db_server='AWS-PROD-SQL\Sockeye',
	database='ElmerGeo')


def export(config):
	layers = config.keys()

	for l in layers:
		title = l
		params = config[l]['layer_params']
		source = config[l]['source']
		tags = params['tags']
		description = params['description']
		share_level = params['share_level']
		is_spatial = params['spatial_data']
		my_pub = PortalResource(
			p_connector=my_p_conn,
			db_connector=my_db_conn,
			params=params
			#title=title,
			# tags=tags,
			# description=description,
			# share_level=share_level,
			# allow_edits = params['allow_edits']
			)
		source = config[l]['source']
		schema = source['schema_name']
		table = source['table_name']
		if is_spatial:
			my_pub.define_spatial_source_layer(
				layer_name=table)
		else:	
			my_pub.define_simple_source(
				in_schema=schema,
				in_recordset_name=table)
		my_pub.export()
		#my_pub.print_df()
		print("exported {}".format(title))

##############################################################################
#Example 1: export tables and/or view using define_simple_source
#  Use the config info in config\config.yml
##############################################################################
# for each yaml file in folder
run_files = os.listdir('./Config/run_files/')
for f in run_files:
	f_path = './Config/run_files/' + f
	with open(f_path) as file:
		config = yaml.load(file, Loader=yaml.FullLoader)
		export(config)

#with open(r'Config\config_test.yml') as file:
#	config = yaml.load(file, Loader=yaml.FullLoader)
