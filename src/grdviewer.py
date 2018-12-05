"""This module is the entry point of the application. It defines 
the main window and call the constructor to earthplot object where 
all the work is done.
"""

# system module
import sys

# import configparser module to manage ini files
import configparser

# import PyQt5 and link with matplotlib
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp, \
                            QVBoxLayout, QWidget, QFileDialog

# local modules
import earthplot as plc

# customised Dialog
from pattern import GrdDialog
from elevation import ElevDialog

# import from viewer module
from viewer import ViewerPos
from viewer import ViewerPosDialog

# import from zoom module
from zoom import Zoom
from zoom import ZoomDialog

# imports from station module 
import station as stn
from station import StationDialog


class GrdViewer(QMainWindow):
    """Class to generate a window with Earth display.
    """   

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
        self.revert_x_axis = False
        self.revert_y_axis = False
        self.second_polarisation = False

        self.config = configparser.ConfigParser()
        self.config.read('C:\\Users\\cfrance\\Dev\\Python\\PayPat\\grdviewer.ini')

        # Create Main window central widget
        self.centralwidget = QWidget(self)

        # Add menu bar and menus
        self._menubar = self.createmenu()

        # Add map
        self.earth_plot = plc.EarthPlot(parent=self.centralwidget, config=self.config)


        # place test field in a vertical box layout
        vbox = QVBoxLayout(self.centralwidget)
        vbox.addWidget(self._menubar)
        vbox.addWidget(self.earth_plot)

        # self.centralwidget.addLayout(vbox)
        self.setCentralWidget(self.centralwidget)
        self.show() 

    # end of constructor
    
    # Create menu bar and menus
    def createmenu(self):
        """Create application menu bar, sub menus and items
        """
        # Add menu bar
        menubar = self.menuBar()

        # Add File menu
        self._menufile = menubar.addMenu('File')

        # Items
        quit_action = QAction('Quit', self)
        self._menufile.addAction(quit_action)
        quit_action.triggered.connect(qApp.quit)
        clear_action = QAction('Clear plot', self)
        self._menufile.addAction(clear_action)
        clear_action.triggered.connect(self.clearplot)

        # Add Viewer Menu
        self._menuview = menubar.addMenu('View')

        # Add Items
        change_viewer_pos_action = QAction('Viewer position', self)
        self._menuview.addAction(change_viewer_pos_action)
        change_viewer_pos_action.triggered.connect(self.viewer_dialog)

        # Add Item: Zoom
        update_zoom_action = QAction('Zoom', self)
        self._menuview.addAction(update_zoom_action)
        update_zoom_action.triggered.connect(self.zoom_dialog)

        # Add Item: Projection
        menuprojection = self._menuview.addMenu('Projection')
        menuprojection.addAction('Geo')
        menuprojection.addAction('Mercator')
        menuprojection.triggered[QAction].connect(self.toggleprojection)

        # Add map resolution
        menuresolution = self._menuview.addMenu('Map resolution')
        # c: crude
        # l: low
        # i: intermediate
        # h: high
        # f: full
        res_crude_action = QAction('crude', self)
        res_low_action = QAction('low', self)
        res_int_action = QAction('intermediate', self)
        res_high_action = QAction('high', self)
        res_full_action = QAction('full', self)
        menuresolution.addAction(res_crude_action)
        menuresolution.addAction(res_low_action)
        menuresolution.addAction(res_int_action)
        menuresolution.addAction(res_high_action)
        menuresolution.addAction(res_full_action)
        menuresolution.triggered[QAction].connect(self.set_earth_resolution)

        # Add display grd Menu
        self.menupattern = menubar.addMenu('Pattern')
        
        # Add Items
        load_grd_action = QAction('Load Grd', self)
        self.menupattern.addAction(load_grd_action)
        load_grd_action.triggered.connect(self.load_grd_dialog)

        # Add Misc menu
        self._menumisc = menubar.addMenu('Misc.')
        # Add Items
        disp_elev_action = QAction('Elevation Contour', self)
        self._menumisc.addAction(disp_elev_action)
        disp_elev_action.triggered.connect(self.elevation_dialog)

        # Add menu item to add stations
        add_station_action = QAction('Add stations file', self)
        self._menumisc.addAction(add_station_action)
        add_station_action.triggered.connect(self.station_dialog)

        return menubar
    # end of method createmenu

    def viewer_dialog(self):
        """This method pops up the viewer setting dialog widget.
        Viewer coordinates are given in LLA.
        """
        dialbox = ViewerPosDialog(self.earth_plot.viewer(), self.earth_plot)
        dialbox.exec_()
    # end of method viewer_dialog
    
    def load_grd_dialog(self):
        """Pops up dialog box to load Grd file and display it
        on the Earth plot.
        """
        # Get filename
        grd_file_name, _ = QFileDialog.getOpenFileName()
        # if file name provided open the customised dialog box
        if grd_file_name:
            dialbox = GrdDialog(grd_file_name, self)
            dialbox.exec_()
    # end of method load_grd_dialog

    def zoom_dialog(self):
        """Open dialog to set zoom of Earth plot.
        """
        dialbox = ZoomDialog(self.earth_plot.zoom(), \
                             self.earth_plot)
        dialbox.exec_()
    # end of method zoom_dialog

    def elevation_dialog(self):
        """Open dialog to draw Elevation contour.
        """
        dialbox = ElevDialog(self)
        dialbox.exec_()
    # end of method elevation_dialog

    def station_dialog(self):
        """Open dialog to get stations to draw.
        """
        filename, _ = StationDialog.getOpenFileName()
        if filename:
            # add the stations to the station list
            self.earth_plot._stations.extend(stn.get_station_from_file(filename))
            # refresh display
            self.earth_plot.draw()
    # end of method station_dialog

    def toggleprojection(self, action):
        """Toggle between Geo and Mercator projection.
        """
        if action.text() == 'Geo':
            self.earth_plot.projection('geos')
            self.earth_plot.draw()
        elif action.text() == 'Mercator':
            self.earth_plot.projection('merc')
            self.earth_plot.draw()
    # end of method toggleprojection

    def clearplot(self):
        """Clear the Earth map plot 
        """
        for key in self.earth_plot._grds:
            menu_action = self.earth_plot._grds[key]['menu'].menuAction()
            self.menupattern.removeAction(menu_action)
        self.earth_plot._grds.clear()
        self.earth_plot._stations.clear()
        self.earth_plot._elev.clear()
        self.earth_plot.zoom(Zoom())
        self.earth_plot.viewer(ViewerPos())
        self.earth_plot.draw()
    
    def set_earth_resolution(self, action):
        """Call back to call for EarthPlot set_resolution function.
        """
        self.earth_plot.set_resolution(action.text()[0].lower())
        self.earth_plot.draw()
    # end of set_earth_resolution

# End of Class GrdViewer   


# Main execution
if __name__ == '__main__':   
    # Create main window
    MAIN_WINDOW = QApplication(sys.argv)
    APP = GrdViewer()

    # Start main loop
    sys.exit(MAIN_WINDOW.exec_())

# end of module grdviewer
