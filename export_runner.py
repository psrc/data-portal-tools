from PortalExporter import PortalResource
from PortalExporter import PortalSpatialResource
from PortalExporter import PortalConnector
from PortalExporter import DatabaseConnector
import yaml


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
	database='Elmer')


##############################################################################
#Example 1: export tables and/or view using define_simple_source
#  Use the config info in config\config.yml
##############################################################################
with open(r'Config\config_test.yml') as file:
	config = yaml.load(file, Loader=yaml.FullLoader)

layers = config.keys()

for l in layers:
	params = config[l]['layer_params']
	source = config[l]['source']
	simple_source = source['is_simple']
	spatial_data = params['spatial_data']
	if spatial_data:
		portal_resource = PortalSpatialResource(
			p_connector=my_p_conn,
			db_connector=my_db_conn,
			params = params
			)
	else:
		portal_resource = PortalResource(
			p_connector=my_p_conn,
			db_connector=my_db_conn,
			params= params
			)
		if simple_source:
			portal_resource.define_simple_source(
				in_schema=source['schema_name'],
				in_recordset_name=source['table_name']
				)
		else:
			portal_resource.define_source_from_query(source['sql_query'])

	portal_resource.export()
	#portal_resource.print_df()
	print("exported {}".format(params['title']))
