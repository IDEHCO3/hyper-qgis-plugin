
# -*- coding: utf-8 -*-
import json

from qgis.core import *
from PyQt4.QtCore import QVariant

import Geometry, Utils

from layers.VectorLayer import VectorLayer


"""
    This script takes care of creating layers in QGIS 
"""


class GeoJsonFeature:
    def __init__(self, json_obj, fields_info=None):
        if 'type' in json_obj and json_obj['type'] != 'Feature':
            raise ValueError('This is not a GeoJSON feature object.')

        self.geometry = json_obj.get('geometry') or None
        self.geom_type = self.geometry.get('type').lower() if self.geometry else None
        self.properties = json_obj.get('properties') and json_obj['properties'].values() or None
        self.keys = json_obj.get('properties') and json_obj['properties'].keys() or None

        self.id = json_obj.get('id') or json_obj.get('Id') or json_obj.get('ID') or \
                  json_obj.get('properties').get('id') or json_obj.get('properties').get('Id') or json_obj.get('properties').get('ID') or None

        self.fields = fields_info

    def get_qgs_geometry(self):
        if self.geometry is None:
            return QgsGeometry()

        return Geometry.convert_to_qgs_geometry(self.geometry)

    def get_qgs_fields(self):
        result = QgsFields()
        result.append(QgsField('feature_id', QVariant.Int))

        if self.fields is not None:
            for field_name in self.keys:
                type_ = self.fields.get(field_name)

                if type_:
                    field_type = _convert_to_QVariant(type_.get('@type'))
                    result.append(QgsField(field_name, field_type))
                else:
                    Utils.MessageBox.critical(u"Arquivo de contexto não é compatível com os dados deste recurso", u'')
                    #raise ValueError(u"Arquivo de contexto não é compatível com os dados deste recurso")
                    return

        else:
            for field_name in self.keys:
                result.append(QgsField(field_name, QVariant.String))

        return result

    def to_qgs_feature(self):
        qgs_fields = self.get_qgs_fields()
        f = QgsFeature()

        if qgs_fields:
            f.setAttributes([self.id] + self.properties)
            f.setGeometry(self.get_qgs_geometry())

        return f


class FeatureCollection:
    def __init__(self, json_object, fields_info=None):
        switch = {
            'point': 'point',
            'multipoint': 'point',
            'linestring' : 'linestring',
            'multilinestring': 'linestring',
            'polygon': 'polygon',
            'multipolygon': 'polygon'
        }

        self.features = [GeoJsonFeature(f, fields_info) for f in json_object['features']]
        
        self.geom_type = switch.get(self.features[0].geom_type) or 'polygon'

    def get_qgs_fields(self):
        if self.features is not None and len(self.features) > 0:
            return self.features[0].get_qgs_fields()

        return []

    def get_qgs_features(self):
        qgs_features = []

        for feature in self.features:
            qgs_features.append(feature.to_qgs_feature())

        return qgs_features


class GeoJsonGeometry:
    accepted_geometries = ['point', 'multipoint', 'linestring', 'multilinestring', 'polygon', 'multipolygon']

    def __init__(self, json_obj, fields_info=None):
        if json_obj.get('type').lower() not in self.accepted_geometries:
            raise ValueError('Not a GeoJson Geometry json object')

        self.geometry = Geometry.convert_to_qgs_geometry(json_obj)
        self.geom_type = json_obj.get('type') or 'polygon'


class GeometryCollection:
    def __init__(self, json_obj):
        self.geometries = [GeoJsonGeometry(g) for g in json_obj['geometries']]
        self.geom_type = self.geometries[0].geom_type

    def get_qgs_fields(self):
        return QgsFields()

    def get_qgs_features(self):
        qgs_features = []

        for geojson_geom in self.geometries:
            feature = QgsFeature()
            feature.setGeometry(geojson_geom.geometry)

            qgs_features.append(feature)

        return qgs_features


