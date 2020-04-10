"""Multiple GRD file module
"""

# Standard modules import
import os
import sys
import logging


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
        filenames = conf['file']
        excfilename = conf['excfilename']
        self._nb_re = len(filenames)

        # read excitation file name or return (1, 1, ..., 1)
        _law = self.read_exc_file(excfilename=excfilename)
        self._excitation_law = list(_law.items())[0][1]

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

        # Store excitation law in configuration dictionary
        self._configuration['law'] = _law
        # by default apply first law
        self.apply_law(0)

    # End of function __init__

    def read_file(self, filename):
        """Overloading of read_file function from Grd class to handle a set
        of grd instead of only one
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(filename={filename})').format(
                filename=filename
        ))
        nb_sets_list = []
        grid_list = []
        x_list = []
        y_list = []
        E_co_list = []
        E_cr_list = []

        # create progres bar
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
            E_co[s][r][c][e] = E_co_list[e][s][r][c]
            E_cr[s][r][c][e] = E_cr_list[e][s][r][c]

        return (nb_sets, grid, x, y, E_co, E_cr)
    # End of function read_file

    def read_exc_file(self, excfilename=None):
        if excfilename[-3:] == 'exi':
            return self.read_exi_file(excfilename=excfilename)
        else:
            return self.read_wts_file(excfilename=excfilename)

    def read_exi_file(self, excfilename=None):
        """This function reads an excitation law file (GRASP format).
        It is still a WIP as the format is not known yet.
        By default the law is full of ones.
        """
        # initialize law dictionary
        _law = {}
        try:
            # get number of radiating elements
            _nbre = self.get_number_re()
            _law_size = _nbre
            _law_id = '1'
            # open file and read text data
            file = open(excfilename, "r")
            # read all lines in a table
            _lines = file.readlines()
            # close file
            file.close()
            # read A/phi law in file
            _As = np.zeros(_nbre, dtype=float)
            _phis = np.zeros(_nbre, dtype=float)
            _header = 0
            for _i in range(len(_lines)):
                if _lines[_i][:4] == '++++':
                    _header = _i + 1
                    break
            for _i in range(len(_lines) - _header):
                _splitted = _lines[_i + _header].split()
                _As[_i] = np.power(10, float(_splitted[1]) / 20.0)
                _phis[_i] = float(_splitted[2])
            # convert to complex array
            _law[_law_id] = _As * np.exp(1j * _phis * np.pi / 180.0)

        except FileNotFoundError:
            _errmsg = 'Excitation file {} does not exist in file system.'
            print(_errmsg.format(excfilename))
            _nbre = self.get_number_re()
            _law['default'] = np.ones(_nbre, dtype=complex)

        # return law dictionary
        return _law
    # End of function read_excitation_file

    def read_wts_file(self, excfilename=None):
        """This function reads an excitation law file (ADS format).
        It is still a WIP as the format is not known yet.
        By default the law is full of ones.
        """
        # initialize law dictionary
        _law = {}
        try:
            # get number of radiating elements
            _nbre = self.get_number_re()
            _law_size = _nbre + 1
            # open file and read text data
            file = open(excfilename, "r")
            # read all lines in a table
            _lines = file.readlines()
            # close file
            file.close()
            # read A/phi law in file
            _As = np.zeros(_nbre, dtype=float)
            _phis = np.zeros(_nbre, dtype=float)
            _law_nb = int(len(_lines) / _law_size)
            for _i in range(_law_nb):
                _splitted = _lines[_i * _law_size].split()
                _law_id = _splitted[0]
                for _j in range(_nbre):
                    _splitted = _lines[(_i * _law_size) + _j + 1].split()
                    _As[_j] = float(_splitted[1])
                    _phis[_j] = float(_splitted[2])
                # convert to complex array
                _law[_law_id] = _As * np.exp(1j * _phis * np.pi / 180.0)

        except FileNotFoundError:
            _errmsg = 'Excitation file {} does not exist in file system.'
            print(_errmsg.format(excfilename))
            _nbre = self.get_number_re()
            _law['default'] = np.ones(_nbre, dtype=complex)

        # return law dictionary
        return _law
    # End of function read_wts_file

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
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(set={set})').format(
                set=set
        ))
        _, nb_rows, nb_cols, _ = np.array(self._E_co).shape
        E_co = np.zeros((nb_rows, nb_cols), dtype=complex)
        for r, c in itertools.product(range(nb_rows),
                                      range(nb_cols)):
            E_co[r][c] = np.dot(self._E_co[set][r][c],
                                self._excitation_law)
        z = 20.0 * np.log10(np.abs(E_co))
        z[np.where(np.isnan(z))] = -99
        z[np.where(np.isneginf(z))] = -99

        return z
    # End of function copol

    def cross(self, set=0):
        """Compute crosspolarisation magnitude (in dBi).
        Overloading Grd.cross().
        """
        logging.debug((
            sys._getframe().f_code.co_filename.split('\\')[-1]
            + ':' + sys._getframe().f_code.co_name
            + '(set={set})').format(
                set=set
        ))
        _, nb_rows, nb_cols, _ = np.array(self._E_cr).shape
        E_cr = np.zeros((nb_rows, nb_cols), dtype=complex)
        for r, c in itertools.product(range(nb_rows),
                                      range(nb_cols)):
            E_cr[r][c] = np.dot(self._E_cr[set][r][c],
                                self._excitation_law)
        z = 20.0 * np.log10(np.abs(E_cr))
        z[np.where(np.isnan(z))] = -99
        z[np.where(np.isneginf(z))] = -99

        return z
    # End of function cross

    def apply_law(self, law_id):
        if type(law_id) is int:
            if law_id < len(self._configuration['law']) and law_id >= 0:
                (self._configuration['applied_law'],
                 self._excitation_law) = list(
                    self._configuration['law'].items())[law_id]
        elif law_id in self._configuration['law'].keys():
            self._excitation_law = self._configuration['law'][law_id]
            self._configuration['applied_law'] = law_id
        else:
            raise TypeError
    # end of method apply_law

    def diffpolygon(self, polygon):
        """Substract the gain of the polygon to the current beamformed pattern.
        """
        p = polygon.path()
        result = np.zeros(self.E_co.shape)
        # project the polygon to the pattern grid

        copol = self.copol()
        lon = self.longitude()
        lat = self.latitude()
        for i, j in itertools.product(copol.shape[0],
                                      copol.shape[1]):
            if p.contains_points((lon[i][j], lat[i][j])):
                result[i][j] = copol[i][j] - polygon.gain

        return result

# End of class MultiGrd
