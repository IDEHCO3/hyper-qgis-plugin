
# coding: utf-8

import os

from PyQt4 import uic
from PyQt4.QtCore import Qt, QObject, pyqtSignal
from PyQt4.QtGui import QDialog, QListWidgetItem, QPainter, QPixmap

from IBGEVisualizer import HyperResource, Utils
from IBGEVisualizer.gui.v2.components.frame_filter_expression import FrameFilterExpression
from IBGEVisualizer.gui.v2.components.frame_item_list_expression import FrameItemListExpression
from IBGEVisualizer.gui.v2.components.frame_property_list import FramePropertyList
from IBGEVisualizer.gui.v2.components.frame_geometry import FrameGeometry
from IBGEVisualizer.gui import ComponentFactory

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialog_construct_url.ui'))

class DialogConstructUrl(QDialog, FORM_CLASS):
    # 1, nome da layer, 2, url da layer
    load_url_command = pyqtSignal(unicode, unicode)

    def __init__(self, resource_name, resource_url):
        super(DialogConstructUrl, self).__init__()
        self.setupUi(self)

        self.resource_name = resource_name
        self.resource_url = resource_url

        self.setWindowTitle(u'Operações da camada: ' + self.resource_name + ' - ' + self.resource_url)

        operations = self.read_operations_from_url(self.resource_url)
        self.create_operations_list(operations)

        self.url_builder = UrlBuilder()

        # Eventos
        self.url_builder.url_updated.connect(self.ta_url.setPlainText)
        self.list_attributes.itemClicked.connect(self._list_attributes_itemClicked)
        self.bt_load_url.clicked.connect(self._bt_load_url_clicked)

        self.url_builder.set_url(self.resource_url)

    def _list_attributes_itemClicked(self, item):
        if item.type_ == 'supported_property':
            self._load_property_list_frame()

        if item.type_ == 'supported_operation':
            if len(item.property.expects) < 1:
                return

            if 'http://extension.schema.org/expression' in item.property.expects:
                self._load_filter_expression_frame()

            elif 'http://schema.org/ItemList' in item.property.expects:
                self._load_item_list_frame()

            elif 'http://geojson.org/geojson-ld/vocab.html#geometry' in item.property.expects:
                self._load_geometry_frame()

        self.url_builder.set_operation(item.name)

    def _bt_load_url_clicked(self):
        url = self.ta_url.toPlainText()
        name = url.strip('/').split('/')[-1]
        self.load_url_command.emit(name, unicode(url))
        self.close()


    def _load_property_list_frame(self):
        property_ = self.list_attributes.currentItem().name
        widget = FramePropertyList(self.resource_url, property_)
        self._insert_in_operations_layout(widget)

    def _load_filter_expression_frame(self):
        widget = FrameFilterExpression(self.resource_url)
        self._insert_in_operations_layout(widget)
        widget.criteria_inserted.connect(lambda t: self.url_builder.append(t))

    def _load_item_list_frame(self):
        widget = FrameItemListExpression(self.resource_url)
        self._insert_in_operations_layout(widget)

    def _load_geometry_frame(self):
        widget = FrameGeometry()
        self._insert_in_operations_layout(widget)
        widget.criteria_inserted.connect(lambda t: self.url_builder.append(t))

    def _insert_in_operations_layout(self, widget):
        if not widget: return

        layout = self._clear_operations_layout()
        layout.addWidget(widget)

    def _clear_operations_layout(self):
        # clear frame_operations layout
        layout = self.frame_operations.layout()
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        return layout

    def read_operations_from_url(self, url):
        if not url:
            return

        exists, resp = HyperResource.url_exists(url)
        if not exists:
            Utils.Logging.info(
                u''
                u'''Não foi possível localizar url: {}
                {}
                '''
            .format(
                self.resource_url, resp
            ), 'IBGEVisualizer')
            Utils.MessageBox.info(u'Não foi possível localizar url: {}'.format(self.resource_url), 'IBGEVisualizer')
            return

        reply = HyperResource.request_options(url)
        options_response = reply.response()

        return HyperResource.translate_options(options_response)

    def create_operations_list(self, operations):
        if not operations:
            return      # ERRO

        supported_properties = operations.get('supported_properties')
        supported_operations = operations.get('supported_operations')

        if supported_properties:
            self.generate_property_items_from_options(supported_properties)

        if supported_operations:
            self.generate_operation_items_from_options(supported_operations)


    def generate_property_items_from_options(self, options_properties):
        self._generate_items_from_options(
            ComponentFactory.create_property_list_item,
            self.list_attributes.addItem,
            options_properties)

    def generate_operation_items_from_options(self, options_operations):
        self._generate_items_from_options(
            ComponentFactory.create_operation_list_item,
            self.list_attributes.addItem,
            options_operations)

    def _generate_items_from_options(self, factory_callback, add_item_callback, options_attributes=list()):
        def create_and_insert_item(attr):
            res = factory_callback(attr)
            add_item_callback(res)

        map(create_and_insert_item, options_attributes)



class UrlBuilder(QObject):
    url_updated = pyqtSignal(str)

    def __init__(self):
        super(UrlBuilder, self).__init__()

        self._url = ''
        self._operation = ''
        self._appendix = ''

    def set_url(self, url):
        #reseting vars
        self._operation = ''

        self._url = url
        self.url_updated.emit(self.url_builded())

    def url(self):
        if self._url:
            return self._url + ('' if self._url.endswith('/') else '/')

        return ''

    def set_operation(self, operation):
        self._operation = operation
        self.url_updated.emit(self.url_builded())

    def operation(self):
        if self._operation:
            return self._operation + ('' if self._operation.endswith('/') else '/')

        return ''

    def append(self, text):
        self._appendix = self._appendix + text
        self.url_updated.emit(self.url_builded())

    def appendix(self):
        return self._appendix

    def url_builded(self):
        return self.url() + self.operation() + self.appendix()
