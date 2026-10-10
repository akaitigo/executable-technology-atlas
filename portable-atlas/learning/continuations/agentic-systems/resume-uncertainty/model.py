"""Atlas: recovery sees checkpoint+now only, never observer state or a fault label."""
import copy
import hashlib
import json


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode('ascii')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def exact(value, names):
    if type(value) is not dict or set(value) != set(names):
        raise ValueError('schema keys')


def validate(checkpoint, now):
    exact(checkpoint, ('phase', 'call', 'approval', 'completion'))
    if type(now) is not int or not 0 <= now <= 20:
        raise ValueError('logical time')
    call, approval = checkpoint['call'], checkpoint['approval']
    exact(call, ('actor', 'plan_sha256', 'call_id', 'tool', 'args'))
    exact(call['args'], ('counter_id', 'delta'))
    if call['actor'] != 'alice' or call['call_id'] != 'increment-1' or call['tool'] != 'counter.increment':
        raise ValueError('fixed call')
    if call['args']['counter_id'] != 'toy' or type(call['args']['delta']) is not int or call['args']['delta'] != 1:
        raise ValueError('fixed arguments')
    if type(call['plan_sha256']) is not str or len(call['plan_sha256']) != 64 or any(c not in '0123456789abcdef' for c in call['plan_sha256']):
        raise ValueError('plan digest')
    exact(approval, ('source', 'scope', 'expires_at', 'consumed'))
    if type(approval['consumed']) is not bool or type(approval['expires_at']) is not int or approval['expires_at'] != 10:
        raise ValueError('approval state')
    phase = checkpoint['phase']
    if phase not in ('READY', 'PENDING', 'COMPLETED'):
        raise ValueError('phase')
    if phase == 'READY' and approval['consumed'] or phase != 'READY' and not approval['consumed']:
        raise ValueError('phase-consumption contradiction')
    if phase != 'COMPLETED' and checkpoint['completion'] is not None:
        raise ValueError('unexpected completion')
    if phase == 'COMPLETED':
        completion = checkpoint['completion']
        exact(completion, ('call_sha256', 'operation_id', 'result'))
        if completion['call_sha256'] != digest(call) or completion['operation_id'] != call['call_id']:
            raise ValueError('completion binding')
        if type(completion['result']) is not int or not 1 <= completion['result'] <= 2:
            raise ValueError('completion result')


def resume(checkpoint, now):
    validate(checkpoint, now)
    after = copy.deepcopy(checkpoint)
    approval, call = after['approval'], after['call']
    checks = {'source': approval['source'] == 'external-fixed'}
    for key in ('actor', 'plan_sha256', 'call_id', 'tool', 'args'):
        checks[key] = type(approval['scope']) is dict and approval['scope'].get(key) == call[key]
    answer = {'decision': None, 'known_effect_before': None, 'dispatches': 0, 'result': None,
              'approval_reuse': False, 'scope_checks': checks, 'expiry_check': None,
              'unused_check': None, 'checkpoint_after': after}
    if not all(checks.values()):
        answer.update(decision='REJECT_BINDING', known_effect_before='UNKNOWN')
        return answer
    if after['phase'] == 'COMPLETED':
        answer.update(decision='RETURN_SAVED', known_effect_before='RECORDED_APPLIED', result=after['completion']['result'])
    elif after['phase'] == 'PENDING':
        answer.update(decision='HOLD_UNKNOWN', known_effect_before='UNKNOWN')
    else:
        answer['known_effect_before'] = 'NOT_APPLIED'
        answer['expiry_check'] = now < approval['expires_at']
        answer['unused_check'] = not approval['consumed']
        if not answer['expiry_check']:
            answer['decision'] = 'REJECT_EXPIRED'
        elif not answer['unused_check']:
            answer['decision'] = 'REJECT_CONSUMED'
        else:
            approval['consumed'] = True
            after['phase'] = 'PENDING'
            answer.update(decision='DISPATCH', dispatches=1)
    return answer


def bad_resume_reset_consumed(checkpoint, now):
    """Intentional fault: applies only to the two PENDING examples."""
    validate(checkpoint, now)
    if checkpoint['phase'] != 'PENDING':
        raise ValueError('fault comparison applies to PENDING only')
    forged = copy.deepcopy(checkpoint)
    forged['phase'] = 'READY'
    forged['approval']['consumed'] = False
    out = resume(forged, now)
    out.update(decision='BAD_REDISPATCH', approval_reuse=True,
               known_effect_before='UNKNOWN', fault_reset={'consumed_before': True, 'consumed_forged': False})
    return out
