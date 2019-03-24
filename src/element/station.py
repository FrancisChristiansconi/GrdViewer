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
import constant as cst       # constants for the application
import earthplot as eplt     # Earth Plot class definition
from .element import Element # Astract  mother class Element


class Station(Element):
    """Represents a station, i.e. a position on the ground.
    Position is specified with longitude and latitude in decimal number.
    A station has several others attributes helping for display.
    """

# Constructor of class Station
#==================================================================================================
    def __init__(self, parent=None):
        """Constructor
        """
        if not isinstance(parent, eplt.EarthPlot) and parent is not None:
            raise TypeError(args='parent should be of type EarthPlot')
        self._parent = parent # reference to the parent EarthPlot
        self._station = None  # display elements references
        # configuration is stored in a dictionary
        self._config = {}
        # station conf
        self._config['longitude'] = 0.0      # Longitude in degrees
        self._config['latitude'] = 0.0       # Latitude in degrees
        self._config['name'] = ''            # Long name for reference
        self._config['marker'] = 'o'         # station marker
        self._config['marker size'] = 1      # marker size
        self._config['marker color'] = 'r'   # marker color
        # tag config
        self._config['tag'] = ''             # Short name for display
        self._config['tagpos'] = ''          # upleft, upright, downleft or downright
        self._config['fontsize'] = 3         # Tag fontsize
        # Beam pointing error circle
        self._config['bpe'] = 0              # Radius of circle to draw around station
        self._config['circle color'] = 'k'   # Color of bpe circle
        self._config['linewidth'] = 0.3      # Width of bpe circle line
        self._config['linestyle'] = 'dashed' # Style of bpe circle line  
    # end of constructor

# mandatory abstract method implementation inherited from class Element
#==================================================================================================
    def plot(self):
        """Plot the station on the given map if in the frame.
        """
        # get reference to Earth Map where station should be plotted
        earthmap = self._parent.get_earthmap()
        # radius of the Beam Pointing Error circle to be displayed (optionally)
        radius = self._parent.az2x(self._config['bpe'])
        # get coordinates of station in earth plot frame
        xsta, ysta = earthmap(self._config['longitude'], self._config['latitude'])
        # if station is out of plot do not display
        if self.visible(earthmap):
            # if BPE defined, display circle around station
            circle = None
            if self._config['bpe']:
                circle = plt.Circle((xsta, ysta), radius,
                                    color=self._config['circle color'], fill=False,
                                    linewidth=self._config['linewidth'],
                                    linestyle=self._config['linestyle'])
                earthmap.ax.add_artist(circle)
            # display a dot at station coordinates
            point = earthmap.scatter(xsta, ysta,
                                     self._config['marker size'],
                                     marker=self._config['marker'],
                                     color=self._config['marker color'])
            # add station tag, position is computed from plot size and desired relative position
            # wrt. station coordinates
            plot_width = self._parent.get_width()
            plot_height = self._parent.get_height()
            x_offset = plot_width / 200
            y_offset = plot_height / 200
            position = self._config['tagpos']
            if position == 'upleft':
                x_offset *= -1
                valign = 'bottom'
                halign = 'right'
            elif position == 'upright':
                valign = 'bottom'
                halign = 'left'
            elif position == 'downleft':
                x_offset *= -1
                y_offset *= -1
                valign = 'top'
                halign = 'right'
            elif position == 'downright':
                y_offset *= -1
                valign = 'top'
                halign = 'left'
            tag = earthmap.ax.text(s=self._config['tag'],
                                   x=xsta + x_offset,
                                   y=ysta + y_offset,
                                   va=valign,
                                   ha=halign,
                                   fontsize=self._config['fontsize'])
            # store references to plotted elements (point, tag and BPE circle)
            self._station = point, tag, circle
    # end of method plot

    def clearplot(self):
        """Implementation of abstract method clearplot.
        All plotted elements feature a remove method.
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
        # merge configuration of self with provided dictionary
        if config is not None:
            self._config.update(config)
            # check and convert to float
            self._config['longitude'] = float(self._config['longitude'])
            self._config['latitude'] = float(self._config['latitude'])
            self._config['marker size'] = float(self._config['marker size'])
            self._config['fontsize'] = float(self._config['fontsize'])
            self._config['bpe'] = float(self._config['bpe'])
            self._config['linewidth'] = float(self._config['linewidth'])
        # return merged dictionary
        return self._config
    # end of method configure

# Other functions and methods    
#==================================================================================================
    def visible(self, earthmap):
        """States if station is visible in the map frame.
        """
        # get coordinates of station in earth plot frame
        lon = self._config['longitude']
        lat = self._config['latitude']
        xsta, ysta = earthmap(lon, lat)
        return earthmap.llcrnrx < xsta and \
               xsta < earthmap.urcrnrx and \
               earthmap.llcrnry < ysta and \
               ysta < earthmap.urcrnry
    # end of function visible

# end of class Station
#==================================================================================================

class Dialog(QFileDialog):
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

# TODO implement class View to reconfigure a station

# TODO implement class Control to handle station element


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
        if line is not '':
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
