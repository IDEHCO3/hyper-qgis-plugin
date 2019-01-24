
# coding: utf-8

from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QFrame


class FrameBase(QFrame):
    # Sinal emitido ao se adicionar ou modificar informações na variavel setup_info
    setup_info_setted = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(FrameBase, self).__init__(parent)

        self._supported_property = None

        # Guarda informações referentes a url e operação que gerou a janela dinâmica
        self._setup_info = {}

    def set_setup_info(self, **kwargs):
        self._setup_info = kwargs
        self.setup_info_setted.emit(self._setup_info)

    def setup_info(self):
        return self._setup_info
