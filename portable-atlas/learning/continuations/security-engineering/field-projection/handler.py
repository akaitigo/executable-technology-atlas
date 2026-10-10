"""Atlas: synthetic read authorization followed by explicit response projection."""
from copy import deepcopy


def handle(context, request, fixture, mode):
    if mode not in ('object_only', 'projected'):
        raise ValueError('unsupported experiment mode')
    trace = []

    def result(status, reason, payload=None):
        return {'response': {'status': status, 'reason': reason,
                             'payload': deepcopy(payload)}, 'trace': trace}

    trace.append('request-schema')
    if (type(request) is not dict or
        not {'object_id', 'operation'} <= set(request) or
        not set(request) <= {'object_id', 'operation', 'fields'} or
        type(request['object_id']) is not str or not request['object_id'] or
        type(request['operation']) is not str):
        return result(400, 'invalid-request')
    requested = request.get('fields')
    if 'fields' in request:
        if (type(requested) is not list or not requested or
            any(type(x) is not str for x in requested) or
            len(requested) != len(set(requested)) or
            any(x not in fixture['fields'] for x in requested)):
            return result(400, 'invalid-request')
    trace.append('trusted-context-shape')
    if (type(context) is not dict or
        set(context) != {'actor_id', 'role', 'tenant_id', 'read_grants'} or
        any(type(context[k]) is not str or not context[k]
            for k in ('actor_id', 'role', 'tenant_id')) or
        context['role'] not in fixture['roles'] or
        type(context['read_grants']) is not list or
        any(type(x) is not str for x in context['read_grants'])):
        return result(401, 'untrusted-context')
    trace.append('operation')
    if request['operation'] != 'read':
        return result(403, 'unsupported-operation')
    trace.append('object-lookup')
    record = fixture['records'].get(request['object_id'])
    if record is None:
        return result(404, 'not-found')
    trace.append('tenant')
    if context['tenant_id'] != record['tenant_id']:
        return result(403, 'tenant-mismatch')
    trace.append('read-grant')
    if request['object_id'] not in context['read_grants']:
        return result(403, 'no-grant')
    if mode == 'object_only':
        trace.append('copy-all-fields')
        return result(200, 'ok', record)
    trace.append('field-allowlist')
    allowed = fixture['roles'][context['role']]
    if requested is not None and any(x not in allowed for x in requested):
        return result(403, 'field-forbidden')
    selected = allowed if requested is None else requested
    trace.append('build-selected-response')
    return result(200, 'ok', {k: record[k] for k in fixture['fields'] if k in selected})
