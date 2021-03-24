import pandas as pd
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import urllib
import pyodbc
import yaml
import os
import geopandas as gpd
import fiona
from shapely import wkt
import time
import json
import to_SpatiallyEnabledDataFrame

class PortalConnector(object):
	def __init__(self, portal_username, portal_pw, db_server, database, portal_url="https://psregcncl.maps.arcgis.com"):
		"""
		Define the parameters by which the portal_connector can connect a database to a data portal.
		Parameters:
			username: ArcGIS Online/Data Portal username
			pw: ArcGIS Online/Data Portal password
			db_server: PSRC's db server to export from
			database: PSRC's database to export from
			portal_url: An ArcGIS Online portal or Enterprise
		"""
		try:
			self.username = portal_username
			self.pw = portal_pw
			self.db_server = db_server
			self.database = database
			self.portal_url = portal_url
			self.connect()
		except Exception as e:
			print(e.args[0])
			raise


	def connect(self):
		"""
		Make connections to the PSRC database and the data portal
		"""
		try:
			conn_string = "DRIVER={{ODBC Driver 17 for SQL Server}}; " \
				"SERVER={}; DATABASE={}; trusted_connection=yes".format(
					self.db_server,
					self.database)
			self.sql_conn = pyodbc.connect(conn_string)
			self.gis = GIS(self.portal_url, self.username, self.pw)
		except Exception as e:
			print(e.args[0])
			raise


class PortalResource(object):
	"""
	A publishable resource (e.g. CSV, Geodatabase layer)
	"""

	def __init__(self,
			p_connector,
			title,
			tags,
			description='',
			share_level='everyone',
			allow_edits=False):
		"""
		Parameters:
			p_connector: a portal_connector object
			in_schema (string): the schema for the data set in the database.
			in_recordset_name (string): the name of the table or view
			title (string): the name to be used for the published dataset
			tags (string): a comma-delimited list of tags to be used for the published data source
		"""
		try:
			self.portal_connector = p_connector
			self.resource_properties = {
				'title': title,
				'tags': tags,
				'description': description
			}
			self.share_level = share_level
			self.allow_edits = allow_edits
		except Exception as e:
			print(e.args[0])
			raise


	def define_simple_source(self, in_schema, in_recordset_name):
		"""
		Sets the data source table or view in the PSRC database.
		Includes all rows and all columns in the set.
		Requires no knowlege of SQL on the user's part.
		"""
		try:
			self.sql='select * from {}.{}'.format(in_schema, in_recordset_name)
		except Exception as e:
			print(e.args[0])
			raise


	def define_source_from_query(self, sql_query):
		"""
		Sets the data source table or view in the PSRC database.
		Includes all rows and all columns in the set.
		Requires no knowlege of SQL on the user's part.
		"""
		try:
			self.sql = sql_query

		except Exception as e:
			print(e.args[0])
			raise


	def publish_as_new(self):
		"""
		Read a recordset (a table or a view) in the database,
		write it to a CSV locally,
		then publish the CSV to the data portal.
		"""
		try:
			out_type = "CSV"
			csv_name = r'.\temp_data_export_csv.csv'
			connector = self.portal_connector
			df = pd.read_sql(
				sql=self.sql,
				con=connector.sql_conn)
			working_dir = 'working'
			csv_name = working_dir + '\\' + self.resource_properties['title'] + '.csv'
			if not os.path.exists(working_dir):
				os.makedirs(working_dir)
			if os.path.isfile(csv_name):
				os.remove(csv_name)
			df.to_csv(csv_name)
			self.resource_properties['type'] = out_type
			exported = connector.gis.content.add(self.resource_properties, data=csv_name)
			published_csv = exported.publish()
			self.set_editability(published_csv)
			self.share(published_csv)
			print('title: {}'.format(exported.title))
			os.remove(csv_name)
		except Exception as e:
			print(e.args[0])
			if os.path.exists(csv_name): os.remove(csv_name)
			raise

	def set_editability(self, layer):
		'''
		Disallow edits if self.allow_edits is set to False
		'''
		try:
			if self.allow_edits == False:
				capabilities_dict = {'capabilities':'Query', 'syncEnabled': False}
				published_flc = FeatureLayerCollection.fromitem(layer)
				published_flc.manager.update_definition(capabilities_dict)
			elif self.allow_edits == True:
				capabilities_dict = {'capabilities':'Create,Delete,Query,Update,Editing',
									'syncEnabled': False}
				published_flc = FeatureLayerCollection.fromitem(layer)
				published_flc.manager.update_definition(capabilities_dict)
		except Exception as e:
			print(e.args[0])
			raise


	def share(self, layer):
		try:
			sl = self.share_level
			if sl == 'everyone':
				layer.share(everyone=True)
			elif sl == 'org':
				layer.share(everyone=False, org=True)
		except Exception as e:
			print(e.args[0])
			raise

	def export(self):
		"""
		check if self is already published on the data portal.
		  If yes then delete resource, then publish as new
		  If no then publish as new
		"""
		try:
			title = self.resource_properties['title']
			gis = self.portal_connector.gis
			content_list = gis.content.search(query='title:{}'.format(title))
			if len(content_list) > 0:
				#delete title?
				for item in content_list:
					i_deleted = gis.content.get(item.id).delete()
			self.publish_as_new()

		except Exception as e:
			print(e.args[0])
			raise


