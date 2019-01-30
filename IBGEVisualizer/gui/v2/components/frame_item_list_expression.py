
# coding: utf-8

import os

from PyQt4 import uic, QtCore
from PyQt4.QtCore import Qt, QObject, pyqtSignal
from PyQt4.QtGui import QFrame, QListWidgetItem


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_item_list_expression.ui'))

class FrameItemListExpression(QFrame, FORM_CLASS):
    criteria_inserted = pyqtSignal(unicode)

    def __init__(self, resource):
        super(FrameItemListExpression, self).__init__()
        self.setupUi(self)

        self.resource = resource

        self._load_properties(resource)

        self.bt_add_item.clicked.connect(self.add_item_to_selected_list)

        self.bt_insert.clicked.connect(lambda: self.criteria_inserted.emit(self.ta_selected_items.toPlainText().strip()))

    def _load_properties(self, resource):
        for prop in resource.properties():
            item = QListWidgetItem()
            item.setText(prop.name)

            self.list_properties.addItem(item)

    def add_item_to_selected_list(self):
        selected_text = self.list_properties.currentItem().text()

        plain_text = self.ta_selected_items.toPlainText().strip()

        if not plain_text:
            text = selected_text
        else:
            text = plain_text + ',' + selected_text

            self.ta_selected_items.setPlainText(text)