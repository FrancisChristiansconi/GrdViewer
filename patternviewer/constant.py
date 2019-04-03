
# import numpy for constant computation
import numpy as np

# Constants


# Software version
VERSION = '1.1.3Beta'

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
    """This function return a string key from a line width value.
    The string keys are the ones of the dictionary BOLDNESS defined in constant.py.
    """
    # if provided a string check if numeric or already boldness string
    if type(linewidth) is str:
        if not linewidth.isnumeric():
            return linewidth
    # else process as a float linewidth value
        else:
            width = float(linewidth)
    else:
        width = linewidth
    if width == 0:
        return 'no line'
    elif width < 0.2:
        return 'light'
    elif width < 0.4:
        return 'medium'
    else:
        return 'heavy'
# end of function getboldness
