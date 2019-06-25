from patternviewer.element.pattern.grd import Grd


class MultiGrd(Grd):

    def __init__(self, filenames=[], excfilename=None, conf=None, dialog=None, parent=None):
        """Initialize a multigrd object
        """
        # just initialize object
        super().__init__(filenames, conf, dialog, parent)

        # read excitation file name or return (0,0,...,0)
        self.excitation_file = self.read_excitation_file(excfilename)

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

    def read_excitation_file(self, excfilename):
        # open file and read text data
        file = open(excfilename, "r")
        # read all lines in a table
        lines = file.readlines()
        # close file
        file.close()

        
