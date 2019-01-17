
# coding: utf-8

# Decorator class for Pyqt4.QtGui.QTreeWidget
# Component in visualizer_docker
from collections import OrderedDict

from PyQt4.QtGui import QIcon
from IBGEVisualizer import HyperResource
from IBGEVisualizer.gui import ComponentFactory

class ResourceTreeWidgetDecorator:
    def __init__(self, decorated):
        self._decorated = decorated

    def __getattr__(self, name):
        return getattr(self._decorated, name)

    def add_url(self, name, url):
        widget = ComponentFactory.create_list_resource_element(name, url)
        return self.append(widget)

    def add_entry_point(self, name, url):
        reply = HyperResource.request_get(url)
        response = reply.response()

        import json
        entry_point_list = json.loads(response.get('body'))

        order_alphabetically = lambda i: sorted(i, key=lambda t: t[0])
        entry_point_list = OrderedDict(order_alphabetically(entry_point_list.items()))

        return self.append_entry_point(name, url, entry_point_list)

    def append(self, item, parent=None):
        if parent:
            parent.addChild(item)
            return parent

        self.addTopLevelItem(item)
        return item

    # Cria um entry point na lista de recursos
    # name: nome do entry point
    # elements: dict contendo chave:valor dos recursos do entry point
    def append_entry_point(self, name, url, entry_point_elements):
        create_item = ComponentFactory.create_list_resource_element

        parent_item = create_item(name, url)
        entry_point_icon = QIcon(':/plugins/IBGEVisualizer/icon-entry-point.png')
        parent_item.setIcon(0, entry_point_icon)

        for name, url in entry_point_elements.items():
            item = create_item(name, url)
            self.append(item, parent_item)

        self.append(parent_item)
        return parent_item
