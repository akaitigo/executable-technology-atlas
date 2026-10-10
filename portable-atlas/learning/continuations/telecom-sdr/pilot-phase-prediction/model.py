"""Atlas: finite receiver; no true channel, payload truth, or case ID is accepted."""
from fractions import Fraction as F


def keys(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError('SCHEMA')


def rational(value):
    if type(value) is not str:
        raise ValueError('TYPE')
    try:
        number = F(value)
    except (ValueError, ZeroDivisionError):
        raise ValueError('RATIONAL') from None
    if str(number) != value:
        raise ValueError('RATIONAL')
    return number


def complex_pair(value, allow_zero=False):
    if type(value) is not list or len(value) != 2:
        raise ValueError('SCHEMA')
    pair = tuple(rational(x) for x in value)
    norm = pair[0] ** 2 + pair[1] ** 2
    if norm != 1 and not (allow_zero and norm == 0):
        raise ValueError('AMPLITUDE')
    return pair


def mul(a, b):
    return a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]


def conj(a):
    return a[0], -a[1]


def encoded(a):
    return [str(a[0]), str(a[1])]


def validate(request, method):
    if type(method) is not str:
        raise ValueError('TYPE')
    if method not in ('hold-latest', 'extrapolate-two'):
        raise ValueError('UNKNOWN_METHOD')
    keys(request, ['known_pilots', 'received_pilots', 'payload_indices', 'received_payload'])
    known = request['known_pilots']
    if type(known) is not list or len(known) != 2:
        raise ValueError('SCHEMA')
    for n, item in enumerate(known):
        keys(item, ['n', 'bit'])
        if type(item['n']) is not int or type(item['bit']) is not int:
            raise ValueError('TYPE')
        if item != {'n': n, 'bit': 0}:
            raise ValueError('FIXED_INPUT')
    indices = request['payload_indices']
    if type(indices) is not list or len(indices) != 4:
        raise ValueError('SCHEMA')
    if any(type(n) is not int for n in indices):
        raise ValueError('TYPE')
    if indices != [2, 3, 4, 5]:
        raise ValueError('FIXED_INPUT')
    pilots, payload = request['received_pilots'], request['received_payload']
    if type(pilots) is not list or len(pilots) != 2 or type(payload) is not list or len(payload) != 4:
        raise ValueError('SCHEMA')
    # All fields are validated before the first demodulation row is made.
    return [complex_pair(x, True) for x in pilots], [complex_pair(x) for x in payload]


def receive(request, method):
    pilots, payload = validate(request, method)
    z0, z1 = pilots  # Both known pilot signs are +1 in this fixed contract.
    uses_rate = method == 'extrapolate-two'
    reason = 'NO_LATEST_PILOT' if z1 == (0, 0) else ('NO_FIRST_PILOT' if uses_rate and z0 == (0, 0) else None)
    rotation = mul(z1, conj(z0)) if uses_rate and reason is None else None
    rows = []
    predicted = z1
    for n, sample in zip(request['payload_indices'], payload):
        if reason is None:
            if uses_rate:
                predicted = mul(predicted, rotation)
            coefficient = conj(predicted)
            corrected = mul(sample, coefficient)
            bit = int(corrected[0] < 0)
            row = {'n': n, 'received': encoded(sample), 'predicted_channel': encoded(predicted),
                   'correction_factor': encoded(coefficient), 'corrected': encoded(corrected), 'bit': bit}
        else:
            row = {'n': n, 'received': encoded(sample), 'predicted_channel': None,
                   'correction_factor': None, 'corrected': None, 'bit': None}
        rows.append(row)
    return {'method': method, 'status': 'decoded' if reason is None else 'not-estimated', 'reason': reason,
            'required_pilot_indices': [0, 1] if uses_rate else [1], 'uses_rate': uses_rate,
            'rotation_estimate': encoded(rotation) if rotation is not None else None,
            'rows': rows, 'decoded_bits': [x['bit'] for x in rows] if reason is None else None,
            'demodulated_count': 4 if reason is None else 0}
