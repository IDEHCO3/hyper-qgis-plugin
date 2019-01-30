
# coding: utf-8

import os

from PyQt4 import uic
from PyQt4.QtGui import QFrame
from PyQt4.QtCore import pyqtSignal


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_float_expects.ui'))

class FrameFloatExpects(QFrame, FORM_CLASS):
    criteria_inserted = pyqtSignal(unicode)

    def __init__(self):
        super(FrameFloatExpects, self).__init__()
        self.setupUi(self)

        self.bt_insert.clicked.connect(self._bt_insert_clicked)

    def _bt_insert_clicked(self):
        text = self.tx_edit.text()

        self.criteria_inserted.emit(text)