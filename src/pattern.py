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
# import Basemap of mpltoolkit
from mpl_toolkits.basemap import Basemap

# PyQt5 widgets import
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QAction, qApp, QDialog, QLineEdit, \
                            QHBoxLayout, QVBoxLayout, QPushButton, QWidget, QFileDialog, QLabel, \
                            QGridLayout, QCheckBox
from PyQt5.QtGui import QColor, QPalette

# abstract class toolbox
from abc import ABC, abstractmethod

# local import
from viewer import Viewer
import angles as ang


# Constants
# Default isolevel to be displayed at patten loading
DEFAULT_ISOLEVEL_DBI = [25, 30, 35, 38, 40]

# geostationary altitude
ALTGEO = 35786000.0 # m

DEG2RAD = np.pi / 180.0
RAD2DEG = 180.0 / np.pi


class Pattern(ABC):
    """Abstract class representing an antenna pattern. This class define all the 
    functions and methods mandatory for compatibility with the viewer features.
    """
# Function and methods common to all 
#==============================================================================
    def __init__(self, filename=None, revert_x=False, revert_y=False, \
                 use_second_pol=False, sat_alt=None, sat_lon=None, \
                 display_slope=False, shrink=False, az_shrink=None, \
                 el_shrink=None):
        """Constructor of abstract class Pattern do nothing.
        """
        # just initialize object
        super().__init__()

        # string: name of file containing pattern data
        self._filename = filename

        # float[]: isolevel for display
        self._isolevel = DEFAULT_ISOLEVEL_DBI

        # boolean: display slope (True) or isolevel (False)
        self._display_slope = display_slope
        
        # float[]: range of slope displayed
        self._slope_range = [3, 20]

        # boolean: use x axis reverted 
        self._revert_x = revert_x

        # boolean: use y axis reverted
        self._revert_y = revert_y
        
        # boolean: use second polarisation as copol
        self._use_second_pol = use_second_pol

        # boolean: shrink the pattern at display
        self._shrink = shrink

        # float: absolute shrink along azimuth in degrees
        self._azshrink = az_shrink

        # float: absolute shrink along elevation in degrees
        self._elshrink = el_shrink

        # number of data set contained in file
        self._nb_sets = 0

        # first component of copol
        self._E_mag_co = []

        # second component of copol
        self._E_phs_co = []

        # gradient of first component
        self._E_grad_co = []

        # first component of crosspol
        self._E_mag_cr = []

        # second component of crosspol
        self._E_phs_cr = []
        
        # azimuth grid
        self._azimuth = []

        # elevation grid
        self._elevation = []
        
        # longitude grid
        self._longitude = []

        # latitude grid
        self._latitude = []

        # satellite position
        self._satellite = Viewer(sat_lon, 0, sat_alt)
    # end of constructor

    def copol(self, k: int=0):
        """Return co-polarisation pattern. In dBi.
        """
        return self._E_mag_co[k]
    # end of function copol

    def cross(self, k: int=0):
        """Return cross-polarisation pattern. In dBi.
        """
        return self._E_mag_cr[k]
    # end of function cross

    def xpd(self, k: int=0):
        """Return XPD pattern. In dB.
        """
        return self._E_mag_co[k] - self._E_mag_cr[k]
    # end of function xpd

    def satellite(self):
        """return viewer object
        """
        return self._satellite
    # end of function satellite

    def getmax(self, set: int=0):
        """Get max directivity value and coordinates.
        """
        max_value = np.max(self.copol(set))
        max_index = np.argmax(self.copol(set))
        max_longitude = self.longitude().flatten()[max_index]
        max_latitude = self.latitude().flatten()[max_index]
        return max_value, max_longitude, max_latitude
    # end of function getmax

    def displaymax(self, map: Basemap, set: int=0):
        """Display max of pattern as a cross on the map.
        """
        max_val, max_lon, max_lat = self.getmax(set)
        max_x, max_y = map(max_lon, max_lat)
        mark = Path(vertices=[(-100, 0),\
                              (100, 0),\
                              (0, -100),\
                              (0, 100)],\
                    codes=[Path.MOVETO,\
                           Path.LINETO,\
                           Path.MOVETO,\
                           Path.LINETO])
        map.scatter(x=max_x, y=max_y, s=20, marker='+', color='k', \
                    linewidths=25, edgecolors='none')
        map.ax.annotate('{0:0.2f}'.format(max_val), xy=(max_x + 1e4, max_y + 1e4))
    # end of method displaymax

    def slope(self, set: int=0):
        """Return gradient of Co-polarisation pattern
        """
        if self._E_grad_co == []:
            # get gradient of Azimuth coordinate
            azimuth_grad, _ = np.gradient(self.azimuth())
            # get gradient of Elevation coordinate
            _, elevation_grad = np.gradient(self.elevation())
            # get gradient of pattern in Azimuth and Elevation             
            co_grad_az, co_grad_el = np.gradient(self.copol(set))
            # normalize gradient of pattern in Azimuth direction
            co_grad_az /= azimuth_grad
            # normalize gradient of pattern in Elevation direction
            co_grad_el /= elevation_grad
            # RSS the 2 directions gradient in one scalar field
            self._E_grad_co = np.sqrt(co_grad_az**2 + co_grad_el**2)
        return self._E_grad_co
    # end of function slope

    def interpolate_slope(self, az, el, set=0):
        """return interpolated value of the pattern
        """
        if not self.interpolated_copol_gradient:
            self.interpolated_copol_gradient = interp.RectBivariateSpline(self._x[set][:,0], self._y[set][0,:],self.slope())
        # transform azel into uv (-1 because azimuth positive toward East)
        u = -1 * np.cos(el * DEG2RAD) * np.sin(az * DEG2RAD)
        v = np.sin(el * DEG2RAD)
        # flatten, interpolate and reshape
        return np.reshape(self.interpolated_copol_gradient.ev(u.flatten(),v.flatten()),np.array(az).shape)
    # end of function interpolate_slope


