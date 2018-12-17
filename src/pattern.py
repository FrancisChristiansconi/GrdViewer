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
# import path for customised marker
from matplotlib.path import Path
# axes manipulation
from mpl_toolkits.axes_grid1 import make_axes_locatable
# other matplotlib utilities
import matplotlib.pyplot as plt

# PyQt5 widgets import
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QAction, qApp, QDialog, QLineEdit, \
                            QHBoxLayout, QVBoxLayout, QPushButton, QWidget, QFileDialog, QLabel, \
                            QGridLayout, QCheckBox
from PyQt5.QtGui import QColor, QPalette

# Constants
# Default isolevel to be displayed at patten loading
DEFAULT_ISOLEVEL_DBI = [25, 30, 35, 38, 40]

# geostationary altitude
ALTGEO = 35786000.0 # m

DEG2RAD = np.pi / 180.0
RAD2DEG = 180.0 / np.pi


class Grd(object):
    
    # constructor
    def __init__(self, filename=None, bRevertX=False, bRevertY=False, bUseSecondPol=False, \
                 alt=None, lon=None, bDisplaySlope=False, shrink=False, azshrink=None, elshrink=None):

        self.filename = filename

        # open file and read text data
        file = open(filename, "r")
        # read all lines in a table
        lines = file.readlines()
        # close file        
        file.close()
        
         # line number
        linesnumber = len(lines)
        iStart = -1
        
        # map header data into dicData        
        for i in range(linesnumber):
            # detect end of comments
            if lines[i][:4] == '++++':
                iStart = i+1
                break
        
        # header content
        # should always be 1
        self.KTYPE = int(lines[iStart].split()[0])
        iStart += 1
        # number of patterns
        self.NSET = int(lines[iStart].split()[0])
        # field components
        # 1: linear E_theta and E_phi
        # 2: RHCP and LHCP
        # 3: linear co and cx
        # 4: Major and minor axes of polarization ellipse
        # 5: XPD fields: E_theta/E_phi and E_phi/E_theta
        # 6: XPD fields: RHCP/LHCP and LHCP/RHCP
        # 7: XPD fields: co/cx and cx/co
        # 8: XPD fields: major/minor and minor/major
        # 9: total power norm(E) and sqrt(RHCP/LHCP)
        self.ICOMP = int(lines[iStart].split()[1])
        # number of field component (2 for far field, 3 for near field)
        self.NCOMP = int(lines[iStart].split()[2])
        # Type of field grid
        # 1: uv-grid
        # 4: Elevation over Azimuth
        # 5: Elevation and Azimuth
        # 6: Azimuth over Elevation
        # 7: thetaphi grid 
        self.IGRID = int(lines[iStart].split()[3])
        iStart += 1
        # center of beams
        self.XI = [int(lines[iStart+i_set].split()[0]) for i_set in range(self.NSET)]
        self.YI = [int(lines[iStart+i_set].split()[1]) for i_set in range(self.NSET)]
        iStart += self.NSET
        
        # data table reading 
        iSet = 0
        iRow = 0
        iCol = 0      
        self.NX = []
        self.NY = [] 
        self.KLIMIT = [] 
        self._E_field_copol = []
        self._E_field_cross = []
        self._x = []
        self._y = []
        self.XS = []
        self.XE = []
        self.YS = []
        self.YE = []
        iLine = iStart
        for iSet in range(self.NSET):
            # get limits of the pattern grid
            if bRevertX == False:
                self.XS.append(float(lines[iLine].split()[0]))
                self.XE.append(float(lines[iLine].split()[2]))
            else:   
                self.XS.append(float(lines[iLine].split()[2]))
                self.XE.append(float(lines[iLine].split()[0]))
            if bRevertY == False:
                self.YS.append(float(lines[iLine].split()[1]))
                self.YE.append(float(lines[iLine].split()[3]))
            else:
                self.YS.append(float(lines[iLine].split()[3]))
                self.YE.append(float(lines[iLine].split()[1]))
            iLine += 1
            # begin of new set, configure set
            self.NX.append(int(lines[iLine].split()[0]))
            self.NY.append(int(lines[iLine].split()[1]))
            self.KLIMIT.append(int(lines[iLine].split()[2]))
            self._E_field_copol.append(np.zeros((self.NX[iSet], self.NY[iSet]),dtype=np.complex_))
            self._E_field_cross.append(np.zeros((self.NX[iSet], self.NY[iSet]),dtype=np.complex_))
            self._x.append(np.zeros((self.NX[iSet], self.NY[iSet]),dtype=np.float_))
            self._y.append(np.zeros((self.NX[iSet], self.NY[iSet]),dtype=np.float_))
            iLine += 1
            # put data in the table
            for iTabLine in range(iLine, iLine + self.NX[iSet] * self.NY[iSet]):
                E_real_copol    = float(lines[iTabLine].split()[0])
                E_imag_copol    = float(lines[iTabLine].split()[1])
                E_real_cross = float(lines[iTabLine].split()[2])
                E_imag_cross = float(lines[iTabLine].split()[3])
                
                self._E_field_copol[iSet][iRow,iCol] = E_real_copol + 1j * E_imag_copol
                self._E_field_cross[iSet][iRow,iCol] = E_real_cross + 1j * E_imag_cross
                dx = (self.XE[iSet] - self.XS[iSet]) / (self.NX[iSet] - 1)
                dy = (self.YE[iSet] - self.YS[iSet]) / (self.NY[iSet] - 1)
                self._x[iSet][iRow,iCol] = iRow * dx + self.XS[iSet] + self.XI[iSet] * dx
                self._y[iSet][iRow,iCol] = iCol * dy + self.YS[iSet] + self.YI[iSet] * dy
                
                iRow += 1
                if iRow == self.NX[iSet]:
                    iRow = 0
                    iCol += 1
                    if iCol == self.NY[iSet]:
                        iCol = 0
                        iLine = iTabLine + 1
        # end of file reading
        

        # initialize some grided data
        if bUseSecondPol:
            self._E_mag_copol = 20*np.log10(np.absolute(self._E_field_cross))
            self._E_mag_cross = 20*np.log10(np.absolute(self._E_field_copol))
        else:
            self._E_mag_copol = 20*np.log10(np.absolute(self._E_field_copol))
            self._E_mag_cross = 20*np.log10(np.absolute(self._E_field_cross))
        self._azimuth = []
        self._elevation = []
        self._E_gradient_copol = []

        if not alt == None and not lon == None:
            x = alt * self.azimuth() * np.pi / 180.0
            y = alt * self.elevation() * np.pi / 180.0
            self.proj = prj.Proj(init='epsg:4326 +proj=geos +h=' + str(alt) + ' +a=6378137.00 +b=6378137.00 +lon_0=' + str(lon) + ' +x_0=0 +y_0=0 +units=meters +no_defs') 
            self.longitude, self.latitude = self.proj(x, y, inverse=True)

        self.isolevel = [25,30,35,38,40]
        self.bDisplaySlope = bDisplaySlope
        self.slope_range = [3,20]

        self.shrink = shrink
        self.azshrink = azshrink
        self.elshrink = elshrink

    # End of __init__
        
    # return Azimuth grid for this data set
    def azimuth(self, set=0):
        if self._azimuth == []:
            if self.IGRID == 1:
                self._azimuth = -1 * np.arctan(self._x[set] / np.sqrt(1 - self._x[set]**2 - self._y[set]**2)) * 180.0 / np.pi
            elif self.IGRID == 4:
                self._azimuth = self._x[set]
            elif self.IGRID == 5:
                self._azimuth = self._x[set]
            elif self.IGRID == 6:
                self._azimuth = self._x[set]
        return self._azimuth
        
    # return Elevation grid for this data set
    def elevation(self, set=0):
        if self._elevation == []:
            if self.IGRID == 1:
                self._elevation = np.arcsin(self._y[set]) * RAD2DEG
            elif self.IGRID == 4:
                self._elevation = self._y[set]
            elif self.IGRID == 5:
                self._elevation = self._y[set]
            elif self.IGRID == 6:
                self._elevation = self._y[set]
        return self._elevation

    def theta(self, set=0):
        if self.IGRID == 1:
            # _x == u and _y == v
            return np.arcsin(np.sqrt(self._x[set]**2 + self._y[set]**2)) * RAD2DEG
        elif self.IGRID == 4 or self.IGRID == 5 or self.IGRID == 6:
            # _x == az and _y == el
            return np.arccos(np.cos(self._x[set] * DEG2RAD) * np.cos(self._y[set] * DEG2RAD)) * RAD2DEG

    def phi(self, set=0):
        if self.IGRID == 1:
            # _x == u and _y == v
            return np.arctan(self._x[set] / self._y[set]) * RAD2DEG
        elif self.IGRID == 4 or self.IGRID == 5 or self.IGRID == 6:
            # _x == az and _y == el
            return np.arctan(np.tan(self._y[set] * DEG2RAD) / np.sin(self._x[set] * DEG2RAD))

    def u(self):
        """Returns u coordinates got from grd file or converted from az/el from file.
        """
        if self.IGRID == 1:
            return self._x[set]
        elif self.IGRID == 4:
            return np.cos(self._y[set] * DEG2RAD) * np.sin(self._x[set] * DEG2RAD)
        elif self.IGRID == 5:
            # az = -theta*cos(phi), el=theta*sin(phi)
            return np.sin(self.theta(set) * DEG2RAD) * np.cos(self.phi(set) * DEG2RAD)
    
    def v(self):
        """Returns v coordinates got from grd file or converted from az/el from file.
        """
        if self.IGRID ==1:
            return self._y[set]
        elif self.IGRID == 4:
            return np.sin(self._y[set] * np.pi / 180.0)

    # return minimum Azimuth of the grid
    def MinAz(self):
        return np.min(self.azimuth())
        
    # return maximum Azimuth of the grid
    def MaxAz(self):
        return np.max(self.azimuth())
    
    # return minimum Elevation of the grid
    def MinEl(self):
        return np.min(self.elevation())
    
    # return maximum Elevation of the grid
    def MaxEl(self):
        return np.max(self.elevation())
        
    # return Co-polarisation pattern
    def copol(self, set=0):
        return self._E_mag_copol[set]

    def cross(self, set = 0):
        return self._E_mag_cross[set]
        
    # return gradient of Co-polarisation pattern
    def slope(self, set=0):
        if self._E_gradient_copol == []:
            # get gradient of Azimuth coordinate
            azimuth_grad, _ = np.gradient(self.azimuth())
            # get gradient of Elevation coordinate
            _, elevation_grad = np.gradient(self.elevation())
            # get gradient of pattern in Azimuth and Elevation             
            self.fCoGradX, self.fCoGradY = np.gradient(self.copol(set))
            # normalize gradient of pattern in Azimuth direction
            self.fCoGradX /= azimuth_grad
            # normalize gradient of pattern in Elevation direction
            self.fCoGradY /= elevation_grad
            # RSS the 2 directions gradient in one scalar field
            self._E_gradient_copol = np.sqrt(self.fCoGradX**2 + self.fCoGradY**2)
        return self._E_gradient_copol
            
    # return gradient of Co-polarisation pattern along Azimuth
    def azel_slope(self,signed=False):
        # get gradient of Azimuth coordinate
        azimuth_grad, _ = np.gradient(self.azimuth())
        # get gradient of Elevation coordinate
        _, elevation_grad = np.gradient(self.elevation())
        # get gradient of pattern in Azimuth and Elevation             
        copol_azgrad, copol_elgrad = np.gradient(self._E_mag_copol)
        # normalize gradient of pattern in Azimuth direction
        copol_azgrad /= azimuth_grad
        # normalize gradient of pattern in Elevation direction
        copol_elgrad /= elevation_grad
        # use absolute value
        if not signed:
            return {'Az':np.absolute(copol_azgrad), 'El':np.absolute(copol_elgrad)}
        else:
            return {'Az':copol_azgrad, 'El':copol_elgrad}
        
    # return interpolated value of the pattern
    def interpolate_copol(self, az, el, set=0):
        if self._x[set][set][1,0] > self._x[set][0,0] and self._y[set][0,1] > self._y[set][0,0]:
            interpolated_copol = interp.RectBivariateSpline(self._x[set][:,0], self._y[set][0,:],self.copol())
        elif self._x[set][1,0] < self._x[set][0,0] and self._y[set][0,1] > self._y[set][0,0]:
            interpolated_copol = interp.RectBivariateSpline(self._x[set][::-1,0], self._y[set][0,:],self.copol()[::-1,:])
        elif self._x[set][1,0] < self._x[set][0,0] and self._y[set][0,1] < self._y[set][0,0]:
            interpolated_copol = interp.RectBivariateSpline(self._x[set][::-1,0], self._y[set][0,::-1],self.copol()[::-1,::-1])
        elif self._x[set][1,0] > self._x[set][0,0] and self._y[set][0,1] < self._y[set][0,0]:
            interpolated_copol = interp.RectBivariateSpline(self._x[set][:,0], self._y[set][0,::-1],self.copol()[:,::-1])
        # transform azel into uv (-1 because azimuth positive toward East)
        u = -1 * np.cos(el * math.pi / 180) * np.sin(az * math.pi / 180)
        v = np.sin(el * math.pi / 180)
        return np.reshape(interpolated_copol.ev(u.flatten(),v.flatten()),np.array(az).shape)
        
    # return interpolated value of the pattern
    def interpolate_slope(self, az, el, set=0):
        # if not yet use interpolation of slopes            
        if self.azimuth(set)[1,0] > self.azimuth(set)[0,0] and self.elevation(set)[0,1] > self.elevation(set)[0,0]:
            interpolated_copol_gradient = interp.RectBivariateSpline(self.azimuth(set)[:,0], self.elevation(set)[0,:],self.slope())
        elif self.azimuth(set)[1,0] < self.azimuth(set)[0,0] and self.elevation(set)[0,1] > self.elevation(set)[0,0]:
            interpolated_copol_gradient = interp.RectBivariateSpline(self.azimuth(set)[::-1,0], self.elevation(set)[0,:],self.slope()[::-1,:])
        elif self.azimuth(set)[1,0] < self.azimuth(set)[0,0] and self.elevation(set)[0,1] < self.elevation(set)[0,0]:
            interpolated_copol_gradient = interp.RectBivariateSpline(self.azimuth(set)[::-1,0], self.elevation(set)[0,::-1],self.slope()[::-1,::-1])
        elif self.azimuth(set)[1,0] > self.azimuth(set)[0,0] and self.elevation(set)[0,1] < self.elevation(set)[0,0]:
            interpolated_copol_gradient = interp.RectBivariateSpline(self.azimuth(set)[:,0], self.elevation(set)[0,::-1],self.slope()[:,::-1])
        # flatten, interpolate and reshape
        return np.reshape(interpolated_copol_gradient.ev(az.flatten(),el.flatten()),np.array(az).shape)
        
    # return interpolated value of the pattern
    def interpolate_azel_slope(self, az, el, signed=False):
        # if not yet use interpolation of slopes  
        if self.azimuth(set)[1,0] > self.azimuth(set)[0,0] and self.elevation(set)[0,1] > self.elevation(set)[0,0]:
            interpolated_copol_azgrad = interp.RectBivariateSpline(self.azimuth(set)[:,0], self.elevation(set)[0,:],self.azel_slope()['Az'])
            interpolated_copol_elgrad = interp.RectBivariateSpline(self.azimuth(set)[:,0], self.elevation(set)[0,:],self.azel_slope()['El'])
        elif self.azimuth(set)[1,0] < self.azimuth(set)[0,0] and self.elevation(set)[0,1] > self.elevation(set)[0,0]:
            interpolated_copol_azgrad = interp.RectBivariateSpline(self.azimuth(set)[::-1,0], self.elevation(set)[0,:],self.azel_slope()['Az'][::-1,:])
            interpolated_copol_elgrad = interp.RectBivariateSpline(self.azimuth(set)[::-1,0], self.elevation(set)[0,:],self.azel_slope()['El'][::-1,:])
        elif self.azimuth(set)[1,0] < self.azimuth(set)[0,0] and self.elevation(set)[0,1] < self.elevation(set)[0,0]:
            interpolated_copol_azgrad = interp.RectBivariateSpline(self.azimuth(set)[::-1,0], self.elevation(set)[0,::-1],self.azel_slope()['Az'][::-1,::-1])
            interpolated_copol_elgrad = interp.RectBivariateSpline(self.azimuth(set)[::-1,0], self.elevation(set)[0,::-1],self.azel_slope()['El'][::-1,::-1])
        elif self.azimuth(set)[1,0] > self.azimuth(set)[0,0] and self.elevation(set)[0,1] < self.elevation(set)[0,0]:
            interpolated_copol_azgrad = interp.RectBivariateSpline(self.azimuth(set)[:,0], self.elevation(set)[0,::-1],self.azel_slope()['Az'][:,::-1])
            interpolated_copol_elgrad = interp.RectBivariateSpline(self.azimuth(set)[:,0], self.elevation(set)[0,::-1],self.azel_slope()['El'][:,::-1])
        
        # if uv are 2D, flat them. Use absolute value depending on signed flag
        if not signed:
            return {'Az':np.absolute(np.reshape(interpolated_copol_azgrad.ev(az.flatten(),el.flatten()),np.array(az).shape)), \
                    'El':np.absolute(np.reshape(interpolated_copol_elgrad.ev(az.flatten(),el.flatten()),np.array(az).shape))}
        else:
            return {'Az':np.reshape(interpolated_copol_azgrad.ev(az.flatten(),el.flatten()),np.array(az).shape), \
                    'El':np.reshape(interpolated_copol_elgrad.ev(az.flatten(),el.flatten()),np.array(az).shape)}

    def getmax(self, set=0):
        """Get max directivity value and coordinates.
        """
        max_value = np.max(self._E_mag_copol[set])
        max_index = np.argmax(self._E_mag_copol[set])
        max_longitude = self.longitude.flatten()[max_index]
        max_latitude = self.latitude.flatten()[max_index]
        return max_value, max_longitude, max_latitude
    # end of function getmax

    def displaymax(self, earthmap):
        max_val, max_lon, max_lat = self.getmax()
        max_x, max_y = earthmap(max_lon, max_lat)
        mark = Path(vertices=[(-100, 0),\
                              (100, 0),\
                              (0, -100),\
                              (0, 100)],\
                    codes=[Path.MOVETO,\
                           Path.LINETO,\
                           Path.MOVETO,\
                           Path.LINETO])
        earthmap.scatter(x=max_x, y=max_y, s=20, marker='+', color='k', \
                         linewidths=25, edgecolors='none')
        earthmap.ax.annotate('{0:0.2f}'.format(max_val), xy=(max_x + 1e4, max_y + 1e4))

    def shrink_copol(self, az, el, step=0.05, set=0):
        """Shrink pattern using an elliptical beam pointing error.
        This function compute the pattern with different pointing error and
        keep the minimum directivity for each station.
        """
        # Create azel meshgrid (rectangular grid)
        az_vec = np.arange(-az, az, step, endpoint=True)
        el_vec = np.arange(-el, el, step, endpoint=True)
        az_grid, el_grid = np.meshgrid(az_vec, el_vec)
        # exclude point out of the ellipse
        for i in len(az_grid):
            if (az_grid[i]/az)**2 + (el_grid[i]/el)**2 > 1:
                az_grid[i] = np.nan
                el_grid[i] = np.nan
        # add points of the ellipse
        az_ellipse =[]
        el_ellipse = []        
        if az > el:
            a = az
            b = el
        else:
            a = el
            b = az
        c = np.sqrt(a**2 + b**2)
        e = c / a
        theta_vec = np.linspace(-np.pi, np.pi, np.pi / 20)
        rho_vec = a * (1 - e**2) / (1 + e * np.cos(theta_vec)) 
        if az > el:
            az_ellipse = rho_vec * np.cos(theta_vec)
            el_ellipse = rho_vec * np.sin(theta_vec)
        else:
            az_ellipse = rho_vec * np.sin(theta_vec)
            el_ellipse = rho_vec * np.cos(theta_vec)
        # concatenate grid and surrounding ellipse
        az_depointing = np.concatenate([f for f in az_grid.flatten() if not np.isnan(f)], az_ellipse)
        el_depointing = np.concatenate([f for f in el_grid.flatten() if not np.isnan(f)], el_ellipse)

        # interpolate copol into a step accurate grid
        az_min = self.MinAz() - az
        az_max = self.MaxAz() + az
        el_min = self.MinEl() - el
        el_max = self.MaxEl() + el
        az_co_grid, el_co_grid = np.meshgrid(np.arange(az_min, az_max, step, endpoint=True))
        co = []

        # create interpolation object
        if self._x[set][set][1,0] > self._x[set][0,0] and self._y[set][0,1] > self._y[set][0,0]:
            interpolated_copol = interp.RectBivariateSpline(self._x[set][:,0], self._y[set][0,:],self.copol())
        elif self._x[set][1,0] < self._x[set][0,0] and self._y[set][0,1] > self._y[set][0,0]:
            interpolated_copol = interp.RectBivariateSpline(self._x[set][::-1,0], self._y[set][0,:],self.copol()[::-1,:])
        elif self._x[set][1,0] < self._x[set][0,0] and self._y[set][0,1] < self._y[set][0,0]:
            interpolated_copol = interp.RectBivariateSpline(self._x[set][::-1,0], self._y[set][0,::-1],self.copol()[::-1,::-1])
        elif self._x[set][1,0] > self._x[set][0,0] and self._y[set][0,1] < self._y[set][0,0]:
            interpolated_copol = interp.RectBivariateSpline(self._x[set][:,0], self._y[set][0,::-1],self.copol()[:,::-1])
      
        for i in len(az_co_grid):
            co[i] = np.min(interpolated_copol.ev(az_co_grid[i] + az_depointing, el_co_grid[i] + el_depointing))

        return co
    # end of function shrink

    def plot(self, map, viewer, figure, axes, cbar, cbar_axes):
        """Draw pattern on the earth plot from the provided grd.
        """
        x, y = map(self.longitude, self.latitude)
        
        if not self.bDisplaySlope:
            try:
                if not self.shrink:
                    cs_grd = map.contour(x, y, self.copol(), self.isolevel, linestyles='solid', linewidths=0.5)
                    self.displaymax(map)
                else:
                    cs_grd = map.contour(x, y, self.shrink_copol(self.azshrink, self.elshrink), self.isolevel, linestyles='solid', linewidths=0.5)
                figure.axes[0].clabel(cs_grd, self.isolevel, inline=True, fmt='%1.1f',fontsize=5)

                # # resize plot
                # l = axes.figure.subplotpars.left
                # r = axes.figure.subplotpars.right
                # t = axes.figure.subplotpars.top
                # b = axes.figure.subplotpars.bottom
                # figw = float(figure.get_figwidth())/(r-l) * 0.95
                # figh = float(figure.get_figheight())/(t-b) * 0.95
                # axes.figure.set_size_inches(figw, figh)
                
                return cs_grd
            except ValueError as value_err:
                print(value_err)
                print('Pattern ' + self.filename + ' will not be displayed.')
                return None
        else:
            # define grid
            iNx = 1001
            iNy = 1001
            fAzlin = np.linspace(self.MinAz(), self.MaxAz(), iNx)
            fEllin = np.linspace(self.MinEl(), self.MaxEl(), iNy)
            fAzMesh, fElMesh = np.meshgrid(fAzlin, fEllin)
            x = fAzMesh * viewer.altitude() * DEG2RAD
            y = fElMesh * viewer.altitude() * DEG2RAD
            # display color mesh
            cmap = plt.get_cmap('jet')
            cmap.set_over('white', self.slope_range[1])
            cmap.set_under('white', self.slope_range[0])
            xOrigin, yOrigin = map(viewer.longitude(), viewer.latitude())
            pcmGrd = map.pcolormesh(x + xOrigin, \
                                    y + yOrigin, \
                                    self.interpolate_slope(fAzMesh, fElMesh), \
                                    vmin=self.slope_range[0], vmax=self.slope_range[1], \
                                    cmap=cmap, alpha=0.5)
            # add color bar
            if cbar:
                cbar = figure.colorbar(pcmGrd, cax=cbar_axes)     
            else:
                divider = make_axes_locatable(axes)
                cbar_axes = divider.append_axes("right", size="5%", pad=0.05)  
                cbar = figure.colorbar(pcmGrd, cax=cbar_axes)   
            cbar.ax.set_ylabel('Pattern slope (dB/deg)')
