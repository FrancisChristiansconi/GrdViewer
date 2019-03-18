"""This module deals with station representation.
"""

# import third party modules
#==================================================================================================
# PyQt5 widgets import
from PyQt5.QtWidgets import QFileDialog
# matplotlib import
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
# numpy
import numpy as np

# import local modules
#==================================================================================================
import constant as cst
import earthplot as eplt
from .element import Element


class Station(Element):
    """Represents a station, i.e. a position on the ground.
    Position is specified with longitude and latitude in decimal number.
    A station has several others attributes helping for display.
    """

    # Constructor of station
    def __init__(self, parent=None):
        """Constructor
        """
        if not isinstance(parent, eplt.EarthPlot) and parent is not None:
            raise TypeError(args='parent should be of type EarthPlot')
        self._parent = parent # reference to the parent EarthPlot
        self._longitude = 0.0 # Longitude in degrees
        self._latitude = 0.0  # Latitude in degrees
        self._name = ''       # Long name for reference
        self._tag = ''        # Short name for display
        self._tagpos = ''     # upleft, upright, downleft or downright
        self._bpe = 0         # Radius of circle to draw around station
        self._station = None  # display elements references
    # end of constructor

# getter and setter
#==================================================================================================
    def longitude(self, lon: float = None) -> float:
        """Get/set for longitude.
        """
        if lon != None:
            self._longitude = lon
        return self._longitude
    
    def latitude(self, lat: float = None) -> float:
        """Get/set for latitude.
        """
        if lat != None:
            self._latitude = lat
        return self._latitude
    
    def tagpos(self, tagpos: str = None) -> str:
        """Get/set for tag x coordinate.
        """
        if tagpos != None:
            self._tag_x = tagpos
        return self._tag_x
    
    def beampointingerr(self, bpe: float = None) -> float:
        """Get/set for Beam pointing error value.
        """
        if bpe != None:
            self._bpe = bpe
        return self._bpe
    
    def name(self, name: str = None) -> str:
        """Get/set for station name.
        """
        if name != None:
            self._name = name
        return self._name

    def tag(self, tag: str = None) -> str:
        """Get/set for station tag.
        """
        if tag != None:
            self._tag = tag
        return self._tag

    def visible(self, earthmap):
        """States if station is visible in the map frame. 
        """
        # get coordinates of station in earth plot frame
        xsta, ysta = earthmap(self._longitude,self._latitude)
        return earthmap.llcrnrx < xsta and \
               xsta < earthmap.urcrnrx and \
               earthmap.llcrnry < ysta and \
               ysta < earthmap.urcrnry
    # end of function visible

    def plot(self):
        """Plot the station on the given map if in the frame.
        """
        earthmap = self._parent.get_earthmap()
        radius = self._parent.az2x(self._bpe)
        # get coordinates of station in earth plot frame
        xsta, ysta = earthmap(self._longitude, self._latitude)
        # if station is out of plot do not display
        if self.visible(earthmap):
            # if BPE defined, display circle around station
            circle = None
            if self._bpe:
                circle = plt.Circle((xsta, ysta), radius, \
                                    color='k', fill=False, linewidth=0.3, linestyle='dashed')
                earthmap.ax.add_artist(circle)
            # display a dot at station coordinates
            point = earthmap.scatter(xsta, ysta, 1, marker='o', color='r')
            # add station tag
            plot_width = self._parent.get_width()
            plot_height = self._parent.get_height()
            x_offset = plot_width / 200
            y_offset = plot_height / 200
            if self._tagpos == 'upleft':
                x_offset *= -1
                valign = 'bottom'
                halign = 'right'
            elif self._tagpos == 'upright':
                valign = 'bottom'
                halign = 'left'
            elif self._tagpos == 'downleft':
                x_offset *= -1
                y_offset *= -1
                valign = 'top'
                halign = 'right'
            elif self._tagpos == 'downright':
                y_offset *= -1
                valign = 'top'
                halign = 'right'
            tag = earthmap.ax.text(s=self._tag, x=xsta + x_offset,y=ysta + y_offset, va=valign, ha=halign)
            self._station = point, tag, circle
    # end of method plot

    def clearplot(self):
        """Implementation of abstract method clearplot.
        """
        if self._station is not None:
            for element in self._station:
                if element is not None:
                    element.remove()
            self._station = None
    # end of method clearplot

    def configure(self, config=None):
        """Implementation of abstract method configure.
        """
        self._longitude = self.set(config, 'longitude')
        self._latitude = self.set(config, 'latitude')
        self._name = self.set(config, 'name')
        self._tag = self.set(config, 'tag')
        self._tagpos = self.set(config, 'tagpos')
        self._bpe = self.set(config, 'bpe')

# end of class Station

class StationDialog(QFileDialog):
    """Customised dialog box to open a file and load station list.
    """
    def __init__(self):
        # Parent constructor
        super().__init__()

        # Add Title to the widget
        self.setWindowTitle('Add stations from file')

        # Dialog is modal to avoid reentry and weird behaviour
        self.setModal(True)
        self.show()
    # end of constructor
# End of Customized QDialog StationDialog


def get_station_from_file(filename: str, earthplot=None):
    """Returns a list of Station created from a text file passed
    to the function.
    """
    # initialize return list
    stations = []
    # open file and read text data
    file = open(filename, "r")
    # read all lines in a table
    lines = file.readlines()
    # close file        
    file.close()

    # split data and add them to Station list
    for line in lines:
        if len(line):
            if not line[0] == "#":
                tokens = line.split(',')
                name = tokens[0]
                tag  = tokens[1]
                lon = float(tokens[2]) 
                lat = float(tokens[3])
                tagpos = tokens[4]
                beam_point_err = float(tokens[5])
                station = Station(parent=earthplot)
                station.configure({'longitude': lon,
                                   'latitude': lat,
                                   'tag':tag,
                                   'name':name,
                                   'bpe':beam_point_err,
                                   'tagpos':tagpos})
                stations.append(station)

    return stations
# end of function get_station_from_file

# end of module
