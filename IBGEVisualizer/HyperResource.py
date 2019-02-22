
# coding: utf-8

import os
import re
import json

import Utils
import request

from PyQt4.QtCore import pyqtSignal, QObject
from IBGEVisualizer.Utils import Logging

from IBGEVisualizer.error import BadAddressError


def GET(url):
    return request_get(url)

def HEAD(url):
    return request_head(url)

def OPTIONS(url):
    return request_options(url)

def request_get(url):
    Utils.Logging.info(u'URL consultada: {}. Method: GET'.format(url), u'IBGEVisualizer')
    return request.get(url)

def request_options(url):
    Utils.Logging.info(u'URL consultada: {}. Method: OPTIONS'.format(url), u'IBGEVisualizer')
    return request.options(url)

def request_head(url):
    Utils.Logging.info(u'URL consultada: {}. Method: HEAD'.format(url), u'IBGEVisualizer')
    return request.head(url)

def _get_fields(context):
    if context is None:
        return {}

    output = {}

    switch = {
        INTEGER_TYPE_VOCAB: int,
        TEXT_TYPE_VOCAB: unicode,
        FLOAT_TYPE_VOCAB: float,
        BOOLEAN_TYPE_VOCAB: bool,
        GEOMETRY_TYPE_VOCAB: u'geometria',
        u"@id": unicode
    }

    for k, v in context.items():
        if isinstance(v, dict):
            output.update({k: v})
            field = output[k]
            field.update({'@type': switch.get(v.get('@type')) or unicode})

    return output

def _get_entry_point_from_link(link_tab):
    if not link_tab:
        return ''

    import re
    entry_point = re.search(r'^<.+?>', link_tab).group(0).strip('<>')

    return entry_point


class SupportedProperty(object):
    def __init__(self, at_context, **data):
        self.name = data.get('hydra:property') or data.get('hydra:title') or data.get('name') or ''
        self.is_writeable = data.get('hydra:writeable') or data.get('is_writeable') or False
        self.is_readable = data.get('hydra:readable') or data.get('is_readable') or False
        self.is_required = data.get('hydra:required') or data.get('is_required') or False
        self.is_unique = data.get('isUnique') or data.get('is_unique') or False
        self.is_identifier = data.get('isIdentifier') or data.get('is_identifier') or False
        self.is_external = data.get('isExternal') or data.get('is_external') or False
        self.supported_operation = data.get('hydra:supportedOperations') or data.get('supportedOperations') or []

        term_definition = at_context.get(self.name) or {}
        self.at_type = term_definition.get('@type') or None
        self.at_id = term_definition.get('@id')

    def __str__(self):
        return u'<SupportedProperty: "name":{}, "is_writeable":{}, "is_readable":{}, "is_required":{}, "is_unique": {}, ' \
               u'"is_identifier": {}, "is_external": {}, "supported operations": {}>' \
                .format(unicode(self.name), str(self.is_writeable), str(self.is_readable), str(self.is_required),
                    str(self.is_unique), str(self.is_identifier), str(self.is_external),
                        str(self.supported_operation_link()))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.name == other.name

    def supported_operation_link(self):
        operation = self.supported_operation[0] if self.supported_operation else {}

        if operation.get('hydra:Link'):
            return (operation.get('hydra:Link'))[0] or None

        return None

    def operations(self):
        link = self.supported_operation_link()
        reader = PropertySupportedOperationReader(link)

        return reader.extract_operation()


