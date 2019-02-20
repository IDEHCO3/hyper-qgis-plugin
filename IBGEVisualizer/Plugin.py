
# coding: utf-8

from PyQt4.QtCore import QVariant
from qgis.core import QgsGeometry, QgsField, QgsFields, QgsFeature

import Geometry, Utils

from layers.VectorLayer import VectorLayer

from IBGEVisualizer.HyperResource import COLLECTION_TYPE_VOCAB, FEATURE_COLLECTION_TYPE_VOCAB, FEATURE_TYPE_VOCAB, \
    POINT_TYPE_VOCAB, MULTIPOINT_TYPE_VOCAB, LINESTRING_TYPE_VOCAB, MULTILINESTRING_TYPE_VOCAB, POLYGON_TYPE_VOCAB, \
    MULTIPOLYGON_TYPE_VOCAB, GEOMETRY_COLLECTION_TYPE_VOCAB, POINT_HTTPS_TYPE_VOCAB, MULTIPOINT_HTTPS_TYPE_VOCAB, \
    LINESTRING_HTTPS_TYPE_VOCAB, MULTILINESTRING_HTTPS_TYPE_VOCAB, POLYGON_HTTPS_TYPE_VOCAB, \
    MULTIPOLYGON_HTTPS_TYPE_VOCAB, FEATURE_COLLECTION_HTTPS_TYPE_VOCAB, FEATURE_HTTPS_TYPE_VOCAB, \
    GEOMETRY_COLLECTION_HTTPS_TYPE_VOCAB

"""
    This script that create layers in QGIS 
"""

class GeoJsonFeature:
    def __init__(self, json_data, resource_properties):
        self.geometry = json_data.get('geometry') or None
        self.geom_type = self.geometry.get('type').lower() if self.geometry else None
        self.properties = json_data.get('properties') and json_data['properties'].values() or None
        self.keys = json_data.get('properties') and json_data['properties'].keys() or None

        self.id = json_data.get('id') or json_data.get('ID') or json_data.get('id_objeto') or None

        self.supported_properties = resource_properties

    def get_qgs_geometry(self):
        if not self.geometry:
            return QgsGeometry()

        return Geometry.convert_to_qgs_geometry(self.geometry)

    def get_qgs_fields(self):
        result = QgsFields()
        result.append(QgsField('feature_id', QVariant.Int))

        if self.supported_properties:
            for field_name in self.keys:
                arr = [prop for prop in self.supported_properties if prop.name == field_name]
                prop = next(iter(arr)) if len(arr) else None

                if prop:
                    field_type = _convert_to_QVariant(prop.at_type)
                    result.append(QgsField(field_name, field_type))
                else:
                    Utils.MessageBox.critical(u"Arquivo de contexto não é compatível com os dados deste recurso")
                    raise Exception(u"Arquivo de contexto não é compatível com os dados deste recurso")

        else:
            for field_name in self.keys:
                result.append(QgsField(field_name, QVariant.String))

        return result

    def as_qgs_features(self):
        qgs_fields = self.get_qgs_fields()
        f = QgsFeature()

        if qgs_fields:
            f.setAttributes([self.id] + self.properties)
            f.setGeometry(self.get_qgs_geometry())

        return [f]


class FeatureCollection:
    def __init__(self, resource):
        switch = {
            'point': 'point',
            'multipoint': 'point',
            'linestring' : 'linestring',
            'multilinestring': 'linestring',
            'polygon': 'polygon',
            'multipolygon': 'polygon'
        }

        self.features = [GeoJsonFeature(f, resource.properties()) for f in resource.as_json().get('features')]

        self.geom_type = switch.get(self.features[0].geom_type) if self.features else 'polygon'

    def get_qgs_fields(self):
        has_features = self.features and len(self.features) > 0
        if has_features:
            return self.features[0].get_qgs_fields()

        return []

    def as_qgs_features(self):
        qgs_features = []

        for feature in self.features:
            qgs_features.append(next(iter(feature.as_qgs_features())))

        return qgs_features


class GeoJsonGeometry:
    def __init__(self, json_data):
        self.geometry = Geometry.convert_to_qgs_geometry(json_data)
        self.geom_type = json_data.get('type') or 'polygon'

    def get_qgs_fields(self):
        return QgsFields()

    def as_qgs_features(self):
        feature = QgsFeature()
        feature.setGeometry(self.geometry)

        return [feature]

class GeometryCollection:
    def __init__(self, resource):
        self.geometries = [GeoJsonGeometry(g) for g in resource.as_json().get('geometries')]
        self.geom_type = self.geometries[0].geom_type

    def get_qgs_fields(self):
        return QgsFields()

    def as_qgs_features(self):
        qgs_features = []

        for geojson_geom in self.geometries:
            feature = QgsFeature()
            feature.setGeometry(geojson_geom.geometry)

            qgs_features.append(feature)

        return qgs_features


