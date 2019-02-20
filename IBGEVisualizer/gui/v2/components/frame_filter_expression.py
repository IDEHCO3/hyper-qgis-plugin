
# coding: utf-8

import os, json

from PyQt4 import uic, QtCore
from PyQt4.QtCore import Qt, QObject, pyqtSignal
from PyQt4.QtGui import QFrame, QListWidgetItem

from IBGEVisualizer import HyperResource
from IBGEVisualizer.model import ResourceManager

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_filter_expression.ui'))

class FrameFilterExpression(QFrame, FORM_CLASS):
    criteria_inserted = pyqtSignal(str)

    def __init__(self, resource):
        super(FrameFilterExpression, self).__init__()
        self.setupUi(self)

        self.resource = resource

        self.tab_values.setCurrentIndex(0)
        self.tab_values.currentChanged.connect(lambda n: self._on_tab_change(n))

        self.preview_builder = FilterPreviewBuilder()
        self.preview_builder.preview_changed.connect(self.preview_changed)

        self.property_selected = ''
        self.operator_selected = ''

        self.cb_filter_property.currentIndexChanged.connect(self._cb_property_changed)

        self.bt_insert_criteria.clicked.connect(self._emit_insert_criteria)
        self.bt_or.clicked.connect(lambda: self._emit_insert_logical_or_and('/or/'))
        self.bt_and.clicked.connect(lambda: self._emit_insert_logical_or_and('/and/'))

        ####
        # tab Valor
        ####
        # Mudar preview ao selecionar operador
        self.bt_number_eq.clicked.connect(lambda x: self._set_preview_operator('='))
        self.bt_number_neq.clicked.connect(lambda x: self._set_preview_operator('!='))
        self.bt_number_lt.clicked.connect(lambda x: self._set_preview_operator('<'))
        self.bt_number_gt.clicked.connect(lambda x: self._set_preview_operator('>'))
        self.bt_number_lte.clicked.connect(lambda x: self._set_preview_operator('<='))
        self.bt_number_gte.clicked.connect(lambda x: self._set_preview_operator('>='))

        self.tabValue_bt_insert.clicked.connect(self._tabValue_value_inserted)
        self.tabValue_list_values.itemSelectionChanged.connect(self._tabValue_list_values_selection_changed)

        ####
        # tab Lista de Valores
        ####
        self.tabListValue_bt_in.clicked.connect(lambda x: self._set_preview_operator('in'))
        #self.tabListValue_bt_not_in.clicked.connect(lambda x: self._set_preview_operator('not/in'))

        self.tabListValue_bt_insert.clicked.connect(self._tabListValue_value_inserted)
        self.tabListValue_list_values.itemSelectionChanged.connect(self._tabListValue_list_values_selection_changed)

        ####
        # tb Data
        ####
        # self.tabDate_bt_eq.clicked.connect(lambda x: self._set_preview_operator('='))
        # self.tabDate_bt_neq.clicked.connect(lambda x: self._set_preview_operator('!='))
        # self.tabDate_bt_lt.clicked.connect(lambda x: self._set_preview_operator('<'))
        # self.tabDate_bt_gt.clicked.connect(lambda x: self._set_preview_operator('>'))
        # self.tabDate_bt_lte.clicked.connect(lambda x: self._set_preview_operator('<='))
        # self.tabDate_bt_gte.clicked.connect(lambda x: self._set_preview_operator('>='))
        # self.tabDate_bt_between.clicked.connect(lambda x: self._set_preview_operator('between'))

        ####
        # tab URL
        ####
        self.tabUrl_list_operations.itemSelectionChanged.connect(self._tabUrl_list_operations_selected_changed)
        self.tabUrl_tx_url.textChanged.connect(self._tabUrl_tx_url_text_changed)
        self.tabUrl_tx_url.setAcceptDrops(True)

        self._fill_cb_filter_property(resource)

    def _on_tab_change(self, index):
        switch = {
            0: self._tabValue_setup,
            1: self.bla,
            2: self._tabListValue_setup,
            3: self._tabUrl_setup,
        }

        # executing
        callback = switch.get(index)
        callback()

    def _tabValue_setup(self):
        self.tabValue_list_values.clear()
        self.tabValue_tx_insert_value.clear()

        prop = self.property_selected

        if prop == 'geom':
            return

        property_list = self._get_property(self.resource, prop)

        for elem in property_list:
            k, v = elem.items()[0]

            item = QListWidgetItem()
            item.setText(unicode(v))

            self.tabValue_list_values.addItem(item)

    def _tabListValue_setup(self):
        self.tabListValue_list_values.clear()
        self.tabListValue_tx_value.clear()

        prop = self.property_selected

        if prop == 'geom':
            return

        property_list = self._get_property(self.resource, prop)

        for elem in property_list:
            k, v = elem.items()[0]

            item = QListWidgetItem()
            item.setText(unicode(v))

            self.tabListValue_list_values.addItem(item)

    def _tabUrl_setup(self):
        self.tabUrl_list_operations.clear()

        # TODO Aqui operations deveria ser as operações do atributo selecionado e não da coleção, mas não há acesso facilitado a isso
        operations = self.resource.operations()

        for elem in operations:
            item = OperationListItem(elem)

            self.tabUrl_list_operations.addItem(item)

    def _cb_property_changed(self, index):
        # Mudar preview ao selecionar novo item na combo box property
        self._set_preview_property(index)

        # e mudar a aba atual
        self._current_tab_property_changed(index)

    def _get_property(self, resource, prop):
        url = resource.iri
        url = url + ('' if url.endswith('/') else '/')
        projection_url = u'{url}projection/{prop}/offset-limit/1&200'.format(url=url, prop=prop)

        resource = ResourceManager.load(projection_url)

        return sorted(resource.as_json())

    def _current_tab_property_changed(self, index):
        prop = self.property_selected

        property_list = self._get_property(self.resource, prop)

        current_tab = self.tab_values.currentIndex()

        # tab Valor
        if current_tab == 0:
            self.tabValue_list_values.clear()
            self.tabValue_tx_insert_value.clear()

            if prop == 'geom':
                return

            for elem in property_list:
                k, v = elem.items()[0]

                item = QListWidgetItem()
                item.setText(unicode(v))

                self.tabValue_list_values.addItem(item)

        # tab Lista de Valores
        elif current_tab == 2:
            self.tabListValue_list_values.clear()
            self.tabListValue_tx_value.clear()

            if prop == 'geom':
                return

            for elem in property_list:
                k, v = elem.items()[0]

                item = QListWidgetItem()
                item.setText(unicode(v))

                self.tabListValue_list_values.addItem(item)

        # tab URL
        elif current_tab == 3:
            self._tabUrl_setup()


    def _tabValue_list_values_selection_changed(self):
        current_selected = self.tabValue_list_values.currentItem()
        self.tabValue_tx_insert_value.setText(current_selected.text())

    def _tabValue_value_inserted(self):
        value_inserted = self.tabValue_tx_insert_value.text()
        self.preview_builder.set_value(value_inserted)

    def _tabListValue_list_values_selection_changed(self):
        current_selected = self.tabListValue_list_values.currentItem()
        self.tabListValue_tx_value.setText(current_selected.text())

    def _tabListValue_value_inserted(self):
        value_inserted = self.tabListValue_tx_value.text()
        self.preview_builder.append_value(value_inserted)

    def _tabUrl_list_operations_selected_changed(self):
        current_selected = self.tabUrl_list_operations.currentItem()
        self.preview_builder.set_operator(current_selected.text())

    def _tabUrl_tx_url_text_changed(self):
        text = self.tabUrl_tx_url.toPlainText()
        self.preview_builder.set_value(text)


    def _set_preview_property(self, index):
        property_ = self.cb_filter_property.itemText(index)
        self.property_selected = property_
        self.preview_builder.set_property(property_)

    def _set_preview_operator(self, operator):
        self.preview_builder.set_operator(operator)
        self.operator_selected = operator

    def preview_changed(self, preview):
        self.lb_criteria_preview.setText(preview)

    def _fill_cb_filter_property(self, resource):
        items = sorted([elem.name for elem in (resource.properties() or [])])

        self.cb_filter_property.addItems(items)

    def reset_filter_operation(self):
        self.tabUrl_tx_url.clear()
        self.tabListValue_tx_value.clear()
        self.tabValue_tx_insert_value.clear()

        self.tab_values.setCurrentIndex(0)
        self.preview_builder.reset()
        self.cb_filter_property.setCurrentIndex(0)

    def _emit_insert_criteria(self):
        preview = self.preview_builder.preview()

        # Retira barra ('/') do final, se houver, ao inserir um critério
        preview = preview[:-1] if preview.endswith('/') else preview
        if self.tab_values.currentIndex() == 4:     # tab URL
            preview = preview + '/*'

        self.reset_filter_operation()

        self.criteria_inserted.emit(preview)

    def _emit_insert_logical_or_and(self, or_and):
        self.reset_filter_operation()

        self.criteria_inserted.emit(or_and)



