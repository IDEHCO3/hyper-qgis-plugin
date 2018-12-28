
# coding: utf-8

import os

from PyQt4 import uic, QtCore
from PyQt4.QtCore import Qt, QObject, pyqtSignal
from PyQt4.QtGui import QFrame, QListWidgetItem

from IBGEVisualizer import HyperResource, Utils

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_geometry.ui'))

class FrameGeometry(QFrame, FORM_CLASS):
    criteria_inserted = pyqtSignal(str)

    def __init__(self):
        super(FrameGeometry, self).__init__()
        self.setupUi(self)

        self.bt_insert.clicked.connect(self.insert_criteria)

    def insert_criteria(self):
        url = self.tx_url.toPlainText()
        url = url + ('/*' if not url.endswith('/*') else '')
        self.criteria_inserted.emit(url)
