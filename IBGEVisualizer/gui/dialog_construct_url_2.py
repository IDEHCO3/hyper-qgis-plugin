
# coding: utf-8

import os

from PyQt4 import uic
from PyQt4.QtCore import Qt, QObject, pyqtSignal
from PyQt4.QtGui import QDialog, QListWidgetItem

from IBGEVisualizer import HyperResource, Utils
from IBGEVisualizer.gui import ComponentFactory
from IBGEVisualizer.gui.components.frame_filter_expression import FrameFilterExpression
from IBGEVisualizer.gui.components.frame_item_list_expression import FrameItemListExpression
from IBGEVisualizer.gui.components.frame_property_list import FramePropertyList

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialog_construct_url.ui'))

class DialogConstructUrl2(QDialog, FORM_CLASS):
    url_inserted = pyqtSignal(str)
    url_removed = pyqtSignal(str)
    url_selected = pyqtSignal(dict)
    attribute_selected = pyqtSignal(dict)
    load_url_command = pyqtSignal(str)

    def __init__(self):
        super(DialogConstructUrl2, self).__init__()
        self.setupUi(self)

        self.my_layers = None

        self.url_builder = UrlBuilder()
        self.memo_urls = Utils.Config.get('memo_urls') or {}

        # Sinal Inserir URL
        self.tx_url.returnPressed.connect(self._emit_url_inserted)
        self.bt_resource_insert.clicked.connect(self._emit_url_inserted)

        # Sinal Remover URL
        self.bt_resource_remove.clicked.connect(self._emit_url_removed)

        # Sinal URL selecionado
        self.list_resource.itemClicked.connect(self._emit_url_selected)

        # Sinal atributo selecionado
        self.list_attributes.itemClicked.connect(self._emit_attribute_selected)

        # Adicionando URL na lista de recursos
        self.url_inserted.connect(self._list_resource_url_inserted)

        # Removendo URL da lists de recursos
        self.url_removed.connect(self._list_resource_url_removed)

        # Quando uma url é selecionada, deve carregar o options exibir em 'list_attributes'
        self.url_selected.connect(self._list_resource_url_selected)

        # Quando um atributo é selecionado, o quadro de informações ao lado muda de acordo
        self.attribute_selected.connect(self._list_attributes_attribute_selected)

        # Quando há uma mudança na url construida é setado um novo texto
        self.url_builder.url_updated.connect(self.tx_url_builded.setPlainText)

        # Botão carregar URL
        self.bt_load_url.clicked.connect(self._emit_load_url)

        self.init_ui()

    def init_ui(self):
        # Hide headers of list_resource
        self.list_resource.setHeaderHidden(True)

        self._load_model_to_list_resource()

        self.my_layers.setExpanded(True)

    def _emit_load_url(self):
        text = self.tx_url_builded.toPlainText()
        self.load_url_command.emit(text)

    def _emit_url_inserted(self):
        url = self.tx_url.text().strip()
        self.url_inserted.emit(url)

    def _emit_url_removed(self):
        current_item = self.list_resource.currentItem()
        self.url_removed.emit(current_item.text())

    def _emit_url_selected(self, item):
        url = item.text(1)
        self.url_selected.emit({'url': url})

    def _emit_attribute_selected(self, item):
        self.attribute_selected.emit({'attribute': item})



    def _add_item_to_list_resource(self, name, url):
        item = ComponentFactory.create_list_resource_element(name, url)

        self.my_layers.addChild(item)
        self.my_layers.setExpanded(True)

    def _load_model_to_list_resource(self):
        from IBGEVisualizer.model import ListResourceModel as List

        counter = 1
        for key, values in List.model.items():
            parent_item = ComponentFactory.create_list_resource_element(key, '')

            # Pega a última layer - Minhas Camadas
            if counter == len(List.model.items()):
                self.my_layers = parent_item

            for name, url in values.items():
                item = ComponentFactory.create_list_resource_element(name, url)

                parent_item.addChild(item)

            self.list_resource.addTopLevelItem(parent_item)
            counter += 1

    def _list_resource_url_inserted(self, url):
        if not url: return
        if not HyperResource.url_exists(url):
            Utils.MessageBox.warning(u'URL não existe ou não pode ser acessada', u'Aviso')
            return

        split_url = url.split('/')
        name = split_url[-1] if split_url[-1] != '' else split_url[-2]

        # Save url in config file
        self.memo_urls.update({name: url})
        Utils.Config.set('memo_urls', self.memo_urls)

        self._add_item_to_list_resource(name, url)
        self.tx_url.clear()

    def _list_resource_url_removed(self):
        selected_item = self.list_resource.currentItem()
        name = selected_item.text(0)

        if not selected_item or name not in self.memo_urls: return

        self.memo_urls.pop(name)
        Utils.Config.set('memo_urls', self.memo_urls)

        self.list_resource.takeItem(self.list_resource.currentRow())

        self.list_attributes.clear()
        self.url_builder.set_url('')

        # Esvaziando frame_operations
        self._clear_operations_layout()

    def _list_resource_url_selected(self, info):
        url = info.get('url')

        if url in ['', None]:
            return

        self.url_builder.set_url(url)
        self.list_attributes.clear()
        self._clear_operations_layout()

        options_reply = HyperResource.request_options(url)

        response = HyperResource.translate_options(options_reply.response())

        self._generate_property_items_from_options(response.get('supported_properties'))
        self._generate_operation_items_from_options(response.get('supported_operations'))

    def _generate_property_items_from_options(self, options_properties):
        self.generate_items_from_options(
            ComponentFactory.create_property_list_item,
            self.list_attributes.addItem,
            options_properties)

    def _generate_operation_items_from_options(self, options_operations):
        self.generate_items_from_options(
            ComponentFactory.create_operation_list_item,
            self.list_attributes.addItem,
            options_operations)

    def generate_items_from_options(self, factory_callback, add_item_callback, options_attributes=list()):
        def create_and_insert_item(attr):
            res = factory_callback(attr)
            add_item_callback(res)

        map(create_and_insert_item, options_attributes)

    def _list_attributes_attribute_selected(self, list_item):
        attribute = list_item.get('attribute')

        if attribute.type_ == 'supported_property':
            self._show_property_list_frame()

        if attribute.type_ == 'supported_operation':
            if len(attribute.property.expects) == 1:
                if 'http://extension.schema.org/expression' in attribute.property.expects:
                    self._show_filter_expression_frame()

                elif 'http://schema.org/ItemList' in attribute.property.expects:
                    self._show_item_list_frame()

            self.url_builder.set_operation(attribute.property.name)

    def _clear_operations_layout(self):
        # clear frame_operations layout
        layout = self.frame_operations.layout()
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        return layout

    def _insert_in_operations_layout(self, widget):
        if not widget: return

        layout = self._clear_operations_layout()
        layout.addWidget(widget)

    def _show_property_list_frame(self):
        url = self.list_resource.currentItem().text(1)
        property_ = self.list_attributes.currentItem().name

        widget = FramePropertyList(url, property_)
        self._insert_in_operations_layout(widget)

    def _show_filter_expression_frame(self):
        url = self.list_resource.currentItem().text(1)

        widget = FrameFilterExpression(url)
        self._insert_in_operations_layout(widget)

        widget.criteria_inserted.connect(self._append_to_url)

    def _show_item_list_frame(self):
        url = self.list_resource.currentItem().text(1)

        widget = FrameItemListExpression(url)
        self._insert_in_operations_layout(widget)

        widget.criteria_inserted.connect(self._append_to_url)

    def _append_to_url(self, text):
        url = self.url_builder.url_builded()

        # tratamento de url com * no final
        if url[-1] == '*' and text[0] == '/':
            text = text[1:]

        self.url_builder.append(text)




class ListItem(QListWidgetItem):
    def __init__(self):
        super(ListItem, self).__init__()

        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsTristate)

        self._url = ''

    def setUrl(self, url):
        self._url = url
        self.setToolTip('Link: ' + url)

    def url(self):
        return self._url




class OperationListItem(QListWidgetItem):
    def __init__(self, prop_or_oper):
        super(OperationListItem, self).__init__()

        self.property = prop_or_oper
        self.type_ = 'supported_property' if type(self.property).__name__ == 'SupportedProperty' else 'supported_operation'
        self.name = self.property.name

        self.setText(self.name)

        self.setToolTip(str(self.property))




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
