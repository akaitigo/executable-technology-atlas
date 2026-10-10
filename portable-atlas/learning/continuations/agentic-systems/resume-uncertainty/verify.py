"""Atlas: saved-output comparison only; producer/model are not imported."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def check(result):
    fixture = json.loads((ROOT/'cases.json').read_text())
    expected = json.loads((ROOT/'expected.json').read_text())
    plan = json.loads((ROOT/'plan.json').read_text())
    def independent_digest(value):
        return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode('ascii')).hexdigest()
    count = 0
    def eq(actual, wanted):
        nonlocal count
        count += 1
        assert actual == wanted, (actual, wanted)
    eq([c['id'] for c in result['cases']], [c['id'] for c in fixture['cases']])
    for saved, case in zip(result['cases'], fixture['cases']):
        data = (ROOT/case['resume_input']).read_bytes()
        arguments = json.loads(data)
        eq(arguments['checkpoint']['call']['plan_sha256'], independent_digest(plan))
        eq(saved['resume_input_bytes'], data.decode('ascii'))
        eq(saved['resume_input_sha256'], hashlib.sha256(data).hexdigest())
        eq(saved['input_before'], arguments)
        eq(saved['input_after'], arguments)
        eq(set(saved)-{'fault'}, {'id','resume_input_bytes','resume_input_sha256','input_before','input_after','strict'})
        for policy in ['strict'] + (['fault'] if case['id'] in fixture['fault_cases'] else []):
            block = saved[policy]
            wanted = expected['strict' if policy == 'strict' else 'fault_reset_consumed'][case['id']]
            for key in ['decision','dispatches','result']:
                eq(block['final'][key], wanted[key])
            eq(block['observer']['effect_before'], case['observer_effect_before'])
            eq(block['observer']['effect_after'], wanted['effect_after'])
            eq(block['final']['approval_reuse'], policy == 'fault')
            eq(all(block['resume_output']['scope_checks'].values()), True)
            eq(set(block['resume_output']) & {'observer','case','id','effect_before','effect_after','fault_position'}, set())
            if policy == 'strict':
                eq(block['resume_output']['known_effect_before'], wanted['known_effect_before'])
                eq(block['final']['checkpoint_after']['approval']['consumed'], wanted['consumed_after'])
            else:
                eq(block['resume_output']['known_effect_before'], 'UNKNOWN')
                eq(block['resume_output']['fault_reset'], {'consumed_before':True,'consumed_forged':False})
            cp = copy.deepcopy(arguments['checkpoint'])
            dispatch = wanted['dispatches']
            if dispatch:
                cp['phase'] = 'PENDING'
                cp['approval']['consumed'] = True
            phase = arguments['checkpoint']['phase']
            expected_resume = {'decision':wanted['decision'],
                'known_effect_before':wanted.get('known_effect_before', 'UNKNOWN'),
                'dispatches':dispatch,'result':wanted['result'] if phase == 'COMPLETED' else None,
                'approval_reuse':policy == 'fault',
                'scope_checks':dict.fromkeys(['source','actor','plan_sha256','call_id','tool','args'],True),
                'expiry_check':arguments['now'] < 10 if phase == 'READY' or policy == 'fault' else None,
                'unused_check':True if phase == 'READY' or policy == 'fault' else None,
                'checkpoint_after':copy.deepcopy(cp)}
            if policy == 'fault':expected_resume['fault_reset']={'consumed_before':True,'consumed_forged':False}
            eq(block['resume_output'], expected_resume)
            final = copy.deepcopy(expected_resume)
            if dispatch:
                final['result']=wanted['result']
                final['checkpoint_after']['phase']='COMPLETED'
                final['checkpoint_after']['completion']={'call_sha256':independent_digest(cp['call']),
                    'operation_id':'increment-1','result':wanted['result']}
            eq(block['final'],final)
    left, right = result['cases'][1:3]
    eq(left['resume_input_bytes'], right['resume_input_bytes'])
    for policy in ('strict','fault'):
        eq(left[policy]['resume_output'], right[policy]['resume_output'])
    return count


def mutation_examples(result):
    mutations=[]
    for name, mutate in [
        ('missing-case', lambda r:r['cases'].pop()),
        ('leaked-effect-knowledge', lambda r:r['cases'][2]['strict']['resume_output'].update(known_effect_before='APPLIED')),
        ('unknown-returned-success', lambda r:r['cases'][1]['strict']['final'].update(result=1)),
        ('duplicate-hidden', lambda r:r['cases'][2]['fault']['observer'].update(effect_after=1)),
        ('consumption-reset-hidden', lambda r:r['cases'][1]['fault']['final'].update(approval_reuse=False)),
        ('final-call-changed', lambda r:r['cases'][0]['strict']['final']['checkpoint_after']['call'].update(actor='bob')),
        ('completion-hash-changed', lambda r:r['cases'][4]['strict']['final']['checkpoint_after']['completion'].update(call_sha256='0'*64)),
        ('premature-resume-result', lambda r:r['cases'][0]['strict']['resume_output'].update(result=1)),
    ]:
        changed=copy.deepcopy(result);mutate(changed)
        try:check(changed)
        except AssertionError:mutations.append({'name':name,'rejected':True})
        else:raise AssertionError(name)
    return mutations
