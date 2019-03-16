"""This module implement a dialog widget to deal with line configuration.
"""

# Import third party modules
import sys

# PyQt5 widgets import
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QAction, qApp, QDialog, QLineEdit, \
                            QHBoxLayout, QVBoxLayout, QPushButton, QWidget, QFileDialog, QLabel, \
                            QGridLayout, QCheckBox
from PyQt5.QtGui import QColor, QPalette

# Import local modules
import utils

class LineDialog(QDialog):
    """This class implement a dialog widget to deal with line configuration.
    """

    def __init__(self, parent=None):
        """Constructor of the class LineDialog.
        parent is to line object to be configured using this dialog box
        """
        super().__init__(parent)

        # parent is the object or list of object to modify
        self._parent = parent

        # dictionary containing the configuration of the object to be configured  
        self._config = {}

    # end of constructor


# Getters and Setters

    def get_parent(self):
        """Return this instance parent object.
        """
        return self._parent
    # end of function parent


# end of class LineDialog

# Main execution
if __name__ == '__main__':
    # Create main window
    MAIN_WINDOW = QApplication(sys.argv)
    APP = LineDialog()

    # Start main loop
    sys.exit(MAIN_WINDOW.exec_())

# end of module linedialog
