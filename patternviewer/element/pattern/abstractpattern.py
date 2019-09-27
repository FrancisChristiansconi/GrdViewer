# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 15:56:00 2018

@author: cfrance
"""

# Standard module import
# ==================================================================================================
# import os function
import os
# import math basic library
import math

# Third party module import
# ==================================================================================================
# import array/calculus utilities
import numpy as np
# import interpolation routine from scipy
from scipy import interpolate as interp
# import pyproj for coordinates conversion
import pyproj as prj
# import path for customised marker
from matplotlib.path import Path
# axes manipulation
from mpl_toolkits.axes_grid1 import make_axes_locatable, Size
# other matplotlib utilities
import matplotlib.pyplot as plt
# import Basemap of mpltoolkit
from mpl_toolkits.basemap import Basemap
# PyQt5 widgets import
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QAction, \
    qApp, QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QWidget, \
    QFileDialog, QLabel, QGridLayout, QCheckBox, QLineEdit
from PyQt5.QtGui import QColor, QPalette
# abstract class toolbox
from abc import ABC, abstractmethod

# Local module import
# ==================================================================================================
# debug
import patternviewer.utils as utils
from patternviewer.viewer import Viewer
import patternviewer.angles as ang
# import constant file
import patternviewer.constant as cst
# Edit dialog
from patternviewer.element.pattern.dialog import PatternDialog
from patternviewer.element.element import Element

# Class definition
# --------------------------------------------------------------------------------------------------


class AbstractPattern(Element):
    """Abstract class representing an antenna pattern. This class define all the
    functions and methods mandatory for compatibility with the viewer features.
    """

# Function and methods common to all
# --------------------------------------------------------------------------------------------------
    def __init__(self, filename=None, conf=None, dialog=False, parent=None):
        """Constructor of abstract class Pattern do nothing.
        """
        utils.trace('in')

        # just initialize object
        super().__init__()

        # get reference to parent object
        self._parent = parent

        # get reference to Earth_plot object
        if self._parent is not None:
            self._earthplot = self._parent.get_earthplot()

        # dictionary with the pattern conf
        self._conf = conf

        # number of data set contained in file
        self._nb_sets = 0

        # complex copol
        self._E_co = []

        # complex crosspol
        self._E_cr = []

        # gradient of first component of co
        self._E_co_grad = []

        # azimuth grid
        self._azimuth = []

        # elevation grid
        self._elevation = []

        # longitude grid
        self._longitude = []

        # latitude grid
        self._latitude = []

        # rotated pattern
        self._rotated = False

        # storage for plot objects
        self._plot = None

        # satellite position
        sat_lon = self.set(conf, 'sat_lon', 0)
        sat_lat = self.set(conf, 'sat_lat', 0)
        sat_alt = self.set(conf, 'sat_alt', cst.ALTGEO)
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
            self._E_co, \
            self._E_cr = self.read_file(conf['filename'])

        # float[]: isolevel for display
        max_directivity = np.max(self.copol())
        self._isolevel = np.array(
            cst.DEFAULT_ISOLEVEL_DBI) + int(max_directivity)

        utils.trace('out')
    # end of constructor

    def reshapedata(self):
        """For interpolation, the azimuth and elevation gradient have to be positive
        """
        # apply to all sets of data
        for set in range(self._nb_sets):

            if (self._x[set][0, 1] > self._x[set][0, 0] and
                    self._y[set][1, 0] > self._y[set][0, 0]):
                # already the good orientation
                pass
            elif (self._x[set][0, 1] < self._x[set][0, 0] and
                  self._y[set][1, 0] > self._y[set][0, 0]):
                # change only x-axis of the grid
                self._x[set] = self._x[set][::-1, :]
                self._y[set] = self._y[set][::-1, :]
                self._E_co[set] = self._E_co[set][::-1, :]
                if len(self._E_cr):
                    self._E_cr[set] = self._E_cr[set][::-1, :]
            elif (self._x[set][0, 1] < self._x[set][0, 0] and
                  self._y[set][1, 0] < self._y[set][0, 0]):
                # change x and y-axes of the grid
                self._x[set] = self._x[set][::-1, ::-1]
                self._y[set] = self._y[set][::-1, ::-1]
                self._E_co[set] = self._E_co[set][::-1, ::-1]
                if len(self._E_cr):
                    self._E_cr[set] = self._E_cr[set][::-1, ::-1]
            elif (self._x[set][0, 1] > self._x[set][0, 0] and
                  self._y[set][1, 0] < self._y[set][0, 0]):
                # change only y-axis of the grid
                self._x[set] = self._x[set][:, ::-1]
                self._y[set] = self._y[set][:, ::-1]
                self._E_co[set] = self._E_co[set][:, ::-1]
                if len(self._E_cr):
                    self._E_cr[set] = self._E_cr[set][:, ::-1]
    # end of reshapedata function

    def generate_grid(self):
        """Generate longitude/latitude and azimuth/elevation grid from
        native format grid.
        """
        for k in range(self._nb_sets):
            self._longitude[k], self._latitude[k] = self.ll_grid(k)
            self._azimuth[k], self._elevation[k] = self.azel_grid(k)
    # end of function generate_grid

    def configure(self, config=None):
        utils.trace('in')
        # if config dictionary is provided, merge it to this instance
        # dictionary
        if config is not None:
            # merge to this instance dictionary
            self._conf.update(config)
            # file name
            self._filename = self.set(self._conf, 'filename')
            # boolean: display slope (True) or isolevel (False)
            self._display_slope = self.set(self._conf, 'display_slope', False)
            # float[]: range of slope displayed
            self._slope_range = self.set(self._conf, 'slopes', [3, 30])
            # boolean: use x axis reverted
            self._revert_x = self.set(self._conf, 'revert_x', False)
            # boolean: use y axis reverted
            self._revert_y = self.set(self._conf, 'revert_y', False)
            # boolean: rotate 180 degrees around sub sat
            self._rotate = self.set(self._conf, 'rotate', False)
            # boolean: use second polarisation as copol
            self._use_second_pol = self.set(
                self._conf, 'use_second_pol', False)
            # boolean: shrink the pattern at display
            self._shrink = self.set(self._conf, 'shrink', False)
            # float: absolute shrink along azimuth in degrees
            self._azshrink = self.set(self._conf, 'azshrink', 0.25)
            # float: absolute shrink along elevation in degrees
            self._elshrink = self.set(self._conf, 'elshrink', 0.25)
            # offset of pattern
            self._offset = self.set(self._conf, 'offset', False)
            # azimuth offset
            self._azimuth_offset = self.set(self._conf, 'azoffset', 0)
            # elevation offset
            self._elevation_offset = self.set(self._conf, 'eloffset', 0)
            # conversion factor
            self._conversion_factor = self.set(self._conf, 'cf', 0)
            # satellite position
            sat_lon = self.set(self._conf, 'sat_lon', 0)
            sat_lat = self.set(self._conf, 'sat_lat', 0)
            sat_alt = self.set(self._conf, 'sat_alt', cst.ALTGEO)
            self._satellite = Viewer(sat_lon, sat_lat, sat_alt)

            # if requested by the new configuration, rotate the pattern
            self.rotate()

            # reshape the grid to correspond to interpolation standard
            self.reshapedata()
            # regenerate longitue/latitude and azimuth/elevation grids
            self.generate_grid()

            # set the data to be plotted according to configuration
            self.set_to_plot(self._use_second_pol)

            # reverse x and y axis if requested
            if self._revert_x:
                self._to_plot = self._to_plot[::-1, :]
            if self._revert_y:
                self._to_plot = self._to_plot[:, ::-1]

            self._isolevel = self.set(self._conf, 'isolevel')
            if self._isolevel is None:
                max_directivity = np.max(self._to_plot)
                self._isolevel = np.array(cst.DEFAULT_ISOLEVEL_DBI) + \
                    int(max_directivity + self._conversion_factor)

        utils.trace('out')
        return self._conf
    # end of function configure

    def set_to_plot(self, cross=False):
        """Set the pattern data to be plotted by the plot method.
        """
        utils.trace('in')

        # select to plot co or cross
        if not cross:
            self._to_plot = self.copol()
        else:
            self._to_plot = self.cross()
            if self._to_plot is None:
                print('set_to_plot: No crosspol data available. ' +
                      'Stick to copol.')
                self._to_plot = self.copol()
        # if shrink option
        if self._shrink:
            # shrink_copol uses interpolate_copol function that
            # uses _to_plot attribute
            self._to_plot = self.shrink_copol(self._azshrink, self._elshrink)
        elif self.set(self.configure(), 'expand', False):
            # expand_copol uses interpolate_copol function that
            # uses _to_plot attribute
            self._to_plot = self.expand_copol(self._azshrink, self._elshrink)

        utils.trace('out')

    def copol(self, set: int = 0):
        """Return co-polarisation pattern. In dBi.
        """
        z = 20.0 * np.log10(np.abs(self._E_co[set]))
        z[np.where(np.isnan(z))] = -99
        z[np.where(np.isneginf(z))] = -99
        return z
    # end of function copol

    def cross(self, set: int = 0):
        """Return cross-polarisation pattern. In dBi.
        """
        try:
            z = 20 * np.log10(np.abs(self._E_cr[set]))
            z[np.where(np.isnan(z))] = -99
            z[np.where(np.isneginf(z))] = -99
            return z
        except IndexError:
            print('cross: This pattern does not have crosspol information.')
            return None
    # end of function cross

    def xpd(self, set: int = 0):
        """Return XPD pattern. In dB.
        """
        return (20 * np.log10(np.abs(self._E_co[set])) -
                20 * np.log10(np.abs(self._E_cr[set])))
    # end of function xpd

    def satellite(self):
        """return viewer object
        """
        return self._satellite
    # end of function satellite

    def getmax(self, set: int = 0):
        """Get max directivity value and coordinates.
        """
        max_value = np.amax(
            self._to_plot[self._to_plot != np.inf]) + self._conversion_factor
        max_index = np.argmax(self._to_plot[self._to_plot != np.inf])
        max_longitude = self.longitude().flatten()[max_index]
        max_latitude = self.latitude().flatten()[max_index]
        return max_value, max_longitude, max_latitude
    # end of function getmax

    def get_isolevel(self):
        """This function is a simple getter for _isolevel attribute.
        """
        return self._isolevel
    # end of function get_isolevel

    def displaymax(self, map: Basemap, set: int = 0):
        """Display max of pattern as a cross on the map.
        """
        plot_width = self._earthplot.get_width()
        plot_height = self._earthplot.get_height()
        x_offset = plot_width / 200
        y_offset = plot_height / 200
        max_val, max_lon, max_lat = self.getmax(set)
        max_x, max_y = map(max_lon, max_lat)
        marker = map.plot(x=max_lon, y=max_lat, latlon=True,
                          marker='+', color='k', fillstyle=None,
                          markersize=2, markeredgewidth=0.2)
        tag = map.ax.annotate('{0:0.2f}'.format(max_val),
                              xy=(max_x + x_offset, max_y + y_offset),
                              fontsize=2, fontweight='semibold')
        return marker, tag
    # end of method displaymax

    def slope(self, set: int = 0):
        """Return gradient of Co-polarisation pattern
        """
        utils.trace('in')
        if self._E_grad_co == []:
            # get gradient of Azimuth coordinate
            azimuth_grad, _ = np.gradient(self.azimuth())
            # get gradient of Elevation coordinate
            _, elevation_grad = np.gradient(self.elevation())
            # get gradient of pattern in Azimuth and Elevation
            co_grad_az, co_grad_el = np.gradient(self._to_plot)
            # normalize gradient of pattern in Azimuth direction
            co_grad_az /= azimuth_grad
            # normalize gradient of pattern in Elevation direction
            co_grad_el /= elevation_grad
            # RSS the 2 directions gradient in one scalar field
            self._E_grad_co = np.sqrt(co_grad_az**2 + co_grad_el**2)
        utils.trace('out')
        return self._E_co_grad
    # end of function slope

    def interpolate_copol(self, az, el, set: int = 0, spline=None):
        """Return interpolated value of the pattern.
        The spline object is also returned for reuse.
        """

        if spline is None:
            if self._x[set][0, 0] == self._x[set][1, 0]:
                x = self._x[set][0, :]
                y = self._y[set][:, 0]
                z = self._to_plot.T
            else:
                x = self._x[set][:, 0]
                y = self._y[set][0, :]
                z = self._to_plot
            if x[0] > x[1]:
                x = x[::-1]
                z = z[::-1, :]
            if y[0] > y[1]:
                y = y[::-1]
                z = z[:, ::-1]
            # remove NaN and inf
            z[np.where(np.isnan(z))] = -99
            z[np.where(np.isneginf(z))] = -99
            spline = interp.RectBivariateSpline(x, y, z)

        # transform azel into native coordinates
        x, y = self.azel2xy(az, el)

        # prepare results for return statement
        a, b = np.reshape(spline.ev(x.flatten(), y.flatten()),
                          np.array(az).shape), spline

        return a, b
    # end of function interpolate_copol

    def interpolate_slope(self, az, el, set: int = 0, spline=None):
        """return interpolated value of the pattern
        """
        utils.trace('in')
        if spline is None:
            if self._x[set][0, 0] == self._x[set][1, 0]:
                x = self._x[set][0, :]
                y = self._y[set][:, 0]
                z = self.slope(set).T
            else:
                x = self._x[set][:, 0]
                y = self._y[set][0, :]
                z = self.slope(set)
            if x[0] > x[1]:
                x = x[::-1]
                z = z[::-1, :]
            if y[0] > y[1]:
                y = y[::-1]
                z = z[:, ::-1]
            z[np.where(np.isnan(z))] = -99
            z[np.where(np.isneginf(z))] = -99
            spline = interp.RectBivariateSpline(x, y, z)

        # transform azel into native coordinates
        x, y = self.azel2xy(az, el)

        # prepare results for return statement
        a, b = np.reshape(spline.ev(x.flatten(), y.flatten()),
                          np.array(az).shape), spline

        utils.trace('out')
        return a, b
    # end of function interpolate_slope

    def shrinkextend(self, shrink, azshrink, elshrink, az_co=[], el_co=[],
                     step=None, set: int = 0):
        """Shrink pattern using an elliptical beam pointing error.
        This function compute the pattern with different pointing error and
        keep the minimum directivity for each station.
        """
        utils.trace('in')
        # Create azel meshgrid (rectangular grid)
        if step is None:
            az_step = azshrink / 10
            el_step = elshrink / 10
        else:
            az_step = step
            el_step = step
        az_vec = np.arange(-azshrink, azshrink + az_step, az_step)
        el_vec = np.arange(-elshrink, elshrink + el_step, el_step)
        az_grid, el_grid = np.meshgrid(az_vec, el_vec)
        # exclude points out of the ellipse
        out_of_ellipse = np.nonzero(
            (az_grid / azshrink) ** 2 + (el_grid / elshrink) ** 2 > 1)
        az_grid[out_of_ellipse] = np.nan
        el_grid[out_of_ellipse] = np.nan
        # add points of the ellipse
        # approximation of ellipse circumference with Ramanujan 1
        a = azshrink
        b = elshrink
        h = ((a - b) / (a + b)) ** 2
        l = np.pi * (a + b) * (3 - np.sqrt(4 - h))
        nb_step = int(l / (2 * min(az_step, el_step))) * 2
        theta = np.linspace(0, 2 * np.pi, nb_step)
        x_ellipse = azshrink * np.cos(theta)
        y_ellipse = elshrink * np.sin(theta)

        # concatenate ellipse filling grid and circumference points
        az_depointing = np.concatenate(([f for f in az_grid.flatten()
                                         if not np.isnan(f)],
                                        x_ellipse))
        el_depointing = np.concatenate(([f for f in el_grid.flatten()
                                         if not np.isnan(f)],
                                        y_ellipse))

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

        def depointmin(az_co, el_co):
            depointed_copol, _ = self.interpolate_copol(az_co + az_depointing,
                                                        el_co + el_depointing,
                                                        set, spline)
            depointed_copol = depointed_copol[~np.isnan(depointed_copol)]
            return np.min(depointed_copol)

        def depointmax(az_co, el_co):
            depointed_copol, _ = self.interpolate_copol(az_co + az_depointing,
                                                        el_co + el_depointing,
                                                        set, spline)
            depointed_copol = depointed_copol[~np.isnan(depointed_copol)]
            return np.max(depointed_copol)

        if shrink is True:
            co = np.vectorize(depointmin)(az_co, el_co)
        else:
            co = np.vectorize(depointmax)(az_co, el_co)
        co = np.reshape(co, self.azimuth().shape)

        utils.trace('out')
        # return result pattern
        return co
    # end of function shrinkextend_copol

    def shrink_copol(self, azshrink, elshrink, az_co=[], el_co=[],
                     step=None, set: int = 0):
        """Shrink pattern using an elliptical beam pointing error.
        This function compute the pattern with different pointing error and
        keep the minimum directivity for each station.
        """
        shrink = True
        return self.shrinkextend(shrink, azshrink, elshrink, az_co, el_co,
                                 step, set)
    # end of function shrink_copol

    def expand_copol(self, azshrink, elshrink, az_co=[], el_co=[],
                     step=None, set: int = 0):
        """Expand pattern using an elliptical beam pointing error.
        This function compute the pattern with different pointing error and
        keep the maximum directivity for each station.
        """
        shrink = False
        return self.shrinkextend(shrink, azshrink, elshrink, az_co, el_co,
                                 step, set)
# ==================================================================================================

# grid conversion functions and getters
# --------------------------------------------------------------------------------------------------
    def azel_grid(self, set: int = 0):
        """This function convert grid format to azimuth elevation.
        set is the data set to be used
        """
        def id(x, y):
            return x, y

        convert = {1: ang.uv2azel,
                   2: ang.thetaphi2azel,
                   3: id,
                   4: ang.elovaz2azel,
                   5: ang.azovel2azel}

        return convert[self.grid_type()](self._x[set], self._y[set])
    # end of function azel_grid

    def azel2xy(self, az, el):
        """Convert (az, el) to native coordinates.
        az is the azimuth coordinate vector to be converted
        el is the elevation coordinate vector to be converted
        """
        def id(x, y):
            return x, y

        convert = {1: ang.azel2uv,
                   2: ang.azel2thetaphi,
                   3: id,
                   4: ang.azel2elovaz,
                   5: ang.azel2azovel}
        return convert[self.grid_type()](az, el)
    # end of function azel2xy

    def ll_grid(self, set: int = 0):
        """Return (longitude, latitude) grid converted from (az, el) grid.
        set is the data set to be used
        """
        # Get azel grid
        az, el = self.azel_grid(set)

        if self._offset:
            if self.set(self.configure(), 'azeloffset', True):
                az_offset = self._azimuth_offset
                el_offset = self._elevation_offset
            else:
                az_offset, el_offset = \
                    self.compute_azel_boresight(self._azimuth_offset,
                                                self._elevation_offset)
        else:
            az_offset = 0
            el_offset = 0

        # apply offset
        az += az_offset    
        el += el_offset
         # rotate azel grid
        yaw_deg = self.set(conf=self.configure(), key='sat_yaw', fallback=0.0)
        yaw_rad = yaw_deg * cst.DEG2RAD
        az_origin = az
        el_origin = el
        az = az_origin * np.cos(-1 * yaw_rad) - \
            el_origin * np.sin(-1 * yaw_rad)
        el = az_origin * np.sin(-1 * yaw_rad) + \
            el_origin * np.cos(-1 * yaw_rad)

        x = self._satellite.altitude() * np.tan((az) * cst.DEG2RAD)
        y = self._satellite.altitude() * np.tan((el) * cst.DEG2RAD)
        self.proj = prj.Proj(init='epsg:4326 +proj=nsper' +
                             ' +h=' + str(self._satellite.altitude()) +
                             ' +a=6378137.00 +b=6378137.00' +
                             ' +lon_0=' + str(self._satellite.longitude()) +
                             ' +lat_0=' + str(self._satellite.latitude()) +
                             ' +x_0=0 +y_0=0 +units=m +no_defs')
        return self.proj(x, y, inverse=True)
    # end of function ll_grid

    def compute_azel_boresight(self, lon=0.0, lat=0.0):
        """Compute the az and el offsets for a given non-null boresight
        of the pattern grid.
        """
        if (lon == self._satellite.longitude() and
                lat == self._satellite.latitude()):
            az = 0.0
            el = 0.0
        else:
            # get projection object
            self.proj = prj.Proj(init='epsg:4326 +proj=nsper' +
                                 ' +h=' + str(self._satellite.altitude()) +
                                 ' +a=6378137.00 +b=6378137.00' +
                                 ' +lon_0=' +
                                 str(self._satellite.longitude()) +
                                 ' +lat_0=' + str(self._satellite.latitude()) +
                                 ' +x_0=0 +y_0=0 +units=m +no_defs')
            x, y = self.proj(lon, lat, inverse=False)
            az = (cst.RAD2DEG *
                  np.arctan2(x, self._satellite.altitude()))
            el = (cst.RAD2DEG *
                  np.arctan2(y, self._satellite.altitude()))
        return az, el

    def latlon2azel(self, lon, lat):
        # get projection object
        self.proj = prj.Proj(init='epsg:4326 +proj=nsper' +
                             ' +h=' + str(self._satellite.altitude()) +
                             ' +a=6378137.00 +b=6378137.00' +
                             ' +lon_0=' +
                             str(self._satellite.longitude()) +
                             ' +lat_0=' + str(self._satellite.latitude()) +
                             ' +x_0=0 +y_0=0 +units=m +no_defs')
        x, y = self.proj(lon, lat, inverse=False)
        az = (cst.RAD2DEG *
              np.arctan2(x, self._satellite.altitude()))
        el = (cst.RAD2DEG *
              np.arctan2(y, self._satellite.altitude()))
        return az, el

    def revert_x(self, set=0):
        """Revert pattern along x axis.
        """
        self._E_co[set] = self._E_co[set][::-1, :]
        if len(self._E_cr):
            self._E_cr[set] = self._E_cr[set][::-1, :]
    # end of method revert_x

    def revert_y(self, set: int = 0):
        """Revert pattern along y axis.
        """
        self._E_co[set] = self._E_co[set][:, ::-1]
        if len(self._E_cr):
            self._E_cr[set] = self._E_cr[set][:, ::-1]
    # end of method revert_y

    def azimuth(self, set: int = 0):
        """Return Azimuth grid for data set of index set
        """
        return self._azimuth[set]
    # end of function azimuth

    def elevation(self, set: int = 0):
        """Return Elevation grid for data set of index set
        """
        return self._elevation[set]
    # end of function elevation

    def longitude(self, set: int = 0):
        """Return longitude grid for data set of index set
        """
        return self._longitude[set]
    # end of function longitude

    def latitude(self, set: int = 0):
        """Return latitude grid for data set of index set
        """
        return self._latitude[set]
    # end of function latitude

    def directivity(self, lon, lat):
        """Return directivity for a vector of stations defined with
        longitude and latitude.
        """
        if np.isnan(lon) or np.isnan(lat):
            return None

        # get projection
        self.proj = prj.Proj(init='epsg:4326 +proj=nsper' +
                             ' +h=' + str(self._satellite.altitude()) +
                             ' +a=6378137.00 +b=6378137.00' +
                             ' +lon_0=' + str(self._satellite.longitude()) +
                             ' +lat_0=' + str(self._satellite.latitude()) +
                             ' +x_0=0 +y_0=0 +units=m +no_defs')
        # consider offset
        if self._offset:
            if self.set(self.configure(), 'azeloffset', True):
                az_offset = self._azimuth_offset
                el_offset = self._elevation_offset
            else:
                az_offset, el_offset = \
                    self.compute_azel_boresight(self._azimuth_offset,
                                                self._elevation_offset)
        else:
            az_offset = 0
            el_offset = 0

        # get az el vector
        x, y = self.proj(lon, lat, inverse=False)
        az = cst.RAD2DEG * \
            np.arctan2(x, self._satellite.altitude())
        el = cst.RAD2DEG * \
            np.arctan2(y, self._satellite.altitude())

        # rotate back azel grid
        yaw_deg = self.set(conf=self.configure(), key='sat_yaw', fallback=0.0)
        yaw_rad = yaw_deg * cst.DEG2RAD
        az_origin = az
        el_origin = el
        az = az_origin * np.cos(yaw_rad) - \
            el_origin * np.sin(yaw_rad)
        el = az_origin * np.sin(yaw_rad) + \
            el_origin * np.cos(yaw_rad)

        # remove offset
        az -= az_offset
        el -= el_offset

        # get directivity vector
        gain, _ = self.interpolate_copol(az, el)
        return gain
    # end of function directivity

# ==================================================================================================


# plot or export to file methods
# --------------------------------------------------------------------------------------------------


    def plot(self):
        """Draw pattern on the earth plot from the provided grd.
        """
        utils.trace('in')
        map = self._earthplot.get_earthmap()
        viewer = self._earthplot._viewer
        figure = self._earthplot._figure
        axes = self._earthplot._axes
        cbar = self._earthplot._clrbar
        cbar_axes = self._earthplot._clrbar_axes
        # choose data to plot
        if not self._display_slope:
            x, y = map(self.longitude(), self.latitude())
            lon_mesh, lat_mesh = self.longitude(), self.latitude()
            x_origin, y_origin = 0, 0
            to_plot = self._to_plot + self._conversion_factor
            isolevelscale = self._isolevel
            maxgain, _, _ = self.getmax()
            colorbarscale = np.amin(self._isolevel), np.ceil(maxgain)
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
            if self._offset:
                az_offset = self._azimuth_offset
                el_offset = self._elevation_offset
            else:
                az_offset = 0
                el_offset = 0
            # convert grid to plot coordinates
            x = self._satellite.altitude() * \
                np.tan((az_mesh + az_offset) * cst.DEG2RAD)

            y = self._satellite.altitude() * \
                np.tan((el_mesh + el_offset) * cst.DEG2RAD)

            # compute plot origin (Nadir of spacecraft)
            # get projection
            self.proj = prj.Proj(init='epsg:4326 +proj=nsper' +
                                 ' +h=' + str(self._satellite.altitude()) +
                                 ' +a=6378137.00 +b=6378137.00' +
                                 ' +lon_0=' +
                                 str(self._satellite.longitude()) +
                                 ' +lat_0=' +
                                 str(self._satellite.latitude()) +
                                 ' +x_0=0 +y_0=0 +units=m +no_defs')
            lon_mesh, lat_mesh = self.proj(x, y, inverse=True)
            # x, y = map(lon_mesh, lat_mesh, inverse=False)
            x_origin, y_origin = 0, 0
            # get interpolated points on a regular grid
            to_plot, _ = self.interpolate_slope(az_mesh, el_mesh)
            isolevelscale = np.arange(np.floor(self._slope_range[0]),
                                      np.ceil(self._slope_range[1]),
                                      3)
            colorbarscale = self._slope_range
        # display either isolevel or color map of slopes
        if not self._conf['Color surface']:
            # try to display isolevel
            # if wrong pol is chosen, isolevel value might not be found,
            # hence an exception is thrown and has to be caught.
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
                # if shrink pattern option is selected,
                # use shrink_copol function
                cs_pattern = map.contour(x + x_origin, y + y_origin,
                                         to_plot,
                                         isolevelscale,
                                         linestyles=linestyles,
                                         linewidths=linewidths)
                if not self._shrink:
                    cs_marker, cs_tag = self.displaymax(map)
                else:
                    cs_marker = None
                    cs_tag = None
                    # no call to displaymax because it has no meaning
                    # when shrinking the pattern
                # add isolevels labels
                cs_label = figure.axes[0].clabel(cs_pattern, isolevelscale,
                                                 inline=True, fmt='%1.1f',
                                                 fontsize=2)
                # Set return value
                self._plot = 'contour', cs_pattern, cs_marker, cs_tag, cs_label

            except ValueError as value_err:
                print(value_err)
                if not type(self._filename) is list:
                    print('Pattern ' +
                          self._filename +
                          ' will not be displayed.')
                else:
                    print(
                        'Law {} will not be displayed.'.format(
                            self._conf['applied_law']))
                self._plot = None

        else:
            # display color mesh
            cmap = plt.get_cmap('jet')
            cmap.set_over('white', np.amax(colorbarscale))
            cmap.set_under('white', np.amin(colorbarscale))

            pcm_pattern = map.pcolormesh(lon_mesh, lat_mesh, to_plot,
                                         vmin=np.amin(colorbarscale),
                                         vmax=np.amax(colorbarscale),
                                         cmap=cmap, alpha=1, latlon=True)

            # add color bar
            if cbar:
                cbar = figure.colorbar(pcm_pattern, cax=cbar_axes)
            else:
                divider = make_axes_locatable(axes)
                cbar_axes = divider.append_axes("right", size="5%", pad=0.05)
                cbar = figure.colorbar(pcm_pattern, cax=cbar_axes)
            if self._conf['display_slope']:
                cbar.ax.set_ylabel('Slope (dB/deg)')
            else:
                cbar.ax.set_ylabel('Gain (dB)')

            self._plot = 'surface', pcm_pattern, cbar, figure
        # endif

        utils.trace('out')
        return self._plot
    # end of method plot

    def clearplot(self):
        utils.trace('in')
        if self._plot is not None:
            if self._plot[0] == 'surface':
                self._plot[1].remove()
                figure = self._plot[3]
                if len(figure.axes) > 1:
                    figure.delaxes(figure.axes[1])
                ax = self._earthplot._axes
                cbax = self._earthplot._clrbar_axes
                divider = make_axes_locatable(ax)
                divider.set_horizontal(
                    [Size.AxesX(ax), Size.Fixed(0), Size.Fixed(0)])
            elif self._plot[0] == 'contour':
                for element in self._plot[1].collections:
                    try:
                        element.remove()
                    except ValueError:
                        print(element)
                if len(self._plot) > 2:
                    try:
                        self._plot[2][0].remove()
                    except TypeError:
                        print("None element cannot be removed")
                    try:
                        self._plot[3].remove()
                    except AttributeError:
                        print("None element have no attribute remove")
                    for element in self._plot[4]:
                        element.remove()
        self._plot = None
        utils.trace('out')

    def export_to_file(self, filename: str, shrunk: bool = False,
                       set: int = 0):
        """Export this pattern to .pat file.
        filename is the target filename
        shrunk is a boolean specifying if the output pattern should be shrunk
        set is the index of the data set to use
        """
        utils.trace('in')
        # open file and read text data
        file = open(filename, "w")

        file.write('File generated by GrdViewer\n')

        # end of comment section
        file.write("++++0020\n")

        # format of file
        ny, nx = self._x[set].shape
        file.write("  " + str(self._nb_sets) + ", " +
                   "0" + ", " +
                   "1" + ", " +
                   str(3) + ", " +
                   str(nx) + ", " +
                   str(ny) + ", " +
                   "0" + ", " +
                   "1" + "\n")

        # limits of grid
        xs = np.min(self.azimuth(set)) * cst.DEG2RAD
        xe = np.max(self.azimuth(set)) * cst.DEG2RAD
        ys = np.min(self.elevation(set)) * cst.DEG2RAD
        ye = np.max(self.elevation(set)) * cst.DEG2RAD

        # recompute boresight
        if self._offset:
            if self.set(self.configure(), 'azeloffset', True):
                az_offset = self._azimuth_offset
                el_offset = self._elevation_offset
            else:
                az_offset, el_offset = \
                    self.compute_azel_boresight(self._azimuth_offset,
                                                self._elevation_offset)
            x_offset = az_offset * cst.DEG2RAD
            y_offset = el_offset * cst.DEG2RAD
        else:
            x_offset = 0
            y_offset = 0

        file.write("  " +
                   str(xs + x_offset) + ", " +
                   str(ys + y_offset) + ", " +
                   str(xe + x_offset) + ", " +
                   str(ye + y_offset) + "\n")
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
            co_to_write = self.shrink_copol(azshrink=self._azshrink,
                                            elshrink=self._elshrink,
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
# ==================================================================================================

# Mandatory functions and methods to be implemented
# --------------------------------------------------------------------------------------------------
    @abstractmethod
    def read_file(self, filename):
        """Read antenna pattern data from file filename.
        """
        pass
    # end of method read_file

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
# ==================================================================================================

# end of class AbstractPattern

# end of module abstractpattern
