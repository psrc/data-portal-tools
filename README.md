# data-portal-tools

This repo is intended to house classes to be used for import and export to PSRC's data portal hosted on ArcGIS Online.  

See the module `PortalExporter` for classes to use for import and export from our internally-facing SQL Server databases.  The module contains several classes:
 * __PortalConnector__ provides a connection object that binds an internally-facing database to the data portal.
 * __PortalResource__ defines a resource (a table, view, or user-defined query) on an internally-facing database, and provides an *export* method that allows that data to be easily published to the data portal as a single CSV.
 * __PortalSpatialResource__ is similar to __PortalResource__, but is for versioned spatial data layers such as those in ElmerGeo.  The *export* method in this class publishes a spatial layer on the data portal in GeoJSON format.

The is run by executing the file __export_runner.py__, which in turn looks to the configuration file __Config/config.yml__ for a list of data sets to export.  The YAML file also allows each data set's properties to be defined.  The config parameters for each data set are as follows:
*  _share_level_ (string): allow the exported layer to be share globally (the default) or just with members of our organization.  The two possible values are 'everyone' (the default) or 'org'.
* _description_ (string): this is the layer description that will be listed in ArcGIS Online.
* _allow_edits_ (True or False): (feature pending) This will control whether the layer will be editable in Arc Online. 
* _tags_ (string): A comma-delimited list of tags for the layer in ArcGIS Online
