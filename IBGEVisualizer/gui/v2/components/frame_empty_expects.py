
# coding: utf-8

import os

from PyQt4 import uic, QtCore
from PyQt4.QtCore import Qt, QObject, pyqtSignal
from PyQt4.QtGui import QFrame


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_empty_expects.ui'))

class FrameEmptyExpects(QFrame, FORM_CLASS):
    criteria_inserted = pyqtSignal(str)

    def __init__(self, resource):
        super(FrameEmptyExpects, self).__init__()
        self.setupUi(self)

        self.ta_content.setPlainText(resource.as_text())
