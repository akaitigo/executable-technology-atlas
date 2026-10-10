# SPDX-License-Identifier: Apache-2.0
"""Independent authored transition table and hand arithmetic. Explicit --record only."""
import argparse
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import re
import sys
sys.dont_write_bytecode=True
import machine
import route

HERE=Path(__file__).resolve().parent
SOURCES=['machine.py','verify.py','route.py','serve.py','plans.json','tools.json','oracle.json','index.html',
         'README.md','VERIFICATION.md','coverage.json','sources.json','skills/atlas-agentic-systems/SKILL.md']


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def check_audit(result,edges):
    audit=result['audit'];previous='START';selected=0;value=None
    assert len(audit)<=4*result['budget']+2
    for i,row in enumerate(audit):
        assert row['index']==i and row['from_state']==previous
        assert row['to_state'] in edges.get(previous,[]),(previous,row['to_state'])
        assert row['steps']<=result['budget']
        if row['event']=='select':selected+=1
        assert row['steps']==selected
        if row['to_state']=='OBSERVE':value=row['detail']['result']['value']
        assert row['last_value']==value
        if row['to_state']=='EXECUTE':
            assert row['detail']['tool'] in ('read','add')
            assert row['detail']['authorized_plan']==(row['plan_source']=='authored')
        previous=row['to_state']
    assert previous==result['status'] and selected==result['steps'] and value==result['output']
    assert all(call['step']<=result['budget'] for call in result['calls'])
    assert result['authority_breach']==any(call['plan_source']=='tool-data' for call in result['calls'])
    assert sum(row['to_state']=='EXECUTE' for row in audit)==len(result['calls'])


def expected_case(fixture,policy,hand):
    expected=copy.deepcopy(hand[fixture['id']])
    if policy=='promote-result' and 'bad_override' in expected:expected=expected['bad_override']
    expected.pop('bad_override',None)
    expected['authority_breach']=(fixture['id']=='tainted-result' and policy=='promote-result')
    return expected


def execute():
    plans=json.loads((HERE/'plans.json').read_text());store=json.loads((HERE/'tools.json').read_text())
    oracle=json.loads((HERE/'oracle.json').read_text());edges=oracle['allowed_edges'];hand=oracle['hand_cases']
    assert {p['id'] for p in plans}==set(hand)
    assert store['counter']=={'value':4} and store['tainted']['value']==4
    runs=[]
    for fixture in plans:
        outcomes={};expectations={}
        for policy in ('data-only','promote-result'):
            result=machine.execute(fixture,store,policy);check_audit(result,edges)
            expected=expected_case(fixture,policy,hand)
            for key in ('status','steps','output','authority_breach'):assert result[key]==expected[key],(fixture['id'],key)
            assert len(result['calls'])==expected['calls']
            assert [a['pc'] for a in result['audit'] if a['event']=='select']==expected['pcs']
            if fixture['id']=='tainted-result':
                b=100 if policy=='promote-result' else 3
                assert result['calls'][1]['args']=={'a':4,'b':b}
                assert result['output']==4+b  # Hand prediction, not tool function call.
                if policy=='data-only':
                    assert any(a['detail'].get('proposal_ignored') for a in result['audit'])
                else:
                    assert any(a['event']=='promote-tool-data' for a in result['audit'])
            outcomes[policy]=result;expectations[policy]=expected
        runs.append(dict(id=fixture['id'],input=fixture,policies=outcomes,independent_oracle=expectations))
    rng=random.Random(20261005)
    for _ in range(100):
        n=rng.randint(1,5);program=[];values=[]
        for _ in range(n):
            if rng.random()<.3:
                program.append(dict(op='call',tool='read',args={'key':'counter'}));values.append(4)
            else:
                a,b=rng.randint(-100,100),rng.randint(-100,100)
                program.append(dict(op='call',tool='add',args={'a':a,'b':b}));values.append(a+b)
        program.append({'op':'end'})
        for budget in (n,n+1):
            result=machine.execute(dict(plan=program,budget=budget),store)
            check_audit(result,edges)
            assert result['status']==('ENDED' if budget==n+1 else 'BUDGET_EXHAUSTED')
            assert result['output']==values[-1] and len(result['calls'])==n
            # Independent phase induction for a straight authored plan: four edges per tool, then two end edges.
            expected_edges=[('START','PLAN')]
            for _ in range(n):expected_edges += [('PLAN','VALIDATE'),('VALIDATE','EXECUTE'),('EXECUTE','OBSERVE'),('OBSERVE','PLAN')]
            expected_edges += [('PLAN','VALIDATE'),('VALIDATE','ENDED')] if budget==n+1 else [('PLAN','BUDGET_EXHAUSTED')]
            assert [(a['from_state'],a['to_state']) for a in result['audit']]==expected_edges
    invalid=[]
    base=plans[0]
    for name,change in [('empty-plan',dict(plan=[])),('long-plan',dict(plan=[{'op':'end'}]*17)),
                        ('not-list',dict(plan='read')),('negative-budget',dict(budget=-1)),
                        ('bool-budget',dict(budget=True)),('too-large-budget',dict(budget=17))]:
        fixture=dict(base,**change)
        try:machine.execute(fixture,store)
        except ValueError as e:invalid.append(dict(id=name,input=fixture,error=str(e)))
        else:raise AssertionError(name)
    invalid_options=[]
    for name,fixture,storage,policy in [('fixture-object',None,store,'data-only'),('store',base,{},'data-only'),('policy',base,store,'unknown')]:
        try:machine.execute(fixture,storage,policy)
        except ValueError as e:invalid_options.append(dict(id=name,error=str(e)))
        else:raise AssertionError(name)
    return dict(machine_version=machine.VERSION,plans_sha256=digest(HERE/'plans.json'),tools_sha256=digest(HERE/'tools.json'),
                oracle_sha256=digest(HERE/'oracle.json'),tools=store,allowed_edges=edges,runs=runs,randomized_straight_plans=100,
                invalid_inputs=invalid,invalid_options=invalid_options,
                oracle_scope='hand case status/step/value/call/pc predictions plus independent transition table and straight-plan phase induction; no LLM evaluator',
                author_routing_smoke={'budget':route.route('budget'),'llm-agent':route.route('llm-agent')})


