from arcgis import features
from arcgis import mapping
import sys
from pathlib import Path
from arcpy import metadata as md
import os, shutil 
import xml.dom.minidom as DOM
from arcgis import GIS


elmer_geo_conn_path = r'C:\Users\cpeak\OneDrive - Puget Sound Regional Council\Documents\ArcGIS\Projects\metadata_test\AWS-PROD-SQL.sde'
elmer_geo_conn_path = r'T:\2024May\cpeak\AWS-PROD-SQL.sde'
arcpy.env.workspace = f"{elmer_geo_conn_path}"
#aprx_path = r'C:\Users\scoe\Documents\publish_elmer_geo\elmer_geo\elmer_geo.aprx'
dataset = 'political'
centers = r"ElmerGeo.DBO.urban_centers"
#outdir = r'C:\Users\scoe\Documents\publish_elmer_geo\service_definitions'

centers_path = Path(elmer_geo_conn_path)/dataset/centers

# Set the standard-format metadata XML file's path
src_file_path = r'T:\2024May\cpeak\metadata.xml'
target_item_md = md.Metadata(centers_path)
target_item_md.isReadOnly
mdata = md.Metadata(centers_path)
dir(target_item_md)
target_item_md.credits

# Import and apply to target
if not target_item_md.isReadOnly:
    target_item_md.importMetadata(src_file_path)
    target_item_md.save()
    target_item_md.synchronize('ALWAYS')
    target_item_md.save()
    print(f"target item updated")

target_item_md.importMetadata(src_file_path)
target_item_md.save()
target_item_md.synchronize('ALWAYS')
target_item_md.save()
target_item_md.synchronize()
target_item_md.xml
target_item_md.title
    
# loop through each dataset example
for dataset in arcpy.ListDatasets():
    dataset_name = dataset.split(".")[2]
    for fc in arcpy.ListFeatureClasses("*", "", dataset_name):
        print(f"{dataset}, {fc}")

# create dict of datasets per feature classes
fc_dict = {}
for dataset in arcpy.ListDatasets():
    dataset_name = dataset.split(".")[2]
    for fc in arcpy.ListFeatureClasses("*", "", dataset_name):
        fc_name = fc.split(".")[2]
        fc_dict[fc_name] = dataset_name


metadata_path = Path('./workspace/metadata')

def get_dataset(layer):
    try:
        return(fc_dict[l])
    except Exception as e:
        return('nothing')

run_files = os.listdir(metadata_path)
src_file_path = r'.'
for f in run_files:
    print(f"{metadata_path}\{f}")

run_files = os.listdir(metadata_path)
src_file_path = r'.'
for f in run_files:
    l = f.replace('_metadata.xml','').lower()
    dataset = get_dataset(l)
    # print(f"layer {l} is in dataset {dataset}")
    layer_path = Path(elmer_geo_conn_path)/dataset/l 
    target_item_md = md.Metadata(layer_path)
    mdata_path = f"{metadata_path}\{f}"
    new_md = md.Metadata(mdata_path)
    target_item_md.copy(new_md)
    target_item_md.save()
    if l == 'block2000_nowater':
        if not target_item_md.isReadOnly:
            #target_item_md.importMetadata(src_file_path)
            target_item_md.importMetadata(mdata_path)
            target_item_md.save()
            target_item_md.synchronize('ALWAYS')
            target_item_md.save()
            print(f"exported metadata for {l}")
        else:
            print(f"layer {l} is read-only")

new_md = md.Metadata('./workspace/metadata/safety_rest_area_metadata.xml')
print(new_md)


for f in run_files:
    l = f.replace('_metadata.xml','').lower()
    dataset = get_dataset(l)
    # print(f"layer {l} is in dataset {dataset}")
    layer_path = Path(elmer_geo_conn_path)/dataset/l 
    target_item_md = md.Metadata(layer_path)
    if target_item_md.isReadOnly:
        print(f"{l}:         READONLY")
    else:
        print(f"{l}:not readonly")

username = arcpy.Describe(elmer_geo_conn_path).connectionProperties.user
conn_properties = arcpy.Describe(elmer_geo_conn_path).connectionProperties
conn_properties = arcpy.Describe(elmer_geo_conn_path)
print(conn_properties)
conn_properties.dataType
dir(conn_properties)
arcpy.ListUsers()

arcpy.Describe(elmer_geo_conn_path)

arcpy.ListUsers(arcpy.env.workspace)[0]

w = arcpy.env.workspace
for u in arcpy.ListUsers(w):
    print(u)