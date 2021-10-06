import pandas as pd
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import urllib
import pyodbc
import zipfile
import glob
import yaml
import xmltodict
import os
import geopandas as gpd
import fiona
from shapely import wkt
from shapely.geometry.polygon import Polygon
import time
import json
import to_SpatiallyEnabledDataFrame
from pathlib import Path

class PortalConnector(object):
	def __init__(self, portal_username, portal_pw, portal_url="https://psregcncl.maps.arcgis.com"):
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
			self.portal_url = portal_url
			self.connect()
		except Exception as e:
			print(e.args[0])
			raise


	def connect(self):
		"""
		Make connections to the data portal
		"""
		try:
			self.gis = GIS(self.portal_url, self.username, self.pw)
		except Exception as e:
			print(e.args[0])
			raise

class DatabaseConnector(object):
	def __init__(self, db_server, database):
		"""
		Define the parameters by which the database_connector can connect a database.
		Parameters:
			db_server: PSRC's db server to export from
			database: PSRC's database to export from
		"""
		try:
			self.db_server = db_server
			self.database = database
			self.connect()
		except Exception as e:
			print(e.args[0])
			raise


	def connect(self):
		"""
		Make connections to the PSRC database
		"""
		try:
			conn_string = "DRIVER={{ODBC Driver 17 for SQL Server}}; " \
				"SERVER={}; DATABASE={}; trusted_connection=yes".format(
					self.db_server,
					self.database)
			self.sql_conn = pyodbc.connect(conn_string)
		except Exception as e:
			print(e.args[0])
			raise

