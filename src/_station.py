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

class StationDialog(QFileDialog):

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


def getStationFromFile(strFileName):
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
        tokens = tLines[iLine].split(',')
        strName = tokens[0]
        strTag  = tokens[1]
        fLonDeg = float(tokens[2])
        fLatDeg = float(tokens[3])
        fTagX   = float(tokens[4])
        fTagY   = float(tokens[5])
        fBpe    = float(tokens[6])
        stationList.append(Station(lon=fLonDeg, lat=fLatDeg, name=strName, \
                                    tag=strTag, xtag=fTagX, ytag=fTagY, Bpe=fBpe))

    return stationList


