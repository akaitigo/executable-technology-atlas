#!/usr/bin/env python3
"""Atlas: calculate finite bit-flip cases; writes only with explicit --record."""
import argparse
import datetime
import hashlib
import itertools
import json
from pathlib import Path
import platform
import shutil
import sys
import time

from codec import encode, decode7, decode8, flip_positions

ROOT = Path(__file__).resolve().parent
INPUTS = ('expected.json', 'codec.py', 'oracle.py', 'run.py', 'verify.py')


def case(scheme, message, errors, category):
    sent = encode(message, scheme)
    received = flip_positions(sent, errors)
    # The decoder is given received bits only. Truth belongs to this experiment.
    decoded = (decode8 if scheme == 'secded8' else decode7)(received)
    match = None if decoded['decoded'] is None else decoded['decoded'] == message
    return {'id': scheme + '/' + message + '/' + (','.join(map(str, errors)) or '-'),
            'scheme': scheme, 'message': message, 'errors': list(errors), 'sent': sent,
            'category': category, 'decoder': decoded,
            'answerCheck': {'matchesOriginal': match, 'comparisonOwner': 'experiment_only'}}


def calculate():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    tick = time.monotonic()
    rows = []
    for scheme, length in (('hamming7', 7), ('secded8', 8)):
        for number in range(16):
            message = f'{number:04b}'
            for weight in range(3):
                for errors in itertools.combinations(range(1, length + 1), weight):
                    rows.append(case(scheme, message, errors, 'zero_one_two_bits'))
    outside = [case('secded8', '0000', e, 'outside_guarantee_example')
               for e in ((1, 2, 3), (1, 2, 3, 8))]
    return {'kind': 'Atlas deterministic finite bit-flip model',
            'executionStatus': 'completed', 'realChannelOrHardware': False,
            'startedAt': started, 'finishedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'elapsedSeconds': round(time.monotonic() - tick, 6),
            'python': platform.python_version(), 'platform': platform.platform(),
            'mainCaseCount': len(rows), 'rows': rows, 'outsideGuaranteeExamples': outside,
            'decoderInputs': 'received word only; original message and error positions are withheld',
            'outsideGuaranteeNote': 'Only these two 3/4-bit examples are recorded; no higher-error guarantee.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path)
    args = parser.parse_args()
    result = calculate()
    if args.record:
        destination = args.record.resolve()
        if ROOT not in destination.parents:
            parser.error('record directory must be inside this lesson')
        destination.mkdir(parents=True, exist_ok=False)
        inputs = destination / 'inputs'; inputs.mkdir()
        hashes = {}
        for name in INPUTS:
            hashes[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            shutil.copyfile(ROOT / name, inputs / name)
        result['inputSha256'] = hashes
        (destination / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        if any(hashlib.sha256((ROOT / n).read_bytes()).hexdigest() != digest for n, digest in hashes.items()):
            raise RuntimeError('inputs changed during calculation')
    print(json.dumps({'Atlas': 'SECDED calculation', 'recorded': bool(args.record),
                      'mainCaseCount': result['mainCaseCount'],
                      'outsideGuaranteeExampleCount': len(result['outsideGuaranteeExamples']),
                      'elapsedSeconds': result['elapsedSeconds'],
                      'independentVerification': 'separate verify.py step'}, indent=2))


if __name__ == '__main__':
    main()
