"""
This barebones script updates the Regional Growth Centers Feature Layer in AGOL 
with the zip file /workspace/Regional_Growth_Centers.zip, which was generated 
by running export_runner.py in the usual way.  For some reason the python script 
failed to update the feature layer with the new geometry, 
even though they AGOL layer's metadata was successfully updated with the data 
from the yaml file.
"""

from arcgis.gis import GIS 
from arcgis.features import FeatureLayerCollection 
import os
pw = os.getenv('AGOL_ADMIN_PW')
gis = GIS("https://www.arcgis.com", "gisadmin_PSRC", pw)
item = gis.content.get("2a6243faa0fe47a5b90526c6d0e01cbb")
flc = FeatureLayerCollection.fromitem(item)
flc.manager.overwrite("../workspace/Regional_Growth_Centers.zip")