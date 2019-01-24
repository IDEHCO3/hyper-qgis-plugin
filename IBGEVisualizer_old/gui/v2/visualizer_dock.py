
# coding: utf-8

import os

from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal, Qt, QTimer
from PyQt4.QtGui import QApplication, QDockWidget, QMenu, QAction, QIcon, QSortFilterProxyModel, QBrush, QColor

from IBGEVisualizer import HyperResource, Plugin
from IBGEVisualizer.Utils import Config, Layer, MessageBox
from IBGEVisualizer.gui.v2.components.resource_treewidget_decorator import ResourceTreeWidgetDecorator
from IBGEVisualizer.gui.v2.dialog_construct_url import DialogConstructUrl
from IBGEVisualizer.gui.v2.dialog_add_resource import DialogAddResource
from IBGEVisualizer.gui.v2.dialog_edit_resource import DialogEditResource


YELLOW = QBrush(QColor(255, 252, 226))
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'visualizer_dock.ui'))


class VisualizerDock(QDockWidget, FORM_CLASS):
    # Evento para quando o plugin é fechado
    closingPlugin = pyqtSignal()

    def __init__(self, iface):
        super(VisualizerDock, self).__init__()

        self.iface = iface
        self.request_error = False

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(7000)
        self.timer.timeout.connect(lambda: self.lb_status.setText('Pronto'))

        self.setupUi(self)

        self.list_resource = ResourceTreeWidgetDecorator(self.list_resource)

        self.load_resources_from_model()

        # Eventos
        self.bt_add_resource.clicked.connect(self._bt_add_resource_clicked)
        self.bt_remove_resource.clicked.connect(self._bt_remove_resource_clicked)

        self.list_resource.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_resource.customContextMenuRequested.connect(self.open_context_menu)
        #self.list_resource.doubleClicked.connect(self._list_resource_doubleClicked)

        #self.tx_quick_resource.returnPressed.connect(self._tx_quick_resource_pressed)

    def _tx_quick_resource_pressed(self):
        def extract_name(url):
            return url.strip(' /').split('/')[-1]

        url = self.tx_quick_resource.text()
        self.tx_quick_resource.clear()

        if url:
            name = extract_name(url)
            self.add_resource(name, url)


    def _list_resource_doubleClicked(self, index):
        if index and index.isValid():
            item = self.list_resource.itemFromIndex(index)

            name = item.text(0)
            url = item.text(1)

            item_has_children = item.childCount() > 0
            if item_has_children:
                return

            # Verifica se é um entrypoint com layers ainda não carregadas
            # url_is_entry_point = HyperResource.is_entry_point(HyperResource.request_head(url).response())
            # if url_is_entry_point:
            #     self.add_entry_point_to_resources(name, url)
            #     return

            self.open_operations_editor(name, url)

    def _bt_add_resource_clicked(self):
        self.open_add_resource_dialog()

    def _bt_remove_resource_clicked(self):
        selected_items = self.list_resource.selectedItems()

        if not selected_items:
            return

        confirm = MessageBox.question(u'Deseja realmente remover o recurso selecionado?', u'Remover Recurso')

        if confirm:
            memorized_urls = Config.get('memo_urls')

            item_name = selected_items[0].text(0)

            if item_name in memorized_urls:
                index = self.list_resource.indexOfTopLevelItem(selected_items[0])
                self.list_resource.takeTopLevelItem(index)

                memorized_urls.pop(item_name)
                Config.update_dict('memo_urls', memorized_urls)

    def load_resource(self, name, url):
        if not url: return
        if not HyperResource.url_exists(url): return

        is_entry_point = HyperResource.is_entry_point(HyperResource.request_head(url).response())
        if is_entry_point:
            parent_item = self.list_resource.add_entry_point(name, url)
            parent_item.setBackground(0, YELLOW)
        else:
            item = self.list_resource.add_url(name, url)
            item.setBackground(0, YELLOW)

    def add_resource(self, name, url):
        self.load_resource(name, url)

        Config.set('memo_urls', {name: url})

    def load_resources_from_model(self):
        model = Config.get('memo_urls')
        if not model:
            return

        for name, iri in model.items():
            self.load_resource(name, iri)


    def open_context_menu(self, position):
        item = self.list_resource.itemAt(position)
        if not item:
            return

        is_tree_leaf = item.childCount() == 0

        menu = QMenu()

        # Load layers action
        action_open_layer = QAction(self.tr(u'Carregar camada'), None)
        action_open_layer.triggered.connect(lambda: self._load_layer_from_url(item.text(0), item.text(1)))
        menu.addAction(action_open_layer) if is_tree_leaf else None

        # Load layers as...
        #action_open_layer_as = QAction(self.tr(u'Carregar camada como...'), None)
        #action_open_layer_as.triggered.connect(lambda: self._load_layer_from_url(item.text(0), item.text(1)))
        # menu.addAction(action_open_layer_as)

        menu.addSeparator()

        # Montar Operações
        action_open_editor = QAction(self.tr(u'Montar operações'), None)
        action_open_editor.triggered.connect(lambda: self.open_operations_editor(item.text(0), item.text(1)))
        menu.addAction(action_open_editor) if is_tree_leaf else None

        menu.addSeparator() if is_tree_leaf else None

        action_edit = QAction(self.tr(u'Editar'), None)
        action_edit.triggered.connect(lambda: self.open_edit_dialog(item))
        menu.addAction(action_edit)

        menu.exec_(self.list_resource.viewport().mapToGlobal(position))

    def open_edit_dialog(self, item):
        dialog_edit_resource = DialogEditResource(item)
        dialog_edit_resource.accepted.connect(self._resource_edited)
        dialog_edit_resource.exec_()

        return dialog_edit_resource

    def open_operations_editor(self, name, url):
        dialog_construct_url = DialogConstructUrl(name, url)
        dialog_construct_url.load_url_command.connect(self._load_layer_from_url)
        dialog_construct_url.exec_()

        return dialog_construct_url

    def open_add_resource_dialog(self):
        dialog_add_resource = DialogAddResource()
        dialog_add_resource.accepted.connect(self.add_resource)
        dialog_add_resource.exec_()

        return dialog_add_resource

    def _resource_edited(self, tree_item, new_name, new_url):
        memo = Config.get('memo_urls')

        old = memo.pop(tree_item.text(0))
        new = {new_name: new_url}

        memo.update(new)
        Config.update_dict('memo_urls', memo)

        tree_item.setText(0, new_name)
        tree_item.setText(1, new_url)

    def _load_layer_from_url(self, layer_name, url):
        get_reply = HyperResource.request_get(url)
        options_reply = HyperResource.request_options(url)

        self.timer.stop()
        get_reply.requestStarted.connect(self.start_request)
        get_reply.downloadProgress.connect(self.download_progress)
        get_reply.error.connect(self.show_request_error)
        get_reply.finished.connect(self.trigger_reset_status)

        response = get_reply.response()
        options_response = options_reply.response()

        if not self.request_error:
            obj = HyperResource.create_hyper_object(response, options_response, url)

            layer = Plugin.create_layer_with_hyper_object(layer_name, obj)

            if layer:
                Layer.add(layer)


    def start_request(self):
        self.request_error = False
        self.timer.stop()
        self.lb_status.setText(u'Enviando requisição e aguardando resposta...')

    def update_status(self, msg):
        self.lb_status.setText(msg)

    def download_progress(self, received, total):
        if not self.request_error:
            if received == total:
                msg = u'Concluído ' + received
            else:
                msg = u'Baixando recurso... ' + received + (' / ' + total if total != '-1.0' else '')

            self.update_status(msg)

    def trigger_reset_status(self):
        if not self.request_error:
            self.timer.start()

    def show_request_error(self, error):
        self.request_error = True
        self.update_status(u'Requisição retornou um erro')
        MessageBox.critical(error, u'Requisição retornou um erro')


    def close_event(self, event):
        self.closingPlugin.emit()
        event.accept()

    def run(self):
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self)

        self.show()



