import warnings
from arcgis.geometry import Geometry
from arcgis.features import GeoAccessor, GeoSeriesAccessor
from pandas import DataFrame
from geopandas import GeoDataFrame

def to_SpatiallyEnabledDataFrame(self, spatial_reference=None):
    """Returns an arcgis spatially-enabled data frame.

    Arguments:
    spatial_reference  Either None or a spatial reference integer code.
                       If None, the spatial reference will be extracted
                       from the GeoDataFrame if it is defined using an
                       EPSG code.
    """
    if not spatial_reference:
        crs = self.crs
        epsg_code = crs.to_epsg()
        if epsg_code:
            spatial_reference = {'wkid': epsg_code}
        else:
            spatial_reference = {'wkid': 4326}
            warnings.warn('Unable to extract a spatial reference, assuming latitude/longitude (EPSG 4326).')
    else:
        spatial_reference = {'wkid': spatial_reference}

    sdf = DataFrame(data=self.drop(self.geometry.name, axis=1))
    sdf['SHAPE'] = [Geometry.from_shapely(g, spatial_reference) for g in self.geometry.tolist()]
    sdf.spatial.set_geometry('SHAPE')

    return sdf

GeoDataFrame.to_SpatiallyEnabledDataFrame = to_SpatiallyEnabledDataFrame