
# import numpy for constant computation
import numpy as np

# Constants


# Software version
VERSION = '1.1.3'

# Contact mail address
CONTACT = 'christian.francesconi@ses.com'

# Default isolevel to be displayed at patten loading
DEFAULT_ISOLEVEL_DBI = [-10, -8, -6, -4, -2, 0]

# geostationary altitude
ALTGEO = 35786000.0 # m

# Earth radius at equator and pole
EARTH_RAD_EQUATOR_M = 6378137.0000 # m
EARTH_RAD_POLE_M = 6356752.3142 # m
EARTH_RAD_BASEMAP = 6370997.0000 # m

# degrees to radians conversion
DEG2RAD = np.pi / 180.0
# radians to degrees conversion 
RAD2DEG = 180.0 / np.pi

# Default elevation contour
DEFAULT_ELEVATION = 10

# boldness of drawing
BOLDNESS = {'no line': 0,
            'light': 0.1,
            'medium': 0.3,
            'heavy':0.5}
def getboldness(linewidth):
    if linewidth == 0:
        return 'no line'
    elif linewidth < 0.2:
        return 'light'
    elif linewidth < 0.4:
        return 'medium'
    else:
        return 'heavy'
