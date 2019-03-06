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
# import os function
import os


# PyQt5 widgets import
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QAction, qApp, QDialog, QLineEdit, \
                            QHBoxLayout, QVBoxLayout, QPushButton, QWidget, QFileDialog, QLabel, \
                            QGridLayout, QCheckBox
from PyQt5.QtGui import QColor, QPalette

# abstract class toolbox
from abc import ABC, abstractmethod

# debug
import utils

# local import
from viewer import Viewer
import angles as ang

# import constant file
import constant as cst

# Edit dialog
from .dialog import PatternDialog


class AbstractPattern(ABC):
    """Abstract class representing an antenna pattern. This class define all the 
    functions and methods mandatory for compatibility with the viewer features.
    """
# Function and methods common to all 
#==============================================================================
    def __init__(self, filename=None, conf=None, dialog=False, parent=None):
        """Constructor of abstract class Pattern do nothing.
        """
        utils.trace('in')

        # just initialize object
        super().__init__()

        # dictionary with the pattern conf
        self._conf = conf

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
        try:
            sat_lon = conf['sat_lon']
        except:
            sat_lon = 0
        try:
            sat_lat = conf['sat_lat']
        except:
            sat_lat = 0
        try:
            sat_alt = conf['sat_alt']
        except:
            sat_alt = cst.ALTGEO
        self._satellite = Viewer(sat_lon, sat_lat, sat_alt)

        # Conversion factor
        self._conversion_factor = 0

        self.interpolated_copol = None
        self.interpolated_copol_gradient = None
        self.interpolated_copol_azgrad = None
        self.interpolated_copol_elgrad = None

        # read data file
        self._nb_sets, \
        self._grid, \
        self._x, \
        self._y, \
        self._E_mag_co, \
        self._E_phs_co, \
        self._E_mag_cr, \
        self._E_phs_cr = self.read_file(conf['filename'])

        # float[]: isolevel for display
        max_directivity = np.max(self.copol())
        self._isolevel = np.array(cst.DEFAULT_ISOLEVEL_DBI) + int(max_directivity)

        # matrix to be plotted
        self._to_plot = np.zeros(shape=np.array(self._E_mag_co).shape, dtype=float)
        
        for k in range(self._nb_sets):
            self._longitude.append(np.zeros_like(self._x[k]))
            self._latitude.append(np.zeros_like(self._x[k]))
            self._azimuth.append(np.zeros_like(self._x[k]))
            self._elevation.append(np.zeros_like(self._x[k]))

        # configure 
        self.configure(conf=conf)

        utils.trace('out')


    # end of constructor

    def reshapedata(self):

        # for interpolation, the azimuth and elevation gradient have to be positive
        for set in range(self._nb_sets):

            if self._x[set][0,1] > self._x[set][0,0] and self._y[set][1,0] > self._y[set][0,0]:
                # already the good orientation
                pass
            elif self._x[set][0,1] < self._x[set][0,0] and self._y[set][1,0] > self._y[set][0,0]:
                # change only x-axis of the grid
                self._x[set] = self._x[set][::-1,:]
                self._y[set] = self._y[set][::-1,:]
                self._E_mag_co[set] = self._E_mag_co[set][::-1,:]
                self._E_phs_co[set] = self._E_phs_co[set][::-1,:]
                if len(self._E_mag_cr):
                    self._E_mag_cr[set] = self._E_mag_cr[set][::-1,:]
                    self._E_phs_cr[set] = self._E_phs_cr[set][::-1,:]
            elif self._x[set][0,1] < self._x[set][0,0] and self._y[set][1,0] < self._y[set][0,0]:
                # change x and y-axes of the grid
                self._x[set] = self._x[set][::-1,::-1]
                self._y[set] = self._y[set][::-1,::-1]
                self._E_mag_co[set] = self._E_mag_co[set][::-1,::-1]
                self._E_phs_co[set] = self._E_phs_co[set][::-1,::-1]
                if len(self._E_mag_cr):
                    self._E_mag_cr[set] = self._E_mag_cr[set][::-1,::-1]
                    self._E_phs_cr[set] = self._E_phs_cr[set][::-1,::-1]
            elif self._x[set][0,1] > self._x[set][0,0] and self._y[set][1,0] < self._y[set][0,0]:
                # change only y-axis of the grid
                self._x[set] = self._x[set][:,::-1]
                self._y[set] = self._y[set][:,::-1]
                self._E_mag_co[set] = self._E_mag_co[set][:,::-1]
                self._E_phs_co[set] = self._E_phs_co[set][:,::-1]
                if len(self._E_mag_cr):
                    self._E_mag_cr[set] = self._E_mag_cr[set][:,::-1]
                    self._E_phs_cr[set] = self._E_phs_cr[set][:,::-1]
    # end of reshapedata function

    def generate_grid(self):
        for k in range(self._nb_sets):
            self._longitude[k], self._latitude[k] = self.ll_grid(k)
            self._azimuth[k], self._elevation[k] = self.azel_grid(k)
    # end of function generate_grid

    def configure(self, conf):
        utils.trace('in')

        self._conf.update(conf)
        # file name
        try:
            self._filename = self._conf['filename']
        except:
            raise ValueError("No file name provided")
        # boolean: display slope (True) or isolevel (False)
        try:
            self._display_slope = self._conf['display_slope']
        except:
            self._display_slope = False
        
        # float[]: range of slope displayed
        try:
            self._slope_range = self._conf['slopes']
        except:
            self._slope_range = [3, 20]

        # boolean: use x axis reverted 
        try:
            self._revert_x = self._conf['revert_x']
        except:
            self._revert_x = False

        # boolean: use y axis reverted
        try:
            self._revert_y = self._conf['revert_y']
        except:
            self._revert_y = False

        # boolean: rotate 180 degrees around sub sat
        try:
            self._rotate = self._conf['rotate']
        except:
            self._rotate = False

        # boolean: use second polarisation as copol
        try:
            self._use_second_pol = self._conf['use_second_pol']
        except:
            self._use_second_pol = False

        # boolean: shrink the pattern at display
        try:
            self._shrink = self._conf['shrink']
        except:
            self._shrink = False

        # float: absolute shrink along azimuth in degrees
        try:
            self._azshrink = self._conf['azshrink']
        except:
            self._azshrink = 0.25

        # float: absolute shrink along elevation in degrees
        try:
            self._elshrink = self._conf['elshrink']
        except:
            self._elshrink = 0.25

        # offset of pattern
        try:
            self._offset = self._conf['offset']
        except:
            self._offset = False 

        # azimuth offset
        try:
            self._azimuth_offset = self._conf['azoffset']
        except:
            self._azimuth_offset = 0

        # elevation offset
        try:
            self._elevation_offset = self._conf['eloffset']
        except:
            self._elevation_offset = 0

        # conversion factor
        try:
            self._conversion_factor = self._conf['cf']
        except:
            self._conversion_factor = 0
        
        # satellite position
        try:
            sat_lon = self._conf['sat_lon']
        except:
            sat_lon = 0
        try:
            sat_lat = self._conf['sat_lat']
        except:
            sat_lat = 0
        try:
            sat_alt = self._conf['sat_alt']
        except:
            sat_alt = cst.ALTGEO
        self._satellite = Viewer(sat_lon, sat_lat, sat_alt)

        for set in range(self._nb_sets):
            if self._rotate:
                x_offset = (np.max(self._x[set][:]) - np.min(self._x[set][:]))
                y_offset = (np.max(self._y[set][:][:]) - np.min(self._y[set][:][:]))
                self._x[set] = -1*self._x[set]
                self._y[set] = -1*self._y[set]

        self.reshapedata()

        self.generate_grid()

       
        self.set_to_plot(self._use_second_pol)

        # revevrse x and y axis if requested
        if self._revert_x:
            self._to_plot = self._to_plot[::-1,:]
        if self._revert_y:
            self._to_plot = self._to_plot[:,::-1]


        try:
            self._isolevel = self._conf['isolevel']
        except KeyError:
            max_directivity = np.max(self._to_plot)
            self._isolevel = np.array(cst.DEFAULT_ISOLEVEL_DBI) + int(max_directivity + self._conversion_factor)

    # end of function configure

    def set_to_plot(self, cross=False):
        utils.trace('in')

        # if shrink option
        if self._shrink:
            self._to_plot = self.shrink_copol(self._azshrink, self._elshrink)
        # if not, select co or cross to be plotted
        else:    
            if not cross:
                self._to_plot = self.copol()
            else:
                self._to_plot = self.cross()
                if self._to_plot is None:
                    print('set_to_plot: No crosspol data available. Stick to copol.')
                    self._to_plot = self.copol()


        utils.trace('out')

    def copol(self, set: int=0):
        """Return co-polarisation pattern. In dBi.
        """
        return self._E_mag_co[set]
    # end of function copol

    def cross(self, set: int=0):
        """Return cross-polarisation pattern. In dBi.
        """
        try:
            return self._E_mag_cr[set]
        except IndexError:
            print('cross: This pattern does not have crosspol information.')
            return None
    # end of function cross

    def xpd(self, set: int=0):
        """Return XPD pattern. In dB.
        """
        return self._E_mag_co[set] - self._E_mag_cr[set]
    # end of function xpd

    def satellite(self):
        """return viewer object
        """
        return self._satellite
    # end of function satellite

    def getmax(self, set: int=0):
        """Get max directivity value and coordinates.
        """
        max_value = np.amax(self._to_plot[self._to_plot != np.inf]) + self._conversion_factor
        max_index = np.argmax(self._to_plot[self._to_plot != np.inf])
        max_longitude = self.longitude().flatten()[max_index]
        max_latitude = self.latitude().flatten()[max_index]
        return max_value, max_longitude, max_latitude
    # end of function getmax

    def displaymax(self, map: Basemap, set: int=0):
        """Display max of pattern as a cross on the map.
        """
        max_val, max_lon, max_lat = self.getmax(set)
        max_x, max_y = map(max_lon, max_lat)
        marker = map.plot(x=max_lon, y=max_lat, latlon=True, 
                          marker='+', color='k', fillstyle=None,
                          markersize=2, markeredgewidth=0.2)
        tag = map.ax.annotate('{0:0.2f}'.format(max_val), 
                        xy=(max_x + 1e4, max_y + 1e4), 
                        fontsize=2, fontweight='semibold')
        return marker, tag
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

    def interpolate_copol(self, az, el, set: int=0, spline=None):
        """return interpolated value of the pattern
        """
        if spline == None:
            if self._x[set][0,0] == self._x[set][1,0]:
                x = self._x[set][0, :]
                y = self._y[set][:, 0]
                z = self._to_plot.T
            else:
                x = self._x[set][:, 0]
                y = self._y[set][0, :]
                z = self._to_plot
            if x[0] > x[1]:
                x = x[::-1]
                z = z[::-1,:]
            if y[0] > y[1]:
                y = y[::-1]
                z = z[:,::-1]
            # remove NaN and inf
            z[np.where(np.isnan(z))] = -99
            z[np.where(np.isneginf(z))] = -99
            spline = interp.RectBivariateSpline(x, y, z)
                    
        # transform azel into native coordinates
        x, y = self.azel2xy(az, el)

        return np.reshape(spline.ev(x.flatten(), y.flatten()), np.array(az).shape), spline
    # end of function interpolate_copol

    def interpolate_slope(self, az, el, set: int=0, spline=None):
        """return interpolated value of the pattern
        """
        if spline == None:
            if self._x[set][0,0] == self._x[set][1,0]:
                x = self._x[set][0, :]
                y = self._y[set][:, 0]
                z = self.slope(set).T
            else:
                x = self._x[set][:, 0]
                y = self._y[set][0, :]
                z = self.slope(set)
            spline = interp.RectBivariateSpline(x, y, z)
            
        # transform azel into native coordinates
        x, y = self.azel2xy(az, el)

        # flatten, interpolate and reshape
        return np.reshape(spline.ev(x.flatten(), y.flatten()),np.array(az).shape), spline
    # end of function interpolate_slope

    def shrink_copol(self, azshrink, elshrink, az_co=[], el_co=[], step=None, set: int=0):
        """Shrink pattern using an elliptical beam pointing error.
        This function compute the pattern with different pointing error and
        keep the minimum directivity for each station.
        """
        utils.trace('in')
        # Create azel meshgrid (rectangular grid)
        if step == None:
            az_step = azshrink / 10
            el_step = elshrink / 10
        else:
            az_step = step
            el_step = step
        az_vec = np.arange(-azshrink, azshrink + az_step, az_step)
        el_vec = np.arange(-elshrink, elshrink + el_step, el_step)
        az_grid, el_grid = np.meshgrid(az_vec, el_vec)
        # exclude point out of the ellipse
        for i in range(len(az_grid)):
            for j in range(len(az_grid[i])):
                if (az_grid[i][j]/azshrink)**2 + (el_grid[i][j]/elshrink)**2 > 1:
                    az_grid[i][j] = np.nan
                    el_grid[i][j] = np.nan
        # add points of the ellipse
        # TODO improve this part. Ellipse is not very well defined
        x = np.arange(-azshrink, azshrink + az_step, az_step)
        y = np.arange(-elshrink, elshrink + el_step, el_step)
        y_prime = np.concatenate((elshrink * np.sqrt(1 - x**2 / azshrink**2), -elshrink * np.sqrt(1 - x**2 / azshrink**2)))
        x_prime = np.concatenate((azshrink * np.sqrt(1 - y**2 / elshrink**2), -azshrink * np.sqrt(1 - y**2 / elshrink**2)))

        az_depointing = np.concatenate(([f for f in az_grid.flatten() if not np.isnan(f)], x, x, x_prime))
        el_depointing = np.concatenate(([f for f in el_grid.flatten() if not np.isnan(f)], y_prime, y, y))

        # interpolate copol into a step accurate grid
        if not len(az_co):
            az_co = self.azimuth(set)
        if not len(el_co):
            el_co = self.elevation(set)
        az_co = az_co.flatten()
        el_co = el_co.flatten()
        co = []

        # create interpolation object, and create shrunk pattern
        _, spline = self.interpolate_copol(az_co[0], el_co[0], set)

        def depoint(az_co, el_co):
            depointed_copol, _ = self.interpolate_copol(az_co + az_depointing, el_co + el_depointing, set, spline)
            depointed_copol = depointed_copol[~np.isnan(depointed_copol)]
            return np.min(depointed_copol)

        # for i in range(len(az_co)):
        #     depointed_copol = self.interpolate_copol(az_co[i] + az_depointing, el_co[i] + el_depointing, set, reuse)
        #     # filter NaN value
        #     depointed_copol = depointed_copol[~np.isnan(depointed_copol)]
        #     co.append(np.min(depointed_copol))
        #     reuse = True
        co = np.vectorize(depoint)(az_co, el_co)
        co = np.reshape(co, self.azimuth().shape)

        utils.trace('out')
        # return result pattern
        return co
    # end of function shrink

    def plot(self, map: Basemap, viewer, figure, axes, cbar, cbar_axes):
        """Draw pattern on the earth plot from the provided grd.
        """
        utils.trace('in')

        # project pattern grid in map coordinates
        x, y = map(self.longitude(), self.latitude())
        
        # display either isolevel or color map of slopes 
        if not self._display_slope:
            # try to display isolevel
            # if wrong pol is chosen, isolevel value might not be found, hence an exception is thrown
            # and has to be caught
            try:
                # get linestyles for contour plot
                if 'linestyles' in self._conf:
                    linestyles = self._conf['linestyles']
                else:
                    linestyles = 'solid'
                # get linewidths for contour plot
                if 'linewidths' in self._conf:
                    linewidths = self._conf['linewidths']
                else:
                    linewidths = 0.2
                
                # if shrink pattern option is selected, use shrink_copol function
                cs_pattern = map.contour(x, y,
                                        self._to_plot + self._conversion_factor, 
                                         self._isolevel, 
                                         linestyles=linestyles,
                                         linewidths=linewidths)
                if not self._shrink:
                    cs_marker, cs_tag = self.displaymax(map)
                else:
                    cs_marker = None
                    cs_tag = None
                    # no call to displaymax because it has no meaning when shrinking the pattern

                # add isolevels labels    
                cs_label = figure.axes[0].clabel(cs_pattern, self._isolevel, inline=True, fmt='%1.1f',fontsize=2)
                
                utils.trace('out')
                return cs_pattern, cs_marker, cs_tag, cs_label

            except ValueError as value_err:
                print(value_err)
                print('Pattern ' + self._filename + ' will not be displayed.')
                utils.trace('out')
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
            x = np.tan(az_mesh * cst.DEG2RAD) * self._satellite.altitude()
            y = np.tan(el_mesh * cst.DEG2RAD) * self._satellite.altitude()
            
            # compute plot origin (Nadir of spacecraft)
            x_origin, y_origin = map(self._satellite.longitude(), self._satellite.latitude())
            
            # display color mesh
            cmap = plt.get_cmap('jet')
            cmap.set_over('white', self._slope_range[1])
            cmap.set_under('white', self._slope_range[0])
            
            slope, _ = self.interpolate_slope(az_mesh, el_mesh)

            pcm_pattern = map.pcolormesh(x + x_origin, \
                                    y + y_origin, \
                                    slope, \
                                    vmin=self._slope_range[0], vmax=self._slope_range[1], \
                                    cmap=cmap, alpha=0.5)

            # add color bar
            if cbar:
                cbar = figure.colorbar(pcm_pattern, cax=cbar_axes)     
            else:
                divider = make_axes_locatable(axes)
                cbar_axes = divider.append_axes("right", size="5%", pad=0.05)  
                cbar = figure.colorbar(pcm_pattern, cax=cbar_axes)   
            cbar.ax.set_ylabel('Pattern slope (dB/deg)')
                
            
            utils.trace('out')
            return pcm_pattern

            
        # endif
    # end of method plot

