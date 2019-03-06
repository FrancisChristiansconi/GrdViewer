"""This file contains definition of class PatternDialog. It's the GUI for Pattern (re)configuration.
"""


# system module
import sys

# utils
import utils

# PyQt5 widgets import
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QAction, qApp, QDialog, QLineEdit, \
                            QHBoxLayout, QVBoxLayout, QPushButton, QWidget, QFileDialog, QLabel, \
                            QGridLayout, QCheckBox
from PyQt5.QtGui import QColor, QPalette

# import numpy
import numpy as np

from matplotlib.collections import QuadMesh

# import pattern.py module 
# from pattern import Pattern, Grd, Pat

# import constant file
import constant as cst


class PatternDialog(QDialog):
    """QDialog derived class which is used to configure display of a pattern file.
    """

    # Constructor for PatternDialog class
    def __init__(self, filename: str=None, parent=None, control=None):
        utils.trace()
        # Parent constructor
        super().__init__()

        # abort the pattern loading ?
        self.abort = True

        # configure widget
        self.filename = filename
        self.earth_plot = parent
        self._control = control
        self._pattern = control._pattern
        self._plot = control._plot
        self._item = control._pattern_sub_menu

        # Add Title to the widget
        self.setWindowTitle('Load pattern')
        self.setMinimumSize(100, 100)

        # Everything in a vertical Layout
        vbox = QVBoxLayout(self)

        # Add file name
        self.filename_label = QLabel('File', parent=self)
        self.filename_field = QLineEdit('Dummy_file.txt', parent=self)
        self.filename_field.setEnabled(False)
        self.filename_field.adjustSize()
        hbox_filename = QHBoxLayout(None)
        hbox_filename.addWidget(self.filename_label)
        hbox_filename.addWidget(self.filename_field)
        vbox.addLayout(hbox_filename)

        # Add Title field
        self.title_label = QLabel('Title', parent=self)
        self.title_field = QLineEdit('Default Title', parent=self)
        hbox_title = QHBoxLayout(None)
        hbox_title.addWidget(self.title_label)
        hbox_title.addWidget(self.title_field)
        vbox.addLayout(hbox_title)

        # Add longitude/latitude/altitude fields
        self.lon_label = QLabel('Lon.', parent=self)
        self.lon_field = QLineEdit('0.0', parent=self)
        self.lat_label = QLabel('Lat.', parent=self)
        self.lat_field = QLineEdit('0.0', parent=self)
        self.alt_label = QLabel('Alt.', parent=self)
        self.alt_field = QLineEdit('0.0', parent=self)
        hbox_sat_position = QHBoxLayout(None)
        hbox_sat_position.addWidget(self.lon_label)
        hbox_sat_position.addWidget(self.lon_field)
        hbox_sat_position.addStretch(1)
        hbox_sat_position.addWidget(self.lat_label)
        hbox_sat_position.addWidget(self.lat_field)
        hbox_sat_position.addStretch(1)
        hbox_sat_position.addWidget(self.alt_label)
        hbox_sat_position.addWidget(self.alt_field)
        hbox_sat_position.addStretch(1)
        vbox.addLayout(hbox_sat_position)


        # Add isolevel 
        self.isolevel_label = QLabel('Isolevels', parent=self)
        self.isolevel_field = QLineEdit(self.get_isolevel(), parent=self)
        self.cf_label = QLabel('Conv. Factor', parent=self)
        self.cf_field = QLineEdit('0.0', parent=self)
        hbox_isolevel = QHBoxLayout(None)
        hbox_isolevel.addWidget(self.isolevel_label)
        hbox_isolevel.addWidget(self.isolevel_field)
        hbox_isolevel.addWidget(self.cf_label)
        hbox_isolevel.addWidget(self.cf_field)
        vbox.addLayout(hbox_isolevel)

        # Add checkboxes
        self.chk_revert_x = QCheckBox('Revert X axis', parent=self)
        self.chk_revert_y = QCheckBox('Revert Y axis', parent=self)
        self.chk_rotate = QCheckBox('Rotate 180deg', parent=self)
        hbox_revert = QHBoxLayout(None)
        hbox_revert.addWidget(self.chk_revert_x)
        hbox_revert.addWidget(self.chk_revert_y)
        hbox_revert.addWidget(self.chk_rotate)
        vbox.addLayout(hbox_revert)
        self.chkXPol    = QCheckBox('Use crosspol data', parent=self)
        self.chkXPol.stateChanged.connect(self.refresh_isolevel)
        self.chkSlope   = QCheckBox('Display Slope', parent=self)

        # place test field in a vertical box layout
        vbox.addWidget(self.chkXPol)
        vbox.addWidget(self.chkSlope)
        vbox.addStretch(1)

        # add shrink sub form
        self.chkshrink = QCheckBox('Shrink', parent=self)
        self.azshrklbl = QLabel('Az.', parent=self)
        self.azfield = QLineEdit('0.25', parent=self)
        # self.azfield.setFixedWidth(50)
        self.elshrklbl = QLabel('El.', parent=self)
        self.elfield = QLineEdit('0.25', parent=self)
        # self.elfield.setFixedWidth(50)
        hbox_shrink = QHBoxLayout(None)
        hbox_shrink.addWidget(self.chkshrink)
        hbox_shrink.addWidget(self.azshrklbl)
        hbox_shrink.addWidget(self.azfield)
        hbox_shrink.addWidget(self.elshrklbl)
        hbox_shrink.addWidget(self.elfield)
        hbox_shrink.addStretch(1)
        vbox.addLayout(hbox_shrink)
        self.chkshrink.stateChanged.connect(self.chkshrinkstatechanged)
        self.chkshrinkstatechanged()

        # add offset sub form
        self.chk_offset = QCheckBox('Offset', parent=self)
        self.az_offset_label = QLabel('Az.', parent=self)
        self.az_offset_field = QLineEdit('0.0', parent=self)
        self.el_offset_label = QLabel('El.', parent=self)
        self.el_offset_field = QLineEdit('0.0', parent=self)
        hbox_offset = QHBoxLayout(None)
        hbox_offset.addWidget(self.chk_offset)
        hbox_offset.addWidget(self.az_offset_label)
        hbox_offset.addWidget(self.az_offset_field)
        hbox_offset.addWidget(self.el_offset_label)
        hbox_offset.addWidget(self.el_offset_field)
        hbox_offset.addStretch(1)
        vbox.addLayout(hbox_offset)
        self.chk_offset.stateChanged.connect(self.chk_offset_state_changed)
        self.chk_offset_state_changed()


        # set fields value
        if filename:
            self.filename_field.setText(filename)
        if self.earth_plot:
            self.title_field.setText(self.earth_plot._plot_title)
            self.lon_field.setText(str(self.earth_plot._viewer.longitude()))
            self.lat_field.setText(str(self.earth_plot._viewer.latitude()))
            self.alt_field.setText(str(self.earth_plot._viewer.altitude()))
            # TODO do something for the multiple beams in one file case 
            self.cf_field.setText(str(self._pattern._conversion_factor))
        
        # Add Ok/Cancel buttons
        apply_button = QPushButton('Apply', self)
        ok_button = QPushButton('OK', self)
        cancel_button = QPushButton('Cancel', self)

        # Place Ok/Cancel button in an horizontal box layout
        hbox2 = QHBoxLayout()
        hbox2.addStretch(1)
        hbox2.addWidget(apply_button)
        hbox2.addWidget(ok_button)
        hbox2.addWidget(cancel_button)

        # put the button layout in the Vertical Layout
        vbox.addLayout(hbox2)

        # set dialog box layout
        self.setLayout(vbox)

        # connect buttons to actions
        apply_button.clicked.connect(self.set_pattern_conf)
        ok_button.clicked.connect(lambda: self.set_pattern_conf(close=True))
        cancel_button.clicked.connect(self.close)
        self.cf_field.textChanged.connect(self.refresh_isolevel)


        # Set default field value if pattern object has been provided
        if self._pattern:
            self.configure(self._pattern)
        
    # end of __init__

    def configure(self, pattern):
        utils.trace('in')
        try:
            self.title_field.setText(pattern._conf['title'])
        except KeyError:
            print('pattern.dialog: No title in pattern._conf dictionary.')
        self.lon_field.setText(str(pattern.satellite().longitude()))
        self.lat_field.setText(str(pattern.satellite().latitude()))
        self.alt_field.setText(str(pattern.satellite().altitude()))
        self.isolevel_field.setText(self.get_isolevel(pattern))
        self.chk_revert_x.setChecked(pattern._revert_x)
        self.chk_revert_y.setChecked(pattern._revert_y)
        self.chk_rotate.setChecked(pattern._rotate)
        self.chkXPol.setChecked(pattern._use_second_pol)
        self.chkSlope.setChecked(pattern._display_slope)
        self.chkshrink.setChecked(pattern._shrink)
        self.chk_offset.setChecked(pattern._offset)
        if pattern._shrink:
            self.azfield.setText(str(pattern._azshrink))
            self.elfield.setText(str(pattern._elshrink))
        if pattern._offset:
            self.az_offset_field.setText(str(pattern._azimuth_offset))
            self.el_offset_field.setText(str(pattern._elevation_offset))

        # disable use second pol option if second pol not available
        if len(pattern._E_mag_cr):
            self.chkXPol.setEnabled(True)
        else:
            self.chkXPol.setEnabled(False)
        
        self.refresh_isolevel()
        utils.trace('out')


    def get_isolevel(self, pattern=None):
        if pattern == None:
            return ",".join(str(x) for x in cst.DEFAULT_ISOLEVEL_DBI)
        else:
            return ",".join(str(x) for x in pattern._isolevel)

    def get_cf(self):
        """Return numerical conversion factor from widget field text.
        """
        cf_string = self.cf_field.text()
        try:
            cf_float = float(cf_string)
        except ValueError:
            cf_float = 0.0
        return cf_float

    def refresh_isolevel(self):
        if self._pattern:
            max_co = int(np.max(self._pattern.copol()))
            try:
                max_cr = int(np.max(self._pattern.cross()))
            except TypeError:
                max_cr = 0
        else:
            max_co = 0
            max_cr = 0

        cf = self.get_cf()
        if self.chkXPol.checkState():
            tmp_str = ",".join(str(x) for x in np.array(cst.DEFAULT_ISOLEVEL_DBI) + max_cr + cf)
        else:
            tmp_str = ",".join(str(x) for x in np.array(cst.DEFAULT_ISOLEVEL_DBI) + max_co + cf)
        
        self.isolevel_field.setText(tmp_str)

    def set_pattern_conf(self, close=False):
        # if no defined pattern attribute return 
        if not self._pattern:
            return

        conf = {}
        conf['revert_x'] = self.chk_revert_x.isChecked()
        conf['revert_y'] = self.chk_revert_y.isChecked()
        conf['rotate'] = self.chk_rotate.isChecked()
        conf['use_second_pol'] = self.chkXPol.isChecked()
        conf['sat_alt'] = float(self.alt_field.text())
        conf['sat_lon'] = float(self.lon_field.text())
        conf['sat_lat'] = float(self.lat_field.text())
        conf['display_slope'] = self.chkSlope.isChecked()
        conf['shrink'] = self.chkshrink.isChecked()
        if conf['shrink']:
            conf['azshrink'] = float(self.azfield.text())
            conf['elshrink'] = float(self.elfield.text())
        conf['offset'] = self.chk_offset.isChecked()
        if conf['offset']:
            conf['azoffset'] = float(self.az_offset_field.text())
            conf['eloffset'] = float(self.el_offset_field.text())
        conf['isolevel'] = [float(s) for s in self.isolevel_field.text().split(',')]

        self._pattern.configure(conf=conf)

        # self._pattern._isolevel = [float(s) for s in self.isolevel_field.text().split(',')]
        self.earth_plot.settitle(self.title_field.text())

        self._pattern._conversion_factor = float(self.cf_field.text())

        self.abort = False

        # update plot from GUI input
        self._control.plot()
        
        if close:
            self.close()
    # end of function set_pattern_conf

    # def addpattern(self):
    #     utils.trace('in')
    #     self.close()

    #     file_index = 1
    #     file_key = self.filename + ' ' + str(file_index)
    #     while (file_key in self.earth_plot._patterns) and file_index <= 50:
    #         file_index = file_index + 1
    #         file_key = self.filename + ' ' + str(file_index)
    #     if file_index == 50:
    #         print('Max repetition of same file reached. Index 50 will be overwritten')
        
    #     # add item in Grd menu
    #     patternmenu = self.parent.menupattern.addMenu(file_key)
    #     remove_pat_action = QAction('Remove', self.parent)
    #     edit_pat_action = QAction('Edit', self.parent)
    #     export_pat_action = QAction('Export', self.parent)
    #     patternmenu.addAction(remove_pat_action)
    #     patternmenu.addAction(edit_pat_action)
    #     patternmenu.addAction(export_pat_action)
    #     remove_pat_action.triggered.connect(self.make_remove_pattern(file_key, self.earth_plot._patterns, self.earth_plot))
    #     edit_pat_action.triggered.connect(self.make_edit_pattern(file_key, self.earth_plot._patterns, self.parent))
    #     export_pat_action.triggered.connect(self.make_export_pattern(file_key, self.earth_plot._patterns, self.parent))

    #     if self.filename[-3:] == 'grd':
    #         pattern = Grd(filename=self.filename, \
    #                       revert_x=self.chk_revert_x.checkState(), \
    #                       revert_y=self.chk_revert_y.checkState(), \
    #                       use_second_pol=self.chkXPol.checkState(), \
    #                       sat_alt=ALTGEO, \
    #                       sat_lon=float(self.lon_field.text()), \
    #                       display_slope=self.chkSlope.checkState(), \
    #                       shrink=self.chkshrink.checkState(), \
    #                       azshrink=float(self.azfield.text()), \
    #                       elshrink=float(self.elfield.text()))
    #     elif self.filename[-3:] == 'pat':
    #         pattern = Pat(filename=self.filename, \
    #                       revert_x=self.chk_revert_x.checkState(), \
    #                       revert_y=self.chk_revert_y.checkState(), \
    #                       use_second_pol=self.chkXPol.checkState(), \
    #                       sat_alt=ALTGEO, \
    #                       sat_lon=float(self.lon_field.text()), \
    #                       display_slope=self.chkSlope.checkState(), \
    #                       shrink=self.chkshrink.checkState(), \
    #                       azshrink=float(self.azfield.text()), \
    #                       elshrink=float(self.elfield.text()))

    #     self.earth_plot._patterns[file_key] = {'pattern': pattern, 'menu': patternmenu, 'plot': pattern.plot()}
    #     self.earth_plot.settitle(self.title_field.text())
    #     pattern._isolevel = [float(s) for s in self.isolevel_field.text().split(',')]
    #     self.earth_plot.draw_elements()
    #     utils.trace('out')
    # # end of function addpattern
    
    def make_remove_pattern(self, file_key, patterns, eplot):
        """Callback maker for remove pattern menu items.
        """
        utils.trace('in')
        def remove_pattern():
            utils.trace('in')
            menu = patterns[file_key]['menu']
            menu_action = menu.menuAction()
            menu.parent().removeAction(menu_action)
            del patterns[file_key]
            self.clear_plot()
            utils.trace('out')
            # eplot.draw_elements()
        utils.trace('out')
        return remove_pattern
    # end of function make_remove_pattern

    def make_edit_pattern(self, file_key, patterns, dialog_parent):
        """Callback maker for edit pattern menu items.
        """
        utils.trace('in')
        filename = ' '.join(file_key.split(' ')[:-1])
        def edit_pattern():
            utils.trace('in')
            dialbox = PatternDialog(filename, dialog_parent, patterns[file_key])
            dialbox.exec_()
            utils.trace('out')
        utils.trace('ou')
        return edit_pattern  
    # end of function make_edit_pattern

    def make_export_pattern(self, file_key, patterns, dialog_parent):
        """Open QDialog box to select file//directory where to export the file.
        """
        utils.trace('in')
        # get file path + file name
        filepath = ' '.join(file_key.split(' ')[:-1])
        # get directory
        directory = self.earth_plot.rootdir
        # recreate default filename with .pat extension
        defaultfilename = '.'.join(os.path.basename(filepath).split('.')[:-1]) + '.pat'
        def export_pattern():
            utils.trace('in')
            # Get filename for exporting file
            filename, _ = QFileDialog.getSaveFileName(dialog_parent,
                                                      'Select file',
                                                      os.path.join(directory, defaultfilename), 
                                                      'PAT (*.pat)')

            # get pattern to export
            if filename:
                pattern = patterns[file_key]['pattern']
                pattern.export_to_file(filename, shrunk = pattern._shrink)
            
            utils.trace('out')
        utils.trace('out')
        return export_pattern
    # end of function make_export_pattern

    def chkshrinkstatechanged(self):
        """Callback deactivating the shrink fields wheb shrink checkbox is unchecked.
        """
        utils.trace()
        self.azfield.setEnabled(self.chkshrink.isChecked())
        self.elfield.setEnabled(self.chkshrink.isChecked())
    # end of callback

    def chk_offset_state_changed(self):
        utils.trace()
        self.az_offset_field.setEnabled(self.chk_offset.isChecked())
        self.el_offset_field.setEnabled(self.chk_offset.isChecked())
    # end of callback

    def clear_plot(self):
        """Clear the current plot
        """
        utils.trace('in')
        if type(self._plot) is QuadMesh:
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
# end of classe PatternDialog


# Main execution
if __name__ == '__main__':   
    # Create main window
    MAIN_WINDOW = QApplication(sys.argv)
    APP = PatternDialog()

    # Start main loop
    sys.exit(MAIN_WINDOW.exec_())

# end of module grdviewer