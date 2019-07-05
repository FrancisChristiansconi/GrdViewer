

import numpy as np

from patternviewer.element.pattern.grd import Grd


class MultiGrd(Grd):

    def __init__(self, filenames=[], excfilename=None, conf=None,
                 dialog=None, parent=None):
        """Initialize a multigrd object
        """
        # just initialize object
        super().__init__(filenames, conf, dialog, parent)

        # read excitation file name or return (0,0,...,0)
        self.excitation_law = self.read_excitation_file(excfilename)

    def read_file(self, filename):
        nb_sets_list = []
        grid_list = []
        x_list = []
        y_list = []
        E_mag_co_list = []
        E_phs_co_list = []
        E_mag_cr_list = []
        E_phs_cr_list = []
        for f in filename:
            (nb_sets, grid, x, y,
             E_mag_co, E_phs_co, E_mag_cr, E_phs_cr) = super().read_file(f)
            nb_sets_list.append(nb_sets)
            grid_list.append(grid)
            x_list.append(x)
            y_list.append(y)
            E_mag_co_list.append(E_mag_co)
            E_phs_co_list.append(E_phs_co)
            E_mag_cr_list.append(E_mag_cr)
            E_phs_cr_list.append(E_phs_cr)
        return (nb_sets_list, grid_list, x_list, y_list, E_mag_co_list,
                E_phs_co_list, E_mag_cr_list, E_phs_cr_list)

    def read_excitation_file(self, excfilename=None):
        if excfilename is not None:
            # open file and read text data
            file = open(excfilename, "r")
            # read all lines in a table
            lines = file.readlines()
            # close file
            file.close()
        else:
            return np.zeros(self.get_number_re(), dtype=complex)

    def get_number_re(self):
        if self.nb_sets is not []:
            return len(self.nb_sets)

    def copol(self):
        pass

    def cross(self):
        pass
