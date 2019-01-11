
# coding: utf-8

import os
from collections import OrderedDict

from PyQt4 import uic, QtCore
from PyQt4.QtCore import Qt, QObject, pyqtSignal
from PyQt4.QtGui import QFrame, QListWidgetItem, QIcon

from IBGEVisualizer import HyperResource, Utils
from IBGEVisualizer.gui import ComponentFactory

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_geometry.ui'))

class FrameGeometry(QFrame, FORM_CLASS):
    criteria_inserted = pyqtSignal(str)

    def __init__(self):
        super(FrameGeometry, self).__init__()
        self.setupUi(self)

        self.bt_insert.clicked.connect(self.insert_criteria)

        self.list_resource = TreeWidgetDecorator(self.list_resource)
        self.load_resources_from_model()

        self.list_resource.itemClicked.connect(self._list_resource_clicked)

    def _list_resource_clicked(self, item):
        url = item.text(1)

        self.tx_url.setPlainText(url)

    def insert_criteria(self):
        url = self.tx_url.toPlainText()
        url = url + ('/*' if not url.endswith('/*') else '')
        self.criteria_inserted.emit(url)

    def load_resources_from_model(self):
        model = Utils.Config.get('memo_urls')

        for name, values in model.items():
            self.add_resource(name, values)

    def add_resource(self, name, url=''):
        if not url: return
        if not HyperResource.url_exists(url): return

        head = HyperResource.request_head(url)

        if HyperResource.is_entry_point(head.response()):
            self.add_entry_point_to_resources(name, url)
            return

        self.add_url_to_resources(name, url)

    def add_url_to_resources(self, name, url):
        widget = ComponentFactory.create_list_resource_element(name, url)
        self.list_resource.addTopLevelItem(widget)

    def add_entry_point_to_resources(self, name, url):
        reply = HyperResource.request_get(url)
        response = reply.response()

        import json
        entry_point_list = json.loads(response.get('body'))

        # Ordena o dict pela chave.
        entry_point_list = OrderedDict(sorted(entry_point_list.items(), key=lambda t: t[0]))

        self.list_resource.append_entry_point(name, entry_point_list)



class TreeWidgetDecorator:
    def __init__(self, decorated):
        self._decorated = decorated

    def __getattr__(self, name):
        return getattr(self._decorated, name)

    def append(self, item, parent=None):
        if parent:
            parent.addChild(item)
            return

        self.addTopLevelItem(item)

    # Cria um entry point na lista de recursos
    # name: nome do entry point
    # elements: dict contendo chave:valor dos recursos do entry point
    def append_entry_point(self, name, elements):
        parent_item = ComponentFactory.create_list_resource_element(name, '')
        icon = QIcon(':/plugins/IBGEVisualizer/icon-entry-point.png')
        parent_item.setIcon(0, icon)

        for layer_name, layer_url in elements.items():
            item = ComponentFactory.create_list_resource_element(layer_name, layer_url)
            self.append(item, parent_item)

        self.append(parent_item)