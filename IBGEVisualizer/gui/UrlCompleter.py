# coding=utf-8

import copy, json
from urlparse import urlparse

from PyQt4.QtCore import Qt, QModelIndex, QAbstractItemModel
from PyQt4.QtGui import QCompleter, QStringListModel, QStandardItemModel, QStandardItem

from IBGEVisualizer import HyperResource


class UrlCompleter(QCompleter):
    def __init__(self):
        super(UrlCompleter, self).__init__()

        self.setCaseSensitivity(Qt.CaseInsensitive)
        #self.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.setCompletionMode(QCompleter.UnfilteredPopupCompletion)

        self.current_url = ''
        self.tree_model = APITreeModel()
        self.setModel(self.tree_model)

    def update_completer(self, text):
        if not self.splitPath(text):
            self.setCompletionPrefix('')
            return

        self.setCompletionPrefix(self.splitPath(text)[-1].strip())

        results = APIConnection.options(text)

        if results is None:
            return

        self.tree_model.setup(results)

        text_url = text if text.endswith('/') else text + '/'
        self.current_url = text_url

        self.complete()

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

    def pathFromIndex(self, index=QModelIndex()):
        if not index.isValid():
            return ''

        if index.data() is None:
            return ''

        if index.parent() is not None:
            if index.parent().data() is None:
                return unicode(index.data())

            return unicode(index.data())

        return unicode(index.data())






class StringListModel(QStringListModel):
    pass

# Modelo será atualizado quando entrar uma url válida
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

        if role not in [Qt.DisplayRole, Qt.EditRole]:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.root.data(section)

        return None

    def hasChildren(self, parent=QModelIndex()):
        return True if parent.child(0, 0) else False

    def setup(self, results):
        entry_point = results['entry_point']

        node = self.root.add_child(entry_point)

        for attr in results['attributes']:
            node.add_child(attr)



class TreeNode:
    def __init__(self, data=None, parent=None):
        self._parent = parent
        self.children = []
        self._data = None

        if data:
            self._data = data
            self._data = self.path()

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

        return self.parent().path() + self.data()

    def __str__(self):
        return '<Node: data={}, children={}>'.format(self._data, str(self.children))




class APIConnection:
    @staticmethod
    def options(url):
        if not HyperResource.url_exists(url):
            return

        options = HyperResource.request_options(url)
        body = options['body']
        header = options['header']

        link_tab = header['link']

        entry_point = APIConnection._get_entry_point_from_link(link_tab)

        try:
            json_data = json.loads(body)

            text_url = url if url.endswith('/') else url + '/'
            resources = copy.copy(json_data['@context'].keys())
            resources = [path.replace(' ', '-') for path in resources]
            resources = [path if path.endswith('/') else path + '/' for path in resources]
            #resources = [text_url + path for path in resources]

            r = {
                'entry_point': entry_point,
                'attributes': sorted(resources)
            }

        except ValueError:
            return

        return r

    @staticmethod
    def _get_entry_point_from_link(link_tab):
        import re
        entry_point = re.search('^<.+?>', link_tab).group(0).strip('<>')

        return entry_point










class CodeCompleter(QCompleter):
    ConcatenationRole = Qt.UserRole + 1

    def __init__(self, parent=None):
        super(CodeCompleter, self).__init__(parent)
        test_model_data = [
            ('tree', [  # tree
                ('branch', [  # tree.branch
                    ('leaf', [])]),  # tree.branch.leaf
                ('roots', [])]),  # tree.roots
            ('house', [  # house
                ('kitchen', []),  # house.kitchen
                ('bedroom', [])]),  # house.bedroom
            ('obj3', []),  # etc..
            ('obj4', [])
        ]
        self.create_model(test_model_data)

    def splitPath(self, path):
        splitted_path =  path.split('.')
        return splitted_path

    def pathFromIndex(self, ix):
        return ix.data(CodeCompleter.ConcatenationRole)

    def create_model(self, data):
        def addItems(parent, elements, t=""):
            for text, children in elements:
                item = QStandardItem(text)
                data = t + "." + text if t else text
                item.setData(data, CodeCompleter.ConcatenationRole)
                parent.appendRow(item)
                if children:
                    addItems(item, children, data)

        model = QStandardItemModel(self)
        addItems(model, data)
        self.setModel(model)