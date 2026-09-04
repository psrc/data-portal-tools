import yaml
from PortalExporter import PortalResource
from PortalConnector import PortalConnector
from DatabaseConnector import DatabaseConnector
import os


##############################################################################
# Setup: construct connector (for Examples 1 and 2)
##############################################################################
# enterprise_user = os.getenv("ENTERPRISE_PORTAL_ADVANCED_USERNAME")
# enterprise_pw = os.getenv("ENTERPRISE_PORTAL_ADVANCED_PW")
enterprise_client_id = os.getenv("ENTERPRISE_PORTAL_CLIENT_ID")
agol_user = os.getenv('AGOL_ADMIN_USERNAME')
agol_pw = os.getenv('AGOL_ADMIN_PW')
# with open(r'Config\\auth.yml') as file:
# 	auth = yaml.load(file, Loader=yaml.FullLoader)
portal_conn = PortalConnector(
	portal_username=agol_user,
	portal_pw=agol_pw
 )
enterprise_conn = PortalConnector(
	 portal_url='https://gis.psrc.org/portal',
	 client_id=enterprise_client_id,
	 profile='psrc_enterprise'
 )
# portal_conn = PortalConnector(
# 	portal_username=auth['enterprise']['username'],
# 	portal_pw=auth['enterprise']['pw'],
# 	portal_url='https://gis.psrc.org/portal'
#  )
elmer_conn = DatabaseConnector(
	db_server='SQLserver',
	database='Elmer')
elmergeo_conn = DatabaseConnector(
	db_server='SQLserver',
	database='ElmerGeo')

def export(config):
	try:

		for k in config.keys():
			params = config[k]['layer_params']
			title = params['title']
			source = config[k]['source']
			is_spatial = params['spatial_data']
			if is_spatial:
				db_conn = elmergeo_conn
			else:
				db_conn = elmer_conn
			my_pub = PortalResource(
				p_connector=portal_conn,
				enterprise_connector=enterprise_conn,
				db_connector=db_conn,
				params=params,
				source=source
				)
			if is_spatial:
				if not source['is_simple']:
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
	#if r'Regional_Growth_Centers' in f:
	if (f.lower() == 'weigh_stations.yml'):
		print(f"exporting {f}")
		f_path = './Config/run_files/' + f
		with open(f_path) as file:
			config = yaml.load(file, Loader=yaml.FullLoader)
			export(config)
print("completed export_runner.py")
