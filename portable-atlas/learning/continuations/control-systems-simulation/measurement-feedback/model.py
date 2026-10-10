"""Atlas: four finite measurement paths, one fixed discrete plant; no real device."""
from fractions import Fraction

FIXTURE = {
    'title': 'Atlas fixed measurement feedback inputs', 'schema': 1,
    'unit': 'synthetic dimensionless', 'time_unit': 'one virtual sample',
    'updates': 6, 'plant_a': '1/2', 'plant_b': '1/2', 'reference': '1',
    'gain': '1', 'initial_state': '0', 'initial_history': '0',
    'quantization_rule': 'nearest-ties-away-from-zero',
    'cases': [
        {'id': 'current-exact', 'delay_samples': 0, 'noise': ['0'] * 7, 'quantization_step': None},
        {'id': 'delayed-one', 'delay_samples': 1, 'noise': ['0'] * 7, 'quantization_step': None},
        {'id': 'fixed-noise', 'delay_samples': 0,
         'noise': ['1/4', '-1/4', '1/4', '-1/4', '1/4', '-1/4', '1/4'], 'quantization_step': None},
        {'id': 'quantized-unit', 'delay_samples': 0, 'noise': ['0'] * 7, 'quantization_step': '1'},
    ],
}


def require_fixed(actual, expected):
    if type(actual) is not type(expected):
        raise ValueError('TYPE')
    if isinstance(expected, dict):
        if set(actual) != set(expected):
            raise ValueError('SCHEMA')
        for key in expected:
            require_fixed(actual[key], expected[key])
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError('SCHEMA')
        for value, fixed in zip(actual, expected):
            require_fixed(value, fixed)
    elif actual != expected:
        raise ValueError('FIXED_INPUT')


def quantize(value):
    """Exact nearest integer; either signed half moves away from zero."""
    magnitude = abs(value)
    rounded = (2 * magnitude.numerator + magnitude.denominator) // (2 * magnitude.denominator)
    return Fraction(-rounded if value < 0 else rounded)


def execute(fixture, case_id):
    require_fixed(fixture, FIXTURE)  # Validate every input before any state update.
    if type(case_id) is not str or case_id not in [x['id'] for x in FIXTURE['cases']]:
        raise ValueError('UNKNOWN_CASE')
    case = next(x for x in fixture['cases'] if x['id'] == case_id)
    a, b = Fraction(fixture['plant_a']), Fraction(fixture['plant_b'])
    reference, gain = Fraction(fixture['reference']), Fraction(fixture['gain'])
    history = {-1: Fraction(fixture['initial_history']), 0: Fraction(fixture['initial_state'])}
    rows = []
    for k in range(fixture['updates'] + 1):
        state = history[k]
        source_index = k - case['delay_samples']
        source = history[source_index]
        noise = Fraction(case['noise'][k])
        before = source + noise
        measured = quantize(before) if case['quantization_step'] is not None else before
        error = reference - measured
        control = gain * error
        applied = k < fixture['updates']
        next_state = a * state + b * control if applied else None
        rows.append({'k': k, 'true_state': str(state), 'source_index': source_index,
                     'source_value': str(source), 'noise': str(noise),
                     'before_quantization': str(before), 'measurement': str(measured),
                     'measurement_error': str(measured - state), 'true_error': str(reference - state),
                     'control_error': str(error), 'control_input': str(control),
                     'input_applied': applied, 'next_state': str(next_state) if applied else None})
        if applied:
            history[k + 1] = next_state
    return {'id': case_id, 'updates': fixture['updates'], 'boundaries': rows,
            'final_state': str(history[fixture['updates']])}
