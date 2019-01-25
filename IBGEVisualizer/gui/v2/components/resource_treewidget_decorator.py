
# coding: utf-8

# Decorator class for Pyqt4.QtGui.QTreeWidget
# Component in visualizer_docker
import json
from collections import OrderedDict

from PyQt4.QtGui import QIcon
from IBGEVisualizer import HyperResource
from IBGEVisualizer.gui import ComponentFactory
from IBGEVisualizer.model import ResourceManager


class ResourceTreeWidgetDecorator:
    def __init__(self, decorated):
        self._decorated = decorated

        # Events
        self.itemDoubleClicked.connect(self._on_itemDoubleClicked)

    def __getattr__(self, name):
        return getattr(self._decorated, name)

    def _on_itemDoubleClicked(self, item, column_index):
        # if not item:
        #     return
        #
        # iri = item.text(1)
        # resource = ResourceManager.load(iri)
        #
        # item_is_leaf_node = item.childCount() <= 0
        # if item_is_leaf_node:
        #     if resource.is_entry_point():
        #         self.load_entry_point_children(item)
        #         return
            return

    def load_entry_point_children(self, item):
        pass

    def add(self, resource, parent_item=None):
        if resource.is_entry_point():
            item = self._add_entry_point(resource, parent_item)

        else:
            item = self._add_simple_resource(resource, parent_item)

        return item

    def _add_simple_resource(self, resource, parent_item=None):
        widget = ComponentFactory.create_list_resource_element(resource.name, resource.iri)
        return self._append(widget, parent_item)

    def _add_entry_point(self, resource, parent_item=None):
        entry_point_list = json.loads(resource.data())

        order_alphabetically = lambda i: sorted(i, key=lambda t: t[0])
        entry_point_list = OrderedDict(order_alphabetically(entry_point_list.items()))

        # For the next level, mark what is entry point

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

        parent_item = parent_item or create_item(resource.name, resource.iri)
        parent_item.mark_as_entry_point()

        for name, url in entry_point_elements.items():
            item = create_item(name, url)

            # if HyperResource.is_entry_point(HyperResource.HEAD(url).response()):
            #     item.mark_as_entry_point()

            self._append(item, parent_item)

        self._append(parent_item)
        return parent_item
