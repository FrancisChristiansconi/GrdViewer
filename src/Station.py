# PyQt5 widgets import
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QAction, qApp, QDialog, QLineEdit, \
                            QHBoxLayout, QVBoxLayout, QPushButton, QWidget, QFileDialog, QLabel, \
                            QGridLayout, QCheckBox

class Station(object):
    
    # Constructor of station
    def __init__(self, lon=0.0, lat=0.0, name='nowhere', tag='NWH', xtag=0.0, ytag=0.0,Bpe=None):        
        self.fLonDeg = lon   # Longitude in degrees
        self.fLatDeg = lat   # Latitude in degrees
        self.strName = name  # Long name for reference
        self.strTag  = tag   # Short name for display
        self.fTagX   = xtag  # X Position of tag relative to point
        self.fTagY   = ytag  # Y position of tag relative to point   
        self.fBpe    = Bpe   # Radius of circle to draw around station
    # end of constructor
# end of class Station

class ViewStation(QFileDialog):

    def __init__(self, parent=None):
        # Parent constructor
        super().__init__()

        # Add Title to the widget
        self.setWindowTitle('Add stations from file')
        self.setMinimumSize(100, 50)

        if parent:
            self.stationList = parent.earthPlt.stationList


        # Dialog is modal to avoid reentry and weird behaviour
        self.setModal(True)
        self.show()
    # end of constructor

    def getStationFromFile(self, strFileName):
        # initialize return list
        stationList = []
        # open file and read text data
        oFile = open(strFileName, "r")
        # read all lines in a table
        tLines = oFile.readlines()
        # close file        
        oFile.close()

        # split data and add them to Station list
        for iLine in range(len(tLines)):
            tokens = tLines[iLine].split()
            strName = tokens[0]
            strTag  = tokens[1]
            fLonDeg = tokens[2]
            fLatDeg = tokens[3]
            fTagX   = tokens[4]
            fTagY   = tokens[5]
            fBpe    = tokens[6]
            stationList.append(Station(lon=fLonDeg, lat=fLatDeg, name=strName, \
                                        tag=strTag, xtag=fTagX, ytag=fTagY, Bpe=fBpe))

        return stationList


