
# coding: utf-8

import os, json

from PyQt4 import uic, QtCore
from PyQt4.QtCore import Qt, QObject, pyqtSignal
from PyQt4.QtGui import QFrame, QListWidgetItem

from IBGEVisualizer import HyperResource


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_item_list_expression.ui'))

class FrameItemListExpression(QFrame, FORM_CLASS):
    criteria_inserted = pyqtSignal(str)

    def __init__(self, url):
        super(FrameItemListExpression, self).__init__()
        self.setupUi(self)

        self._load_properties_from_url(url)

        self.bt_add_item.clicked.connect(self.add_item_to_selected_list)

        self.bt_insert.clicked.connect(lambda: self.criteria_inserted.emit(self.ta_selected_items.toPlainText().strip()))

    def _load_properties_from_url(self, url):
        reply = HyperResource.request_options(url)
        response = reply.response()
        translation = HyperResource.translate_options(response)

        for prop in translation.get('supported_properties'):
            item = QListWidgetItem()
            item.setText(prop.name)

            self.list_properties.addItem(item)

    def add_item_to_selected_list(self):
        selected_text = self.list_properties.currentItem().text()

        plain_text = self.ta_selected_items.toPlainText().strip()

        if not plain_text:
            self.ta_selected_items.setPlainText(selected_text)
        else:
            self.ta_selected_items.setPlainText(plain_text + ',' + selected_text)