# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 15:56:39 2018

@author: cfrance
"""

# import built-in modules
#------------------------------------------------------------------------------
# import plotting utilities
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# import array/calculus utilities
import numpy as np

# local module
import Pattern as rgrd

# Pattern files
strA2FPETx= './data/A2F_PE_Tx_pointing_0E_0N_G01_12515.00.grd'
strA2FPETxE2= './data/A2F_PE_Tx_pointing_0E_0N_E02_11739.00.grd'
strA2FPERx= './data/A2F_PE_Rx_pointing_0E_0N_G1_13765.00.grd'
strA2EPETx= './data/A2E_PE_Tx_Steering_model_412_12500.00_H.grd'
strA2GPETx= './data/A2G_PE_Tx_High_B_Tx_11.70000_H.grd'
fMinSlope = 3 		# dB/deg
fMaxSlope = 20 		# dB/deg
fMinLevel = 46		# dBi
fMaxLevel = 62		# dBi
fIsolevel = range(fMinLevel, fMaxLevel, 2)
fIsoSlope = range(fMinSlope, fMaxSlope+5, 5)

# Orbital slot #2
fSatLong = 28.2     # deg
fSatLat  = 0.0      # deg 
fSatAlt  = 35786000 # m

# Display Europe
fAzMin   = -5       # degrees
fAzMax   =  0.5     # degrees
fElMin   =  5       # degrees
fElMax   =  8.5     # degrees
# Display complete Earth
# fAzMin   = -9       # degrees
# fAzMax   =  9       # degrees
# fElMin   = -9       # degrees
# fElMax   =  9       # degrees

# Finess of graphs
iNx = 1001
iNy = 1001

# Station dictionary
dicStation = { \
	'Agesta'   :{'disp':False,'code':'AGE','lon': 18.08,'lat': 59.21,'xlab':1e4,'ylab':1e4}, \
	'Apuglia'  :{'disp':False,'code':'APU','lon': 16.72,'lat': 40.64,'xlab':1e4,'ylab':1e4}, \
	'Betzdorf' :{'disp':True ,'code':'BTZ','lon':  6.33,'lat': 49.69,'xlab':-6e4,'ylab':-8e4}, \
	'Budapest' :{'disp':False,'code':'BUD','lon': 19.01,'lat': 47.38,'xlab':1e4,'ylab':1e4}, \
	'Cagliari' :{'disp':False,'code':'CGL','lon':  8.97,'lat': 39.25,'xlab':1e4,'ylab':1e4}, \
	'Cork'     :{'disp':False,'code':'CRK','lon': -8.18,'lat': 51.95,'xlab':1e4,'ylab':1e4}, \
	'Darmstadt':{'disp':False,'code':'DAR','lon':  8.56,'lat': 49.86,'xlab':1e4,'ylab':1e4}, \
	'Denmark'  :{'disp':False,'code':'DEN','lon':  8.11,'lat': 55.56,'xlab':1e4,'ylab':1e4}, \
	'Frejus'   :{'disp':False,'code':'FRE','lon':  6.44,'lat': 43.25,'xlab':1e4,'ylab':1e4}, \
	'Fucino'   :{'disp':False,'code':'FUC','lon': 13.60,'lat': 41.98,'xlab':1e4,'ylab':1e4}, \
	'Gibraltar':{'disp':True ,'code':'GIB','lon': -5.34,'lat': 36.12,'xlab':1e4,'ylab':1e4}, \
	'Hanover'  :{'disp':False,'code':'HAN','lon':  9.32,'lat': 52.06,'xlab':1e4,'ylab':1e4}, \
	'La Ciotat':{'disp':False,'code':'CIO','lon':  5.60,'lat': 43.20,'xlab':-15e4,'ylab':-7e4}, \
	'Lario'    :{'disp':True ,'code':'LAR','lon':  9.41,'lat': 46.16,'xlab':1e4,'ylab':1e4}, \
	'Madrid'   :{'disp':True ,'code':'MAD','lon': -3.79,'lat': 40.40,'xlab':1e4,'ylab':1e4}, \
	'Munich'   :{'disp':True ,'code':'MUN','lon': 11.65,'lat': 48.19,'xlab':1e4,'ylab':1e4}, \
	'Nemea'    :{'disp':False,'code':'NMA','lon': 22.37,'lat': 37.5 ,'xlab':1e4,'ylab':1e4}, \
	'Norway'   :{'disp':True ,'code':'NWA','lon':  6.46,'lat': 58.53,'xlab':1e4,'ylab':1e4}, \
	'Palermo'  :{'disp':False,'code':'SIC','lon': 13.36,'lat': 37.91,'xlab':1e4,'ylab':1e4}, \
	'Palma'    :{'disp':False,'code':'PAL','lon':  2.63,'lat': 39.63,'xlab':1e4,'ylab':1e4}, \
	'Redu'     :{'disp':True ,'code':'RED','lon':  5.15,'lat': 50   ,'xlab':-18e4,'ylab':1e4}, \
	'Riga'     :{'disp':False,'code':'RIG','lon': 24.12,'lat': 56.93,'xlab':1e4,'ylab':1e4}, \
	'Sintra'   :{'disp':True ,'code':'SIN','lon': -9.28,'lat': 38.87,'xlab':1e4,'ylab':1e4}, \
	'Toulouse' :{'disp':True ,'code':'TLS','lon':  1.50,'lat': 43.48,'xlab':1e4,'ylab':1e4}, \
	'Wien'     :{'disp':False,'code':'WIE','lon': 16.2 ,'lat': 48.17,'xlab':1e4,'ylab':1e4}}
	
# load pattern files
print('Loading: ' + strA2FPETx)
oA2FGrd = rgrd.Grd(strA2FPETx)
print('Loading: ' + strA2FPETxE2)
oA2FE2Grd = rgrd.Grd(strA2FPETxE2,bUseSecondPol=True)
print('Loading: ' + strA2FPERx)
oA2FRxGrd = rgrd.Grd(strA2FPERx, bUseSecondPol=True)
print('Loading: ' + strA2EPETx)
oA2EGrd = rgrd.Grd(strA2EPETx)
print('Loading: ' + strA2GPETx)
oA2GGrd = rgrd.Grd(strA2GPETx, True, True)

# spacecraft dictionary
dicA2F = { \
	'sc':'A2F_G1', \
	'cf':18.96, \
	'lon':fSatLong, \
	'lat':fSatLat, \
	'alt':fSatAlt, \
	'Az':(fAzMin,fAzMax), \
	'El':(fElMin,fElMax),
	'grd':oA2FGrd, \
	'slope':range(fMinSlope, fMaxSlope+1,1), \
	'level':range(fMinLevel, fMaxLevel, 2)}
	
dicA2FE2 = { \
	'sc':'A2F_E2', \
	'cf':19.03, \
	'lon':fSatLong, \
	'lat':fSatLat, \
	'alt':fSatAlt, \
	'Az':(fAzMin,fAzMax), \
	'El':(fElMin,fElMax),
	'grd':oA2FE2Grd, \
	'slope':range(fMinSlope, fMaxSlope+1,1), \
	'level':range(fMinLevel, fMaxLevel, 2)}
	
dicA2FRx = { \
	'sc':'A2F_PE_Rx', \
	'cf':-27.476, \
	'lon':fSatLong, \
	'lat':fSatLat, \
	'alt':fSatAlt, \
	'Az':(fAzMin,fAzMax), \
	'El':(fElMin,fElMax),
	'grd':oA2FRxGrd, \
	'slope':range(0, 6, 1), \
	'level':range(2, 14, 2)}

dicA2E = { \
	'sc':'A2E', \
	'cf':18.96, \
	'lon':fSatLong, \
	'lat':fSatLat, \
	'alt':fSatAlt, \
	'Az':(fAzMin,fAzMax), \
	'El':(fElMin,fElMax),
	'grd':oA2EGrd, \
	'slope':[fMinSlope, fMaxSlope], \
	'level':range(fMinLevel, fMaxLevel, 2)}

dicA2G = { \
	'sc':'A2G', \
	'cf':18.96, \
	'lon':fSatLong, \
	'lat':fSatLat, \
	'alt':fSatAlt, \
	'Az':(fAzMin,fAzMax), \
	'El':(fElMin,fElMax),
	'grd':oA2GGrd, \
	'slope':[fMinSlope, fMaxSlope], \
	'level':range(fMinLevel, fMaxLevel, 2)}

# Get area with more than 5dB/degree slope for the three patterns
# A = np.logical_and(oA2FGrd.Slope() > fMinSlope, oA2FGrd.Slope() < fMaxSlope)
# B = oA2EGrd.InterpSlope(oA2FGrd.Azimuth(), oA2FGrd.Elevation())
# B = np.logical_and(B > fMinSlope, B < fMaxSlope)
# C = oA2GGrd.InterpSlope(oA2FGrd.Azimuth(), oA2FGrd.Elevation())
# C = np.logical_and(C > fMinSlope, C < fMaxSlope)
#J = np.logical_and(np.logical_and(A,B),C)
# D = np.logical_and(np.logical_and(A,B),C)
# E = 1-D

# Directivity criterion > 30dBi
#F = oA2GGrd.InterpCo(oA2FGrd.Azimuth(), oA2FGrd.Elevation()) > 30
#G = oA2EGrd.InterpCo(oA2FGrd.Azimuth(), oA2FGrd.Elevation()) > 30
#H = oA2FGrd.Copol() > 30
#I = np.logical_and(np.logical_and(F,G),H)
#K = np.logical_and(I,J)
#E = 1-np.reshape([int(b) for b in K.flatten()],K.shape)

# Compute elevation of spacecraft seen from a station on the ground
def elevation(fSatLon, fSatAlt, fStaLon, fStaLat):
	# Earth radius (meters)
	fEarthRad = 6378137.00
	
	# compute phi
	fPhi = np.arccos(np.cos(np.pi / 180 * fStaLat) * np.cos(np.pi / 180 * (fSatLon - fStaLon)))

	# compute elevation
	fElev = np.reshape([90 if phi == 0 else 180 / np.pi * np.arctan((np.cos(phi) - (fEarthRad/(fEarthRad+fSatAlt)))/ np.sin(phi)) for phi in fPhi.flatten()], fPhi.shape)
	
	# remove station out of view
	fElev = np.where(np.absolute(fStaLon - fSatLon) < 90,fElev,-1)
	
	# Return vector
	return fElev
	
	
def generatePlot(dicSat, strSlope, fIsolevel, fIsoslope):
	print('Plotting slopes for: ' + dicSat['sc'] + '/' + strSlope)

	def xformat(x,pos=None): return '{:0.1f}'.format((x - (map.xmax-map.xmin)/2) / (dicSat['alt'] * np.pi / 180))
	def yformat(y,pos=None): return '{:0.1f}'.format((y - (map.ymax-map.ymin)/2) / (dicSat['alt'] * np.pi / 180))
	# open plot
	fig,ax = plt.subplots(num=None, figsize=(8, 6), dpi=300, facecolor='w', edgecolor='k')
	
	# choose color map
	# strCMapName = 'Reds'
	strCMapName = 'jet'

	# create map for projection
	map = Basemap(projection='geos', lat_0=fSatLat, lon_0=fSatLong, \
		rsphere=(6378137.00,6356752.3142), \
		llcrnrx=fAzMin * np.pi / 180 * dicSat['alt'], \
		llcrnry=fElMin * np.pi / 180 * dicSat['alt'], \
		urcrnrx=fAzMax * np.pi / 180 * dicSat['alt'], \
		urcrnry=fElMax * np.pi / 180 * dicSat['alt'], \
		resolution='l', \
		suppress_ticks=False)
	
	# tick formatter
	xformatter = FuncFormatter(xformat)
	yformatter = FuncFormatter(yformat)
	ax.xaxis.set_major_formatter(xformatter)
	ax.yaxis.set_major_formatter(yformatter)
	
	# shortcut
	oGrd = dicSat['grd']

	# convert Az and El to x,y coordination in the projection plan
	x = dicSat['alt'] * oGrd.Azimuth() * np.pi / 180 + (map.xmax-map.xmin)/2
	y = dicSat['alt'] * oGrd.Elevation() * np.pi / 180 + (map.ymax-map.ymin)/2
	xLin = np.linspace(oGrd.MinAz(), oGrd.MaxAz(), iNx)
	yLin = np.linspace(oGrd.MinEl(), oGrd.MaxEl(), iNy)
	AzCmesh, ElCmesh = np.meshgrid(xLin, yLin)
	xCmesh = dicSat['alt'] * AzCmesh * np.pi / 180 + (map.xmax-map.xmin)/2
	yCmesh = dicSat['alt'] * ElCmesh * np.pi / 180 + (map.ymax-map.ymin)/2
	fStaLon, fStaLat = map(x, y, inverse=True)
	
	# draw coastlines, country boundaries
	map.drawcoastlines(linewidth=0.25)
	map.drawcountries(linewidth=0.25)
	# draw lat/lon grid lines every 30 degrees.
	map.drawmeridians(np.arange(0,360,30))
	map.drawparallels(np.arange(-90,90,30))
	map.drawmapboundary()

	cmap = plt.get_cmap(strCMapName)

	fMinSlope = np.min(dicSat['slope'])
	fMaxSlope = np.max(dicSat['slope'])	
	fMinLevel = np.min(dicSat['level'])
	fMaxLevel = np.max(dicSat['level'])	
	
	if strSlope == 'Az':
		plt.title(dicSat['sc'] + ' Azimuth Slopes between ' + str(fMinSlope) + ' and ' + str(fMaxSlope) + ' dB/deg')
		cs = map.contour(x,y, oGrd.Copol() + dicSat['cf'], dicSat['level'], linestyles='solid', linewidths=0.5)
		cs2 = map.contour(x,y,elevation(dicSat['lon'],dicSat['alt'],fStaLon,fStaLat), (10,20), colors=['black','black'], linestyles='dashed', linewidths=0.5)
		cmesh = map.pcolormesh(xCmesh, yCmesh, oGrd.InterpAzElSlope(AzCmesh,ElCmesh)['Az'], alpha=0.5, cmap=cmap, vmin=fMinSlope, vmax=fMaxSlope)
	elif strSlope == 'El':
		plt.title(dicSat['sc'] + ' Elevation Slopes between ' + str(fMinSlope) + ' and ' + str(fMaxSlope) + ' dB/deg')
		cs = map.contour(x,y, oGrd.Copol() + dicSat['cf'], dicSat['level'], linestyles='solid', linewidths=0.5)
		cs2 = map.contour(x,y,elevation(dicSat['lon'],dicSat['alt'],fStaLon,fStaLat), (10,20), colors=['black','black'], linestyles='dashed', linewidths=0.5)
		cmesh = map.pcolormesh(xCmesh, yCmesh, oGrd.InterpAzElSlope(AzCmesh,ElCmesh)['El'], alpha=0.5, cmap=cmap, vmin=fMinSlope, vmax=fMaxSlope)
	elif strSlope == 'Both':
		plt.title(dicSat['sc'] + ' combined Slopes between ' + str(fMinSlope) + ' and ' + str(fMaxSlope) + ' dB/deg')
		cs = map.contour(x,y, oGrd.Copol() + dicSat['cf'], dicSat['level'], linestyles='solid', linewidths=0.5)
		cs2 = map.contour(x,y,elevation(dicSat['lon'],dicSat['alt'],fStaLon,fStaLat), (10,20), colors=['black','black'], linestyles='dashed', linewidths=0.5)
		cmesh = map.pcolormesh(xCmesh, yCmesh, oGrd.InterpSlope(AzCmesh,ElCmesh), alpha=0.5, cmap=cmap, vmin=fMinSlope, vmax=fMaxSlope)
	elif strSlope == 'Quiver':
		plt.title(dicSat['sc'] + ' Vector field Slopes between ' + str(fMinSlope) + ' and ' + str(fMaxSlope) + ' dB/deg')
		cs = map.contour(x,y, oGrd.Copol() + dicSat['cf'], dicSat['level'], linestyles='solid', linewidths=0.5)
		quiv = map.quiver(xCmesh, yCmesh, \
						  # -1 * oGrd.InterpAzElSlope(AzCmesh,ElCmesh,True)['Az'], \
						  # oGrd.InterpAzElSlope(AzCmesh,ElCmesh,True)['El'], \
						  # np.clip(oGrd.InterpSlope(AzCmesh,ElCmesh),fMinSlope,fMaxSlope), \
						  oGrd.AzElSlope(True)['Az'], \
						  oGrd.AzElSlope(True)['El'], \
						  oGrd.Slope(), \
						  angles='xy', cmap=cmap, scale=2e3, width=1 / 1e3, headlength=4, headwidth=3)
	if strSlope != 'Quiver':
		cmap.set_under('#FFFFFF')
		cmap.set_over('#FFFFFF')
		cbar=map.colorbar(cmesh,size="3%", label='Slope (dB/deg)',extend="neither",ticks=dicSat['slope'])
	# elif strSlope == 'Quiver':
		# cbar=map.colorbar(quiv,size="3%", label='Slope (dB/deg)',extend="neither",ticks=fIsoSlope)
		
	ax.clabel(cs, inline=True, fontsize=7, inline_spacing=1, fmt='%1.1f')
	ax.clabel(cs2, inline=True, fontsize=7, inline_spacing=1, fmt='%1.0f')

	# display station
	for k in dicStation:
		if dicStation[k]['disp']:
			xSta,ySta = map(dicStation[k]['lon'],dicStation[k]['lat'])
			xCntr, yCntr = map(fSatLong, fSatLat)
			fMaxBpe = 0.25
			circle = plt.Circle((xSta, ySta), dicSat['alt'] * fMaxBpe * np.pi / 180, color='k', fill=False, linewidth=0.3, linestyle='dashed')
			ax.add_artist(circle)
			map.scatter(xSta,ySta,3,marker='o',color='k')
			plt.text(xSta+dicStation[k]['xlab'], ySta+dicStation[k]['ylab'], dicStation[k]['code'])
			print(k + ' ' + str(oGrd.InterpSlope(np.array((xSta-xCntr) / (np.pi / 180 * dicSat['alt'])), np.array((ySta-yCntr) / (np.pi / 180 * dicSat['alt'])))))
	
	plt.xlabel('Azimuth (deg)')
	plt.ylabel('Elevation (deg)')
	plt.ioff()
	#plt.show()
	fig.savefig('./out/' + dicSat['sc'] + '_' + strSlope + '.png')
	
def generateMulti(dicSat1, dicSat2, dicSat3, strSlope, fIsolevel, fIsoslope):
	print('Plotting slopes for: ' + dicSat1['sc'] + ',' + dicSat2['sc'] + ',' + dicSat3['sc'] + '/' + strSlope)

	def xformat(x,pos=None): return '{:0.1f}'.format((x - (map.xmax-map.xmin)/2) / (dicSat1['alt'] * np.pi / 180))
	def yformat(y,pos=None): return '{:0.1f}'.format((y - (map.ymax-map.ymin)/2) / (dicSat1['alt'] * np.pi / 180))
	# open plot
	fig,ax = plt.subplots(num=None, figsize=(8, 6), dpi=300, facecolor='w', edgecolor='k')
	
	# choose color map
	strCMapName = 'jet'

	# create map for projection
	map = Basemap(projection='geos', lat_0=fSatLat, lon_0=fSatLong, \
		rsphere=(6378137.00,6356752.3142), \
		llcrnrx=fAzMin * np.pi / 180 * dicSat1['alt'], \
		llcrnry=fElMin * np.pi / 180 * dicSat1['alt'], \
		urcrnrx=fAzMax * np.pi / 180 * dicSat1['alt'], \
		urcrnry=fElMax * np.pi / 180 * dicSat1['alt'], \
		resolution='l', \
		suppress_ticks=False)
	
	# tick formatter
	xformatter = FuncFormatter(xformat)
	yformatter = FuncFormatter(yformat)
	ax.xaxis.set_major_formatter(xformatter)
	ax.yaxis.set_major_formatter(yformatter)
	
	# shortcut
	oGrd1 = dicSat1['grd']
	oGrd2 = dicSat2['grd']
	oGrd3 = dicSat3['grd']

	# convert Az and El to x,y coordination in the projection plan
	x = dicSat1['alt'] * oGrd1.Azimuth() * np.pi / 180 + (map.xmax-map.xmin)/2
	y = dicSat1['alt'] * oGrd1.Elevation() * np.pi / 180 + (map.ymax-map.ymin)/2
	xLin = np.linspace(oGrd1.MinAz(), oGrd1.MaxAz(), iNx)
	yLin = np.linspace(oGrd1.MinEl(), oGrd1.MaxEl(), iNy)
	AzCmesh, ElCmesh = np.meshgrid(xLin, yLin)
	xCmesh = dicSat1['alt'] * AzCmesh * np.pi / 180 + (map.xmax-map.xmin)/2
	yCmesh = dicSat1['alt'] * ElCmesh * np.pi / 180 + (map.ymax-map.ymin)/2
	
	# draw coastlines, country boundaries
	map.drawcoastlines(linewidth=0.25)
	map.drawcountries(linewidth=0.25)
	# draw lat/lon grid lines every 30 degrees.
	map.drawmeridians(np.arange(0,360,30))
	map.drawparallels(np.arange(-90,90,30))
	map.drawmapboundary()

	# generate colormap
	cmap = plt.get_cmap(strCMapName)

	# generate grid value
	if strSlope == 'Az':
		fArea1 = np.logical_and(oGrd1.InterpAzElSlope(AzCmesh,ElCmesh)['Az'] > fMinSlope, oGrd1.InterpAzElSlope(AzCmesh,ElCmesh)['Az'] < fMaxSlope)
		fArea2 = np.logical_and(oGrd2.InterpAzElSlope(AzCmesh,ElCmesh)['Az'] > fMinSlope, oGrd2.InterpAzElSlope(AzCmesh,ElCmesh)['Az'] < fMaxSlope)
		fArea3 = np.logical_and(oGrd3.InterpAzElSlope(AzCmesh,ElCmesh)['Az'] > fMinSlope, oGrd3.InterpAzElSlope(AzCmesh,ElCmesh)['Az'] < fMaxSlope)
		fArea  = np.logical_and(fArea1,np.logical_and(fArea2,fArea3))

		plt.title('Azimuth Slopes between ' + str(fMinSlope) + ' and ' + str(fMaxSlope) + ' dB/deg')
		cmesh = map.pcolormesh(xCmesh, yCmesh, fArea, alpha=0.5, cmap=cmap, vmin=0.5, vmax=1)
	elif strSlope == 'El':
		fArea1 = np.logical_and(oGrd1.InterpAzElSlope(AzCmesh,ElCmesh)['El'] > fMinSlope, oGrd1.InterpAzElSlope(AzCmesh,ElCmesh)['El'] < fMaxSlope)
		fArea2 = np.logical_and(oGrd2.InterpAzElSlope(AzCmesh,ElCmesh)['El'] > fMinSlope, oGrd2.InterpAzElSlope(AzCmesh,ElCmesh)['El'] < fMaxSlope)
		fArea3 = np.logical_and(oGrd3.InterpAzElSlope(AzCmesh,ElCmesh)['El'] > fMinSlope, oGrd3.InterpAzElSlope(AzCmesh,ElCmesh)['El'] < fMaxSlope)
		fArea  = np.logical_and(fArea1,np.logical_and(fArea2,fArea3))

		plt.title('Elevation Slopes between ' + str(fMinSlope) + ' and ' + str(fMaxSlope) + ' dB/deg')
		cmesh = map.pcolormesh(xCmesh, yCmesh, fArea, alpha=0.5, cmap=cmap, vmin=0.5, vmax=1)
	elif strSlope == 'Both':
		fArea1 = np.logical_and(oGrd1.InterpSlope(AzCmesh,ElCmesh) > fMinSlope, oGrd1.InterpSlope(AzCmesh,ElCmesh) < fMaxSlope)
		fArea2 = np.logical_and(oGrd2.InterpSlope(AzCmesh,ElCmesh) > fMinSlope, oGrd2.InterpSlope(AzCmesh,ElCmesh) < fMaxSlope)
		fArea3 = np.logical_and(oGrd3.InterpSlope(AzCmesh,ElCmesh) > fMinSlope, oGrd3.InterpSlope(AzCmesh,ElCmesh) < fMaxSlope)
		fArea  = np.logical_and(fArea1,np.logical_and(fArea2,fArea3))

		plt.title('Total Slopes between ' + str(fMinSlope) + ' and ' + str(fMaxSlope) + ' dB/deg')
		cmesh = map.pcolormesh(xCmesh, yCmesh, fArea, alpha=0.5, cmap=cmap, vmin=0.5, vmax=1)
	
	cmap.set_under('#FFFFFF')
	cmap.set_over('#FFFFFF')
	# cbar=map.colorbar(cmesh,size="3%", label='Slope (dB/deg)',extend="neither",ticks=(0,1))		
	
	# display station
	for k in dicStation:
		xSta,ySta = map(dicStation[k]['lon'],dicStation[k]['lat'])
		map.scatter(xSta,ySta,3,marker='o',color='k')
		plt.text(xSta+dicStation[k]['xlab'], ySta+dicStation[k]['ylab'], dicStation[k]['code'])
	
	
	plt.xlabel('Azimuth (deg)')
	plt.ylabel('Elevation (deg)')
	plt.ioff()
	#plt.show()
	fig.savefig('./out/' + dicSat1['sc'] + '_' + dicSat2['sc'] + '_' + dicSat3['sc'] + '_' + strSlope + '.png')
	
	
# create plots for A2F
# generatePlot(dicA2F, 'Az',   fIsolevel,fIsoSlope)
# generatePlot(dicA2F, 'El',   fIsolevel,fIsoSlope)
generatePlot(dicA2F, 'Both', fIsolevel,fIsoSlope)
# generatePlot(dicA2F, 'Quiver', fIsolevel,fIsoSlope)
# generatePlot(dicA2FRx, 'Az',   fIsolevel,fIsoSlope)
# generatePlot(dicA2FRx, 'El',   fIsolevel,fIsoSlope)
# generatePlot(dicA2FRx, 'Both', fIsolevel,fIsoSlope)
# generatePlot(dicA2FE2, 'Az',   fIsolevel,fIsoSlope)
# generatePlot(dicA2FE2, 'El',   fIsolevel,fIsoSlope)
generatePlot(dicA2FE2, 'Both', fIsolevel,fIsoSlope)

# create plots for A2E
# generatePlot(dicA2E, 'Az',   fIsolevel,fIsoSlope)
# generatePlot(dicA2E, 'El',   fIsolevel,fIsoSlope)
# generatePlot(dicA2E, 'Both', fIsolevel,fIsoSlope)

# create plots for A2G
# generatePlot(dicA2G, 'Az',   fIsolevel,fIsoSlope)
# generatePlot(dicA2G, 'El',   fIsolevel,fIsoSlope)
# generatePlot(dicA2G, 'Both', fIsolevel,fIsoSlope)

# combined for the 3 spacecraft
# generateMulti(dicA2E, dicA2F, dicA2G, 'Az', fIsolevel, fIsoSlope)
# generateMulti(dicA2E, dicA2F, dicA2G, 'El', fIsolevel, fIsoSlope)
# generateMulti(dicA2E, dicA2F, dicA2G, 'Both', fIsolevel, fIsoSlope)



print('End')



