from PortalExporter import portal_spatial_resource
from PortalExporter import portal_connector
from Config import config

#example 3: export a spatial layer from ElmerGeo
spatial_conn = portal_connector(portal_username=config.arc_gis_online['username'],
	portal_pw=config.arc_gis_online['pw'],
	db_server='AWS-PROD-SQL\Sockeye',
	database='ElmerGeo')

my_pub = portal_spatial_resource(spatial_conn,
	title='test_spatial_layer2',
	tags='test')

my_pub.define_spatial_source_layer('rural')

my_pub.export()