# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 15:56:00 2018

@author: cfrance
"""

# import array/calculus utilities
import numpy as np
# import math basic library
import math
# import interpolation routine from scipy
from scipy import interpolate as interp
# import pyproj for coordinates conversion
import pyproj as prj

# PyQt5 widgets import
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QAction, qApp, QDialog, QLineEdit, \
                            QHBoxLayout, QVBoxLayout, QPushButton, QWidget, QFileDialog, QLabel, \
                            QGridLayout, QCheckBox

# Constants
# Default isolevel to be displayed at patten loading
DEFAULT_ISOLEVEL_DBI = [25, 30, 35, 38, 40]


class Grd(object):
    
    # constructor
    def __init__(self, strFileName=None, bRevertX=False, bRevertY=False, bUseSecondPol=False, alt=None, lon=None, bDisplaySlope=False):

        self.filename = strFileName

        # open file and read text data
        oFile = open(strFileName, "r")
        # read all lines in a table
        tLines = oFile.readlines()
        # close file        
        oFile.close()
        
         # line number
        iLineNb = len(tLines)
        iStart = -1
        
        # map header data into dicData        
        for i in range(iLineNb):
            # detect end of comments
            if tLines[i] == '++++\n':
                iStart = i+1
                break
        
        # header content
        self.iKTYPE  = tLines[iStart].split()[0]
        self.iNSET   = tLines[iStart+1].split()[0]
        self.iICOMP  = tLines[iStart+1].split()[1]
        self.iNCOMP  = tLines[iStart+1].split()[2]
        self.iIGRID  = tLines[iStart+1].split()[3]
        self.iXI     = tLines[iStart+2].split()[0]
        self.iYI     = tLines[iStart+2].split()[1]
        if bRevertX == False:
            self.iXS     = float(tLines[iStart+3].split()[0])
            self.iXE     = float(tLines[iStart+3].split()[2])
        else:   
            self.iXS     = float(tLines[iStart+3].split()[2])
            self.iXE     = float(tLines[iStart+3].split()[0])
        if bRevertY == False:
            self.iYS     = float(tLines[iStart+3].split()[1])
            self.iYE     = float(tLines[iStart+3].split()[3])
        else:
            self.iYS     = float(tLines[iStart+3].split()[3])
            self.iYE     = float(tLines[iStart+3].split()[1])
        self.iNX     = int(tLines[iStart+4].split()[0])
        self.iNY     = int(tLines[iStart+4].split()[1])
        self.iKLIMIT = tLines[iStart+4].split()[2]
        
        # data table reading 
        iRow = 0
        iCol = 0
        self.cGridCo    = np.zeros((self.iNX, self.iNY),dtype=np.complex_)
        self.cGridCross = np.zeros((self.iNX, self.iNY),dtype=np.complex_)
        self.fXCoord    = np.zeros((self.iNX, self.iNY),dtype=np.float_)
        self.fYCoord    = np.zeros((self.iNX, self.iNY),dtype=np.float_)
        
        
        for iLine in range(iStart+5, iLineNb):
            fRealCo    = float(tLines[iLine].split()[0])
            fImagCo    = float(tLines[iLine].split()[1])
            fRealCross = float(tLines[iLine].split()[2])
            fImagCross = float(tLines[iLine].split()[3])
            
            self.cGridCo[iRow,iCol]    = fRealCo + 1j*fImagCo
            self.cGridCross[iRow,iCol] = fRealCross + 1j*fImagCross
            self.fXCoord[iRow,iCol]    = iRow * (self.iXE-self.iXS)/(self.iNX-1)+self.iXS 
            self.fYCoord[iRow,iCol]    = iCol * (self.iYE-self.iYS)/(self.iNY-1)+self.iYS
            
            iRow += 1
            if iRow == self.iNX:
                iRow = 0
                iCol += 1
                
        # initialize some grided data
        if bUseSecondPol:
            self.fCoMag = 20*np.log10(np.absolute(self.cGridCross))
        else:
            self.fCoMag = 20*np.log10(np.absolute(self.cGridCo))
        self.fAzCoord = []
        self.fElCoord = []
        self.fCoGrad = []
        self.fAzCoGrad = []
        self.fElCoGrad = []
        self.interpCoGrad = []
        self.interpAzCoGrad = []
        self.interpElCoGrad = []
        self.interpCo = []

        if not alt == None and not lon == None:
            x = alt * self.Azimuth() * np.pi / 180
            y = alt * self.Elevation() * np.pi / 180
            self.proj = prj.Proj(init='epsg:4326 +proj=geos +h=' + str(alt) + ' +a=6378137.00 +b=6378137.00 +lon_0=' + str(lon) + ' +x_0=0 +y_0=0 +units=meters +no_defs') 
            self.fLonDeg, self.fLatDeg = self.proj(x,y,inverse=True)

        self.fIsolvl = [25,30,35,38,40]
        self.bDisplaySlope = bDisplaySlope
        self.fSlope = [3,20]

    # End of __init__
        
    # return Azimuth grid for this data set
    def Azimuth(self):
        if self.fAzCoord == []:
            self.fAzCoord = -1*np.arctan(self.fXCoord/np.sqrt(1-self.fXCoord**2-self.fYCoord**2))*180/math.pi
        return self.fAzCoord
        
    # return Elevation grid for this data set
    def Elevation(self):
        if self.fElCoord == []:
            self.fElCoord = np.arcsin(self.fYCoord)*180/math.pi
        return self.fElCoord
        
    # return U coordinate grid for this data set
    def UCoordinate(self):
        return self.fXCoord
    
    # return Y coordinate grid for this data set
    def VCoordinate(self):
        return self.fYCoord

    # return minimum Azimuth of the grid
    def MinAz(self):
        return np.min(self.Azimuth())
        
    # return maximum Azimuth of the grid
    def MaxAz(self):
        return np.max(self.Azimuth())
    
    # return minimum Elevation of the grid
    def MinEl(self):
        return np.min(self.Elevation())
    
    # return maximum Elevation of the grid
    def MaxEl(self):
        return np.max(self.Elevation())
        
    # return Co-polarisation pattern
    def Copol(self):
        return self.fCoMag
        
    # return gradient of Co-polarisation pattern
    def Slope(self):
        if self.fCoGrad == []:
            # get gradient of Azimuth coordinate
            [self.fGradAz, A] = np.gradient(self.Azimuth())
            # get gradient of Elevation coordinate
            [A, self.fGradEl] = np.gradient(self.Elevation())
            # get gradient of pattern in Azimuth and Elevation             
            [self.fCoGradX, self.fCoGradY] = np.gradient(self.fCoMag)
            # normalize gradient of pattern in Azimuth direction
            self.fCoGradX /= self.fGradAz
            # normalize gradient of pattern in Elevation direction
            self.fCoGradY /= self.fGradEl
            # RSS the 2 directions gradient in one scalar field
            self.fCoGrad = np.sqrt(self.fCoGradX**2+self.fCoGradY**2)
        return self.fCoGrad
            
    # return gradient of Co-polarisation pattern along Azimuth
    def AzElSlope(self,signed=False):
        if self.fAzCoGrad == []:
            # get gradient of Azimuth coordinate
            [self.fGradAz, A] = np.gradient(self.Azimuth())
            # get gradient of Elevation coordinate
            [A, self.fGradEl] = np.gradient(self.Elevation())
            # get gradient of pattern in Azimuth and Elevation             
            [self.fAzCoGrad, self.fElCoGrad] = np.gradient(self.fCoMag)
            # normalize gradient of pattern in Azimuth direction
            self.fAzCoGrad /= self.fGradAz
            # normalize gradient of pattern in Elevation direction
            self.fElCoGrad /= self.fGradEl
        # use absolute value
        if not signed:
            return {'Az':np.absolute(self.fAzCoGrad), 'El':np.absolute(self.fElCoGrad)}
        else:
            return {'Az':self.fAzCoGrad, 'El':self.fElCoGrad}
        
    # return interpolated value of the pattern
    def InterpCo(self, az, el):
        if self.interpCo == []:
            if self.fXCoord[1,0] > self.fXCoord[0,0] and self.fYCoord[0,1] > self.fYCoord[0,0]:
                self.interpCo = interp.RectBivariateSpline(self.fXCoord[:,0], self.fYCoord[0,:],self.Copol())
            elif self.fXCoord[1,0] < self.fXCoord[0,0] and self.fYCoord[0,1] > self.fYCoord[0,0]:
                self.interpCo = interp.RectBivariateSpline(self.fXCoord[::-1,0], self.fYCoord[0,:],self.Copol()[::-1,:])
            elif self.fXCoord[1,0] < self.fXCoord[0,0] and self.fYCoord[0,1] < self.fYCoord[0,0]:
                self.interpCo = interp.RectBivariateSpline(self.fXCoord[::-1,0], self.fYCoord[0,::-1],self.Copol()[::-1,::-1])
            elif self.fXCoord[1,0] > self.fXCoord[0,0] and self.fYCoord[0,1] < self.fYCoord[0,0]:
                self.interpCo = interp.RectBivariateSpline(self.fXCoord[:,0], self.fYCoord[0,::-1],self.Copol()[:,::-1])
        # transform azel into uv (-1 because azimuth positive toward East)
        u = -1 * np.cos(el * math.pi / 180) * np.sin(az * math.pi / 180)
        v = np.sin(el * math.pi / 180)
        return np.reshape(self.interpCo.ev(u.flatten(),v.flatten()),np.array(az).shape)
        
    # return interpolated value of the pattern
    def InterpSlope(self, az, el):
        # if not yet use interpolation of slopes    
        if self.interpCoGrad == []:
            if self.fXCoord[1,0] > self.fXCoord[0,0] and self.fYCoord[0,1] > self.fYCoord[0,0]:
                self.interpCoGrad = interp.RectBivariateSpline(self.fXCoord[:,0], self.fYCoord[0,:],self.Slope())
            elif self.fXCoord[1,0] < self.fXCoord[0,0] and self.fYCoord[0,1] > self.fYCoord[0,0]:
                self.interpCoGrad = interp.RectBivariateSpline(self.fXCoord[::-1,0], self.fYCoord[0,:],self.Slope()[::-1,:])
            elif self.fXCoord[1,0] < self.fXCoord[0,0] and self.fYCoord[0,1] < self.fYCoord[0,0]:
                self.interpCoGrad = interp.RectBivariateSpline(self.fXCoord[::-1,0], self.fYCoord[0,::-1],self.Slope()[::-1,::-1])
            elif self.fXCoord[1,0] > self.fXCoord[0,0] and self.fYCoord[0,1] < self.fYCoord[0,0]:
                self.interpCoGrad = interp.RectBivariateSpline(self.fXCoord[:,0], self.fYCoord[0,::-1],self.Slope()[:,::-1])
            
        # transform azel into uv (-1 because azimuth positive toward East)
        u = -1 * np.cos(el * math.pi / 180) * np.sin(az * math.pi / 180)
        v = np.sin(el * math.pi / 180)
        # if uv are 2D, flat them
        return np.reshape(self.interpCoGrad.ev(u.flatten(),v.flatten()),np.array(az).shape)
        
    # return interpolated value of the pattern
    def InterpAzElSlope(self, az, el, signed=False):
        # if not yet use interpolation of slopes    
        if self.interpAzCoGrad == []:
            if self.fXCoord[1,0] > self.fXCoord[0,0] and self.fYCoord[0,1] > self.fYCoord[0,0]:
                self.interpAzCoGrad = interp.RectBivariateSpline(self.fXCoord[:,0], self.fYCoord[0,:],self.AzElSlope()['Az'])
                self.interpElCoGrad = interp.RectBivariateSpline(self.fXCoord[:,0], self.fYCoord[0,:],self.AzElSlope()['El'])
            elif self.fXCoord[1,0] < self.fXCoord[0,0] and self.fYCoord[0,1] > self.fYCoord[0,0]:
                self.interpAzCoGrad = interp.RectBivariateSpline(self.fXCoord[::-1,0], self.fYCoord[0,:],self.AzElSlope()['Az'][::-1,:])
                self.interpElCoGrad = interp.RectBivariateSpline(self.fXCoord[::-1,0], self.fYCoord[0,:],self.AzElSlope()['El'][::-1,:])
            elif self.fXCoord[1,0] < self.fXCoord[0,0] and self.fYCoord[0,1] < self.fYCoord[0,0]:
                self.interpAzCoGrad = interp.RectBivariateSpline(self.fXCoord[::-1,0], self.fYCoord[0,::-1],self.AzElSlope()['Az'][::-1,::-1])
                self.interpElCoGrad = interp.RectBivariateSpline(self.fXCoord[::-1,0], self.fYCoord[0,::-1],self.AzElSlope()['El'][::-1,::-1])
            elif self.fXCoord[1,0] > self.fXCoord[0,0] and self.fYCoord[0,1] < self.fYCoord[0,0]:
                self.interpAzCoGrad = interp.RectBivariateSpline(self.fXCoord[:,0], self.fYCoord[0,::-1],self.AzElSlope()['Az'][:,::-1])
                self.interpElCoGrad = interp.RectBivariateSpline(self.fXCoord[:,0], self.fYCoord[0,::-1],self.AzElSlope()['El'][:,::-1])
            
        # transform azel into uv (-1 because azimuth positive toward East)
        u = -1 * np.cos(el * math.pi / 180) * np.sin(az * math.pi / 180)
        v = np.sin(el * math.pi / 180)
                
        # if uv are 2D, flat them. Use absolute value
        if not signed:
            return {'Az':np.absolute(np.reshape(self.interpAzCoGrad.ev(u.flatten(),v.flatten()),np.array(az).shape)), \
                    'El':np.absolute(np.reshape(self.interpElCoGrad.ev(u.flatten(),v.flatten()),np.array(az).shape))}
        else:
            return {'Az':np.reshape(self.interpAzCoGrad.ev(u.flatten(),v.flatten()),np.array(az).shape), \
                    'El':np.reshape(self.interpElCoGrad.ev(u.flatten(),v.flatten()),np.array(az).shape)}
        
class GrdDialog(QDialog):

    # Constructor for GrdDialog class
    def __init__(self, strFileName: str, parent=None):
        # Parent constructor
        super().__init__()

        self.strFileName = strFileName
        self.parent = parent
        self.earth_plot = parent.earth_plot

        # Add Title to the widget
        self.setWindowTitle('Load pattern')
        self.setMinimumSize(100, 50)

        # Everything in a vertical Layout
        vbox = QVBoxLayout(self)

        # Add longitude field
        self.viewLonLbl = QLabel('Longitude', parent=self)
        self.viewLonField = QLineEdit(str(parent.earth_plot._viewer.longitude()), parent=self)
        hbox1 = QHBoxLayout(None)
        hbox1.addWidget(self.viewLonLbl)
        hbox1.addStretch(1)
        hbox1.addWidget(self.viewLonField)
        vbox.addLayout(hbox1)

        # Add Title field
        self.viewTitleLbl = QLabel('Title', parent=self)
        self.viewTitleField = QLineEdit(parent=self)
        hbox3 = QHBoxLayout(None)
        hbox3.addWidget(self.viewTitleLbl)
        hbox3.addStretch(1)
        hbox3.addWidget(self.viewTitleField)
        vbox.addLayout(hbox3)

        # Add isolevel 
        self.viewIsoLvlLbl = QLabel('Isolevels', parent=self)
        self.viewIsoLvlField = QLineEdit(self.getIsoLvl(), parent=self)
        hbox4 = QHBoxLayout(None)
        hbox4.addWidget(self.viewIsoLvlLbl)
        hbox4.addStretch(1)
        hbox4.addWidget(self.viewIsoLvlField)
        vbox.addLayout(hbox4)

        # Add checkboxes
        self.chkRevertX = QCheckBox('Revert X axis', parent=self)
        self.chkRevertY = QCheckBox('Revert Y axis', parent=self)
        self.chkXPol    = QCheckBox('Use crosspol data', parent=self)
        self.chkSlope   = QCheckBox('Display Slope', parent=self)

        # place test field in a vertical box layout
        vbox.addWidget(self.chkRevertX)
        vbox.addWidget(self.chkRevertY)
        vbox.addWidget(self.chkXPol)
        vbox.addWidget(self.chkSlope)
        vbox.addStretch(1)

        # Add Ok/Cancel buttons
        okButton = QPushButton('OK',self)
        cancelButton = QPushButton('Cancel',self)

        # Place Ok/Cancel button in an horizontal box layout
        hbox2 = QHBoxLayout()
        hbox2.addStretch(1)
        hbox2.addWidget(okButton)
        hbox2.addWidget(cancelButton)

        # put the button layout in the Vertical Layout
        vbox.addLayout(hbox2)

        # set dialog box layout
        self.setLayout(vbox)

        # connect buttons to actions
        okButton.clicked.connect(self.setLoadGrd)
        cancelButton.clicked.connect(self.close)

        # Dialog is modal to avoid reentry and weird behaviour
        self.setModal(True)
        self.show()

    def setLoadGrd(self):
        self.close()
        self.earth_plot.setViewLon(float(self.viewLonField.text()))
        grd = self.earth_plot.loadGrd(self.strFileName, bRevertX=self.chkRevertX.checkState(), \
                                                bRevertY=self.chkRevertY.checkState(), \
                                                bUseSecondPol=self.chkXPol.checkState(), \
                                                bDisplaySlope=self.chkSlope.checkState())['grd']
        self.earth_plot.setTitle(self.viewTitleField.text())
        grd.fIsolvl = [float(s) for s in self.viewIsoLvlField.text().split(',')]
        self.earth_plot.draw()

    def getIsoLvl(self, grd: Grd=None):
        if grd == None:
            return ",".join(str(x) for x in DEFAULT_ISOLEVEL_DBI)
        else:
            return ",".join(str(x) for x in grd.fIsolvl)
