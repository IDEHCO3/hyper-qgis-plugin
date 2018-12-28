
# coding: utf-8

import os, json

from PyQt4 import uic

from IBGEVisualizer import Utils, HyperResource

from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QDialog, QCheckBox, QListWidgetItem


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialog_open_entry_point.ui'))

class DialogOpenEntryPoint(QDialog, FORM_CLASS):
    layers_selected = pyqtSignal(list)

    def __init__(self):
        super(DialogOpenEntryPoint, self).__init__()
        self.setupUi(self)

        self.loaded_layer_items  = []

        self.setWindowModality(Qt.ApplicationModal)

        self.buttonBox.accepted.connect(self.__emit_layers_selected)

    def set_layers_from_url(self, url):
        self.list_layers.clear()
        self.loaded_layer_items = []

        try:
            get_reply = HyperResource.request_get(url)
            response = get_reply.response()

            data = json.loads(response.get('body'))

            for k in sorted(data, key=data.__getitem__):
                item = self.create_list_item(k, data.get(k))

                self.list_layers.addItem(item)
                self.loaded_layer_items.append(item)

        except:
            raise

    def create_list_item(self, name, link):
        if not name or not link:
            return

        item = ListItem()
        item.setText(name)
        item.setLink(link)

        return item

    def __emit_layers_selected(self):
        selected_items = [item for item in self.loaded_layer_items if item.checkState() == Qt.Checked]

        self.layers_selected.emit(selected_items)



class ListItem(QListWidgetItem):
    def __init__(self):
        super(ListItem, self).__init__()

        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsTristate)
        self.setCheckState(Qt.Unchecked)

        self.link = ''

    def setLink(self, link):
        self.link = link

    def link(self):
        return self.link
