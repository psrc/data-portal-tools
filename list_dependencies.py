from PortalConnector import PortalConnector
import yaml
import os

with open(r'Config\\auth.yml') as file:
	auth = yaml.load(file, Loader=yaml.FullLoader)


# Create connector
#portal = PortalConnector("username", "password", "portal_url")

portal = PortalConnector(
	portal_username=os.getenv('AGOL_ADMIN_USERNAME'),
	portal_pw=os.getenv('AGOL_ADMIN_PW')
 )

# Find references to a feature layer
results = portal.find_items_referencing_feature_layer("Urban_Growth_Area")

# Process results
for item in results:
    print(f"Found in {item['type']}: {item['title']}")
