# data-portal-tools

This repo is intended to house classes to be used for import and export to PSRC's data portal hosted on ArcGIS Online.  

### How to run it ###

#### Setup ####
You will need to create two environment variables to store your ArcGIS username and password.  I gave these variables the names AGOL_ADMIN_USERNAME and AGOL_ADMIN_PW, but you can choose other names as you like.  They are referenced in the code in [export_runner.py](export_runner.py#16) so make sure you update those lines to reflect your environment variable names.

#### To export a layer from ElmerGeo or a table from Elmer:  ####
1. Create a config file (in yaml format) for the layer/table in the /Config/run_files directory.  Give it a filename that is very close or identical to the layer name itself.
1. Open the file _export_runner.py_ and adjust the final block to search for your new yaml file. 
1. Run _export_runner.py_

The main code is run by executing the file __export_runner.py__, which in turn looks to the configuration files in  __Config/run_files/__ for a lists of data sets to export.  Each YAML file in this directory defines the parameters for a single dataset (i.e. a spatial layer or a tabular data set).  A single run of __export_runner.py__ iterates through all the config files in __Config/run_files/__, exporting each in turn.  The config parameters for each data set are as follows:
*  _share_level_ (string): allow the exported layer to be share globally (the default) or just with members of our organization.  The two possible values are 'everyone' (the default) or 'org'.
* _description_ (string): this is the layer description that will be listed in ArcGIS Online.
* _allow_edits_ (True or False): (feature pending) This will control whether the layer will be editable in Arc Online. 
* _tags_ (string): A comma-delimited list of tags for the layer in ArcGIS Online

### Config file structure ###

The yaml files in folder `Config\run_files` define the details of each layer to be published.  These details include things like the source data to be published, metadata, and some other related information.  The elements in the yaml are defined as follows

- `layer_params`
  - `accessInformation`:
  - `allow_edits`: This should be set to False, unless you want users to be able to edit the data set
  - `licenseInfo`: If you want to publish the data with any particular license, you can specify the license here. 
  - `metadata`
    - `contact_city`:  Seattle
    - `contact_email`: email address of the PSRC staff member
    - `contact_name`:  The PSRC staff member available to respond to questions about the data set
    - `contact_phone`:  The phone number of the PSRC staff member 
    - `contact_state`:  Washington
    - `contact_street_address`:  1201 3rd Ave. Ste. 500
    - `contact_zip`: 98101
    - `data_lineage`:
    - `fields`: a list of pairs of `title` and  `description` elements, with one pair for each field in the data set
        - `- title`: The title of a column
        - `  description`: The description of the column
    - `data_source`: Organizations or locations that originally provided the data to PSRC, even if it has been reshaped since.
    - `date_last_updated`:  The date of the last modification to the data. 
    - `organization_name`: Puget Sound Regional Council
    - `psrc_website`: URL of web page discussing the program or project around the data (or just www.psrc.org)
    - `summary`: A description of the data set.  This could be a short sentence or a long paragraph.
    - `summary_addendum`:  Anything entered here will appear as a secondary paragraph in the description/summary
    - `summary_footer`: Anything entered here will appear as a third paragraph in the description/summary
    - `supplemental_info`: This is appended as an element in the layer's metadata xml, but is not currently included in ESRI's metadata display.  
    - `time_period`: The span of time represented by the data.  
    - `update_cadence`: The frequency at which the data set gets updated
  - `share_level`: a member of the set ["everyone", "org", "owner"].  This determines how widely the data will be shared.  Usually this will be "everyone".
  - `snippet`: If provided, this is appended to the top of the layer's summary.  It is often a very brief description of the data, with or without a version number.
  - `groups`: Groups are groupings of data on the Data Portal.
  - `spatial_data`: [True, False].  True means it is a spatial layer, False means it will be published in tabular format.
  - `tags`: Any tags to be associated with the layer, for searchability.  At least one tag should be supplied. 
  - `title`: The title
- `source`
  - `is_simple`: Set this to True if the spatial layer does not contain polygons with donut holes.  For tabular data, set to True if the table will be exported in its entirety as it exists in Elmer (False if it is defined by a `sql_query`)
  - `feature_dataset`: If the spatial layer exists as a layer in ElmerGeo, list its feature dataset container here
  - `has_donut_holes`: deprected column.  Ignored
  - `schema_name`: The schema in which a table resides in Elmer (ignored unless `is_simple == True AND spatial_data == False`)
  - `sql_query`: A Select query runnable against Elmer (if `spatial_data == False`) or against ElmerGeo (if `spatial_data == True`).
  - `table_name`: The name of a table in Elmer (ignored unless `is_simple == True AND spatial_data == False`)



### Internals ###
See the module `PortalExporter` for classes to use for import and export from our internally-facing SQL Server databases.  The module contains several classes:
 * __PortalConnector__ provides a connection object that binds an internally-facing database to the data portal.
 * __PortalResource__ defines a resource (a table, view, or user-defined query) on an internally-facing database, and provides an *export* method that allows that data to be easily published to the data portal as a single CSV.
 * __PortalSpatialResource__ is similar to __PortalResource__, but is for versioned spatial data layers such as those in ElmerGeo.  The *export* method in this class publishes a spatial layer on the data portal in GeoJSON format.

