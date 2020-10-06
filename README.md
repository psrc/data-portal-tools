# data-portal-tools

This repo is intended to house classes to be used for import and export to PSRC's data portal hosted on ArcGIS Online.  

See the module `PortalExporter` for classes to use for import and export from our internally-facing SQL Server databases.  The module contains several classes:
 * __PortalConnector__ provides a connection object that binds an internally-facing database to the data portal.
 * __PortalResource__ defines a resource (a table, view, or user-defined query) on an internally-facing database, and provides an *export* method that allows that data to be easily published to the data portal as a single CSV.
 * __PortalSpatialResource__ is similar to __portal_resource__, but is for versioned spatial data layers such as those in ElmerGeo.  The *export* method in this class publishes a spatial layer on the data portal in GeoJSON format.