class PortalResource(object):
	"""
	A publishable resource (e.g. CSV, Geodatabase layer)
	"""

	def __init__(self,
			p_connector,
			db_connector,
			params):
		"""
		Parameters:
			p_connector: a PortalConnector object
			db_connector: a DatabaseConnector object
			in_schema (string): the schema for the data set in the database.
			in_recordset_name (string): the name of the table or view
			title (string): the name to be used for the published dataset
			tags (string): a comma-delimited list of tags to be used for the published data source
		"""
		try:
			self.portal_connector = p_connector
			self.db_connector = db_connector
			self.resource_properties = {
				'title': params['title'],
				'tags': params['tags'],
				#'description': params['description'],
				'snippet': params['snippet'],
				'accessInformation': params['accessInformation'],
				'licenseInfo': params['licenseInfo']
			}
			self.metadata = params['metadata']
			self.title = params['title']
			self.working_folder = 'workspace'
			# self.contact_name = params['contact_name']
			# self.contact_email = params['contact_email']
			self.share_level = params['share_level']
			self.allow_edits = params['allow_edits']
			self.is_spatial = params['spatial_data']
			# self.organization_name = params['organization_name']
			# self.constraints = params['constraints']
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
			self.sql = 'SELECT {} FROM dbo.{}'.format(
				self.columns_clause,
				layer_name)

		except Exception as e:
			print(e.args[0])
			raise

	def close_holes(self, poly: Polygon) -> Polygon:
			"""
			Close polygon holes by limitation to the exterior ring.
			Args:
				poly: Input shapely Polygon
			Example:
				df.geometry.apply(lambda p: close_holes(p))
			"""
			try: 
				if poly.interiors:
					return Polygon(list(poly.exterior.coords))
				else:
					return poly

			except Exception as e:
				print(e.args[0])
				raise

	def add_to_zip(self, raw_file, zip_file, overwrite=False):
		try:
			if overwrite == True:
				with zipfile.ZipFile(zip_file, 'w') as myzip:
					myzip.write(raw_file)
			else: 
				with zipfile.ZipFile(zip_file, 'a') as myzip:
					myzip.write(raw_file)

		except Exception as e:
			print(e.args[0])
			raise


	def shape_to_zip(self, shape_name):
		"""
		Compress the constituent files within a shapefile into a zip file on disk.
		Parameter:
			shape_name: the name of the shapefile, without suffix
		"""
		try:
			zip_name = shape_name + '.zip'
			#get list of files > files
			files = glob.glob(shape_name + '*')
			f = files.pop()
			self.add_to_zip(f, zip_name, overwrite=True)
			for f in files:
				self.add_to_zip(f, zip_name)
			return zip_name

		except Exception as e:
			print(e.args[0])
			raise

	def simplify_gdf(self, gdf):
		try:
			geo_type = gdf.Shape_wkt.geom_type.unique()[0]
			if geo_type == 'Polygon':
				gdf = gdf.explode()
				gdf['Shape_wkt'] = gdf.geometry.apply(lambda p: self.close_holes(p))
			return gdf

		except Exception as e:
			print(e.args[0])
			raise

	def replublish_spatial(self):
		try:
			title = self.resource_properties['title']
			gis = self.portal_connector.gis
			portal_connector = self.portal_connector
			db_connector = self.db_connector
			df = pd.read_sql(sql=self.sql, con=self.db_connector.sql_conn)
			df['Shape_wkt'] = df['Shape_wkt'].apply(wkt.loads)
			gdf = gpd.GeoDataFrame(df, geometry='Shape_wkt')
			gdf = self.simplify_gdf(gdf)
			sdf = gdf.to_SpatiallyEnabledDataFrame(spatial_reference = 2285)
			working_dir = Path(self.working_folder)
			shape_name = '.\\' +  title + '.shp'
			if os.path.exists(working_dir): #clear the working directory
				files = glob.glob(str(working_dir / '*'))
				for f in files:
					os.remove(f)
			else:
				os.makedirs(working_dir)
			exported = self.search_by_title()
			os.chdir(self.working_folder)
			shapefile = sdf.spatial.to_featureclass(location=shape_name)
			if shapefile.endswith('.shp'):
				shapefile = shapefile[:-4]
			zipfile = self.shape_to_zip(shape_name = shapefile)
			exported.update(data=zipfile)
			published = exported.publish(overwrite=True)
			os.chdir('..')
			self.set_editability(published)
			print("{} exported to {}".format(shape_name, working_dir))

		except Exception as e:
			print(e.args[0])
			raise


	def publish_spatial_as_new(self):
		"""
		Export a resource from a geodatabase to a GeoJSON layer on the data portal.
		"""
		try:
			gis = self.portal_connector.gis
			db_connector = self.db_connector
			df = pd.read_sql(sql=self.sql, con=self.db_connector.sql_conn)
			df['Shape_wkt'] = df['Shape_wkt'].apply(wkt.loads)
			gdf = gpd.GeoDataFrame(df, geometry='Shape_wkt')
			gdf = self.simplify_gdf(gdf)
			sdf = gdf.to_SpatiallyEnabledDataFrame(spatial_reference = 2285)
			# layer = sdf.spatial.to_featurelayer(self.title,
			# 	gis=self.portal_connector.gis,
			# 	tags=self.resource_properties['tags'])
			fldr = Path(self.working_folder)
			fldr = Path('.')
			os.chdir(self.working_folder)
			ttl = self.title + '.shp'
			shape_file_name = fldr / ttl
			#shape_file_name = '.\cities_test.shp'
			shape_file_string = '.\\' + str(shape_file_name)
			shapefile = sdf.spatial.to_featureclass(shape_file_string)
			if shapefile.endswith('.shp'):
				shapefile = shapefile[:-4]
			zipfile = self.shape_to_zip(shape_name = shapefile)
			exported = gis.content.add(self.resource_properties, data=zipfile)
			#os.chdir('..')
			params = {"name":self.title}
			layer = exported.publish(publish_parameters=params)
			os.chdir('../')
			self.set_and_update_metadata(layer)
			self.set_editability(layer)
			layer_shared = layer.share(everyone=True)

		except Exception as e:
			print(e.args[0])
			raise

	def republish(self):
		try: 
			title = self.resource_properties['title']
			gis = self.portal_connector.gis
			out_type = "CSV"
			csv_name = r'.\temp_data_export_csv.csv'
			db_connector = self.db_connector
			df = pd.read_sql(
				sql=self.sql,
				con=db_connector.sql_conn)
			self.df = df
			working_dir = self.working_folder
			csv_name = working_dir + '\\' + self.resource_properties['title'] + '.csv'
			if not os.path.exists(working_dir):
				os.makedirs(working_dir)
			if os.path.isfile(csv_name):
				os.remove(csv_name)
			df.to_csv(csv_name)
			self.resource_properties['type'] = out_type
			exported = self.search_by_title()
			exported.update(data=csv_name)
			params = {"type":"csv","locationType":"none","name":self.title}
			published_csv = exported.publish(publish_parameters=params, overwrite=True)
			self.set_and_update_metadata(published_csv)
			self.set_editability(published_csv)
			self.share(published_csv)
			os.remove(csv_name)

		except Exception as e:
			print(e.args[0])
			if os.path.exists(csv_name): os.remove(csv_name)
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
			portal_connector = self.portal_connector
			db_connector = self.db_connector
			df = pd.read_sql(
				sql=self.sql,
				con=db_connector.sql_conn)
			self.df = df
			working_dir = self.working_folder
			csv_name = working_dir + '\\' + self.resource_properties['title'] + '.csv'
			if not os.path.exists(working_dir):
				os.makedirs(working_dir)
			if os.path.isfile(csv_name):
				os.remove(csv_name)
			df.to_csv(csv_name)
			self.resource_properties['type'] = out_type
			title = self.resource_properties['title']
			exported = portal_connector.gis.content.add(self.resource_properties, data=csv_name)
			params = {"name":title,"type":"csv","locationType":"none"}
			published_csv = exported.publish(publish_parameters=params)
			self.set_and_update_metadata(published_csv)
			self.set_editability(published_csv)
			self.share(published_csv)
			os.remove(csv_name)
		except Exception as e:
			print(e.args[0])
			if os.path.exists(csv_name): os.remove(csv_name)
			raise

	def update_xml_node(self, doc, tag_list, value):
		"""
		find a tag (defined by tag_list) in a parsed xml document,
		and update its value
		"""
		try:
			pass

		except Exception as e:
			print(e.args[0])
			raise

	def set_and_update_metadata(self, item):
		try:
			metadata_file = r'./workspace/metadata.xml'
			if not os.path.exists(metadata_file):
				self.initialize_metadata_file(item)
			metadata = item.metadata
			doc = xmltodict.parse(metadata)
			doc['metadata']['mdContact']['rpIndName'] = self.metadata['contact_name']

			dataIdInfo = doc['metadata']['dataIdInfo']
			dataIdInfo['idCitation']['resTitle'] = self.resource_properties['title']
			dataIdInfo['idCitation']['citRespParty']['rpIndName'] = self.metadata['contact_name']
			dataIdInfo['idCitation']['citRespParty']['rpOrgName'] = self.metadata['organization_name']
			dataIdInfo['idCitation']['date'] = {}
			dataIdInfo['idCitation']['date']['pubDate'] = self.metadata['date_last_updated']
			dataIdInfo['resConst'] = {'Consts':{'useLimit':None}}
			dataIdInfo['resConst']['Consts']['useLimit'] = self.metadata['constraints']

			doc['metadata']['dataIdInfo']['idCitation']['citRespParty']['rpCntInfo'] = {'cntAddress':{},'cntPhone':{},'cntOnlineRes':{}}
			rpCntInfo = doc['metadata']['dataIdInfo']['idCitation']['citRespParty']['rpCntInfo']
			rpCntInfo['cntAddress']['eMailAdd'] = self.metadata['contact_email']
			rpCntInfo['cntAddress']['delPoint'] = self.metadata['contact_street_address']
			rpCntInfo['cntAddress']['city'] = self.metadata['contact_city']
			rpCntInfo['cntAddress']['adminArea'] = self.metadata['contact_state']
			rpCntInfo['cntAddress']['postCode'] = self.metadata['contact_zip']
			rpCntInfo['cntPhone']['voiceNum'] = self.metadata['contact_phone']
			rpCntInfo['cntOnlineRes']['linkage'] = self.metadata['psrc_website']

			dataIdInfo['idAbs'] = self.metadata['description']
			dataIdInfo['idPurp'] = self.metadata['summary_purpose']
			dataIdInfo['idCredit'] = self.metadata['data_source']

			dataIdInfo['resConst'] = {'Consts':{}}
			dataIdInfo['resConst']['Consts']['useLimit'] = self.metadata['constraints']

			doc['metadata']['dqInfo'] = {'dataLineage':{}}
			doc['metadata']['dqInfo']['dataLineage']['statement'] = self.metadata['data_lineage']

			new_metadata = xmltodict.unparse(doc)
			textfile = open(metadata_file,'w')
			a = textfile.write(new_metadata)
			textfile.close()
			item.update(metadata=metadata_file)
			if os.path.exists(metadata_file): os.remove(metadata_file)

		except Exception as e:
			print(e.args[0])
			if os.path.exists(metadata_file): os.remove(metadata_file)
			raise

	def initialize_metadata_file(self, item):
		try:
			metadata_template = r'./metadata_template.xml'
			metadata_file = r'./workspace/metadata.xml'
			if not os.path.exists(r'./workspace'):
				os.mkdir(r'./workspace')
			with open(metadata_template) as f:
				content = f.read()
			file = open(metadata_file, 'w')
			a = file.write(content)
			file.close()
			item.update(metadata=metadata_file)

		except Exception as e:
			print(e.args[0])
			if os.path.exists(metadata_file): os.remove(metadata_file)
			raise

	def print_df(self):
		try:
			print("printing dataframe:")
			print(self.df)
			print("finished printing dataframe")
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


	def search_by_title(self):
		"""
		Search self.gis for layers with a given title (self.title),
		which is of the same type (Shapefile or tabular CSV) as self,
		and which is also owned by the current user. 
		Return the first layer that is an exact match.
		If no match is found, returns the string "no item"
		"""
		try:
			return_item = "no item"
			title = self.resource_properties['title']
			gis = self.portal_connector.gis
			layer_type_pred = '; type:Shapefile' if self.is_spatial else '; type:CSV'
			owner_clause = '; owner:{}'.format(gis.users.me.username)
			content_list = gis.content.search(
				query='title:{}{}{}'.format(title, layer_type_pred, owner_clause),
				)
			for item in content_list:
				if item['title'] == title:
					return_item = item
					break	
			return return_item

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
			found_item = self.search_by_title()
			if found_item != "no item":
				if self.is_spatial:
					self.replublish_spatial()
				else:
					self.republish()
			else: 
				if self.is_spatial:
					self.publish_spatial_as_new()
				else:
					self.publish_as_new()

		except Exception as e:
			print(e.args[0])
			raise

	def get_sql(self):
		return self.sql


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
			df = pd.read_sql(sql=col_sql, con=self.db_connector.sql_conn)
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




