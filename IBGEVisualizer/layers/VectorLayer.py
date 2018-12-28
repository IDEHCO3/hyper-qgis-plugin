
# -*- coding: utf-8 -*-

from qgis.core import QgsVectorLayer


class VectorLayer(QgsVectorLayer):
    def __init__(self, name=None, geom_type=None, crs='EPSG:4326'):
        if name is None:
            super(VectorLayer, self).__init__()
            return

        typ = geom_type or 'point'
        super(VectorLayer, self).__init__('%s?crs=%s&index=yes' % (typ, crs), name, 'memory')

    def __enter__(self):
        self.startEditing()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.commitChanges()
        self.updateExtents()
        self.updateFields()
        self.reload()

    def fields(self):
        return super(VectorLayer, self).fields().toList()

    def add_fields(self, qgs_field_list):
        if not qgs_field_list: return

        for field in qgs_field_list:
            self.addAttribute(field)
