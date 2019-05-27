"""This module is the entry point of the application. It defines
the main window and call the constructor to earthplot object where
all the work is done.
"""

# import standard modules
# ==================================================================================================
# import os
import os
# system module
import sys
from sys import argv

# import third party modules
# ==================================================================================================
# import configparser module to manage ini files
import configparser
# import PyQt5 and link with matplotlib
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp, \
    QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, \
    QLabel, QComboBox
# numerical help
import numpy as np

# import local modules
# ==================================================================================================
# debug utilities
import patternviewer.utils as utils
# Earthplot objects
import patternviewer.earthplot as plc
# elevation curves dialog
from patternviewer.element.elevation import ElevDialog
# import from viewer module
from patternviewer.viewer import Viewer
from patternviewer.viewer import ViewerPosDialog
# import from zoom module
from patternviewer.zoom import Zoom
from patternviewer.zoom import ZoomDialog
# imports from station module
import patternviewer.element.station as stn
# import polygon module
from patternviewer.element import polygon
# import constant file
import patternviewer.constant as cst

# static functions
# ==================================================================================================


def version():
    """Returns version of the software as a string.
    """
    return cst.VERSION
# end of function version


def contact():
    """Returns contact email of the software as a string.
    """
    return cst.CONTACT
# end of function contact


