
# coding: utf-8

import os

from PyQt4 import uic
from PyQt4.QtCore import Qt, QObject, pyqtSignal
from PyQt4.QtGui import QDialog, QListWidgetItem, QPainter, QPixmap

from IBGEVisualizer.HyperResource import ITEM_LIST_TYPE_VOCAB, EXPRESSION_TYPE_VOCAB, GEOMETRY_TYPE_VOCAB, \
    FLOAT_TYPE_VOCAB, PROPERTY_VOCAB, GEOMETRY_HTTPS_TYPE_VOCAB
from IBGEVisualizer.gui.v2.components.frame_collect import FrameCollect
from IBGEVisualizer.gui.v2.components.frame_filter_expression import FrameFilterExpression
from IBGEVisualizer.gui.v2.components.frame_item_list_expression import FrameItemListExpression
from IBGEVisualizer.gui.v2.components.frame_property_list import FramePropertyList
from IBGEVisualizer.gui.v2.components.frame_geometry import FrameGeometry
from IBGEVisualizer.gui.v2.components.frame_empty_expects import FrameEmptyExpects
from IBGEVisualizer.gui.v2.components.frame_float_expects import FrameFloatExpects
from IBGEVisualizer.gui.v2.components.frame_offset_limit import FrameOffsetLimit
from IBGEVisualizer.gui import ComponentFactory
from IBGEVisualizer.model import ResourceManager

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialog_construct_url.ui'))

class DialogConstructUrl(QDialog, FORM_CLASS):
    # 1, nome da layer, 2, url da layer
    load_url_command = pyqtSignal(unicode, unicode)

    def __init__(self, resource):
        super(DialogConstructUrl, self).__init__()
        self.setupUi(self)

        self.resource = resource

        self.setWindowTitle(u'Operações da camada: ' + self.resource.name + ' - ' + self.resource.iri)

        self._on_load_commands()

        self.url_builder = UrlBuilder(self.ta_url)

        # Eventos
        self.list_attributes.itemClicked.connect(self._list_attributes_itemClicked)
        self.bt_load_url.clicked.connect(self._bt_load_url_clicked)

        self.url_builder.set_url(self.resource.iri)

    def _on_load_commands(self):
        self.create_operations_list()

    def _list_attributes_itemClicked(self, item):
        if item.type_ == 'supported_property':
            self._load_property_list_frame()

        if item.type_ == 'supported_operation':
            if len(item.property.parameters()) < 1:
                self._load_empty_expects_frame(item)

            elif item.name == 'offset-limit':
                self._load_offset_limit_frame()

            elif item.name == 'collect':
                self._load_collect_frame()

            elif EXPRESSION_TYPE_VOCAB in item.property.parameters():
                self._load_filter_expression_frame()

            elif ITEM_LIST_TYPE_VOCAB in item.property.parameters() or PROPERTY_VOCAB in item.property.parameters():
                self._load_item_list_frame()

            elif GEOMETRY_HTTPS_TYPE_VOCAB in item.property.parameters() or GEOMETRY_TYPE_VOCAB in item.property.parameters():
                self._load_geometry_frame()

            elif FLOAT_TYPE_VOCAB in item.property.parameters():
                self._load_float_frame()

        self.url_builder.set_operation(item.name)

    def _bt_load_url_clicked(self):
        url = self.ta_url.toPlainText()
        name = url.strip('/').split('/')[-1]
        self.load_url_command.emit(name, unicode(url))

    def _load_collect_frame(self):
        widget = FrameCollect(self.resource)
        self._insert_in_operations_layout(widget)
        widget.criteria_inserted.connect(lambda t: self.url_builder.append(t))

    def _load_offset_limit_frame(self):
        widget = FrameOffsetLimit()
        self._insert_in_operations_layout(widget)
        widget.criteria_inserted.connect(lambda t: self.url_builder.append(t))

    def _load_property_list_frame(self):
        property_ = self.list_attributes.currentItem().name
        widget = FramePropertyList(self.resource, property_)
        self._insert_in_operations_layout(widget)

    def _load_filter_expression_frame(self):
        widget = FrameFilterExpression(self.resource)
        self._insert_in_operations_layout(widget)
        widget.criteria_inserted.connect(lambda t: self.url_builder.append(t))

    def _load_item_list_frame(self):
        widget = FrameItemListExpression(self.resource)
        self._insert_in_operations_layout(widget)
        widget.criteria_inserted.connect(lambda t: self.url_builder.append(t))

    def _load_geometry_frame(self):
        widget = FrameGeometry()
        self._insert_in_operations_layout(widget)
        widget.criteria_inserted.connect(lambda t: self.url_builder.append(t))

    def _load_empty_expects_frame(self, item):
        url = self.resource.iri
        url = url + ('' if url.endswith('/') else '/')
        url = url + item.text()

        resource = ResourceManager.load(url)

        widget = FrameEmptyExpects(resource)
        self._insert_in_operations_layout(widget)

    def _load_float_frame(self):
        widget = FrameFloatExpects()
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

    def create_operations_list(self):
        properties = self.resource.properties()
        operations = self.resource.operations()

        if properties:
            self.generate_property_items_from_options(properties)

        if operations:
            self.generate_operation_items_from_options(operations)

    def generate_property_items_from_options(self, supported_properties):
        self._generate_items_from_options(
            ComponentFactory.create_property_list_item,
            self.list_attributes.addItem,
            supported_properties)

    def generate_operation_items_from_options(self, supported_operations):
        self._generate_items_from_options(
            ComponentFactory.create_operation_list_item,
            self.list_attributes.addItem,
            supported_operations)

    def _generate_items_from_options(self, factory_callback, add_item_callback, options_attributes=list()):
        def create_and_insert_item(attr):
            res = factory_callback(attr)
            add_item_callback(res)

        map(create_and_insert_item, options_attributes)


class UrlBuilder(QObject):
    url_updated = pyqtSignal(str)

    def __init__(self, bound_item):
        super(UrlBuilder, self).__init__()

        self.bound_item = bound_item

        self.url_updated.connect(self.bound_item.setPlainText)

        self._url = ''
        self._operation = ''

    def set_url(self, url):
        #reseting vars
        self._operation = ''

        self._url = url
        self.url_updated.emit(self.url_built())

    def url(self):
        if self._url:
            return self._url + ('' if self._url.endswith('/') else '/')

        return ''

    def set_operation(self, operation):
        self._operation = operation
        self.url_updated.emit(self.url_built())

    def operation(self):
        if self._operation:
            return self._operation + ('' if self._operation.endswith('/') else '/')

        return ''

    def append(self, text):
        old_text = self.bound_item.toPlainText()
        self.bound_item.setPlainText(old_text + text)
        self.url_updated.emit(self.url_built())

    def appendix(self):
        len1 = len(self.url())
        len2 = len(self.operation())

        whole_text = self.bound_item.toPlainText()

        return whole_text[len1+len2:]

    def url_built(self):
        appendix = self.appendix()

        if not appendix == '' and not appendix.endswith('/*') and not appendix.endswith('/'):
            appendix = appendix + '/'

        return self.url() + self.operation() + appendix

