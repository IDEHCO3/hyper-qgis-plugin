
# coding: utf-8

import os

from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QDialog


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialog_edit_resource.ui'))

class DialogEditResource(QDialog, FORM_CLASS):
    accepted = pyqtSignal(object, unicode, unicode)

    def __init__(self, tree_item):
        super(DialogEditResource, self).__init__()
        self.setupUi(self)

        self.tree_item = tree_item

        self.tx_name.setText(tree_item.text(0))
        self.tx_url.setText(tree_item.text(1))

        self.tx_name.setFocus()

        self.bt_ok.clicked.connect(self._emit_accepted)
        self.bt_cancel.clicked.connect(lambda: self.close())

    def _emit_accepted(self):
        url = self.tx_url.text()
        name = self.tx_name.text()

        self.accepted.emit(self.tree_item, name, url)
        self.close()