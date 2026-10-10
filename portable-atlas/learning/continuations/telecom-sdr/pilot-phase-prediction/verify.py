"""Atlas: read saved results with a binomial and dot-product oracle; never import the receiver."""
import argparse
import copy
import hashlib
import json
from fractions import Fraction as F
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def power_from_binomial(j):
    values = [sum(F(comb(j, k) * 3 ** (j - k) * 4 ** k * (-1) ** (k // 2), 5 ** j)
                  for k in range(parity, j + 1, 2)) for parity in [0, 1]]
    return values


def pair(value):
    return [F(x) for x in value]


def check(result):
    hand = json.loads((ROOT / 'hand-oracle.json').read_text())
    fixture = json.loads((ROOT / 'fixtures.json').read_text())
    truth = json.loads((ROOT / 'comparison-truth.json').read_text())
    assert type(result['schema']) is int and result['schema'] == 1 and result['status'] == 'observed'
    assert type(result['priority_observed']) is int and result['priority_observed'] == 10
    assert result['fixture_sha256'] == sha(ROOT / 'fixtures.json')
    assert result['comparison_truth_sha256'] == sha(ROOT / 'comparison-truth.json')
    assert canonical(result['scope']) == canonical({'model_only': True, 'exact_rational': True,
        'real_device_runs': 0, 'rf_samples': 0, 'matlab_runs': 0, 'pll_implemented': False,
        'random_draws': 0, 'network_requests': 0, 'browser_executed': False, 'server_started': False})
    assert canonical(result['cases']) == canonical(hand['cases'])
    for j, expected in enumerate(hand['powers_r']):
        assert [str(x) for x in power_from_binomial(j)] == expected
    for case, inp, answer in zip(result['cases'], fixture['cases'], truth['cases']):
        for method in case['methods']:
            rec, comparison = method['receiver'], method['comparison']
            missed = case['id'] == 'first-pilot-missing' and rec['method'] == 'extrapolate-two'
            errors = []
            for j, row in enumerate(rec['rows']):
                n = j + 2
                assert row['n'] == n and row['received'] == inp['request']['received_payload'][j]
                h = pair(answer['channel'][n]); sign = 1 - 2 * answer['payload_bits'][j]
                assert pair(row['received']) == [sign * h[0], sign * h[1]]
                if missed:
                    assert all(row[k] is None for k in ['predicted_channel', 'correction_factor', 'corrected', 'bit'])
                    continue
                exponent = 0 if case['id'] == 'constant-phase' else (1 if rec['method'] == 'hold-latest' else n)
                c, d = power_from_binomial(exponent)
                assert pair(row['predicted_channel']) == [c, d]
                assert pair(row['correction_factor']) == [c, -d]
                a, b = pair(row['received']); corrected = [a * c + b * d, b * c - a * d]
                assert pair(row['corrected']) == corrected
                bit = 1 if corrected[0] < 0 else 0
                assert type(row['bit']) is int and row['bit'] == bit
                if bit != answer['payload_bits'][j]: errors.append(n)
            assert comparison['errors'] == (None if missed else len(errors))
            assert comparison['error_indices'] == (None if missed else errors)
            assert comparison['compared_bits'] == (0 if missed else 4)
    reasons = [('missing-field','SCHEMA'),('extra-truth','SCHEMA'),('extra-case-id','SCHEMA'),
        ('pilot-bit-bool','TYPE'),('pilot-bit-one','FIXED_INPUT'),('pilot-index-float','TYPE'),
        ('pilot-gap','FIXED_INPUT'),('short-pilots','SCHEMA'),('short-payload','SCHEMA'),
        ('payload-index-bool','TYPE'),('payload-index-order','FIXED_INPUT'),('fraction-float','TYPE'),
        ('fraction-noncanonical','RATIONAL'),('fraction-zero-denominator','RATIONAL'),('fraction-nan','RATIONAL'),
        ('pilot-not-unit','AMPLITUDE'),('payload-zero','AMPLITUDE'),('unknown-method','UNKNOWN_METHOD')]
    assert canonical(result['input_refusals']) == canonical([{'id': name,'status':'INPUT_REFUSED',
        'reason': reason,'demodulated_count':0,'rows':[],'value':None} for name,reason in reasons])
    return {'cases': 4, 'methods': 8, 'rows': 32, 'decoded_rows': 28, 'not_estimated_rows': 4,
            'compared_bits_total': 28, 'input_refusals': 18}


def mutants(result):
    changes = [
        ('received-sign', lambda r: r['cases'][1]['methods'][0]['receiver']['rows'][1]['received'].__setitem__(0,'-117/125')),
        ('future-channel-fed-to-hold', lambda r: r['cases'][1]['methods'][0]['receiver']['rows'][0].update(predicted_channel=['-7/25','24/25'])),
        ('coefficient-not-conjugate', lambda r: r['cases'][1]['methods'][1]['receiver']['rows'][0]['correction_factor'].__setitem__(1,'24/25')),
        ('corrected-imaginary-sign', lambda r: r['cases'][2]['methods'][1]['receiver']['rows'][2]['corrected'].__setitem__(1,'-24/25')),
        ('bit-from-truth', lambda r: r['cases'][2]['methods'][1]['receiver']['rows'][2].update(bit=1)),
        ('wrong-error-position', lambda r: r['cases'][2]['methods'][1]['comparison'].update(error_indices=[3,4])),
        ('missing-means-zero-errors', lambda r: r['cases'][3]['methods'][1]['comparison'].update(errors=0)),
        ('missing-means-compared-four', lambda r: r['cases'][3]['methods'][1]['comparison'].update(compared_bits=4)),
        ('missing-means-bit-zero', lambda r: r['cases'][3]['methods'][1]['receiver']['rows'][0].update(bit=0)),
        ('rate-estimate-corrupted', lambda r: r['cases'][2]['methods'][1]['receiver'].update(rotation_estimate=['1','0'])),
        ('hold-claims-rate', lambda r: r['cases'][0]['methods'][0]['receiver'].update(uses_rate=True)),
        ('wrong-required-pilot', lambda r: r['cases'][3]['methods'][0]['receiver'].update(required_pilot_indices=[0,1])),
        ('missing-row', lambda r: r['cases'][1]['methods'][1]['receiver']['rows'].pop()),
        ('float-in-rational', lambda r: r['cases'][0]['methods'][0]['receiver']['rows'][0]['corrected'].__setitem__(0,1.0)),
        ('refusal-demodulates', lambda r: r['input_refusals'][0].update(demodulated_count=4)),
        ('real-RF-claim', lambda r: r['scope'].update(rf_samples=6)),
    ]
    rejected = []
    for name, change in changes:
        candidate = copy.deepcopy(result); change(candidate)
        try: check(candidate)
        except (AssertionError, KeyError, TypeError, ValueError): rejected.append(name)
        else: raise AssertionError('changed record accepted: '+name)
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('run'); args = parser.parse_args()
    directory = (ROOT / args.run).resolve(); assert ROOT / 'observations' in directory.parents
    report = json.loads((directory / 'report.json').read_text())
    assert report['status'] == 'observed' and report['child_reaped'] and report['exit_code'] == 0
    assert report['result_sha256'] == sha(directory / 'result.json')
    for name, digest in report['sources'].items(): assert sha(ROOT / name) == digest, name
    for name in ['stdout','stderr']: assert report[name+'_sha256'] == sha(directory/(name+'.txt'))
    for name,digest in json.loads((ROOT/'contract-lock.json').read_text())['files'].items(): assert sha(ROOT/name)==digest,name
    result = json.loads((directory/'result.json').read_text())
    assert canonical(json.loads((directory/'stdout.txt').read_text())) == canonical(result)
    print(json.dumps({'title':'Atlas saved telecom phase verification','passed':True,**check(result),
        'mutation_refusals':mutants(result),'model_rerun':False,'source_sha256':sha(Path(__file__)),'run':args.run}))


if __name__ == '__main__': main()
