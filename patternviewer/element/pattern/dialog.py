"""This file contains definition of class PatternDialog.
It's the GUI for Pattern (re)configuration.
"""

# import standard modules
# --------------------------------------------------------------------------------------------------
# system module
import sys
# ==================================================================================================

# import third party modules
# --------------------------------------------------------------------------------------------------
# import of PyQt5 for all GUI elements
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, \
    QAction, qApp, QDialog, QComboBox, \
    QLineEdit, QHBoxLayout, QVBoxLayout, QPushButton, QWidget, \
    QFileDialog, QLabel, QGridLayout, QCheckBox, QGridLayout
from PyQt5.QtGui import QColor, QPalette
from PyQt5 import QtCore
# import numpy
import numpy as np
# ==================================================================================================

# import local modules
# --------------------------------------------------------------------------------------------------
# debug utility module
import patternviewer.utils as utils
# import constant file
import patternviewer.constant as cst
# import line configuration dialog
from patternviewer.element.linedialog import LineDialog
# ==================================================================================================

# classe definition
# --------------------------------------------------------------------------------------------------


class PatternDialog(QDialog):
    """QDialog derived class which is used to configure display of
    a pattern file.
    """

    def __init__(self, filename: str = None, parent=None, control=None):
        """Constructor for PatternDialog class.
        filename is the path to the file containing data of
            antenna pattern
        parent is the EarthPlot instance which will display
            the antenna pattern
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
        self._patternctlr = None
        self._plot = None
        self._item = None
        if control is not None:
            self._patternctlr = control._pattern
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
        self.yaw_label = QLabel('Yaw', parent=self)
        self.yaw_field = QLineEdit('0.0', parent=self)
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
        hbox_sat_position.addWidget(self.yaw_label)
        hbox_sat_position.addWidget(self.yaw_field)
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

        # Add special combo box for multigrd
        if 'law'in self._patternctlr.configure().keys():
            self.law_id_lbl = QLabel('Excitation law', parent=self)
            self.law_id_cmb = QComboBox(self)
            self.law_id_cmb.addItems(self._patternctlr.configure()['law'])
            self.law_id_cmb.setCurrentText(
                self._patternctlr.configure()['applied_law'])
            self.law_id_cmb.currentTextChanged.connect(self.cmb_law_changed)
            hbox_law = QHBoxLayout(None)
            hbox_law.addWidget(self.law_id_lbl)
            hbox_law.addWidget(self.law_id_cmb)
            vbox.addLayout(hbox_law)

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
        self.chkslope.stateChanged.connect(self.chk_display_slope_changed)
        self.chksurf = QCheckBox('Color surface', parent=self)
        optionbox = QGridLayout(None)
        optionbox.addWidget(self.chkxpol, 1, 1)
        optionbox.addWidget(self.chkslope, 1, 2)
        optionbox.addWidget(self.chksurf, 1, 3)
        vbox.addLayout(optionbox)

        # add offset sub form
        self.chk_offset = QCheckBox('Offset', parent=self)
        self.offset_button = QPushButton('Lon/Lat', parent=self)
        self.offset_button.setCheckable(True)
        self.offset_button.toggle()
        self.az_offset_label = QLabel('Az.', parent=self)
        self.az_offset_field = QLineEdit('0.0', parent=self)
        self.el_offset_label = QLabel('El.', parent=self)
        self.el_offset_field = QLineEdit('0.0', parent=self)
        self.az_offset_label.setFixedWidth(40)
        self.el_offset_label.setFixedWidth(40)
        self.az_offset_label.setAlignment(QtCore.Qt.AlignRight
                                          | QtCore.Qt.AlignVCenter)
        self.el_offset_label.setAlignment(QtCore.Qt.AlignRight
                                          | QtCore.Qt.AlignVCenter)
        self.az_offset_field.setFixedWidth(80)
        self.el_offset_field.setFixedWidth(80)
        self.az_offset_field.setAlignment(QtCore.Qt.AlignRight
                                          | QtCore.Qt.AlignVCenter)
        self.el_offset_field.setAlignment(QtCore.Qt.AlignRight
                                          | QtCore.Qt.AlignVCenter)
        # accomodate in horizontal layout
        hbox_offset = QHBoxLayout(None)
        hbox_offset.addWidget(self.chk_offset)
        hbox_offset.addWidget(self.az_offset_label)
        hbox_offset.addWidget(self.az_offset_field)
        hbox_offset.addWidget(self.el_offset_label)
        hbox_offset.addWidget(self.el_offset_field)
        hbox_offset.addStretch(1)
        hbox_offset.addWidget(self.offset_button)
        vbox.addLayout(hbox_offset)
        # link to callback
        self.chk_offset.stateChanged.connect(self.chk_offset_state_changed)
        self.chk_offset_state_changed()
        self.offset_button.clicked.connect(self.offset_button_state_changed)
        self.offset_button.setChecked(False)
        self.offset_button_state_changed()

        # add shrink sub form
        self.chkshrink = QCheckBox('Shrink', parent=self)
        self.shrink_button = QPushButton('Expand', parent=self)
        self.shrink_button.setCheckable(True)
        self.shrink_button.toggle()
        self.azshrklbl = QLabel('Az.', parent=self)
        self.azfield = QLineEdit('0.25', parent=self)
        self.elshrklbl = QLabel('El.', parent=self)
        self.elfield = QLineEdit('0.25', parent=self)
        self.azshrklbl.setFixedWidth(40)
        self.elshrklbl.setFixedWidth(40)
        self.azfield.setFixedWidth(80)
        self.elfield.setFixedWidth(80)
        self.azshrklbl.setAlignment(QtCore.Qt.AlignRight
                                    | QtCore.Qt.AlignVCenter)
        self.elshrklbl.setAlignment(QtCore.Qt.AlignRight
                                    | QtCore.Qt.AlignVCenter)
        self.azfield.setAlignment(QtCore.Qt.AlignRight
                                  | QtCore.Qt.AlignVCenter)
        self.elfield.setAlignment(QtCore.Qt.AlignRight
                                  | QtCore.Qt.AlignVCenter)
        hbox_shrink = QHBoxLayout(None)
        hbox_shrink.addWidget(self.chkshrink)
        hbox_shrink.addWidget(self.azshrklbl)
        hbox_shrink.addWidget(self.azfield)
        hbox_shrink.addWidget(self.elshrklbl)
        hbox_shrink.addWidget(self.elfield)
        hbox_shrink.addStretch(1)
        hbox_shrink.addWidget(self.shrink_button)
        self.chkshrink.stateChanged.connect(self.chkshrinkstatechanged)
        self.chkshrinkstatechanged()
        self.shrink_button.clicked.connect(self.shrink_button_state_changed)
        self.shrink_button.setChecked(False)
        self.shrink_button_state_changed()
        vbox.addLayout(hbox_shrink)

        # set fields value
        if filename:
            if type(filename) is list:
                self.filename_field.setText(filename[0])
            else:
                self.filename_field.setText(filename)
        if self.earth_plot:
            self.title_field.setText(self.earth_plot._plot_title)
            self.lon_field.setText(str(self.earth_plot._viewer.longitude()))
            self.lat_field.setText(str(self.earth_plot._viewer.latitude()))
            self.alt_field.setText(str(self.earth_plot._viewer.altitude()))
            # TODO do something for the multiple beams in one file case
            self.cf_field.setText(str(self._patternctlr._conversion_factor))

        # Add Ok/Cancel buttons
        self.lines_button = QPushButton('Lines', self)
        self.lines_button.setEnabled(False)
        apply_button = QPushButton('Apply', self)
        ok_button = QPushButton('OK', self)
        cancel_button = QPushButton('Cancel', self)

        # Place Ok/Cancel button in an horizontal box layout
        hbox2 = QHBoxLayout()
        hbox2.addStretch(1)
        hbox2.addWidget(self.lines_button)
        hbox2.addWidget(apply_button)
        hbox2.addWidget(ok_button)
        hbox2.addWidget(cancel_button)

        # put the button layout in the Vertical Layout
        vbox.addLayout(hbox2)

        # set dialog box layout
        self.setLayout(vbox)

        # connect buttons to actions
        self.lines_button.clicked.connect(self.setlines)
        apply_button.clicked.connect(self.set_pattern_conf)
        ok_button.clicked.connect(lambda: self.set_pattern_conf(close=True))
        cancel_button.clicked.connect(self.close)
        self.cf_field.textChanged.connect(self.refresh_isolevel)

        # Set default field value if pattern object has been provided
        if self._patternctlr:
            self.configure(self._patternctlr)
    # end of __init__

    def configure(self, pattern):
        """This method configure the fields of the dialog with
        the pattern configuration values.
        pattern is the antenna pattern object which provide
        the configuration for this GUI
        """
        utils.trace('in')
        try:
            self.title_field.setText(pattern._conf['title'])
        except KeyError:
            print('pattern.dialog: No title in pattern._conf dictionary.')
        self.lon_field.setText(str(pattern.satellite().longitude()))
        self.lat_field.setText(str(pattern.satellite().latitude()))
        self.alt_field.setText(str(pattern.satellite().altitude()))
        self.yaw_field.setText(
            str(pattern.set(pattern.configure(), 'sat_yaw', 0.0)))
        if pattern._display_slope:
            low = np.amin(pattern.configure()['slopes'])
            high = np.amax(pattern.configure()['slopes'])
            self.isolevel_field.setText('{},{}'.format(low, high))
        else:
            self.isolevel_field.setText(self.get_isolevel())
        self.chk_revert_x.setChecked(pattern._revert_x)
        self.chk_revert_y.setChecked(pattern._revert_y)
        self.chk_rotate.setChecked(pattern._rotated)
        self.chkxpol.setChecked(pattern._use_second_pol)
        self.chkslope.setChecked(pattern._display_slope)
        _shrink = pattern._shrink
        _expand = pattern.set(pattern.configure(), 'expand', False)
        self.chkshrink.setChecked(_shrink | _expand)
        if _shrink != _expand:
            self.shrink_button_state_changed()
        elif _shrink and _expand:
            print("Error: you cannot shrink and expand in the same time.")
        self.chk_offset.setChecked(pattern._offset)
        self.chksurf.setChecked(pattern.set(
            pattern.configure(), 'Color surface', False))
        if pattern._shrink:
            self.azfield.setText(str(pattern._azshrink))
            self.elfield.setText(str(pattern._elshrink))
        if pattern._offset:
            self.az_offset_field.setText(str(pattern._azimuth_offset))
            self.el_offset_field.setText(str(pattern._elevation_offset))
        self.offset_button.setChecked(pattern.set(pattern.configure(),
                                                  'azeloffset',
                                                  True))
        self.offset_button_state_changed()

        # disable use second pol option if second pol not available
        if len(pattern._E_cr):
            self.chkxpol.setEnabled(True)
        else:
            self.chkxpol.setEnabled(False)

        self.refresh_isolevel()
        utils.trace('out')
    # end of configure method

    def get_isolevel(self, pattern=None):
        """Return string formatted isolevel list.
        Each value separated with comma.
        pattern is the antenna pattern
        """
        if self._patternctlr is None:
            return ",".join(str(x) for x in cst.DEFAULT_ISOLEVEL_DBI)
        else:
            return ",".join(str(x) for x in self._patternctlr.get_isolevel())
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
        if self._patternctlr:
            max_co = int(np.max(self._patternctlr.copol()))
            try:
                max_cr = int(np.max(self._patternctlr.cross()))
            except TypeError:
                max_cr = 0
        else:
            max_co = 0
            max_cr = 0

        cf = self.get_cf()
        isolevel = np.array(self._patternctlr._isolevel) - \
            np.max(self._patternctlr._isolevel)
        if self.chkxpol.checkState():
            tmp_str = ",".join(str(x) for x in isolevel + max_cr + cf)
        else:
            tmp_str = ",".join(str(x) for x in isolevel + max_co + cf)

        self.isolevel_field.setText(tmp_str)
    # end of method refresh_isolevel

    def set_pattern_conf(self, close=False):
        utils.trace('in')

        # if no defined pattern attribute return
        if not self._patternctlr:
            return

        config = {}
        config['revert_x'] = self.chk_revert_x.isChecked()
        config['revert_y'] = self.chk_revert_y.isChecked()
        config['rotate'] = self.chk_rotate.isChecked()
        config['use_second_pol'] = self.chkxpol.isChecked()
        config['sat_alt'] = float(self.alt_field.text())
        config['sat_lon'] = float(self.lon_field.text())
        config['sat_lat'] = float(self.lat_field.text())
        config['sat_yaw'] = float(self.yaw_field.text())
        config['display_slope'] = self.chkslope.isChecked()
        config['shrink'] = (self.chkshrink.isChecked()
                            and not self.shrink_button.isChecked())
        config['expand'] = (self.chkshrink.isChecked()
                            and self.shrink_button.isChecked())
        if config['shrink'] or config['expand']:
            config['azshrink'] = float(self.azfield.text())
            config['elshrink'] = float(self.elfield.text())
        config['offset'] = self.chk_offset.isChecked()
        config['azeloffset'] = self.offset_button.isChecked()
        if config['offset']:
            # if offset is defined as azel
            config['azoffset'] = float(self.az_offset_field.text())
            config['eloffset'] = float(self.el_offset_field.text())

        # if multigrd pattern, apply law selected
        if 'law' in self._patternctlr.configure().keys():
            self._patternctlr.apply_law(self.law_id_cmb.currentText())

        if self.chkslope.isChecked():
            config['slopes'] = [float(s)
                                for s in self.isolevel_field.text().split(',')]
        else:
            config['isolevel'] = [float(s)
                                  for s in
                                  self.isolevel_field.text().split(',')]
        config['cf'] = float(self.cf_field.text())
        config['Color surface'] = self.chksurf.isChecked()

        self._patternctlr.configure(config=config)

        self.earth_plot.settitle(self.title_field.text())

        self._patternctlr._conversion_factor = float(self.cf_field.text())

        self.abort = False

        # update plot from GUI input
        self._control.plot()

        # ungrey Lines button
        self.lines_button.setEnabled(True)

        if close:
            self.close()
        utils.trace('out')
    # end of function set_pattern_conf

    def chkshrinkstatechanged(self):
        """Callback deactivating the shrink fields when
        shrink checkbox is unchecked.
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

    def offset_button_state_changed(self):
        if not self.offset_button.isChecked():
            self.offset_button.setText('Az/El')
            self.az_offset_label.setText('Lon')
            self.el_offset_label.setText('Lat')
        else:
            self.offset_button.setText('Lon/Lat')
            self.az_offset_label.setText('Az')
            self.el_offset_label.setText('El')

    def shrink_button_state_changed(self):
        if not self.shrink_button.isChecked():
            self.shrink_button.setText('Expand')
            self.chkshrink.setText('Shrink')
        else:
            self.shrink_button.setText('Shrink')
            self.chkshrink.setText('Expand')

    def chk_display_slope_changed(self):
        """Callback changing the range displayed in case
        the display slope option is checked.
        """
        utils.trace()
        if self.chkslope.isChecked():
            self.isolevel_field.setText('{},{}'.format(
                self._patternctlr._slope_range[0],
                self._patternctlr._slope_range[1]))
        else:
            self.isolevel_field.setText(self.get_isolevel())

    def cmb_law_changed(self):
        self._patternctlr.apply_law(self.law_id_cmb.currentText())
        self.refresh_isolevel()

    def setlines(self):
        linedlg = LineDialog(self._patternctlr)
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
