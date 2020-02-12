"""This module defines controler for patterns objects.
"""

# file manipulation
import os.path

# to be able to add action to menu Pattern
from PyQt5.QtWidgets import QAction, QFileDialog

# axes manipulation
from mpl_toolkits.axes_grid1 import make_axes_locatable, Size

# import traceback utilities
import patternviewer.utils as utils

# Import dialog to configure pattern display
from patternviewer.element.pattern.dialog import PatternDialog

# import patterns classes
from patternviewer.element.pattern.abstractpattern import AbstractPattern
from patternviewer.element.pattern.pat import Pat
from patternviewer.element.pattern.grd import Grd
from patternviewer.element.pattern.multigrd import MultiGrd


class PatternControler():
    """A pattern controler is an attribute of and EarthPlot that
    links together a pattern, a dialog box and a menu.
    """

    def __init__(self, parent, config):
        """Initialize a pattern controler.
        parent is the earthplot which is used to display the pattern
        filename is the name of the file containing the pattern data
        """
        self._config = config

        # reference of the parent EarthPlot
        self._earthplot = parent

        # reference of the Central Widget
        self._centralwidget = parent.get_centralwidget()

        # Reference to the Main Window
        self._mainwindow = self._centralwidget.parent()

        # attribute pattern
        if self.isgrd():
            self._pattern = Grd(conf=self._config, parent=self)
        elif self.ispat():
            self._pattern = Pat(conf=self._config, parent=self)
        elif self.ismultigrd():
            self._pattern = MultiGrd(conf=self._config, parent=self)
        else:
            raise Exception(
                'The file provided is not a grd file or a pat file.')

        # get Menu Pattern reference
        self._pattern_menu = self._mainwindow.menupattern
        # pattern sub menu
        file_key = self._earthplot.get_file_key(self._config['file'])
        self._pattern_sub_menu = self.add_menu_items(file_key)

        # define _plot attribute for Controler
        self._plot = None
        self._plot_type = None

        # create dialog box to configure the pattern
        self._pdialog = PatternDialog(filename=self._config['file'],
                                      parent=self._earthplot,
                                      control=self)
    # end of constructor

    def configure(self, config=None, dialog=True):
        """This method is used to update PatternControler attributes either via
        predefined configuration or via dialog window.
        """
        utils.trace('in')
        if config:
            self._config.update(config)
            self._pattern.configure(config=config)
        if dialog:
            # if dialog use the GUI to update
            self._pdialog.configure(self._pattern)
            self._pdialog.setModal(True)
            self._pdialog.show()
            self._pdialog.exec_()

        utils.trace('out')
        return self._config
    # end of function configure

    def add_menu_items(self, file_key):
        """Add Pattern menu elements to exploit current pattern.
        """
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
        return self._config['file'][-3:] == 'grd'
    # end of isgrd function

    def ispat(self):
        """Return True if file extension is pat.
        """
        utils.trace()
        return self._config['file'][-3:] == 'pat'
    # end of ispat function

    def ismultigrd(self):
        return type(self._config['file']) is list
    # End of ismultigrd function

    def plot(self):
        """Plot the antenna pattern into the parent EarthPlot.
        """
        utils.trace('in')
        if self._plot:
            self.clearplot()
        self._plot = self._pattern.plot()
        try:
            if self._config['slope'] is True:
                self._plot_type = 'surf'
            else:
                self._plot_type = 'contour'
            self._earthplot.draw()
        except KeyError:
            # if KeyError it means that Cancel button has been pressed
            print('control.plot: issue with display_slope attribute')
        utils.trace('out')
    # end of function plot

    def clearplot(self):
        """Clear the current plot
        """
        self._pattern.clearplot()
    # end of function clear_plot

    # def make_remove_pattern(self, file_key, patterns, eplot):
    def remove_pattern(self):
        """Callback maker for remove pattern menu items.
        """
        utils.trace('in')
        menu = self._pattern_sub_menu
        menu_action = menu.menuAction()
        menu.parent().removeAction(menu_action)

        # delete reference to pattern object
        del self._earthplot._patterns[self._config['key']]

        # clear the plot and redraw EarthPlot
        self.clearplot()
        self._earthplot.draw()

        # refresh pattern combo box
        itemlist = ['']
        itemlist.extend(self._earthplot._patterns.keys())
        self._mainwindow.setpatterncombo(itemlist)

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
        if isinstance(self._pattern, MultiGrd):
            default_filename = ''
        else:
            origin_filename = os.path.basename(self._config['file'])
            default_filename = origin_filename[:-3] + 'pat'
        # Get filename for exporting file
        filename, _ = \
            QFileDialog.getSaveFileName(parent=self._mainwindow,
                                        caption='Select file',
                                        directory=os.path.join(
                                            directory,
                                            default_filename),
                                        filter='pattern file (*.pat)')
        # get pattern to export
        if filename:
            self._pattern.export_to_file(
                filename, shrunk=self._pattern._shrink)
        utils.trace('out')
    # end of function export_pattern

    def get_config(self):
        """Return _config protected attribute.
        """
        return self._config
    # end of function get_config

    def get_pattern(self):
        """Return _pattern attribute of the controller.
        """
        return self._pattern
    # end of function get_pattern

    def get_earthplot(self):
        """Return this controler reference to the parent earth plot object.
        """
        return self._earthplot
    # end of function get_earthplot

# end of module control
