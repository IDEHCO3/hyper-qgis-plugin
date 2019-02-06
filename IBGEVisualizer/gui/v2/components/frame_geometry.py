
# coding: utf-8

import os

from PyQt4 import uic, QtCore
from PyQt4.QtCore import Qt, QObject, pyqtSignal
from PyQt4.QtGui import QFrame, QListWidgetItem, QIcon

from IBGEVisualizer.Utils import Config
from IBGEVisualizer.gui.v2.components.resource_treewidget_decorator import ResourceTreeWidgetDecorator
from IBGEVisualizer.model import ResourceManager


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_geometry.ui'))

class FrameGeometry(QFrame, FORM_CLASS):
    criteria_inserted = pyqtSignal(str)

    def __init__(self):
        super(FrameGeometry, self).__init__()
        self.setupUi(self)

        self.bt_insert.clicked.connect(self.insert_criteria)

        self.list_resource = ResourceTreeWidgetDecorator(self.list_resource)
        self.load_resources_from_model()

        self.list_resource.itemClicked.connect(self._list_resource_clicked)

    def _list_resource_clicked(self, item):
        url = item.text(1)

        self.tx_url.setPlainText(url)

    def insert_criteria(self):
        url = self.tx_url.toPlainText()
        url = url + ('/*' if not url.endswith('/') else '')
        self.criteria_inserted.emit(url)

    def load_resources_from_model(self):
        model = Config.get('memo_urls')
        if not model:
            return

        for name, iri in model.items():
            resource = ResourceManager.load(iri, name)

            self.list_resource.add(resource)