class FilterPreviewBuilder(QObject):
    preview_changed = pyqtSignal(str)

    LIST_SEPARATOR = '&'

    def __init__(self):
        super(FilterPreviewBuilder, self).__init__()

        self._property = ''
        self._operator = ''
        self._value = ''

        self._reset()

    # Este método emite o sinal preview_changed ao ser chamado
    def reset(self):
        self._reset()
        self.preview_changed.emit(self.preview())

    # Este método não emite sinal ao resetar as variáveis
    def _reset(self):
        self._property = '<property>'
        self._operator = '<operator>'
        self._value = '<value>'

    def set_property(self, prop):
        self._reset()
        self._property = unicode(prop)
        self.preview_changed.emit(self.preview())

    def property(self):
        return unicode(self._property)

    def set_operator(self, oper):
        switch = {
            '=': 'eq',
            '!=': 'neq',
            '<': 'lt',
            '>': 'gt',
            '<=': 'lte',
            '>=': 'gte'
        }

        self._operator = switch.get(oper) or unicode(oper)
        self.preview_changed.emit(self.preview())

    def operator(self):
        return unicode(self._operator)

    def set_value(self, value):
        self._value = unicode(value)
        self.preview_changed.emit(self.preview())

    def value(self):
        return unicode(self._value)

    def append_value(self, value):
        if self.value() in ['', '<value>']:
            self.set_value(value)

        else:
            self.set_value(self.value() + self.LIST_SEPARATOR + value)

    def preview(self):
        return u'{property}/{operator}/{value}'.format(
            property=self.property(),
            operator=self.operator(),
            value=self.value()
        )


class OperationListItem(QListWidgetItem):
    def __init__(self, prop_or_oper):
        super(OperationListItem, self).__init__()

        self.property = prop_or_oper
        self.type_ = 'supported_property' if type(self.property).__name__ == 'SupportedProperty' else 'supported_operation'
        self.name = self.property.name

        self.setText(self.name)

        self.setToolTip(str(self.property))