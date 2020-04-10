"""This module deals with station representation.
"""


import os
import sys
import logging

# import third party modules
# ==================================================================================================
# PyQt5 widgets import
from PyQt5.QtWidgets import QFileDialog, QDialog, QAction, QLineEdit, QLabel, \
    QCheckBox, QComboBox, QGridLayout, QPushButton
from PyQt5 import QtCore
# matplotlib import
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
# numpy
import numpy as np

# import local modules
# ==================================================================================================
# import traceback utilities
import patternviewer.utils as utils
# Earth Plot class definition
from patternviewer import earthplot as eplt
# Astract mother class Element
from patternviewer.element.element import Element
# import line configuration dialog
from patternviewer.element.linedialog import LineDialog
from patternviewer.element.markerdialog import MarkerDialog
# import project constant
import patternviewer.constant as cst


class Station(Element):
    """Represents a station, i.e. a position on the ground.
    Position is specified with longitude and latitude in decimal number.
    A station has several others attributes helping for display.
    """

# Constructor of class Station
# ==================================================================================================
    def __init__(self, parent=None):
        """Constructor
        """
        self._parent = parent  # reference to the parent EarthPlot
        self._station = None  # display elements references
        # configuration is stored in a dictionary
        self._configuration = {}
        # station conf
        self._configuration['longitude'] = 0.0      # Longitude in degrees
        self._configuration['latitude'] = 0.0       # Latitude in degrees
        self._configuration['name'] = ''            # Long name for reference
        self._configuration['marker'] = 'o'         # station marker
        self._configuration['marker size'] = 1      # marker size
        self._configuration['marker color'] = 'red'   # marker color
        # tag config
        self._configuration['tag'] = ''             # Short name for display
        # upleft, upright, downleft or downright
        self._configuration['tagpos'] = ''
        self._configuration['fontsize'] = 3         # Tag fontsize
        # Beam pointing error circle
        # Radius of circle to draw around station
        self._configuration['bpe'] = 0
        self._configuration['linecolor'] = 'black'   # Color of bpe circle
        self._configuration['linewidth'] = 0.3      # Width of bpe circle line
        self._configuration['linestyle'] = 'dashed'  # Style of bpe circle line
    # end of constructor

# mandatory abstract method implementation inherited from class Element
# ==================================================================================================
    def plot(self):
        """Plot the station on the given map if in the frame.
        """
        if self.set(key='visible',
                    fallback=True, dtype=bool):
            # get reference to Earth Map where station should be plotted
            earthmap = self._parent.get_earthmap()
            # radius of the Beam Pointing Error circle to be displayed
            radius = self._parent.az2x(self._configuration['bpe'])
            # get coordinates of station in earth plot frame
            xsta, ysta = earthmap(
                self._configuration['longitude'], self._configuration['latitude'])
            # if station is out of plot do not display
            if self.visible(earthmap):
                # if BPE defined, display circle around station
                circle = None
                if self._configuration['bpe'] > 0:
                    circle = plt.Circle(
                        (xsta, ysta), radius,
                        color=self._configuration['linecolor'],
                        fill=False,
                        linewidth=self._configuration['linewidth'],
                        linestyle=self._configuration['linestyle'])
                    earthmap.ax.add_artist(circle)
                elif self._configuration['bpe'] < 0:
                    radius = np.abs(radius)
                    circle = plt.Rectangle(
                        (xsta - radius / 2, ysta - radius / 2),
                        radius, radius,
                        color=self._configuration['linecolor'],
                        fill=False,
                        linewidth=self._configuration['linewidth'],
                        linestyle=self._configuration['linestyle'])
                    earthmap.ax.add_artist(circle)
                # display a dot at station coordinates
                point = earthmap.scatter(
                    xsta,
                    ysta,
                    self._configuration['marker size'],
                    marker=self._configuration['marker'],
                    color=self._configuration['marker color'])
                # add station tag, position is computed from plot size and
                # desired relative position wrt. station coordinates
                plot_width = self._parent.get_width()
                plot_height = self._parent.get_height()
                x_offset = plot_width / 200
                y_offset = plot_height / 200
                position = self._configuration['tagpos']
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
                else:
                    # default will be upright
                    valign = 'bottom'
                    halign = 'left'
                tag = earthmap.ax.text(
                    s=self._configuration['tag'],
                    x=xsta + x_offset,
                    y=ysta + y_offset,
                    va=valign,
                    ha=halign,
                    fontsize=self._configuration['fontsize'])
                # store references to plotted elements
                # (point, tag and BPE circle)
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
            self._configuration.update(config)
            # check and convert to float
            self._configuration['longitude'] = float(self._configuration['longitude'])
            self._configuration['latitude'] = float(self._configuration['latitude'])
            self._configuration['marker size'] = float(self._configuration['marker size'])
            self._configuration['fontsize'] = float(self._configuration['fontsize'])
            self._configuration['bpe'] = float(self._configuration['bpe'])
            self._configuration['linewidth'] = float(self._configuration['linewidth'])
        # return merged dictionary
        return self._configuration
    # end of method configure