class SupportedOperation(object):
    def __init__(self, **data):
        self.name = data.get('hydra:operation') or data.get('name') or ''
        self.expects = data.get('hydra:expects') or data.get('expects') or []
        self.returns = data.get('hydra:returns') or data.get('returns') or []
        self.status_code = data.get('hydra:statusCode') or data.get('status_code') or ''
        self.method = data.get('hydra:method') or data.get('method') or ''
        self.context = data.get('@id') or data.get('id') or ''

    def __str__(self):
        return u'<SupportedOperation: "name":{}, "expects":{}, "returns":{}, "method":{}, "status_code": {}, "context": {}>'\
            .format(unicode(self.name), str(self.expects), str(self.returns), str(self.method),
                   str(self.status_code), str(self.context))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.name == other.name

    def parameters(self):
        if isinstance(self.expects, list):
            if isinstance(self.expects[0], dict):
                return [param.get('parameter') for param in self.expects]

            return self.expects


class PropertySupportedOperation:
    def __init__(self, **data):
        self.name = data.get('name') or ''
        self.definition = data.get('definition') or ''
        self.parameters = data.get('parameters') or ''
        self.return_field = data.get('return_field') or ''
        self.example = data.get('example') or ''


class PropertySupportedOperationReader:
    def __init__(self, url):
        #TODO apagar isso qundo tiver um ip certo
        if url:
            url = url.replace('172.30.10.86', '172.30.137.117')

        self.url = url

        self._data = {}
        self._response = None
        self._promise = GET(self.url) if self.url else None

    def response(self):
        if not self._response:
            if self._promise:
                self._response = self._promise.response()

        return self._response or {}

    def as_text(self):
        if not self._data:
            self._data = self.response()

            if 200 > self._data.get('status_code') >= 300:
                raise Exception(
                    u'Acesso à {url} retornou {code} {phrase}'.format(
                        url=self.url,
                        code=self._data['status_code'],
                        phrase=self._data['status_phrase']))

        return self._data.get('body') or '{}'

    def as_json(self):
        return json.loads(self.as_text())

    def extract_operation(self):
        json_options = self.as_json()

        if not json_options:
            return []

        order_by_name = lambda prop: prop.name
        return_array = [PropertySupportedOperation(**data) for data in json_options]
        return_array.sort(key=order_by_name)

        return return_array or []


JSON_LD_CONTENT_TYPE = 'application/ld+json'

CONTEXT_LINK = 'http://www.w3.org/ns/json-ld#context'
ENTRY_POINT_LINK = 'https://schema.org/EntryPoint'
ENTRY_POINT_HTTP_LINK = 'http://schema.org/EntryPoint'
STYLESHEET_LINK = 'stylesheet'
METADATA_LINK = 'metadata'

HYDRA_VOCAB = 'hydra:'
SUPPORTED_OPERATION_VOCAB = HYDRA_VOCAB + 'supportedOperations'
SUPPORTED_PROPERTY_VOCAB = HYDRA_VOCAB + 'supportedProperties'
PROPERTY_VOCAB = HYDRA_VOCAB + 'property'
OPERATION_VOCAB = HYDRA_VOCAB + 'operation'

COLLECTION_TYPE_VOCAB = HYDRA_VOCAB + "Collection"

FEATURE_COLLECTION_TYPE_VOCAB = "http://geojson.org/geojson-ld/vocab.html#FeatureCollection"
FEATURE_COLLECTION_HTTPS_TYPE_VOCAB  = "https://purl.org/geojson/vocab#FeatureCollection"
FEATURE_TYPE_VOCAB = "http://geojson.org/geojson-ld/vocab.html#Feature"
FEATURE_HTTPS_TYPE_VOCAB  = "https://purl.org/geojson/vocab#Feature"

POINT_TYPE_VOCAB = "https://purl.org/geojson/vocab#Point"
POINT_HTTPS_TYPE_VOCAB = "http://geojson.org/geojson-ld/vocab.html#Point"
MULTIPOINT_TYPE_VOCAB = "http://geojson.org/geojson-ld/vocab.html#MultiPoint"
MULTIPOINT_HTTPS_TYPE_VOCAB = "https://purl.org/geojson/vocab#MultiPoint"

