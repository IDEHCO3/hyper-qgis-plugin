
# coding: utf-8

import os

from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal, Qt, QTimer
from PyQt4.QtGui import QApplication, QDockWidget, QMenu, QAction, QIcon, QSortFilterProxyModel, QBrush, QColor

from IBGEVisualizer import HyperResource, Plugin
from IBGEVisualizer.model import ResourceManager
from IBGEVisualizer.Utils import Config, Layer, MessageBox, Logging
from IBGEVisualizer.gui.v2.components.resource_treewidget_decorator import ResourceTreeWidgetDecorator
from IBGEVisualizer.gui.v2.dialog_construct_url import DialogConstructUrl
from IBGEVisualizer.gui.v2.dialog_add_resource import DialogAddResource
from IBGEVisualizer.gui.v2.dialog_edit_resource import DialogEditResource


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
        self.list_resource.itemDoubleClicked.connect(self._list_resource_doubleClicked)

        #self.tx_quick_resource.returnPressed.connect(self._tx_quick_resource_pressed)

    def _tx_quick_resource_pressed(self):
        def extract_name(url):
            return url.strip(' /').split('/')[-1]

        url = self.tx_quick_resource.text()
        self.tx_quick_resource.clear()

        if url:
            name = extract_name(url)
            self.add_resource(name, url)


    def _list_resource_doubleClicked(self, item):
        name = item.text(0)
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
            self.list_resource.add(resource, item)
            return

        self.open_operations_editor(name, iri)

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

    def load_resource(self, resource):
        parent_item = self.list_resource.add(resource)
        parent_item.set_color_user_resource()

    def add_resource(self, name, url):
        resource = ResourceManager.load(url, name)
        self.load_resource(resource)

        Config.set('memo_urls', {name: url})

    def load_resources_from_model(self):
        model = Config.get('memo_urls')
        if not model:
            return

        for name, iri in model.items():
            resource = ResourceManager.load(iri, name)
            self.load_resource(resource)

    def open_context_menu(self, position):
        item = self.list_resource.itemAt(position)
        if not item:
            return

        resource = ResourceManager.load(item.url(), item.name())
        is_leaf_node = item.childCount() == 0
        if is_leaf_node:
            self.show_context_menu(item, resource, position)
        else:
            self.show_entry_point_menu(item, resource, position)

    def show_context_menu(self, item, resource, where):
        menu = QMenu()

        # Load layers action
        action_open_layer = QAction(self.tr(u'Carregar camada'), None)
        action_open_layer.triggered.connect(lambda: self._load_layer_on_qgis(resource))
        menu.addAction(action_open_layer)

        # Load layers as...
        # action_open_layer_as = QAction(self.tr(u'Carregar camada como...'), None)
        # action_open_layer_as.triggered.connect(lambda: self._load_layer_from_url(item.text(0), item.text(1)))
        # menu.addAction(action_open_layer_as)

        menu.addSeparator()

        # Montar Operações
        action_open_editor = QAction(self.tr(u'Montar operações'), None)
        action_open_editor.triggered.connect(lambda: self.open_operations_editor(item.text(0), item.text(1)))
        menu.addAction(action_open_editor)

        menu.addSeparator()

        action_edit = QAction(self.tr(u'Editar'), None)
        action_edit.triggered.connect(lambda: self.open_edit_dialog(item))
        menu.addAction(action_edit)

        menu.exec_(self.list_resource.viewport().mapToGlobal(where))

    def show_entry_point_menu(self, item, resource, where):
        menu = QMenu()

        action_edit = QAction(self.tr(u'Editar'), None)
        action_edit.triggered.connect(lambda: self.open_edit_dialog(item))
        menu.addAction(action_edit)

        menu.exec_(self.list_resource.viewport().mapToGlobal(where))

    def open_edit_dialog(self, item):
        dialog_edit_resource = DialogEditResource(item)
        dialog_edit_resource.accepted.connect(self._resource_edited)
        dialog_edit_resource.exec_()

        return dialog_edit_resource

    def open_operations_editor(self, name, url):
        resource = ResourceManager.load(url, name)

        dialog_construct_url = DialogConstructUrl(resource)
        dialog_construct_url.load_url_command.connect(lambda n, i: self._load_layer_from_iri(dialog_construct_url, n, i))
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

    def _load_layer_from_iri(self, widget, name, iri):
        try:
            dummy = ResourceManager.load(iri, name)
            self._load_layer_on_qgis(dummy)
            widget.close()

        except Exception as e:
            raise

    def _load_layer_on_qgis(self, resource):
        def request_failed(error):
            self.request_error = error
            self.update_status(u'Requisição retornou um erro')
            MessageBox.critical(error, u'Requisição retornou um erro')

        self.timer.stop()
        resource.request_started.connect(self.start_request)
        resource.request_progress.connect(self.download_progress)
        resource.request_error.connect(request_failed)
        resource.request_finished.connect(self.trigger_reset_status)

        # Trigger download of data and events for user feedback
        resource.data()

        if not self.request_error:
            layer = Plugin.create_layer(resource)

            if layer:
                Layer.add(layer)

            if layer.featureCount() == 0:
                Logging.info(u'{} retornou conjunto vazio de dados'.format(resource.iri), u'IBGEVisualizer')
                MessageBox.info(u'URL retornou conjunto vazio')

        else:
            raise Exception(self.request_error)

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
            #self.request_error = False
            self.timer.start()

    def close_event(self, event):
        self.closingPlugin.emit()
        event.accept()

    def run(self):
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self)

        self.show()