class PortalSpatialResource(PortalResource):

	def __init__(self, p_connector, title, tags):
		super().__init__(p_connector, title, tags)
		# self.resource_properties['type'] = 'GeoJson'
		self.title = title
		self.tags = tags


	def define_spatial_source_layer(self, layer_name):
		"""
		Produce a SQL query for a layer's versioned view in the geodatabase
		Parameters:
			layer_name: the name of the layer in the geodatabase (without an *_evw suffix)
		Output:
			self.sql: a SQL string that can be used to build a geodataframe
		"""
		try:
			self.column_list = self.get_columns_for_recordset(layer_name)
			self.get_columns_clause()
			self.sql = 'SELECT {} FROM dbo.{}_evw'.format(
				self.columns_clause,
				layer_name)

		except Exception as e:
			print(e.args[0])
			raise

	def publish_as_new(self):
		"""
		Export a resource from a geodatabase to a GeoJSON layer on the data portal.
		"""
		try:
			connector = self.portal_connector
			df = pd.read_sql(sql=self.sql, con=self.portal_connector.sql_conn)
			df['Shape_wkt'] = df['Shape_wkt'].apply(wkt.loads)
			gdf = gpd.GeoDataFrame(df, geometry='Shape_wkt')
			sdf = gdf.to_SpatiallyEnabledDataFrame(spatial_reference = 2285)
			layer = sdf.spatial.to_featurelayer(self.title,
				gis=self.portal_connector.gis,
				tags=self.tags)
			layer_shared = layer.share(everyone=True)

		except Exception as e:
			print(e.args[0])
			raise


	def get_columns_for_recordset(self, layer_name):
		"""
		Get a list of columns for a table or view in a database,
		minus the system columns GDB_GEOMATTR_DATA and SDE_STATE_ID, if they exists.
		Parameters:
			layer_name: the name of a table or view in a database
		Returns a list of strings representing column names.
		"""
		try:
			col_sql = "SELECT COLUMN_NAME FROM {} WHERE TABLE_NAME = '{}'".format(
				'INFORMATION_SCHEMA.COLUMNS',
				layer_name)
			df = pd.read_sql(sql=col_sql, con=self.portal_connector.sql_conn)
			l = []
			for n in df.COLUMN_NAME:
				l.append(n) if n not in ['GDB_GEOMATTR_DATA', 'SDE_STATE_ID'] else l
			return l

		except Exception as e:
			print(e.args[0])
			raise


	def get_columns_clause(self):
		"""
		Constructs a string representing column names, which can be inserted into
		a SQL query.
		Column "Shape" gets wrapped in a function to produce its wlt representation.
		Depends on the existence of self.column_list, a list of strings representing column names.
		Produces self.columns_clause, which can be used in a SQL query.
		"""
		try:
			l = self.column_list
			l = ['Shape.STAsText() as Shape_wkt' if x=='Shape' else x for x in l]
			self.columns_clause = ','.join(l)

		except Exception as e:
			print(e.args[0])
			raise
