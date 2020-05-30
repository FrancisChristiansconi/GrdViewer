# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 15:56:00 2018
AbstractPattern class inherits from Element abstract class.
It is the mother class defining the generic function the patterns subclasses
should implement. It also features the high level functions and methods needed
to manipulate antenna pattern files.

@author: cfrance
"""

# Standard module import
# ==================================================================================================
# import os function
import os
import sys
import logging
# import math basic library
import math

# Third party module import
# ==================================================================================================
# import array/calculus utilities
import numpy as np
# import interpolation routine from scipy
from scipy import interpolate as interp
# import pyproj for coordinates conversion
# import pyproj as prj
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
import simplekml

# Local module import
# ==================================================================================================
# definition of viewer
from patternviewer.viewer import Viewer
# debug
import patternviewer.utils as utils
# conversion between angles
import patternviewer.angles as ang
# import constant file
import patternviewer.constant as cst
# Edit dialog
from patternviewer.element.pattern.dialog import PatternDialog
# abstract mother class Element
from patternviewer.element.element import Element


# Class definition
# --------------------------------------------------------------------------------------------------
class AbstractPattern(Element):
    """Abstract class representing an antenna pattern. This class define all
    the functions and methods mandatory for compatibility with the viewer
    features.
    """

# Function and methods common to all
# --------------------------------------------------------------------------------------------------
    def __init__(self, filename=None, conf=None, dialog=False, parent=None):
        """Constructor of abstract class Pattern do nothing.
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(filename={filename},'
            + 'conf={conf},'
            + 'dialog={dialog},'
            + 'parent={parent})').format(
                filename=filename,
                conf=conf,
                dialog=dialog,
                parent=parent
        ))

        # just initialize object
        super().__init__()

        # get reference to parent object
        self._parent = parent

        # get reference to Earth_plot object
        if self._parent is not None:
            self._earthplot = self._parent.get_earthplot()

        # dictionary with the pattern conf
        # self._conf = conf
        self._configuration = conf

        # number of data set contained in file
        self._nb_sets = 0

        # complex copol
        self._E_co = []

        # complex crosspol
        self._E_cr = []

        # gradient of first component of co
        self._E_grad_co = []

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
        sat_lon = self.set('longitude', 0, float)
        sat_lat = self.set('latitude', 0, float)
        sat_alt = self.set('altitude', cst.ALTGEO, float)
        self._satellite = Viewer(sat_lon, sat_lat, sat_alt)

        self.interpolated_copol = None
        self.interpolated_copol_gradient = None
        self.interpolated_copol_azgrad = None
        self.interpolated_copol_elgrad = None

        # read data file
        try:
            self._nb_sets, \
                self._grid, \
                self._x, \
                self._y, \
                self._E_co, \
                self._E_cr = self.read_file(conf['file'])
        except (IndexError, ValueError):
            logging.error((
                sys._getframe().f_code.co_filename.split('\\')[-1]
                + ':' + sys._getframe().f_code.co_name
                + ': File reading issue: verify format'
            ))
            raise PatternNotCreatedError(
                value=('Error during reading of file: {filename}. '
                       'Verify consistency between extension '
                       'and content.').format(
                           filename=conf['file']))
        except PatternNotCreatedError:
            logging.error((
                sys._getframe().f_code.co_filename.split('\\')[-1]
                + ':' + sys._getframe().f_code.co_name
                + ': Pattern object not created'
            ))
            raise

        # float[]: isolevel for display
        max_directivity = np.max(self.copol())
        self._isolevel = np.array(
            cst.DEFAULT_ISOLEVEL_DBI) + int(max_directivity)
    # end of constructor

    def reshapedata(self):
        """For interpolation, the azimuth and elevation gradient have
        to be positive
        """
        # apply to all sets of data
        for set in range(self._nb_sets):
            def x_inc():
                return self._x[set][0, 1] > self._x[set][0, 0]

            def x_dec():
                return self._x[set][0, 1] < self._x[set][0, 0]

            def y_inc():
                return self._y[set][1, 0] > self._y[set][0, 0]

            def y_dec():
                return self._y[set][1, 0] < self._y[set][0, 0]

            if x_inc() and y_inc():
                # already the good orientation
                pass
            elif x_dec() and y_inc():
                # change only x-axis of the grid
                self._x[set] = self._x[set][::-1, :]
                self._y[set] = self._y[set][::-1, :]
                self._E_co[set] = self._E_co[set][::-1, :]
                if len(self._E_cr):
                    self._E_cr[set] = self._E_cr[set][::-1, :]
            elif x_dec() and y_dec():
                # change x and y-axes of the grid
                self._x[set] = self._x[set][::-1, ::-1]
                self._y[set] = self._y[set][::-1, ::-1]
                self._E_co[set] = self._E_co[set][::-1, ::-1]
                if len(self._E_cr):
                    self._E_cr[set] = self._E_cr[set][::-1, ::-1]
            elif x_inc() and y_dec():
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
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(config={config})').format(
                config=config
        ))
        # if config dictionary is provided, merge it to this instance
        # dictionary
        if config is not None:
            # merge to this instance dictionary
            self._configuration.update(config)
            # boolean: display slope (True) or isolevel (False)
            self._configuration['slope'] = self.set(
                'slope', False, dtype=bool)
            # float[]: range of slope displayed
            self._configuration['slopes'] = self.set(
                'slopes', [3, 30], list)
            # boolean: use x axis reverted
            self._configuration['revert x-axis'] = self.set(
                'revert x-axis', False, bool)
            # boolean: use y axis reverted
            self._configuration['revert y-axis'] = self.set(
                'revert y-axis', False, bool)
            # boolean: rotate 180 degrees around sub sat
            self._configuration['rotate'] = self.set(
                'rotate', False, bool)
            # boolean: use second polarisation as copol
            self._configuration['second polarisation'] = self.set(
                'second polarisation', False, bool)
            # boolean: shrink the pattern at display
            self._configuration['shrink'] = self.set(
                'shrink', False, bool)
            self._configuration['expand'] = self.set(
                'expand', False, bool)
            # float: absolute shrink along azimuth in degrees
            self._configuration['azimuth shrink'] = self.set(
                'azimuth shrink', 0.0, float)
            # float: absolute shrink along elevation in degrees
            self._configuration['elevation shrink'] = self.set(
                'elevation shrink', 0.0, float)
            # offset of pattern
            self._configuration['offset'] = self.set(
                'offset', False, bool)
            self._configuration['offset azel format'] = self.set(
                'offset azel format', False, bool)
            # azimuth offset
            self._configuration['azimuth offset'] = self.set(
                'azimuth offset', 0.0, float)
            # elevation offset
            self._configuration['elevation offset'] = self.set(
                'elevation offset', 0.0, float)
            # conversion factor
            self._configuration['conversion factor'] = self.set(
                'conversion factor', 0, float)
            # satellite position
            self._configuration['longitude'] = self.set(
                'longitude', 0.0, float)
            self._configuration['latitude'] = self.set(
                'latitude', 0.0, float)
            self._configuration['altitude'] = self.set(
                'altitude', cst.ALTGEO, float)
            self._configuration['yaw'] = self.set(
                'yaw', 0.0, float)
            self._satellite = Viewer(
                lon=self._configuration['longitude'],
                lat=self._configuration['latitude'],
                alt=self._configuration['altitude'])
            # iso-levels or surface color
            self._configuration['color surface'] = self.set(
                'color surface', False, bool)

            # linewidths for display
            try:
                self._configuration['linewidths'] = cst.BOLDNESS[
                    self._configuration['linewidths']]
            except KeyError:
                # will happen if already converted
                pass

            # if requested by the new configuration, rotate the pattern
            self.rotate()

            # reshape the grid to correspond to interpolation standard
            self.reshapedata()
            # regenerate longitue/latitude and azimuth/elevation grids
            self.generate_grid()

            # set the data to be plotted according to configuration
            self.set_to_plot(self._configuration['second polarisation'])

            # reverse x and y axis if requested
            if self._configuration['revert x-axis']:
                self._to_plot = self._to_plot[::-1, :]
            if self._configuration['revert y-axis']:
                self._to_plot = self._to_plot[:, ::-1]

            self._isolevel = self.set('level', dtype=str)
            if self._isolevel is None:
                max_directivity = np.max(self._to_plot)
                self._isolevel = np.array(cst.DEFAULT_ISOLEVEL_DBI) + \
                    int(max_directivity
                        + self._configuration['conversion factor'])
            else:
                self._isolevel = self.lvl_str_to_list(self._isolevel)

        return self._configuration
    # end of function configure

    def lvl_str_to_list(self, level_str):
        str_list = level_str.split(',')
        flt_list = []
        for l in str_list:
            if not ':'in l:
                flt_list.append(float(l))
            else:
                sub_list = l.split(':')
                str_list.remove(l)
                if len(sub_list) == 2:
                    sub_range = np.arange(
                        float(sub_list[0]),
                        float(sub_list[1]) + 1)
                elif len(sub_list) == 3:
                    sub_range = np.arange(
                        float(sub_list[0]),
                        float(sub_list[2]) + float(sub_list[1]),
                        float(sub_list[1]))
                for r in sub_range:
                    flt_list.append(r)
        return flt_list

    def set_to_plot(self, cross=False):
        """Set the pattern data to be plotted by the plot method.
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(cross={cross})').format(
                cross=cross
        ))

        # select to plot co or cross
        if not cross:
            self._to_plot = self.copol()
        else:
            self._to_plot = self.cross()
            if self._to_plot is None:
                print(
                    'set_to_plot: No crosspol data available. Stick to copol.')
                self._to_plot = self.copol()
        # if shrink option
        if self._configuration['shrink']:
            # shrink_copol uses interpolate_copol function that
            # uses _to_plot attribute
            self._to_plot = self.shrink_copol(
                self._configuration['azimuth shrink'],
                self._configuration['elevation shrink'])
        elif self.set('expand', False, bool):
            # expand_copol uses interpolate_copol function that
            # uses _to_plot attribute
            self._to_plot = self.expand_copol(
                self._configuration['azimuth shrink'],
                self._configuration['elevation shrink'])
    # end of function set_to_plot

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
        return (20 * np.log10(np.abs(self._E_co[set])) - 20 * np.log10(
            np.abs(self._E_cr[set])))
    # end of function xpd

    def satellite(self):
        """return viewer object
        """
        return self._satellite
    # end of function satellite

    def getmax(self, set: int = 0):
        """Get max directivity value and coordinates.
        """
        max_value = (np.amax(self._to_plot[self._to_plot != np.inf])
                     + self._configuration['conversion factor'])
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
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(set={set})').format(
                set=set
        ))
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
        return self._E_grad_co
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
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(az={az},'
            + 'el={el},'
            + 'set={set},'
            + 'spline={spline})').format(
                az=az,
                el=el,
                set=set,
                spline=sline
        ))
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
        return a, b
    # end of function interpolate_slope

    def shrinkextend(self, shrink, azshrink, elshrink, az_co=[], el_co=[],
                     step=None, set: int = 0):
        """Shrink pattern using an elliptical beam pointing error.
        This function compute the pattern with different pointing error and
        keep the minimum directivity for each station.
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(shrink={shrink},'
            + 'azshrink={azshrink},'
            + 'elshrink={elshrink},'
            + 'az_co={az_co},'
            + 'el_co={el_co},'
            + 'step={step},'
            + 'set={set})').format(
                shrink=shrink,
                azshrink=azshrink,
                elshrink=elshrink,
                az_co=az_co,
                el_co=el_co,
                step=step,
                set=set
        ))
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
        numerator = np.pi * (a + b) * (3 - np.sqrt(4 - h))
        nb_step = int(numerator / (2 * min(az_step, el_step))) * 2
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

        if self._configuration['offset']:
            if self.set('offset azel format', True, bool):
                az_offset = self._configuration['azimuth offset']
                el_offset = self._configuration['elevation offset']
            else:
                az_offset, el_offset = self.compute_azel_boresight(
                    self.set('longitude offset', 0.0, float),
                    self.set('latitude offset', 0.0, float))
        else:
            az_offset = 0
            el_offset = 0

        # apply offset
        az += az_offset
        el += el_offset
        # rotate azel grid
        yaw_deg = self.set(key='yaw',
                           fallback=0.0, dtype=float)
        yaw_rad = yaw_deg * cst.DEG2RAD
        az_origin = az
        el_origin = el
        az = az_origin * np.cos(-1 * yaw_rad) - \
            el_origin * np.sin(-1 * yaw_rad)
        el = az_origin * np.sin(-1 * yaw_rad) + \
            el_origin * np.cos(-1 * yaw_rad)

        x = self._satellite.altitude() * np.tan((az) * cst.DEG2RAD)
        y = self._satellite.altitude() * np.tan((el) * cst.DEG2RAD)
        return self._satellite.projection(x, y, inverse=True)
    # end of function ll_grid

    def compute_azel_boresight(self, lon=0.0, lat=0.0):
        """Compute the az and el offsets for a given non-null boresight
        of the pattern grid.
        """
        if (lon == self._satellite.longitude()
            and lat == self._satellite.latitude()):
            az = 0.0
            el = 0.0
        else:
            # get projection object
            x, y = self._satellite.projection(lon, lat, inverse=False)
            az = (cst.RAD2DEG
                  * np.arctan2(x, self._satellite.altitude()))
            el = (cst.RAD2DEG
                  * np.arctan2(y, self._satellite.altitude()))
        return az, el

    def latlon2azel(self, lon, lat):
        # get projection object
        x, y = self._satellite.projection(lon, lat, inverse=False)
        az = (cst.RAD2DEG
              * np.arctan2(x, self._satellite.altitude()))
        el = (cst.RAD2DEG
              * np.arctan2(y, self._satellite.altitude()))
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

        # consider offset
        if self._configuration['offset']:
            if self.set('offset azel format', True, bool):
                az_offset = self._configuration['azimuth offset']
                el_offset = self._configuration['elevation offset']
            else:
                az_offset, el_offset = self.compute_azel_boresight(
                    self._configuration['longitude offset'],
                    self._configuration['latitude offset'])
        else:
            az_offset = 0
            el_offset = 0

        # get az el vector
        x, y = self._satellite.projection(lon, lat, inverse=False)
        az = cst.RAD2DEG * \
            np.arctan2(x, self._satellite.altitude())
        el = cst.RAD2DEG * \
            np.arctan2(y, self._satellite.altitude())

        # rotate back azel grid
        yaw_deg = self.set(key='yaw',
                           fallback=0.0, dtype=float)
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
    def plot(self, label=True):
        """Draw pattern on the earth plot from the provided grd.
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
        ))
        map = self._earthplot.get_earthmap()
        viewer = self._earthplot._viewer
        figure = self._earthplot._figure
        axes = self._earthplot._axes
        cbar = self._earthplot._clrbar
        cbar_axes = self._earthplot._clrbar_axes
        # choose data to plot
        if not self._configuration['slope']:
            x, y = map(self.longitude(), self.latitude())
            lon_mesh, lat_mesh = self.longitude(), self.latitude()
            x_origin, y_origin = 0, 0
            to_plot = self._to_plot + self._configuration['conversion factor']
            isolevelscale = self._isolevel
            maxgain, _, _ = self.getmax()
            colorbarscale = np.amin(isolevelscale), np.ceil(maxgain)
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
            if self._configuration['offset']:
                if self._configuration['offset azel format']:
                    az_offset = self._configuration['azimuth offset']
                    el_offset = self._configuration['elevation offset']
                else:
                    az_offset, el_offset = self.compute_azel_boresight(
                        self._configuration['longitude offset'],
                        self._configuration['latitude offset'])
            else:
                az_offset = 0
                el_offset = 0
            # convert grid to plot coordinates
            x = self._satellite.altitude() * \
                np.tan((az_mesh + az_offset) * cst.DEG2RAD)

            y = self._satellite.altitude() * \
                np.tan((el_mesh + el_offset) * cst.DEG2RAD)

            # compute plot origin (Nadir of spacecraft)
            lon_mesh, lat_mesh = self._satellite.projection(x, y, inverse=True)
            # x, y = map(lon_mesh, lat_mesh, inverse=False)
            x_origin, y_origin = 0, 0
            # get interpolated points on a regular grid
            to_plot, _ = self.interpolate_slope(az_mesh, el_mesh)
            isolevelscale = np.arange(
                np.floor(self._configuration['slopes'][0]),
                np.ceil(self._configuration['slopes'][1]),
                3)
            colorbarscale = self._configuration['slopes']
        # display either isolevel or color map of slopes
        if not self._configuration['color surface']:
            # try to display isolevel
            # if wrong pol is chosen, isolevel value might not be found,
            # hence an exception is thrown and has to be caught.
            try:
                # get linestyles for contour plot
                if 'linestyles' in self._configuration:
                    linestyles = self._configuration['linestyles']
                else:
                    linestyles = 'solid'
                # get linewidths for contour plot
                if 'linewidths' in self._configuration:
                    linewidths = self._configuration['linewidths']
                else:
                    linewidths = 0.2
                # if shrink pattern option is selected,
                # use shrink_copol function
                cs_pattern = map.contour(x + x_origin, y + y_origin,
                                         to_plot,
                                         isolevelscale,
                                         linestyles=linestyles,
                                         linewidths=linewidths)
                if not self._configuration['shrink']:
                    cs_marker, cs_tag = self.displaymax(map)
                else:
                    cs_marker = None
                    cs_tag = None
                    # no call to displaymax because it has no meaning
                    # when shrinking the pattern
                # add isolevels labels
                if label:
                    cs_label = figure.axes[0].clabel(
                        cs_pattern, isolevelscale,
                        inline=True, fmt='%1.1f',
                        fontsize=2)
                else:
                    cs_label = None
                # Set return value
                self._plot = 'contour', cs_pattern, cs_marker, cs_tag, cs_label

            except ValueError as value_err:
                # TODO add error/warning logs
                print(value_err)
                if not type(self._configuration['file']) is list:
                    print(('Pattern {file}'
                           ' will not be displayed.').format(
                               file=self._configuration['file']))
                else:
                    print(
                        'Law {} will not be displayed.'.format(
                            self._configuration['applied_law']))
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
            if self._configuration['slope']:
                cbar.ax.set_ylabel('Slope (dB/deg)')
            else:
                cbar.ax.set_ylabel('Gain (dB)')

            self._plot = 'surface', pcm_pattern, cbar, figure
        # endif

        return self._plot
    # end of method plot

    def clearplot(self):
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
        ))
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

    def export_to_pat(self, filename: str, shrunk: bool = False,
                      set: int = 0, data=None, x=None, y=None):
        """Export this pattern to .pat file.
        filename is the target filename
        shrunk is a boolean specifying if the output pattern should be shrunk
        set is the index of the data set to use
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(filename={filename},'
            + 'shrunk={shrunk},'
            + 'set={set},'
            + 'data={data},'
            + 'x={x},'
            + 'y={y},)').format(
                filename=filename,
                shrunk=shrunk,
                set=set,
                data=data,
                x=x,
                y=y
        ))

        regrid = False
        if x is not None and y is not None:
            if len(x) == len(y) == 3:
                _nx, _xs, _xe = x
                _ny, _ys, _xe = y
                regrid = True
            else:
                raise TypeError(
                    ('x an y should be tuple of kind '
                     + '(nx, xs, xe) and (ny, ys, ye)')
                )
        # open file and read text data
        file = open(filename, "w")

        file.write('File generated by GrdViewer\n')

        # end of comment section
        file.write("++++0020\n")

        # format of file
        if regrid:
            ny, nx = _ny, _nx
        else:
            ny, nx = self._x[set].shape
        file.write(
            "  {nset:d}, 0, 1, 3, {nx:d}, {ny:d}, 0, 1\n".format(
                nset=self._nb_sets,
                nx=nx,
                ny=ny))

        # limits of grid
        if regrid:
            xs = np.min(self.azimuth(set)) * cst.DEG2RAD
            xe = np.max(self.azimuth(set)) * cst.DEG2RAD
            ys = np.min(self.elevation(set)) * cst.DEG2RAD
            ye = np.max(self.elevation(set)) * cst.DEG2RAD
        else:
            xs = _xs
            xe = _xe
            ys = _ys
            ye = _ye

        # recompute boresight
        if self._configuration['offset']:
            if self.set('offset azel format', True, bool):
                az_offset = self._configuration['azimuth offset']
                el_offset = self._configuration['elevation offset']
            else:
                az_offset, el_offset = self.compute_azel_boresight(
                    self._configuration['longitude offset'],
                    self._configuration['latitude offset'])
            x_offset = az_offset * cst.DEG2RAD
            y_offset = el_offset * cst.DEG2RAD
        else:
            x_offset = 0
            y_offset = 0

        file.write("  {xs:0.10E}, {ys:0.10E}, {xe:0.10E}, {ye:0.10E}\n".format(
            xs=xs + x_offset,
            ys=ys + y_offset,
            xe=xe + x_offset,
            ye=ye + y_offset))
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
        if data is None:
            if shrunk:
                co_to_write = self.shrink_copol(
                    azshrink=self._configuration['azimuth shrink'],
                    elshrink=self._configuration['elevation shrink'],
                    az_co=x, el_co=y, set=set)
            else:
                co_to_write, _ = self.interpolate_copol(x, y, set)
        else:
            co_to_write = data

        for j in range(ny):
            for i in range(nx):
                file.write('{co:8.3f} {cross:8.3f}\n'.format(
                    co=co_to_write[j][i],
                    cross=0.0))

        # close file
        file.close()
        logging.info((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + ': Exported pattern to : {filename}').format(
                filename=filename
        ))
    # end of function export_to_pat

    def export_to_grd(self, filename: str, shrunk: bool = False, set: int = 0):
        """Export this pattern to .grd file.
        filename is the target filename
        shrunk is a boolean specifying if the output pattern should be shrunk
        set is the index of the data set to use
        TODO: finish the work
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(filename={filename},'
            + 'shrunk={shrunk},'
            + 'set={set})').format(
                filename=filename,
                shrunk=shrunk,
                set=set
        ))

        # open file and read text data
        file = open(filename, "w")

        file.write('File generated by GrdViewer\n')

        # end of comment section
        file.write("++++\n")

        # write header
        # write ktype, should always be 1
        file.write('{:4d}'.format(1))
        # next line gives:
        # number of patterns: self._nb_sets
        # field components: icomp=3 (linear co and cx)
        # number of field components: ncomp=2 (far field)
        # grid type: grid=5 (elevation and azimuth)
        file.write('{nset:4d}{icomp:4d}{ncomp:4d}{grid:4d}'.format(
            nset=1,
            icomp=3,
            ncomp=2,
            grid=5
        ))
        # center of grid for each set
        file.write('{ix:4d}{iy:4d}'.format(
            ix=0,
            iy=0
        ))
        # limits of grid
        xs = np.min(self.azimuth(set))
        xe = np.max(self.azimuth(set))
        ys = np.min(self.elevation(set))
        ye = np.max(self.elevation(set))
        file.write((' {xs: 0.10E} {xe: 0.10E} {ys: 0.10E} {ye: 0.10E}').format(
            xs=xs, xe=xe, ys=ys, ye=ye
        ))
        # number of rows and columns and klimit=0
        ny, nx = self._x[set].shape
        klimit = 0
        file.write('{nx: 4d}{ny: 4d}{klimit: 4d}'.format(
            nx=nx, ny=ny, klimit=klimit
        ))

    def export_to_kml(self, filename: str):
        # create instance of Kml
        kml = simplekml.Kml()

        # test if there is a plot and if the plot is contour
        if self._plot is not None:
            # replot without labels (to have nice lines)
            self.plot(label=False)
            if self._plot[0] == 'contour':
                for i in range(len(self._isolevel)):
                    level = self._isolevel[i]
                    # get used color
                    color = self._plot[1].collections[i]._original_edgecolor
                    # get all the polygons for this level
                    contours = self._plot[1].collections[i]._paths
                    for contour in contours:
                        # get coordinates and convert
                        map_coords = contour.vertices
                        lon, lat = self._earthplot._earth_map(
                            map_coords[:, 0], map_coords[:, 1], inverse=True)
                        llg_coords = np.stack((lon, lat), axis=1)

                        lin = kml.newlinestring(
                            name='{:0.2f}'.format(level),
                            coords=llg_coords)
                        r, g, b, a = color[0]
                        r = int(r * 255)
                        g = int(g * 255)
                        b = int(b * 255)
                        a = int(a * 255)
                        lin.style.linestyle.color = simplekml.Color.rgb(
                            r, g, b, a)
            self.plot()
        kml.save(filename)

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


class PatternNotCreatedError(Exception):
    """Exception to flag something went wrong when creating pattern
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

# end of module abstractpattern
