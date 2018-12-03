"""This module deals with station representation.
"""

# PyQt5 widgets import
from PyQt5.QtWidgets import QFileDialog


class Station(object):
    """Represents a station, i.e. a position on the ground.
    Position is specified with longitude and latitude in decimal number.
    A station has several others attributes helping for display.
    """

    # Constructor of station
    def __init__(self, ll=(0.0, 0.0), name='nowhere', \
                 tag='NWH', xytag=(0.0, 0.0), bpe=None):
        """Constructor
        """   
        self._longitude = ll[0]    # Longitude in degrees
        self._latitude = ll[1]     # Latitude in degrees
        self._name = name          # Long name for reference
        self._tag = tag            # Short name for display
        self._tag_x = xytag[0]     # X Position of tag relative to point
        self._tag_y = xytag[1]     # Y position of tag relative to point   
        self._beam_point_err = bpe # Radius of circle to draw around station
    # end of constructor

    def longitude(self, lon:float = None) -> float:
        """Get/set for longitude.
        """
        if lon != None:
            self._longitude = lon
        return self._longitude
    
    def latitude(self, lat:float = None) -> float:
        """Get/set for latitude.
        """
        if lat != None:
            self._latitude = lat
        return self._latitude
    
    def xtag(self, x:float = None) -> float:
        """Get/set for tag x coordinate.
        """
        if x != None:
            self._tag_x = x
        return self._tag_x

    def ytag(self, y:float = None) -> float:
        """Get/set for tag y coordinate.
        """
        if y != None:
            self._tag_y = y
        return self._tag_y
    
    def beampointingerr(self, bpe:float = None) -> float:
        """Get/set for Beam pointing error value.
        """
        if bpe != None:
            self._beam_point_err = bpe
        return self._beam_point_err
    
    def name(self, s:str = None) -> str:
        """Get/set for station name.
        """
        if s != None:
            self._name = s
        return self._name
    
    def tag(self, s:str = None) -> str:
        """Get/set for station tag.
        """
        if s != None:
            self._tag = s
        return self._tag
    
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


def get_station_from_file(filename: str):
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
        tokens = line.split(',')
        name = tokens[0]
        tag  = tokens[1]
        lon = float(tokens[2]) 
        lat = float(tokens[3])
        tag_x = float(tokens[4])
        tag_y = float(tokens[5])
        beam_point_err = float(tokens[6])
        stations.append(Station(ll=(lon, lat), name=name, \
                                tag=tag, xytag=(tag_x, tag_y), \
                                bpe=beam_point_err))

    return stations
# end of function get_station_from_file

# end of module
