
# coding: utf-8

from IBGEVisualizer.HyperResource import Resource

_resource_set = dict()

def load(iri, name=''):
    i = iri.strip()
    if not i:
        raise ValueError(u'iri com valor vazio')

    if i in _resource_set:
        resource = _resource_set[i]

    else:
        resource = Resource(i, name)

        if resource:
            _resource_set.update({i:resource})

    return resource
