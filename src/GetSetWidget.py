
from PyQt5.QtWidgets import QDialog, QPushButton, QSizePolicy, QAction, qApp, QLineEdit, QDoubleValidator, QHBoxLayout, QVBoxLayout


class GetSetWidget(QDialog):

    def __init__(self, strLabel, strDefVal):
        # Call to generic constructor
        super().__init__()
