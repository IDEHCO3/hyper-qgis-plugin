
# coding: utf-8

import os, json

from PyQt4 import uic, QtCore
from PyQt4.QtCore import Qt, QObject, pyqtSignal
from PyQt4.QtGui import QFrame

from IBGEVisualizer import HyperResource


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_empty_expects.ui'))

class FrameEmptyExpects(QFrame, FORM_CLASS):
    criteria_inserted = pyqtSignal(str)

    def __init__(self, url):
        super(FrameEmptyExpects, self).__init__()
        self.setupUi(self)

        reply = HyperResource.request_get(url)
        response = reply.response()

        self.lb_content.setText(response.get('body'))