class SimpleJSON(object):
    def __init__(self, json_obj, fields_info=None):
        self.properties = {}
        self.fields = fields_info

        for k, v in json_obj.items():
            if isinstance(v, (int, str, type(None), type(u''), float)):
                self.properties.update({k: v})

            else:
                Utils.Logging.info(u'{key} is {type} and not a primitive type and will not be included as property of this feature'.format(
                    key=k, type=type(v)
                ), 'IBGEVisualizer')

        self.keys = self.properties.keys()

    def get_qgs_fields(self):
        result = QgsFields()

        if self.fields is not None:
            for field_name in self.keys:
                type_ = self.fields[field_name].get('@type')
                qvariant_type = _convert_to_QVariant(type_)

                result.append(QgsField(field_name, qvariant_type))
        else:
            fields = self.properties.keys()
            for field in fields:
                result.append(QgsField(field, QVariant.String))

        return result

    def to_qgs_feature(self):
        f = QgsFeature(self.get_qgs_fields())

        f.setAttributes(self.properties.values())

        return f


class SimpleJSONCollection:
    def __init__(self, json_obj, fields_info=None):
        self.properties = [SimpleJSON(s, fields_info) for s in json_obj]

    def get_qgs_fields(self):
        if self.properties is not None and len(self.properties) > 0:
            return self.properties[0].get_qgs_fields()

        return []

    def get_qgs_features(self):
        qgs_features = []

        for p in self.properties:
            qgs_features.append(p.to_qgs_feature())

        return qgs_features

def _convert_to_QVariant(var_type):
    switch = {
        str: QVariant.String,
        unicode: QVariant.String,
        int: QVariant.Int,
        float: QVariant.Double,
        bool: QVariant.Bool
    }

    return switch.get(var_type) or QVariant.String

def create_layer(name, response):
    json_as_dict = json.loads(response.get('body'))
    fields_info = response.get('fields')

    collection = extract_json(json_as_dict, fields_info)

    geom_type = collection.geom_type if hasattr(collection, 'geom_type') else None

    with VectorLayer(name, geom_type) as layer:
        # Setting layer fields
        attributes = collection.get_qgs_fields()
        layer.add_fields(attributes)

        # Put features into layer
        qgis_features = collection.get_qgs_features()
        layer.addFeatures(qgis_features, False)

    return layer

def create_layer_with_hyper_object(name, obj):
    json_as_dict = json.loads(obj.resource)
    fields_info = obj.fields

    collection = extract_json(json_as_dict, fields_info)

    geom_type = collection.geom_type if hasattr(collection, 'geom_type') else None

    with VectorLayer(name, geom_type) as layer:
        # Setting layer fields
        attributes = collection.get_qgs_fields()
        layer.add_fields(attributes)

        # Put features into layer
        qgis_features = collection.get_qgs_features()
        layer.addFeatures(qgis_features, False)

    return layer

def extract_json(json_object, fields_info=None):
    if isinstance(json_object, list):
        return SimpleJSONCollection(json_object, fields_info)

    switch = {}

    if 'type' in json_object:
        switch.update({
            'FeatureCollection': lambda json_obj: FeatureCollection(json_obj, fields_info),
            'Feature': lambda json_obj: FeatureCollection({'features': [json_obj]}, fields_info),
            'GeometryCollection': lambda json_obj: GeometryCollection(json_obj),

            'Point': lambda json_obj: GeometryCollection({'geometries': [json_obj]}),
            'MultiPoint': lambda json_obj: GeometryCollection({'geometries': [json_obj]}),
            'Linestring': lambda json_obj: GeometryCollection({'geometries': [json_obj]}),
            'MultiLinestring': lambda json_obj: GeometryCollection({'geometries': [json_obj]}),
            'Polygon': lambda json_obj: GeometryCollection({'geometries': [json_obj]}),
            'MultiPolygon': lambda json_obj: GeometryCollection({'geometries': [json_obj]}),
        })

    callback = switch.get(json_object.get('type')) or (lambda json_obj: SimpleJSONCollection([json_obj], fields_info))

    return callback(json_object)