LINESTRING_TYPE_VOCAB = "http://geojson.org/geojson-ld/vocab.html#LineString"
LINESTRING_HTTPS_TYPE_VOCAB = "https://purl.org/geojson/vocab#LineString"

MULTILINESTRING_TYPE_VOCAB = "http://geojson.org/geojson-ld/vocab.html#MultiLineString"
MULTILINESTRING_HTTPS_TYPE_VOCAB = "https://purl.org/geojson/vocab#MultiLineString"

POLYGON_TYPE_VOCAB = "http://geojson.org/geojson-ld/vocab.html#Polygon"
POLYGON_HTTPS_TYPE_VOCAB = "https://purl.org/geojson/vocab#Polygon"

MULTIPOLYGON_TYPE_VOCAB = "http://geojson.org/geojson-ld/vocab.html#MultiPolygon"
MULTIPOLYGON_HTTPS_TYPE_VOCAB = "https://purl.org/geojson/vocab#MultiPolygon"

GEOMETRY_TYPE_VOCAB = "http://geojson.org/geojson-ld/vocab.html#geometry"
GEOMETRY_HTTPS_TYPE_VOCAB = "https://purl.org/geojson/vocab#geometry"

GEOMETRY_COLLECTION_TYPE_VOCAB = "http://geojson.org/geojson-ld/vocab.html#GeometryCollection"
GEOMETRY_COLLECTION_HTTPS_TYPE_VOCAB = "https://purl.org/geojson/vocab#GeometryCollection"

EXPRESSION_TYPE_VOCAB = 'http://extension.schema.org/expression'
ITEM_LIST_TYPE_VOCAB = 'https://schema.org/ItemList'
THING_TYPE_VOCAB = 'https://schema.org/Thing'
INTEGER_TYPE_VOCAB = 'https://schema.org/Integer'
FLOAT_TYPE_VOCAB = 'https://schema.org/Float'
TEXT_TYPE_VOCAB = 'https://schema.org/Text'
BOOLEAN_TYPE_VOCAB = 'https://schema.org/Boolean'

class Resource(QObject):
    request_started = pyqtSignal()
    request_progress = pyqtSignal(unicode, unicode)
    request_error = pyqtSignal(unicode)
    request_finished = pyqtSignal()

    def __init__(self, iri, name=''):
        super(Resource, self).__init__()

        self._resource_name = None
        self._resource_iri = None

        self._header = None
        self._get = None
        self._options = None

        self.iri = iri
        self.name = name

        self.error = None

        #self.jsonld_parser = JsonLdParser(iri)

    @property
    def name(self):
        return self._resource_name

    @name.setter
    def name(self, name):
        self._resource_name = name

    @property
    def iri(self):
        return self._resource_iri

    @iri.setter
    def iri(self, iri):
        i = iri.strip()
        if self._resource_iri == i:
            return

        self._resource_iri = i
        self._header = None
        self._get = None
        self._options = None

    def header(self):
        if self._header is None:
            try:
                self._header = HeaderReader(self.iri)
                self._header.headers()      # Forcing download of data for error handling
            except Exception as e:
                self.error = e
                Logging.warning(unicode(e))

        return self._header

    def data(self):
        if self._get is None:
            self._get = GetReader(self.iri)
            self._connect_signals(self._get)

        return self._get

    def options(self):
        if self._options is None:
            self._options = OptionsReader(self.iri)

        return self._options

    def properties(self):
        return self.options().properties()

    def operations(self):
        return self.options().operations()

    def property(self, name):
        return self.options().get_property(name)

    def operation(self, name):
        return self.options().get_operation(name)

    def as_text(self):
        return self.data().as_text()

    def as_json(self):
        return self.data().as_json()

    def resource_type(self):
        return self.options().at_type()

    def is_entry_point(self):
        return self.header().is_entry_point()

    def at_id(self):
        return self.options().at_id()

    def at_type(self):
        return self.options().at_type()

    def _connect_signals(self, obj):
        obj.request_started.connect(self.request_started)
        obj.request_progress.connect(self.request_progress)
        obj.request_error.connect(self.request_error)
        obj.request_finished.connect(self.request_finished)


