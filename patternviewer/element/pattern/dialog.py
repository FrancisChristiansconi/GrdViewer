"""This file contains definition of class PatternDialog. It's the GUI for Pattern (re)configuration.
"""

# import standard modules
#--------------------------------------------------------------------------------------------------
# system module
import sys
#==================================================================================================

# import third party modules
#--------------------------------------------------------------------------------------------------
# import of PyQt5 for all GUI elements
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QAction, qApp, QDialog, \
                            QLineEdit, QHBoxLayout, QVBoxLayout, QPushButton, QWidget, \
                            QFileDialog, QLabel, QGridLayout, QCheckBox, QGridLayout
from PyQt5.QtGui import QColor, QPalette
# import numpy
import numpy as np
#==================================================================================================

# import local modules
#--------------------------------------------------------------------------------------------------
# debug utility module
import patternviewer.utils as utils
# import constant file
import patternviewer.constant as cst
# import line configuration dialog
from patternviewer.element.linedialog import LineDialog
#==================================================================================================

# classe definition
#--------------------------------------------------------------------------------------------------
class PatternDialog(QDialog):
    """QDialog derived class which is used to configure display of a pattern file.
    """

    def __init__(self, filename: str=None, parent=None, control=None):
        """Constructor for PatternDialog class.
        filename: str is the path to the file containing data of antenna pattern
        parent is the EarthPlot instance which will display the antenna pattern
        control is the antenna pattern controler instance
        """
        utils.trace()
        # Parent constructor
        super().__init__()

        # abort the pattern loading ?
        self.abort = True

        # configure widget
        self.filename = filename
        self.earth_plot = parent
        self._control = control
        self._pattern = None
        self._plot = None
        self._item = None
        if control is not None:
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

        # options grid layout
        self.chkxpol = QCheckBox('Use crosspol data', parent=self)
        self.chkxpol.stateChanged.connect(self.refresh_isolevel)
        self.chkslope = QCheckBox('Display Slope', parent=self)
        self.chksurf = QCheckBox('Color surface', parent=self)
        optionbox = QGridLayout(None)
        optionbox.addWidget(self.chkxpol, 1, 1)
        optionbox.addWidget(self.chkslope, 1, 2)
        optionbox.addWidget(self.chksurf, 1, 3)
        vbox.addLayout(optionbox)

        # add shrink sub form
        self.chkshrink = QCheckBox('Shrink', parent=self)
        self.azshrklbl = QLabel('Az.', parent=self)
        self.azfield = QLineEdit('0.25', parent=self)
        self.elshrklbl = QLabel('El.', parent=self)
        self.elfield = QLineEdit('0.25', parent=self)
        self.azfield.setFixedWidth(50)
        self.elfield.setFixedWidth(50)
        # self.elfield.setFixedWidth(50)
        hbox_shrink = QGridLayout(None)
        hbox_shrink.addWidget(self.chkshrink, 1, 1)
        hbox_shrink.addWidget(self.azshrklbl, 1, 2)
        hbox_shrink.addWidget(self.azfield, 1, 3)
        hbox_shrink.addWidget(self.elshrklbl, 1, 4)
        hbox_shrink.addWidget(self.elfield, 1, 5)
        # hbox_shrink.addStretch(1)
        # vbox.addLayout(hbox_shrink)
        self.chkshrink.stateChanged.connect(self.chkshrinkstatechanged)
        self.chkshrinkstatechanged()

        # add offset sub form
        self.chk_offset = QCheckBox('Offset', parent=self)
        self.az_offset_label = QLabel('Az.', parent=self)
        self.az_offset_field = QLineEdit('0.0', parent=self)
        self.el_offset_label = QLabel('El.', parent=self)
        self.el_offset_field = QLineEdit('0.0', parent=self)
        self.az_offset_field.setFixedWidth(50)
        self.el_offset_field.setFixedWidth(50)
        # hbox_shrink = QHBoxLayout(None)
        hbox_shrink.addWidget(self.chk_offset, 1, 6)
        hbox_shrink.addWidget(self.az_offset_label, 1, 7)
        hbox_shrink.addWidget(self.az_offset_field, 1, 8)
        hbox_shrink.addWidget(self.el_offset_label, 1, 9)
        hbox_shrink.addWidget(self.el_offset_field, 1, 10)
        # hbox_shrink.addStretch(1)
        vbox.addLayout(hbox_shrink)
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
        lines_button = QPushButton('Lines', self)
        apply_button = QPushButton('Apply', self)
        ok_button = QPushButton('OK', self)
        cancel_button = QPushButton('Cancel', self)

        # Place Ok/Cancel button in an horizontal box layout
        hbox2 = QHBoxLayout()
        hbox2.addStretch(1)
        hbox2.addWidget(lines_button)
        hbox2.addWidget(apply_button)
        hbox2.addWidget(ok_button)
        hbox2.addWidget(cancel_button)

        # put the button layout in the Vertical Layout
        vbox.addLayout(hbox2)

        # set dialog box layout
        self.setLayout(vbox)

        # connect buttons to actions
        lines_button.clicked.connect(self.setlines)
        apply_button.clicked.connect(self.set_pattern_conf)
        ok_button.clicked.connect(lambda: self.set_pattern_conf(close=True))
        cancel_button.clicked.connect(self.close)
        self.cf_field.textChanged.connect(self.refresh_isolevel)


        # Set default field value if pattern object has been provided
        if self._pattern:
            self.configure(self._pattern)
    # end of __init__

    def configure(self, pattern):
        """This method configure the fields of the dialog with the pattern configuration values.
        pattern is the antenna pattern object which provide the configuration for this GUI
        """
        utils.trace('in')
        try:
            self.title_field.setText(pattern._conf['title'])
        except KeyError:
            print('pattern.dialog: No title in pattern._conf dictionary.')
        self.lon_field.setText(str(pattern.satellite().longitude()))
        self.lat_field.setText(str(pattern.satellite().latitude()))
        self.alt_field.setText(str(pattern.satellite().altitude()))
        self.isolevel_field.setText(self.get_isolevel())
        self.chk_revert_x.setChecked(pattern._revert_x)
        self.chk_revert_y.setChecked(pattern._revert_y)
        self.chk_rotate.setChecked(pattern._rotated)
        self.chkxpol.setChecked(pattern._use_second_pol)
        self.chkslope.setChecked(pattern._display_slope)
        self.chkshrink.setChecked(pattern._shrink)
        self.chk_offset.setChecked(pattern._offset)
        self.chksurf.setChecked(pattern.set(pattern.configure(), 'Color surface', False))
        if pattern._shrink:
            self.azfield.setText(str(pattern._azshrink))
            self.elfield.setText(str(pattern._elshrink))
        if pattern._offset:
            self.az_offset_field.setText(str(pattern._azimuth_offset))
            self.el_offset_field.setText(str(pattern._elevation_offset))

        # disable use second pol option if second pol not available
        if len(pattern._E_mag_cr):
            self.chkxpol.setEnabled(True)
        else:
            self.chkxpol.setEnabled(False)

        self.refresh_isolevel()
        utils.trace('out')
    # end of configure method

    def get_isolevel(self, pattern=None):
        """Return string formatted isolevel list. Each value separated with comma.
        pattern is the antenna pattern
        """
        if self._pattern == None:
            return ",".join(str(x) for x in cst.DEFAULT_ISOLEVEL_DBI)
        else:
            return ",".join(str(x) for x in self._pattern.get_isolevel())
    # end of function get_isolevel

    def get_cf(self):
        """Return numerical conversion factor from widget field text.
        """
        cf_string = self.cf_field.text()
        try:
            cf_float = float(cf_string)
        except ValueError:
            cf_float = 0.0
        return cf_float
    # end of function get_cf

    def refresh_isolevel(self):
        """Refresh isolevel field regarding polarisation selected and
        absolute isolevel stored in pattern configuration dictionary.
        """
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
        isolevel = np.array(self._pattern._isolevel) - np.max(self._pattern._isolevel)
        if self.chkxpol.checkState():
            tmp_str = ",".join(str(x) for x in isolevel + max_cr + cf)
        else:
            tmp_str = ",".join(str(x) for x in isolevel + max_co + cf)

        self.isolevel_field.setText(tmp_str)
    # end of method refresh_isolevel

    def set_pattern_conf(self, close=False):
        utils.trace('in')

        # if no defined pattern attribute return
        if not self._pattern:
            return

        config = {}
        config['revert_x'] = self.chk_revert_x.isChecked()
        config['revert_y'] = self.chk_revert_y.isChecked()
        config['rotate'] = self.chk_rotate.isChecked()
        config['use_second_pol'] = self.chkxpol.isChecked()
        config['sat_alt'] = float(self.alt_field.text())
        config['sat_lon'] = float(self.lon_field.text())
        config['sat_lat'] = float(self.lat_field.text())
        config['display_slope'] = self.chkslope.isChecked()
        config['shrink'] = self.chkshrink.isChecked()
        if config['shrink']:
            config['azshrink'] = float(self.azfield.text())
            config['elshrink'] = float(self.elfield.text())
        config['offset'] = self.chk_offset.isChecked()
        if config['offset']:
            config['azoffset'] = float(self.az_offset_field.text())
            config['eloffset'] = float(self.el_offset_field.text())
        config['isolevel'] = [float(s) for s in self.isolevel_field.text().split(',')]
        config['cf'] = float(self.cf_field.text())
        config['Color surface'] = self.chksurf.isChecked()

        self._pattern.configure(config=config)

        # self._pattern._isolevel = [float(s) for s in self.isolevel_field.text().split(',')]
        self.earth_plot.settitle(self.title_field.text())

        self._pattern._conversion_factor = float(self.cf_field.text())

        self.abort = False

        # update plot from GUI input
        self._control.plot()

        if close:
            self.close()
        utils.trace('out')
    # end of function set_pattern_conf

    def chkshrinkstatechanged(self):
        """Callback deactivating the shrink fields when shrink checkbox is unchecked.
        """
        utils.trace()
        self.azfield.setEnabled(self.chkshrink.isChecked())
        self.elfield.setEnabled(self.chkshrink.isChecked())
    # end of callback

    def chk_offset_state_changed(self):
        """Callback deactivating the offset fields when checkbox is unchecked.
        """
        utils.trace()
        self.az_offset_field.setEnabled(self.chk_offset.isChecked())
        self.el_offset_field.setEnabled(self.chk_offset.isChecked())
    # end of callback

    def setlines(self):
        linedlg = LineDialog(self._pattern)
        self.setModal(False)
        linedlg.setModal(True)
        # linedlg.show()
        linedlg.exec_()
        self.setModal(True)

# end of classe PatternDialog

# Main execution
if __name__ == '__main__':
    # Create main window
    MAIN_WINDOW = QApplication(sys.argv)
    APP = PatternDialog()
    APP.show()

    # Start main loop
    sys.exit(MAIN_WINDOW.exec_())

# end of module grdviewer