
# coding: utf-8

import os, json

from PyQt4 import uic, QtCore
from PyQt4.QtCore import Qt, QObject, pyqtSignal
from PyQt4.QtGui import QFrame, QListWidgetItem

from IBGEVisualizer import HyperResource


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_property_list.ui'))

class FramePropertyList(QFrame, FORM_CLASS):
    def __init__(self, url, property):
        super(FramePropertyList, self).__init__()
        self.setupUi(self)

        self._request_list(url, property)

    def _request_list(self, url, prop):
        # Não abrir geom na lista
        if prop == 'geom':
            return

        url = url + ('' if url.endswith('/') else '/')
        projection_url =  u'{url}/projection/{prop}/offset-limit/1/200'.format(url=url, prop=prop)

        reply = HyperResource.request_get(projection_url)
        response = reply.response()

        dic = json.loads(response.get('body'))

        # filtro para elementos vazios
        proc_dict = filter(lambda e: (e.values()[0] not in [None, 'None']), dic)

        for element in proc_dict:
            k, v = element.items()[0]

            item = QListWidgetItem()
            item.setText(unicode(v))

            self.list_attribute.addItem(item)