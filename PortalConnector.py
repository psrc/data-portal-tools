from arcgis.gis import GIS

class PortalConnector(object):

	def __init__(self, 
              portal_username, 
              portal_pw, 
              portal_url="https://psregcncl.maps.arcgis.com"):
		"""
		Define the parameters by which the portal_connector can connect a database to a data portal.
		Parameters:
			portal_username: ArcGIS Online/Data Portal username
			portal_pw: ArcGIS Online/Data Portal password
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

	@property
	def portal_url(self):
		return self._portal_url

	@portal_url.setter 
	def portal_url(self, value): 
		self._portal_url = value


	def connect(self):
		"""
		Make connections to the data portal
		"""
		try:
			self.gis = GIS(self.portal_url, self.username, self.pw)
		except Exception as e:
			print(e.args[0])
			raise


	def find_by_title(self, title):
		"""
		Find a feature layer or feature service on the portal, and return that layer.
		Searches among only those layers that are owned by the authenticated portal user
		Returns the string "no object" if no layer is found.
		parameters:
			title: The title of the layer to be searched for
		"""
		try:
			lyr = "no object"
			title = title
			gis = self.gis
			owner_clause = '; owner:{}'.format(gis.users.me.username)
			content_list = gis.content.search(
				query='title:{}{}'.format(title, owner_clause),
				)
			for item in content_list:
				if (item['title'] == title and 'Feature' in item['type']) :
					# return_item = item
					lyr = item
					break	
			return(lyr)

		except Exception as e:
			print(e.args[0])
			raise

	def find_items_referencing_feature_layer(self, feature_layer_name):
		"""
		Find web maps and other collections that reference a specific feature layer
		
		Args:
			feature_layer_name (str): The name/title of the feature layer to search for
			
		Returns:
			list: A list of dictionaries containing information about items that reference the feature layer.
				  Each dictionary contains: {'id', 'title', 'type', 'url', 'owner', 'modified'}
		"""
		referencing_items = []
		
		try:
			# Search for web maps, dashboards, story maps, and other items that might reference layers
			item_types = ['Web Map', 'Dashboard', 'StoryMap', 'Web Scene', 'Web Mapping Application', 
						 'Operation View', 'Feature Collection', 'Web Experience']
			
			print(f"Searching for items that reference feature layer: '{feature_layer_name}'")
			
			for item_type in item_types:
				try:
					# Search for items of this type
					search_results = self.gis.content.search(
						query=f'type:"{item_type}"',
						max_items=1000,
						sort_field='modified',
						sort_order='desc'
					)
					
					print(f"Checking {len(search_results)} {item_type} items...")
					
					for item in search_results:
						try:
							# Get the item's JSON data
							item_data = None
							
							if hasattr(item, 'get_data'):
								try:
									item_data = item.get_data()
								except:
									# Some items might not have accessible data
									continue
							
							# Check if the feature layer is referenced in the item data
							if item_data and self._check_for_layer_reference(item_data, feature_layer_name):
								referencing_items.append({
									'id': item.id,
									'title': item.title,
									'type': item.type,
									'url': item.url if hasattr(item, 'url') else None,
									'owner': item.owner,
									'modified': str(item.modified) if hasattr(item, 'modified') else None
								})
								print(f"Found reference in {item_type}: '{item.title}' (ID: {item.id})")
						
						except Exception as e:
							# Continue processing other items if one fails
							print(f"Error processing item {item.id}: {e}")
							continue
				
				except Exception as e:
					print(f"Error searching for {item_type} items: {e}")
					continue
			
			print(f"Found {len(referencing_items)} items referencing '{feature_layer_name}'")
			return referencing_items
			
		except Exception as e:
			print(f"Error in find_items_referencing_feature_layer: {e}")
			raise

	def _check_for_layer_reference(self, item_data, feature_layer_name):
		"""
		Helper method to recursively check if a feature layer is referenced in item data
		
		Args:
			item_data: The JSON data of the item to check
			feature_layer_name (str): The name of the feature layer to search for
			
		Returns:
			bool: True if the feature layer is referenced, False otherwise
		"""
		try:
			import json
			
			# Convert to string for searching if it's not already
			if isinstance(item_data, dict):
				data_str = json.dumps(item_data).lower()
			else:
				data_str = str(item_data).lower()
			
			feature_layer_name_lower = feature_layer_name.lower()
			
			# Check for direct name matches
			if feature_layer_name_lower in data_str:
				return True
			
			# For web maps, also check operational layers specifically
			if isinstance(item_data, dict):
				# Check operational layers in web maps
				if 'operationalLayers' in item_data:
					for layer in item_data['operationalLayers']:
						if isinstance(layer, dict):
							# Check layer title
							if 'title' in layer and layer['title'].lower() == feature_layer_name_lower:
								return True
							# Check layer name
							if 'name' in layer and layer['name'].lower() == feature_layer_name_lower:
								return True
							# Check layer URL for the feature layer name
							if 'url' in layer and feature_layer_name_lower in layer['url'].lower():
								return True
				
				# Check base maps
				if 'baseMap' in item_data and 'baseMapLayers' in item_data['baseMap']:
					for layer in item_data['baseMap']['baseMapLayers']:
						if isinstance(layer, dict):
							if 'title' in layer and layer['title'].lower() == feature_layer_name_lower:
								return True
							if 'url' in layer and feature_layer_name_lower in layer['url'].lower():
								return True
				
				# Check tables
				if 'tables' in item_data:
					for table in item_data['tables']:
						if isinstance(table, dict):
							if 'title' in table and table['title'].lower() == feature_layer_name_lower:
								return True
							if 'name' in table and table['name'].lower() == feature_layer_name_lower:
								return True
			
			return False
			
		except Exception as e:
			print(f"Error checking layer reference: {e}")
			return False
