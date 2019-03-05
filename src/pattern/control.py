# file manipulation
import os.path

# import traceback utilities
import utils

# to be able to add action to menu Pattern
from PyQt5.QtWidgets import QAction, QFileDialog

# Import dialog to configure pattern display
from .dialog import PatternDialog

# import patterns classes
from .abstractpattern import AbstractPattern
from .pat import Pat
from .grd import Grd


class PatternControler(object):
    """A pattern controler is an attribute of and EarthPlot that links together a pattern, a dialog box and a menu
    """


    def __init__(self, parent, filename):
        """Initialize a pattern controler.
        parent is the earthplot which is used to display the pattern
        filename is the name of the file containing the pattern data
        """
        utils.trace('in')
        self._config ={}

        # name and path to the pattern data file
        self._config['filename'] = filename

        # reference of the parent EarthPlot
        self._earthplot = parent
        
        # reference of the Central Widget
        self._centralwidget = parent._centralwidget

        # Reference to the Main Window
        self._mainwindow = self._centralwidget.parent()

        # attribute pattern
        if self.isgrd():
            self._pattern = Grd(conf=self._config)
        elif self.ispat():
            self._pattern = Pat(conf=self._config)
        else:
            raise Exception('The file provided is not a grd file or a pat file.')

        # get Menu Pattern reference
        self._pattern_menu = self._mainwindow.menupattern
        # pattern sub menu
        self._pattern_sub_menu = self.add_menu_items(self._earthplot.get_file_key(self._config['filename']))

        # define _plot attribute for Controler
        self._plot = None

        # create dialog box to configure the pattern
        self._pdialog = PatternDialog(filename=self._config['filename'], parent=self._earthplot, control=self)
        utils.trace('out')
    # end of constructor

    def configure(self, dialog=True, config=None):
        """This method is used to update PatternControler attributes either via
        predefined configuration or via dialog window.
        """
        utils.trace('in')
        if config:
            self._config.update(config)
            self._pattern.configure(conf=config)
        if dialog:
            # if dialog use the GUI to update
            self._pdialog.configure(self._pattern)
            self._pdialog.setModal(True)
            self._pdialog.show()
            self._pdialog.exec_()
        utils.trace('out')
    # end of function configure

    def add_menu_items(self, file_key):
        utils.trace('in')
        # get Pattern menu reference and add sub menu for current pattern
        patternmenu = self._pattern_menu.addMenu(file_key)
        # add Remove action
        remove_pat_action = QAction('Remove', self._mainwindow)
        remove_pat_action.triggered.connect(self.remove_pattern)
        patternmenu.addAction(remove_pat_action)
        # add Edit action
        edit_pat_action = QAction('Edit', self._mainwindow)
        patternmenu.addAction(edit_pat_action)
        edit_pat_action.triggered.connect(self.edit_pattern)
        # add Export action
        export_pat_action = QAction('Export', self._mainwindow)
        patternmenu.addAction(export_pat_action)
        export_pat_action.triggered.connect(self.export_pattern)

        utils.trace('out')
        # return submenu
        return patternmenu

    def isgrd(self):
        """Return True if file extension is grd.
        """
        utils.trace()
        return self._config['filename'][-3:] == 'grd'
    # end of isgrd function

    def ispat(self):
        """Return True if file extension is pat.
        """
        utils.trace()
        return self._config['filename'][-3:] == 'pat'
    # end of isgrd function

    def plot(self):
        utils.trace('in')
        if self._plot:
            self.clear_plot()
        self._plot = self._pattern.plot(self._earthplot._earth_map, self._earthplot._viewer, \
                                        self._earthplot._figure, self._earthplot._axes, \
                                        self._earthplot._clrbar, self._earthplot._clrbar_axes)
        self._earthplot.draw()
        utils.trace('out')
        
    def clear_plot(self):
        """Clear the current plot
        """
        utils.trace('in')
        if self._config['display_slope']:
            self._plot.remove()
        else:
            for c in self._plot[0].collections:
                try:
                    c.remove()
                except ValueError:
                    print(c)
            if len(self._plot) > 1:
                self._plot[1][0].remove()
                self._plot[2].remove()
                for t in self._plot[3]:
                    t.remove()
        utils.trace('out')


    # def make_remove_pattern(self, file_key, patterns, eplot):
    def remove_pattern(self):
        """Callback maker for remove pattern menu items.
        """
        utils.trace('in')
        menu = self._pattern_sub_menu
        menu_action = menu.menuAction()
        menu.parent().removeAction(menu_action)
        # del patterns[file_key]
        del self._earthplot._patterns[self._config['key']]

        self._earthplot.draw_elements()
        utils.trace('out')
    # end of function make_remove_pattern

    def edit_pattern(self):
        """Callback maker for edit pattern menu items.
        """
        utils.trace('in')
        self.configure(dialog=True)
        utils.trace('out') 
    # end of function make_edit_pattern

    def export_pattern(self):
        """Open QDialog box to select file//directory where to export the file.
        """
        utils.trace('in')
        # get directory
        directory = self._earthplot.rootdir
        # recreate default filename with .pat extension
        f = os.path.basename(self._config['filename'])
        defaultfilename = f[:-4] + '.pat'
        # Get filename for exporting file
        filename, _ = QFileDialog.getSaveFileName(self._mainwindow,
                                                  'Select file',
                                                  os.path.join(directory, defaultfilename), 
                                                  'PAT (*.pat)')
        # get pattern to export
        if filename:
            self._pattern.export_to_file(filename, shrunk = self._pattern._shrink)
        utils.trace('out')
    # end of function export_pattern