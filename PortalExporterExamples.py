from PortalExporter import PortalResource
from PortalExporter import PortalSpatialResource
from PortalExporter import PortalConnector
from Config import config

##############################################################################
# Setup: construct connector (for Examples 1 and 2)
##############################################################################
my_p_conn = PortalConnector(portal_username=config.arc_gis_online['username'],
	portal_pw=config.arc_gis_online['pw'],
	db_server='SQLserver',
	database='Elmer')


##############################################################################
#Example 1: export a table or view using define_simple_source
##############################################################################
my_pub = PortalResource(my_p_conn,
	title='test_data_from_simple_source',
	tags='test')
my_pub.define_simple_source(
	in_schema='small_areas',
	in_recordset_name='sector_dim'
	)
my_pub.export();
print("exported test_data_from_simple_source")

##############################################################################
#Example 2: export data through an ad-hoc query:
##############################################################################
my_pub = PortalResource(my_p_conn,
	title='test_data_from_query',
	tags='test')

sql = """select top 10 ef.*
from census.estimate_facts as ef
	join census.variable_dim as vd on ef.variable_dim_id = vd.variable_dim_id
"""

my_pub.define_source_from_query(sql)
my_pub.export();
print("exported test_data_from_query")

##############################################################################
#example 3: export a spatial layer from ElmerGeo
##############################################################################
spatial_conn = PortalConnector(portal_username=config.arc_gis_online['username'],
	portal_pw=config.arc_gis_online['pw'],
	db_server='SQLserver',
	database='ElmerGeo')
my_pub = PortalSpatialResource(spatial_conn,
	title='test_spatial_layer',
	tags='test')
my_pub.define_spatial_source_layer('rural')
my_pub.export()
print("exported spatial layer")
