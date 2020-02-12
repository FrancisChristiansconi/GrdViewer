"""This module helps dealing with elevation contour display.
"""
# Imports of third party modules
# PyQt5 widgets import
from PyQt5.QtWidgets import QDialog, QLineEdit, \
    QHBoxLayout, QVBoxLayout, QPushButton, QLabel
import numpy as np

# import of local modules
# Constants
import patternviewer.constant as cst
# Astract  mother class Element
from patternviewer.element.element import Element
from patternviewer.element.linedialog import LineDialog
import patternviewer.utils as utils

# Classes


class Elevation(Element):
    """This class defines an elevation angle.
    """

    def __init__(self, parent=None, config=None):
        self._parent = parent
        self._config = {}
        self._config['linewidths'] = 0.3
        self._config['linestyles'] = 'dashed'
        self._config['colors'] = 'k'
        self.configure(config)
        self._plot = None

    def elevation(self, stalon, stalat):
        """Compute elevation of spacecraft seen from a station on the ground.
        """
        utils.trace('in')
        # compute phi
        phi = np.arccos(
            np.cos(cst.DEG2RAD * stalat)
            * np.cos(cst.DEG2RAD
                     * (self._parent._viewer.longitude() - stalon)))

        # compute elevation
        elev = np.reshape(
            [90 if phi == 0 else cst.RAD2DEG * np.arctan(
                (np.cos(phi) - (cst.EARTH_RAD_EQUATOR_M
                 / (cst.EARTH_RAD_EQUATOR_M
                    + self._parent._viewer.altitude())))
                / np.sin(phi)) for phi in phi.flatten()],
            phi.shape)

        # remove station out of view
        elev = np.where(np.absolute(
            stalon - self._parent._viewer.longitude()) < 90, elev, -1)

        utils.trace('out')
        # Return vector
        return elev
    # end of function elevation

# implementation of Element abstract methods
    def plot(self):
        utils.trace('in')
        emap = self._parent.get_earthmap()
        # define grid
        nx = 200
        ny = 200
        xvec = np.linspace(emap.xmin, emap.xmax, nx)
        yvec = np.linspace(emap.ymin, emap.ymax, ny)
        xgrid, ygrid = np.meshgrid(xvec, yvec)
        longrid, latgrid = emap(xgrid, ygrid, inverse=True)
        # define Elevation matrix
        elevgrid = self.elevation(longrid, latgrid)
        self._plot = emap.contour(xgrid, ygrid, elevgrid,
                                  [self._config['elevation']],
                                  colors=self._config['colors'],
                                  linestyles=self._config['linestyles'],
                                  linewidths=self._config['linewidths'])
        utils.trace('out')
        return self._plot
    # end of plot

    def clearplot(self):
        if self._plot is not None:
            for element in self._plot.collections:
                try:
                    element.remove()
                except ValueError:
                    print(element)

    def configure(self, config=None):
        if config is not None:
            self._config.update(config)
            self._config['linewidths'] = self.set(
                self._config, 'linewidths', float)
        return self._config


# end of class Elevation

class ElevDialog(QDialog):
    """This class defines a customised dialog box to set an elevation
    angle to display on the parent's Earth plot.
    """

    def __init__(self, parent=None):
        # Parent constructor
        super().__init__()

        self._eplt = parent._earthplot

        # Add Title to the widget
        self.setWindowTitle('Add/Remove Elevation contour')
        self.setMinimumSize(100, 50)

        # Everything in a vertical Layout
        vbox = QVBoxLayout(self)

        # Add longitude field
        self.labelelev = QLabel('Elevation (deg)', parent=self)
        self.fieldelev = QLineEdit('10', parent=self)
        hboxelev = QHBoxLayout(None)
        hboxelev.addWidget(self.labelelev)
        hboxelev.addStretch(1)
        hboxelev.addWidget(self.fieldelev)
        vbox.addLayout(hboxelev)

        # Add Ok/Cancel buttons
        addbutton = QPushButton('Add', self)
        rembutton = QPushButton('Remove', self)
        cancelbutton = QPushButton('Cancel', self)

        # Place Ok/Cancel button in an horizontal box layout
        hboxbutton = QHBoxLayout()
        hboxbutton.addStretch(1)
        hboxbutton.addWidget(addbutton)
        hboxbutton.addWidget(rembutton)
        hboxbutton.addWidget(cancelbutton)

        # put the button layout in the Vertical Layout
        vbox.addLayout(hboxbutton)

        # set dialog box layout
        self.setLayout(vbox)

        # connect buttons to actions
        addbutton.clicked.connect(self.addcontour)
        rembutton.clicked.connect(self.removecontour)
        cancelbutton.clicked.connect(self.close)

        # Dialog is modal to avoid reentry and weird behaviour
        self.setModal(True)
        self.show()
    # end of constructor

    def addcontour(self):
        self.close()
        config = {}
        elevationlist = [float(s) for s in self.fieldelev.text().split(',')]
        for elevation_value in elevationlist:
            config['elevation'] = elevation_value
            elevation = Elevation(parent=self._eplt, config=config)
            dialog = LineDialog(parent=elevation)
            dialog.show()
            dialog.exec_()
            self._eplt._elev['Elev[' + str(elevation_value) + ']'] = elevation
            elevation.plot()
        self._eplt.draw()
        # self._eplt.draw_elements()

    def removecontour(self):
        self.close()
        elevationlist = [float(s) for s in self.fieldelev.text().split(',')]
        for elevation in elevationlist:
            try:
                self._eplt._elev['Elev[' + str(elevation) + ']'].clearplot()
                del self._eplt._elev['Elev[' + str(elevation) + ']']
            except KeyError:
                pass
        self._eplt.draw()
        # self._eplt.draw_elements()
