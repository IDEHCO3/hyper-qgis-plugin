
# -*- coding: utf-8 -*-

from __future__ import with_statement

import os

from qgis.core import QgsMapLayerRegistry, QgsVectorLayer, QgsVectorJoinInfo

from IBGEVisualizer import Utils

from PyQt4 import uic
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QFrame, QCheckBox, QListWidgetItem


class FrameJoinAttributes:
    def __init__(self):
        self.view = FrameJoinAttributesView()
        self.view.bt_connect_attributes.clicked.connect(self._clicked_bt_connect_attributes)

    def show(self):
        self.view.show()

    def hide(self):
        self.view.hide()

    # Events
    def _clicked_bt_connect_attributes(self):
        first_layer, second_layer = (self.view.first_layer, self.view.second_layer)
        selected_field = (self.view.selected_first_field, self.view.selected_second_field)

        if first_layer is None or second_layer is None or \
            first_layer.name() == '' or second_layer.name() == '':
            Utils.info_message('Alguma camada não foi selecionada')
            return

        if selected_field[0] is None or selected_field[1] is None:
            Utils.info_message('Algum campo para união não foi selecionado')
            return

        # Get checked fields in list_fields element
        list_fields = self.view.list_fields
        checked_fields = []
        for index in range(list_fields.count()):
            item = list_fields.item(index)
            if item.checkState() == Qt.Checked:
                checked_fields.append(item.text())

        if not len(checked_fields):
            Utils.info_message('Marque algum campo na lista para haver união')
            return

        join_object = QgsVectorJoinInfo()
        join_object.joinLayerId = second_layer.id()
        join_object.joinFieldName = selected_field[1]
        join_object.targetFieldName = selected_field[0]
        join_object.memoryCache = True
        join_object.setJoinFieldNamesSubset(checked_fields)

        if first_layer.addJoin(join_object):
            self.hide()


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'join_attributes_frame.ui'))


class FrameJoinAttributesView(QFrame, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FrameJoinAttributesView, self).__init__(parent)

        self.current_layers = []
        self.first_layer = None
        self.second_layer = None

        self.selected_first_field = None
        self.selected_second_field = None

        self.setupUi(self)

        # Connect Signals
        self.cb_first_layer.currentIndexChanged.connect(self._index_changed_first_layer)
        self.cb_second_layer.currentIndexChanged.connect(self._index_changed_second_layer)

        self.list_first_layer.currentRowChanged.connect(self._item_changed_list_first_layer)
        self.list_second_layer.currentRowChanged.connect(self._item_changed_list_second_layer)

        self.cb_second_layer.currentIndexChanged.connect(self._refresh_list_fields)

    def refresh_combobox_layers(self):
        layers = QgsMapLayerRegistry.instance().mapLayers()
        self.current_layers = [QgsVectorLayer()] + [instance for _, instance in layers.items()]

        self.cb_first_layer.clear()
        self.cb_second_layer.clear()

        self.cb_first_layer.addItems([layer.name() for layer in self.current_layers])
        self.cb_second_layer.addItems([layer.name() for layer in self.current_layers])

    def show(self):
        super(FrameJoinAttributesView, self).show()
        self.refresh_combobox_layers()

    # GUI Events
    def _update_list_widget(self, widget, cb_index):
        layer = self.current_layers[cb_index]

        if layer:
            widget.clear()

            fields = layer.fields()
            name_fields = [field.name() for field in fields]

            widget.addItems(name_fields)

    def _index_changed_first_layer(self, index):
        self.first_layer = self.current_layers[index]
        self._update_list_widget(self.list_first_layer, index)

    def _index_changed_second_layer(self, index):
        self.second_layer = self.current_layers[index]
        self._update_list_widget(self.list_second_layer, index)

    def _item_changed_list_first_layer(self, index):
        item = self.list_first_layer.item(index)
        self.selected_first_field = item.text() if item else ''

    def _item_changed_list_second_layer(self, index):
        item = self.list_second_layer.item(index)
        self.selected_second_field = item.text() if item else ''

    def _refresh_list_fields(self, index):
        self.list_fields.clear()

        if index == 0:
            return

        fields = self.second_layer.fields()
        name_fields = [field.name() for field in fields]

        for name in name_fields:
            item = QListWidgetItem()
            item.setText(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)

            self.list_fields.addItem(item)
