
# coding: utf-8

import os, json

from PyQt4 import uic, QtCore
from PyQt4.QtGui import QFrame, QListWidgetItem

from IBGEVisualizer.model import ResourceManager
from IBGEVisualizer.HyperResource import FEATURE_COLLECTION_TYPE_VOCAB, COLLECTION_TYPE_VOCAB

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_property_list.ui'))

class FramePropertyList(QFrame, FORM_CLASS):
    def __init__(self, resource, property_):
        super(FramePropertyList, self).__init__()
        self.setupUi(self)

        self.resource = resource
        self._property = property_

        self.bt_reload.clicked.connect(lambda: self._request_list())

        self._request_list()

        self._lb_property_loaded()

    def _lb_property_loaded(self):
        at_id = self.resource.property(self._property).at_id
        at_type = self.resource.property(self._property).at_type

        switch = {
            unicode: u'Text',
            int: u'Número Inteiro',
            float: u'Número Real',
            'geometria': u'Geometria'
        }

        self.lb_property.setText(
            (u'@id: {id}\n'
            u'Propriedade: {prop}\n'
            u'Tipo: {type}')
        .format(
            prop=self._property,
            type=switch.get(at_type) or unicode(at_type),
            id=at_id
        ))

    def _request_list(self):
        prop = self._property

        # Não abrir geom na lista
        if prop == 'geom':
            return

        lower = self.tx_offset_1.text()
        upper = self.tx_offset_2.text()

        dic = self.request_sample(lower, upper)

        if isinstance(dic, list):
            # filtro para elementos vazios
            filtered_dict = [elem for elem in dic if elem.values()[0] not in [None, 'None']]
        elif isinstance(dic, dict):
            filtered_dict = [dic]
        else:
            filtered_dict = []

        self.load_sample(filtered_dict)

    def request_sample(self, lower, upper):
        url = self.resource.iri
        url = url + ('' if url.endswith('/') else '/')

        if self.resource.at_type() in [FEATURE_COLLECTION_TYPE_VOCAB, COLLECTION_TYPE_VOCAB]:
            projection_url = u'{url}projection/{prop}/offset-limit/{lower}&{upper}'\
                .format(url=url, prop=self._property,
                        lower=lower, upper=upper)
        else:
            # It not a Collection so offset-limit will not work
            projection_url = u'{url}projection/{prop}'.format(url=url, prop=self._property)

        resource = ResourceManager.load(projection_url)

        return resource.as_json()

    def load_sample(self, sample):
        self.list_attribute.clear()

        for element in sample:
            k, v = element.items()[0]

            item = QListWidgetItem()
            item.setText(unicode(v))

            self.list_attribute.addItem(item)
