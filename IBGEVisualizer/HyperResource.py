
# -*- coding: utf-8 -*-

import request


def request_get(url):
    return request.get(url)

    
def request_options(url):
    return request.options(url)
    
    
def request_head(url):
    return request.head(url)


def url_exists(url):
    reply = request_head(url)
    response = reply.response()

    return 200 <= response.get('status_code') < 300


import json, copy, os

def translate_get(response):
    return response

def translate_options(response, url=''):
    body = response.get('body')
    header = response.get('header')

    link_tab = header.get('link') or ''

    entry_point = _get_entry_point_from_link(link_tab)

    try:
        json_data = json.loads(body)

        fields = _get_fields(json_data.get('@context'))

        # text_url = url if url.endswith('/') else url + '/'
        resources = copy.copy(json_data.get('@context').keys())
        resources = [path.replace(' ', '-') for path in resources]
        resources = [path if path.endswith('/') else path + '/' for path in resources]
        # resources = [text_url + path for path in resources]

        # Se url igual entry_point, criar fake Supported Property
        if url == entry_point or url + '/' == entry_point:
            supported_properties = [SupportedProperty(name=name) for name in resources]
            supported_properties.sort(key=lambda prop: prop.name)
            supported_operations = None
        else:
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
            'entry_point': entry_point,
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
        "http://schema.org/Integer": int,
        "http://schema.org/Text": unicode,
        "http://schema.org/Float": float,
        "http://schema.org/Boolean": bool
    }

    for k, v in context.items():
        output.update({
            k: switch.get(v['@type']) or unicode
        })

    return output

def _get_entry_point_from_link(link_tab):
    if not link_tab:
        return ''

    import re
    entry_point = re.search(r'^<.+?>', link_tab).group(0).strip('<>')

    return entry_point

# Hyper Object é uma objeto que reune o output do get e do options
# em um objeto só, dando mais sentido ao recurso
def create_hyper_object(get_reply, options_reply, url=''):
    return HyperObject(translate_get(get_reply), translate_options(options_reply, url))


class HyperObject(object):
    def __init__(self, get_obj, options_obj=None):
        self.get_obj = get_obj
        self.options_obj = options_obj

        self.request_header = get_obj.get('header')
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

import json

class OperationContext:
    @staticmethod
    def translate(url):
        context_path = os.path.join(os.path.dirname(__file__), 'gui/operations_template.html')
        context_html = open(context_path).read()

        # Tentando interpretar link do contexto
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