# Mandatory functions and methods to be implemented
#==============================================================================

    @abstractmethod
    def read_file(self):
        """Read antenna pattern data from file self._filename.
        """
        pass
    # end of method read_file

    @abstractmethod
    def longitude(self):
        """Return longitude matrix of the data grid points
        """
        pass
    # end of function longitude

    @abstractmethod
    def latitude(self):
        """Return latitude matrix of the data grid points
        """
        pass
    # end of function latitude

    @abstractmethod
    def azimuth(self, k: int=0):
        """Return azimuth matrix of the data grid points
        """
        pass
    # end of function azimuth

    @abstractmethod
    def elevation(self, k: int=0):
        """Return elevation matrix of the data grid points
        """
        pass
    # end of function elevation

    @abstractmethod
    def plot(self, k: int=0):
        """Plot itself in an EarthPlot Canvas.
        """
        pass
    # end of function plot

    @abstractmethod
    def grid_type(self):
        """Return file grid type is a standardised format.
        1 - uv grid
        2 - theta/phi
        3 - Az and El
        4 - Elevation over Azimuth
        5 - Azimuth over Elevation
        """
        # Type of grd field grid
        # 1: uv-grid
        # 4: Elevation over Azimuth
        # 5: Elevation and Azimuth
        # 6: Azimuth over Elevation
        # 7: thetaphi grid 
        #
        # Type of pat field grid
        # 1 - uv
        # 2 - theta, phi
        # 3 - az over el
        # 4 - el over az
        # 101 - x, y Plane rectangular grid used for array excitations
        #       not supported
        pass
    # end function grid_type

    def azel_grid(self, k: int = 0):
        """This function convert grid format to azimuth elevation.
        """
        def id(x, y):
            return x, y

        convert = {1:ang.uv2azel, \
                   2:ang.thetaphi2azel, \
                   3:id, \
                   4:ang.elovaz2azel, \
                   5:ang.azovel2azel}

        return convert[self.grid_type()](self._x[k], self._y[k])
    # end of function azel_grid
    
    def ll_grid(self, k: int = 0):
        az, el = self.azel_grid(k)
        x = self._satellite.altitude() * az * DEG2RAD
        y = self._satellite.altitude() * el * DEG2RAD
        self.proj = prj.Proj(init='epsg:4326 +proj=geos +h=' + str(self._satellite.altitude()) + \
                                ' +a=6378137.00 +b=6378137.00 +lon_0=' + \
                                str(self._satellite.longitude()) + \
                                ' +x_0=0 +y_0=0 +units=meters +no_defs') 
        longitude, latitude = self.proj(x, y, inverse=True)
        return longitude, latitude
    # end of function ll_grid    


# end of class Pattern