# Other functions and methods
# ==================================================================================================
    def visible(self, earthmap):
        """States if station is visible in the map frame.
        """
        # get coordinates of station in earth plot frame
        lon = self._configuration['longitude']
        lat = self._configuration['latitude']
        xsta, ysta = earthmap(lon, lat)
        return earthmap.llcrnrx < xsta and \
            xsta < earthmap.urcrnrx and \
            earthmap.llcrnry < ysta and \
            ysta < earthmap.urcrnry
    # end of function visible

# end of class Station
# ==================================================================================================


class Dialog(QFileDialog):
    """Customised dialog box to open a file and load station list.
    """

    def __init__(self, station=None):
        # Parent constructor
        super().__init__()

        # Add Title to the widget
        self.setWindowTitle('Add stations from file')

        # Dialog is modal to avoid reentry and weird behaviour
        self.setModal(True)
        self.show()
    # end of constructor

# End of Customized QDialog StationDialog


class StationControler():
    """Enable control over a Station instance.
    """

    def __init__(self, parent, station):
        """Constructor of class StationControler. It takes as parameter
        a reference to an instance of class Station.
        """
        # reference of the parent EarthPlot
        self._earthplot = parent

        # reference of the Central Widget
        self._centralwidget = None
        if parent is not None:
            self._centralwidget = parent.get_centralwidget()

        # Reference to the Main Window
        self._app = None
        if self._centralwidget is not None:
            self._app = self._centralwidget.parent()

        # store station reference
        self._station = station

        # Store sub menu
        self.stn_menu = self.add_menu_items(station.configure()['tag'])

    def add_menu_items(self, station_key):
        """Add Pattern menu elements to exploit current pattern.
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(station_key={station_key})').format(
                station_key=station_key
        ))
        # get Pattern menu reference and add sub menu for current pattern
        stns_menu = self._app.getmenuitem('Misc.>Stations').menu()
        stn_name = self._station.configure()['name']
        stn_menu = stns_menu.addMenu(stn_name)
        # add Remove action
        rem_action = QAction('Remove', self._app)
        rem_action.triggered.connect(self.remove_station)
        stn_menu.addAction(rem_action)
        # add Edit action
        edit_action = QAction('Edit', self._app)
        stn_menu.addAction(edit_action)
        edit_action.triggered.connect(self.edit_station)

        # return submenu
        return stn_menu

    def remove_station(self):
        # remove menu
        menu = self.stn_menu
        menu_action = menu.menuAction()
        menu.parent().removeAction(menu_action)

        # remove item from plot
        self._earthplot._stations.remove(self)

        # redraw
        self.clearplot()
        self._earthplot.draw()

    def edit_station(self):
        dialog = StationWidget(self._station)
        menu = self.stn_menu
        menu_action = menu.menuAction()
        menu_action.setText(self._station.configure()['name'])

    def plot(self):
        self._station.plot()

    def clearplot(self):
        self._station.clearplot()

    def configure(self, config=None):
        if config is not None:
            self._station.configure(config)
        return self._station.configure(config)


class StationWidget(QDialog):
    """This widget is used to configure a station object.
    """

    def __init__(self, station: Station):
        """Create a dedicated widget from a Station instance.
        """

        # Call to parent constructor
        super().__init__()

        # store reference to station instance and config dictionary
        self._station = station
        self._stationconfig = station.configure()

        # build the widget
        self.build_widget(station)
        self.conf_widget(station)

        # connect the buttons
        self.ok_btn.clicked.connect(lambda: self.ok_close(self._station))
        self.cancel_btn.clicked.connect(self.close)

        # display the widget
        self.show()
        self.exec_()

    def build_widget(self, station=None):
        """Build and initialize widget from station config"""

        layout = QGridLayout(self)

        self.visible_chk = QCheckBox(parent=self, text='Visible')
        self.visible_chk.setChecked(True)
        layout.addWidget(self.visible_chk, 1, 1)
        self.name_lbl = QLabel(parent=self, text='Name')
        self.name_fld = QLineEdit(parent=self)
        layout.addWidget(self.name_lbl, 2, 1)
        layout.addWidget(self.name_fld, 2, 2)
        self.tag_lbl = QLabel(parent=self, text='Tag')
        self.tag_fld = QLineEdit(parent=self)
        layout.addWidget(self.tag_lbl, 3, 1)
        layout.addWidget(self.tag_fld, 3, 2)
        self.tag_pos_lbl = QLabel(parent=self, text='Tag position')
        self.tag_pos_cmb = QComboBox(parent=self)
        self.tag_pos_cmb.addItems(
            ['upleft',
             'upright',
             'downleft',
             'downright'])
        layout.addWidget(self.tag_pos_lbl, 4, 1)
        layout.addWidget(self.tag_pos_cmb, 4, 2)
        self.longitude_lbl = QLabel(parent=self, text='Longitude')
        self.longitude_fld = QLineEdit(parent=self, text='0.0')
        layout.addWidget(self.longitude_lbl, 5, 1)
        layout.addWidget(self.longitude_fld, 5, 2)
        self.latitude_lbl = QLabel(parent=self, text='Latitude')
        self.latitude_fld = QLineEdit(parent=self, text='0.0')
        layout.addWidget(self.latitude_lbl, 6, 1)
        layout.addWidget(self.latitude_fld, 6, 2)
        self.bpe_chk = QCheckBox(parent=self, text='BPE circle')
        self.bpe_fld = QLineEdit(parent=self, text='0.25')
        layout.addWidget(self.bpe_chk, 7, 1)
        layout.addWidget(self.bpe_fld, 7, 2)

        # line and marker button
        self.marker_btn = QPushButton('Marker', self)
        self.marker_btn.setEnabled(True)
        layout.addWidget(self.marker_btn, 8, 1)
        self.marker_btn.clicked.connect(self.setmarker)

        # Ok/Cancel buttons
        self.ok_btn = QPushButton(parent=self, text='OK')
        self.cancel_btn = QPushButton(parent=self, text='Cancel')
        layout.addWidget(self.ok_btn, 9, 1)
        layout.addWidget(self.cancel_btn, 9, 2)

    def conf_widget(self, station=None):
        """Set GUI fields with station values
        """
        if station is not None:
            # Get station conf dictionary
            conf = station.configure()
            # set name and tag
            self.name_fld.setText(conf['name'])
            self.tag_fld.setText(conf['tag'])
            # retrieve visibility status
            self.visible_chk.setChecked(station.set(
                key='visible', fallback=True, dtype=bool))
            # retrieve tag position value and set
            text = station.set(
                key='tagpos', fallback='')
            index = self.tag_pos_cmb.findText(text, QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.tag_pos_cmb.setCurrentIndex(index)
            # set longitude
            self.longitude_fld.setText(
                "{lon:0.2f}".format(lon=station.set(
                    key='longitude', fallback=0.0)))
            # set latitude
            self.latitude_fld.setText(
                "{lat:0.2f}".format(lat=station.set(
                    key='latitude', fallback=0.0)))
            # set BPE status
            bpe = station.set(key='bpe', fallback=0.0)
            self.bpe_chk.setChecked(bpe != 0.0)
            self.bpe_fld.setText(
                "{bpe:0.2f}".format(bpe=bpe)
            )

    def conf_station(self, station, close=False):
        """Set station dictionary with widget fields value
        """
        if station is not None:
            # Get station conf dictionary
            conf = {}
            # set name and tag
            conf['name'] = self.name_fld.text()
            conf['tag'] = self.tag_fld.text()
            # retrieve visibility status
            conf['visible'] = self.visible_chk.isChecked()
            # retrieve tag position value and set
            conf['tagpos'] = self.tag_pos_cmb.currentText()
            # set longitude
            conf['longitude'] = float(self.longitude_fld.text())
            # set latitude
            conf['latitude'] = float(self.latitude_fld.text())
            # set BPE status
            if self.bpe_chk.isChecked():
                conf['bpe'] = float(self.bpe_fld.text())
            else:
                conf['bpe'] = 0.0
            # merge created dictionary into station dictionary
            station.configure(config=conf)

    def ok_close(self, station):
        # update dictionary
        self.conf_station(station=station)
        # update drawing
        station.clearplot()
        station.plot()
        station._parent.draw()
        self.close()

    def setmarker(self):
        mkrdlg = MarkerDialog(self._station)
        self.setModal(False)
        mkrdlg.setModal(True)
        mkrdlg.exec_()
        self.setModal(True)


# Static methods and functions
# ==================================================================================================
def get_station_from_file(filename: str, earthplot=None):
    """Returns a list of Station created from a text file passed
    to the function.
    """
    # initialize return list
    stations = []
    # open file and read text data
    try:
        file = open(filename, "r")
        # read all lines in a table
        lines = file.readlines()
        # close file
        file.close()

        # split data and add them to Station list
        for line in lines:
            if not line[0] == "#":
                tokens = line.split(',')
                if len(tokens) > 1:
                    name = tokens[0]
                    tag = tokens[1]
                    lon = float(tokens[2])
                    lat = float(tokens[3])
                    tagpos = tokens[4]
                    beam_point_err = float(tokens[5])
                    station = Station(parent=earthplot)
                    station.configure({'longitude': lon,
                                       'latitude': lat,
                                       'tag': tag,
                                       'name': name,
                                       'bpe': beam_point_err,
                                       'tagpos': tagpos})
                    if earthplot is not None:
                        stncontroler = StationControler(parent=earthplot,
                                                        station=station)
                        # stncontroler.add_menu_items(station.configure()['tag'])
                        stations.append(stncontroler)
                    else:
                        stations.append(station)

    except FileNotFoundError:
        print('station.py: {} not found'.format(filename))

    return stations
# end of function get_station_from_file

# end of module