class HeaderReader:
    def __init__(self, iri):
        i = iri.strip()
        if not i:
            return

        self._headers = None
        self.error = None
        self.iri = i

    def headers(self):
        if not self._headers:
            reply = request_head(self.iri)
            response = reply.response()

            # Verify if iri is available
            if int(response['status_code']) < 200 or int(response['status_code']) >= 300:
                error = BadAddressError(u'Acesso à {} retornou {} {}'.format(
                    self.iri, response['status_code'], response['status_phrase']))
                self.error = error
                self._headers = None
                raise error

            self._headers = self._parse(response)

        return self._headers

    def field(self, name):
        if self.error:
            return None

        return self.headers().get(name) or None

    def _parse(self, response):
        headers = response.get('headers')

        headers.update(response)
        headers.update({
            'link': self.parse_link_header(headers.get('link')),
            'allow': self.parse_list(headers.get('allow')),
            'date': self.parse_date(headers.get('date')),
            'access-control-allow-headers': self.parse_list(headers.get('access-control-allow-headers')),
            'access-control-allow-origin': self.parse_list(headers.get('access-control-allow-origin')),
            'access-control-allow-methods': self.parse_list(headers.get('access-control-allow-methods')),
            'access-control-expose-headers': self.parse_list(headers.get('access-control-expose-headers'))
        })

        return headers

    def link_header(self):
        if self.error:
            return None

        return self.field('link')

    def is_entry_point(self):
        if self.error:
            return False

        return self.link_header().get(ENTRY_POINT_LINK) or self.link_header().get(ENTRY_POINT_HTTP_LINK) or False

    def stylesheet_iri(self):
        if self.error:
            return None

        return self.link_header().get(STYLESHEET_LINK)

    def metadata_iri(self):
        if self.error:
            return None

        return self.link_header().get(METADATA_LINK)

    def context_iri(self):
        if self.error:
            return None

        link = self.link_header()
        context = link.get(CONTEXT_LINK) or None
        if not context:
            raise ValueError('Context link dont exists')

        if context['type'] == JSON_LD_CONTENT_TYPE:
            raise ValueError('Context is not ld+json media file')

        return context

    def parse_list(self, field):
        if not field:
            return []

        return field.split(',')

    def parse_date(self, date):
        if not date:
            return ''

        from datetime import datetime
        return datetime.strptime(date, '%a, %d %b %Y %H:%M:%S GMT')

    def parse_link_header(self, header):
        if not header: {}
        """
        Parses a link header. The results will be key'd by the value of "rel".

        Link: <http://json-ld.org/contexts/person.jsonld>; \
          rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"

        Parses as: {
          'http://www.w3.org/ns/json-ld#context': {
            target: http://json-ld.org/contexts/person.jsonld,
            type: 'application/ld+json'
          }
        }

        If there is more than one "rel" with the same IRI, then entries in the
        resulting map for that "rel" will be lists.

        :param header: the link header to parse.

        :return: the parsed result.
        """
        rval = {}
        # split on unbracketed/unquoted commas
        entries = re.findall(r'(?:<[^>]*?>|"[^"]*?"|[^,])+', header)
        if not entries:
            return rval

        for entry in entries:
            match = re.search(r'\s*<([^>]*?)>\s*(?:;\s*(.*))?', entry)

            if not match:
                continue

            match = match.groups()
            result = {'target': match[0]}
            params = match[1]
            matches = re.findall(r'(.*?)=(?:(?:"([^"]*?)")|([^"]*?))\s*(?:(?:;\s*)|$)', params)

            for match in matches:
                result[match[0]] = match[2] if match[1] is None else match[1]

            rel = result.get('rel', '')
            if isinstance(rval.get(rel), list):
                rval[rel].append(result)
            elif rel in rval:
                rval[rel] = [rval[rel], result]
            else:
                rval[rel] = result

        return rval


