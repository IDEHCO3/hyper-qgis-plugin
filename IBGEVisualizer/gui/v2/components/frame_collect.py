
# coding: utf-8

import os

from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QFrame

from IBGEVisualizer.gui import ComponentFactory

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'frame_collect.ui'))


class FrameCollect(QFrame, FORM_CLASS):
    criteria_inserted = pyqtSignal(unicode)

    def __init__(self, resource):
        super(FrameCollect, self).__init__()
        self.setupUi(self)

        self.resource = resource

        self.selected_property = None
        self.selected_operation = None

        self._load_properties(resource)

        self.list_properties.itemClicked.connect(self._item_list_properties_clicked)
        self.list_operations.itemClicked.connect(self._item_list_operations_clicked)
        self.bt_insert.clicked.connect(self._bt_insert_clicked)

    def _load_properties(self, resource):
        properties = resource.properties()

        for property_ in properties:
            component = ComponentFactory.create_property_list_item(property_)
            self.list_properties.addItem(component)

    def _item_list_properties_clicked(self, item):
        self.selected_property = item
        self._fill_list_operations(item.property)

    def _item_list_operations_clicked(self, item):
        self.selected_operation = item
        self._change_description(item)
        self._update_lb_expression()

    def _bt_insert_clicked(self):
        self.criteria_inserted.emit(self.lb_expression.text())

    def _fill_list_operations(self, property_):
        self.list_operations.clear()
        operations = property_.operations()

        if operations:
            for operation in operations:
                item = ComponentFactory.create_operation_list_item(operation)
                text = item.text().lower()
                item.setText(text)

                self.list_operations.addItem(item)
        else:
            item = ComponentFactory.create_dummy_list_item(u'Sem operações')
            self.list_operations.addItem(item)

    def _change_description(self, item):
        operation = item.property

        description_text = u'' \
                           u'<b>Operação</b>: {oper}<br>' \
                           u'<b>Descrição</b>: {desc}<br>' \
                           u'<b>Parâmetros</b>: <b>{param}</b><br>' \
                           u'<b>Retorno</b>: {ret}<br>' \
                           u'<b>Exemplo</b>: {example}<br>' \
            .format(
                oper=operation.name,
                desc=operation.definition,
                param=operation.parameters,
                ret=operation.return_field,
                example=operation.example
            )
        self.lb_description.setText(description_text)

    def _update_lb_expression(self):
        if not self.selected_property:
            return

        prop_name = self.selected_property.name
        oper_name = self.selected_operation.property.name.lower()
        text = prop_name + '/' + oper_name
        self.lb_expression.setText(text)