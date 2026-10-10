"""Public fictional keys only. Not a production token protocol."""
import hashlib
import hmac
import json

KEYS = {'v1': b'PUBLIC-FICTIONAL-DUMMY-v1', 'v2': b'PUBLIC-FICTIONAL-DUMMY-v2'}
POLICY = {'initial': ('v1', {'v1'}), 'overlap': ('v2', {'v1', 'v2'}), 'revoked': ('v2', {'v2'})}

def encoded(body):
    return json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()

def issue(version='v1', payload='demo', expires=110):
    if version not in KEYS or not isinstance(payload, str) or not 1 <= len(payload) <= 80 or type(expires) is not int or not 0 <= expires <= 1000000:
        raise ValueError('input')
    body = {'version': version, 'payload': payload, 'expires': expires}
    return dict(body, mac=hmac.new(KEYS[version], encoded(body), hashlib.sha256).hexdigest())

def verify(token, phase='overlap', now=100):
    if phase not in POLICY or type(now) is not int or now < 0:
        raise ValueError('input')
    if not isinstance(token, dict) or set(token) != {'version', 'payload', 'expires', 'mac'}:
        return {'result': 'input'}
    version, payload, expires, mac = (token[k] for k in ('version', 'payload', 'expires', 'mac'))
    if not isinstance(version, str) or not isinstance(payload, str) or not 1 <= len(payload) <= 80 or type(expires) is not int or not 0 <= expires <= 1000000 or not isinstance(mac, str) or len(mac) != 64 or any(c not in '0123456789abcdef' for c in mac):
        return {'result': 'input'}
    if version not in KEYS:
        return {'result': 'unknown-key', 'version': version}
    body = {k: token[k] for k in ('version', 'payload', 'expires')}
    expected = hmac.new(KEYS[version], encoded(body), hashlib.sha256).hexdigest()
    trace = {'version': version, 'canonical': encoded(body).decode(), 'receivedMAC': mac, 'computedMAC': expected, 'macMatches': hmac.compare_digest(mac, expected), 'phase': phase, 'now': now, 'expires': expires, 'authorized': version in POLICY[phase][1]}
    result = 'revoked' if not trace['authorized'] else 'tamper' if not trace['macMatches'] else 'expired' if now >= expires else 'accept'
    return dict(trace, result=result)

def experiment(phase='overlap', version='v1', now=100, fault='none'):
    if fault not in {'none', 'tamper', 'unknown', 'input'}:
        raise ValueError('input')
    token = issue(version)
    if fault == 'tamper': token['payload'] = 'changed'
    if fault == 'unknown': token['version'] = 'v9'
    if fault == 'input': token['expires'] = True
    return {'input': {'phase': phase, 'version': version, 'now': now, 'fault': fault}, 'token': token, 'trace': verify(token, phase, now), 'issuer': POLICY[phase][0]}
