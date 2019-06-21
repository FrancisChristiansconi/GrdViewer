"""This module contains the class definition for the canvas containing
the Earth plot and all the subsequent elements plots.
"""

# Imports

# import os module for files and directories manipulation
import os

# import Matplotlib and Base_earth_map
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_qt5agg \
    import FigureCanvasQTAgg as FigureCanvas

# import PyQt5
from PyQt5.QtWidgets import QSizePolicy
from PyQt5 import QtCore

# import numpy for arrays and mathematical operations
import numpy as np

# local module
import patternviewer.utils as utils
from patternviewer.element.pattern.control import PatternControler
from patternviewer.element import station as stn
# import patternviewer.element.station as stn
import patternviewer.element.elevation as elv
from patternviewer.viewer import Viewer
from patternviewer.zoom import Zoom

# import constant file
import patternviewer.constant as cst


class EarthPlot(FigureCanvas):
    """This class is the core of the appliccation. It display the Earth
    map, the patterns, stations, elevation contour, etc.
    """

    # EarthPlot constructor
    def __init__(self, parent=None, width=5, height=5, dpi=300,
                 proj='nsper', res='crude', config=None):
        utils.trace('in')

        # Store Canvas properties
        self._plot_title = 'Default Title'
        self._width = width
        self._height = height
        self._dpi = dpi
        self._centralwidget = parent
        self._app = self._centralwidget.parent()
        # store _earth_map properties
        self._projection = proj
        self._resolution = res

        # define figure in canvas
        self._figure = Figure(figsize=(self._width, self._height),
                              dpi=self._dpi)
        self._axes = self._figure.add_subplot(111)

        FigureCanvas.__init__(self, self._figure)
        self.setParent(self._centralwidget)
        self._app = self.parent().parent()
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setFocus()

        # initialize EarthPlot fields
        self._patterns = {}
        self._elev = {}
        self._stations = []
        self._polygons = []
        self._clrbar = None
        self._clrbar_axes = None
        self._earth_map = None
        self._coastlines_col = None
        self._countries_col = None
        self._parallels_col = None
        self._meridians_col = None

        # initialize PPlot limits
        self.llcrnrx = None
        self.llcrnry = None
        self.urcrnrx = None
        self.urcrnry = None
        self.llcrnrlon = None
        self.llcrnrlat = None
        self.urcrnrlon = None
        self.urcrnrlat = None
        self.centerx = None
        self.centery = None
        self.cntrlon = None
        self.cntrlat = None

        # if a config has been provided by caller
        if config:
            # get font size with fallback = 5
            fontsize = config.getint('DEFAULT', 'font size', fallback=5)
            # set default font size
            plt.rcParams.update({'font.size': fontsize})
            self._axes.xaxis.label.set_fontsize(fontsize)
            self._axes.yaxis.label.set_fontsize(fontsize)

            # set map resolution (take only first letter in lower case)
            self._resolution = config.get('DEFAULT',
                                          'map resolution',
                                          fallback=self._resolution).lower()
            self._app.getmenuitem(
                item='View>Map resolution>' +
                self._resolution).setChecked(True)
            self._resolution = self._resolution[0]
            self._projection = config.get(
                'DEFAULT', 'projection', fallback='nsper')
            if self._projection == 'nsper':
                self._app.getmenuitem(
                    item='View>Projection>Geo').setChecked(True)
            elif self._projection == 'cyl':
                self._app.getmenuitem(
                    item='View>Projection>Cylindrical').setChecked(True)

            # get point of view coordinates if defined
            longitude = config.getfloat('VIEWER', 'longitude', fallback=0.0)
            latitude = config.getfloat('VIEWER', 'latitude', fallback=0.0)
            altitude = config.getfloat(
                'VIEWER', 'altitude', fallback=cst.ALTGEO)

            # get Earth plot configuration
            self._bluemarble = config.getboolean(
                'DEFAULT', 'blue marble', fallback=False)
            self._app.getmenuitem(
                item='View>Blue Marble').setChecked(self._bluemarble)
            self._coastlines = config.get(
                'DEFAULT', 'coast lines', fallback='light')
            self._app.getmenuitem(
                item='View>Coast lines>' + self._coastlines).setChecked(True)
            self._countries = config.get(
                'DEFAULT', 'countries', fallback='light')
            self._app.getmenuitem(
                item='View>Country borders>' +
                self._countries).setChecked(True)
            self._parallels = config.get(
                'DEFAULT', 'parallels', fallback='light')
            self._app.getmenuitem(
                item='View>Parallels>' + self._parallels).setChecked(True)
            self._meridians = config.get(
                'DEFAULT', 'meridians', fallback='light')
            self._app.getmenuitem(
                item='View>Meridians>' + self._meridians).setChecked(True)

            # initialize angle of view
            # Satellite Longitude, latitude and altitude
            self._viewer = Viewer(lon=longitude, lat=latitude, alt=altitude)

            # get default directory
            self.rootdir = config.get('DEFAULT', 'root', fallback='C:\\')

            # Initialize zoom
            self._zoom = Zoom(self._projection)
            self._zoom.min_azimuth = config.getfloat(
                'GEO', 'min azimuth', fallback=-9)
            self._zoom.min_elevation = config.getfloat(
                'GEO', 'min elevation', fallback=-9)
            self._zoom.max_azimuth = config.getfloat(
                'GEO', 'max azimuth', fallback=9)
            self._zoom.max_elevation = config.getfloat(
                'GEO', 'max elevation', fallback=9)
            self._zoom.min_longitude = config.getfloat(
                'CYLINDRICAL', 'min longitude', fallback=-180)
            self._zoom.min_latitude = config.getfloat(
                'CYLINDRICAL', 'min latitude', fallback=-90)
            self._zoom.max_longitude = config.getfloat(
                'CYLINDRICAL', 'max longitude', fallback=180)
            self._zoom.max_latitude = config.getfloat(
                'CYLINDRICAL', 'max latitude', fallback=90)
            pattern_index = 1
            pattern_section = 'PATTERN' + str(pattern_index)
            while pattern_section in config:
                if 'file' in config[pattern_section]:
                    conf = {}
                    conf['filename'] = config.get(pattern_section, 'file')
                    conf['sat_lon'] = config.getfloat(pattern_section,
                                                      'longitude',
                                                      fallback=0.0)
                    conf['sat_lat'] = config.getfloat(pattern_section,
                                                      'latitude',
                                                      fallback=0.0)
                    conf['sat_alt'] = config.getfloat(pattern_section,
                                                      'altitude',
                                                      fallback=cst.ALTGEO)
                    conf['title'] = config.get(pattern_section,
                                               'title',
                                               fallback='Default title')
                    conf['level'] = config.get(pattern_section,
                                               'level',
                                               fallback='25, 30, 35, 38, 40')
                    conf['revert_x'] = config.getboolean(pattern_section,
                                                         'revert x-axis',
                                                         fallback=False)
                    conf['revert_y'] = config.getboolean(pattern_section,
                                                         'revert y-axis',
                                                         fallback=False)
                    conf['rotate'] = config.getboolean(pattern_section,
                                                       'rotate',
                                                       fallback=False)
                    conf['use_second_pol'] = \
                        config.getboolean(pattern_section,
                                          'second polarisation',
                                          fallback=False)
                    conf['display_slope'] = \
                        config.getboolean(pattern_section,
                                          'slope',
                                          fallback=False)
                    conf['shrink'] = config.getboolean(pattern_section,
                                                       'shrink',
                                                       fallback=False)
                    conf['azshrink'] = config.getfloat(pattern_section,
                                                       'azimuth shrink',
                                                       fallback=0.0)
                    conf['elshrink'] = config.getfloat(pattern_section,
                                                       'elevation shrink',
                                                       fallback=0.0)
                    conf['offset'] = config.getboolean(pattern_section,
                                                       'offset',
                                                       fallback=False)
                    conf['azeloffset'] = config.getboolean(pattern_section,
                                                           'azeloffset',
                                                           fallback=True)
                    conf['azoffset'] = config.getfloat(pattern_section,
                                                       'azimuth offset',
                                                       fallback=0.0)
                    conf['eloffset'] = config.getfloat(pattern_section,
                                                       'elevation offset',
                                                       fallback=0.0)
                    conf['cf'] = config.getfloat(pattern_section,
                                                 'conversion factor',
                                                 fallback=0.0)
                    conf['linestyles'] = config.get(pattern_section,
                                                    'linestyles',
                                                    fallback='solid')
                    conf['linewidths'] = \
                        cst.BOLDNESS[config.get(pattern_section,
                                                'linewidths',
                                                fallback='medium')]
                    conf['isolevel'] = [float(s)
                                        for s in conf['level'].split(',')]
                    conf['Color surface'] = config.getboolean(pattern_section,
                                                              'Color surface',
                                                              fallback=False)

                    self.loadpattern(conf=conf)

                    self.settitle(conf['title'])

                    # check for next pattern
                    pattern_index += 1
                    pattern_section = 'PATTERN' + str(pattern_index)
            # add stations from ini file
            station_index = 1
            station_section = 'STATION' + str(station_index)
            while station_section in config:
                # load stations from sta file
                if 'file' in config[station_section]:
                    station_file = config.get(station_section, 'file')
                    self._stations.extend(
                        stn.get_station_from_file(station_file, self))
                # load station from description in ini file
                elif 'name' in config[station_section]:
                    station = stn.Station(parent=self)
                    station.configure(config._sections[station_section])
                    self._stations.append(station)
                # check for next station section
                station_index += 1
                station_section = 'STATION' + str(station_index)
            # add elevation contour from ini file
            elevation_index = 1
            elevation_section = 'ELEVATION' + str(elevation_index)
            while elevation_section in config:
                # load stations from sta file
                elevationlist = [
                    float(s) for s in
                    config._sections[
                        elevation_section]['elevation'].split(',')]
                for elevation_value in elevationlist:
                    conf = config._sections[elevation_section]
                    conf['elevation'] = elevation_value
                    elevation = elv.Elevation(parent=self)
                    elevation.configure(conf)
                    self._elev['Elev[' + str(elevation_value) + ']'
                               ] = elevation
                # check for next station section
                elevation_index += 1
                elevation_section = 'ELEVATION' + str(elevation_index)

        # initialise reference to Blue Marble
        self._bluemarble_imshow = None

        # default file name to save figure
        self.filename = 'plot.PNG'

        # connect canvas to mouse event (enable zoom and recenter)
        self.zoomposorigin = None
        self.zoomposfinal = None
        self.zoompatch = None
        self.dragorigin = None
        # detect motion to update zoom rectangle
        self.mpl_connect('motion_notify_event', self.mouse_move)
        # detect mouse press to recenter or initiate drag and zoom
        self.mpl_connect('button_press_event', self.mouse_press)
        # detect mouse button release to finalize zoom
        self.mpl_connect('button_release_event', self.mouse_release)
        # detect keyboard kkey press for shortcut
        self.mpl_connect('key_press_event', self.key_press)

        # draw the already loaded elements
        self.draw_elements()

        utils.trace('out')
    # End of EarthPlot constructor

    def mouse_move(self, event):
        """Set mouse longitude and latitude plus directivity in the status bar.
        """
        # get coordinates of the mouse motion event
        xevent = event.x
        yevent = event.y
        bbox = event.canvas.figure.axes[0].bbox
        # compute longitude and latitude from the bbox of the event
        mouselon, mouselat = self.get_mouse_ll(xevent, yevent, bbox)
        if mouselon > 180 or mouselon < -180:
            mouselon = np.nan
        if mouselat > 90 or mouselat < -90:
            mouselat = np.nan
        # compute mouse azimuth and elevation for directivity computation
        mouseaz, mouseel = self.get_mouse_azel(xevent, yevent, bbox)
        if self._patterns is not {} and self._app.getpatterncombo() is not '':
            controler = self._patterns[self._app.getpatterncombo()]
            pattern = controler.get_pattern()
            gain = pattern.directivity(mouselon, mouselat)
            gain += pattern.configure()['cf']
        else:
            gain = None
        if mouseaz >= self._zoom.max_azimuth or \
                mouseaz <= self._zoom.min_azimuth or \
                mouseel >= self._zoom.max_elevation or \
                mouseel <= self._zoom.min_elevation:
            mouselon = np.nan
            mouselat = np.nan
            gain = np.nan
        # set status bar text
        app = self.parent().parent()
        app.setmousepos(mouselon, mouselat, gain)

        # if start of zoom is defined set final position
        if self.zoomposorigin is not None:
            mousex, mousey = self. get_mouse_xy(xevent, yevent, bbox)
            self.zoomposfinal = mouseaz, mouseel, \
                mouselon, mouselat, \
                mousex, mousey
            # update and draw patch
            self.zoompatch.set_x(min(mousex, self.zoomposorigin[4]))
            self.zoompatch.set_y(min(mousey, self.zoomposorigin[5]))
            self.zoompatch.set_width(abs(mousex - self.zoomposorigin[4]))
            self.zoompatch.set_height(abs(mousey - self.zoomposorigin[5]))
            self.draw()

        if self.dragorigin is not None:
            deltalon = mouselon - self.dragorigin[0]
            deltalat = mouselat - self.dragorigin[1]
            self._viewer.longitude(self._viewer.longitude() - deltalon)
            self._viewer.latitude(self._viewer.latitude() - deltalat)
            self.draw_elements()
            app = self.parent().parent()
            app.setviewerpos(self._viewer.longitude(),
                             self._viewer.latitude(),
                             self._viewer.altitude())
            self.dragorigin = mouselon, mouselat
    # end of method mouse_move

    def get_mouse_xy(self, xmouse, ymouse, bbox):
        """This function compute x and y in basemap coordinates of the mouse given
        the mouse motion event data.
        """
        # get relative x and y inside the box
        origin_x = bbox.bounds[0]
        origin_y = bbox.bounds[1]
        pixel_width = bbox.bounds[2]
        pixel_height = bbox.bounds[3]
        rel_x = (xmouse - origin_x) / pixel_width
        rel_y = (ymouse - origin_y) / pixel_height
        # get dimensions of the basemap plot and position of the mouse
        map_width = self._earth_map.urcrnrx - self._earth_map.llcrnrx
        map_height = self._earth_map.urcrnry - self._earth_map.llcrnry
        map_x = self._earth_map.llcrnrx + rel_x * map_width
        map_y = self._earth_map.llcrnry + rel_y * map_height
        return map_x, map_y
    # end of function get_mouse_xy

    def get_mouse_ll(self, xmouse, ymouse, bbox):
        """This function compute longitude and latitude of the mouse given
        the mouse motion event data.
        """
        # get relative x and y inside the box
        map_x, map_y = self.get_mouse_xy(xmouse, ymouse, bbox)
        # convert to longitue and latitude
        lon, lat = self._earth_map(map_x, map_y, inverse=True)
        # eliminate out of the Earth cases
        if lon > 180 or lon < -180:
            lon = np.nan
        if lat > 90 or lat < -90:
            lat = np.nan
        return lon, lat
    # end of function get_mouse_ll

    def get_mouse_azel(self, xmouse, ymouse, bbox):
        """This function compute azimuth and elevation of the mouse given
        the mouse motion event data.
        """
        # get relative x and y inside the box
        origin_x = bbox.bounds[0]
        origin_y = bbox.bounds[1]
        pixel_width = bbox.bounds[2]
        pixel_height = bbox.bounds[3]
        rel_x = (xmouse - origin_x) / pixel_width
        rel_y = (ymouse - origin_y) / pixel_height
        # get azel dimensions of the box
        azimuth_width = self._zoom.max_azimuth - self._zoom.min_azimuth
        elevation_height = self._zoom.max_elevation - self._zoom.min_elevation
        # compute mouse azel
        azimuth = rel_x * azimuth_width + self._zoom.min_azimuth
        elevation = rel_y * elevation_height + self._zoom.min_elevation
        azimuth = min(azimuth, self._zoom.max_azimuth)
        azimuth = max(azimuth, self._zoom.min_azimuth)
        elevation = min(elevation, self._zoom.max_elevation)
        elevation = max(elevation, self._zoom.min_elevation)
        return azimuth, elevation
    # end of function get_mouse_azel

    def mouse_press(self, event):
        """Process mouse click event.
        Buttons Ids:
        1: left-click: start drag and zoom
        2: wheel-click
        3: right-click: recenter plot
        """
        # affectation of action to button id
        action = {1: self.mouse_press_zoom,
                  2: self.mouse_donothing,
                  3: self.mouse_press_drag}
        # execution of action
        action[event.button](event)
    # end of method mouse_click

    def mouse_release(self, event):
        """Process mouse release event.
        Buttons Ids:
        1: left-click
        2: wheel-click
        3: right-click
        """
        # affectation of action to button id
        action = {1: self.mouse_release_zoom,
                  2: self.mouse_donothing,
                  3: self.mouse_release_drag}
        # execution of action
        action[event.button](event)
    # end of method mouse_click

    def mouse_donothing(self, _):
        """This method do nothing. See usecase in mouse_click method.
        """
        pass
    # end of method mouse_donothing

    def mouse_set_viewer(self, event):
        """Set viewer position by right clicking on the map.
        """
        xevent = event.x
        yevent = event.y
        bbox = event.canvas.figure.axes[0].bbox
        lon, lat = self.get_mouse_ll(xevent, yevent, bbox)
        self._viewer.longitude(round(lon, 1))
        self._viewer.latitude(round(lat, 1))
        self.draw_elements()
        app = self.parent().parent()
        app.setviewerpos(self._viewer.longitude(),
                         self._viewer.latitude(),
                         self._viewer.altitude())
    # end of method mouse_set_viewer

    def mouse_press_zoom(self, event):
        """On event mouse_press, this method is called by matplotlib environment.
        It's role is to store the first angle of the rectangular zoom on
        Earth display.
        """
        xevent = event.x
        yevent = event.y
        bbox = event.canvas.figure.axes[0].bbox
        az, el = self.get_mouse_azel(xevent, yevent, bbox)
        lon, lat = self.get_mouse_ll(xevent, yevent, bbox)
        x, y = self.get_mouse_xy(xevent, yevent, bbox)
        self.zoomposorigin = az, el, lon, lat, x, y
        self.zoompatch = Rectangle(
            xy=(x, y), width=0, height=0, fill=False, linewidth=0.2)
        self._axes.add_patch(self.zoompatch)
    # end of method mouse_press_zoom

    def mouse_release_zoom(self, _):
        """Process mouse release event.
        """
        # if original and final position are defined, zoom the plot
        if self.zoomposorigin is not None and\
           self.zoomposfinal is not None:
            azorigin, elorigin, \
                lonorigin, latorigin, \
                xorigin, yorigin = self.zoomposorigin
            azfinal, elfinal, \
                lonfinal, latfinal, \
                xfinal, yfinal = self.zoomposfinal
            xzoom = abs(xfinal - xorigin) / self.get_width()
            yzoom = abs(yfinal - yorigin) / self.get_height()
            # authorize zooming if bigger than 5% of each axis dimension
            if xzoom > 0.05 and yzoom > 0.05:
                if self._projection == 'nsper':
                    self._zoom.min_azimuth = round(min(azorigin, azfinal), 1)
                    self._zoom.min_elevation = round(min(elorigin, elfinal), 1)
                    self._zoom.max_azimuth = round(max(azorigin, azfinal), 1)
                    self._zoom.max_elevation = round(max(elorigin, elfinal), 1)
                elif self._projection == 'cyl':
                    self._zoom.min_longitude = round(
                        min(lonorigin, lonfinal), 1)
                    self._zoom.min_latitude = round(
                        min(latorigin, latfinal), 1)
                    self._zoom.max_longitude = round(
                        max(lonorigin, lonfinal), 1)
                    self._zoom.max_latitude = round(
                        max(latorigin, latfinal), 1)
            self.zoomposorigin = None
            self.zoomposfinal = None
            self.zoompatch.remove()
            self.zoompatch = None
            self.draw_elements()
            self.draw_axis()
    # end of method mouse_release_event

    def mouse_press_drag(self, event):
        xevent = event.x
        yevent = event.y
        bbox = event.canvas.figure.axes[0].bbox
        self.dragorigin = self.get_mouse_ll(xevent, yevent, bbox)

    def mouse_release_drag(self, _):
        self.dragorigin = None

    def key_press(self, event):
        """Handle key_press event.
        """
        action = {'escape': self.key_press_esc}
        try:
            action[event.key](event)
        except KeyError:
            pass

    def key_press_esc(self, _):
        """Handle Escape pressed event.
        """
        # abort mouse drag and zoom
        if self.zoomposorigin is not None:
            self.zoomposorigin = None
            self.zoomposfinal = None
            self.zoompatch.remove()
            self.zoompatch = None
            self.draw()

    def draw_elements(self):
        """This method redraw all elements of the earth plot
        """
        utils.trace('in')
        # clear display and reset it
        self._axes.clear()

        # update the zoom
        self.updatezoom()

        # Draw Earth in the background
        self.drawearth(proj=self._projection, resolution=self._resolution)

        # draw all patterns
        at_least_one_slope = False
        for key in self._patterns:
            self._patterns[key].plot()
            if 'display_slope' in self._patterns[key].get_config():
                if self._patterns[key].get_config()['display_slope']:
                    at_least_one_slope = True
        if not at_least_one_slope and len(self._patterns):
            for i in range(len(self._figure.axes)):
                if i:
                    self._figure.delaxes(self._figure.axes[i])

        # draw all Elevation contour
        for element in self._elev:
            self._elev[element].plot()

        # draw stations
        for s in self._stations:
            s.clearplot()
            s.plot()

        # draw polygons
        for p in self._polygons:
            p.clearplot()
            p.plot()

        # draw axis
        self.draw_axis()

        # call to surcharged draw function
        self.draw()
        utils.trace('out')
    # end of draw_elements function

    def draw_axis(self):
        utils.trace('in')
        if self._projection == 'nsper':
            self._axes.set_xlabel('Azimuth (deg)')
            self._axes.set_ylabel('Elevation (deg)')
            # compute and add x-axis ticks
            azticks = np.arange(self._zoom.min_azimuth,
                                self._zoom.max_azimuth + 0.1, 2)
            self._axes.set_xticks(self.az2x(azticks) +
                                  self._earth_map(self._viewer.longitude(),
                                                  self._viewer.latitude())[0])
            self._axes.set_xticklabels('{0:0.1f}'.format(f) for f in azticks)
            # compute and add y-axis ticks
            elticks = np.arange(self._zoom.min_elevation,
                                self._zoom.max_elevation + 0.1, 2)
            self._axes.set_yticks(self.el2y(elticks) +
                                  self._earth_map(self._viewer.longitude(),
                                                  self._viewer.latitude())[1])
            self._axes.set_yticklabels('{0:0.1f}'.format(f) for f in elticks)
        elif self._projection == 'cyl':
            self._axes.set_xlabel('Longitude (deg)')
            self._axes.set_ylabel('Latitude (deg)')
            lonticks = np.arange(
                int(self._zoom.min_longitude / 10) * 10,
                self._zoom.max_longitude + 0.1, 20)
            lonticks_converted, _ = np.array(self._earth_map(
                lonticks, np.ones(lonticks.shape) * self._zoom.min_latitude))
            self._axes.set_xticks(lonticks_converted)
            self._axes.set_xticklabels('{0:0.1f}'.format(f) for f in lonticks)
            # compute and add y-axis ticks
            latticks = np.arange(
                int(self._zoom.min_latitude / 10) * 10,
                self._zoom.max_latitude + 0.1, 20)
            _, latticks_converted = np.array(self._earth_map(
                np.ones(latticks.shape) * self._zoom.min_longitude, latticks))
            self._axes.set_yticks(latticks_converted)
            self._axes.set_yticklabels('{0:0.1f}'.format(f) for f in latticks)
        self._axes.tick_params(axis='both', width=0.2)
        self._axes.set_title(self._plot_title)
        utils.trace('out')
    # end of function draw_axis

    def settitle(self, title: str):
        """Set Earth plot title.
        """
        utils.trace('in')
        self._plot_title = title
        self._axes.set_title(self._plot_title)
        utils.trace('out')
    # end of method settitle

    # Change observer Longitude
    def setviewerlongitude(self, lon):
        utils.trace()
        self._viewer.longitude(lon)
    # end of method setviewerlongitude

    # Draw Earth and return Basemap handler
    def drawearth(self, proj='nsper', resolution='c'):
        utils.trace('in')

        ax = self._axes
        # add Earth _earth_map
        # resolution :
        # c: crude
        # l: low
        # i: intermediate
        # h: high
        # f: full
        if self._bluemarble_imshow is not None:
            self._bluemarble_imshow.remove()

        if proj == 'nsper':
            self._earth_map = Basemap(projection='nsper',
                                      llcrnrx=self.llcrnrx,
                                      llcrnry=self.llcrnry,
                                      urcrnrx=self.urcrnrx,
                                      urcrnry=self.urcrnry,
                                      lon_0=self._viewer.longitude(),
                                      lat_0=self._viewer.latitude(),
                                      satellite_height=self._viewer.altitude(),
                                      resolution=resolution,
                                      ax=ax)
            # display Blue Marble picture, projected and cropped
            if self._bluemarble:
                self._bluemarble_imshow = self.croppedbluemarble()
            else:
                self._bluemarble_imshow = None

        elif proj == 'cyl':
            self._earth_map = Basemap(projection=proj,
                                      llcrnrlat=self.llcrnrlat,
                                      urcrnrlat=self.urcrnrlat,
                                      llcrnrlon=self.llcrnrlon,
                                      urcrnrlon=self.urcrnrlon,
                                      lon_0=self._viewer.longitude(),
                                      lat_0=self._viewer.latitude(),
                                      lat_ts=self._viewer.latitude(),
                                      resolution=resolution,
                                      ax=ax)
            if self._bluemarble:
                self._bluemarble_imshow = self._earth_map.bluemarble(scale=0.5)
            else:
                self._bluemarble_imshow = None

        # Earth map drawing options
        # 1. Drawing coast lines
        if self._coastlines_col:
            try:
                # coast lines LineCollection can be remove at once
                self._coastlines_col.remove()
            except ValueError:
                print('drawearth: issue removing coastlines.')
        if self._coastlines != 'no line':
            self._coastlines_col = \
                self._earth_map.drawcoastlines(
                    linewidth=cst.BOLDNESS[self._coastlines])
        # 2. Drawing countries borders
        if self._countries_col:
            try:
                # Country borders LineCollection can be remove at once
                self._countries_col.remove()
            except ValueError:
                print('drawearth: issue removing borders.')
        if self._countries != 'no line':
            self._countries_col = \
                self._earth_map.drawcountries(
                    linewidth=cst.BOLDNESS[self._countries])
        # 3. Drawing parallels
        if self._parallels_col:
            try:
                # Parallels are a dictionary of 2D lines to be
                # removed one by one
                for k in self._parallels_col:
                    self._parallels_col[k][0][0].remove()
                self._parallels_col.clear()
            except ValueError:
                print('drawearth: issue removing parallels.')
        if self._parallels != 'no line':
            self._parallels_col = \
                self._earth_map.drawparallels(
                    np.arange(-80., 81., 20.),
                    linewidth=cst.BOLDNESS[self._parallels])
        # 4. Drawing meridians
        if self._meridians_col:
            try:
                # Meridians are a dictionary of 2D lines to be
                # removed one by one
                for k in self._meridians_col:
                    self._meridians_col[k][0][0].remove()
                self._meridians_col.clear()
            except ValueError:
                print('drawearth: issue removing meridians.')
        if self._meridians != 'no line':
            self._meridians_col = \
                self._earth_map.drawmeridians(
                    np.arange(-180., 181., 20.),
                    linewidth=cst.BOLDNESS[self._meridians])
        # Unconditional drawing of Earth boundary
        self._earth_map.drawmapboundary(linewidth=0.2)

        utils.trace('out')
        return self._earth_map
    # end of drawEarth function

    # Draw isoElevation contours
    def drawelevation(self, level=(10, 20, 30)):
        utils.trace('in')
        # define grid
        iNx = 200
        iNy = 200
        fXlin = np.linspace(self._earth_map.xmin, self._earth_map.xmax, iNx)
        fYlin = np.linspace(self._earth_map.ymin, self._earth_map.ymax, iNy)
        fXMesh, fYMesh = np.meshgrid(fXlin, fYlin)
        fLonMesh, fLatMesh = self._earth_map(fXMesh, fYMesh, inverse=True)
        # define Elevation matrix
        fElev = self.elevation(fLonMesh, fLatMesh)
        csElev = self._earth_map.contour(
            fXMesh, fYMesh, fElev, level,
            colors='black', linestyles='dotted', linewidths=0.5)
        utils.trace('out')
        return csElev
    # end of drawelevation

    def elevation(self, stalon, stalat):
        """Compute elevation of spacecraft seen from a station on the ground.
        """
        utils.trace('in')
        # compute phi
        phi = np.arccos(np.cos(cst.DEG2RAD * stalat) *
                        np.cos(cst.DEG2RAD *
                               (self._viewer.longitude() - stalon)))

        # compute elevation
        elev = np.reshape([90 if phi == 0 else
                           cst.RAD2DEG *
                           np.arctan((np.cos(phi) -
                                      (cst.EARTH_RAD_EQUATOR_M /
                                       (cst.EARTH_RAD_EQUATOR_M +
                                        self._viewer.altitude()))) /
                                     np.sin(phi))
                           for phi in phi.flatten()], phi.shape)

        # remove station out of view
        elev = np.where(np.absolute(
            stalon - self._viewer.longitude()) < 90, elev, -1)

        utils.trace('out')
        # Return vector
        return elev
    # end of function elevation

    def get_file_key(self, filename):
        utils.trace('in')
        file_index = 1
        f = os.path.basename(filename)
        file_key = f + ' ' + str(file_index)
        while (file_key in self._patterns) and file_index <= 50:
            file_index = file_index + 1
            file_key = f + ' ' + str(file_index)
        if file_index == 50:
            print('Max repetition of same file reached.' +
                  ' Index 50 will be overwritten')
        utils.trace('out')
        return file_key
    # end of function get_file_key

    def loadpattern(self, conf=None):
        """Load and display a grd file.
        """
        utils.trace('in')
        try:
            filename = conf['filename']
        except KeyError:
            print('load_pattern:File name is mandatory.')
            utils.trace('out')
            return None
        file_key = self.get_file_key(filename)
        conf['key'] = file_key
        try:
            pattern = PatternControler(parent=self, filename=filename)
        except FileNotFoundError:
            print('Pattern file ' + filename + ' not found')
            return None
        if 'sat_lon' not in conf:
            dialog = True
            conf['sat_lon'] = self._viewer.longitude()
            conf['sat_lat'] = self._viewer.latitude()
            conf['sat_alt'] = self._viewer.altitude()
        else:
            dialog = False
        pattern.configure(dialog=dialog, config=conf)

        # Add grd in grd dictionary
        self._patterns[file_key] = pattern

        utils.trace('out')
        # refresh pattern combo box
        itemlist = ['']
        itemlist.extend(self._patterns.keys())
        self._app.setpatterncombo(itemlist)
        # return pattern controler instance
        return self._patterns[file_key]
    # end of load_pattern

    # Zoom on the _earth_map
    def updatezoom(self):
        self.llcrnrx = self.az2x(self._zoom.min_azimuth)
        self.llcrnry = self.el2y(self._zoom.min_elevation)
        self.urcrnrx = self.az2x(self._zoom.max_azimuth)
        self.urcrnry = self.el2y(self._zoom.max_elevation)
        self.llcrnrlon = self._zoom.min_longitude
        self.llcrnrlat = self._zoom.min_latitude
        self.urcrnrlon = self._zoom.max_longitude
        self.urcrnrlat = self._zoom.max_latitude
        self.centerx = (self.llcrnrx + self.urcrnrx) / 2
        self.centery = (self.llcrnry + self.urcrnry) / 2
        self.cntrlon = (self.llcrnrlon + self.urcrnrlon) / 2
        self.cntrlat = (self.llcrnrlat + self.urcrnrlat) / 2
    # end of method updatezoom

    def get_width(self):
        if self._projection == 'nsper':
            return self.urcrnrx - self.llcrnrx
        elif self._projection == 'cyl':
            return self.urcrnrlon - self.llcrnrlon
        else:
            return 0
    # end of function get_width

    def get_height(self):
        if self._projection == 'nsper':
            return self.urcrnry - self.llcrnry
        elif self._projection == 'cyl':
            return self.urcrnrlat - self.llcrnrlat
        else:
            return 0
    # end of function get_width

    # convert Azimuth to _earth_map.x
    def az2x(self, az):
        return np.tan(az * cst.DEG2RAD) * self._viewer.altitude()

    # convert Elevation to _earth_map.y
    def el2y(self, el):
        return np.tan(el * cst.DEG2RAD) * self._viewer.altitude()

    def x2az(self, x):
        return np.arctan2(x, self._viewer.altitude()) * cst.RAD2DEG

    def y2el(self, y):
        return np.arctan2(y, self._viewer.altitude()) * cst.RAD2DEG

    def projection(self, proj: str = None):
        """This function allows access to attribute _projection.
        """
        utils.trace('in')
        if proj:
            if proj == 'nsper' or proj == 'cyl':
                self._projection = proj
            else:
                raise ValueError("Projection is either 'nsper' or 'cyl'.")
        utils.trace('out')
        return self._projection
    # end of function projection

    def set_resolution(self, resolution: str = 'c'):
        """Set Earth map resolution.
        """
        utils.trace('in')
        self._resolution = resolution
        self._earth_map.resolution = self._resolution
        self.draw_elements()
        utils.trace('out')
    # end of function set_resolution

    def save(self, filename=None):
        """Save the plot with given filename. If file name not provided,
        use last used name.
        """
        utils.trace('in')
        # store file name for future call to this function
        if filename:
            self.filename = filename
        # save plot into file
        # plt.savefig(self.filename, dpi='figure')
        self.print_figure(self.filename)
        utils.trace('out')
    # end of function save

    ###################################################################
    #
    #       Getters and Setters
    #
    ###################################################################

    def viewer(self, v=None):
        """Get _viewer attribute.
        """
        if v:
            self._viewer = v
        return self._viewer

    def zoom(self, z=None):
        """Get _zoom attribute.
        """
        if z:
            self._zoom = z
        return self._zoom

    def get_coastlines(self):
        """Return value of private attribute _coastlines
        """
        return self._coastlines
    # end of function get_coastlines

    def set_coastlines(self, c: str, refresh: bool = False):
        """Set private attribute _coastlines value.
        If refresh is True, redraw Earth.
        Return the value passed to the function.
        """
        utils.trace('in')
        self._coastlines = c
        if refresh:
            self.drawearth(proj=self._projection,
                           resolution=self._resolution)
            self.draw()
        utils.trace('out')
        return self._coastlines
    # end of function set_coastlines

    def get_countries(self):
        """Return value of private attribute _countries
        """
        return self._countries
    # end of function get_countries

    def set_countries(self, c: str, refresh: bool = False):
        """Set private attribute _countries value.
        If refresh is True, redraw Earth.
        Return the value passed to the function.
        """
        utils.trace('in')
        self._countries = c
        if refresh:
            self.drawearth(proj=self._projection,
                           resolution=self._resolution)
            self.draw()
        utils.trace('out')
        return self._countries
    # end of function set_countries

    def get_parallels(self):
        """Return the value of private attribute _parallels
        """
        return self._parallels
    # end of function get_parallels

    def set_parallels(self, p: str, refresh: bool = False):
        """Set the value of private attribute _parallels.
        If refresh is True, redraw Earth.
        Return the value passed to the function.
        """
        utils.trace('in')
        self._parallels = p
        if refresh:
            self.drawearth(proj=self._projection,
                           resolution=self._resolution)
            self.draw()
        utils.trace('out')
        return self._parallels
    # end of function set_parallels

    def get_meridians(self):
        """Return the value of private attribute _meridians.
        """
        return self._meridians
    # end of function get_meridians

    def set_meridians(self, m: str, refresh: bool = False):
        """Set the value of the private attribute _meridians.
        If refresh is True, redraw Earth.
        Return the value passed to the function.
        """
        utils.trace('in')
        self._meridians = m
        if refresh:
            self.drawearth(proj=self._projection,
                           resolution=self._resolution)
            self.draw()
        utils.trace('out')
        return self._meridians
    # end of function set_meridians

    def get_centralwidget(self):
        """Accessor to central widget.
        """
        return self._centralwidget
    # end of get_centralwidget

    def croppedbluemarble(self):
        # get blue marble data projected on the current projection
        im = self._earth_map.bluemarble(alpha=0.9, scale=0.5)
        data = im.get_array()

        # get data array dimension
        nx, ny, _ = data.shape
        ead = self.earth_angular_diameter()
        stepx = ead / (nx - 1)
        stepy = ead / (ny - 1)

        # create new matrix to the dimension of the current plot
        azmin = self._zoom.min_azimuth
        azmax = self._zoom.max_azimuth
        elmin = self._zoom.min_elevation
        elmax = self._zoom.max_elevation
        new_nx = int((azmax - azmin) / stepx / 2) * 2 + 1
        new_ny = int((elmax - elmin) / stepy / 2) * 2 + 1
        new_data = np.zeros((new_ny, new_nx, 4))

        # compute first azimuth index of source array and destination array
        x0_source = 0
        x0_destination = 0
        if azmin > -ead/2:
            # crop in azimuth
            x0_source = int(np.abs(azmin + ead/2) / stepx)
        else:
            x0_destination = int(np.abs(azmin + ead/2) / stepx)
        # if destination array smaller than origin array, limit source array
        if new_nx - x0_destination < nx - x0_source:
            x_source = range(x0_source, x0_source + new_nx - x0_destination)
        else:
            x_source = range(x0_source, nx)
        x_destination = range(x0_destination, x0_destination + len(x_source))

        # compute first elevation index of source array and destination array
        y0_source = 0
        y0_destination = 0
        if elmin > -ead/2:
            # crop in azimuth
            y0_source = int(np.abs(elmin + ead/2) / stepy)
        else:
            y0_destination = int(np.abs(elmin + ead/2) / stepy)
        # if destination array smaller than origin array, limit source array
        if new_ny - y0_destination < ny - y0_source:
            y_source = range(y0_source, y0_source + new_ny - y0_destination)
        else:
            y_source = range(y0_source, ny)
        y_destination = range(y0_destination, y0_destination + len(y_source))

        x0_src = x_source[0]
        x1_src = x_source[-1]
        y0_src = y_source[0]
        y1_src = y_source[-1]
        x0_des = x_destination[0]
        x1_des = x_destination[-1]
        y0_des = y_destination[0]
        y1_des = y_destination[-1]
        new_data[y0_des:y1_des, x0_des:x1_des] = \
            data[y0_src:y1_src, x0_src:x1_src]
        im.set_array(new_data)
        return im
    # end of method croppedbluemarble

    def earth_angular_diameter(self):
        """Compute Earth anguar diameter from spacecraft point of view
        depending on the altitude.
        """
        sat_height = cst.EARTH_RAD_BASEMAP + self._viewer.altitude()
        d = 2 * np.arcsin(cst.EARTH_RAD_BASEMAP / sat_height) * cst.RAD2DEG
        return d
    # end of function earth_angular_diameter

    def get_earthmap(self):
        return self._earth_map
    # end of function get_earthmap

    def get_axes(self):
        return self._axes
    # end of function get_axes


# end of class EarthPlot

# end of module earthplot
