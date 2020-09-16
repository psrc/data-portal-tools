import pandas as pd
from arcgis.gis import GIS
import urllib
import pyodbc
import os
import geopandas as gpd
import fiona
from shapely import wkt

class portal_connector():
	def __init__(self, username, pw, db_server, database, portal_url="https://psregcncl.maps.arcgis.com"):
		"""
		Initialization method.
		Parameters:
			username: ArcGIS Online/Data Portal username
			pw: ArcGIS Online/Data Portal password
			db_server: PSRC's db server to export from
			database: PSRC's database to export from
			portal_url: An ArcGIS Online portal or Enterprise
		"""
		try:
			self.username = username
			self.pw = pw
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


class portal_resource():
	"""
	A publishable resource (e.g. CSV, Geodatabase layer)
	"""

	def __init__(self, p_connector, title, tags):
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
				'tags': tags
			}
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
			self.sql='select * from {}.{}'.format(in_schema, in_recordset_name),
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


	def define_source_from_sql(self, sql):
		"""
		Sets the data source as a user-defined SQL query
		"""
		try:
			self.sql=sql
		except Exception as e:
			print(e.args[0])
			raise


	def export(self):
		"""
		Read a recordset (a table or a view) in the database,
		write it to a CSV locally,
		then publish the CSV to the data portal.
		"""
		try:
			out_type = "CSV"
			csv_name = r'.\temp_data_export_csv.csv'
			connector = self.portal_connector
			in_schema = self.in_schema
			in_recordset_name = self.in_recordset_name
			df = pd.read_sql(
				sql=self.sql,
				con=connector.sql_conn)
			df.to_csv(csv_name)
			resource_properties['type'] = out_type
			exported = connector.gis.content.add(resource_properties, data=csv_name)
			published_csv = exported.publish()
			os.remove(csv_name)
		except Exception as e:
			print(e.args[0])
			os.remove(csv_name)
			raise


class portal_spatial_resource(portal_resource):

	def __init__(self, p_connector, title, tags):
		super().__init__(p_connector, title, tags)
		self.resource_properties['type'] = 'GeoJson'


	def define_spatial_source(self, layer_name, list_of_col_names):
		try:
			l = list_of_col_names
			l.append('Shape') if 'Shape' not in l else l
			l = ['Shape.STAsText() as Shape_wkt' if x=='Shape' else x for x in l]
			columns_clause = ','.join(l)
			self.sql = 'SELECT {} FROM dbo.{}_evw'.format(
				columns_clause,
				layer_name)

		except Exception as e:
			print(e.args[0])
			raise

	def export(self):
		try:
			df = pd.read_sql(sql=self.sql, con=self.portal_connector.sql_conn)
			df['Shape_wkt'] = df['Shape_wkt'].apply(wkt.loads)
			gdf = gpd.GeoDataFrame(df, geometry='Shape_wkt')
			gdf.crs = 'EPSG:2285'
			file_name = 'working\\' + self.resource_properties['title'] + '.json'
			#MOREMORE check for file existence before executing this next line:
			if not os.path.exists('working'):
				os.makedirs('working')
			gdf.to_file(file_name, driver='GeoJSON')
			connector = self.portal_connector
			exported = connector.gis.content.add(
				self.resource_properties,
				data = file_name)
			published_shape = exported.publish()
			os.remove(file_name)

		except Exception as e:
			print(e.args[0])
			raise

