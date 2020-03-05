"""This module defines the viewer position.
"""

import sys
import logging

from PyQt5.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QHBoxLayout, \
    QPushButton, QLabel
import PyQt5.QtCore as QtCore

# import constant file
import patternviewer.constant as cst


class Viewer(object):
    """Viewer represents position of observer of the projection.
    """

    # Default constructor for Viewer
    def __init__(self, lon=0.0, lat=0.0, alt=35786000.0, config=None):
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(lon={lon}, lat={lat}, alt={alt}, config={config})').format(
                lon=lon,
                lat=lat,
                alt=alt,
                config=config
        ))
        self._config = {}
        self.configure({
            'longitude': lon,
            'latitude': lat,
            'altitude': alt
        })
        self.configure(config)
    # End of Constructor

    def longitude(self, lon: float = None):
        """Get/set for attribute _longitude_deg.
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(lon={lon})').format(
                lon=lon
        ))
        if lon is not None:
            self._config['longitude'] = lon
        return self._config['longitude']
    # end of longitude function

    def latitude(self, lat: float = None):
        """Get/set for attribute _latitude_deg.
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(lat={lat})').format(
                lat=lat
        ))
        if lat is not None:
            self._config['latitude'] = lat
        return self._config['latitude']
    # end of latitude function

    def altitude(self, alt: float = None):
        """Get/set for attribute _altitude_m.
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(alt={alt})').format(
                alt=alt
        ))
        if alt is not None:
            self._config['altitude'] = alt
        return self._config['altitude']
    # end of altitude function

    def set(self, lon: float = None, lat: float = None, alt: float = None):
        """Set all three LLA coordinates at once.
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(lon={alt},'
            + 'lat={lat},'
            + 'alt={alt})').format(
                lon=lon,
                lat=lat,
                alt=alt
        ))
        if lon is not None:
            self._config['longitude'] = lon
        if lat is not None:
            self._config['latitude'] = lat
        if alt is not None:
            self._config['altitude'] = alt
    # end of set function

    def configure(self, config=None):
        """Properly configure instance.
        Make sure none-string values are the right type.
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(config={config})'
        ).format(
            config=config
        ))
        if config is not None:
            self._config.update(config)
            self._config['longitude'] = float(self._config['longitude'])
            self._config['latitude'] = float(self._config['latitude'])
            self._config['altitude'] = float(self._config['altitude'])
        return self._config
    # end of configure function

# end of class Viewer


class ViewerPosDialog(QDialog):
    """This class implement a customised dialog box to set the viewer
    passed to the constructor.
    """

    def __init__(self, viewer: Viewer, parent=None):
        """Default constructor of the class.
        """

        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(viewer={viewer},'
            + 'parent={parent})'
        ).format(
            viewer=viewer,
            parent=parent
        ))

        # Parent constructor
        super().__init__()

        # Store parent ref
        self.parent = parent

        # store reference to Viewer object
        self._viewerpos = viewer

        # Add Title to the widget
        self.setWindowTitle('Viewer position')
        self.setMinimumSize(100, 50)

        # Add field, label and alignment
        self._lon_field = QLineEdit(str(viewer.longitude()), parent=self)
        self._lat_field = QLineEdit(str(viewer.latitude()), parent=self)
        self._alt_field = QLineEdit(str(viewer.altitude()), parent=self)
        self._lon_label = QLabel('Longitude (deg)', parent=self)
        self._lat_label = QLabel('Latitude (deg)', parent=self)
        self._alt_label = QLabel('Altitude (m)', parent=self)
        self._lon_label.setAlignment(QtCore.Qt.AlignRight
                                     | QtCore.Qt.AlignVCenter)
        self._lat_label.setAlignment(QtCore.Qt.AlignRight
                                     | QtCore.Qt.AlignVCenter)
        self._alt_label.setAlignment(QtCore.Qt.AlignRight
                                     | QtCore.Qt.AlignVCenter)

        # Add Ok/Cancel buttons
        ok_button = QPushButton('OK', self)
        cancel_button = QPushButton('Cancel', self)

        # Create Vertical layout
        verticalbox = QVBoxLayout(self)

        # Create longitude line layout
        longitudebox = QHBoxLayout(None)
        longitudebox.addWidget(self._lon_label)
        longitudebox.addStretch(1)
        longitudebox.addWidget(self._lon_field)
        # Create latitude line layout
        latitudebox = QHBoxLayout(None)
        latitudebox.addWidget(self._lat_label)
        latitudebox.addStretch(1)
        latitudebox.addWidget(self._lat_field)
        # Create altitude line layout
        altitudebox = QHBoxLayout(None)
        altitudebox.addWidget(self._alt_label)
        altitudebox.addStretch(1)
        altitudebox.addWidget(self._alt_field)

        # Place Ok/Cancel button in an horizontal box layout
        buttonbox = QHBoxLayout(None)
        buttonbox.addStretch(1)
        buttonbox.addWidget(ok_button)
        buttonbox.addWidget(cancel_button)

        # put the button layout in the Vertical Layout
        verticalbox.addLayout(longitudebox)
        verticalbox.addLayout(latitudebox)
        verticalbox.addLayout(altitudebox)
        verticalbox.addLayout(buttonbox)

        # set dialog box layout
        self.setLayout(verticalbox)

        # connect buttons to actions
        ok_button.clicked.connect(self.update_viewerpos)
        cancel_button.clicked.connect(self.close)
        # Dialog is modal to avoid reentry and weird behaviour
        self.setModal(True)
        self.show()
    # end of function __init__

    # Update Viewer fields with dialog box fields values

    def update_viewerpos(self):
        """Update the coordinates of the viewer from the widget values.
        """
        logging.debug(sys._getframe().f_code.co_filename.split('\\')[-1]
                      + ':' + sys._getframe().f_code.co_name)
        if self._alt_field.text().upper() == 'GEO':
            alt = cst.ALTGEO
        else:
            alt = float(self._alt_field.text())
        self._viewerpos.set(float(self._lon_field.text()),
                            float(self._lat_field.text()),
                            alt)
        self.parent.draw_elements()
        self.close()
    # end of method update_viewerpos

# End of class ViewerPosDialog
