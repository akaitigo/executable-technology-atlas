"""Atlas: fixed pure read/add calls; typed data and synthetic approval stay separate."""
import copy
import hashlib
import json

SCOPE_KEYS = ('actor', 'plan_sha256', 'call_id', 'tool', 'args')
CHECKS = ('exists', 'origin', 'actor', 'plan', 'call_id', 'tool', 'args', 'time', 'unused')

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)

def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()

def require(value, message):
    if not value:
        raise ValueError(message)

def keys(value, expected, name):
    require(type(value) is dict and set(value) == set(expected), 'Atlas: invalid '+name+' fields')

def integer(value, low, high):
    return type(value) is int and low <= value <= high

def validate_grant(grant):
    if grant is None:
        return
    keys(grant, SCOPE_KEYS + ('expires_at', 'consumed'), 'approval')
    require(grant['actor'] in ('alice', 'bob'), 'Atlas: invalid approval actor')
    require(type(grant['plan_sha256']) is str and len(grant['plan_sha256']) == 64 and
            all(c in '0123456789abcdef' for c in grant['plan_sha256']), 'Atlas: invalid plan digest')
    require(grant['call_id'] in ('add-a', 'add-other') and grant['tool'] == 'add', 'Atlas: invalid approval call')
    keys(grant['args'], ('a', 'b'), 'approval arguments')
    require(all(integer(v, -100, 100) for v in grant['args'].values()), 'Atlas: invalid approval argument')
    require(integer(grant['expires_at'], 0, 20) and type(grant['consumed']) is bool, 'Atlas: invalid approval validity')

def validate(case):
    keys(case, ('id', 'label', 'policy', 'input'), 'case')
    require(type(case['id']) is str and type(case['label']) is str, 'Atlas: invalid case labels')
    require(case['policy'] in ('strict', 'bad-data-approval'), 'Atlas: unsupported policy')
    x = case['input']
    keys(x, ('actor', 'request_id', 'now', 'plan', 'observation', 'approval'), 'input')
    require(x['actor'] in ('alice', 'bob') and x['request_id'] == 'request-1', 'Atlas: invalid actor/request')
    require(integer(x['now'], 0, 20), 'Atlas: invalid logical time')
    plan = x['plan']
    keys(plan, ('version', 'nodes'), 'plan')
    require(plan['version'] in ('plan-v1', 'plan-v2'), 'Atlas: unsupported plan version')
    expected = [
        {'id': 'read-r', 'tool': 'read', 'args': {'key': 'fixed'}},
        {'id': 'add-a', 'tool': 'add', 'args': {'a': {'ref': 'read-r', 'field': 'value', 'type': 'int'}, 'b': {'literal': 3}}},
    ]
    require(plan['nodes'] == expected, 'Atlas: plan schema/tool/reference rejected before read')
    obs = x['observation']
    keys(obs, ('request_id', 'value', 'proposed_approval'), 'observation')
    require(obs['request_id'] in ('request-1', 'request-old'), 'Atlas: unsupported observation request')
    require(type(obs['value']) in (int, str, bool), 'Atlas: unsupported observation value shape')
    validate_grant(obs['proposed_approval'])
    validate_grant(x['approval'])

def execute(case):
    """Execute only the validated fixture read and pure addition; no I/O tools."""
    validate(case)
    x = copy.deepcopy(case['input'])
    source = 'external-fixed' if x['approval'] is not None else None
    grant = x['approval']
    if case['policy'] == 'bad-data-approval':
        source, grant = 'tool-data', x['observation']['proposed_approval']
    before = grant['consumed'] if grant else None
    checks = {key: None for key in CHECKS}
    out = {
        'id': case['id'], 'policy': case['policy'], 'status': 'REJECTED', 'reason': None,
        'stopped_at': None, 'read_calls': 0, 'add_calls': 0, 'final': None,
        'resolved_args': None, 'plan_sha256': digest(x['plan']),
        'actual_call_canonical': None, 'actual_call_sha256': None,
        'approved_call_canonical': canonical({k: grant[k] for k in SCOPE_KEYS}) if grant else None,
        'approved_call_sha256': digest({k: grant[k] for k in SCOPE_KEYS}) if grant else None,
        'approval_source': source, 'consumed_before': before, 'consumed_after': before,
        'authorized': False, 'authority_breach': False, 'authorization_reached': False,
        'checks': checks, 'calls': [], 'trace': [],
        'now': x['now'], 'expires_at': grant['expires_at'] if grant else None,
        'observation_request': x['observation']['request_id'], 'current_request': x['request_id'],
    }
    def event(stage, state, data):
        out['trace'].append({'step': len(out['trace']) + 1, 'stage': stage, 'state': state,
                             'read_calls': out['read_calls'], 'add_calls': out['add_calls'], 'data': data})
        out['stopped_at'] = stage
    def reject(stage, reason):
        out['reason'] = reason
        event(stage, 'rejected', {'reason': reason})
        return out

    event('preflight', 'passed', {'tools': ['read', 'add'], 'plan_sha256': out['plan_sha256']})
    observation = copy.deepcopy(x['observation'])
    out['calls'].append({'call_id': 'read-r', 'tool': 'read', 'args': {'key': 'fixed'}, 'result': observation})
    out['read_calls'] = 1
    event('read', 'completed', {'observation': observation, 'fixed_read_permission': True})
    if observation['request_id'] != x['request_id']:
        return reject('binding', 'STALE_OBSERVATION')
    if not integer(observation['value'], -100, 100):
        return reject('binding', 'TYPED_INT')
    args = {'a': observation['value'], 'b': 3}
    actual = {'actor': x['actor'], 'plan_sha256': out['plan_sha256'], 'call_id': 'add-a', 'tool': 'add', 'args': args}
    out.update(resolved_args=args, actual_call_canonical=canonical(actual), actual_call_sha256=digest(actual))
    event('binding', 'passed', {'args': args, 'request_id': observation['request_id'], 'type': 'int'})
    out['authorization_reached'] = True
    checks['exists'] = grant is not None
    if grant is None:
        return reject('authorize', 'NO_APPROVAL')
    checks['origin'] = source == 'external-fixed'
    # The intentionally faulty policy skips only the trusted-origin requirement.
    for name, ok, reason in [
        ('actor', actual['actor'] == grant['actor'], 'ACTOR_MISMATCH'),
        ('plan', actual['plan_sha256'] == grant['plan_sha256'], 'PLAN_MISMATCH'),
        ('call_id', actual['call_id'] == grant['call_id'], 'CALL_MISMATCH'),
        ('tool', actual['tool'] == grant['tool'], 'TOOL_MISMATCH'),
        ('args', actual['args'] == grant['args'], 'ARGS_MISMATCH'),
        ('time', x['now'] < grant['expires_at'], 'EXPIRED'),
        ('unused', grant['consumed'] is False, 'CONSUMED'),
    ]:
        checks[name] = ok
        if not ok:
            return reject('authorize', reason)
    out['authorized'] = source == 'external-fixed'
    out['authority_breach'] = not out['authorized']
    grant['consumed'] = True
    out['consumed_after'] = True
    event('authorize', 'passed' if out['authorized'] else 'fault-promoted',
          {'source': source, 'authorized': out['authorized'], 'consumed': True, 'checks': copy.deepcopy(checks)})
    result = args['a'] + args['b']
    out['calls'].append({'call_id': 'add-a', 'tool': 'add', 'args': args, 'result': result})
    out.update(add_calls=1, final=result, status='COMPLETED' if out['authorized'] else 'BAD_COMPLETED')
    event('dispatch', 'completed', {'result': result, 'authorized': out['authorized']})
    return out
