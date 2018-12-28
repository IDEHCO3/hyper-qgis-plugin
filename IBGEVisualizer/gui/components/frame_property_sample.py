
# coding: utf-8

import os, json

from PyQt4 import uic
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QListWidgetItem

from IBGEVisualizer import HyperResource
from IBGEVisualizer.gui.components.frame_base import FrameBase


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_property_sample.ui'))

class FramePropertySample(FrameBase, FORM_CLASS):
    def __init__(self, parent=None):
        super(FramePropertySample, self).__init__(parent)
        self.setupUi(self)

        self.setup_info_setted.connect(self._fill_list_sample)

    def _fill_list_sample(self, setup_info):
        self.list_sample.clear()

        if not setup_info or setup_info is None: return

        url = setup_info.get('url')
        property_name = setup_info.get('property').name
        projection_url = url + ('' if url.endswith('/') else '/') + 'offset_limit/1&100/' + property_name

        # Se geom for selecionado, não fazer a requisição
        if property_name == 'geom':
            return

        reply = HyperResource.request_get(projection_url)
        response = reply.response()

        dic = json.loads(response.get('body'))

        for element in dic:
            k, v = element.items()[0]

            item = ListItem()
            item.setText(unicode(v))
            item.setUrl(projection_url)

            self.list_sample.addItem(item)





class ListItem(QListWidgetItem):
    def __init__(self):
        super(ListItem, self).__init__()

        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)

        self._url = ''

    def setUrl(self, url):
        self._url = url

    def url(self):
        return self._url
