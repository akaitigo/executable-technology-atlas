"""Finite synthetic configuration policies; never reads or mutates os.environ."""
from copy import deepcopy
import re

FIELDS = ('timeout_ms', 'retries', 'flag_enabled', 'rollout_percent')
LAYERS = ('default', 'env-input', 'task-json')
ENV = dict(zip(FIELDS, ('APP_TIMEOUT_MS', 'APP_RETRIES',
                       'APP_FLAG_ENABLED', 'APP_ROLLOUT_PERCENT')))
RANGES = {'timeout_ms': (1, 5000), 'retries': (0, 5),
          'rollout_percent': (0, 100)}


def structure_error(layers):
    """Names and shapes first, without fetching unknown field values."""
    def error(layer, source, reason):
        return {'layer': layer, 'source_field': source,
                'field': None, 'reason': reason}
    if type(layers) is not dict or set(layers) != set(LAYERS):
        return error('request', None, 'layers-required')
    for name in LAYERS:
        values = layers[name]
        if type(values) is not dict:
            return error(name, None, 'layer-object-required')
        if any(type(key) is not str for key in values):
            return error(name, None, 'field-name-required')
        allowed = set(ENV.values()) if name == 'env-input' else set(FIELDS)
        unknown = sorted(set(values) - allowed)
        if unknown:
            return error(name, unknown[0], 'unknown-field')
        if name == 'default' and set(values) != set(FIELDS):
            return error(name, None, 'default-fields-required')
    return None


def parse_value(layer, field, raw):
    value = raw
    if layer == 'env-input':
        if type(raw) is not str:
            raise ValueError('env-string-required')
        if field == 'flag_enabled':
            if raw not in ('true', 'false'):
                raise ValueError('strict-boolean-required')
            value = raw == 'true'
        else:
            if re.fullmatch(r'-?(?:0|[1-9][0-9]*)', raw) is None:
                raise ValueError('integer-string-required')
            value = int(raw)
    if field == 'flag_enabled':
        if type(value) is not bool:
            raise ValueError('boolean-required')
    else:
        if type(value) is not int:
            raise ValueError('integer-required')
        low, high = RANGES[field]
        if not low <= value <= high:
            raise ValueError('range')
    return value


def evaluate(case_id, layers, policy):
    if policy not in ('all-layer', 'winning-only'):
        raise ValueError('unsupported-policy')
    state = {'parse_attempts': [], 'candidate': None,
             'config': None, 'provenance': None, 'error': None}
    events = []

    def emit(action, metadata=None):
        meta = {key: None for key in ('layer', 'source_field', 'field', 'reason')}
        if metadata is not None:
            meta = {key: metadata[key] for key in meta}
        events.append({'index': len(events), 'action': action,
                       **deepcopy(meta), **deepcopy(state)})

    def finish():
        error = state['error']
        return {'case_id': case_id, 'policy': policy,
                'decision': 'refused' if error else 'accepted',
                'reason': error['reason'] if error else 'resolved',
                'config': deepcopy(state['config']),
                'provenance': deepcopy(state['provenance']),
                'diagnostic': {key: deepcopy(state[key]) for key in
                               ('parse_attempts', 'candidate', 'error')},
                'events': events}

    def attempt(layer, source, field, raw):
        typed, reason = None, 'ok'
        try:
            typed = parse_value(layer, field, raw)
        except ValueError as exc:
            reason = str(exc)
        item = {'layer': layer, 'source_field': source, 'field': field,
                'raw': deepcopy(raw), 'typed': typed, 'reason': reason}
        state['parse_attempts'].append(item)
        if reason != 'ok':
            state['error'] = {key: item[key] for key in
                              ('layer', 'source_field', 'field', 'reason')}
            emit('PARSE_REJECT', item)
            emit('REFUSE')
            return False
        emit('PARSE_OK', item)
        return True

    emit('START')
    state['error'] = structure_error(layers)
    if state['error']:
        emit('STRUCTURE_REJECT', state['error'])
        emit('REFUSE')
        return finish()
    emit('STRUCTURE_OK')
    if policy == 'all-layer':
        for layer in LAYERS:
            for field in FIELDS:
                source = ENV[field] if layer == 'env-input' else field
                if source in layers[layer]:
                    if not attempt(layer, source, field, layers[layer][source]):
                        return finish()
        chosen = {}
        for item in state['parse_attempts']:
            chosen[item['field']] = {key: deepcopy(item[key]) for key in
                                     ('layer', 'source_field', 'raw', 'typed')}
        state['candidate'] = chosen
        emit('MERGE_TYPED')
    else:
        chosen = {}
        for layer in LAYERS:
            for field in FIELDS:
                source = ENV[field] if layer == 'env-input' else field
                if source in layers[layer]:
                    chosen[field] = {'layer': layer, 'source_field': source,
                                     'raw': deepcopy(layers[layer][source])}
        state['candidate'] = chosen
        emit('MERGE_RAW')
        for field in FIELDS:
            item = chosen[field]
            if not attempt(item['layer'], item['source_field'], field, item['raw']):
                return finish()
    # Only reaching this point publishes a usable configuration.
    resolved = {}
    for item in state['parse_attempts']:
        resolved[item['field']] = {key: deepcopy(item[key]) for key in
                                  ('layer', 'source_field', 'raw', 'typed')}
    state['config'] = {field: resolved[field]['typed'] for field in FIELDS}
    state['provenance'] = {field: resolved[field] for field in FIELDS}
    emit('COMMIT')
    return finish()
