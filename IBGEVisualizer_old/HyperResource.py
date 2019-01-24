
# coding: utf-8

import os
import re
import copy
import json

import Utils
import request


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


def url_exists(url):
    reply = request_head(url)
    response = reply.response()
    return 200 <= response.get('status_code') < 300, response

def is_entry_point(response):
    if 200 <= response.get('status_code') < 300:
        link_tab = response.get('headers').get('link')

        if link_tab:
            return link_tab.find('rel="http://schema.org/EntryPoint"') >= 0 \
                or link_tab.find('rel="https://schema.org/EntryPoint"') >= 0

    return False


def translate_get(response):
    return response

def translate_options(response, url=''):
    body = response.get('body')
    headers = response.get('headers')

    link_tab = headers.get('link') or ''

    try:
        json_data = json.loads(body)

        fields = _get_fields(json_data.get('@context'))

        # text_url = url if url.endswith('/') else url + '/'
        resources = copy.copy(json_data.get('@context').keys())
        resources = [path.replace(' ', '-') for path in resources]
        resources = [path if path.endswith('/') else path + '/' for path in resources]
        # resources = [text_url + path for path in resources]

        if 'hydra:supportedProperties' in json_data:
            supported_properties = [SupportedProperty(**data) for data in json_data['hydra:supportedProperties']]
            supported_properties.sort(key=lambda prop: prop.name)
        else:
            supported_properties = None

        if 'hydra:supportedOperations' in json_data:
            supported_operations = [SupportedOperation(**data) for data in json_data['hydra:supportedOperations']]
            supported_operations.sort(key=lambda oper: oper.name)
        else:
            supported_operations = None

        r = {
            'url': url,
            'fields': fields,
            'attributes': sorted(resources),
            'supported_properties': supported_properties,
            'supported_operations': supported_operations
        }

    except ValueError:
        return

    return r

