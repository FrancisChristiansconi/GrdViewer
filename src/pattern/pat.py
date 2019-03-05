import numpy as np

import utils

import constant as cst

from .abstractpattern import AbstractPattern

class Pat(AbstractPattern):
    """This class implement reading and processing of Satsoft .pat files.
    """

    def read_file(self, filename):
        utils.trace('in')
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
        # 3 - az over el
        # 4 - el over az
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
            
        xs = float(lines[istart].split(sep)[0]) * cst.RAD2DEG
        xe = float(lines[istart].split(sep)[2]) * cst.RAD2DEG
        ys = float(lines[istart].split(sep)[1]) * cst.RAD2DEG
        ye = float(lines[istart].split(sep)[3]) * cst.RAD2DEG 

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
                E_phs_cr.append(self.phase(iunit, c21, c22))
        # end for

        
        utils.trace('out')

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
            return np.angle(c1 + 1j * c2) * cst.RAD2DEG
        
        def identity(c1, c2):
            return c2

        converter = {0: convert, \
                     1: identity}

        return converter[iunit](c1, c2)
    # end of function phase
    
    # def getmax(self, k=0):
    #     """Get max directivity value and coordinates.
    #     """
    #     max_value = np.max(self._E_mag_co[k])
    #     max_index = np.argmax(self._E_mag_co[k])
    #     max_longitude = self.longitude().flatten()[max_index]
    #     max_latitude = self.latitude().flatten()[max_index]
    #     return max_value, max_longitude, max_latitude
    # # end of function getmax

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
        return self._azimuth[k]
        
    def elevation(self, k: int=0):
        """This function provide elevation grid for self, beam number k.
        """
        return self._elevation[k]


    # Longitude/ Latitude
    ###################################################################

    def longitude(self, k: int=0):
        """Project grid on Earth viewed from observer point of view. Return longitude.
        """
        return self._longitude[k]
    # end of function longitude

    def latitude(self, k: int=0):
        """Project grid on Earth viewed from observer point of view. Return latitude.
        """
        return self._latitude[k]
    # end of function latitude
# end of class Pat