class Grd(Pattern):
    """This class implement an antenna pattern object using data from a Ticra .grd file.
    """
    
    # constructor
    def __init__(self, filename=None, revert_x=False, revert_y=False, use_second_pol=False, \
                 sat_alt=None, sat_lon=None, display_slope=False, shrink=False, azshrink=None, elshrink=None):

        # call Abstract class Pattern constructor
        super().__init__(filename, revert_x, revert_y, use_second_pol, sat_alt, sat_lon, display_slope, shrink, azshrink, elshrink)

        # read data file
        self._nb_sets, \
        self._grid, \
        self._x, \
        self._y, \
        self._E_mag_co, \
        self._E_phs_co, \
        self._E_mag_cr, \
        self._E_phs_cr = self.read_file(self._filename, self._revert_x, self._revert_y)

        # for interpolation, the azimuth and elevation gradient have to be positive
        for set in range(self._nb_sets):
            if self._x[set][1,0] > self._x[set][0,0] and self._y[set][0,1] > self._y[set][0,0]:
                # already the good orientation
                pass
            elif self._x[set][1,0] < self._x[set][0,0] and self._y[set][0,1] > self._y[set][0,0]:
                # change only x-axis of the grid
                self._x[set] = self._x[set][::-1,0]
                self._y[set] = self._y[set][::-1,0]
                self._E_mag_co[set] = self._E_mag_co[set][::-1,0]
                self._E_phs_co[set] = self._E_phs_co[set][::-1,0]
                self._E_mag_cr[set] = self._E_mag_cr[set][::-1,0]
                self._E_phs_cr[set] = self._E_phs_cr[set][::-1,0]
            elif self._x[set][1,0] < self._x[set][0,0] and self._y[set][0,1] < self._y[set][0,0]:
                # change x and y-axes of the grid
                self._x[set] = self._x[set][::-1,::-1]
                self._y[set] = self._y[set][::-1,::-1]
                self._E_mag_co[set] = self._E_mag_co[set][::-1,::-1]
                self._E_phs_co[set] = self._E_phs_co[set][::-1,::-1]
                self._E_mag_cr[set] = self._E_mag_cr[set][::-1,::-1]
                self._E_phs_cr[set] = self._E_phs_cr[set][::-1,::-1]
            elif self._x[set][1,0] > self._x[set][0,0] and self._y[set][0,1] < self._y[set][0,0]:
                # change only y-axis of the grid
                self._x[set] = self._x[set][0,::-1]
                self._y[set] = self._y[set][0,::-1]
                self._E_mag_co[set] = self._E_mag_co[set][0,::-1]
                self._E_phs_co[set] = self._E_phs_co[set][0,::-1]
                self._E_mag_cr[set] = self._E_mag_cr[set][0,::-1]
                self._E_phs_cr[set] = self._E_phs_cr[set][0,::-1]

        # if use_second_pol, swap copol and crosspol data
        if use_second_pol:
            self._E_mag_co, self._E_mag_cr = self._E_mag_cr, self._E_mag_co
            self._E_phs_co, self._E_phs_cr = self._E_phs_cr, self._E_phs_co

        # if not sat_alt == None and not sat_lon == None:
        #     x = self._satellite.altitude() * self.azimuth() * DEG2RAD
        #     y = self._satellite.altitude() * self.elevation() * DEG2RAD
        #     self.proj = prj.Proj(init='epsg:4326 +proj=geos +h=' + str(self._satellite.altitude()) + \
        #                          ' +a=6378137.00 +b=6378137.00 +lon_0=' + \
        #                          str(sat_lon) + ' +x_0=0 +y_0=0 +units=meters +no_defs') 
        #     self._longitude, self._latitude = self.proj(x, y, inverse=True)
            #self.satellite_longitude = sat_lon
        
        for k in range(self._nb_sets):
            self._longitude.append(np.zeros_like(self._x[k]))
            self._latitude.append(np.zeros_like(self._x[k]))
            self._longitude[k], self._latitude[k] = self.ll_grid(k)

        self.interpolated_copol = None
        self.interpolated_copol_gradient = None
        self.interpolated_copol_azgrad = None
        self.interpolated_copol_elgrad = None
    # end of constructor __init__


    def read_file(self, filename, revert_x, revert_y):
        """Read data from TICRA .grd file.
        Params:
            filename: the path to the file to read
        Returns:
            nb_sets: number of data sets
            grid: type de grid
            x: grid stations x coordinates 
            y: grid stations y coordinates
            E_mag_co: magnitude of electrical field in copolarisation (dBi)
            E_phs_co: phase of electrical field in copolarisation (degrees)
            E_mag_cr: magnitude of electrical field in crosspolarisation (dBi)
            E_phs_cr: pahse of electrical field in crosspolarisation (degrees)
        """
        # open file and read text data
        file = open(filename, "r")
        # read all lines in a table
        lines = file.readlines()
        # close file        
        file.close()
        
         # line number
        linesnumber = len(lines)
        istart = -1
        
        # map header data into dicData        
        for i in range(linesnumber):
            # detect end of comments
            if lines[i][:4] == '++++':
                istart = i + 1
                break
        
        # header content
        # should always be 1
        ktype = int(lines[istart].split()[0])
        istart += 1
        # number of patterns
        nb_sets = int(lines[istart].split()[0])
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
        icomp = int(lines[istart].split()[1])
        # number of field component (2 for far field, 3 for near field)
        ncomp = int(lines[istart].split()[2])
        # Type of field grid
        # 1: uv-grid
        # 4: Elevation over Azimuth
        # 5: Elevation and Azimuth
        # 6: Azimuth over Elevation
        # 7: thetaphi grid 
        grid = int(lines[istart].split()[3])
        istart += 1
        # center of beams
        xi = [int(lines[istart+i_set].split()[0]) for i_set in range(nb_sets)]
        yi = [int(lines[istart+i_set].split()[1]) for i_set in range(nb_sets)]
        istart += nb_sets
        
        # data table reading 
        iSet = 0
        iRow = 0
        iCol = 0      
        nx = []               # number of points of the grid along x axis
        ny = []               # number of pointd of the grid along y axis
        klimit = []           # ???
        E_field_copol = []    # Electrical field in copolarisation (complex format)
        E_field_cross = []    # Electrical field in crosspolarisation (complex format)
        x = []                # x coordinates of points of the grid (vector)
        y = []                # y coordinates of points of the grid (vector)
        xs = []               # x start
        xe = []               # x end
        ys = []               # y start
        ye = []               # y end
        iLine = istart
        for iSet in range(nb_sets):
            # get limits of the pattern grid
            if revert_x == False:
                xs.append(float(lines[iLine].split()[0]))
                xe.append(float(lines[iLine].split()[2]))
            else:   
                xs.append(float(lines[iLine].split()[2]))
                xe.append(float(lines[iLine].split()[0]))
            if revert_y == False:
                ys.append(float(lines[iLine].split()[1]))
                ye.append(float(lines[iLine].split()[3]))
            else:
                ys.append(float(lines[iLine].split()[3]))
                ye.append(float(lines[iLine].split()[1]))
            iLine += 1
            # begin of new set, configure set
            nx.append(int(lines[iLine].split()[0]))
            ny.append(int(lines[iLine].split()[1]))
            klimit.append(int(lines[iLine].split()[2]))
            E_field_copol.append(np.zeros((nx[iSet], ny[iSet]),dtype=np.complex_))
            E_field_cross.append(np.zeros((nx[iSet], ny[iSet]),dtype=np.complex_))
            x.append(np.zeros((nx[iSet], ny[iSet]),dtype=np.float_))
            y.append(np.zeros((nx[iSet], ny[iSet]),dtype=np.float_))
            iLine += 1
            # put data in the table
            for iTabLine in range(iLine, iLine + nx[iSet] * ny[iSet]):
                E_real_copol    = float(lines[iTabLine].split()[0])
                E_imag_copol    = float(lines[iTabLine].split()[1])
                E_real_cross = float(lines[iTabLine].split()[2])
                E_imag_cross = float(lines[iTabLine].split()[3])
                
                E_field_copol[iSet][iRow,iCol] = E_real_copol + 1j * E_imag_copol
                E_field_cross[iSet][iRow,iCol] = E_real_cross + 1j * E_imag_cross
                dx = (xe[iSet] - xs[iSet]) / (nx[iSet] - 1)
                dy = (ye[iSet] - ys[iSet]) / (ny[iSet] - 1)
                x[iSet][iRow,iCol] = iRow * dx + xs[iSet] + xi[iSet] * dx
                y[iSet][iRow,iCol] = iCol * dy + ys[iSet] + yi[iSet] * dy
                
                iRow += 1
                if iRow == nx[iSet]:
                    iRow = 0
                    iCol += 1
                    if iCol == ny[iSet]:
                        iCol = 0
                        iLine = iTabLine + 1
        # end of file reading

        # initialize some grided data
        E_mag_co = 20*np.log10(np.absolute(E_field_copol))
        E_phs_co = np.angle(E_field_copol, deg=True)
        E_mag_cr = 20*np.log10(np.absolute(E_field_cross))
        E_phs_cr = np.angle(E_field_cross, deg=True)

        return nb_sets, \
               grid, \
               x, \
               y, \
               E_mag_co, \
               E_phs_co, \
               E_mag_cr, \
               E_phs_cr
    # end of read_file

    def grid_type(self):
        """Return file grid type is a standardised format.
        1 - uv grid
        2 - theta/phi
        3 - Az/El
        4 - Elevation over Azimuth
        5 - Azimuth over Elevation
        6 - Alpha/epsilon (only .pat)
        101 - .pat 101 format
        """
        # Type of grd field grid
        # 1: uv-grid
        # 4: Elevation over Azimuth
        # 5: Elevation and Azimuth
        # 6: Azimuth over Elevation
        # 7: thetaphi grid 
        convert = {1: 1, \
                   4: 4, \
                   5: 3, \
                   6: 5, \
                   7: 2}
        return convert[self._grid]
    # end function grid_type

    # return Azimuth grid for this data set
    def azimuth(self, set=0):
        if self._azimuth == []:
            if self._grid == 1:
                self._azimuth = -1 * np.arctan(self._x[set] / np.sqrt(1 - self._x[set]**2 - self._y[set]**2)) * RAD2DEG
            elif self._grid == 4:
                self._azimuth = self._x[set]
            elif self._grid == 5:
                self._azimuth = self._x[set]
            elif self._grid == 6:
                self._azimuth = self._x[set]
        return self._azimuth
        
    # return Elevation grid for this data set
    def elevation(self, set=0):
        if self._elevation == []:
            if self._grid == 1:
                self._elevation = np.arcsin(self._y[set]) * RAD2DEG
            elif self._grid == 4:
                self._elevation = self._y[set]
            elif self._grid == 5:
                self._elevation = self._y[set]
            elif self._grid == 6:
                self._elevation = self._y[set]
        return self._elevation

    def theta(self, set=0):
        if self._grid == 1:
            # _x == u and _y == v
            return np.arcsin(np.sqrt(self._x[set]**2 + self._y[set]**2)) * RAD2DEG
        elif self._grid == 4 or self._grid == 5 or self._grid == 6:
            # _x == az and _y == el
            return np.arccos(np.cos(self._x[set] * DEG2RAD) * np.cos(self._y[set] * DEG2RAD)) * RAD2DEG

    def phi(self, set=0):
        if self._grid == 1:
            # _x == u and _y == v
            return np.arctan(self._x[set] / self._y[set]) * RAD2DEG
        elif self._grid == 4 or self._grid == 5 or self._grid == 6:
            # _x == az and _y == el
            return np.arctan(np.tan(self._y[set] * DEG2RAD) / np.sin(self._x[set] * DEG2RAD))

    def u(self):
        """Returns u coordinates got from grd file or converted from az/el from file.
        """
        if self._grid == 1:
            return self._x[set]
        elif self._grid == 4:
            return np.cos(self._y[set] * DEG2RAD) * np.sin(self._x[set] * DEG2RAD)
        elif self._grid == 5:
            # az = -theta*cos(phi), el=theta*sin(phi)
            return np.sin(self.theta(set) * DEG2RAD) * np.cos(self.phi(set) * DEG2RAD)
    
    def v(self):
        """Returns v coordinates got from grd file or converted from az/el from file.
        """
        if self._grid ==1:
            return self._y[set]
        elif self._grid == 4:
            return np.sin(self._y[set] * np.pi / 180.0)

    def longitude(self, k: int = 0):
        """Return longitude grid of the Grd instance
        """
        return self._longitude[k]

    def latitude(self, k: int = 0):
        """Return latitude grid of the Grd instance
        """
        return self._latitude[k]

    # # return minimum Azimuth of the grid
    # def MinAz(self):
    #     return np.min(self.azimuth())
        
    # # return maximum Azimuth of the grid
    # def MaxAz(self):
    #     return np.max(self.azimuth())
    
    # # return minimum Elevation of the grid
    # def MinEl(self):
    #     return np.min(self.elevation())
    
    # # return maximum Elevation of the grid
    # def MaxEl(self):
    #     return np.max(self.elevation())
        

            
    # return gradient of Co-polarisation pattern along Azimuth
    def azel_slope(self, signed=False, set=0):
        # get gradient of Azimuth coordinate
        azimuth_grad, _ = np.gradient(self.azimuth())
        # get gradient of Elevation coordinate
        _, elevation_grad = np.gradient(self.elevation())
        # get gradient of pattern in Azimuth and Elevation             
        copol_azgrad, copol_elgrad = np.gradient(self.copol(set))
        # normalize gradient of pattern in Azimuth direction
        copol_azgrad /= azimuth_grad
        # normalize gradient of pattern in Elevation direction
        copol_elgrad /= elevation_grad
        # use absolute value
        if not signed:
            return {'Az':np.absolute(copol_azgrad), 'El':np.absolute(copol_elgrad)}
        else:
            return {'Az':copol_azgrad, 'El':copol_elgrad}
        
    def interpolate_copol(self, az, el, set=0):
        """return interpolated value of the pattern
        """
        if not self.interpolated_copol:
            self.interpolated_copol = interp.RectBivariateSpline(self._x[set][:,0], self._y[set][0,:],self.copol())
            
        # transform azel into uv (-1 because azimuth positive toward East)
        u = -1 * np.cos(el * DEG2RAD) * np.sin(az * DEG2RAD)
        v = np.sin(el * DEG2RAD)

        return np.reshape(self.interpolated_copol.ev(u.flatten(),v.flatten()),np.array(az).shape)
    # end of function interpolate_copol    

    # def interpolate_slope(self, az, el, set=0):
    #     """return interpolated value of the pattern
    #     """
    #     if not self.interpolated_copol_gradient:
    #         self.interpolated_copol_gradient = interp.RectBivariateSpline(self._x[set][:,0], self._y[set][0,:],self.slope())
    #     # transform azel into uv (-1 because azimuth positive toward East)
    #     u = -1 * np.cos(el * DEG2RAD) * np.sin(az * DEG2RAD)
    #     v = np.sin(el * DEG2RAD)
    #     # flatten, interpolate and reshape
    #     return np.reshape(self.interpolated_copol_gradient.ev(u.flatten(),v.flatten()),np.array(az).shape)
    # # end of function interpolate_slope
        
    def interpolate_azel_slope(self, az, el, signed=False):
        """return interpolated value of the pattern
        """
        if not self.interpolated_copol_azgrad or not self.interpolated_copol_elgrad:
            # if not yet use interpolation of slopes  
            self.interpolated_copol_azgrad = interp.RectBivariateSpline(self._x[set][:,0], self._y[set][0,:],self.azel_slope()['Az'])
            self.interpolated_copol_elgrad = interp.RectBivariateSpline(self._x[set][:,0], self._y[set][0,:],self.azel_slope()['El'])
            
        # transform azel into uv (-1 because azimuth positive toward East)
        u = -1 * np.cos(el * DEG2RAD) * np.sin(az * DEG2RAD)
        v = np.sin(el * DEG2RAD)
        
        # if uv are 2D, flat them. Use absolute value depending on signed flag
        if not signed:
            return {'Az':np.absolute(np.reshape(self.interpolated_copol_azgrad.ev(u.flatten(),v.flatten()),np.array(az).shape)), \
                    'El':np.absolute(np.reshape(self.interpolated_copol_elgrad.ev(u.flatten(),v.flatten()),np.array(az).shape))}
        else:
            return {'Az':np.reshape(self.interpolated_copol_azgrad.ev(u.flatten(),v.flatten()),np.array(az).shape), \
                    'El':np.reshape(self.interpolated_copol_elgrad.ev(u.flatten(),v.flatten()),np.array(az).shape)}
    # end of function interpolate_azel_slope

    def getmax(self, k: int=0):
        """Get max directivity value and coordinates.
        """
        max_value = np.max(self.copol(k))
        max_index = np.argmax(self.copol(k))
        max_longitude = self.longitude().flatten()[max_index]
        max_latitude = self.latitude().flatten()[max_index]
        return max_value, max_longitude, max_latitude
    # end of function getmax

    def displaymax(self, earthmap):
        """Display max directivity location of the pattern.
        """
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
    # end of method displaymax

    def shrink_copol(self, az, el, step=0.05, set=0):
        """Shrink pattern using an elliptical beam pointing error.
        This function compute the pattern with different pointing error and
        keep the minimum directivity for each station.
        """
        # Create azel meshgrid (rectangular grid)
        az_vec = np.arange(-az, az + step, step)
        el_vec = np.arange(-el, el + step, step)
        az_grid, el_grid = np.meshgrid(az_vec, el_vec)
        # exclude point out of the ellipse
        for i in range(len(az_grid)):
            for j in range(len(az_grid[i])):
                if (az_grid[i][j]/az)**2 + (el_grid[i][j]/el)**2 > 1:
                    az_grid[i][j] = np.nan
                    el_grid[i][j] = np.nan
        # add points of the ellipse
        # TODO improve this part. Ellipse is not very well defined
        az_ellipse =[]
        el_ellipse = []   
        x = np.arange(-az, az + step, step)
        y = np.arange(-el, el + step, step)
        y_prime = np.concatenate((el * np.sqrt(1 - x**2 / az**2), -el * np.sqrt(1 - x**2 / az**2)))
        x_prime = np.concatenate((az * np.sqrt(1 - y**2 / el**2), -az * np.sqrt(1 - y**2 / el**2)))

        az_depointing = np.concatenate(([f for f in az_grid.flatten() if not np.isnan(f)], x, x, x_prime))
        el_depointing = np.concatenate(([f for f in el_grid.flatten() if not np.isnan(f)], y_prime, y, y))

        # interpolate copol into a step accurate grid
        az_co = self.azimuth().flatten()
        el_co = self.elevation().flatten()
        co = []

        # create interpolation object, and create shrunk pattern
        for i in range(len(az_co)):
            co.append(np.min(self.interpolate_copol(az_co[i] + az_depointing, el_co[i] + el_depointing)))
        co = np.reshape(co, self.azimuth().shape)

        # return result pattern
        return co
    # end of function shrink

    def plot(self, map: Basemap, viewer, figure, axes, cbar, cbar_axes):
        """Draw pattern on the earth plot from the provided grd.
        """

        # project pattern grid in map coordinates
        x, y = map(self.longitude(), self.latitude())
        
        # display either isolevel or color map of slopes 
        if not self._display_slope:
            # try to display isolevel
            # if wrong pol is chosen, isolevel value might not be found, hence an exception is thrown
            # and has to be caught
            try:
                # if shrink pattern option is selected, use shrink_copol function
                if not self._shrink:
                    cs_pattern = map.contour(x, y, self.copol(), self._isolevel, linestyles='solid', linewidths=0.5)
                    self.displaymax(map)
                else:
                    cs_pattern = map.contour(x, y, self.shrink_copol(self._azshrink, self._elshrink), self._isolevel, linestyles='solid', linewidths=0.5)
                    # no call to displaymax because it has no meaning when shrinking the pattern

                # add isolevels labels    
                figure.axes[0].clabel(cs_pattern, self._isolevel, inline=True, fmt='%1.1f',fontsize=5)
                
                # return 
                return cs_pattern

            except ValueError as value_err:
                print(value_err)
                print('Pattern ' + self._filename + ' will not be displayed.')
                return None
        else:
            # define regular grid and azimuth/elevation
            nx, ny = 1001, 1001
            az_min = np.min(self.azimuth())
            az_max = np.max(self.azimuth())
            el_min = np.min(self.elevation())
            el_max = np.max(self.elevation())
            az_lin = np.linspace(az_min, az_max, nx)
            el_lin = np.linspace(el_min, el_max, ny)
            az_mesh, el_mesh = np.meshgrid(az_lin, el_lin)
            
            # convert grid to plot coordinates
            x = az_mesh * self._satellite.altitude() * DEG2RAD
            y = el_mesh * self._satellite.altitude() * DEG2RAD
            
            # compute plot origin (Nadir of spacecraft)
            x_origin, y_origin = map(self._satellite.longitude(), self._satellite.latitude())
            
            # display color mesh
            cmap = plt.get_cmap('jet')
            cmap.set_over('white', self._slope_range[1])
            cmap.set_under('white', self._slope_range[0])
            
            pcmGrd = map.pcolormesh(x + x_origin, \
                                    y + y_origin, \
                                    self.interpolate_slope(az_mesh, el_mesh), \
                                    vmin=self._slope_range[0], vmax=self._slope_range[1], \
                                    cmap=cmap, alpha=0.5)

            # add color bar
            if cbar:
                cbar = figure.colorbar(pcmGrd, cax=cbar_axes)     
            else:
                divider = make_axes_locatable(axes)
                cbar_axes = divider.append_axes("right", size="5%", pad=0.05)  
                cbar = figure.colorbar(pcmGrd, cax=cbar_axes)   
            cbar.ax.set_ylabel('Pattern slope (dB/deg)')
        # endif
    # end of method plot
