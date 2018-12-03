from PyQt5.QtWidgets import QDialog, QLineEdit, QGridLayout, \
                            QPushButton, QLabel
import PyQt5.QtCore as QtCore

class Zoom(object):

    # Zoom class constructor
    def __init__(self, proj='geos', geo=(-9.0,-9.0,9.0,9.0), merc=(-180.0, -85.0, 180.0, -85.0)):
        self._projection = proj
        self.fLowLeftAz    = geo[0]  # deg Azimuth
        self.fLowLeftEl    = geo[1]  # deg Elevation
        self.fUpRightAz    = geo[2]  # deg Azimuth
        self.fUpRightEl    = geo[3]  # deg Elevation
        self.fLowLeftLon   = merc[0] # deg Longitude
        self.fLowLeftLat   = merc[1] # deg Latitude
        self.fUpRightLon   = merc[2] # deg Longitude
        self.fUpRightLat   = merc[3] # deg Latitude
# End of 


class ZoomDialog(QDialog):

    # ZoomDialog class constructor
    def __init__(self, zoom: Zoom, parent=None):
        # Parent constructor
        super().__init__()

        # Link to parent's Earth Plot
        self.earth_plot = parent

        self.zoom = zoom

        # Add Title to the widget
        self.setWindowTitle('Zoom')
        self.setMinimumSize(70, 50)
        
        # Add labels
        self.viewLblLowLeftX = QLabel(parent=self)
        self.viewLblLowLeftY = QLabel(parent=self)
        self.viewLblUpRightX = QLabel(parent=self)
        self.viewLblUpRightY = QLabel(parent=self)
        self.viewLblLowLeftX.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.viewLblLowLeftY.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.viewLblUpRightX.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.viewLblUpRightY.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        # Add field
        self.viewSetLowLeftX = QLineEdit(parent=self)
        self.viewSetLowLeftY = QLineEdit(parent=self)
        self.viewSetUpRightX = QLineEdit(parent=self)
        self.viewSetUpRightY = QLineEdit(parent=self)
        if self.earth_plot._projection == 'geos':
            self.viewLblLowLeftX.setText('min. Az')
            self.viewLblLowLeftY.setText('min. El')
            self.viewLblUpRightX.setText('max. Az')
            self.viewLblUpRightY.setText('max. El')
            self.viewSetLowLeftX.setText(str(self.zoom.fLowLeftAz))
            self.viewSetLowLeftY.setText(str(self.zoom.fLowLeftEl))
            self.viewSetUpRightX.setText(str(self.zoom.fUpRightAz))
            self.viewSetUpRightY.setText(str(self.zoom.fUpRightEl))
        elif self.earth_plot._projection == 'merc':
            self.viewLblLowLeftX.setText('min. Lon')
            self.viewLblLowLeftY.setText('min. Lat')
            self.viewLblUpRightX.setText('max. Lon')
            self.viewLblUpRightY.setText('max. Lat')
            self.viewSetLowLeftX.setText(str(self.zoom.fLowLeftLon))
            self.viewSetLowLeftY.setText(str(self.zoom.fLowLeftLat))
            self.viewSetUpRightX.setText(str(self.zoom.fUpRightLon))
            self.viewSetUpRightY.setText(str(self.zoom.fUpRightLat))


        # Add a vertical box layout
        gbox = QGridLayout(self)

        # Line 1
        gbox.addWidget(self.viewLblLowLeftX, 1, 1)
        gbox.addWidget(self.viewSetLowLeftX, 1, 2)
        gbox.addWidget(self.viewLblLowLeftY, 1, 3)
        gbox.addWidget(self.viewSetLowLeftY, 1, 4)
        # Line 2
        gbox.addWidget(self.viewLblUpRightX, 2, 1)
        gbox.addWidget(self.viewSetUpRightX, 2, 2)
        gbox.addWidget(self.viewLblUpRightY, 2, 3)
        gbox.addWidget(self.viewSetUpRightY, 2, 4)
        
        # Add Ok/Cancel buttons
        okButton = QPushButton('OK',self)
        cancelButton = QPushButton('Cancel',self)

        # line 3
        gbox.addWidget(okButton, 3, 3)
        gbox.addWidget(cancelButton, 3, 4)

        # connect buttons to actions
        okButton.clicked.connect(self.updatezoom)
        cancelButton.clicked.connect(self.close)
        
        # Dialog is modal to avoid reentry and weird behaviour
        self.setModal(True)
        self.show()
    # end of constructor

    def updatezoom(self):
        if self.earth_plot._projection == 'geos':
            self.zoom.fLowLeftAz = float(self.viewSetLowLeftX.text())
            self.zoom.fLowLeftEl = float(self.viewSetLowLeftY.text())
            self.zoom.fUpRightAz = float(self.viewSetUpRightX.text())
            self.zoom.fUpRightEl = float(self.viewSetUpRightY.text())
        elif self.earth_plot._projection == 'merc':
            self.zoom.fLowLeftLon = float(self.viewSetLowLeftX.text())
            self.zoom.fLowLeftLat = float(self.viewSetLowLeftY.text())
            self.zoom.fUpRightLon = float(self.viewSetUpRightX.text())
            self.zoom.fUpRightLat = float(self.viewSetUpRightY.text())
        self.earth_plot.updatezoom()
        self.earth_plot.draw()
        self.close()
    # end of method updatezoom
# end of class ZoomDialog