def _get_fields(context):
    if context is None:
        return {}

    output = {}

    switch = {
        u"http://schema.org/Integer": int,
        u"http://schema.org/Text": unicode,
        u"http://schema.org/Float": float,
        u"http://schema.org/Boolean": bool,
        u"http://geojson.org/geojson-ld/vocab.html#geometry": u'geometria',
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

# Hyper Object é um objeto que reune o output do get e do options
def create_hyper_object(get_reply, options_reply, url=''):
    return HyperObject(translate_get(get_reply), translate_options(options_reply, url))


class HyperObject(object):
    def __init__(self, get_obj, options_obj=None):
        self.get_obj = get_obj
        self.options_obj = options_obj

        self.request_header = get_obj.get('headers')
        self.resource = get_obj.get('body')

        if options_obj is not None:
            self.url = options_obj.get('url')
            self.fields = options_obj.get('fields')
            self.supported_properties = options_obj.get('supported_properties')
            self.supported_operations = options_obj.get('supported_operations')


class SupportedProperty(object):
    def __init__(self, **data):
        self.name = data.get('hydra:property') or data.get('name') or ''
        self.is_writeable = data.get('hydra:writeable') or data.get('is_writeable') or False
        self.is_readable = data.get('hydra:readable') or data.get('is_readable') or False
        self.is_required = data.get('hydra:required') or data.get('is_required') or False
        self.is_unique = data.get('isUnique') or data.get('is_unique') or False
        self.is_identifier = data.get('isIdentifier') or data.get('is_identifier') or False
        self.is_external = data.get('isExternal') or data.get('is_external') or False

    def __str__(self):
        return u'<SupportedProperty: "name":{}, "is_writeable":{}, "is_readable":{}, "is_required":{}, "is_unique": {}, "is_identifier": {}, "is_external": {}>' \
                .format(unicode(self.name), str(self.is_writeable), str(self.is_readable), str(self.is_required),
                    str(self.is_unique), str(self.is_identifier), str(self.is_external))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.name == other.name

    def html_formatted(self):
        path = os.path.join(os.path.dirname(__file__), 'gui/supported_property_html_template.html')
        html = open(path).read()

        return html.format(
            name=unicode(self.name),
            is_writeable=str(self.is_writeable),
            is_readable=str(self.is_readable),
            is_required=str(self.is_required),
            is_unique=str(self.is_unique),
            is_identifier=str(self.is_identifier),
            is_external=str(self.is_external))


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

    def html_formatted(self):
        path = os.path.join(os.path.dirname(__file__), 'gui/supported_operation_html_template.html')
        html = open(path).read()

        html_formmated = html.format(
            name=unicode(self.name),
            expects="<br>".join(map(lambda link: u'<a href="{link}">{link}</a>'.format(link=link), self.expects)),
            http_method=str(self.method),
            status_code=str(self.status_code),
            returns=str(self.returns),
            context=str(OperationContext.translate(self.context))
        )

        return html_formmated


class OperationContext:
    @staticmethod
    def translate(url):
        context_path = os.path.join(os.path.dirname(__file__), 'gui/operations_template.html')
        context_html = open(context_path).read()

        context_definition = '---'
        context_params = '---'
        context_return = '---'
        context_example = '---'
        try:
            context = request_get(url)
            #header = context.get('header') or ''

            dic = json.loads(context.get('body'))

            context_definition = dic.get('definition') or '---'
            context_params = dic.get('parameters') or '---'
            context_return = dic.get('return') or '---'
            context_example = dic.get('example') or '---'
        except:
            pass

        return context_html.format(
            definition=context_definition,
            params=context_params,
            returns=context_return,
            example=context_example,
        )


JSON_LD_CONTENT_TYPE = 'application/ld+json'

CONTEXT_LINK = 'http://www.w3.org/ns/json-ld#context'
ENTRY_POINT_LINK = 'https://schema.org/EntryPoint'
STYLESHEET_LINK = 'stylesheet'
METADATA_LINK = 'metadata'

HYDRA_VOCAB = 'hydra:'
SUPPORTED_OPERATION_VOCAB = HYDRA_VOCAB + 'supportedOperations'
SUPPORTED_PROPERTY_VOCAB = HYDRA_VOCAB + 'supportedProperties'

class Resource:
    def __init__(self, iri, name=''):
        self._resource_name = None
        self._resource_iri = None

        self._header = None
        self._get = None
        self._options = None

        self.iri = iri
        self.name = name
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
            self._header = HeaderReader(self.iri)

        return self._header

    def data(self):
        if self._get is None:
            self._get = GetReader(self.iri)

        return self._get.data

    def options(self):
        if self._options is None:
            self._options = OptionsReader(self.iri)

        return self._options

    def is_entry_point(self):
        return self.header().is_entry_point()


class HeaderReader:
    def __init__(self, iri):
        i = iri.strip()
        if not i:
            return

        self.__headers = None

        self.iri = i

    @property
    def headers(self):
        if not self.__headers:
            self.__headers = self._parse(self.iri)

        return self.__headers

    @headers.setter
    def headers(self, val):
        pass

    def field(self, name):
        return self.headers.get(name)

    def _parse(self, iri):
        reply = request_head(iri)
        response = reply.response()

        if 200 > response['status_code'] >= 300:
            raise Exception(u'Acesso à {} retornou {} {}'.format(
                iri, response['status_code'], response['status_phrase']))

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
        return self.field('link')

    def is_entry_point(self):
        return self.link_header().get(ENTRY_POINT_LINK) or False

    def stylesheet_iri(self):
        return self.link_header().get(STYLESHEET_LINK)

    def metadata_iri(self):
        return self.link_header().get(METADATA_LINK)

    def context_iri(self):
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


class GetReader:
    def __init__(self, iri):
        if not iri:
            return

        self.iri = iri

        self.__data = None

    @property
    def data(self):
        if not self.__data:
            self.__data = self._response(self.iri)

            if 200 > self.__data['status_code'] >= 300:
                raise Exception(u'Acesso à {} retornou {} {}'.format(
                    self.iri, self.__data['status_code'], self.__data['status_phrase']))

        return self.__data.get('body')

    @data.setter
    def data(self, val):
        pass

    def _response(self, iri):
        reply = request_get(iri)
        response = reply.response()

        return response
        #return get

class OptionsReader:
    def __init__(self, iri):
        if not iri:
            return

        self.iri = iri

        self._operations = None
        self._properties = None

    def _parse(self, callback):
        response = self._response(self.iri)

        invalid_status_code = 200 > response['status_code'] >= 300
        if invalid_status_code:
            raise Exception(u'Acesso à {} retornou {} {}'.format(
                self.iri, response['status_code'], response['status_phrase']))

        options_body = response.get('body')
        json_opt = json.loads(options_body)

        #TODO passar json_opt por json-ld parser para acesso semântico aos elementos

        return callback(json_opt)

    def operations(self):
        if self._operations is None:
            self._operations = self._parse(self._extract_supported_operations)

        return self._operations

    def properties(self):
        if self._properties is None:
            self._properties = self._parse(self._extract_supported_properties)

        return self._properties

    @staticmethod
    def _extract_supported_operations(json_options):
        if SUPPORTED_OPERATION_VOCAB not in json_options:
            return {}

        json_supported_oper = json_options[SUPPORTED_OPERATION_VOCAB]

        return_array = [SupportedOperation(**elem) for elem in json_supported_oper]
        return_array.sort(key=lambda oper: oper.name)

        return return_array

    @staticmethod
    def _extract_supported_properties(json_options):
        if SUPPORTED_PROPERTY_VOCAB not in json_options:
            return {}

        json_supported_prop = json_options[SUPPORTED_PROPERTY_VOCAB]

        return_array = [SupportedProperty(**elem) for elem in json_supported_prop]
        return_array.sort(key=lambda prop: prop.name)

        return return_array

    def _response(self, iri):
        reply = request_options(iri)
        response = reply.response()

        return response
        #return get

class ContextReader:
    pass


from IBGEVisualizer.modules.pyld import jsonld

class JsonLdParser:
    def __init__(self, iri):
        jsonld.set_document_loader(jsonld.hyper_requests_document_loader())

        self.data = self.parse(iri)

    def parse(self, iri):
        print(jsonld.expand(iri))
        return {}
