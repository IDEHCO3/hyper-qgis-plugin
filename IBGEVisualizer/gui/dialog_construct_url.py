
# coding: utf-8

import os

from PyQt4 import uic

from PyQt4.QtCore import Qt, pyqtSignal, QObject
from PyQt4.QtGui import QDialog, QListWidgetItem, QBrush, QColor, QMenu, QAction

from IBGEVisualizer import Utils, HyperResource


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialog_construct_url.ui'))

class DialogConstructUrl(QDialog, FORM_CLASS):
    resource_added = pyqtSignal(str)
    resource_removed = pyqtSignal()

    url_selected = pyqtSignal(str)
    attribute_selected = pyqtSignal(str)

    def __init__(self):
        super(DialogConstructUrl, self).__init__()
        self.setupUi(self)

        self.url_builder = UrlBuilder()
        self.loaded_resource_item = None

        # variável para guardar itens selecionados pelo usuário na interface
        self.selected_attributes = {}

        self.tx_url.returnPressed.connect(self._emit_layer_added)
        self.bt_add_url.clicked.connect(self._emit_layer_added)

        self.resource_added.connect(self._command_add_layer)

        self.list_resources.itemClicked.connect(self._load_resource_options)
        self.list_properties.itemClicked.connect(self._load_operation_window)

        self.url_selected.connect(self.url_builder.set_base_url)
        self.attribute_selected.connect(self.url_builder.set_operation)
        self.url_builder.base_url_changed.connect(self.tx_url_constructed.setText)

    def _emit_layer_added(self):
        self.resource_added.emit(self.tx_url.text().strip())

    def _command_add_layer(self, url):
        #todo considerar links repetidos
        item = ListItem()
        item.setText(url)
        item.setUrl(url)

        self.list_resources.addItem(item)

    def clear_layout(self, layout):
        # This clears the layout of a groupOperations
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

    def change_operations_frame(self, frame):
        layout = self.groupOperations.layout()
        self.clear_layout(layout)

        layout.addWidget(frame)

    def _load_resource_options(self, resource):
        # Controle para múltiplos cliques em um mesmo item, evita repetidas requisições ao link
        if resource == self.loaded_resource_item:
            return

        self.loaded_resource_item = resource
        self.selected_attributes.update(url=resource.url())
        self.url_selected.emit(resource.url())

        self.list_properties.clear()

        options_reply = HyperResource.request_options(resource.url())

        response = HyperResource.translate_options(options_reply.response())

        for element in (response.get('supported_properties') or []):
            resource = OperationListItem(element)
            resource.setBackground(QBrush(QColor(255, 237, 248)))
            self.list_properties.addItem(resource)

        for element in (response.get('supported_operations') or []):
            resource = OperationListItem(element)
            resource.setBackground(QBrush(QColor(255, 252, 226)))
            self.list_properties.addItem(resource)

    def _load_operation_window(self, item):
        self.selected_attributes.update(property=item.property)
        self.attribute_selected.emit(item.property.name)

        if item.type_ == 'supported_property':
            self._load_frame_property_sample(item.property)

        elif item.type_ == 'supported_operation':
            expects = item.property.expects

            if 'http://extension.schema.org/expression' in expects:
                self._load_frame_filter(item.property)

    def _load_frame_property_sample(self, property):
        from IBGEVisualizer.gui.components.frame_property_sample import FramePropertySample

        frame = FramePropertySample()
        frame.set_setup_info(**self.selected_attributes)

        self.change_operations_frame(frame)

    def _load_frame_filter(self, property):
        from IBGEVisualizer.gui.components.frame_filter_operation import FrameFilterOperation

        frame = FrameFilterOperation()
        frame.set_setup_info(**self.selected_attributes)

        self.change_operations_frame(frame)



class ListItem(QListWidgetItem):
    def __init__(self):
        super(ListItem, self).__init__()

        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsTristate)
        self.setCheckState(Qt.Unchecked)

        self._url = ''

    def setUrl(self, url):
        self._url = url
        self.setToolTip(url)

    def url(self):
        return self._url


class OperationListItem(QListWidgetItem):
    def __init__(self, prop_or_oper):
        super(OperationListItem, self).__init__()

        self.property = prop_or_oper
        self.type_ = 'supported_property' if type(self.property).__name__ == 'SupportedProperty' else 'supported_operation'

        self.setText(self.property.name)

        self.setToolTip(str(self.property))


class UrlBuilder(QObject):
    base_url_changed = pyqtSignal(str)

    def __init__(self):
        super(UrlBuilder, self).__init__()

        self._base_url = ''
        self._operation = ''

        self._url_builded = ''

    def set_base_url(self, url):
        self._base_url = url
        self._operation = ''
        self.base_url_changed.emit(self.url_builded())

    def base_url(self):
        if self._base_url:
            return self._base_url + ('' if self._base_url.endswith('/') else '/')

        return ''

    def set_operation(self, operation):
        self._operation = operation
        self.base_url_changed.emit(self.url_builded())

    def operation(self):
        if self._operation:
            return self._operation + ('' if self._operation.endswith('/') else '/')

        return ''

    def url_builded(self):
        return self.base_url() + self.operation()
