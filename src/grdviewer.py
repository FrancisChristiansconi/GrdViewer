"""This module is the entry point of the application. It defines 
the main window and call the constructor to earthplot object where 
all the work is done.
"""

# system module
import sys

# debug utilities
import utils

# import configparser module to manage ini files
import configparser

# import PyQt5 and link with matplotlib
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp, \
                            QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, \
                            QLabel

# import os
import os

# traceback
import utils

# local modules
import earthplot as plc

# customised Dialog
from pattern.dialog import PatternDialog
from elevation import ElevDialog

# import from viewer module
from viewer import Viewer
from viewer import ViewerPosDialog

# import from zoom module
from zoom import Zoom
from zoom import ZoomDialog

# imports from station module 
import station as stn
from station import StationDialog

# import polygon module
import polygon

# import constant file
import constant as cst


class GrdViewer(QMainWindow):
    """Class to generate a window with Earth display.
    """   

    # constructor
    def __init__(self):
        utils.trace("in")

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

        # get current dir
        cwd = os.getcwd()
        # go to .ini directory
        # target work directory is
        if cwd[-3:] == 'src':
            target_dir = cwd[:-4]
            os.chdir(target_dir)
        # read .ini file
        self.config = configparser.ConfigParser()
        self.config.read('grdviewer.ini')
        # go back to original directory
        os.chdir(cwd)

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

        hbox = QHBoxLayout(None)
        self._lon_label = QLabel('Longitude (deg)', parent=self)
        self._lat_label = QLabel('Latitude (deg)',  parent=self)
        self._alt_label = QLabel('Altitude (m)',    parent=self)
        self._lon_label.setText(str(self.earth_plot.viewer().longitude()) + 'deg. E')
        self._lat_label.setText(str(self.earth_plot.viewer().latitude()) + 'deg. N')
        self._alt_label.setText(str(self.earth_plot.viewer().altitude()) + 'm.')
        hbox.addWidget(self._lon_label)
        hbox.addStretch(1)
        hbox.addWidget(self._lat_label)
        hbox.addStretch(1)
        hbox.addWidget(self._alt_label)
        vbox.addLayout(hbox)

        # self.centralwidget.addLayout(vbox)
        self.setCentralWidget(self.centralwidget)
        self.show() 

        utils.trace('out')
    # end of constructor
    
    # Create menu bar and menus
    def createmenu(self):
        """Create application menu bar, sub menus and items
        """
        # Add menu bar
        menubar = self.menuBar()

        # Add File menu
        self._menufile = menubar.addMenu('File')
        # saveas item
        saveas_action = QAction('Save plot as', self)
        self._menufile.addAction(saveas_action)
        saveas_action.triggered.connect(self.saveas)
        # save plot item
        save_action = QAction('Save plot', self)
        self._menufile.addAction(save_action)
        save_action.triggered.connect(self.save)
        # clear plot item
        clear_action = QAction('Clear plot', self)
        self._menufile.addAction(clear_action)
        clear_action.triggered.connect(self.clearplot)
        # quit application item
        quit_action = QAction('Quit', self)
        self._menufile.addAction(quit_action)
        quit_action.triggered.connect(qApp.quit)

        # Add Viewer Menu
        self._menuview = menubar.addMenu('View')
        # viewer position item
        change_viewer_pos_action = QAction('Viewer position', self)
        self._menuview.addAction(change_viewer_pos_action)
        change_viewer_pos_action.triggered.connect(self.viewer_dialog)
        # zoom item
        update_zoom_action = QAction('Zoom', self)
        self._menuview.addAction(update_zoom_action)
        update_zoom_action.triggered.connect(self.zoom_dialog)
        # projection submenu and items
        menuprojection = self._menuview.addMenu('Projection')
        menuprojection.addAction('Geo')
        menuprojection.addAction('Mercator')
        menuprojection.triggered[QAction].connect(self.toggleprojection)
        # map resolution submenu and items
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
        # configure Earth lines
        coastlines_menu = self._menuview.addMenu('Coast lines')
        no_coastlines_action = QAction('no line', self)
        coastlines_light_action = QAction('light', self)
        coastlines_medium_action = QAction('medium', self)
        coastlines_heavy_action = QAction('heavy', self)
        coastlines_menu.addAction(no_coastlines_action)
        coastlines_menu.addAction(coastlines_light_action)
        coastlines_menu.addAction(coastlines_medium_action)
        coastlines_menu.addAction(coastlines_heavy_action)
        coastlines_menu.triggered[QAction].connect(self.set_coastlines)


        # Add display pattern Menu
        self.menupattern = menubar.addMenu('Pattern')
        # load pattern item
        load_pattern_action = QAction('Load Grd', self)
        self.menupattern.addAction(load_pattern_action)
        load_pattern_action.triggered.connect(self.load_pattern)

        # Add Misc menu
        self._menumisc = menubar.addMenu('Misc.')
        # elevation item
        disp_elev_action = QAction('Elevation Contour', self)
        self._menumisc.addAction(disp_elev_action)
        disp_elev_action.triggered.connect(self.elevation_dialog)
        # load stations file
        add_station_action = QAction('Add stations file', self)
        self._menumisc.addAction(add_station_action)
        add_station_action.triggered.connect(self.station_dialog)
        # load polygons file
        add_poly_action = QAction('Add polygons file', self)
        self._menumisc.addAction(add_poly_action)
        add_poly_action.triggered.connect(self.loadpolygon)

        # add Help menu
        self._menu_help = menubar.addMenu('Help')
        # Version
        version_action = QAction('Version: ' + self.version(), self)
        # Contact
        contact_action = QAction(' Contact: ' + cst.CONTACT, self)
        self._menu_help.addAction(version_action)
        self._menu_help.addAction(contact_action)

        # return statement
        return menubar
    # end of method createmenu

    def version(self):
        """Returns version of the software as a string.
        """
        return cst.VERSION
    # end of function version

    def viewer_dialog(self):
        """This method pops up the viewer setting dialog widget.
        Viewer coordinates are given in LLA.
        """
        dialbox = ViewerPosDialog(self.earth_plot.viewer(), self.earth_plot)
        dialbox.exec_()
        
        # refresh satellite position display
        self._lon_label.setText(str(self.earth_plot.viewer().longitude()) + 'deg. N')
        self._lat_label.setText(str(self.earth_plot.viewer().latitude()) + 'deg. E')
        self._alt_label.setText(str(self.earth_plot.viewer().altitude()) + 'm.')
    # end of method viewer_dialog
    
    def load_pattern(self):
        """Pops up dialog box to load Grd file and display it
        on the Earth plot.
        """
        utils.trace('in')
        # Get filename
        file_name, _ = QFileDialog.getOpenFileNames()
        # if file name provided open the customised dialog box
        if len(file_name):
            for f in file_name:
                try:
                    p = self.earth_plot.load_pattern({'filename':f})
                except:
                    print("Load pattern cancelled.")
            if p:
                self.earth_plot.draw_elements()
        utils.trace('out')
    # end of method load_pattern

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
            self.earth_plot.draw_elements()
    # end of method station_dialog

    def loadpolygon(self):
        """Open dialog to get polygon to draw.
        """
        filename, _ = QFileDialog.getOpenFileName()
        if filename:
            # get list of polygon and append it to the existing list
            self.earth_plot._polygons.extend(polygon.getpolygons(filename))
            # refresh display
            self.earth_plot.draw_elements()
    # end of method 

    def toggleprojection(self, action):
        """Toggle between Geo and Mercator projection.
        """
        if action.text() == 'Geo':
            self.earth_plot.projection('nsper')
        elif action.text() == 'Mercator':
            self.earth_plot.projection('merc')
        self.earth_plot.draw_elements()
    # end of method toggleprojection

    def clearplot(self):
        """Clear the Earth map plot 
        """
        # remove pattern menu items
        for f in self.earth_plot._patterns:
            menu = self.earth_plot._patterns[f]['menu']
            menu_action = menu.menuAction()
            menu.parent().removeAction(menu_action)
        self.earth_plot._patterns.clear()
        self.earth_plot._stations.clear()
        self.earth_plot._elev.clear()
        self.earth_plot.zoom(Zoom())
        self.earth_plot.viewer(Viewer())
        self.earth_plot.draw_axis()
        self.earth_plot.draw_elements()
        self.earth_plot.draw()
    # end of function clearplot
    
    def set_earth_resolution(self, action):
        """Call back to call for EarthPlot set_resolution function.
        """
        self.earth_plot.set_resolution(action.text()[0].lower())
    # end of set_earth_resolution

    def set_coastlines(self, action):
        """Callback to set the boldness of coastlines on Earth map
        """
        utils.trace('in')
        boldness = {'no line': 0,
                    'light': 0.1,
                    'medium': 0.3,
                    'heavy':0.5}
        self.earth_plot.set_coastlines(boldness[action.text()], True)
        utils.trace('out')
    # end of method set_coastlines

    def saveas(self):
        """Callback to save the Earth plot into file.
        """
        utils.trace('in')
        defaultfilename = 'plot.PNG'
        dialogbox = QFileDialog(caption='Save As ...', directory=self.earth_plot.rootdir)
        dialogbox.selectFile(defaultfilename)
        filename, _ = dialogbox.getSaveFileName()
        self.earth_plot.save(filename)
        utils.trace('out')
    # end of callback saveas
    
    def save(self):
        """Callback to save the Earth plot with default/previously given file name.
        """
        self.earth_plot.save()
    # end of callback save

# End of Class GrdViewer   


# Main execution
if __name__ == '__main__':   
    # Create main window
    MAIN_WINDOW = QApplication(sys.argv)
    APP = GrdViewer()

    # Start main loop
    sys.exit(MAIN_WINDOW.exec_())

# end of module grdviewer
