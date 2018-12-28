
#coding: utf-8

import os

from PyQt4 import uic
from PyQt4.QtGui import QDialog
from PyQt4.QtCore import pyqtSignal


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialog_add_resource.ui'))

class DialogAddResource(QDialog, FORM_CLASS):
    accepted = pyqtSignal(unicode, unicode)

    def __init__(self):
        super(DialogAddResource, self).__init__()
        self.setupUi(self)

        self.tx_name.setFocus()

        self.bt_ok.clicked.connect(self._emit_accepted)
        self.bt_cancel.clicked.connect(lambda: self.close())

    def _emit_accepted(self):
        url = self.tx_url.text()
        name = self.tx_name.text()

        self.accepted.emit(name, url)
        self.close()