class GetReader(QObject):
    request_started = pyqtSignal()
    request_progress = pyqtSignal(unicode, unicode)
    request_error = pyqtSignal(unicode)
    request_finished = pyqtSignal()

    def __init__(self, iri):
        super(GetReader, self).__init__()

        if not iri:
            return

        self.iri = iri
        self._data = None

        self._reply = GET(iri)
        self._connect_signals(self._reply)

        self._response = None

    def response(self):
        if self._response is None:
            self._response = self._reply.response()

        return self._response

    def as_text(self):
        if not self._data:
            self._data = self.response()

            if 200 > self._data['status_code'] >= 300:
                raise Exception(u'Acesso à {} retornou {} {}'.format(
                    self.iri, self._data['status_code'], self._data['status_phrase']))

        return self._data.get('body')

    def as_json(self):
        return json.loads(self.as_text())

    def _connect_signals(self, obj):
        obj.requestStarted.connect(self.request_started)
        obj.downloadProgress.connect(self.request_progress)
        obj.error.connect(self.request_error)
        obj.finished.connect(self.request_finished)


class OptionsReader:
    def __init__(self, iri):
        if not iri:
            return

        self.iri = iri

        self._reply = request_options(iri)
        self._response = None

        self._operations = None
        self._properties = None

    def _parse(self, callback):
        response = self.response()

        invalid_status_code = 200 > response['status_code'] >= 300
        if invalid_status_code:
            raise Exception(u'Acesso à {} retornou {} {}'.format(
                self.iri, response['status_code'], response['status_phrase']))

        options_body = response.get('body')
        json_opt = json.loads(options_body)

        #TODO passar json_opt por json-ld parser para acesso semântico aos elementos

        return callback(json_opt)

    def response(self):
        if self._response is None:
            self._response = self._reply.response()

        return self._response

    def operations(self):
        if self._operations is None:
            self._operations = self._parse(self._extract_supported_operations)

        return self._operations

    def properties(self):
        if self._properties is None:
            self._properties = self._parse(self._extract_supported_properties)

        return self._properties

    def get_property(self, name):
        for property_ in self.properties():
            if property_.name == name:
                return property_

    def get_operation(self, name):
        for operation in self.operations():
            if operation.name == name:
                return operation

    def at_context(self):
        options_body = json.loads(self.response().get('body'))

        return options_body.get('@context')

    def at_id(self):
        options_body = json.loads(self.response().get('body'))

        return options_body.get('@id')

    def at_type(self):
        options_body = json.loads(self.response().get('body'))

        return options_body.get('@type')

    @staticmethod
    def _extract_supported_operations(json_options):
        if SUPPORTED_OPERATION_VOCAB not in json_options:
            return []

        json_supported_oper = json_options[SUPPORTED_OPERATION_VOCAB]

        order_by_name = lambda prop: prop.name
        return_array = [SupportedOperation(**elem) for elem in json_supported_oper]
        return_array.sort(key=order_by_name)

        return return_array

    @staticmethod
    def _extract_supported_properties(json_options):
        if SUPPORTED_PROPERTY_VOCAB not in json_options:
            return []

        json_supported_prop = json_options.get(SUPPORTED_PROPERTY_VOCAB)
        at_context = json_options.get('@context')

        order_by_name = lambda prop: prop.name
        return_array = [SupportedProperty(at_context, **elem) for elem in json_supported_prop]
        return_array.sort(key=order_by_name)

        return return_array


from IBGEVisualizer.modules.pyld import jsonld

class JsonLdParser:
    def __init__(self, iri):
        jsonld.set_document_loader(jsonld.hyper_requests_document_loader())

        self.data = self.parse(iri)

    def parse(self, iri):
        print(jsonld.expand(iri))
        return {}

