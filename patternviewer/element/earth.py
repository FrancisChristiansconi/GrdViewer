"""This module handle the earth element of the display
"""

# Third party imports
from mpl_toolkits.basemap import Basemap as bmap

# Local imports
# Astract mother class Element
from patternviewer.element.element import Element
# Module constants
import patternviewer.constant as cst


class Earth(Element):
    """This class wrap off interaction with Basemap module.
    """

    def __init__(self, parent, conf):
        """Initialize Earth instance
        """
        self._parent = parent

        # Set minimal default values
        self._config['projection'] = cst.DEFAULT_PROJ
        self._config['min_azimuth'] = cst.MIN_AZ
        self._config['max_azimuth'] = cst.MAX_AZ
        self._config['min_elevation'] = cst.MIN_EL
        self._config['max_elevation'] = cst.MAX_EL
        self._config['lon'] = 0.0
        self._config['lat'] = 0.0

        self.configure(conf)


        # extract required parameters from self._config
        c = self._config
        projection = self.set(c, 'projection', 'nsper')
        llcrnrx=self.set(c, 'llcrnrx', 
        llcrnry=self.llcrnry,
        urcrnrx=self.urcrnrx,
        urcrnry=self.urcrnry,
        lon_0=self._viewer.longitude(),
        lat_0=self._viewer.latitude(),
        satellite_height=self._viewer.altitude(),
        resolution=resolution,
        ax=ax
        self._map = bmap()
    # End of function __init__

    def refresh(self):
        """Refresh self._map with config data
        """
        pass
    # End of function refresh

    def plot(self):
        pass
    # End of function plot

    def clearplot(self):
        pass
    # End of function clearplot

    def configure(self, conf=None):
        self._config.update(conf)
    # End of function configure

# End of class Earth
