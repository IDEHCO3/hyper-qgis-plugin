
# coding: utf-8

import os
from collections import OrderedDict

from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal, Qt, QTimer
from PyQt4.QtGui import QApplication, QDockWidget, QMenu, QAction, QIcon, QSortFilterProxyModel

from IBGEVisualizer import Utils, HyperResource, Plugin
from IBGEVisualizer.gui.v2.dialog_construct_url import DialogConstructUrl
from IBGEVisualizer.gui.v2.dialog_add_resource import DialogAddResource
from IBGEVisualizer.gui import ComponentFactory


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

        self.list_resource = TreeWidgetDecorator(self.list_resource)

        # Carrega a lista de recurso padrão da classe IBGEVisualizer.model.ListResourceModel
        self.load_resources_from_model()
        #self.list_resource.setModel(ResourceTreeModel())
        # Eventos
        self.bt_add_resource.clicked.connect(self._bt_add_resource_clicked_open)

        self.list_resource.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_resource.customContextMenuRequested.connect(self.openContextMenu)
        self.list_resource.doubleClicked.connect(self._list_resource_doubleClicked)

        self.tx_quick_resource.returnPressed.connect(self._tx_quick_resource_pressed)

    def _tx_quick_resource_pressed(self):
        def extract_name(url):
            return url.strip(" /").split('/')[-1]

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

            if item.childCount() > 0:
                return

            # Verifica se é um entrypoint com layers ainda não carregadas
            if HyperResource.is_entry_point(HyperResource.request_head(url).response()):
                self.add_entry_point_to_resources(name, url)
                return

            self.open_operations_editor(name, url)

    def _bt_add_resource_clicked_open(self):
        self.open_add_resource_dialog()

    def add_resource(self, name, url=''):
        if not url: return
        if not HyperResource.url_exists(url): return

        head = HyperResource.request_head(url)

        if HyperResource.is_entry_point(head.response()):
            self.add_entry_point_to_resources(name, url)
            return

        self.add_url_to_resources(name, url)

    def add_url_to_resources(self, name, url):
        widget = ComponentFactory.create_list_resource_element(name, url)
        self.list_resource.addTopLevelItem(widget)

    def add_entry_point_to_resources(self, name, url):
        reply = HyperResource.request_get(url)
        response = reply.response()

        import json
        entry_point_list = json.loads(response.get('body'))

        # Ordena o dict pela chave.
        entry_point_list = OrderedDict(sorted(entry_point_list.items(), key=lambda t: t[0]))

        self.list_resource.append_entry_point(name, entry_point_list)


    def load_resources_from_model(self):
        model = Utils.Config.get('memo_urls')

        for name, values in model.items():
            self.add_resource(name, values)


    def openContextMenu(self, position):
        item = self.list_resource.itemAt(position)

        if item and item.childCount() > 0:
            return

        action_open_layer = QAction(self.tr(u'Carregar camada'), None)
        action_open_layer.triggered.connect(lambda: self._load_layer_from_url(item.text(0), item.text(1)))

        action_open_layer_as = QAction(self.tr(u'Carregar camada como...'), None)
        action_open_layer_as.triggered.connect(lambda: self._load_layer_from_url(item.text(0), item.text(1)))

        action_open_editor = QAction(self.tr(u'Executar operações'), None)
        action_open_editor.triggered.connect(lambda: self.open_operations_editor(item.text(0), item.text(1)))

        action_rename = QAction(self.tr(u'Renomear'), None)

        menu = QMenu()
        menu.addAction(action_open_layer)
        menu.addAction(action_open_layer_as)
        menu.addSeparator()
        menu.addAction(action_open_editor)
        menu.addSeparator()
        menu.addAction(action_rename)

        menu.exec_(self.list_resource.viewport().mapToGlobal(position))

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
                Utils.Layer.add(layer)


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
        Utils.MessageBox.critical(error, u'Requisição retornou um erro')


    def close_event(self, event):
        self.closingPlugin.emit()
        event.accept()

    def run(self):
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self)

        self.show()



class TreeWidgetDecorator:
    def __init__(self, decorated):
        self._decorated = decorated

    def __getattr__(self, name):
        return getattr(self._decorated, name)

    def append(self, item, parent=None):
        if parent:
            parent.addChild(item)
            return

        self.addTopLevelItem(item)

    # Cria um entry point na lista de recursos
    # name: nome do entry point
    # elements: dict contendo chave:valor dos recursos do entry point
    def append_entry_point(self, name, elements):
        parent_item = ComponentFactory.create_list_resource_element(name, '')
        icon = QIcon(':/plugins/IBGEVisualizer/icon-entry-point.png')
        parent_item.setIcon(0, icon)

        for layer_name, layer_url in elements.items():
            item = ComponentFactory.create_list_resource_element(layer_name, layer_url)
            self.append(item, parent_item)

        self.append(parent_item)



from PyQt4.QtCore import QObject, QModelIndex
from PyQt4.QtGui import QStandardItemModel

class ResourceTreeModel(QStandardItemModel):
    def __init__(self):
        super(ResourceTreeModel, self).__init__()

        memo = Utils.Config.get('memo_urls')
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