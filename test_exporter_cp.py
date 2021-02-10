from PortalExporter import PortalResource
from PortalExporter import PortalSpatialResource
from PortalExporter import PortalConnector
from Config import config

##############################################################################
# Setup: construct connector (for Examples 1 and 2)
##############################################################################
my_p_conn = PortalConnector(portal_username=config.arc_gis_online['username'],
	portal_pw=config.arc_gis_online['pw'],
	db_server='AWS-PROD-SQL\Sockeye',
	database='Elmer')


##############################################################################
#Example 1: export a table or view using define_simple_source
##############################################################################
my_pub = PortalResource(my_p_conn,
	title='cpeak_test_210209',
	tags='test2')
my_pub.define_simple_source(
	in_schema='parking_inventory',
	in_recordset_name='vintage_dim'
	)
my_pub.export();
print("exported cpeak_test_210209")
