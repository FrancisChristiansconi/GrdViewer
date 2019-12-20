# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 15:56:00 2018
This module contains definition of Pat class.
"""

# Third party modules import
# ==================================================================================================
import numpy as np

# local modules import
# ==================================================================================================
# debug trace utility
import patternviewer.utils as utils
# package constants definition
import patternviewer.constant as cst
# Definition of mother class AbstractPattern
from patternviewer.element.pattern.abstractpattern import AbstractPattern


class Pat(AbstractPattern):
    """This class implement reading and processing of Satsoft .pat files.
    """

    def __init__(self, filename=[], conf=None,
                 dialog=False, parent=None):
        """Initialize a Pat object
        """
        # just initialize object
        super().__init__(filename=filename, conf=conf,
                         dialog=dialog, parent=parent)

        # matrix to be plotted
        self._to_plot = np.zeros(shape=np.array(
            self._E_co).shape, dtype=float)

        for k in range(self._nb_sets):
            self._longitude.append(np.zeros_like(self._x[k]))
            self._latitude.append(np.zeros_like(self._x[k]))
            self._azimuth.append(np.zeros_like(self._x[k]))
            self._elevation.append(np.zeros_like(self._x[k]))

        # configure
        self.configure(config=conf)
    # End of function __init__

# Mandatory abstract method to implement
# --------------------------------------------------------------------------------------------------
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
                istart = i + 1
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
            raise ValueError(
                '101 grid format is not supported by this software.')
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
            x_vec.append(np.linspace(start=xs, stop=xe,
                                     num=nx, endpoint=True) + ix[k])
            y_vec.append(np.linspace(start=ys, stop=ye,
                                     num=ny, endpoint=True) + iy[k])
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
        E_mag_co = []  # first component of copol
        E_phs_co = []  # second component of copol
        E_mag_cr = []  # first component of crosspol
        E_phs_cr = []  # second component of crosspol
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

        # convert list to array
        E_mag_co = np.array(E_mag_co)
        E_phs_co = np.array(E_phs_co)
        E_co = (np.power(10, E_mag_co / 20)
                * np.cos(E_phs_co * np.pi / 180.0)
                + 1j * np.power(10, E_mag_co / 20)
                * np.sin(E_phs_co * np.pi / 180.0))

        E_mag_cr = np.array(E_mag_cr)
        E_phs_cr = np.array(E_phs_cr)
        E_cr = (np.power(10, E_mag_cr / 20)
                * np.cos(E_phs_cr * np.pi / 180.0)
                + 1j * np.power(10, E_mag_cr / 20)
                * np.sin(E_phs_cr * np.pi / 180.0))

        utils.trace('out')

        return nb_sets, \
            grid, \
            x, \
            y, \
            E_co, \
            E_cr
    # end of function read_file

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
        convert = {1: 1,
                   2: 2,
                   3: 5,
                   4: 4,
                   101: 101}
        return convert[self._grid]
    # end of function grid_type
# ==================================================================================================

# Electrical field processing
# --------------------------------------------------------------------------------------------------
    def magnitude(self, iunit, component1, component2):
        """Convert (C1, C2) to magnitude (dB) depending on IUNIT value
        """
        utils.trace('in')

        def convert(component1, component2):
            """Convert from real/imag electrical field values to magnitude.
            """
            return 20 * np.log10(np.absolute(component1 + 1j * component2))

        def identity(component1, _):
            """Return directly the magnitude which is the first component.
            """
            return component1

        # create the processing dictionary
        converter = {0: convert,
                     1: identity}

        # convert/extract the magnitude
        mag = converter[iunit](component1, component2)

        utils.trace('out')
        return mag
    # end of function magnitude

    def phase(self, iunit, component1, component2):
        """Convert (C1, C2) to phase (deg) depending on IUNIT value
        """
        utils.trace('in')

        def convert(component1, component2):
            """Convert from real/imag electrical field to phase (in degrees)
            """
            return np.angle(component1 + 1j * component2) * cst.RAD2DEG

        def identity(_, component2):
            """Directly returns component2 which is the phase.
            """
            return component2

        # create the processing dictionary
        converter = {0: convert,
                     1: identity}

        # convert/extract the magnitude
        phs = converter[iunit](component1, component2)

        utils.trace('out')
        return phs
    # end of function phase
# ==================================================================================================

    def rotate(self):
        # if requested by the new configuration,
        # rotate the pattern by 180 degrees
        for set in range(self._nb_sets):
            if ((self._rotate and not self._rotated)
                or (not self._rotate and self._rotated)):
                self._x[set] = -1 * self._x[set]
                self._y[set] = -1 * self._y[set]
                self._rotated = self._rotate

# end of class Pat
