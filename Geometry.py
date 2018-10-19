
# -*- coding: utf-8 -*-

from qgis.core import *

def convert_to_qgs_geometry(geom):
    if geom is None: return create_empty_qgs_geometry()

    switch = {
        'point': create_point,
        'multipoint': create_multi_point,
        'linestring': create_linestring,
        'multilinestring': create_multi_linestring,
        'polygon': create_polygon,
        'multipolygon': create_multi_polygon
        #'geometrycollection': create_geometry_collection
    }

    callback = switch.get(geom['type'].lower(), create_empty_qgs_geometry)
    return callback(geom['coordinates'])

    
def create_empty_qgs_geometry(*args):
    return QgsGeometry()
    

def create_point(coord):
    return QgsGeometry.fromPoint( QgsPoint(coord[0], coord[1]) )


def create_multi_point(point_array):
    vector = []

    for point in point_array:
        p = create_point(point)
        vector.append(p.asPoint())

    return QgsGeometry.fromMultiPoint( vector )


def create_linestring(point_array):
    vector = []

    for point in point_array:
        p = QgsPoint(point[0], point[1])
        vector.append(p)

    return QgsGeometry.fromPolyline( vector )

    
def create_multi_linestring(line_array):
    vector = []

    for line in line_array:
        l = create_linestring(line)
        vector.append(l.asPolyline())

    return QgsGeometry.fromMultiPolyline( vector )


def create_polygon(line_array):
    vector = []

    for line in line_array:
        l = create_linestring(line)
        vector.append(l.asPolyline())

    return QgsGeometry.fromPolygon( vector )


def create_multi_polygon(polygon_array):
    vector = []

    for polygon in polygon_array:
        p = create_polygon(polygon)
        vector.append(p.asPolygon())

    return QgsGeometry.fromMultiPolygon( vector )