from PyQt4.QtCore import QObject, QModelIndex
from PyQt4.QtGui import QStandardItemModel

class ResourceTreeModel(QStandardItemModel):
    def __init__(self):
        super(ResourceTreeModel, self).__init__()

        memo = Config.get('memo_urls')
        self._data = memo

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = index.data()
        column = index.column()

        return item.data().name if column == 0 else index.data().url

    def hasChildren(self, parent=QModelIndex()):
        if not parent.isValid(): return False

        item = parent.data()
        if len(item.children) > 0: return True

        url = item.url
        if not url: return False
        if not HyperResource.url_exists(url): return False

        head = HyperResource.request_head(url)
        return HyperResource.is_entry_point(head.response())

    def get_row(self, pos):
        return self._data[pos]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return 2

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        if role == Qt.EditRole:
            row_index = index.row()

            row = self._data[row_index]

            row.set(index.column(), value)

            self.dataChanged.emit(index, index)
            return True

        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled

        return Qt.ItemIsEnabled


class TreeItem(QObject):
    def __init__(self, name, url='', parent=None):
        self._parent = parent
        self.name = name
        self.url = url
        self.children = []

    def add_child(self, item):
        self.children.append(item)

    def get_child(self, index_num):
        return self.children[index_num]

    def is_entry_point(self):
        if not self.url: return False
        if not HyperResource.url_exists(self.url): return False

        head = HyperResource.request_head(self.url)

        return HyperResource.is_entry_point(head.response())

    def parent(self):
        return self._parent



class FilterTreeModel(QSortFilterProxyModel):
    pass