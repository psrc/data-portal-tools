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