# end of class Grd


class GrdDialog(QDialog):

    # Constructor for GrdDialog class
    def __init__(self, strFileName: str, parent=None):
        # Parent constructor
        super().__init__()

        self.filename = strFileName
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

        # add shrink sub form
        self.chkshrink = QCheckBox('Shrink', parent=self)
        self.azshrklbl = QLabel('Az.', parent=self)
        self.azfield = QLineEdit('0.25', parent=self)
        self.azfield.setFixedWidth(50)
        self.elshrklbl = QLabel('El.', parent=self)
        self.elfield = QLineEdit('0.25', parent=self)
        self.elfield.setFixedWidth(50)
        hbox5 = QHBoxLayout(None)
        hbox5.addWidget(self.chkshrink)
        hbox5.addWidget(self.azshrklbl)
        hbox5.addWidget(self.azfield)
        hbox5.addWidget(self.elshrklbl)
        hbox5.addWidget(self.elfield)
        vbox.addLayout(hbox5)
        self.chkshrink.stateChanged.connect(self.chkshrinkstatechanged)
        self.chkshrinkstatechanged()

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
        grd = self.earth_plot.loadgrd(self.filename, lon=float(self.viewLonField.text()), \
                                      alt=ALTGEO, \
                                      revertx=self.chkRevertX.checkState(), \
                                      reverty=self.chkRevertY.checkState(), \
                                      secondpol=self.chkXPol.checkState(), \
                                      dispslope=self.chkSlope.checkState())['grd']
        self.earth_plot.settitle(self.viewTitleField.text())
        grd.fIsolvl = [float(s) for s in self.viewIsoLvlField.text().split(',')]
        self.earth_plot.draw()

    def getIsoLvl(self, grd: Grd=None):
        if grd == None:
            return ",".join(str(x) for x in DEFAULT_ISOLEVEL_DBI)
        else:
            return ",".join(str(x) for x in grd.isolevel)

    def chkshrinkstatechanged(self):
        """Callback deactivating the shrink fields wheb shrink checkbox is unchecked.
        """
        palette = QPalette()
        if self.chkshrink.checkState():
            palette.setColor(QPalette.Base, QColor(255, 255, 255))
            self.azfield.setStyleSheet("color: rgb(0, 0, 0);")
            self.elfield.setStyleSheet("color: rgb(0, 0, 0);")
            self.azfield.setReadOnly(False)
            self.azfield.setPalette(palette)
            self.elfield.setReadOnly(False)
            self.elfield.setPalette(palette)
        else:
            palette.setColor(QPalette.Base, QColor(230, 230, 230))
            self.azfield.setStyleSheet("color: rgb(180, 180, 180);")
            self.elfield.setStyleSheet("color: rgb(180, 180, 180);")
            self.azfield.setReadOnly(True)
            self.azfield.setPalette(palette)
            self.elfield.setReadOnly(True)
            self.elfield.setPalette(palette)
    # end of callback

    
    