# Mandatory functions and methods to be implemented
#==============================================================================

    @abstractmethod
    def read_file(self, filename):
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
    def azimuth(self, set: int=0):
        """Return azimuth matrix of the data grid points
        """
        pass
    # end of function azimuth

    @abstractmethod
    def elevation(self, set: int=0):
        """Return elevation matrix of the data grid points
        """
        pass
    # end of function elevation

    # @abstractmethod
    # def plot(self, set: int=0):
    #     """Plot itself in an EarthPlot Canvas.
    #     """
    #     pass
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
        # 1: uv-gridse
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

    def azel_grid(self, set: int = 0):
        """This function convert grid format to azimuth elevation.
        """
        def id(x, y):
            return x, y

        convert = {1:ang.uv2azel, \
                   2:ang.thetaphi2azel, \
                   3:id, \
                   4:ang.elovaz2azel, \
                   5:ang.azovel2azel}

        return convert[self.grid_type()](self._x[set], self._y[set])
    # end of function azel_grid

    def azel2xy(self, az, el):
        """Convert (az, el) to native coordinates.
        """
        def id(x, y):
            return x, y

        convert = {1:ang.azel2uv, \
                   2:ang.azel2thetaphi, \
                   3:id, \
                   4:ang.azel2elovaz, \
                   5:ang.azel2azovel}
        return convert[self.grid_type()](az, el)
    
    def ll_grid(self, set: int = 0):
        """ Return (longitude, latitude) grid converted from (az, el) grid.
        """
        az, el = self.azel_grid(set)
        if self._offset:
            az_offset = self._azimuth_offset
            el_offset = self._elevation_offset
        else:
            az_offset = 0
            el_offset = 0
            
        x = self._satellite.altitude() * np.tan((az + az_offset) * cst.DEG2RAD)
        y = self._satellite.altitude() * np.tan((el + el_offset) * cst.DEG2RAD)
        self.proj = prj.Proj(init='epsg:4326 +proj=nsper' + \
                             ' +h=' + str(self._satellite.altitude()) + \
                             ' +a=6378137.00 +b=6378137.00' + \
                             ' +lon_0=' + str(self._satellite.longitude()) + \
                             ' +lat_0=' + str(self._satellite.latitude()) + \
                             ' +x_0=0 +y_0=0 +units=meters +no_defs') 
        return self.proj(x, y, inverse=True)
    # end of function ll_grid    

    def export_to_file(self, filename: str, shrunk: bool = False, set: int = 0):
        """Export this pattern to .pat file.
        """
        utils.trace('in')
        # open file and read text data
        file = open(filename, "w")

        file.write('File generated by GrdViewer\n')

        # end of comment section
        file.write("++++0020\n")

        # format of file
        ny, nx = self._x[set].shape
        file.write("  " + str(self._nb_sets) + ", "
                        + "0" + ", "
                        + "1" + ", " 
                        + str(3) + ", "
                        + str(nx) + ", "
                        + str(ny) + ", "
                        + "0" + ", "
                        + "1" + "\n")

        # limits of grid
        xs = np.min(self.azimuth(set)) * cst.DEG2RAD
        xe = np.max(self.azimuth(set)) * cst.DEG2RAD
        ys = np.min(self.elevation(set)) * cst.DEG2RAD
        ye = np.max(self.elevation(set)) * cst.DEG2RAD
        if self._offset:
            x_offset =  self._azimuth_offset * cst.DEG2RAD
            y_offset =  self._elevation_offset * cst.DEG2RAD
        else:
            x_offset = 0
            y_offset = 0
        file.write("  " + str(xs + x_offset) + ", " 
                        + str(ys + y_offset) + ", "
                        + str(xe + x_offset) + ", "
                        + str(ye + y_offset) + "\n")

        x = np.linspace(xs, xe, nx)
        y = np.linspace(ys, ye, ny)
        x, y = np.meshgrid(x, y)
        x = x * cst.RAD2DEG
        y = y * cst.RAD2DEG
        
        # white line
        file.write(" \n")                
        
        # beam center
        file.write(" 0, 0\n")
        # Frequency
        file.write("1\n")

        # write pattern data
        if shrunk:
            co_to_write = self.shrink_copol(azshrink=self._azshrink, elshrink=self._elshrink, 
                                            az_co=x, el_co=y, set=set)
        else:
            co_to_write, _ = self.interpolate_copol(x, y, set)

        for j in range(ny):
            for i in range(nx):
                file.write('{0:8.3f}'.format(co_to_write[j][i]) + ' ' +
                           '{0:8.3f}'.format(0.0) + '\n')

        # close file
        file.close()
        utils.trace('out')
    # end of function export_to_file


    def revert_x(self, set=0):
        """Revert pattern along x axis.
        """
        self._E_mag_co[set] = self._E_mag_co[set][::-1,:]
        self._E_phs_co[set] = self._E_phs_co[set][::-1,:]
        if len(self._E_mag_cr):
            self._E_mag_cr[set] = self._E_mag_cr[set][::-1,:]
            self._E_phs_cr[set] = self._E_phs_cr[set][::-1,:]

    def revert_y(self, set=0):
        """Revert pattern along y axis.
        """
        self._E_mag_co[set] = self._E_mag_co[set][:, ::-1]
        self._E_phs_co[set] = self._E_phs_co[set][:, ::-1]
        if len(self._E_mag_cr):
            self._E_mag_cr[set] = self._E_mag_cr[set][:, ::-1]
            self._E_phs_cr[set] = self._E_phs_cr[set][:, ::-1]
# end of class Pattern






