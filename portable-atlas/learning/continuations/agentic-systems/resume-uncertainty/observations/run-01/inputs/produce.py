"""Atlas: static producer preparation. No CLI entry or external effect is provided."""
import copy
import hashlib
import json
from pathlib import Path
from model import resume, bad_resume_reset_consumed, canonical, digest

ROOT = Path(__file__).resolve().parent


def finish_in_observer(decision, effect_before):
    """Only this driver sees the separate synthetic effect count."""
    out = copy.deepcopy(decision)
    effect_after = effect_before
    if out['dispatches']:
        effect_after += 1
        out['result'] = effect_after
        checkpoint = out['checkpoint_after']
        checkpoint['phase'] = 'COMPLETED'
        checkpoint['completion'] = {'call_sha256': digest(checkpoint['call']),
                                    'operation_id': checkpoint['call']['call_id'], 'result': effect_after}
    return {'resume_output': decision, 'observer': {'effect_before': effect_before, 'effect_after': effect_after},
            'final': out}


def collect():
    """A future bounded runner may call once, after independent review and a slot."""
    fixture = json.loads((ROOT/'cases.json').read_text())
    records = []
    for case in fixture['cases']:
        data = (ROOT/case['resume_input']).read_bytes()
        arguments = json.loads(data)
        before = copy.deepcopy(arguments)
        checkpoint, now = arguments['checkpoint'], arguments['now']
        # No case label, cut point, effect count, or observer callback crosses this call.
        strict = resume(checkpoint, now)
        record = {'id': case['id'], 'resume_input_bytes': data.decode('ascii'),
                  'resume_input_sha256': hashlib.sha256(data).hexdigest(),
                  'input_before': before, 'input_after': arguments,
                  'strict': finish_in_observer(strict, case['observer_effect_before'])}
        if case['id'] in fixture['fault_cases']:
            bad = bad_resume_reset_consumed(checkpoint, now)
            record['fault'] = finish_in_observer(bad, case['observer_effect_before'])
        records.append(record)
    return {'Atlas': '有限な再開判断と、別のobserverの合成効果', 'kind': 'synthetic_not_real_restart', 'cases': records}