class SimpleJSON(object):
    def __init__(self, json_data, resource_properties):
        self.fields = {}
        self.supported_properties = resource_properties

        for k, v in json_data.items():
            if isinstance(v, (int, str, type(None), type(u''), float)):
                self.fields.update({k: v})

            else:
                Utils.Logging.info(u'{key} is {type} and not a primitive type and will not be included as property of this feature'.format(
                    key=k, type=type(v)
                ), 'IBGEVisualizer')

        self.keys = self.fields.keys()

    def get_qgs_fields(self):
        result = QgsFields()

        if self.supported_properties:
            for field_name in self.keys:
                prop = next(prop for prop in self.supported_properties if prop.name == field_name)

                type_ = prop.at_type
                qvariant_type = _convert_to_QVariant(type_)

                result.append(QgsField(field_name, qvariant_type))
        else:
            fields = self.fields.keys()
            for field in fields:
                result.append(QgsField(field, QVariant.String))

        return result

    def as_qgs_features(self):
        f = QgsFeature(self.get_qgs_fields())

        f.setAttributes(self.fields.values())

        return [f]


class SimpleJSONCollection:
    def __init__(self, resource):
        json_data = resource.as_json()
        self.properties = [SimpleJSON(s, resource.properties()) for s in json_data]

    def get_qgs_fields(self):
        if not self.properties or len(self.properties) <= 0:
            return []

        return self.properties[0].get_qgs_fields()

    def as_qgs_features(self):
        qgs_features = []

        for p in self.properties:
            qgs_features.append(next(iter(p.as_qgs_features())))

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

def create_layer(resource):
    collection = _parse_to_layer(resource)

    geom_type = collection.geom_type if hasattr(collection, 'geom_type') else None

    with VectorLayer(resource.name, geom_type) as layer:
        # Setting layer fields
        attributes = collection.get_qgs_fields()
        layer.add_fields(attributes)

        # Put features into layer
        qgis_features = collection.as_qgs_features()
        layer.addFeatures(qgis_features, False)

    return layer

def _parse_to_layer(resource):
    simple_json_collection_command = lambda: SimpleJSONCollection(resource)
    simple_json_command = lambda: SimpleJSON(resource.as_json(), resource.properties())
    feature_collection_command = lambda: FeatureCollection(resource)
    feature_command = lambda: GeoJsonFeature(resource.as_json(), resource.properties())
    geojson_command = lambda: GeoJsonGeometry(resource.as_json())
    geometry_collection_command = lambda: GeometryCollection(resource)

    switch = {
        COLLECTION_TYPE_VOCAB: simple_json_collection_command,

        FEATURE_COLLECTION_TYPE_VOCAB: feature_collection_command,
        FEATURE_TYPE_VOCAB: feature_command,
        GEOMETRY_COLLECTION_TYPE_VOCAB: geometry_collection_command,

        FEATURE_COLLECTION_HTTPS_TYPE_VOCAB: feature_collection_command,
        FEATURE_HTTPS_TYPE_VOCAB: feature_command,
        GEOMETRY_COLLECTION_HTTPS_TYPE_VOCAB: geometry_collection_command,

        POINT_TYPE_VOCAB: geojson_command,
        MULTIPOINT_TYPE_VOCAB: geojson_command,
        LINESTRING_TYPE_VOCAB: geojson_command,
        MULTILINESTRING_TYPE_VOCAB: geojson_command,
        POLYGON_TYPE_VOCAB: geojson_command,
        MULTIPOLYGON_TYPE_VOCAB: geojson_command,

        # TODO ajustar para novas versões do hyper
        POINT_HTTPS_TYPE_VOCAB: geojson_command,
        MULTIPOINT_HTTPS_TYPE_VOCAB: geojson_command,
        LINESTRING_HTTPS_TYPE_VOCAB: geojson_command,
        MULTILINESTRING_HTTPS_TYPE_VOCAB: geojson_command,
        POLYGON_HTTPS_TYPE_VOCAB: geojson_command,
        MULTIPOLYGON_HTTPS_TYPE_VOCAB: geojson_command,

        'Collection': simple_json_collection_command,
        'Thing': simple_json_command,
        'FeatureCollection': feature_collection_command,
        'GeometryCollection': geometry_collection_command,
        'Feature': feature_command,
        'Point': geojson_command,
        'MultiPoint': geojson_command,
        'LineString': geojson_command,
        'MultiLineString': geojson_command,
        'Polygon': geojson_command,
        'MultiPolygon': geojson_command,
    }

    at_type = resource.options().at_type()
    callback = switch.get(at_type) or simple_json_collection_command

    return callback()
