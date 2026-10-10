"""Atlas: one covered sample, exact depth versus an explicitly defined integer rule."""
from fractions import Fraction as F

SCOPE = {'model_only': True, 'sample_count': 1, 'gpu_api_calls': 0,
         'hardware_measured': False, 'coverage_recomputed': False, 'network_requests': 0}
CENTRAL = [
    ('same-bin-ab', 3, [('A', '2/5'), ('B', '7/15')]),
    ('same-bin-ba', 3, [('B', '7/15'), ('A', '2/5')]),
    ('separated-ab', 4, [('A', '2/5'), ('B', '7/15')]),
    ('separated-ba', 4, [('B', '7/15'), ('A', '2/5')]),
    ('exact-tie-ab', 3, [('A', '2/5'), ('B', '2/5')]),
    ('exact-tie-ba', 3, [('B', '2/5'), ('A', '2/5')]),
]
BOUNDARIES = [(f'b{b}-{name}', b, [('F', z)]) for b in (3, 4)
              for name, z in [('zero', '0'), ('half-before', '49/100'), ('half', '1/2'),
                              ('half-after', '51/100'), ('clear-bin', '31/32'), ('one', '1')]]


def keys(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError('SCHEMA')


def rational(value):
    if type(value) is not str:
        raise ValueError('TYPE')
    try:
        parsed = F(value)
    except (ValueError, ZeroDivisionError):
        raise ValueError('RATIONAL') from None
    if str(parsed) != value:
        raise ValueError('RATIONAL')
    if not 0 <= parsed <= 1:
        raise ValueError('DEPTH_RANGE')
    return parsed


def validate_fixture(fixture):
    """Validate every field before a fragment is compared or a sample is written."""
    keys(fixture, ['schema_version', 'central', 'boundaries'])
    if type(fixture['schema_version']) is not int:
        raise ValueError('TYPE')
    if fixture['schema_version'] != 1:
        raise ValueError('FIXED_INPUT')
    for group, expected in [('central', CENTRAL), ('boundaries', BOUNDARIES)]:
        rows = fixture[group]
        if type(rows) is not list or len(rows) != len(expected):
            raise ValueError('SCHEMA')
        for item, (case_id, bits, fragments) in zip(rows, expected):
            keys(item, ['id', 'request'])
            if type(item['id']) is not str or item['id'] != case_id:
                raise ValueError('UNKNOWN_CASE')
            request = item['request']; keys(request, ['bits', 'fragments'])
            if type(request['bits']) is not int:
                raise ValueError('TYPE')
            if request['bits'] not in (3, 4):
                raise ValueError('BITS')
            values = request['fragments']
            if type(values) is not list or len(values) != len(fragments):
                raise ValueError('SCHEMA')
            seen = set()
            for fragment, (fragment_id, z) in zip(values, fragments):
                keys(fragment, ['id', 'z'])
                if type(fragment['id']) is not str or fragment['id'] not in ('A', 'B', 'F'):
                    raise ValueError('FRAGMENT_ID')
                if fragment['id'] in seen:
                    raise ValueError('DUPLICATE_FRAGMENT')
                seen.add(fragment['id'])
                rational(fragment['z'])
            # All literal types have already been checked; Python int/float equality is insufficient.
            if request['bits'] != bits or [(v['id'], v['z']) for v in values] != fragments:
                raise ValueError('FIXED_INPUT')


def draw_validated(item):
    request = item['request']; bits = request['bits']; maximum = (1 << bits) - 1
    exact = {'depth': '1', 'winner': None}; quantized = {'code': maximum, 'winner': None}
    trace = []
    for step, fragment in enumerate(request['fragments'], 1):
        z = F(fragment['z']); scaled = maximum * z
        whole, remainder = divmod(scaled.numerator, scaled.denominator)
        code = whole + int(2 * remainder >= scaled.denominator)
        exact_before = dict(exact); quantized_before = dict(quantized)
        exact_pass = z < F(exact['depth']); quantized_pass = code < quantized['code']
        if exact_pass:
            exact = {'depth': str(z), 'winner': fragment['id']}
        if quantized_pass:
            quantized = {'code': code, 'winner': fragment['id']}
        trace.append({'step': step, 'fragment_id': fragment['id'], 'z': str(z),
                      'scaled': str(scaled), 'code': code, 'reconstructed': str(F(code, maximum)),
                      'rounding_error': str(F(code, maximum) - z), 'exact_before': exact_before,
                      'exact_pass': exact_pass, 'exact_after': dict(exact),
                      'quantized_before': quantized_before, 'quantized_pass': quantized_pass,
                      'quantized_after': dict(quantized)})
    return {'id': item['id'], 'bits': bits, 'maximum': maximum, 'trace': trace,
            'exact_final': exact, 'quantized_final': quantized}


def evaluate(fixture):
    validate_fixture(fixture)
    return {'schema_version': 1, 'scope': dict(SCOPE),
            'central': [draw_validated(item) for item in fixture['central']],
            'boundaries': [draw_validated(item) for item in fixture['boundaries']]}
