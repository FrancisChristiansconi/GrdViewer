# system module
import sys

# import Matplotlib and Basemap
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter
from matplotlib.figure import Figure

# import PyQt5 and link with matplotlib
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QAction, qApp, QDialog, QLineEdit, \
                            QHBoxLayout, QVBoxLayout, QPushButton, QWidget, QFileDialog, QLabel, \
                            QGridLayout, QCheckBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# import numpy
import numpy as np

# import configparser module to manage ini files
import configparser

# local modules
import EarthPlot as plc
import Station as stn

# Customised Dialog
from Viewer import ViewerPosDialog
from Zoom import ZoomDialog
from Pattern import GrdDialog
from Elevation import ElevDialog
from Station import StationDialog



# Class to generate a window with Earth display
class PayPat(QMainWindow):
    
    # constructor
    def __init__(self):

        # Parent constructor
        super().__init__()
                
        # give an name to the windows
        self.title = 'Grd viewer'
        self.setWindowTitle(self.title)

        # # window dimension
        # self.width  = 8     # inches
        # self.height = 6     # inches
        # self.dpi    = 300   # dot per inch
        # self.resize(self.width*self.dpi, self.height*self.dpi)
        self.bRevertX      = False
        self.bRevertY      = False
        self.bUseSecondPol = False

        self.config = configparser.ConfigParser()
        self.config.read('.\\GrdViewer\\grdviewer.ini')

        # Create Main window central widget
        self.cWidget = QWidget()

        # Add menu bar and menus
        self.menuBar = self.createMenu()

        # Add map
        self.earthPlt = plc.EarthPlot(parent=self.cWidget, config=self.config)

        # place test field in a vertical box layout
        vbox = QVBoxLayout(self.cWidget)
        vbox.addWidget(self.menuBar)
        vbox.addWidget(self.earthPlt)

        # self.cWidget.addLayout(vbox)
        self.setCentralWidget(self.cWidget)
        self.show()

    # end of constructor
    
    # Create menu bar and menus
    def createMenu(self):
        # Add menu bar
        self.menuBar = self.menuBar()

        # Add File menu
        self.menuFile = self.menuBar.addMenu('File')

        # Items
        actQuit = QAction('Quit', self)
        self.menuFile.addAction(actQuit)
        actQuit.triggered.connect(qApp.quit)

        # Add Viewer Menu
        self.menuView = self.menuBar.addMenu('View')

        # Add Items
        actChgViewPos = QAction('Viewer position', self)
        self.menuView.addAction(actChgViewPos)
        actChgViewPos.triggered.connect(self.viewViewer)

        # Add Item: Zoom
        actZoom = QAction('Zoom', self)
        self.menuView.addAction(actZoom)
        actZoom.triggered.connect(self.viewZoom)

        # Add Item: Projection
        menuProjection = self.menuView.addMenu('Projection')
        menuProjection.addAction('Geo')
        menuProjection.addAction('Mercator')
        menuProjection.triggered[QAction].connect(self.toggleProj)

        # Add display grd Menu
        self.menuPat = self.menuBar.addMenu('Pattern')
        
        # Add Items
        actLoadGrd = QAction('Load Grd', self)
        self.menuPat.addAction(actLoadGrd)
        actLoadGrd.triggered.connect(self.viewLoadGrd)

        # Add Misc menu
        self.menuMisc = self.menuBar.addMenu('Misc.')
        # Add Items
        actElevation = QAction('Elevation Contour', self)
        self.menuMisc.addAction(actElevation)
        actElevation.triggered.connect(self.viewElevation)

        # Add menu item to add stations
        actStation = QAction('Add stations file', self)
        self.menuMisc.addAction(actStation)
        actStation.triggered.connect(self.viewStation)

        return self.menuBar
        

    # Dialog box to change position of Viewer (LLA coordinates)
    def viewViewer(self):
        vPosDial = ViewerPosDialog(self.earthPlt.viewer, self.earthPlt)
        vPosDial.exec_()
    
    # Dialog box to load Grd file and display
    def viewLoadGrd(self):
        # Get filename
        self.strFileName, _ = QFileDialog.getOpenFileName()
        if self.strFileName:
            grdDialog = GrdDialog(self.strFileName, self)
            grdDialog.exec_()
        
    # Open dialog to set zoom of Earth plot
    def viewZoom(self):
        vZoomDial = ZoomDialog(self.earthPlt.zoom, self.earthPlt.strProjection, self.earthPlt)
        vZoomDial.exec_()

    # open dialog to draw Elevation contour
    def viewElevation(self):
        vElevDial = ElevDialog(self)
        vElevDial.exec_()

    # open dialog to get stations to draw
    def viewStation(self):
        strStationFileName, _ = StationDialog.getOpenFileName()
        if strStationFileName:
            # add the stations to the station list
            self.earthPlt.stationList.extend(stn.getStationFromFile(strStationFileName))
            # refresh display
            self.earthPlt.draw()

    # Toggle between Geo and Mercator projection
    def toggleProj(self, q):
        if q.text() == 'Geo':
            self.earthPlt.draw(proj='geos')
        elif q.text() == 'Mercator':
            self.earthPlt.draw(proj='merc')

# End of Class PayPat   




# Main execution
if __name__ == '__main__':   
    # Create main window
    mainWindow = QApplication(sys.argv)
    app = PayPat()

    # Start main loop
    sys.exit(mainWindow.exec_())

