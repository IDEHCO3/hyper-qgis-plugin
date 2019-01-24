
# coding: utf-8

import os, json

from PyQt4 import uic, QtCore
from PyQt4.QtCore import QObject
from PyQt4.QtGui import QFrame, QListWidgetItem

from IBGEVisualizer import HyperResource


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_property_list.ui'))

class FramePropertyList(QFrame, FORM_CLASS):
    def __init__(self, url, property_):
        super(FramePropertyList, self).__init__()
        self.setupUi(self)

        self.bt_reload.clicked.connect(lambda: self.reload_sample_ui(url, property_))

        self._request_list(url, property_)

        self._lb_property_loaded(url, property_)

    def _lb_property_loaded(self, url, property_):
        url = url + ('' if url.endswith('/') else '/')
        projection_url = u'{url}{prop}'.format(url=url, prop=property_)

        reply = HyperResource.request_options(projection_url)
        tr = HyperResource.translate_options(reply.response())
        id_ = tr.get('fields').get(property_).get('@id')
        type_ = tr.get('fields').get(property_).get('@type')

        switch = {
            unicode: u'Text',
            int: u'Número Inteiro',
            float: u'Número Real',
            'geometria': u'Geometria'
        }

        self.lb_property.setText(
        u'''@id: {id}
Propriedade: {prop}
Tipo: {type_}
        '''.format(
            prop=property_,
            type_=switch.get(type_) or unicode(type_),
            id=id_
        ))

    def reload_sample_ui(self, url, prop):
        self._request_list(url, prop)

    def _request_list(self, url, prop):
        # Não abrir geom na lista
        if prop == 'geom':
            return

        param1 = self.tx_offset_1.text()
        param2 = self.tx_offset_2.text()

        dic = self.request_sample(url, prop, param1, param2)

        # filtro para elementos vazios
        filtered_dict = filter(lambda e: (e.values()[0] not in [None, 'None']), dic)

        self.load_sample(filtered_dict)

    def request_sample(self, url, property_, param1, param2):
        url = url + ('' if url.endswith('/') else '/')
        projection_url = u'{url}projection/{prop}/offset-limit/{param1}&{param2}'.format(
            url=url,
            prop=property_,
            param1=param1,
            param2=param2
        )

        reply = HyperResource.request_get(projection_url)
        response = reply.response()
        return json.loads(response.get('body'))

    def load_sample(self, sample):
        self.list_attribute.clear()

        for element in sample:
            k, v = element.items()[0]

            item = QListWidgetItem()
            item.setText(unicode(v))

            self.list_attribute.addItem(item)
