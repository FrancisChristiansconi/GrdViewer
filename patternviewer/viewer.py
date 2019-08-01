"""This module defines the viewer position.
"""


from PyQt5.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QHBoxLayout, \
    QPushButton, QLabel
import PyQt5.QtCore as QtCore

# import constant file
import patternviewer.constant as cst


class Viewer(object):
    """Viewer represents position of observer of the projection.
    """

    # Default constructor for Viewer
    def __init__(self, lon=0.0, lat=0.0, alt=35786000.0):
        self._longitude_deg = lon
        self._latitude_deg = lat
        self._altitude_m = alt
    # End of Constructor

    def longitude(self, lon: float = None) -> float:
        """Get/set for attribute _longitude_deg.
        """
        if lon is not None:
            self._longitude_deg = lon
        return self._longitude_deg
    # end of longitude function

    def latitude(self, lat: float = None) -> float:
        """Get/set for attribute _latitude_deg.
        """
        if lat is not None:
            self._latitude_deg = lat
        return self._latitude_deg
    # end of latitude function

    def altitude(self, alt: float = None) -> float:
        """Get/set for attribute _altitude_m.
        """
        if alt is not None:
            self._altitude_m = alt
        return self._altitude_m
    # end of altitude function

    def set(self, lon: float = None, lat: float = None, alt: float = None):
        """Set all three LLA coordinates at once.
        """
        if lon is not None:
            self._longitude_deg = lon
        if lat is not None:
            self._latitude_deg = lat
        if alt is not None:
            self._altitude_m = alt
    # end of set function

# end of class Viewer


class ViewerPosDialog(QDialog):
    """This class implement a customised dialog box to set the viewer
    passed to the constructor.
    """

    def __init__(self, Viewer: Viewer, parent=None):
        """Default constructor of the class.
        """

        # Parent constructor
        super().__init__()

        # Store parent ref
        self.parent = parent

        # store reference to Viewer object
        self._viewerpos = Viewer

        # Add Title to the widget
        self.setWindowTitle('Viewer position')
        self.setMinimumSize(100, 50)

        # Add field, label and alignment
        self._lon_field = QLineEdit(str(Viewer.longitude()), parent=self)
        self._lat_field = QLineEdit(str(Viewer.latitude()), parent=self)
        self._alt_field = QLineEdit(str(Viewer.altitude()), parent=self)
        self._lon_label = QLabel('Longitude (deg)', parent=self)
        self._lat_label = QLabel('Latitude (deg)', parent=self)
        self._alt_label = QLabel('Altitude (m)', parent=self)
        self._lon_label.setAlignment(QtCore.Qt.AlignRight |
                                     QtCore.Qt.AlignVCenter)
        self._lat_label.setAlignment(QtCore.Qt.AlignRight |
                                     QtCore.Qt.AlignVCenter)
        self._alt_label.setAlignment(QtCore.Qt.AlignRight |
                                     QtCore.Qt.AlignVCenter)

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

    # Update Viewer fields with dialog box fields values

    def update_viewerpos(self):
        if self._alt_field.text().upper() == 'GEO':
            alt = cst.ALTGEO
        else:
            alt = float(self._alt_field.text())
        self._viewerpos.set(float(self._lon_field.text()),
                            float(self._lat_field.text()),
                            alt)
        self.parent.draw_elements()
        self.close()

# End of class ViewerPosDialog
