"""Multiple GRD file module
"""

# Standard modules import

# Third party modules import
# =============================================================================
# numpy for computation
import numpy as np
# import pyproj for coordinates conversion
import pyproj as prj
# for efficient loops over several dimensions
import itertools

# Local modules import
# =============================================================================
# project modules
import patternviewer.utils as utils
import patternviewer.constant as cst
import patternviewer.angles as ang
# patterns related modules
from patternviewer.element.pattern.grd import Grd
from patternviewer.element.pattern.abstractpattern import AbstractPattern


class UnassortedGrid(Exception):
    """This class defines the exception to be raised when unassorted pattern
    files are provided to MultiGrd __init__ function.
    """
    def __init__(self, message):
        """message: description of the context of the exception raising
        """
        self.message = message
    # end of function __init__
# end of class UnassortedGrid


class MultiGrd(Grd):
    """Class Multigrd definition.
    Object defined by this class handle a set of grd file and excitation law
    in order to vizualise active antenna resulting pattern.
    """

    def __init__(self, filenames=[], excfilename=None, conf=None,
                 dialog=False, parent=None):
        """Initialize a multigrd object
        """
        # set number of radiating elements to the number of files provided
        self._nb_re = len(filenames)

        # read excitation file name or return (1, 1, ..., 1)
        self._excitation_law = \
            self.read_exc_file(excfilename=excfilename)

        # Initialize object
        AbstractPattern.__init__(self=self, filename=filenames,
                                 conf=conf, dialog=dialog,
                                 parent=parent)

        # Initialize matrix to be plotted
        self._to_plot = np.zeros(shape=np.array(
            self._E_co[0]).shape, dtype=float)

        # Initialize grids
        for set in range(self._nb_sets):
            self._longitude.append(np.zeros_like(self._x[set]))
            self._latitude.append(np.zeros_like(self._x[set]))
            self._azimuth.append(np.zeros_like(self._x[set]))
            self._elevation.append(np.zeros_like(self._x[set]))

        # configure pattern object
        self.configure(config=conf)

    # End of function __init__

    def read_file(self, filename):
        """Overloading of read_file function from Grd class to handle a set
        of grd instead of only one
        """
        utils.trace('in')
        nb_sets_list = []
        grid_list = []
        x_list = []
        y_list = []
        E_co_list = []
        E_cr_list = []
        for f in filename:
            (nb_sets, grid, x, y,
             E_co, E_cr) = Grd.read_file(None, f)
            nb_sets_list.append(nb_sets)
            grid_list.append(grid)
            x_list.append(x)
            y_list.append(y)
            E_co_list.append(E_co)
            E_cr_list.append(E_cr)

        # for all field common to the RE unit files, use only the
        # value from the first file in the series
        nb_sets = nb_sets_list[0]
        grid = grid_list[0]
        # if grid of the files are different throw exception
        for x in x_list[1:]:
            if not np.array_equal(x_list[0], x):
                raise UnassortedGrid("x coordinate grids are not identical.")
        x = x_list[0]
        for y in y_list[1:]:
            if not np.array_equal(y_list[0], y):
                raise UnassortedGrid("x coordinate grids are not identical.")
        y = y_list[0]

        nb_re, nb_set, nb_rows, nb_col = np.array(E_co_list).shape
        E_co = np.zeros((nb_set, nb_rows, nb_col, nb_re), dtype=complex)
        E_cr = np.zeros((nb_set, nb_rows, nb_col, nb_re), dtype=complex)
        for s, r, c, e in itertools.product(range(nb_set),
                                            range(nb_rows),
                                            range(nb_col),
                                            range(nb_re)):
            # print('{} {} {} {}'.format(s, r, c, e))
            E_co[s][r][c][e] = E_co_list[e][s][r][c]
            E_cr[s][r][c][e] = E_cr_list[e][s][r][c]

        utils.trace('out')
        return (nb_sets, grid, x, y, E_co, E_cr)
    # End of function read_file

    def read_exc_file(self, excfilename=None, nbre=None):
        """This function reads an excitation law file.
        It is still a WIP as the format is not known yet.
        By default the law is full of ones.
        """
        try:
            # open file and read text data
            file = open(excfilename, "r")
            # read all lines in a table
            lines = file.readlines()
            # close file
            file.close()
            # read A/phi law in file
            As = []
            phis = []
            for l in lines[1:self.get_number_re() + 1]:
                splitted = l.split()
                As.append(float(splitted[1]))
                phis.append(float(splitted[2]))
            As = np.array(As)
            phis = np.array(phis)
            # convert to complex array
            law = As * np.exp(1j * phis * np.pi / 180.0)
            return law

        except FileNotFoundError:
            errmsg = 'Excitation file {} does not exist in file system.'
            print(errmsg.format(excfilename))
            if nbre is not None:
                _nbre = nbre
            else:
                _nbre = self.get_number_re()
            return np.ones(_nbre, dtype=np.complex)
    # End of function read_excitation_file

    def get_number_re(self):
        """Return the number of radiating element of the antenna.
        This number is retrieved using the number of elementary pattern.
        """
        return self._nb_re
    # End of function get_number_re

    def copol(self, set=0):
        """Compute copolarisation magnitude (in dBi).
        Overloading Grd.Copol()
        """
        utils.trace('in')
        _, nb_rows, nb_cols, _ = np.array(self._E_co).shape
        E_co = np.zeros((nb_rows, nb_cols), dtype=complex)
        for r, c in itertools.product(range(nb_rows),
                                      range(nb_cols)):
            E_co[r][c] = np.dot(self._E_co[set][r][c],
                                self._excitation_law)
        z = 20.0 * np.log10(np.abs(E_co))
        z[np.where(np.isnan(z))] = -99
        z[np.where(np.isneginf(z))] = -99

        utils.trace('out')
        return z
    # End of function copol

    def cross(self):
        """Compute crosspolarisation magnitude (in dBi).
        Overloading Grd.cross().
        """
        utils.trace('in')
        _, nb_rows, nb_cols, _ = np.array(self._E_cr).shape
        E_cr = np.zeros((nb_rows, nb_cols), dtype=complex)
        for r, c in itertools.product(range(nb_rows),
                                      range(nb_cols)):
            E_cr[r][c] = np.dot(self._E_cr[set][r][c],
                                self._excitation_law)
        z = 20.0 * np.log10(np.abs(E_cr))
        z[np.where(np.isnan(z))] = -99
        z[np.where(np.isneginf(z))] = -99

        utils.trace('out')
        return z
    # End of function cross

# End of class MultiGrd
