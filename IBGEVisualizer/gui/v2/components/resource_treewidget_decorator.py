
# coding: utf-8

# Decorator class for Pyqt4.QtGui.QTreeWidget
# Component in visualizer_docker
from PyQt4.QtCore import pyqtSignal, QObject

from collections import OrderedDict

from IBGEVisualizer.Utils import MessageBox
from IBGEVisualizer.gui import ComponentFactory
from IBGEVisualizer.model import ResourceManager


class ResourceTreeWidgetDecorator(QObject):
    branch_resource_double_clicked = pyqtSignal(object)
    leaf_resource_double_clicked = pyqtSignal(object)

    def __init__(self, decorated):
        super(ResourceTreeWidgetDecorator, self).__init__()

        self._decorated = decorated

        self.itemDoubleClicked.connect(self._itemDoubleClicked_event)

    def __getattr__(self, name):
        return getattr(self._decorated, name)

    def _itemDoubleClicked_event(self, item):
        iri = item.text(1)

        item_has_children = item.childCount() > 0
        if item_has_children:
            return

        resource = ResourceManager.load(iri)
        if resource.error:
            MessageBox.critical(u'Link está indisponível ou fora do ar.\n {}'.format(resource.iri), u'Link indisponível')
            return

        # Verifica se é um entrypoint com layers ainda não carregadas
        if resource.is_entry_point():
            item.set_icon_entry_point()
            self.add(resource, item)
            self.branch_resource_double_clicked.emit(item)
            return

        self.leaf_resource_double_clicked.emit(item)


    def add(self, resource, parent_item=None):
        if resource.is_entry_point():
            item = self._add_entry_point(resource, parent_item)

        else:
            item = self._add_simple_resource(resource, parent_item)

        if resource.error:
            item.set_icon_error()

        return item

    def _add_simple_resource(self, resource, parent_item=None):
        widget = ComponentFactory.create_list_resource_element(resource)
        return self._append(widget, parent_item)

    def _add_entry_point(self, resource, parent_item=None):
        entry_point_list = resource.as_json()

        order_alphabetically = lambda i: sorted(i, key=lambda t: t[0])
        entry_point_list = OrderedDict(order_alphabetically(entry_point_list.items()))

        return self._append_entry_point(resource, entry_point_list, parent_item)

    def _append(self, item, parent=None):
        if parent:
            parent.addChild(item)
            return parent

        self.addTopLevelItem(item)
        return item

    # Cria um entry point na lista de recursos
    # name: nome do entry point
    # elements: dict contendo chave:valor dos recursos do entry point
    def _append_entry_point(self, resource, entry_point_elements, parent_item=None):
        create_item = ComponentFactory.create_list_resource_element

        parent_item = parent_item or create_item(resource)
        parent_item.set_icon_entry_point()

        for name, url in entry_point_elements.items():
            new_res = ResourceManager.load(url, name)
            item = create_item(new_res)

            self._append(item, parent_item)

        self._append(parent_item)
        return parent_item
