
# coding: utf-8

import os, json, copy

from urlparse import urlparse

from PyQt4 import uic
from PyQt4.QtCore import Qt, QModelIndex, QAbstractItemModel
from PyQt4.QtGui import QCompleter, QStringListModel, QDialog, QBrush, QColor

from IBGEVisualizer import HyperResource

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'dialog_tree_test.ui'))


class DialogTreeTest(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(DialogTreeTest, self).__init__(parent)
        self.setupUi(self)

        self.model = APITreeModel()
        self.tree_view.setModel(self.model)

        self.txt_metadata.setReadOnly(True)

        self.txt_url.textChanged.connect(self.refresh)

        self.tree_view.setAnimated(True)
        self.tree_view.selectionModel().selectionChanged.connect(self._change_metadata)
        self.tree_view.doubleClicked.connect(self.load_element)

    def refresh(self, text):
        if not HyperResource.url_exists(text):
            return

        reply = HyperResource.request_options(text)
        options = reply.response()

        results = HyperResource.translate_options(options, text)

        if results is None:
            return

        self.model.setup(results)
        self.model.layoutChanged.emit()

    def load_element(self, index):
        node = index.internalPointer()
        if node and not node.children:
            url = index.internalPointer().path()

            self.refresh(url)

    # Override
    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter]:
            index = self.tree_view.selectedIndexes()[0]
            node = index.internalPointer()

            path = node.path() if node.path().endswith('/') else node.path() + '/'
            self.tree_view.setExpanded(index, True)
            self.txt_url.setText(path)

    def _change_metadata(self, selected, deselected):
        index = selected.indexes()[0]
        self.txt_metadata.setText(u'')

        html = index.internalPointer().data().html_formatted()
        self.txt_metadata.setText( html )


class APITreeModel(QAbstractItemModel):
    def __init__(self):
        super(APITreeModel, self).__init__()

        self.root = TreeNode()

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item = self.root if not parent.isValid() else parent.internalPointer()
        child_item = parent_item.child(row)

        if child_item:
            return self.createIndex(row, column, child_item)

        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.root:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self.root

        else:
            parent_item = parent.internalPointer()

        return parent_item.children_count()

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()

        return self.root.columnCount()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        node = index.internalPointer()

        if role in [Qt.BackgroundRole]:
            if isinstance(node.data(), HyperResource.SupportedProperty):
                return QBrush(QColor(255, 228, 196, 100))

            if isinstance(node.data(), HyperResource.SupportedOperation):
                return QBrush(QColor(247, 236, 180, 150))

        if role not in [Qt.DisplayRole, Qt.EditRole]:
            return None

        return node.data(index.column()).name


    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.root.data(section)

        return None

    # def hasChildren(self, parent=QModelIndex()):
    #     node = parent.internalPointer()
    #     if node and len(node.children) <= 0:
    #         print('Calling...')
    #         return True
    #     return False

    def splitPath(self, path):
        parse = urlparse(path)
        path = parse.path[1:]

        if parse.scheme and parse.netloc:
            p1 = parse.scheme + '://' + parse.netloc + '/api/bcim'
            p2 = path.replace('api/bcim', '')

            path_splitted = [item for item in p2.split('/') if item]

            full_split = [p1] + path_splitted

            return full_split

        return []

    def setup(self, results):
        url = results['url']

        # adding entry_point as start point
        # Faking SupportedProperty obj
        entry_point = HyperResource.SupportedProperty(name=results['entry_point'])
        self.root.add_child(entry_point)

        splitted = self.splitPath(url)

        self.add_attr(splitted, 0, self.root, results)

    # Recursive method
    def add_attr(self, splitted, i, node, results):
        # Caso 'splitted' acabe, adicionar properties e operations ao nó
        if i >= len(splitted):
            add_group_of_child = lambda g: map(node.add_child, g)

            if results['supported_properties']:
                add_group_of_child(results['supported_properties'])
            if results['supported_operations']:
                add_group_of_child(results['supported_operations'])

            return

        index, child = -1, None
        for j, child in enumerate(node.children):
            if splitted[i] == child.data().name:
                index = j
                break

        if index > -1:
            self.add_attr(splitted, i+1, node.children[index], results)
        else:
            fake_prop = HyperResource.SupportedProperty(name=splitted[i]+'/')
            new_node = node.add_child(fake_prop)
            self.add_attr(splitted, i+1, new_node, results)



class TreeNode:
    def __init__(self, data=None, parent=None):
        self._parent = parent
        self.children = []
        self._data = data

    def add_child(self, item):
        for node in self.children:
            if node.data() == item:
                return node

        new_node = TreeNode(item, self)
        self.children.append(new_node)

        return new_node

    def remove_child(self, index):
        del self.children[index]

    def parent(self):
        return self._parent

    def child(self, index):
        if isinstance(index, QModelIndex):
            return self.children[index.row()]

        if isinstance(index, int):
            return self.children[index]

    def children_count(self):
        return len(self.children)

    def data(self, column=1):
        return self._data

    def row(self):
        if self._parent:
            return self._parent.children.index(self)

        return 0

    def columnCount(self):
        return 1

    def path(self):
        if not self.parent():
            return ''

        data = self.data()

        return self.parent().path() + (data.name if data.name.endswith('/') else data.name + '/')

    def __str__(self):
        return '<Node: data={}, children={}>'.format(self.data(), str(self.children))
