from PyQt5.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QHBoxLayout, \
                            QPushButton, QLabel
import PyQt5.QtCore as QtCore


# Represent position of observer of the projection
class ViewerPos(object):
    
    # Default constructor for ViewerPos
    def __init__(self, fLonDeg=0.0, fLatDeg=0.0, fAltM=35786000.0):
        self.fLonDeg = fLonDeg
        self.fLatDeg = fLatDeg
        self.fAltM   = fAltM
    # End of Constructor

    def setLon(self, lon):
        self.fLonDeg=lon
    def setLat(self, lat):
        self.fLatDeg=lat
    def setAlt(self, alt):
        self.fAltM=alt
    def set(self, lon, lat, alt):
        self.fLonDeg=lon
        self.fLatDeg=lat
        self.fAltM  =alt
# end of class ViewerPos


# Dialog to set a ViewerPos object
class ViewerPosDialog(QDialog):

    # Default constructor for SetViewerPos
    def __init__(self, vPos: ViewerPos, parent=None):
        # Parent constructor
        super().__init__()

        # Store parent ref
        self.parent=parent

        # store reference to ViewerPos object
        self.vPos = vPos

         # Add Title to the widget
        self.setWindowTitle('Viewer position')
        self.setMinimumSize(100, 50)

        # Add field, label and alignment
        self.fieldLon = QLineEdit(str(vPos.fLonDeg), parent=self)
        self.fieldLat = QLineEdit(str(vPos.fLatDeg), parent=self)
        self.fieldAlt = QLineEdit(str(vPos.fAltM),   parent=self)
        self.labelLon = QLabel('Longitude (deg)', parent=self)
        self.labelLat = QLabel('Latitude (deg)',  parent=self)
        self.labelAlt = QLabel('Altitude (m)',    parent=self)
        self.labelLon.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.labelLat.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.labelAlt.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        # Add Ok/Cancel buttons
        okButton = QPushButton('OK',self)
        cancelButton = QPushButton('Cancel',self)

        # Create Vertical layout 
        vBox = QVBoxLayout(self)

        # Create longitude line layout
        longitudeBox = QHBoxLayout(None)
        longitudeBox.addWidget(self.labelLon)
        longitudeBox.addStretch(1)
        longitudeBox.addWidget(self.fieldLon)
        # Create latitude line layout
        latitudeBox = QHBoxLayout(None)
        latitudeBox.addWidget(self.labelLat)
        latitudeBox.addStretch(1)
        latitudeBox.addWidget(self.fieldLat)
        # Create altitude line layout
        altitudeBox = QHBoxLayout(None)
        altitudeBox.addWidget(self.labelAlt)
        altitudeBox.addStretch(1)
        altitudeBox.addWidget(self.fieldAlt)
        
        # Place Ok/Cancel button in an horizontal box layout
        buttonBox = QHBoxLayout(None)
        buttonBox.addStretch(1)
        buttonBox.addWidget(okButton)
        buttonBox.addWidget(cancelButton)

        # put the button layout in the Vertical Layout
        vBox.addLayout(longitudeBox)
        vBox.addLayout(latitudeBox)
        vBox.addLayout(altitudeBox)
        vBox.addLayout(buttonBox)

        # set dialog box layout
        self.setLayout(vBox) 

        # connect buttons to actions
        okButton.clicked.connect(self.updateViewerPos)
        cancelButton.clicked.connect(self.close)
        # Dialog is modal to avoid reentry and weird behaviour
        self.setModal(True)
        self.show()



    # Update vPos fields with dialog box fields values 
    def updateViewerPos(self):
        self.vPos.set(float(self.fieldLon.text()), \
                      float(self.fieldLat.text()), \
                      float(self.fieldAlt.text()))
        self.parent.draw()
        self.close()

# End of class ViewerPosDialog