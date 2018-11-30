# Earth radius at equator
earthEqRadM  = 6378137.0000 # m
earthPolRadM = 6356752.3142 # m

# import Matplotlib and Basemap
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter
from matplotlib.figure import Figure
from matplotlib import cm
from mpl_toolkits.axes_grid1 import make_axes_locatable

# import PyQt5 and link with matplotlib
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# import numpy
import numpy as np

# local module
from Pattern import Grd
from Viewer import ViewerPos
from Zoom import Zoom

class EarthPlot(FigureCanvas):

    # Canvas constructor
    def __init__(self, parent = None, width=5, height=4, dpi = 300, proj='geos', res='c'):

        # Store Canvas properties
        self.strTitle       = 'Default Title'
        self.iWidth         = width
        self.iHeight        = height
        self.iDpi           = dpi
        self.strProjection  = proj
        self.strResolution  = res

        # define figure in canvas
        self.fig = Figure(figsize=(self.iWidth,self.iHeight),dpi=self.iDpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        # initialize a grd dictionary
        self.dicGrd = {}

        # initialize an elevation contour dictionary
        self.dicElev = {}
        self.cbar = []
        self.map = []
        self.stationList = []
        self.fMaxBPE = None

        # initialize angle of view
        # Satellite Longitude, latitude and altitude
        self.viewer = ViewerPos()
        
        # Initialize zoom
        self.zoom = Zoom(self.strProjection)

        # create map in Geo projection
        # self.draw() ==> not needed : main loop draw it anyway

    # End of EarthPlot constructor

    # Redefine draw function
    def draw(self, proj=None):
        # clear display and reset it
        self.axes.clear()
        if self.cbar:
            self.cbar.ax.clear()
        
        # set projection if parameter provided
        if proj != None:
            self.strProjection=proj

        # update the zoom
        self.updateZoom()

        # Draw Earth in the background
        self.drawEarth(proj=self.strProjection,resolution='i')

        # draw all patterns
        for key in self.dicGrd:
            self.drawGrd(self.dicGrd[key])
        # draw all Elevation contour
        if len(self.dicElev) > 0:
            self.drawElevation([self.dicElev[key].fAngle for key in self.dicElev])

        # draw stations
        if self.stationList != []:
            self.drawStationList(self.stationList,self.fMaxBPE)

        if self.strProjection == 'geos':
            self.axes.set_xlabel('Azimuth (deg)')
            self.axes.set_ylabel('Elevation (deg)')
            self.axes.set_xticks(self.Az2X(np.arange(self.zoom.fLowLeftAz,self.zoom.fUpRightAz+0.1,2)) + self.map(self.viewer.fLonDeg, 0.0)[0])
            self.axes.set_xticklabels(str(f) for f in np.arange(self.zoom.fLowLeftAz,self.zoom.fUpRightAz+0.1,2))
            self.axes.set_yticks(self.El2Y(np.arange(self.zoom.fLowLeftEl,self.zoom.fUpRightEl+0.1,2)) + self.map(self.viewer.fLonDeg, 0.0)[1])
            self.axes.set_yticklabels(str(f) for f in np.arange(self.zoom.fLowLeftEl,self.zoom.fUpRightEl+0.1,2))
        elif self.strProjection == 'merc':
            self.axes.set_xlabel('Longitude (deg)')
            self.axes.set_ylabel('Latitude (deg)')
        self.axes.set_title(self.strTitle)

        # call to super draw method
        super().draw()

    def setTitle(self,strTitle: str):
        self.strTitle = strTitle

    # Change observer Longitude 
    def setViewLon(self, lon):
        self.viewer.setLon(lon)
        
    # Draw Earth and return Basemap handler
    def drawEarth(self, proj='geos', resolution='c'):
        # if self.map:
            # ax = self.map.ax
        # else:
        ax = self.axes
        # add Earth map
        # resolution :
        # c: crude
        # l: low
        # i: intermediate
        # h: high
        # f: full
        if proj=='geos':
            # NB: latitude has to stay 0.0 for geos projection
            self.map = Basemap(projection=proj, \
                            rsphere=(earthEqRadM,earthPolRadM), \
                            llcrnrx=self.llcrnrx, \
                            llcrnry=self.llcrnry, \
                            urcrnrx=self.urcrnrx, \
                            urcrnry=self.urcrnry, \
                            lon_0=self.viewer.fLonDeg, \
                            lat_0=0.0, \
                            satellite_height=self.viewer.fAltM, \
                            resolution=resolution, \
                            ax=ax)
            
            self.map.drawcoastlines(linewidth=0.5)
            self.map.drawcountries(linewidth=0.5)
            self.map.drawparallels(np.arange(-90.,120.,30.),linewidth=0.5)
            self.map.drawmeridians(np.arange(0.,390.,30.),linewidth=0.5)
            self.map.drawmapboundary(linewidth=0.5)
        elif proj=='merc':
            self.map = Basemap(projection=proj, \
                            rsphere=(earthEqRadM,earthPolRadM), \
                            llcrnrlat=self.llcrnrlat, \
                            urcrnrlat=self.urcrnrlat,\
                            llcrnrlon=self.llcrnrlon, \
                            urcrnrlon=self.urcrnrlon, \
                            lat_ts=20, \
                            resolution=resolution, \
                            ax=ax)    

            self.map.drawcoastlines(linewidth=0.5)
            self.map.drawcountries(linewidth=0.5)
            self.map.drawparallels(np.arange(-90.,91.,30.),linewidth=0.5)
            self.map.drawmeridians(np.arange(-180.,181.,30.),linewidth=0.5)
            self.map.drawmapboundary(linewidth=0.5)
    
        return self.map
    # end of drawEarth function    
        
    # Draw isoElevation contours
    def drawElevation(self,level=(10,20,30)):
        # define grid
        iNx = 200
        iNy = 200
        fXlin = np.linspace(self.map.xmin,self.map.xmax,iNx)
        fYlin = np.linspace(self.map.ymin,self.map.ymax,iNy)
        fXMesh, fYMesh = np.meshgrid(fXlin, fYlin)
        fLonMesh, fLatMesh = self.map(fXMesh, fYMesh, inverse=True)
        # define Elevation matrix
        fElev = self.elevation(fLonMesh, fLatMesh)
        csElev = self.map.contour(fXMesh,fYMesh,fElev, level, colors='black', linestyles='dotted', linewidths=0.5)
        return csElev
        
        
    # Compute elevation of spacecraft seen from a station on the ground
    def elevation(self, fStaLon, fStaLat):
        
        # compute phi
        fPhi = np.arccos(np.cos(np.pi / 180 * fStaLat) * np.cos(np.pi / 180 * (self.viewer.fLonDeg - fStaLon)))

        # compute elevation
        fElev = np.reshape([90 if phi == 0 else 180 / np.pi * np.arctan((np.cos(phi) - (earthEqRadM/(earthEqRadM+self.viewer.fAltM)))/ np.sin(phi)) for phi in fPhi.flatten()], fPhi.shape)
        
        # remove station out of view
        fElev = np.where(np.absolute(fStaLon - self.viewer.fLonDeg) < 90,fElev,-1)
        
        # Return vector
        return fElev
    
    # Load and display a grd file
    def loadGrd(self, strFileName, bRevertX=False, bRevertY=False, bUseSecondPol=False, bDisplaySlope=False):
        self.dicGrd[strFileName] = Grd(strFileName, bRevertX=bRevertX, bRevertY=bRevertY, bUseSecondPol=bUseSecondPol, \
                                       alt=self.viewer.fAltM, lon=self.viewer.fLonDeg, bDisplaySlope=bDisplaySlope)
        return self.dicGrd[strFileName]
        
    def drawGrd(self, grd):
        x, y = self.map(grd.fLonDeg, grd.fLatDeg)
        if grd.bDisplaySlope == False:
            csGrd = self.map.contour(x, y, grd.Copol(), grd.fIsolvl, linestyles='solid', linewidths=0.5)
            self.axes.clabel(csGrd, grd.fIsolvl, inline=True, fmt='%1.1f',fontsize=5)
            return csGrd
        else:
            # define grid
            iNx = 201
            iNy = 201
            fAzlin = np.linspace(grd.MinAz(),grd.MaxAz(),iNx)
            fEllin = np.linspace(grd.MinEl(),grd.MaxEl(),iNy)
            fAzMesh, fElMesh = np.meshgrid(fAzlin, fEllin)
            # display color mesh
            cmap = plt.get_cmap('jet')
            cmap.set_over('white',grd.fSlope[1])
            cmap.set_under('white',grd.fSlope[0])
            xOrigin, yOrigin = self.map(self.viewer.fLonDeg,self.viewer.fLatDeg)
            pcmGrd = self.map.pcolormesh(self.Az2X(fAzMesh) + xOrigin, \
                                         self.El2Y(fElMesh) + yOrigin, \
                                         grd.InterpSlope(fAzMesh,fElMesh), \
                                         vmin=grd.fSlope[0],vmax=grd.fSlope[1], \
                                         cmap=cmap,alpha=0.5)
            # add color bar
            if self.cbar:
                self.cbar = self.fig.colorbar(pcmGrd, cax=self.cax)     
            else:
                divider = make_axes_locatable(self.axes)
                self.cax = divider.append_axes("right", size="5%", pad=0.05)
                self.cbar = self.fig.colorbar(pcmGrd,cax=self.cax)     
            self.cbar.ax.set_ylabel('Pattern slope (dB/deg)')

            return pcmGrd
            
    def drawStationList(self,stationList, fBpeCircle=None):
        for s in stationList:
            xSta, ySta = self.map(s.fLonDeg,s.fLatDeg)
            if fBpeCircle:
                circle = plt.Circle((xSta, ySta), self.viewer.fAltM * fBpeCircle * np.pi / 180, \
                                    color='k', fill=False, linewidth=0.3, linestyle='dashed')
            self.map.ax.add_artist(circle)
            self.map.scatter(xSta,ySta,3,marker='o',color='k')
            plt.text(xSta+s.fTagX, ySta+s.fTagY, s.strTag)
			


    # Zoom on the map
    def updateZoom(self):
        self.llcrnrx   = self.Az2X(self.zoom.fLowLeftAz)
        self.llcrnry   = self.El2Y(self.zoom.fLowLeftEl)
        self.urcrnrx   = self.Az2X(self.zoom.fUpRightAz)
        self.urcrnry   = self.El2Y(self.zoom.fUpRightEl)
        self.llcrnrlon = self.zoom.fLowLeftLon
        self.llcrnrlat = self.zoom.fLowLeftLat
        self.urcrnrlon = self.zoom.fUpRightLon
        self.urcrnrlat = self.zoom.fUpRightLat
        self.centerx   = (self.llcrnrx + self.urcrnrx) / 2
        self.centery   = (self.llcrnry + self.urcrnry) / 2
        self.cntrlon   = (self.llcrnrlon + self.urcrnrlon) / 2
        self.cntrlat   = (self.llcrnrlat + self.urcrnrlat) / 2

    # convert Azimuth to map.x
    def Az2X(self,fAz):
        return fAz * np.pi / 180 * self.viewer.fAltM
    
    # convert Elevation to map.y
    def El2Y(self,fEl):
        return fEl * np.pi / 180 * self.viewer.fAltM
    
    def X2Az(self,fX):
        return fX / ( np.pi / 180 * self.viewer.fAltM)
    
    def Y2El(self,fY):
        return fY / ( np.pi / 180 * self.viewer.fAltM)

