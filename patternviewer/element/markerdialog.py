"""This module implement a dialog widget to deal with marker configuration.
"""

# Import third party modules
import sys

# PyQt5 widgets import
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, \
    QAction, qApp, QDialog, QLineEdit, QHBoxLayout, QVBoxLayout, \
    QPushButton, QWidget, QFileDialog, QLabel, QGridLayout, \
    QCheckBox, QComboBox, QColorDialog
from PyQt5.QtGui import QColor, QPalette

# Import local modules
import patternviewer.utils as utils
# import project constant
import patternviewer.constant as cst


class MarkerDialog(QDialog):
    """This class implement a dialog widget to deal with marker configuration.
    """

    def __init__(self, parent=None):
        """Constructor of the class MarkerDialog.
        parent is to line object to be configured using this dialog box
        """
        super().__init__()

        # parent is the object or list of object to modify
        self._parent = parent

        # dictionary containing the configuration of
        # the object to be configured
        self._config = {}

        self.initwidget()
    # end of constructor

    def initwidget(self):
        """Initialise GUI.
        """
        # get parent config
        config = self._parent.configure(None)

        # create this widget layout
        widget_layout = QVBoxLayout(self)
        layout = QGridLayout()
        widget_layout.addLayout(layout)
        # add markers parameters gui elements
        # style
        type_lbl = QLabel(self)
        type_lbl.setText('Marker type')
        layout.addWidget(type_lbl, 1, 1)
        self.type_cmb = QComboBox(self)
        self.type_cmb.addItems(
            ['.', ',', 'o', 'v', '^', '<', '>', '1', '2', '3', '4', '8', 's',
             'p', 'P', '*', 'h', 'H', '+', 'x', 'X', 'D', 'd', '|', '_'])
        try:
            marker = config['marker']
        except KeyError:
            marker = '.'
        self.type_cmb.setCurrentText(marker)
        layout.addWidget(self.type_cmb, 1, 2)

        # marker size
        size_lbl = QLabel(self)
        size_lbl.setText('Marker size')
        layout.addWidget(size_lbl, 2, 1)
        self.size_fld = QLineEdit(parent=self)
        try:
            size = config['marker size']
        except KeyError:
            size = 1
        self.size_fld.setText(str(int(size)))
        layout.addWidget(self.size_fld, 2, 2)

        # marker color
        self.color_btn = QPushButton('Marker color', self)
        self.color_btn.clicked.connect(self.pick_marker_color)
        try:
            self.marker_color = config['marker color']
        except KeyError:
            self.marker_color = 'black'
        layout.addWidget(self.color_btn, 3, 1)
        self.color_lbl = QLabel(self)
        self.color_lbl.setFixedWidth(self.color_lbl.height())
        self.color_lbl.setStyleSheet(
            'background-color: ' + self.marker_color)
        layout.addWidget(self.color_lbl, 3, 2)

        # line style
        linestyle_lbl = QLabel(self)
        linestyle_lbl.setText('linestyle')
        layout.addWidget(linestyle_lbl, 4, 1)
        self.linestyle_cmb = QComboBox(self)
        self.linestyle_cmb.addItems(['solid', 'dashed', 'dashdot', 'dotted',
                                     '-', '--', '-.', ':'])
        try:
            linestyle = config['linestyle']
        except KeyError:
            linestyle = 'solid'
        self.linestyle_cmb.setCurrentText(linestyle)
        layout.addWidget(self.linestyle_cmb, 4, 2)

        # line boldness
        linewidth_lbl = QLabel(self)
        linewidth_lbl.setText('linewidth')
        layout.addWidget(linewidth_lbl, 5, 1)
        self.linewidth_cmb = QComboBox(self)
        self.linewidth_cmb.addItems(['no line', 'light',
                                     'medium', 'heavy'])
        try:
            linewidth = config['linewidth']
        except KeyError:
            linewidth = 'light'
        self.linewidth_cmb.setCurrentText(cst.getboldness(linewidth))
        layout.addWidget(self.linewidth_cmb, 5, 2)

        # line color
        self.line_color_btn = QPushButton('Line color', self)
        self.line_color_btn.clicked.connect(self.pick_line_color)
        try:
            self.line_color = config['linecolor']
        except KeyError:
            self.line_color = 'black'
        self.line_color_lbl = QLabel(self)
        self.line_color_lbl.setFixedWidth(self.line_color_lbl.height())
        self.line_color_lbl.setStyleSheet(
            'background-color:' + self.line_color)
        layout.addWidget(self.line_color_btn, 6, 1)
        layout.addWidget(self.line_color_lbl, 6, 2)

        # Font
        self.fontsize_lbl = QLabel('Font size')
        self.fontsize_fld = QLineEdit()
        try:
            fontsize = int(config['fontsize'])
        except KeyError:
            fontsize = 3
        self.fontsize_fld.setText('{size:d}'.format(size=fontsize))
        layout.addWidget(self.fontsize_lbl, 7, 1)
        layout.addWidget(self.fontsize_fld, 7, 2)

        # add Apply/Ok/Cancel buttons
        buttonlayout = QHBoxLayout()
        applybutton = QPushButton('Apply', self)
        okbutton = QPushButton('Ok', self)
        cancelbutton = QPushButton('Cancel', self)
        buttonlayout.addStretch(1)
        buttonlayout.addWidget(applybutton)
        buttonlayout.addWidget(okbutton)
        buttonlayout.addWidget(cancelbutton)
        widget_layout.addLayout(buttonlayout)

        # connect buttons to action
        applybutton.clicked.connect(self.config)
        okbutton.clicked.connect(self.configandclose)
        cancelbutton.clicked.connect(self.close)

    # end of method initGUI

    def config(self):
        """Collect value from widget and configure parent with
        the collected values.
        """
        # dictionary used to collect parameters
        conf = {}

        # get linewidth
        conf['marker'] = self.type_cmb.currentText()
        conf['marker size'] = int(float(self.size_fld.text()))
        conf['marker color'] = self.marker_color
        conf['linestyle'] = self.linestyle_cmb.currentText()
        conf['linewidth'] = cst.BOLDNESS[self.linewidth_cmb.currentText()]
        conf['linecolor'] = self.line_color
        conf['fontsize'] = int(float(self.fontsize_fld.text()))
        # call to parent configure method and redraw
        self._parent.configure(config=conf)
        self._parent.clearplot()
        self._parent.plot()
        self._parent._parent.draw()
    # end of method config

    def configandclose(self):
        """Configure parent and close the widget.
        """
        self.config()
        self.close()
    # end of method configandclose

    def pick_line_color(self):
        self.line_color = QColorDialog.getColor().name()
        self.line_color_lbl.setStyleSheet(
            'background-color:' + self.line_color)

    def pick_marker_color(self):
        self.marker_color = QColorDialog.getColor().name()
        self.color_lbl.setStyleSheet(
            'background-color:' + self.marker_color)

# Getters and Setters

    def parent(self):
        """Return this instance parent object.
        """
        return self._parent
    # end of function parent


# end of class LineDialog

# Main execution
if __name__ == '__main__':
    # Create main window
    MAIN_WINDOW = QApplication(sys.argv)
    APP = MarkerDialog()

    # Start main loop
    sys.exit(MAIN_WINDOW.exec_())

# end of module linedialog
