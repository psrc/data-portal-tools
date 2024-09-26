import os
from arcgis.gis import GIS
import yaml

    with open(r'Config\\auth.yml') as file:
        auth = yaml.load(file, Loader=yaml.FullLoader)
my_pw = auth['enterprise']['pw']
print(my_pw)

# portal_conn = PortalConnector(
# 	portal_username=auth['enterprise']['username'],
# 	portal_pw=auth['enterprise']['pw'])

gis = GIS('https://gis.psrc.org/', 'cpeak@psrc.org', my_pw)

# Search for feature layer collections in the GIS
search_results = gis.content.search(item_type="Map")
gis.content.

# Loop through each item in the search results
for item in search_results:
    print(f"Item: {item.title}, ID: {item.id}")

    # Access the layers for each item
    for layer in item.layers:
        print(f"Layer: {layer.properties.name}")