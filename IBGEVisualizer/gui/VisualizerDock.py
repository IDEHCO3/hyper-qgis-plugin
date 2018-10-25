
# -*- coding: utf-8 -*-

import os

from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal, Qt, QTimer
from PyQt4.QtGui import QApplication, QDockWidget

from IBGEVisualizer import Plugin, Utils, HyperResource

from IBGEVisualizer.gui.FrameJoinAttributes import FrameJoinAttributes
from IBGEVisualizer.gui.dialog_tree_test import DialogTreeTest
from IBGEVisualizer.gui.UrlCompleter import UrlCompleter


class VisualizerDockController:
    def __init__(self, iface):
        self.iface = iface
        self.pluginIsClosed = True
        self.view = VisualizerDockView()
        self.tree_test = DialogTreeTest()
        self.frame_join_attributes = FrameJoinAttributes()

        # connect to provide cleanup on closing of dockwidget
        self.view.closingPlugin.connect(self._on_close_plugin)

        # Load URL events
        self.view.tx_url.returnPressed.connect(self._load_url)
        self.view.bt_load_url.clicked.connect(self._load_url)

        # Button Join Attributes
        self.view.bt_join_attributes.clicked.connect(self._open_frame_join_attributes)

        #self.view.tx_url.textChanged.connect(self.view.url_completer.update_completer)

        self.view.bt_tree_test.clicked.connect(self.tree_test.show)

        self.request_error = False

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(7000)
        self.timer.timeout.connect(self.view.lb_status.hide)

    # bt_join_attributes button click action
    def _open_frame_join_attributes(self):
        #self.iface.showLayerProperties(self.iface.activeLayer())
        self.frame_join_attributes.show()

    def _on_close_plugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        self.view.closingPlugin.disconnect(self._on_close_plugin)

        self.pluginIsClosed = True

    def _load_url(self):
        url = self.view.tx_url.text()

        if not url:
            return

        name_layer = self.get_layer_name_from_url(url)

        self.set_ui_enabled(False)

        try:
            reply = HyperResource.request_get(url)
            options_reply = HyperResource.request_options(url)

            self.timer.stop()
            reply.requestStarted.connect(self.start_request)
            reply.downloadProgress.connect(self.download_progress)
            reply.error.connect(self.show_request_error)
            reply.finished.connect(self.trigger_hide_status)

            response = reply.response()
            options_response = options_reply.response()

            obj = HyperResource.create_hyper_object(response, options_response, url)

            if not self.request_error:
                #layer = Plugin.create_layer(name_layer, response)
                layer = Plugin.create_layer_with_hyper_object(name_layer, obj)

                if layer:
                    Utils.Layer.add(layer)
                    self.view.tx_url.setText('')
        except:
            self.view.tx_url.setText('')
            raise
        finally:
            self.set_ui_enabled(True)

    def download_progress(self, received, total):
        if not self.request_error:
            if received == total:
                msg = u'Concluído ' + received
            else:
                msg = u'Baixando recurso... ' + received + (' / ' + total if total != '-1.0' else '')

            self.update_status(msg)

    def start_request(self):
        self.request_error = False
        self.view.lb_status.show()
        self.view.lb_status.setText(u'Enviando requisição e aguardando resposta...')

    def update_status(self, msg):
        self.view.lb_status.show()
        self.view.lb_status.setText(msg)

    def show_request_error(self, error):
        self.request_error = True
        self.update_status(u'Requisição retornou um erro')
        Utils.MessageBox.critical(error, u'Requisição retornou um erro')

    def trigger_hide_status(self):
        if not self.request_error:
            self.timer.start()

    def set_ui_enabled(self, enable):
        self.view.request_sended = (not enable)
        self.view.tx_url.setEnabled(enable)
        self.view.bt_load_url.setEnabled(enable)
        self.view.bt_join_attributes.setEnabled(enable)
        self.view.bt_tree_test.setEnabled(enable)

    def get_layer_name_from_url(self, url):
        spl = url.strip('/').split('/')

        return spl[-1]

    def run(self):
        if self.pluginIsClosed:
            self.pluginIsClosed = False

            self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.view)

            self.view.show()





FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'visualizer_dock.ui'))


class VisualizerDockView(QDockWidget, FORM_CLASS):
    request_sended = False
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(VisualizerDockView, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.url_completer = UrlCompleter()
        self.tx_url.setCompleter(self.url_completer)

        self.lb_status.hide()

    def close_event(self, event):
        self.closingPlugin.emit()
        event.accept()

    # Change mouse cursor when a request is sended to server. request_sended variable
    # is controlled by the Controller
    def enterEvent(self, event):
        if self.request_sended:
            QApplication.setOverrideCursor(Qt.WaitCursor)

    # Mouse event
    def leaveEvent(self, event):
        QApplication.restoreOverrideCursor()

