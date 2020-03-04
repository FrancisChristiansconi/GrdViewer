"""This module deals with zoom capability of the application.
"""
# imports
import logging
import sys

from PyQt5.QtWidgets import QDialog, QLineEdit, QGridLayout, \
    QPushButton, QLabel
import PyQt5.QtCore as QtCore


class Zoom(object):
    """This class represents the current zoom of the earth plot.
    """

    def __init__(self, proj='nsper', nsper=(-9.0, -9.0, 9.0, 9.0),
                 cyl=(-180.0, -85.0, 180.0, 85.0), config=None):
        """Default constructor for Zoom objects.
        Works if zoom defined in AzEl of LL coordinates.
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(proj={proj},'
            + 'nsper={nsper},'
            + 'cyl={cyl},'
            + 'config={config})').format(
                proj=proj,
                nsper=nsper,
                cyl=cyl,
                config=config
        ))
        self._config = {}
        self._config['projection'] = proj         # projection
        self._config['min azimuth'] = nsper[0]    # deg Azimuth
        self._config['min elevation'] = nsper[1]  # deg Elevation
        self._config['max azimuth'] = nsper[2]    # deg Azimuth
        self._config['max elevation'] = nsper[3]  # deg Elevation
        self._config['min longitude'] = cyl[0]    # deg Longitude
        self._config['min latitude'] = cyl[1]     # deg Latitude
        self._config['max longitude'] = cyl[2]    # deg Longitude
        self._config['max latitude'] = cyl[3]     # deg Latitude
        self.configure(config)
    # end of constructor

    def configure(self, config=None):
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(config={config})').format(
                config=config
        ))
        if config is not None:
            self._config.update(config)
            self._config['min azimuth'] = float(
                self._config['min azimuth'])
            self._config['min elevation'] = float(
                self._config['min elevation'])
            self._config['max azimuth'] = float(
                self._config['max azimuth'])
            self._config['max elevation'] = float(
                self._config['max elevation'])
            self._config['min longitude'] = float(
                self._config['min longitude'])
            self._config['min latitude'] = float(
                self._config['min latitude'])
            self._config['max longitude'] = float(
                self._config['max longitude'])
            self._config['max latitude'] = float(
                self._config['max latitude'])
        return self._config

    def min_azimuth(self, az=None):
        if az is not None:
            self._config['min azimuth'] = az
        return self._config['min azimuth']

    def max_azimuth(self, az=None):
        if az is not None:
            self._config['max azimuth'] = az
        return self._config['max azimuth']

    def min_elevation(self, el=None):
        if el is not None:
            self._config['min elevation'] = el
        return self._config['min elevation']

    def max_elevation(self, el=None):
        if el is not None:
            self._config['maxe levation'] = el
        return self._config['max elevation']

    def min_longitude(self, lon=None):
        if lon is not None:
            self._config['min longitude'] = lon
        return self._config['min longitude']

    def max_longitude(self, lon=None):
        if lon is not None:
            self._config['max longitude'] = lon
        return self._config['max longitude']

    def min_latitude(self, lat=None):
        if lat is not None:
            self._config['min latitude'] = lat
        return self._config['min latitude']

    def max_latitude(self, lat=None):
        if lat is not None:
            self._config['max latitude'] = lat
        return self._config['max latitude']

# End of class Zoom


class ZoomDialog(QDialog):
    """Customized dialog box to set zoom for the earth plot.
    """

    def __init__(self, zoom: Zoom, parent=None):
        """ZoomDialog class constructor.
        """
        # Parent constructor
        super().__init__()

        # Link to parent's Earth Plot
        self.earth_plot = parent

        self._zoom = zoom

        # Add Title to the widget
        self.setWindowTitle('Zoom')
        self.setMinimumSize(70, 50)

        # Add labels
        min_x_label = QLabel(parent=self)
        min_y_label = QLabel(parent=self)
        max_x_label = QLabel(parent=self)
        max_y_label = QLabel(parent=self)
        min_x_label.setAlignment(QtCore.Qt.AlignRight
                                 | QtCore.Qt.AlignVCenter)
        min_y_label.setAlignment(QtCore.Qt.AlignRight
                                 | QtCore.Qt.AlignVCenter)
        max_x_label.setAlignment(QtCore.Qt.AlignRight
                                 | QtCore.Qt.AlignVCenter)
        max_y_label.setAlignment(QtCore.Qt.AlignRight
                                 | QtCore.Qt.AlignVCenter)
        # Add field
        self.min_x_field = QLineEdit(parent=self)
        self.min_y_field = QLineEdit(parent=self)
        self.max_x_field = QLineEdit(parent=self)
        self.max_y_field = QLineEdit(parent=self)
        if self.earth_plot.projection() == 'nsper':
            min_x_label.setText('min. Az')
            min_y_label.setText('min. El')
            max_x_label.setText('max. Az')
            max_y_label.setText('max. El')
            self.min_x_field.setText(str(self._zoom.min_azimuth()))
            self.min_y_field.setText(str(self._zoom.min_elevation()))
            self.max_x_field.setText(str(self._zoom.max_azimuth()))
            self.max_y_field.setText(str(self._zoom.max_elevation()))
        elif self.earth_plot.projection() == 'cyl':
            min_x_label.setText('min. Lon')
            min_y_label.setText('min. Lat')
            max_x_label.setText('max. Lon')
            max_y_label.setText('max. Lat')
            self.min_x_field.setText(str(self._zoom.min_longitude()))
            self.min_y_field.setText(str(self._zoom.min_latitude()))
            self.max_x_field.setText(str(self._zoom.max_longitude()))
            self.max_y_field.setText(str(self._zoom.max_latitude()))

        # Add a vertical box layout
        gridbox = QGridLayout(self)

        # Line 1
        gridbox.addWidget(min_x_label, 1, 1)
        gridbox.addWidget(self.min_x_field, 1, 2)
        gridbox.addWidget(max_x_label, 1, 3)
        gridbox.addWidget(self.max_x_field, 1, 4)
        # Line 2
        gridbox.addWidget(min_y_label, 2, 1)
        gridbox.addWidget(self.min_y_field, 2, 2)
        gridbox.addWidget(max_y_label, 2, 3)
        gridbox.addWidget(self.max_y_field, 2, 4)

        # Add Ok/Cancel buttons
        resetbutton = QPushButton('Reset', self)
        okbutton = QPushButton('OK', self)
        cancelbutton = QPushButton('Cancel', self)

        # line 3
        gridbox.addWidget(resetbutton, 3, 2)
        gridbox.addWidget(okbutton, 3, 3)
        gridbox.addWidget(cancelbutton, 3, 4)

        # connect buttons to actions
        resetbutton.clicked.connect(self.reset)
        okbutton.clicked.connect(self.updatezoom)
        cancelbutton.clicked.connect(self.close)

        # Dialog is modal to avoid reentry and weird behaviour
        self.setModal(True)
        self.show()
    # end of constructor

    def reset(self):
        """This method reset the earth plot zoom to complete Earth
        depending on the projection.
        """
        if self.earth_plot.projection() == 'nsper':
            self.min_x_field.setText(str(-9))
            self.max_x_field.setText(str(9))
            self.min_y_field.setText(str(-9))
            self.max_y_field.setText(str(9))
        elif self.earth_plot.projection() == 'cyl':
            self.min_x_field.setText(str(-180))
            self.max_x_field.setText(str(180))
            self.min_y_field.setText(str(-90))
            self.max_y_field.setText(str(90))
        self.updatezoom()
    # end of method reset

    def updatezoom(self):
        """This method update the earth plot zoom depending on
        the projection.
        """
        if self.earth_plot.projection() == 'nsper':
            self._zoom.configure({
                'min azimuth': float(self.min_x_field.text()),
                'min elevation': float(self.min_y_field.text()),
                'max azimuth': float(self.max_x_field.text()),
                'max elevation': float(self.max_y_field.text())
            })
        elif self.earth_plot.projection() == 'cyl':
            self._zoom.configure({
                'min longitude': float(self.min_x_field.text()),
                'min latitude': float(self.min_y_field.text()),
                'max longitude': float(self.max_x_field.text()),
                'max latitude': float(self.max_y_field.text())
            })
        self.earth_plot.updatezoom()
        self.earth_plot.draw_elements()
        self.earth_plot.draw_axis()
        self.close()
    # end of method updatezoom
# end of class ZoomDialog