# end of class Grd


class Pat(Pattern):
    """This class implement reading and processing of Satsoft .pat files.
    """
    
    # constructor
    def __init__(self, filename=None, revert_x=False, revert_y=False, use_second_pol=False, \
                 sat_alt=None, sat_lon=None, display_slope=False, shrink=False, azshrink=None, elshrink=None):

        # call Abstract class Pattern constructor
        super().__init__(filename, revert_x, revert_y, use_second_pol, sat_alt, sat_lon, display_slope, shrink, azshrink, elshrink)

        # read data file
        self._nb_sets, \
        self._grid, \
        self._x, \
        self._y, \
        self._E_mag_co, \
        self._E_phs_co, \
        self._E_mag_cr, \
        self._E_phs_cr = self.read_file(self._filename, self._revert_x, self._revert_y)
        
        for k in range(self._nb_sets):
            self._longitude.append(np.zeros_like(self._x[k]))
            self._latitude.append(np.zeros_like(self._x[k]))
            self._longitude[k], self._latitude[k] = self.ll_grid(k)

    def read_file(self, filename, revert_x, revert_y):

        # open file and read text data
        file = open(filename, "r")
        # read all lines in a table
        lines = file.readlines()
        # close file        
        file.close()
        
         # line number
        linesnumber = len(lines)
        istart = -1
        
        # map header data into dicData        
        for i in range(linesnumber):
            # detect end of comments
            if lines[i][:4] == '++++':
                istart = i+1
                break

        # Line 1
        # select separator
        if ',' in lines[istart]:
            sep = ','
        else:
            sep = None
        # read file parameters
        # number of beams in the file
        nb_sets = int(lines[istart].split(sep)[0])
        # field component type
        # 0 - Scalar field (no crosspol)
        # 1 - Linear theta and phi components
        # 2 - Circular right-hand and left-hand components
        # 3 - linear co and cross
        # 4 - major and minor axis of polarisation ellipse
        # 5 - az/el components
        # 6 - Alpha and epsilon components 
        kcomp = int(lines[istart].split(sep)[1])
        # number of field components (1 or 2)
        ncomp = int(lines[istart].split(sep)[2])
        # grid type
        # 1 - uv
        # 2 - theta, phi
        # 3 - az, el
        # 4 - alpha, epsilon
        # 101 - x, y Plane rectangular grid used for array excitations
        grid = int(lines[istart].split(sep)[3])
        if grid == 101:
            raise ValueError('101 grid format is not supported by this software.')
        # X dimension of grid
        nx = int(lines[istart].split(sep)[4])
        # Y dimension of grid
        ny = int(lines[istart].split(sep)[5])
        # read optional parameters
        if len(lines[istart].split(sep)) > 6:
            # Specification of input rotation matrix
            # 0 - No rotation (default)
            # 1 - Exchange X and Y axes
            # 2 - Invert X axis
            # 3 - 1 + 2
            # 4 - Invert Y axis
            # 5 - 1 + 4
            # 6 - 2 + 4
            # 7 - 1 + 2 + 4
            imat = int(lines[istart].split(sep)[6])
        else:
            # default value 0
            imat = 0
        if len(lines[istart].split(sep)) > 7:
            # Unit of field data
            # 0 - complex rectangular voltage
            # 1 - magnitude (dB) and phase (deg) of field
            iunit = int(lines[istart].split(sep)[7])
        else:
            # default value 0
            iunit = 0
        
        # next line
        istart += 1

        # line 2: XS, YS, XE, YE
        # grid limits
        # select separator
        if ',' in lines[istart]:
            sep = ','
        else:
            sep = None
        xs = float(lines[istart].split(sep)[0]) * RAD2DEG
        ys = float(lines[istart].split(sep)[1]) * RAD2DEG
        xe = float(lines[istart].split(sep)[2]) * RAD2DEG
        ye = float(lines[istart].split(sep)[3]) * RAD2DEG

        dx = (xe - xs) / (nx - 1)
        dy = (ye - ys) / (ny - 1)

        # next line
        istart += 2

        # line 4: beams center
        ix = []
        iy = []
        # select separator
        if ',' in lines[istart]:
            sep = ','
        else:
            sep = None
        # get beam center for all beams
        for i in range(nb_sets):
            ix.append(float(lines[istart + i].split(sep)[0]))
            iy.append(float(lines[istart + i].split(sep)[1]))

        # create grids
        x_vec = []
        y_vec = []
        x = [None] * nb_sets
        y = [None] * nb_sets
        for k in range(nb_sets):
            x_vec.append(np.linspace(start=xs, stop=xe, num=nx, endpoint=True) + ix[k]) 
            y_vec.append(np.linspace(start=ys, stop=ye, num=ny, endpoint=True) + iy[k]) 
            x[k], y[k] = np.meshgrid(x_vec[k], y_vec[k])
            
        # next line
        istart += 1

        # line 5: frequency
        freq = []
        for i in range(nb_sets):
            freq.append(float(lines[istart + i]))

        # next line
        istart += 1

        # patterns
        E_mag_co = [] # first component of copol
        E_phs_co = [] # second component of copol
        E_mag_cr = [] # first component of crosspol
        E_phs_cr = [] # second component of crosspol
        if ncomp == 2:
            np.zeros((nx, ny), dtype=float)
        # select separator
        if ',' in lines[istart]:
            sep = ','
        else:
            sep = None
        
        # for each beam
        for k in range(nb_sets):            
            # initialize grids
            c11 = np.zeros((ny, nx), dtype=float)
            c12 = np.zeros((ny, nx), dtype=float)
            if ncomp == 2:
                c21 = np.zeros((ny, nx), dtype=float)
                c22 = np.zeros((ny, nx), dtype=float)
            # extract line per line
            for j in range(ny):
                for i in range(nx):
                    c11[j][i] = float(lines[istart].split(sep)[0])
                    c12[j][i] = float(lines[istart].split(sep)[1])
                    if ncomp == 2:
                        c21[j][i] = float(lines[istart].split(sep)[2])
                        c22[j][i] = float(lines[istart].split(sep)[3])
                    istart += 1
            
            # pattern is read, put it in the right format
            E_mag_co.append(self.magnitude(iunit, c11, c12))
            E_phs_co.append(self.phase(iunit, c11, c12))
            if ncomp == 2:
                E_mag_cr.append(self.magnitude(iunit, c21, c22))
                E_mag_cr.append(self.phase(iunit, c21, c22))
        # end for

        return nb_sets, \
               grid, \
               x, \
               y, \
               E_mag_co, \
               E_phs_co, \
               E_mag_cr, \
               E_phs_cr

    
    # Directivity
    ###################################################################
        
    def magnitude(self, iunit, c1, c2):
        """Convert (C1, C2) to magnitude (dB) depending on IUNIT value
        """            

        def convert(c1, c2):
            return  20 * np.log10(np.absolute(c1 + 1j * c2))
        
        def identity(c1, c2):
            return c1
        
        converter = {0: convert, \
                     1: identity}
        
        return converter[iunit](c1, c2)
    # end of function magnitude

    def phase(self, iunit, c1, c2):
        """Convert (C1, C2) to phase (deg) depending on IUNIT value
        """         

        def convert(c1, c2):
            return np.angle(c1 + 1j * c2) * RAD2DEG
        
        def identity(c1, c2):
            return c2

        converter = {0: convert, \
                     1: identity}

        return converter[iunit](c1, c2)
    # end of function phase
    
    def getmax(self, k=0):
        """Get max directivity value and coordinates.
        """
        max_value = np.max(self._E_mag_co[k])
        max_index = np.argmax(self._E_mag_co[k])
        max_longitude = self.longitude().flatten()[max_index]
        max_latitude = self.latitude().flatten()[max_index]
        return max_value, max_longitude, max_latitude
    # end of function getmax

    def grid_type(self):
        """Return file grid type is a standardised format.
        1 - uv grid
        2 - theta/phi
        3 - Az and El
        4 - Elevation over Azimuth
        5 - Azimuth over Elevation
        101 - .pat 101 format
        """
        # Type of pat field grid
        # 1 - uv
        # 2 - theta, phi
        # 3 - az over el
        # 4 - el over az
        # 101 - x, y Plane rectangular grid used for array excitations
        convert = {1: 1, \
                   2: 2, \
                   3: 5, \
                   4: 4, \
                   101: 101}
        return convert[self._grid]

    # Azimuth / Elevation
    ###################################################################

    def azimuth(self, k: int=0):
        """This function provide azimuth grid for self, beam number k.
        """
        if not len(self._azimuth):
            if self._grid == 1:
                # uv to azel
                self._azimuth = -1 * np.arctan(self._x[k] / np.sqrt(1 - self._x[k]**2 - self._y[k]**2)) * RAD2DEG
            elif self._grid == 3:
                # already azel
                self._azimuth = self._x[k]
        return self._azimuth
        
    def elevation(self, k: int=0):
        """This function provide elevation grid for self, beam number k.
        """
        if not len(self._elevation):
            if self._grid == 1:
                # uv to azel
                self._elevation = np.arcsin(self._y[k]) * RAD2DEG
            elif self._grid == 3:
                # already azel
                self._elevation = self._y[k]
        return self._elevation


    # Longitude/ Latitude
    ###################################################################

    def longitude(self):
        """Project grid on Earth viewed from observer point of view. Return longitude.
        """
        x = self._satellite.altitude() * self.azimuth() * DEG2RAD
        y = self._satellite.altitude() * self.elevation() * DEG2RAD
        self.proj = prj.Proj(init='epsg:4326 +proj=geos +h=' + \
                                  str(self._satellite.altitude()) + \
                                  ' +a=6378137.00 +b=6378137.00 +lon_0=' + \
                                  str(self._satellite.longitude()) + \
                                  ' +x_0=0 +y_0=0 +units=meters +no_defs') 
        longitude, _ = self.proj(x, y, inverse=True)
        return longitude
    # end of function longitude

    def latitude(self):
        """Project grid on Earth viewed from observer point of view. Return latitude.
        """
        x = self._satellite.altitude() * self.azimuth() * DEG2RAD
        y = self._satellite.altitude() * self.elevation() * DEG2RAD
        self.proj = prj.Proj(init='epsg:4326 +proj=geos +h=' + \
                             str(self._satellite.altitude()) + \
                             ' +a=6378137.00 +b=6378137.00 +lon_0=' + \
                             str(self._satellite.longitude()) + \
                             ' +x_0=0 +y_0=0 +units=meters +no_defs') 
        _, latitude = self.proj(x, y, inverse=True)
        return latitude
    # end of function latitude

    # Plot
    ###################################################################
    

    def plot(self, map: Basemap, observer, fig, ax, cbar, cbar_ax):
        """Plot current pattern in the map.
        """
        # Project pattern grid in map coordinates
        x, y = map(self.longitude(), self.latitude())

        # plot the contours
        cs_pattern = map.contour(x, y, self.copol(), self.isolevel, linestyles='solid', linewidths=0.5)
        self.displaymax(map)
        fig.axes[0].clabel(cs_pattern, self.isolevel, inline=True, fmt='%1.1f',fontsize=5)
    # end of method plot

