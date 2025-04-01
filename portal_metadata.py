from arcgis import GIS
import glob
from pathlib import Path
from PortalConnector import PortalConnector
import yaml
import xml.etree.ElementTree as ET


with open(r'Config\\auth.yml') as file:
	auth = yaml.load(file, Loader=yaml.FullLoader)
portal_conn = PortalConnector(
	portal_username=auth['enterprise']['username'],
	portal_pw=auth['enterprise']['pw'],
	portal_url='https://gis.psrc.org/portal')

gis = portal_conn.gis

path = r'.\workspace\metadata'
files = glob.glob(path + "/*.xml")
sub_string = '_metadata.xml'

full_file_list = []
found_list = []
metadata_files = {}
file_to_title_map = {}

# Extract actual titles from XML files
for file in files:
    file_name = Path(file).name
    short_name = file_name.removesuffix(sub_string).lower()
    full_file_list.append(short_name)
    metadata_files[short_name] = file
    
    # Parse XML to get the actual title
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        # Find the resTitle element - adjust namespace if needed
        res_title_elem = root.find(".//resTitle")
        if res_title_elem is not None and res_title_elem.text:
            actual_title = res_title_elem.text
            print(f"File: {short_name}, Actual title: {actual_title}")
            file_to_title_map[short_name] = actual_title
        else:
            print(f"Could not find title in {file}")
            file_to_title_map[short_name] = short_name  # Fallback to filename
    except Exception as e:
        print(f"Error parsing {file}: {e}")
        file_to_title_map[short_name] = short_name  # Fallback to filename

print(full_file_list)
# finding matching layer on portal
for file_name in full_file_list:
    print(f"filename: {file_name}")
    print(f"metadata file: {metadata_files[file_name]}")
    
    # Use the actual title from the XML file for searching
    actual_title = file_to_title_map.get(file_name, file_name)
    print(f"Searching for title: {actual_title}")
    
    # Add owner clause to filter for items owned by the authenticated user
    owner_clause = f'; owner:{gis.users.me.username}'
    items = gis.content.search(query=f'title:{file_name}', item_type='Feature Service')
    for item in items:
        print(f"Found item: {item.title}")
        # Compare with the actual title instead of the filename
        if item.title.lower() == file_name.lower():
            tags = item.tags
            mdata_file = metadata_files[file_name]
            item.update(item_properties={'tags':tags}, metadata=mdata_file)
            found_list.append(file_name)
            print(f"Updated metadata for {item.title}")

if not found_list:
    print("No matching items found. Check portal connection and item titles.")
