
# import numpy for constant computation
import numpy as np

# Constants

# Contact mail address
CONTACT = 'christian.francesconi@ses.com'

# Default isolevel to be displayed at patten loading
DEFAULT_ISOLEVEL_DBI = [-10, -8, -6, -4, -2, 0]

# geostationary altitude
ALTGEO = 35786000.0  # m

# Earth radius at equator and pole
EARTH_RAD_EQUATOR_M = 6378137.0000  # m
EARTH_RAD_POLE_M = 6356752.3142  # m
EARTH_RAD_BASEMAP = 6370997.0000  # m

# degrees to radians conversion
DEG2RAD = np.pi / 180.0
# radians to degrees conversion
RAD2DEG = 180.0 / np.pi

# Default elevation contour
DEFAULT_ELEVATION = 10

# Earth geographical boundaries
MIN_LON = -180.0
MAX_LON = 180.0
MIN_LAT = -90.0
MAX_LAT = 90.0

# Default azel dimension of the plot
MIN_AZ = -9.0
MAX_AZ = 9.0
MIN_EL = -9.0
MAX_EL = 9.0

# Default projection
DEFAULT_PROJ = 'nsper'

# boldness of drawing
BOLDNESS = {'no line': 0,
            'light': 0.1,
            'medium': 0.3,
            'heavy': 0.5}


def getboldness(linewidth):
    """This function return a string key from a line width value.
    The string keys are the ones of the dictionary BOLDNESS defined
    in constant.py.
    """
    # if provided a string check if numeric or already boldness string
    boldstring = ''
    if isinstance(linewidth, str):
        if not linewidth.isnumeric():
            boldstring = linewidth
            return boldstring
    # else process as a float linewidth value
        else:
            width = float(linewidth)
    else:
        width = linewidth
    if width == 0:
        boldstring = 'no line'
    if width < 0.2:
        boldstring = 'light'
    if width < 0.4:
        boldstring = 'medium'
    else:
        boldstring = 'heavy'
    # unique point of exit
    return boldstring
# end of function getboldness
