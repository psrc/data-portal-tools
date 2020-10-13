from PortalExporter import PortalResource
from PortalExporter import PortalConnector
from Config import config

try:
	portal_conn = PortalConnector(portal_username=config.arc_gis_online['username'], portal_pw=config.arc_gis_online['pw'], db_server='AWS-PROD-SQL\Sockeye', database='Elmer')

	public_views = {'households':'v_households_2017_2019_public',
					'days':'v_days_2017_2019_public',
					'persons':'v_persons_2017_2019_public',
					'trips':'v_trips_2017_2019_public',
					'vehicles':'v_vehicles_2017_2019_public'}

	for k in public_views.keys():
		print('exporting {} now...'.format(k))
		title = 'hhsurvey_' + k + '_2019'
		view = public_views[k]
		tags = 'test,household survey,' + k
		pub = PortalResource(portal_conn, title=title, tags=tags)
		pub.define_simple_source(in_schema='HHSurvey', in_recordset_name=view)
		pub.export()
		print('...finished exporting {}'.format(k))

except Exception as e:
	print(e)