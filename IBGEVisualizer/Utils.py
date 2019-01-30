
# coding: utf-8

from __future__ import with_statement

from qgis.core import *
from qgis.utils import iface
from qgis.gui import QgsMessageBar

from PyQt4 import QtGui


class Utils:
    @staticmethod
    # Add a layer
    # @param layer: object type qgis.core.QgsMapLayer
    # @return: None if is no possible add the layer, layer instance otherwise
    def addLayer(layer):
        if layer is None:
            Utils.infoMessage("Layer is null.")
            return None

        l = QgsMapLayerRegistry.instance().addMapLayer(layer)

        if l is None:
            Utils.infoMessage("Impossible to add layer.", 5)
            return None

        return l

    # Get a list of layers with designated name
    # @param name: name of layer
    # @return: List of layers with that name
    @staticmethod
    def getLayersByName(name):
        return QgsMapLayerRegistry.instance().mapLayersByName(name)

    @staticmethod
    def registerLayerType(layer_type):
        return QgsPluginLayerRegistry.instance().addPluginLayerType(layer_type)

    @staticmethod
    # Refresh QGis canvas
    def refreshCanvas():
        iface.mapCanvas().refresh()

    @staticmethod
    def infoMessage(message, duration=3):
        iface.messageBar().pushMessage('Info: ', message, QgsMessageBar.INFO, duration)

    @staticmethod
    def log(msg, tab=None, level=None):
        level = level or Logging.INFO
        QgsMessageLog.instance().logMessage(msg, tab, level)

    @staticmethod
    def message_box(message, title, box_type=None):
        box_type = box_type or MessageBox.INFORMATION

        mes_box = QtGui.QMessageBox(box_type, title, message)

        mes_box.show()
        mes_box.exec_()

    @staticmethod
    def question_box(message, title):
        reply = QtGui.QMessageBox.question(None, title, message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        return True if reply == QtGui.QMessageBox.Yes else False


class Layer:
    @staticmethod
    def add(layer):
        return Utils.addLayer(layer)

    @staticmethod
    def register_type(layer_type):
        return Utils.registerLayerType(layer_type)

    @staticmethod
    def search_by_name(name):
        return Utils.getLayersByName(name)


class Logging:
    INFO, WARNING, CRITICAL = range(3)

    @staticmethod
    def info(msg, tab=None):
        Utils.log(msg, tab)

    @staticmethod
    def warning(msg, tab=None):
        Utils.log(msg, tab, Logging.WARNING)

    @staticmethod
    def critical(msg, tab=None):
        Utils.log(msg, tab, Logging.CRITICAL)


class MessageBox:
    NO_ICON, INFORMATION, WARNING, CRITICAL, QUESTION = range(5)

    @staticmethod
    def info(message, title=''):
        Utils.message_box(message, title, MessageBox.INFORMATION)

    @staticmethod
    def critical(message, title=''):
        Utils.message_box(message, title, MessageBox.CRITICAL)

    @staticmethod
    def question(message, title=''):
        return Utils.question_box(message, title)

    @staticmethod
    def warning(message, title=''):
        Utils.message_box(message, title, MessageBox.WARNING)


class Config:
    @staticmethod
    def has(key):
        import json, os

        path = os.path.dirname(__file__) + '\config.json'

        with open(path, 'r') as file_:
            data = json.loads(file_.read())

        return key in data

    @staticmethod
    def get(key=None):
        import json, os

        path = os.path.dirname(__file__) + '\config.json'

        with open(path, 'r') as file_:
            data = json.loads(file_.read())

        if key:
            if key in data:
                return data[key]

        else:
            return data

    @staticmethod
    def set(key, value):
        import json, os

        path = os.path.dirname(__file__) + '\config.json'

        with open(path, 'r') as file_:
            json_str = file_.read()

            data = {}
            if json_str:
                data = json.loads(json_str)

            key_exists = key and (key in data)
            if key_exists:
                if isinstance(value, dict):
                    data[key].update(value)
                else:
                    data.update({key: value})

        with open(path, 'w') as file_:
            json.dump(data, file_, indent=2, ensure_ascii=True)

    @staticmethod
    def update_dict(key, dict_value):
        import json, os

        path = os.path.dirname(__file__) + '\config.json'

        with open(path, 'r') as file_:
            json_str = file_.read()

            data = {}
            if json_str:
                data = json.loads(json_str)

            key_exists = key and (key in data)
            if key_exists:
                if isinstance(dict_value, dict):
                    data[key] = dict_value

                with open(path, 'w') as config_file:
                    json.dump(data, config_file, indent=2, ensure_ascii=True)