class GrdViewer(QMainWindow):
    """Class to generate a window with Earth display.
    """

    # constructor
    def __init__(self, inifile=None):
        utils.trace("in")

        # Parent constructor
        super().__init__()

        # give an name to the windows
        self.title = 'Pattern viewer'
        self.setWindowTitle(self.title)

        # Do not remember why these are initialized here
        self.revert_x_axis = False
        self.revert_y_axis = False
        self.second_polarisation = False

        # get current dir
        cwd = os.getcwd()
        if inifile is None:
            filename = 'grdviewer.ini'
        else:
            filename = inifile
        print(".ini file: {0:s}".format(filename))
        # read .ini file
        self.config = configparser.ConfigParser()
        self.config.read(filename)
        # go back to original directory
        os.chdir(cwd)

        # Create Main window central widget
        self.centralwidget = QWidget(self)

        # Add menu bar and menus
        self._menubar = self.createmenu()

        # status bar
        statusbar = QHBoxLayout(None)
        # add viewer position to status bar
        self._viewer_label = QLabel('', parent=self)
        statusbar.addWidget(self._viewer_label)
        statusbar.addStretch(1)
        # add mouse ll and gain display
        self._mouse_pos_label = QLabel('0.00deg. E  0.00deg. N', parent=self)
        self.setmousepos(0, 0)
        statusbar.addWidget(self._mouse_pos_label)
        # add combo box for pattern selection
        self._patterncombobox = QComboBox(parent=self)
        statusbar.addWidget(self._patterncombobox)

        # Add map
        self._earthplot = plc.EarthPlot(parent=self.centralwidget,
                                        config=self.config)

        # set viewer pos from EarthPlot config
        self.setviewerpos(self._earthplot.viewer().longitude(),
                          self._earthplot.viewer().latitude(),
                          self._earthplot.viewer().altitude())

        # place test field in a vertical box layout
        vbox = QVBoxLayout(self.centralwidget)
        vbox.addWidget(self._menubar)
        vbox.addWidget(self._earthplot)
        vbox.addLayout(statusbar)

        # self.centralwidget.addLayout(vbox)
        self.setCentralWidget(self.centralwidget)
        self.show()

        utils.trace('out')
    # end of constructor

    def setmousepos(self, lon, lat, gain=None):
        """Set mouse position in status bar.
        """
        # if the mouse is out of Earth do not display anything
        if np.isnan(lon) or np.isnan(lat):
            mouse_label_text = ''
        else:
            # else display longitude latitude an if available antenna gain
            if gain is None:
                mouse_label_text = '{0:0.2f}deg. E  {1:0.2f}deg. N'.format(
                    lon, lat)
            else:
                mouse_label_text = '{0:0.2f}deg. E ' \
                    '{1:0.2f}deg. N {2:0.2f}dB'.format(lon, lat, gain)
        self._mouse_pos_label.setText(mouse_label_text)
    # end of method setmousepos

    def setviewerpos(self, lon, lat, alt):
        """Set viewer position in status bar.
        """
        viewer_label_text = 'Viewer: {0:0.2f}deg. E ' \
            '{1:0.2f}deg. N  {2:0.2f}m.'.format(lon, lat, alt)
        self._viewer_label.setText(viewer_label_text)
    # end of method setviewerpos

    def setpatterncombo(self, items):
        """Update status bar combobox items list.
        """
        pbox = self._patterncombobox
        pbox.clear()
        pbox.addItems(items)
        allitems = [pbox.itemText(i) for i in range(pbox.count())]
        return allitems

    def getpatterncombo(self):
        """Access to pattern combobox value.
        """
        return self._patterncombobox.currentText()

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
        geo_action = QAction('Geo', self, checkable=True)
        cyl_action = QAction('Cylindrical', self, checkable=True)
        menuprojection.addAction(geo_action)
        menuprojection.addAction(cyl_action)
        menuprojection.triggered[QAction].connect(self.toggleprojection)
        # map resolution submenu and items
        menuresolution = self._menuview.addMenu('Map resolution')
        # c: crude
        # l: low
        # i: intermediate
        # h: high
        # f: full
        res_crude_action = QAction('crude', self, checkable=True)
        res_low_action = QAction('low', self, checkable=True)
        res_int_action = QAction('intermediate', self, checkable=True)
        res_high_action = QAction('high', self, checkable=True)
        res_full_action = QAction('full', self, checkable=True)
        menuresolution.addAction(res_crude_action)
        menuresolution.addAction(res_low_action)
        menuresolution.addAction(res_int_action)
        menuresolution.addAction(res_high_action)
        menuresolution.addAction(res_full_action)
        menuresolution.triggered[QAction].connect(self.set_earth_resolution)

        # add/remove Blue Marble
        bluemarble_action = QAction('Blue Marble', self)
        self._menuview.addAction(bluemarble_action)
        bluemarble_action.triggered.connect(self.toggle_bluemarble)

        # configure Earth lines
        # 1. Coast lines
        coastlines_menu = self._menuview.addMenu('Coast lines')
        no_coastlines_action = QAction('no line', self, checkable=True)
        coastlines_light_action = QAction('light', self, checkable=True)
        coastlines_medium_action = QAction('medium', self, checkable=True)
        coastlines_heavy_action = QAction('heavy', self, checkable=True)
        coastlines_menu.addAction(no_coastlines_action)
        coastlines_menu.addAction(coastlines_light_action)
        coastlines_menu.addAction(coastlines_medium_action)
        coastlines_menu.addAction(coastlines_heavy_action)
        coastlines_menu.triggered[QAction].connect(self.set_coastlines)

        # 2. Country borders
        countries_menu = self._menuview.addMenu('Country borders')
        no_countries_action = QAction('no line', self, checkable=True)
        countries_light_action = QAction('light', self, checkable=True)
        countries_medium_action = QAction('medium', self, checkable=True)
        countries_heavy_action = QAction('heavy', self, checkable=True)
        countries_menu.addAction(no_countries_action)
        countries_menu.addAction(countries_light_action)
        countries_menu.addAction(countries_medium_action)
        countries_menu.addAction(countries_heavy_action)
        countries_menu.triggered[QAction].connect(self.set_countries)

        # 3. Parallels
        parallels_menu = self._menuview.addMenu('Parallels')
        no_parallels_action = QAction('no line', self, checkable=True)
        parallels_light_action = QAction('light', self, checkable=True)
        parallels_medium_action = QAction('medium', self, checkable=True)
        parallels_heavy_action = QAction('heavy', self, checkable=True)
        parallels_menu.addAction(no_parallels_action)
        parallels_menu.addAction(parallels_light_action)
        parallels_menu.addAction(parallels_medium_action)
        parallels_menu.addAction(parallels_heavy_action)
        parallels_menu.triggered[QAction].connect(self.set_parallels)

        # 4. Meridians
        meridians_menu = self._menuview.addMenu('Meridians')
        no_meridians_action = QAction('no line', self, checkable=True)
        meridians_light_action = QAction('light', self, checkable=True)
        meridians_medium_action = QAction('medium', self, checkable=True)
        meridians_heavy_action = QAction('heavy', self, checkable=True)
        meridians_menu.addAction(no_meridians_action)
        meridians_menu.addAction(meridians_light_action)
        meridians_menu.addAction(meridians_medium_action)
        meridians_menu.addAction(meridians_heavy_action)
        meridians_menu.triggered[QAction].connect(self.set_meridians)

        # Add display pattern Menu
        self.menupattern = menubar.addMenu('Pattern')
        # load pattern item
        load_pattern_action = QAction('Load pattern file', self)
        self.menupattern.addAction(load_pattern_action)
        load_pattern_action.triggered.connect(self.loadpattern)

        # Add Misc menu
        self._menumisc = menubar.addMenu('Misc.')
        # elevation item
        disp_elev_action = QAction('Elevation Contour', self)
        self._menumisc.addAction(disp_elev_action)
        disp_elev_action.triggered.connect(self.elevation_dialog)
        # load stations file
        add_station_action = QAction('Add stations file', self)
        self._menumisc.addAction(add_station_action)
        add_station_action.triggered.connect(self.loadstations)
        add_station_action = QAction('Add station', self)
        self._menumisc.addAction(add_station_action)
        add_station_action.triggered.connect(self.loadstations)
        # load polygons file
        add_poly_action = QAction('Add polygons file', self)
        self._menumisc.addAction(add_poly_action)
        add_poly_action.triggered.connect(self.loadpolygon)

        # add Help menu
        self._menu_help = menubar.addMenu('Help')
        # Version
        version_action = QAction('Version: ' + version(), self)
        # Contact
        contact_action = QAction('Contact: ' + contact(), self)
        self._menu_help.addAction(version_action)
        self._menu_help.addAction(contact_action)

        # return statement
        return menubar
    # end of method createmenu

    def viewer_dialog(self):
        """This method pops up the viewer setting dialog widget.
        Viewer coordinates are given in LLA.
        """
        dialbox = ViewerPosDialog(self._earthplot.viewer(), self._earthplot)
        dialbox.exec_()

        # refresh satellite position display
        self.setviewerpos(self._earthplot.viewer().longitude(),
                          self._earthplot.viewer().latitude(),
                          self._earthplot.viewer().altitude())
    # end of method viewer_dialog

    def loadpattern(self):
        """Pops up dialog box to load Grd file and display it
        on the Earth plot.
        """
        utils.trace('in')
        # Get filename
        filenames, _ = QFileDialog.getOpenFileNames()
        # if file name provided open the customised dialog box
        if not filenames == []:
            for filename in filenames:
                pattern = self._earthplot.loadpattern({'filename': filename})
            if pattern:
                self._earthplot.draw_elements()
        utils.trace('out')
    # end of method load_pattern

    def loadpolygon(self):
        """Open dialog to get polygon to draw.
        """
        filenames, _ = QFileDialog.getOpenFileNames()
        if not filenames == []:
            for filename in filenames:
                # get list of polygon and append it to the existing list
                self._earthplot._polygons.extend(
                    polygon.getpolygons(self._earthplot, filename))
            # refresh display
            self._earthplot.draw_elements()
    # end of method

    def loadstations(self):
        """Open dialog to get stations to draw.
        """
        filenames, _ = QFileDialog.getOpenFileNames()
        if not filenames == []:
            for filename in filenames:
                # add the stations to the station list
                self._earthplot._stations.extend(
                    stn.get_station_from_file(filename, self._earthplot))
            # refresh display
            self._earthplot.draw_elements()
    # end of method station_dialog

    def zoom_dialog(self):
        """Open dialog to set zoom of Earth plot.
        """
        dialbox = ZoomDialog(self._earthplot.zoom(),
                             self._earthplot)
        dialbox.exec_()
    # end of method zoom_dialog

    def elevation_dialog(self):
        """Open dialog to draw Elevation contour.
        """
        dialbox = ElevDialog(self)
        dialbox.exec_()
    # end of method elevation_dialog

    def toggleprojection(self, action):
        """Toggle between Geo and Cylindrical projection.
        """
        if action.text() == 'Geo':
            self._earthplot.projection('nsper')
            self.getmenuitem('View>Projection>Geo').setChecked(True)
            self.getmenuitem('View>Projection>Cylindrical').setChecked(False)
        elif action.text() == 'Cylindrical':
            self._earthplot.projection('cyl')
            self.getmenuitem('View>Projection>Geo').setChecked(False)
            self.getmenuitem('View>Projection>Cylindrical').setChecked(True)
        self._earthplot.draw_elements()
    # end of method toggleprojection

    def toggle_bluemarble(self):
        """Toggle display of Earth picture Blue Marble.
        """
        self._earthplot._bluemarble = not self._earthplot._bluemarble
        projection = self._earthplot._projection
        resolution = self._earthplot._resolution
        self._earthplot.drawearth(proj=projection,
                                  resolution=resolution)
        self.getmenuitem('View>Blue Marble').setChecked(
            self._earthplot._bluemarble)
        self._earthplot.draw_axis()
        self._earthplot.draw()
        # end of method toggle_bluemarble

    def clearplot(self):
        """Clear the Earth map plot
        """
        # remove pattern menu items
        for pattern in self._earthplot._patterns:
            menu = self._earthplot._patterns[pattern]._pattern_sub_menu
            menu_action = menu.menuAction()
            menu.parent().removeAction(menu_action)
        self._earthplot._patterns.clear()
        self._earthplot._stations.clear()
        self._earthplot._elev.clear()
        self._earthplot.zoom(Zoom())
        self._earthplot.viewer(Viewer())
        self._earthplot.draw_axis()
        self._earthplot.draw_elements()
        self._earthplot.draw()
    # end of function clearplot

    def set_earth_resolution(self, action):
        """Call back to call for EarthPlot set_resolution function.
        """
        menu = self.getmenuitem('View>Map resolution').menu()
        action_dictionary = self.getmenuitemlist(menu=menu)
        for act in action_dictionary:
            action_dictionary[act].setChecked(False)
        action.setChecked(True)
        self._earthplot.set_resolution(action.text()[0].lower())
    # end of set_earth_resolution

    def set_coastlines(self, action):
        """Callback to set the boldness of coastlines on Earth map
        """
        utils.trace('in')
        menu = self.getmenuitem('View>Coast lines').menu()
        action_dictionary = self.getmenuitemlist(menu=menu)
        for act in action_dictionary:
            action_dictionary[act].setChecked(False)
        action.setChecked(True)
        self._earthplot.set_coastlines(action.text(), True)
        utils.trace('out')
    # end of method set_coastlines

    def set_countries(self, action):
        """Callback to set the boldness of country borders on Earth map
        """
        utils.trace('in')
        menu = self.getmenuitem('View>Country borders').menu()
        action_dictionary = self.getmenuitemlist(menu=menu)
        for act in action_dictionary:
            action_dictionary[act].setChecked(False)
        action.setChecked(True)
        self._earthplot.set_countries(action.text(), True)
        utils.trace('out')
    # end of method set_countries

    def set_parallels(self, action):
        """Callback to set the boldness of parallels on Earth map
        """
        utils.trace('in')
        menu = self.getmenuitem('View>Parallels').menu()
        action_dictionary = self.getmenuitemlist(menu=menu)
        for act in action_dictionary:
            action_dictionary[act].setChecked(False)
        action.setChecked(True)
        self._earthplot.set_parallels(action.text(), True)
        utils.trace('out')
    # end of method set_parallels

    def set_meridians(self, action):
        """Callback to set the boldness of meridians on Earth map
        """
        utils.trace('in')
        menu = self.getmenuitem('View>Meridians').menu()
        action_dictionary = self.getmenuitemlist(menu=menu)
        for act in action_dictionary:
            action_dictionary[act].setChecked(False)
        action.setChecked(True)
        self._earthplot.set_meridians(action.text(), True)
        utils.trace('out')
    # end of method set_meridians

    def saveas(self):
        """Callback to save the Earth plot into file.
        """
        utils.trace('in')
        defaultfilename = 'plot.PNG'
        dialogbox = QFileDialog(caption='Save As ...',
                                directory=self._earthplot.rootdir)
        dialogbox.selectFile(defaultfilename)
        filename, _ = dialogbox.getSaveFileName()
        self._earthplot.save(filename)
        utils.trace('out')
    # end of callback saveas

    def save(self):
        """Callback to save the Earth plot with default/previously given file name.
        """
        self._earthplot.save()
    # end of callback save

    def get_centralwidget(self):
        """Accessor to central widget.
        """
        return self.centralwidget
    # end of get_centralwidget

    def getmenuitem(self, item: str):
        """Return menu item from menu name and item name.
        """
        menu_dictionary = self.getmenuitemlist(self._menubar)
        try:
            return menu_dictionary[item]
        except KeyError:
            return None

    def getmenuitemlist(self, menu, basename=''):
        """This recursive function returns a dictionary of menu items which keys
        are the items names.
        Each submenu level up to the item itself is given in the key,
        levels separated by character '>'
        """
        item_dictionary = {}
        for item in menu.actions():
            if isinstance(item, QAction):
                if basename == '':
                    name = item.text()
                else:
                    name = basename + '>' + item.text()
                item_dictionary[name] = item
                try:
                    item_dictionary.update(
                        self.getmenuitemlist(item.menu(), name))
                except AttributeError:
                    # catch AttributeError exception
                    pass
        return item_dictionary


# End of Class GrdViewer


# Main execution
if __name__ == '__main__':
    # Create main window
    MAIN_WINDOW = QApplication(argv)
    # if .ini file is passed as argument use it to initialize application
    if len(argv) > 1:
        INIFILE = argv[1]
    else:
        INIFILE = None
    APP = GrdViewer(INIFILE)

    # Start main loop
    sys.exit(MAIN_WINDOW.exec_())

# end of module grdviewer
