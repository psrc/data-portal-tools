from PortalExporter import PortalResource
from PortalExporter import PortalSpatialResource
from PortalExporter import PortalConnector
from Config import config
import yaml


##############################################################################
# Setup: construct connector (for Examples 1 and 2)
##############################################################################
my_p_conn = PortalConnector(portal_username=config.arc_gis_online['username'],
	portal_pw=config.arc_gis_online['pw'],
	db_server='AWS-PROD-SQL\Sockeye',
	database='Elmer')


##############################################################################
#Example 1: export tables and/or view using define_simple_source
#  Use the config info in config\config.yml
##############################################################################
with open(r'Config\config.yml') as file:
	config = yaml.load(file, Loader=yaml.FullLoader)

layers = config.keys()

for l in layers:
	title = l
	params = config[l]['layer_params']
	source = config[l]['source']
	tags = params['tags']
	description = params['description']
	share_level = params['share_level']
	my_pub = PortalResource(my_p_conn,
		title=title,
		tags=tags,
		description=description,
		share_level=share_level
		)
	source = config[l]['source']
	schema = source['schema_name']
	table = source['table_name']
	my_pub.define_simple_source(
		in_schema=schema,
		in_recordset_name=table
		)
	my_pub.export();
	print("exported {}".format(title))