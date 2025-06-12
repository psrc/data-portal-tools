from arcgis import features
from arcgis import mapping
import arcpy
import sys
from pathlib import Path
from arcpy import metadata as md
import os, shutil 
import xml.dom.minidom as DOM
import xml.etree.ElementTree as ET
from arcgis import GIS


elmer_geo_conn_path = r'C:\Users\cpeak\OneDrive - Puget Sound Regional Council\Documents\ArcGIS\Projects\MyProject13\SQLServer-SQLserver-ElmerGeo.sde'
arcpy.env.workspace = f"{elmer_geo_conn_path}"

# create dict of datasets per feature classes
fc_dict = {}
for dataset in arcpy.ListDatasets():
    dataset_name = dataset.split(".")[2]
    for fc in arcpy.ListFeatureClasses("*", "", dataset_name):
        fc_name = fc.split(".")[2]
        fc_dict[fc_name] = dataset_name

metadata_path = Path('./workspace/metadata')

meta_files = os.listdir(metadata_path)
src_file_path = r'.'

def get_dataset(layer):
    try:
        return(fc_dict[l])
    except Exception as e:
        return('nothing')

for f in meta_files:
    l = f.replace('_metadata.xml','').lower()
    dataset = get_dataset(l)
    # print(f"layer {l} is in dataset {dataset}")
    layer_path = Path(elmer_geo_conn_path)/dataset/l 
    target_item_md = md.Metadata(layer_path)
    mdata_path = f"{metadata_path}\{f}"
    new_md = md.Metadata(mdata_path)
    # target_item_md.copy(new_md)
    # target_item_md.save()
    if l != 'block2000_nowater':
        if not target_item_md.isReadOnly:
            #target_item_md.importMetadata(src_file_path)
            target_item_md.importMetadata(mdata_path)
            target_item_md.save()
            target_item_md.synchronize('ALWAYS')
            target_item_md.save()
            print(f"exported metadata for {l}")
        else:
            print(f"layer {l} is read-only")