# end of class Pat


class GrdDialog(QDialog):

    # Constructor for GrdDialog class
    def __init__(self, strFileName: str, parent=None, pattern=None):
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
        self.viewTitleField = QLineEdit(self.earth_plot._plot_title, parent=self)
        hbox3 = QHBoxLayout(None)
        hbox3.addWidget(self.viewTitleLbl)
        hbox3.addStretch(1)
        hbox3.addWidget(self.viewTitleField)
        vbox.addLayout(hbox3)

        # Add isolevel 
        self.viewIsoLvlLbl = QLabel('Isolevels', parent=self)
        self.viewIsoLvlField = QLineEdit(self.get_isolevel(), parent=self)
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
        okButton.clicked.connect(self.addpattern)
        cancelButton.clicked.connect(self.close)

        # Set default field value if pattern object has been provided
        if pattern:
            self.viewLonField.setText(str(pattern.satellite().longitude()))
            self.viewIsoLvlField.setText(self.get_isolevel(pattern))
            self.chkRevertX.setCheckState(pattern._revert_x)
            self.chkRevertY.setCheckState(pattern._revert_y)
            self.chkXPol.setCheckState(pattern._use_second_pol)
            self.chkSlope.setCheckState(pattern._display_slope)
            self.chkshrink.setCheckState(pattern._shrink)
            if pattern._shrink:
                self.azfield.setText(str(pattern._azshrink))
                self.elfield.setText(str(pattern._elshrink))

        # Dialog is modal to avoid reentry and weird behaviour
        self.setModal(True)
        self.show()
    # end of __init__

    def get_isolevel(self, grd: Grd=None):
        if grd == None:
            return ",".join(str(x) for x in DEFAULT_ISOLEVEL_DBI)
        else:
            return ",".join(str(x) for x in grd._isolevel)

    def addpattern(self):
        self.close()

        # add item in Grd menu
        patternindex = len(self.earth_plot._patterns) + 1
        patternmenu = self.parent.menupattern.addMenu('Pattern ' + \
                                                        str(patternindex))
        remove_pat_action = QAction('Remove', self.parent)
        edit_pat_action = QAction('Edit', self.parent)
        patternmenu.addAction(remove_pat_action)
        patternmenu.addAction(edit_pat_action)
        remove_pat_action.triggered.connect(self.make_remove_pattern(self.filename, self.earth_plot._patterns, self.earth_plot))
        edit_pat_action.triggered.connect(self.make_edit_pattern(self.filename, self.earth_plot._patterns))

        if self.filename[-3:] == 'grd':
            pattern = Grd(filename=self.filename, \
                          revert_x=self.chkRevertX.checkState(), \
                          revert_y=self.chkRevertY.checkState(), \
                          use_second_pol=self.chkXPol.checkState(), \
                          sat_alt=ALTGEO, \
                          sat_lon=float(self.viewLonField.text()), \
                          display_slope=self.chkSlope.checkState(), \
                          shrink=self.chkshrink.checkState(), \
                          azshrink=float(self.azfield.text()), \
                          elshrink=float(self.elfield.text()))
        elif self.filename[-3:] == 'pat':
            pattern = Pat(filename=self.filename, \
                          revert_x=self.chkRevertX.checkState(), \
                          revert_y=self.chkRevertY.checkState(), \
                          use_second_pol=self.chkXPol.checkState(), \
                          sat_alt=ALTGEO, \
                          sat_lon=float(self.viewLonField.text()), \
                          display_slope=self.chkSlope.checkState(), \
                          shrink=self.chkshrink.checkState(), \
                          azshrink=float(self.azfield.text()), \
                          elshrink=float(self.elfield.text()))

        self.earth_plot._patterns[self.filename] = {'grd':pattern, 'menu': patternmenu}
        self.earth_plot.settitle(self.viewTitleField.text())
        pattern.isolevel = [float(s) for s in self.viewIsoLvlField.text().split(',')]
        self.earth_plot.draw()
    # end of function addpattern
    
    def make_remove_pattern(self, filename, grds, eplot):
        """Callback maker for remove pattern menu items.
        """
        def remgrd():
            menu = grds[filename]['menu']
            menu_action = menu.menuAction()
            menu.parent().removeAction(menu_action)
            del grds[filename]
            eplot.draw()
        return remgrd
    # end of function make_remgrd

    def make_edit_pattern(self,filename, grds):
        """Callback maker for edit pattern menu items.
        """
        def editgrd():
            menu = grds[filename]['menu']
            menu_action = menu.menuAction()
            menu.parent().removeAction(menu_action)
            dialbox = GrdDialog(filename, self.parent, grds[filename]['grd'])
            del grds[filename]
            dialbox.exec_()
        return editgrd  
    # end of function make_editgrd

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
# end of classe GrdDialog
