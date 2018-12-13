"""This module contains the class definition for the canvas containing
the Earth plot and all the subsequent elements plots.
"""


# Imports
# import Matplotlib and Base_earth_map
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter
from matplotlib.figure import Figure
from matplotlib import cm
from mpl_toolkits.axes_grid1 import make_axes_locatable

# import PyQt5 and link with matplotlib
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QAction
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# import numpy
import numpy as np

# local module
import pattern
from pattern import Grd
from pattern import GrdDialog
from viewer import ViewerPos
from zoom import Zoom


# Constants 
# Earth radius at equator and pole
EARTH_RAD_EQUATOR_M = 6378137.0000 # m
EARTH_RAD_POLE_M = 6356752.3142 # m

# angle conversion
DEG2RAD = np.pi / 180
RAD2DEG = 180 / np.pi


class EarthPlot(FigureCanvas):
    """This class is the core of the appliccation. It display the Earth
    map, the patterns, stations, elevation contour, etc.
    """ 
    # EarthPlot constructor
    def __init__(self, parent=None, width=5, height=5, dpi=300, \
                 proj='geos', res='c', config=None):

        # Store Canvas properties
        self._plot_title = 'Default Title'
        self._width = width
        self._height = height
        self._dpi = dpi
        # store _earth_map properties
        self._projection = proj
        self._resolution = res

        # define figure in canvas
        self._figure = Figure(figsize=(self._width, self._height), \
                          dpi=self._dpi)
        self._axes = self._figure.add_subplot(111)

        FigureCanvas.__init__(self, self._figure)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, \
                                   QSizePolicy.Expanding, \
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        # initialize EarthPlot fields
        self._grds = {}
        self._elev = {}
        self._clrbar = None
        self._clrbar_axes = None
        self._earth_map = None
        self._stations = []

        # if a config has been provided by caller
        if config:
            # get font size with fallback = 5
            fontsize = config.getint('DEFAULT', 'font size', fallback=5)
            # set default font size
            plt.rcParams.update({'font.size': fontsize})
            self._axes.xaxis.label.set_fontsize(fontsize)
            self._axes.yaxis.label.set_fontsize(fontsize)

            # set map resolution (take only first letter in lower case)
            self._resolution = config.get('DEFAULT', \
                                          'map resolution', \
                                          fallback=self._resolution)[0].lower()

            # get point of view coordinates if defined
            longitude = config.getfloat('VIEWER', 'longitude', fallback=0.0)
            latitude = config.getfloat('VIEWER', 'latitude', fallback=0.0)
            altitude = config.getfloat('VIEWER', 'altitude', fallback=35786000.0)

            # get default directory
            self.rootdir = config.get('DEFAULT', 'root')
            
            # Initialize zoom
            self._zoom = Zoom(self._projection)
            if 'GEO' in config:
                if 'min azimuth' in config['GEO']:
                    self._zoom.min_azimuth = config.getfloat('GEO', 'min azimuth')
                if 'min elevation' in config['GEO']:
                    self._zoom.min_elevation = config.getfloat('GEO', 'min elevation')
                if 'max azimuth' in config['GEO']:
                    self._zoom.max_azimuth = config.getfloat('GEO', 'max azimuth')
                if 'max elevation' in config['GEO']:
                    self._zoom.max_elevation = config.getfloat('GEO', 'max elevation')
            if 'MERCATOR' in config:
                if 'min longitude' in config['MERCATOR']:
                    self._zoom.fLowLeftLon = config.getfloat('MERCATOR', 'min longitude')
                if 'min latitude' in config['MERCATOR']:
                    self._zoom.fLowLeftLat = config.getfloat('MERCATOR', 'min latitude')
                if 'max longitude' in config['MERCATOR']:
                    self._zoom.fUpRightLon = config.getfloat('MERCATOR', 'max longitude')
                if 'max latitude' in config['MERCATOR']:
                    self._zoom.fUpRightLat = config.getfloat('MERCATOR', 'max latitude')
            if 'PATTERN' in config:
                if 'file' in config['PATTERN']:
                    file = config.get('PATTERN', 'file')
                    satlon = config.getfloat('PATTERN', 'longitude', fallback=0.0)
                    title = config.get('PATTERN', 'title', fallback='Default title')
                    level = config.get('PATTERN', 'level', fallback='25, 30, 35, 38, 40')
                    revertx = config.getboolean('PATTERN', 'revert x-axis', fallback=False)
                    reverty = config.getboolean('PATTERN', 'revert y-axis', fallback=False)
                    secondpol = config.getboolean('PATTERN', 'second polarisation', fallback=False)
                    slope = config.getboolean('PATTERN', 'slope', fallback=False)
                    grd = self.loadgrd(filename=file, lon=satlon, alt=pattern.ALTGEO, \
                                       revertx=revertx, reverty=reverty, \
                                       secondpol=secondpol, dispslope=slope)['grd']       
                    self.settitle(title)
                    grd.fIsolvl = [float(s) for s in level.split(',')]
        
        # initialize angle of view
        # Satellite Longitude, latitude and altitude
        self._viewer = ViewerPos(lon=longitude, lat=latitude, alt=altitude)

        # default file name to save figure
        self.filename = 'plot.PNG'

    # End of EarthPlot constructor

    # Redefine draw function
    def draw(self):
        # clear display and reset it
        self._axes.clear()
        if self._clrbar:
            self._clrbar.ax.clear()

        # update the zoom
        self.updatezoom()

        # Draw Earth in the background
        self.drawearth(proj=self._projection, resolution=self._resolution)

        # draw all patterns
        for key in self._grds:
            self.drawgrd(self._grds[key]['grd'])
        # draw all Elevation contour
        if self._elev:
            self.drawelevation([self._elev[key].angle() for key in self._elev])

        # draw stations
        if self._stations:
            self.drawstations(self._stations)

        if self._projection == 'geos':
            self._axes.set_xlabel('Azimuth (deg)')
            self._axes.set_ylabel('Elevation (deg)')
            # compute and add x-axis ticks
            azticks = np.arange(self._zoom.min_azimuth, self._zoom.max_azimuth + 0.1, 2)
            self._axes.set_xticks(self.az2x(azticks)
                                  + self._earth_map(self._viewer.longitude(), 0.0)[0])
            self._axes.set_xticklabels(str(f) for f in azticks)
            # compute and add y-axis ticks
            elticks = np.arange(self._zoom.min_elevation, self._zoom.max_elevation + 0.1, 2)
            self._axes.set_yticks(self.el2y(elticks)
                                  + self._earth_map(self._viewer.longitude(), 0.0)[1])
            self._axes.set_yticklabels(str(f) for f in elticks)
        elif self._projection == 'merc':
            self._axes.set_xlabel('Longitude (deg)')
            self._axes.set_ylabel('Latitude (deg)')
        self._axes.set_title(self._plot_title)

        # call to super draw method
        super().draw()
    # end of draw function

    def settitle(self, title: str):
        """Set Earth plot title.
        """
        self._plot_title = title

    # Change observer Longitude 
    def setviewerlongitude(self, lon):
        self._viewer.longitude(lon)
        
    # Draw Earth and return Basemap handler
    def drawearth(self, proj='geos', resolution='c'):
        # if self._earth_map:
            # ax = self._earth_map.ax
        # else:
        ax = self._axes
        # add Earth _earth_map
        # resolution :
        # c: crude
        # l: low
        # i: intermediate
        # h: high
        # f: full
        if proj == 'geos':
            # NB: latitude has to stay 0.0 for geos projection
            self._earth_map = Basemap(projection=proj, \
                            rsphere=(EARTH_RAD_EQUATOR_M,EARTH_RAD_POLE_M), \
                            llcrnrx=self.llcrnrx, \
                            llcrnry=self.llcrnry, \
                            urcrnrx=self.urcrnrx, \
                            urcrnry=self.urcrnry, \
                            lon_0=self._viewer.longitude(), \
                            lat_0=0.0, \
                            satellite_height=self._viewer.altitude(), \
                            resolution=resolution, \
                            ax=ax)
            
            self._earth_map.drawcoastlines(linewidth=0.5)
            self._earth_map.drawcountries(linewidth=0.5)
            self._earth_map.drawparallels(np.arange(-90., 120., 30.), linewidth=0.5)
            self._earth_map.drawmeridians(np.arange(0., 390., 30.), linewidth=0.5)
            self._earth_map.drawmapboundary(linewidth=0.5)
        elif proj=='merc':
            self._earth_map = Basemap(projection=proj, \
                            rsphere=(EARTH_RAD_EQUATOR_M,EARTH_RAD_POLE_M), \
                            llcrnrlat=self.llcrnrlat, \
                            urcrnrlat=self.urcrnrlat,\
                            llcrnrlon=self.llcrnrlon, \
                            urcrnrlon=self.urcrnrlon, \
                            lat_ts=20, \
                            resolution=resolution, \
                            ax=ax)    

            self._earth_map.drawcoastlines(linewidth=0.5)
            self._earth_map.drawcountries(linewidth=0.5)
            self._earth_map.drawparallels(np.arange(-90., 91., 30.), linewidth=0.5)
            self._earth_map.drawmeridians(np.arange(-180., 181., 30.), linewidth=0.5)
            self._earth_map.drawmapboundary(linewidth=0.5)
    
        return self._earth_map
    # end of drawEarth function    
        
    # Draw isoElevation contours
    def drawelevation(self, level=(10, 20, 30)):
        # define grid
        iNx = 200
        iNy = 200
        fXlin = np.linspace(self._earth_map.xmin,self._earth_map.xmax,iNx)
        fYlin = np.linspace(self._earth_map.ymin,self._earth_map.ymax,iNy)
        fXMesh, fYMesh = np.meshgrid(fXlin, fYlin)
        fLonMesh, fLatMesh = self._earth_map(fXMesh, fYMesh, inverse=True)
        # define Elevation matrix
        fElev = self.elevation(fLonMesh, fLatMesh)
        csElev = self._earth_map.contour(fXMesh,fYMesh,fElev, level, colors='black', linestyles='dotted', linewidths=0.5)
        return csElev
    # end of drawelevation    

    def elevation(self, stalon, stalat):
        """Compute elevation of spacecraft seen from a station on the ground.
        """  
        # compute phi
        phi = np.arccos(np.cos(DEG2RAD * stalat)
              * np.cos(DEG2RAD * (self._viewer.longitude() - stalon)))

        # compute elevation
        elev = np.reshape([90 if phi == 0 else RAD2DEG * np.arctan((np.cos(phi) - (EARTH_RAD_EQUATOR_M/(EARTH_RAD_EQUATOR_M+self._viewer.altitude())))/ np.sin(phi)) for phi in phi.flatten()], phi.shape)
        
        # remove station out of view
        elev = np.where(np.absolute(stalon - self._viewer.longitude()) < 90, elev, -1)
        
        # Return vector
        return elev
    
    def loadgrd(self, filename, lon, alt, revertx=False, reverty=False, secondpol=False, dispslope=False):
        """Load and display a grd file.
        """    
        # add item in Grd menu
        patternindex = len(self._grds) + 1
        patternmenu = self.parent().parent().menupattern.addMenu('Pattern ' \
                                                                  + str(patternindex))
        remove_pat_action = QAction('Remove', self.parent().parent())
        edit_pat_action = QAction('Edit', self.parent().parent())
        patternmenu.addAction(remove_pat_action)
        patternmenu.addAction(edit_pat_action)
        remove_pat_action.triggered.connect(self.make_remgrd(filename))
        edit_pat_action.triggered.connect(self.make_editgrd(filename))

        # Add grd in grd dictionary
        self._grds[filename] = {'grd': Grd(filename, bRevertX=revertx, \
                                           bRevertY=reverty, \
                                           bUseSecondPol=secondpol, \
                                           alt=alt, \
                                           lon=lon, \
                                           bDisplaySlope=dispslope), \
                                'menu': patternmenu}
                                       
        return self._grds[filename]
    # end of loadgrd

    def make_remgrd(self,filename):
        """Callback maker for remove pattern menu items.
        """
        def remgrd():
            menu = self._grds[filename]['menu']
            menu_action = menu.menuAction()
            menu.parent().removeAction(menu_action)
            del self._grds[filename]
            self.draw()
        return remgrd
    # end of function make_remgrd

    def make_editgrd(self,filename):
        """Callback maker for edit pattern menu items.
        """
        def editgrd():
            menu = self._grds[filename]['menu']
            menu_action = menu.menuAction()
            menu.parent().removeAction(menu_action)
            del self._grds[filename]
            dialbox = GrdDialog(filename, self.parent().parent())
            dialbox.exec_()
        return editgrd  
    # end of function make_editgrd

    def drawgrd(self, grd):
        """Draw pattern on the earth plot from the provided grd.
        """
        x, y = self._earth_map(grd.longitude, grd.latitude)
        if not grd.bDisplaySlope:
            try:
                cs_grd = self._earth_map.contour(x, y, grd.copol(), grd.isolevel, linestyles='solid', linewidths=0.5)
                self._axes.clabel(cs_grd, grd.isolevel, inline=True, fmt='%1.1f',fontsize=5)
                grd.displaymax(self._earth_map)
                return cs_grd
            except ValueError as value_err:
                print(value_err)
                print('Pattern ' + grd.filename + ' will not be displayed.')
                return None
        else:
            # define grid
            iNx = 1001
            iNy = 1001
            fAzlin = np.linspace(grd.MinAz(),grd.MaxAz(),iNx)
            fEllin = np.linspace(grd.MinEl(),grd.MaxEl(),iNy)
            fAzMesh, fElMesh = np.meshgrid(fAzlin, fEllin)
            # display color mesh
            cmap = plt.get_cmap('jet')
            cmap.set_over('white',grd.slope_range[1])
            cmap.set_under('white',grd.slope_range[0])
            xOrigin, yOrigin = self._earth_map(self._viewer.longitude(),self._viewer.latitude())
            pcmGrd = self._earth_map.pcolormesh(self.az2x(fAzMesh) + xOrigin, \
                                         self.el2y(fElMesh) + yOrigin, \
                                         grd.interpolate_slope(fAzMesh,fElMesh), \
                                         vmin=grd.slope_range[0],vmax=grd.slope_range[1], \
                                         cmap=cmap,alpha=0.5)
            # add color bar
            if self._clrbar:
                self._clrbar = self._figure.colorbar(pcmGrd, cax=self._clrbar_axes)     
            else:
                divider = make_axes_locatable(self._axes)
                self._clrbar_axes = divider.append_axes("right", size="5%", pad=0.05)
                self._clrbar = self._figure.colorbar(pcmGrd, cax=self._clrbar_axes)     
            self._clrbar.ax.set_ylabel('Pattern slope (dB/deg)')

            return pcmGrd
    # end of drawgrd method       

    def drawstations(self, stations):
        """This method display stations listed in the given stations list.
        """
        for s in stations:
            # get coordinates of station in earth plot frame
            xsta, ysta = self._earth_map(s.longitude(),s.latitude())
            # if station is out of plot do not display
            if self._earth_map.llcrnrx < xsta and \
               xsta < self._earth_map.urcrnrx and \
               self._earth_map.llcrnry < ysta and \
               ysta < self._earth_map.urcrnrx:
                    
                # if BPE defined, display circle around station
                if s.beampointingerr():
                    circle = plt.Circle((xsta, ysta), self._viewer.altitude() * s.beampointingerr() * np.pi / 180, \
                                        color='k', fill=False, linewidth=0.3, linestyle='dashed')
                    self._earth_map.ax.add_artist(circle)
                # display a dot at station coordinates
                self._earth_map.scatter(xsta,ysta,2,marker='o',color='r')
                # add station tag
                self._earth_map.ax.annotate(s.tag(), xy=(xsta + s.xtag(), ysta + s.ytag()))
    # end of method drawstations

    # Zoom on the _earth_map
    def updatezoom(self):
        self.llcrnrx   = self.az2x(self._zoom.min_azimuth)
        self.llcrnry   = self.el2y(self._zoom.min_elevation)
        self.urcrnrx   = self.az2x(self._zoom.max_azimuth)
        self.urcrnry   = self.el2y(self._zoom.max_elevation)
        self.llcrnrlon = self._zoom.min_longitude
        self.llcrnrlat = self._zoom.min_latitude
        self.urcrnrlon = self._zoom.max_longitude
        self.urcrnrlat = self._zoom.max_latitude
        self.centerx   = (self.llcrnrx + self.urcrnrx) / 2
        self.centery   = (self.llcrnry + self.urcrnry) / 2
        self.cntrlon   = (self.llcrnrlon + self.urcrnrlon) / 2
        self.cntrlat   = (self.llcrnrlat + self.urcrnrlat) / 2

    # convert Azimuth to _earth_map.x
    def az2x(self, az):
        return az * np.pi / 180 * self._viewer.altitude()
    
    # convert Elevation to _earth_map.y
    def el2y(self, el):
        return el * np.pi / 180 * self._viewer.altitude()
    
    def x2az(self, x):
        return x / (np.pi / 180 * self._viewer.altitude())
    
    def y2el(self, y):
        return y / (np.pi / 180 * self._viewer.altitude())

    def projection(self,proj: str = None):
        """This function allows access to attribute _projection.
        """ 
        if proj:
            if proj=='geos' or proj == 'merc':
                self._projection = proj
            else:
                raise ValueError("Projection is either 'geos' or 'merc'.")
        return self._projection
    # end of function projection

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

    def set_resolution(self, resolution: str = 'c'):
        """Set Earth map resolution.
        """
        self._resolution = resolution
    # end of function set_resolution

    def save(self,filename=None):
        """Save the plot with given filename. If file name not provided,
        use last used name.
        """
        # store file name for future call to this function
        if filename:
            self.filename = filename
        # save plot into file
        # plt.savefig(self.filename, dpi='figure')
        self.print_figure(self.filename)
    # end of function save

    # def drawpolygon(self, vertex):
        

        

# end of class EarthPlot

# end of module earthplot
