
# -*- coding: utf-8 -*-

"""
    Code adapted from Plugin MemoryLayerSaver: https://github.com/ccrook/QGIS-MemoryLayerSaver-Plugin
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from qgis.core import *
import sys


class Writer(QObject):
    def __init__(self, file_name):
        super(Writer, self).__init__(None)

        self._file_name = file_name
        self._file = None
        self._data_stream = None


    def __enter__(self):
        self.open()
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


    def open(self):
        self._file = QFile(self._file_name)

        if not self._file.open(QIODevice.WriteOnly):
            raise ValueError("Cannot open " + self._filename)

        self._data_stream = QDataStream(self._file)
        self._data_stream.setVersion(QDataStream.Qt_4_5)

        for c in "QGis-PersistentIBGEVisualizerLayer":
            self._data_stream.writeUInt8(c)

        # Write version number
        self._data_stream.writeUInt32(1)

    def close(self):
        try:
            self._data_stream.setDevice(None)
            self._file.close()

        except OSError:
            pass

        self._data_stream = None
        self._file = None


    def write_layers(self, layers):
        for layer in layers:
            self.write_layer(layer)


    def write_layer(self, layer):
        if not self._data_stream:
            raise ValueError("Layer stream not open for reading")

        ds = self._data_stream
        dp = layer.dataProvider()
        ss = layer.subsetString()
        attr = dp.attributeIndexes()

        ds.writeQString(layer.id())
        ds.writeQString(ss)
        ds.writeInt16(len(attr))

        field_names = []
        for i in attr:
            field = dp.fields()[i]
            field_names.append(field.name())

            ds.writeQString(field.name())
            ds.writeInt16(int(field.type()))
            ds.writeQString(field.typeName())
            ds.writeInt16(field.length())
            ds.writeInt16(field.precision())
            ds.writeQString(field.comment())

        layer.setSubsetString('')

        for feat in layer.getFeatures():
            ds.writeBool(True)

            if attr:
                for field in field_names:
                    try:
                        ds.writeQVariant(feat[field])

                    except KeyError:
                        ds.writeQVariant(None)

            geom = feat.geometry()

            if not geom:
                ds.writeUInt32(0)

            else:
                ds.writeUInt32(geom.wkbSize())
                ds.writeRawData(geom.asWkb())

        ds.writeBool(False)
        layer.setSubsetString(ss)

class Reader:
    def __init__(self, filename):
        self._filename = filename
        self._file = None
        self._data_stream = None
        self._version = None


    def __enter__(self):
        self.open()
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


    def open(self):
        self._file = QFile(self._filename)

        if not self._file.open(QIODevice.ReadOnly):
            raise ValueError("Cannot open %s" % self._filename)

        self._data_stream = QDataStream(self._file)
        self._data_stream.setVersion(QDataStream.Qt_4_5)

        for c in "QGis-PersistentIBGEVisualizerLayer":
            ct = self._data_stream.readUInt8()
            if ct != c:
                raise ValueError("%s is not a valid memory layer data file" % self._filename)

        version = self._data_stream.readInt32()

        self._version = version

    def close(self):
        try:
            self._data_stream.setDevice(None)
            self._file.close()

        except OSError:
            pass

        self._data_stream = None
        self._file = None


    def read_layers(self, layers):
        if not self._data_stream:
            raise ValueError("Layer stream not open for reading")

        ds = self._data_stream

        while True:
            if ds.atEnd(): return

            _id = ds.readQString()
            layer = None

            for l in layers:
                if l.id() == _id:
                    layer = l

            if not layer:
                self.skip_layer()

            else:
                self.read_layer(layer)


    def read_layer(self, layer):
        ds = self._data_stream
        dp = layer.dataProvider()

        if dp.featureCount() > 0:
            raise ValueError(u"Memory layer is already loaded")

        attr = dp.attributeIndexes()
        dp.deleteAttributes(attr)

        ss = ds.readQString()

        nattr = ds.readInt16()
        attr = range(nattr)

        for _ in attr:
            name = ds.readQString()
            qtype = ds.readInt16()
            typename = ds.readQString()
            length = ds.readInt16()
            precision = ds.readInt16()
            comment = ds.readQString()
            field = QgsField(name, qtype, typename, length, precision, comment)
            dp.addAttributes([field])

        nullgeom = QgsGeometry()
        fields = dp.fields()

        while ds.readBool():
            feat = QgsFeature(fields)

            for i in attr:
                value = ds.readQVariant()
                if value is not None:
                    feat[i] = value

            wkb_size = ds.readUInt32()
            if wkb_size == 0:
                feat.setGeometry(nullgeom)
            else:
                geom = QgsGeometry()
                geom.fromWkb(ds.readRawData(wkb_size))
                feat.setGeometry(geom)

            dp.addFeatures([feat])

        layer.setSubsetString(ss)
        layer.updateFields()
        layer.updateExtents()


    def skip_layer(self):
        ds = self._data_stream
        nattr = ds.readInt16()
        attr = range(nattr)

        for _ in attr:
            name = ds.readQString()
            qtype = ds.readInt16()
            typename = ds.readQString()
            length = ds.readInt16()
            precision = ds.readInt16()
            comment = ds.readQString()

        while ds.readBool():
            for _ in attr:
                ds.readQVariant()

            wkb_size = ds.readUInt32()

            if wkb_size > 0:
                ds.readRawData(wkb_size)



class MemoryLayerSaver:
    def __init__( self, iface ):
        self._iface = iface
        version = QGis.QGIS_VERSION_INT
        self._deleteSignalOk = version >= 10700

    def attach_to_project(self):
        self.connect_to_project()
        self.connect_memory_layers()

    def detach_from_project(self):
        # Following line OK in 1.7
        # Cannot delete memory files in QGis 1.6 as they get deleted
        # on project exit.
        # self.deleteMemoryDataFiles()
        self.disconnect_from_project()
        self.disconnect_memory_layers()


    def connect_to_project(self):
        proj = QgsProject.instance()
        QObject.connect(proj, SIGNAL("readProject(const QDomDocument &)"),self.load_data)
        QObject.connect(proj, SIGNAL("writeProject(QDomDocument &)"),self.save_data)
        QObject.connect(QgsMapLayerRegistry.instance(),
                        SIGNAL("layerWasAdded(QgsMapLayer *)"),self.connect_provider)


    def disconnect_from_project(self):
        proj = QgsProject.instance()
        QObject.disconnect(proj, SIGNAL("readProject(const QDomDocument &)"),self.load_data)
        QObject.disconnect(proj, SIGNAL("writeProject(QDomDocument &)"),self.save_data)
        QObject.disconnect(QgsMapLayerRegistry.instance(),
                           SIGNAL("layerWasAdded(QgsMapLayer *)"),self.connect_provider)

    def connect_provider( self, layer ):
        if self.is_saved_layer(layer):
            QObject.connect(layer, SIGNAL("committedAttributesDeleted"),self.set_project_dirty2)
            QObject.connect(layer, SIGNAL("committedAttributesAdded"),self.set_project_dirty2)
            if self._deleteSignalOk:
                QObject.connect(layer, SIGNAL("committedFeaturesRemoved"),self.set_project_dirty2)
            QObject.connect(layer, SIGNAL("committedFeaturesAdded"),self.set_project_dirty2)
            QObject.connect(layer, SIGNAL("committedAttributeValuesChanges"),self.set_project_dirty2)
            QObject.connect(layer, SIGNAL("committedGeometriesChanges"),self.set_project_dirty2)

    def disconnect_provider( self, layer ):
        if self.is_saved_layer(layer):
            QObject.disconnect(layer, SIGNAL("committedAttributesDeleted"),self.set_project_dirty2)
            QObject.disconnect(layer, SIGNAL("committedAttributesAdded"),self.set_project_dirty2)
            if self._deleteSignalOk:
                QObject.disconnect(layer, SIGNAL("committedFeaturesRemoved"),self.set_project_dirty2)
            QObject.disconnect(layer, SIGNAL("committedFeaturesAdded"),self.set_project_dirty2)
            QObject.disconnect(layer, SIGNAL("committedAttributeValuesChanges"),self.set_project_dirty2)
            QObject.disconnect(layer, SIGNAL("committedGeometriesChanges"),self.set_project_dirty2)


    def connect_memory_layers( self ):
        for layer in self.memory_layers():
            self.connect_provider( layer )


    def disconnect_memory_layers( self ):
        for layer in self.memory_layers():
            self.disconnect_provider( layer )


    def unload(self):
        # self._iface.removePluginMenu("&Test tools",self._loadadjaction)
        pass


    def load_data(self):
        filename = self.memory_layer_file()
        file = QFile(filename)

        if file.exists():
            layers = list(self.memory_layers())

            if layers:
                try:
                    with Reader(filename) as reader:
                        reader.read_layers(layers)

                except:
                    QMessageBox.information(
                        self._iface.mainWindow(),"Error reloading memory layers",
                        unicode(sys.exc_info()[1]) )

    def save_data(self):
        try:
            filename = self.memory_layer_file()

            layers = list(self.memory_layers())

            if layers:
                with Writer(filename) as writer:
                    writer.write_layers( layers )

        except:
            raise QMessageBox.information(self._iface.mainWindow(), "Error saving memory layers",
                                          unicode(sys.exc_info()[1]) )


    def memory_layers(self):
        for l in QgsMapLayerRegistry.instance().mapLayers().values():
            if self.is_saved_layer(l):
                yield l


    def is_saved_layer( self, l ):
        if l.type() != QgsMapLayer.VectorLayer:
            return

        pr = l.dataProvider()

        if not pr or pr.name() != 'memory':
            return False

        use = l.customProperty("SaveMemoryProvider")

        return not (use == False)


    def memory_layer_file( self ):
        name = QgsProject.instance().fileName()

        if not name:
            return ''

        return '%s.mldata' % name


    def clear_memory_provider(self, lyr):
        pl = lyr.dataProvider()
        pl.select()
        f = QgsFeature()

        while pl.nextFeature(f):
            pl.deleteFeatures(f.id())

        pl.deleteAttributes(pl.attributeIndexes())


    def set_project_dirty2(self, value1, value2):
        self.set_project_dirty()


    def set_project_dirty(self):
        QgsProject.instance().dirty(True)
