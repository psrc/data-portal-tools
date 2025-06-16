#from matplotlib import rc_file
from numpy import NaN
import pandas as pd
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection, GeoAccessor, GeoSeriesAccessor
from arcgis.gis._impl._content_manager import SharingLevel
import urllib
import pyodbc
import sqlalchemy
import zipfile
import glob
import yaml
import os
import re
from shapely import wkt
from shapely.geometry.polygon import Polygon
import time
import json
import to_SpatiallyEnabledDataFrame
from pathlib import Path
import geopandas as gpd
#import fiona
import xml.etree.ElementTree as ET
import arcpy
import shutil


class PortalResource(object):
	"""
	A publishable resource (e.g. CSV, Geodatabase layer)
	"""

	def __init__(self,
			p_connector,
			db_connector,
			params,
			source):
		"""
		Initiate a new PortalResource object.
		Parameters:
			p_connector: a PortalConnector object
			db_connector: a DatabaseConnector object
			in_schema (string): the schema for the data set in the database.
			in_recordset_name (string): the name of the table or view
			title (string): the name to be used for the published dataset
			tags (string): a comma-delimited list of tags to be used for the published data source
			source (yaml): a yaml object defining the layer name or sql definition
		"""
		try:
			self.portal_connector = p_connector
			self.db_connector = db_connector
			self.params = params
			if 'groups' in params:
				self.params['groups'] = params['groups'].split(';')
			else:
				self.params['groups'] = []
			self.metadata = params['metadata']
			tag_string = params['tags']
			tag_string = tag_string[:-1] if tag_string[-1] in [',',';'] else tag_string		
			tag_list = re.split('[,;]', tag_string)
			self.resource_properties = {
				'title': params['title'],
				'tags': tag_list,
				#'description': params['description'],
				'snippet': params['snippet'],
				#'accessInformation': self.metadata['description'],
				'licenseInfo': params['licenseInfo']
			}
			self.title = params['title']
			self.working_folder = 'workspace'
			self.sde_folder = 'sde'
			self.sde_name = 'elmergeo.sde'
			self.sde_instance = 'SQLserver'
			self.sde_database = 'ElmerGeo'
			# self.contact_name = params['contact_name']
			# self.contact_email = params['contact_email']
			self.share_level = params['share_level']
			self.allow_edits = params['allow_edits']
			self.is_spatial = params['spatial_data']
			if 'params' not in params.keys():
				self.srid = {'wkid':2285}
			else:
				self.srid = {'wkid':int(params['srid'])}
			self.source = source
			if 'fields_to_exclude' in self.source:
				self.source['fields_to_exclude'] = source['fields_to_exclude'].split(',')
			else:
				self.source['fields_to_exclude'] = []
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
		"""
  		Add a file to a ZIP archive file.  
    	
     	Inputs:
      		raw_file: (string): the name of the file to be added to the archive.
        	zip_file: (string): the file name of the ZIP archive 
         	overwrite: (True/False): a TRUE value overwrites any currently-existing
          				contents of the ZIP file, while a FALSE value appends to it.
            """
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


	def gdb_to_zip(self, file_gdb_name):
		"""
		Create a local zip file from a file geodatabase.
		
  		input:
    		file_gdb_name: a Path object for the file geodtabase to be zipped.
		
		Returns the name of the new zip file.
		"""
		try:
			if '.gdb' in str(file_gdb_name):
				zip_name = file_gdb_name.stem
				folder_to_be_zipped = str(file_gdb_name.parents[0])
			else:
				zip_name = file_gdb_name + '.zip'
				folder_to_be_zipped = str(file_gdb_name)

			out_zip_name = shutil.make_archive(zip_name, 'zip', folder_to_be_zipped)
			return out_zip_name

		except Exception as e:
			print(e.args[0])
			raise


	def simplify_gdf(self, gdf):
		"""
  		Given a polygon geodataframe, fill in any holes in polygons.
		Polygon holes can represent features such as lakes, but can cause 
		strange triangle-shaped artifacts in geodataframes.  

		input:
			gdf: a geodataframe object

		Returns a geodataframe
    	"""
		try:
			geo_type = gdf.Shape_wkt.geom_type.unique()[0]
			if geo_type == 'Polygon':
				gdf = gdf.explode()
				gdf['Shape_wkt'] = gdf.geometry.apply(lambda p: self.close_holes(p))
			return gdf

		except Exception as e:
			print(e.args[0])
			raise


	def shorten_column_names(self, gdf):
		''' 
		Create a dictionary of column names, with the keys being a short abstracted reference to the full-length col names.
		Set this dictionary as self.column_dict
		Resets gdf.columns to the list of new abstracted columns names ['col1', 'col2'...] 
		'''
		try:
			col_list = gdf.columns.to_list()
			i = 0
			new_col_list = []
			d = {}
			for c in col_list:
				new_col = 'col' + str(i)
				if c != 'Shape_wkt':
					d[new_col] = c
					new_col_list.append(new_col)
				else:
					d[c] = c 
					new_col_list.append(c)
				i+=1
			self.column_dict = d
			self.long_col_names = col_list
			gdf.columns = new_col_list
			return gdf

		except Exception as e:
			print(e.args[0])
			raise


	def prepare_working_dir(self, dir_path):
		"""
		remove layers in a geodatabase at dir_path (it if exists,
		then create a nested directory dir_path/gdb
		"""
		try:
			gdb_filename = self.title + '.gdb'
			# gdb_path = dir_path / 'gdb.gdb'
			gdb_path = dir_path / gdb_filename
			if os.path.exists(dir_path):
				files = glob.glob(str(dir_path / '*'))
				for f in files:
					if '.gdb' in f:
						shutil.rmtree(f)
					elif f != str(gdb_path) and f != 'workspace\\metadata':
						os.remove(f)
				gdb_files = glob.glob(str(gdb_path / '*.gdb'))
				for f in gdb_files:
					shutil.rmtree(f)
			else: 
				os.makedirs(dir_path)
			os.makedirs(gdb_path)
			return gdb_path

		except Exception as e:
			print("error in prepare_working_dir.  dir_path={}".format(dir_path))
			print(e.args[0])
			raise


	def export_remote_featureclass(self, 
					out_gdb, 
					out_fc_name,
					fields_to_exclude=[]
			):
		'''
		Creates a local copy of a feature class in a geodatabase.
		params:
			remote_fc: String. The name of a featureclass in a remote geodatbase
			out_gdb: Path() object. References a file geodatabase
			out_fc_name: String.  The name of the layer to be exported to out_gdb
			fields_to_exclude: a list of field names to exlude from out_fc_name
		'''
		try:
			# conn_path = self.db_connector.gdb_sde_conn
			conn_path = self.sde_path
			#conn_path = os.path.join(os.getcwd(), out_gdb)
			arcpy.env.overwriteOutput = True
			arcpy.env.workspace = conn_path
			out_fc_path = str(out_gdb / out_fc_name)
			featureclass_base = self.source['table_name']
			temp_fc = featureclass_base + "_temp"
			remote_fc = "{}/{}".format(self.source['feature_dataset'], featureclass_base)
			arcpy.MakeFeatureLayer_management(remote_fc, temp_fc)
			fields = arcpy.Describe(temp_fc).fieldInfo
			for i in range(fields.count):
				field_name = fields.getFieldName(i)
				if field_name in fields_to_exclude:
					fields.setVisible(i, 'HIDDEN')
			temp_fc2 = temp_fc + '2'
			arcpy.MakeFeatureLayer_management(temp_fc, 
											temp_fc2, 
											field_info=fields)
			arcpy.management.CopyFeatures(temp_fc2, out_fc_path)
			arcpy.Delete_management(temp_fc2)
			arcpy.ClearWorkspaceCache_management()
			arcpy.env.workspace = None

		except Exception as e:
			print("error in export_remote_featureclass")
			print(e.args[0])
			raise


	def get_group_ids(self):
		"""
		Returns a list of ID's of any groups in self.gis
		that are included in self.params['groups'].
		"""

		try:
			gis = self.portal_connector.gis
			groups = self.params['groups']
			group_ids = []
			for grp in gis.groups.search(query=""):
				if grp.title in groups:
					group_ids.append(grp.id)
			return group_ids

		except Exception as e:
			print("error in get_group_ids")
			print(e.args[0])
			raise


	def _prepare_spatial_data(self, gdb_path):
		"""
		Helper method to prepare spatial data for publishing.
		Returns the path to the created zip file.
		"""
		try:
			title = self.resource_properties['title']
			
			if self.source['is_simple']:
				table_name = self.source['table_name']
				self.remote_fc_def = "{}/{}".format(self.source['feature_dataset'], table_name)
				fields_to_exclude = self.source['fields_to_exclude']
				self.export_remote_featureclass(gdb_path, title, fields_to_exclude)
			else:
				os.chdir(self.working_folder)
				df = pd.read_sql(sql=self.sql, con=self.db_connector.sql_conn)
				df['Shape_wkt'] = df['Shape_wkt'].apply(wkt.loads)
				gdf = gpd.GeoDataFrame(df, geometry='Shape_wkt')
				gdf = self.simplify_gdf(gdf)
				sdf = gdf.to_SpatiallyEnabledDataFrame(spatial_reference = 2285)
				feat_class_name = gdb_path / title
				out_feature_class = sdf.spatial.to_featureclass(location=feat_class_name)
				os.chdir('../')
			
			return self.gdb_to_zip(gdb_path)
		except Exception as e:
			print(e.args[0])
			raise

	def _prepare_tabular_data(self):
		"""
		Helper method to prepare tabular data for publishing.
		Returns the dataframe and CSV file path.
		"""
		try:
			db_connector = self.db_connector
			df = pd.read_sql(sql=self.sql, con=db_connector.sql_conn)
			self.df = df
			
			working_dir = Path(self.working_folder)
			filename = self.resource_properties['title'] + '.csv'
			csv_name = working_dir / filename
			
			if not os.path.exists(working_dir):
				os.makedirs(working_dir)
			if os.path.isfile(csv_name):
				os.remove(csv_name)
			
			df.to_csv(csv_name)
			return df, csv_name
		except Exception as e:
			print(e.args[0])
			raise

	def _setup_spatial_environment(self):
		"""
		Helper method to set up the spatial publishing environment.
		Returns the geodatabase path.
		"""
		try:
			fldr = Path(self.working_folder)
			gdb_path = self.prepare_working_dir(fldr)
			self.make_file_gdb(gdb_path)
			self.set_up_sde()
			return gdb_path
		except Exception as e:
			print(e.args[0])
			raise

	def _finalize_spatial_publishing(self, published_item, is_new=False):
		"""
		Helper method to finalize spatial item publishing with metadata and sharing.
		"""
		try:
			self.set_and_update_metadata(published_item)
			# if is_new:
			self.set_editability(published_item)
			share_group_ids = self.get_group_ids()
			if self.share_level == 'everyone':
				layer_shared = published_item.share(everyone=True, groups=share_group_ids)
			elif self.share_level == 'org':
				layer_shared = published_item.share(org=True, groups=share_group_ids)
			else:
				layer_shared = published_item.share(everyone=False, groups=share_group_ids)
		except Exception as e:
			print(e.args[0])
			raise

	def _finalize_tabular_publishing(self, published_item):
		"""
		Helper method to finalize tabular item publishing with metadata and sharing.
		"""
		try:
			self.set_and_update_metadata(published_item)
			self.share(published_item)
		except Exception as e:
			print(e.args[0])
			raise

	def republish_spatial(self):
		"""
  		Copy a spatial layer from ElmerGeo into a local file geodatabase,
    		then zip up that gdb, identify an existing layer on ArcOnline,
			and overwrite that layer with the zipped gdb.  
			Lastly, publish the updated layer.
      	"""
		try:
			gdb_path = self._setup_spatial_environment()
			zipfile = self._prepare_spatial_data(gdb_path)
			
			exported = self.search_by_title()
			exported.update(data=zipfile, item_properties=self.resource_properties)
			params = {"name": self.title, 'targetSR': self.srid}
			published = exported.publish(publish_parameters=params, overwrite=True)
			
			self._finalize_spatial_publishing(published, is_new=False)

		except Exception as e:
			print(e.args[0])
			raise


	def make_file_gdb(self, gdb_path):
		"""
  		Creates a new empty local file geodatabase.
    
    	Input:  gdb_path.  The directory and file location for the geodatabase.
     	"""
		try:
			if os.path.exists(gdb_path):
				shutil.rmtree(gdb_path)
			arcpy.management.CreateFileGDB(str(gdb_path.parent), gdb_path.stem)

		except Exception as e:
			print("error in make_file_gdb.  out_folder_path={},  gdb_path={}".format(str(gdb_path.parent), str(gdb_path)))
			print(e.args[0])
			raise
	
 
	def set_up_sde(self):
		"""
  		Creates an SDE file, i.e., a connection to a Geodatabase on SQL Server
    	"""
		try:
			sde_dir_name = './' + self.sde_folder
			sde_full_name = str(Path(sde_dir_name) / self.sde_name)
			if not os.path.exists(sde_full_name):
				arcpy.management.CreateDatabaseConnection(sde_dir_name, 
												self.sde_name, 
												'SQL_SERVER',
												self.sde_instance,
												account_authentication='OPERATING_SYSTEM_AUTH',
												database=self.sde_database
				)
			return_path = str(Path(sde_dir_name) / self.sde_name) 
			self.sde_path = return_path

		except Exception as e:
			print("error in set_up_sde.")
			print(e.args[0])
			raise


	def publish_spatial_as_new(self):
		"""
		Export a resource from a ElmerGeo to a new File Geodatabase layer on Arc Online.
			Then, publishes that layer as a new Portal layer.
		"""
		try:
			gis = self.portal_connector.gis
			gdb_path = self._setup_spatial_environment()
			zipfile = self._prepare_spatial_data(gdb_path)
			
			res_properties = self.resource_properties.copy()
			res_properties['type'] = 'File Geodatabase'
			exported = gis.content.add(res_properties, data=zipfile)
			params = {"name": self.title, 'targetSR': self.srid}
			layer = exported.publish(publish_parameters=params)
			
			self._finalize_spatial_publishing(layer, is_new=True)

		except Exception as e:
			print(e.args[0])
			raise

	def build_fields_json(self, df):
		"""
		Return a dictionary of field names and data types in a data frame,
			with the data types in ESRI-friendly form.
  		"""
		try:
			dtypes = zip(df.columns, df.dtypes)
			type_translations = {"int64": "esriFieldTypeInteger", 
								"object": "esriFieldTypeString", 
								"float64": "esriFieldTypeDouble"}
			fields = []
			for f in dtypes:
				pd_type = str(f[1])
				col_name = f[0]
				if col_name in ['data_vintage', 'year_built']:
					type_dict = {"name": col_name, "type": "esriFieldTypeString"}
				else:
					type_dict = {"name": col_name, "type": type_translations[pd_type]}
				fields.append(type_dict)
			return(fields)

		except Exception as e:
			print(e.args[0])
			raise

	def republish(self):
		"""
  		Create a tabular CSV data set on ArcOnline, 
    	and publish it as a table on Portal.
		Both these actions overwrite pre-existing objects.
		"""
		try: 
			df, csv_name = self._prepare_tabular_data()
			
			self.resource_properties['type'] = "CSV"
			exported = self.search_by_title()
			exported.update(data=str(csv_name), item_properties=self.resource_properties)
			
			field_mappings = self.build_fields_json(df)
			params = {
				"type": "csv",
				"locationType": "none",
				"name": self.title,
				"layerInfo": {"fields": field_mappings}
			}
			published_csv = exported.publish(publish_parameters=params, overwrite=True)
			
			self._finalize_tabular_publishing(published_csv)

		except Exception as e:
			print(e.args[0])
			if 'csv_name' in locals() and os.path.exists(csv_name): 
				os.remove(csv_name)
			raise


	def publish_as_new(self):
		"""
		Read a recordset (a table or a view) in the database,
		write it to a CSV locally,
		then publish the CSV to the data portal.
		"""
		try:
			working_dir = Path(self.working_folder)
			self.prepare_working_dir(working_dir)
			df, csv_name = self._prepare_tabular_data()
			
			self.resource_properties['type'] = "CSV"
			exported = self.portal_connector.gis.content.add(self.resource_properties, data=str(csv_name))
			
			field_mappings = self.build_fields_json(df)
			params = {
				"name":self.resource_properties['title'],
				"type":"csv",
				"locationType":"none",
				"layerInfo": {"fields": field_mappings}
			}
			published_csv = exported.publish(publish_parameters=params)
			
			self._finalize_tabular_publishing(published_csv)

		except Exception as e:
			print(e.args[0])
			if 'csv_name' in locals() and os.path.exists(csv_name): 
				os.remove(csv_name)
			raise


	def upsert_element(self, existing_element, new_element_tag, new_element_text = ''):
		"""
  		Looks within existing_element (in an XML document) for an element (new_element_tag).
		If found, it updates its text value according to new_element_text.
		If not found, it adds it as a subElement and update its text according to new_element_text.
		Returns the new elmement.

		Parameters:
			existing_element: The XML element to search through
			new_element_tag: The element tag to look for
			new_element_text: The string to set the new element's text property to.
  		"""
		try:
			sub_el = existing_element.find(new_element_tag)
			if sub_el is None:
				new_element = ET.SubElement(existing_element, new_element_tag)
			else:
				new_element = existing_element.find(new_element_tag)
			if new_element_text is not None and  new_element_text > '':
				new_element.text = new_element_text
			return new_element

		except Exception as e:
			print("error in upsert_element.  existing_element = {}, new_element_tag = {}".format(
				existing_element, 
				new_element_tag))
			print(e.args[0])
			raise


	def clean_metadata_string(self, str):
		"""
		Clean a string of any N/A's or None (NULL) values
		  and wrap any HTTP links in <a> tags
		
		Parameter:
			str: a string to be cleaned
   
		Returns a string
		"""
		try:
			out_str = '' if str == 'N/A' else str
			out_str = '' if str == 'nan' else str
			out_str = '' if out_str is None else out_str
			# url_pattern regex cribbed from guillaumepiot's gist at https://gist.github.com/guillaumepiot/4539986
			url_pattern =  re.compile(r"(?i)((https?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]+[^\.\s])", re.MULTILINE|re.UNICODE)
			out_str = url_pattern.sub(r'<a href="\1" target="_blank">\1</a>', out_str)
			mailto_pattern = re.compile(r"([\w\-\.]+@(\w[\w\-]+\.)+[\w\-]+)", re.MULTILINE|re.UNICODE)
			out_str = mailto_pattern.sub(r'<a href="mailto:\1">\1</a>', out_str)
			return out_str

		except Exception as e:
			print("error in clean_metadata_string")
			print(e.args[0])
			raise


	def set_and_update_metadata(self, item):
		"""
		Update the metadata for a published item in ArcOnline
  
		parameter:
			item: the published item in ArcOnline.
    	"""
		try:
			metadata_file = r'./workspace/metadata.xml'
			#if not os.path.exists(metadata_file):
			self.initialize_metadata_file(item)
			tree = ET.parse(metadata_file)
			root = tree.getroot()
			mdContact = root.find('mdContact')
			dataIdInfo = root.find('./dataIdInfo')
			# citRespParty = root.find('./dataIdInfo/idCitation/citRespParty')
			idCitation = self.upsert_element(dataIdInfo, 'idCitation')
			citRespParty = self.upsert_element(idCitation, 'citRespParty')
			rpIndName = ET.SubElement(citRespParty, 'rpIndName')
			rpIndName.text = self.metadata['contact_name']
			rpOrgName = ET.SubElement(citRespParty, 'rpOrgName')
			#rpOrgName.text = self.metadata['organization_name']
			rpOrgName.text = 'Puget Sound Regional Council'
			role = ET.SubElement(citRespParty, 'role')
			RoleCd = ET.SubElement(role, 'RoleCd')
			RoleCd.set('value', '006')

			#contact info
			contact_rpIndName = self.upsert_element(mdContact, 'rpIndName')
			contact_rpIndName.text = self.metadata['contact_name']
			rpOrgName = self.upsert_element(mdContact, 'rpOrgName')
			rpOrgName.text = self.metadata['organization_name']
			rpCntInfo = self.upsert_element(mdContact, 'rpCntInfo')
			cntAddress = self.upsert_element(rpCntInfo, 'cntAddress')
			eMailAdd = self.upsert_element(cntAddress, 'eMailAdd')
			eMailAdd.text = self.metadata['contact_email']
			city = self.upsert_element(cntAddress, 'city')
			city.text = 'Seattle'
			postCode = self.upsert_element(cntAddress, 'postCode')
			postCode.text = '98104'
			cntPhone = self.upsert_element(rpCntInfo, 'cntPhone')
			voiceNum = self.upsert_element(cntPhone, 'voiceNum')
			voiceNum.text = self.metadata['contact_phone']


			for n in idCitation.findall('citOnlineRes'):
				idCitation.remove(n)
			citOnlineRes = self.upsert_element(idCitation, 'citOnlineRes')
			linkage = self.upsert_element(citOnlineRes, 'linkage', self.metadata['psrc_website'])
			orName = self.upsert_element(citOnlineRes, 'orName', 'Data on PSRC Webpage')

			time_period_text = "time period: {}".format(self.metadata['time_period'])
			other_details = self.upsert_element(idCitation, 'otherCitDet', time_period_text)

			resMaint = self.upsert_element(dataIdInfo, 'resMaint')
			usrDefFreq = self.upsert_element(resMaint, 'usrDefFreq')
			duration = self.upsert_element(usrDefFreq, 'duration', self.metadata['update_cadence'])

			root.find('./dataIdInfo/idCitation/resTitle').text = self.resource_properties['title']
			date = self.upsert_element(idCitation, 'date')
			pubDate = self.upsert_element(date, 'pubDate', self.metadata['date_last_updated'])

			for n in dataIdInfo.findall('resConst'):
				dataIdInfo.remove(n)
			resConst = ET.SubElement(dataIdInfo, 'resConst')
			consts = ET.SubElement(resConst, 'Consts')

			rpCntInfo = ET.SubElement(citRespParty, 'rpCntInfo')
			cntAddress = ET.SubElement(rpCntInfo, 'cntAddress')
			cntPhone = ET.SubElement(rpCntInfo, 'cntPhone')
			cntOnlineRes = ET.SubElement(rpCntInfo, 'cntOnlineRes')
			eMailAdd = ET.SubElement(cntAddress, 'eMailAdd').text = self.metadata['contact_email']
			delPoint = ET.SubElement(cntAddress, 'delPoint').text = self.metadata['contact_street_address']
			city = ET.SubElement(cntAddress, 'city').text = self.metadata['contact_city']
			adminArea = ET.SubElement(cntAddress, 'adminArea').text = self.metadata['contact_state']
			postCode = ET.SubElement(cntAddress, 'postCode').text = str(self.metadata['contact_zip'])
			voiceNum = ET.SubElement(cntPhone, 'voiceNum').text = self.metadata['contact_phone']
			linkage = ET.SubElement(cntOnlineRes, 'linkage').text = self.metadata['psrc_website']

			#add Description (dataIdInfo/idPurp)
			abstract = self.metadata['summary']
			abstract = self.clean_metadata_string(abstract)
			summary_addendum = self.metadata['summary_addendum']
			summary_addendum = self.clean_metadata_string(summary_addendum)
			summary_footer = self.metadata['summary_footer']
			summary_footer = self.clean_metadata_string(summary_footer)
			abstract = abstract + '<br/><br/>' + summary_addendum + '<br/><br/>' + summary_footer
			idAbs = ET.SubElement(dataIdInfo, 'idAbs').text = abstract

			use_constraints = self.metadata['use_constraints']
			use_constraints = self.clean_metadata_string(use_constraints)
			useLimit = ET.SubElement(consts, 'useLimit').text = use_constraints

			sup_info = self.metadata['supplemental_info']
			sup_info = self.clean_metadata_string(sup_info)
			suppInfo = ET.SubElement(dataIdInfo, 'suppInfo').text = sup_info

			#idPurp = ET.SubElement(dataIdInfo, 'idPurp').text = data_lineage

			idCredit = root.find('./dataIdInfo/idCredit')
			idCredit.text = self.metadata['data_source']
		

			fields = self.metadata['fields']
			eainfo = ET.SubElement(root, 'eainfo')
			if fields is not None:
				for f in fields:
					detailed = ET.SubElement(eainfo, 'detailed')
					enttyp = ET.SubElement(detailed, 'enttyp')
					enttypl = ET.SubElement(enttyp, 'enttypl')
					enttypl.text = f['title']
					enttypd = ET.SubElement(enttyp, 'enttypd')
					enttypd.text = f['description']

			dqInfo = ET.SubElement(root, 'dqInfo')
			data_lineage = self.metadata['data_lineage'] 
			data_lineage = self.clean_metadata_string(data_lineage)
			dataLineage = ET.SubElement(dqInfo, 'dataLineage')
			statement = ET.SubElement(dataLineage, 'statement').text = data_lineage
			tree.write(metadata_file, encoding='UTF-8', xml_declaration=True)
			item.update(metadata=metadata_file)

		except Exception as e:
			print('error in set_and_update_metadata')
			print(e.args[0])
			if os.path.exists(metadata_file): os.remove(metadata_file)
			raise


	def initialize_metadata_file(self, item):
		"""
		Create a metadata XML file locally from a template, 
			then update an item in ArcOnline with the metadata XML file.
   
		Parameter:
			item: An item in ArcOnline.
  		"""
		try:
			metadata_template = r'./metadata_template.xml'
			metadata_file = r'./workspace/metadata.xml'
			if os.path.exists(metadata_file):
				os.remove(metadata_file)
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
		"""
  		Print a data frame to the terminal window.  Used for testing only.
    	"""
		try:
			print("printing dataframe:")
			print(self.df)
			print("finished printing dataframe")
		except Exception as e:
			print(e.args[0])
			raise


	def set_editability(self, layer):
		'''
		Set the editability for a layer in ArcOnline.
		Disallow edits if self.allow_edits is set to False,
			otherwise allow CREATE, DELETE, UPDATE and EDITING 
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
		"""
  		Set the sharing properties for a layer/item in ArcOnline so that
			it is visible either globally or just by PSRC staff.
		Also set the group membership for the item.
		The audience is set per the "share_level" property of self 
  			(see the __init__ procedure above)
    
    	Parameter:
     		layer: A layer in ArcOnline"""
		try:
			sl = self.share_level
			item_sharing_mgr = layer.sharing
			if sl == 'everyone':
				item_sharing_mgr.sharing_level = SharingLevel.EVERYONE
			elif sl == 'org':
				item_sharing_mgr.sharing_level = SharingLevel.ORG 
			item_grp_sharing_mgr = item_sharing_mgr.groups
			share_group_ids = self.get_group_ids()
			for grp in share_group_ids:
				item_grp_sharing_mgr.add(group=grp)
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
			layer_type_pred = '; type:File Geodatabase' if self.is_spatial else '; type:CSV'
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
					self.republish_spatial()
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
