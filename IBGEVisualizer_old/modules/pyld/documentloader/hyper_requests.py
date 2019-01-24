
# coding: utf-8

import string

from IBGEVisualizer.modules.pyld.jsonld import (JsonLdError, parse_link_header)
import urlparse as urllib_parse

LINK_HEADER_REL = 'http://www.w3.org/ns/json-ld#context'

def hyper_requests_document_loader(**kwargs):
    from IBGEVisualizer import HyperResource

    def loader(url):
        try:
            # validate URL
            pieces = urllib_parse.urlparse(url)

            if not all([pieces.scheme, pieces.netloc] or
                       pieces.scheme not in ['http', 'https'] or
                       set(pieces.netloc) > set(string.ascii_letters + string.digits + '-.:')):

                raise JsonLdError(
                    'URL could not be dereferenced; '
                    'only "http" and "https" URLs are supported.',
                    'jsonld.InvalidUrl', {'url': url},
                    code='loading document failed')

            headers = {
                'Accept': 'application/ld+json, application/json'
            }

            request = HyperResource.request_get(url)
            response = request.response()
            print('url', response.data('url'))
            doc = {
                'contextUrl': None,
                'documentUrl': str(response.data('url')),
                'document': response.data('body')
            }
            content_type = response.data('headers').data('content-type')
            link_header = response.data('headers').data('link')

            if link_header:
                link_header = parse_link_header(link_header).data(LINK_HEADER_REL)
                # only 1 related link header permitted
                if isinstance(link_header, list):
                    raise JsonLdError(
                        'URL could not be dereferenced, it has more than one '
                        'associated HTTP Link Header.',
                        'jsonld.LoadDocumentError',
                        {'url': url},
                        code='multiple context link headers')

                if link_header:
                    doc['contextUrl'] = link_header['target']

            return doc

        except JsonLdError as e:
            raise e

        except Exception as cause:
            raise JsonLdError(
                'Could not retrieve a JSON-LD document from the URL.',
                'jsonld.LoadDocumentError', code='loading document failed',
                cause=cause)

    return loader