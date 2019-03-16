"""This module deals with polygons representation.
"""

# import Earth projection module
from mpl_toolkits.basemap import Basemap

# import path for customised marker
from matplotlib.path import Path

# import configparser module to manage ini files (.gxt uses .ini format)
import configparser

class Polygon(object):
    """Represent a polygon in longitude, latitude and provide function and methods
    to manipulate it and display it on a map.
    """

    def __init__(self, lon, lat, gain=0.0):
        """Constructor of Polygon class.
        """
        # list of station representing vertex of a polygon
        self._longitude = lon
        self._latitude = lat
    # end of constructor

    def longitude(self):
        """Return list of longitude of polygon vertex.
        """
        return self._longitude
    # end of function longitude

    def latitude(self):
        """Return list of latitude of polygon vertex.
        """
        return self._latitude
    # end of function latitude

    def projected(self, map: Basemap):
        """Return list of stations position in the given Earth projection.
        """
        return map(self._longitude, self._latitude)
    # end of function projected

    def appendvertex(self, lon, lat):
        """Add a station at the end of the list."""
        self._longitude.append(lon)
        self._latitude.append(lat)
    # end of method appendvertex

    def plot(self, map, **kwargs):
        # get coordinates in the Earth projection
        x, y = self.projected(map)
        map.plot(x , y, **kwargs)
        
    # end of method plot

    def len(self):
        """Return number of vertex.
        """
        return len(self._longitude)

# end of class Polygon


def getpolygons(filename: str):
    """Returns a list of Polygons created from a text file passed
    to the function.
    """

    # warning if file format is not the expected one
    if filename[-3:] != 'gxt':
        print('Function getpolygons reads only .GXT file')

    # initialize return list
    polygons = []

    # create configparser instance from polygon file
    config = configparser.ConfigParser()
    config.read(filename)

    # get number of polygons
    polygon_number = config.getint('COHeader','n_cont', fallback=0)

    # read polygons
    for i in range(1, polygon_number+1):
        # section name is Ci
        section = 'C' + str(i)
        # get contour gain spec
        gain = config.getfloat(section, 'gain', fallback=0.0)
        # number of points in the polygon
        n_point = config.getint(section, 'n_point', fallback=0)
        # get longitude and latitude lists
        lon = []
        lat = []
        for j in range(n_point):
            point = config.get(section,'p' + str(j + 1), fallback='')
            lon.append(float(point.split(sep=';')[0]))
            lat.append(float(point.split(sep=';')[1]))
        # end for j

        # if polygon is not closed, add a last vertex
        if lon[-1] != lon[0] or lat[-1] != lat[0]:
            lon.append(lon[0])
            lat.append(lat[0])

        # add polygon to the list
        polygons.append(Polygon(lon, lat,gain))  

    # end for i

    return polygons
# end of function getpolygons
