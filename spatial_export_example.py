from PortalExporter import DatabaseConnector
import yaml

with open(r'Config\\auth.yml') as file:
	auth = yaml.load(file, Loader=yaml.FullLoader)
#example 3: export a spatial layer from ElmerGeo
spatial_conn = PortalConnector(
	portal_username=auth['arc_gis_online']['username'],
	portal_pw=auth['arc_gis_online']['pw'])


db_conn = DatabaseConnector(
	db_server='AWS-PROD-SQL\Sockeye',
	database='ElmerGeo')

my_pub = PortalResource(
	spatial_conn,
	db_conn,
	title='test_spatial_layer3',
	tags='test')

my_pub.define_spatial_source_layer('county_background')

my_pub.export()