def docs_check(record):
    planned={HERE/'observations/raw.json',HERE/'observations/receipt.json'}
    for f in ['README.md','skills/atlas-agentic-systems/SKILL.md']:
        for link in re.findall(r'\]\(([^)]+)\)',(HERE/f).read_text()):
            if not link.startswith(('https:','#')):
                target=((HERE/f).parent/link.split('#')[0]).resolve()
                assert target.exists() or (record and target in planned),link
    text=(HERE/'README.md').read_text();assert all(w in text for w in ['前提','主要概念','実務判断','限界','原典','未教材'])
    coverage=json.loads((HERE/'coverage.json').read_text());sources=json.loads((HERE/'sources.json').read_text());ids={s['id'] for s in sources}
    assert 2<=len(coverage['next_experiments'])<=4
    for area in coverage['areas']+coverage['next_experiments']:assert area['source'] in ids and area['question']
    assert all(s in (HERE/'index.html').read_text() for s in ['coverage.json','sources.json','README.md'])
    assert route.route('budget')['status']=='supported' and route.route('llm-agent')['status']=='unsupported'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true');args=parser.parse_args()
    data=execute();docs_check(args.record);sources={f:digest(HERE/f) for f in SOURCES};folder=HERE/'observations'
    qa=json.loads((folder/'ui-qa.json').read_text())
    if qa['status']=='passed':
        assert qa['observed_ui_sha256']==digest(HERE/'index.html'),'UI changed after observation'
        matrix=json.loads((folder/'ui-matrix.json').read_text())['rows']
        assert len(matrix)==36 and len({(r['id'],r['policy']) for r in matrix})==36
        for row in matrix:
            result=next(r for r in data['runs'] if r['id']==row['id'])['policies'][row['policy']]
            for ui_key,key in [('status','status'),('value','output'),('steps','steps'),('authority_breach','authority_breach')]:assert row[ui_key]==result[key]
            assert row['calls']==len(result['calls'])
            for key in ['index','pc','plan_source']:assert row[key]==result['audit'][-1][key]
    if args.record:
        (folder/'raw.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        names=['observations/raw.json','observations/ui-qa.json']
        for optional in ['ui-matrix.json','preview-http.log','iteration-failure.txt','default-bind.txt','skill-smoke.json']:
            if (folder/optional).exists():names.append('observations/'+optional)
        receipt=dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py --record',
                     environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),
                     input_sha256=data['plans_sha256'],tools_sha256=data['tools_sha256'],sources=sources,
                     artifacts={f:digest(HERE/f) for f in names},checks=dict(runtime_oracle='passed',roadmap_links_binding='passed',
                     author_routing_smoke='passed; not independent AgentEval',actual_iab_qa=json.loads((folder/'ui-qa.json').read_text())['status']))
        (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    else:
        receipt=json.loads((folder/'receipt.json').read_text());assert receipt['sources']==sources,'source changed; explicit --record required'
        assert receipt['input_sha256']==data['plans_sha256'] and receipt['tools_sha256']==data['tools_sha256']
        for f,h in receipt['artifacts'].items():assert digest(HERE/f)==h,f
        assert data==json.loads((folder/'raw.json').read_text()),'runtime replay mismatch'
        qa=json.loads((folder/'ui-qa.json').read_text())
        if qa.get('observed_raw_sha256'):assert qa['observed_raw_sha256']==digest(folder/'raw.json'),'UI raw binding changed'
    print(json.dumps(dict(status='passed',record=args.record,runs=len(data['runs']),randomized_straight_plans=100,
                         invalid_inputs=len(data['invalid_inputs']),invalid_options=len(data['invalid_options']))))

if __name__=='__main__':main()
