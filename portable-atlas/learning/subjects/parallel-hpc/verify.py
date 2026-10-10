# SPDX-License-Identifier: Apache-2.0
"""Independent closed-form and enumerated coverage oracle; explicit --record."""
import argparse,hashlib,json,platform,random,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
import parallel_sum as runner,route
HERE=Path(__file__).resolve().parent
SOURCES=['parallel_sum.py','verify.py','route.py','serve.py','fixtures.json','README.md','VERIFICATION.md','index.html','coverage.json','sources.json','skills/atlas-parallel-hpc/SKILL.md']
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def closed(a,b):return (a+b-1)*(b-a)//2

def check(f,r):
    target=closed(f['start'],f['stop']);assert r['sequential_result']==target
    spans=r['partition'];covered=[n for a,b in spans for n in range(a,b)];full=list(range(f['start'],f['stop']))
    assert len(covered)==len(set(covered)) and covered==full[:len(covered)]
    expected_missing=full[len(covered):];assert r['missing_values']==expected_missing
    assert r['workers_requested']==r['workers_started']==2 and r['owned_remaining']==0
    assert all(not x['alive'] and x['exit_code'] is not None for x in r['cleanup'])
    assert len({x['pid'] for x in r['cleanup']})==2
    assert all(x['pid']>0 for x in r['cleanup'])
    assert len([e for e in r['timeline'] if e['event']=='worker_started'])==2
    assert len([e for e in r['timeline'] if e['event']=='worker_joined'])==2
    assert all(a['at_ms']<=b['at_ms'] for a,b in zip(r['timeline'],r['timeline'][1:]))
    assert r['sequential_elapsed_ms']>=0 and r['parallel_elapsed_ms']>=0
    if f['behavior']=='normal':
        assert r['status']=='OK'
        expected=[closed(a,b) for a,b in spans];assert r['partial_results']==expected and r['parallel_result']==sum(expected)
        assert r['comparison']==('MATCH' if sum(expected)==target else 'MISMATCH')
        assert all(x['exit_code']==0 for x in r['cleanup'])
        assert all(m['status']=='OK' and m['count']==m['bounds'][1]-m['bounds'][0] for m in r['messages'])
    elif f['behavior']=='worker-error':
        assert r['status']=='WORKER_ERROR' and r['parallel_result'] is None and r['comparison']=='NO_RESULT'
        assert r['partial_results'][0]==closed(*spans[0]) and r['partial_results'][1] is None
        assert any(m['status']=='ERROR' and 'authored worker1 failure' in m['error'] for m in r['messages'])
        assert all(x['exit_code']==0 for x in r['cleanup']) # exception reported explicitly by worker, process shutdown succeeds
    else:
        assert r['status']=='TIMEOUT' and r['parallel_result'] is None and r['comparison']=='NO_RESULT'
        assert r['partial_results']==[None,None]
        assert all(x['reason']=='deadline_cleanup' and x['exit_code']!=0 for x in r['cleanup'])
        assert len([e for e in r['timeline'] if e['event']=='terminate_owned'])==2

def semantic(r):return {k:r[k] for k in ['id','policy','behavior','input','partition','sequential_result','partial_results','parallel_result','comparison','status','missing_values','workers_requested','workers_started','owned_remaining']}

def execute():
    fixtures=json.loads((HERE/'fixtures.json').read_text());runs=[]
    for f in fixtures:
        policies={}
        for policy in ('balanced','drop-remainder'):
            r=runner.execute(f,policy);check(f,r);policies[policy]=r
        runs.append(dict(id=f['id'],input=f,closed_form_target=closed(f['start'],f['stop']),policies=policies))
    rng=random.Random(20261005);partition_checks=[]
    for i in range(100):
        a=rng.randint(-100,100);b=a+rng.randint(0,100)
        for policy in ('balanced','drop-remainder'):
            spans=runner.partition(a,b,policy);flat=[n for lo,hi in spans for n in range(lo,hi)]
            assert len(flat)==len(set(flat));assert flat==list(range(a,b))[:len(flat)]
            if policy=='balanced':assert len(flat)==b-a and sum(closed(*span) for span in spans)==closed(a,b)
            else:assert len(flat)==2*((b-a)//2)
            partition_checks.append(dict(start=a,stop=b,policy=policy,spans=spans,covered=len(flat),closed_target=closed(a,b)))
    invalid=[];base=fixtures[0]
    for name,f,policy in [('not-object',None,'balanced'),('bool-start',dict(base,start=True),'balanced'),('float-stop',dict(base,stop=8.0),'balanced'),('reversed',dict(base,start=10),'balanced'),('too-large',dict(base,stop=10001),'balanced'),('too-many',dict(base,start=-10000,stop=10000),'balanced'),('policy',base,'unknown'),('behavior',dict(base,behavior='unknown'),'balanced')]:
        try:runner.execute(f,policy)
        except ValueError as e:invalid.append(dict(id=name,error=str(e)))
        else:raise AssertionError(name)
    assoc=runner.associativity();assert assoc['integer_left']==assoc['integer_right']==1 and assoc['float_left']==1.0 and assoc['float_right']==0.0
    return dict(version=runner.VERSION,seed=20261005,fixture_sha256=digest(HERE/'fixtures.json'),runs=runs,partition_oracle=partition_checks,invalid_inputs=invalid,associativity=assoc,author_routing_smoke={'integer-sum':route.route('integer-sum'),'mpi-cluster':route.route('mpi-cluster')},scope='Observed local spawn workers / integer sum correctness. No timing guarantee, MPI, SIMD, cluster or throughput benchmark.')

def docs_check(record):
    planned={HERE/'observations/raw.json',HERE/'observations/receipt.json'}
    for f in ['README.md','skills/atlas-parallel-hpc/SKILL.md']:
        for link in re.findall(r'\]\(([^)]+)\)',(HERE/f).read_text()):
            if not link.startswith(('https:','#')):
                target=((HERE/f).parent/link.split('#')[0]).resolve();assert target.exists() or record and target in planned,link
    assert all(s in (HERE/'README.md').read_text() for s in ['前提','主要概念','実務判断','限界','原典','未教材'])
    coverage=json.loads((HERE/'coverage.json').read_text());sources=json.loads((HERE/'sources.json').read_text());ids={s['id'] for s in sources}
    assert 2<=len(coverage['next_experiments'])<=4
    for a in coverage['areas']+coverage['next_experiments']:assert a['source'] in ids and a['question']
    assert all(s in (HERE/'index.html').read_text() for s in ['coverage.json','sources.json','README.md'])

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--record',action='store_true');g.add_argument('--seal-record',action='store_true');args=p.parse_args();raw=execute();docs_check(args.record)
    folder=HERE/'observations';source_hashes={f:digest(HERE/f) for f in SOURCES};qa=json.loads((folder/'ui-qa.json').read_text())
    if qa['status']=='passed':
        for key,f in [('observed_ui_sha256','index.html'),('observed_sources_sha256','sources.json'),('observed_coverage_sha256','coverage.json')]:assert qa[key]==digest(HERE/f)
        rows=json.loads((folder/'ui-matrix.json').read_text())['rows'];assert len(rows)==16 and len({(r['id'],r['policy']) for r in rows})==16
        for row in rows:
            result=next(r for r in raw['runs'] if r['id']==row['id'])['policies'][row['policy']]
            for key in ['status','comparison','sequential_result','parallel_result','partial_results','owned_remaining','missing_values']:assert row[key]==result[key]
    if args.seal_record:
        recorded=json.loads((folder/'raw.json').read_text())
        assert recorded['fixture_sha256']==raw['fixture_sha256']
        for old,new in zip(recorded['runs'],raw['runs']):
            for policy in ['balanced','drop-remainder']:
                check(old['input'],old['policies'][policy]);assert semantic(old['policies'][policy])==semantic(new['policies'][policy])
        assert recorded['partition_oracle']==raw['partition_oracle'] and recorded['associativity']==raw['associativity'] and recorded['invalid_inputs']==raw['invalid_inputs']
    if args.record or args.seal_record:
        if args.record:
            assert not qa.get('observed_raw_sha256'),'Use --seal-record to preserve the observed raw'
            (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
        # A later --record reruns real workers, so its observation is a new raw rather than a visual-QA hash update.
        if qa.get('observed_raw_sha256'):assert qa['observed_raw_sha256']==digest(folder/'raw.json'),'UI raw observation belongs to previous execution; retain raw and use --seal-record for final evidence'
        names=['observations/raw.json','observations/ui-qa.json']
        for name in ['ui-matrix.json','preview-http.log','default-bind.txt','skill-smoke.json','iteration-failure.txt']:
            if (folder/name).exists():names.append('observations/'+name)
        receipt=dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py --seal-record' if args.seal_record else 'python3 verify.py --record',environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine(),start_method='spawn',workers_at_once=2),inputs=dict(fixtures=raw['fixture_sha256']),sources=source_hashes,artifacts={f:digest(HERE/f) for f in names},checks=dict(closed_form_partition_cleanup='passed',docs='passed',author_smoke='passed; not independent AgentEval',actual_iab_qa=qa['status']))
        (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    else:
        receipt=json.loads((folder/'receipt.json').read_text());assert receipt['sources']==source_hashes
        for f,h in receipt['artifacts'].items():assert digest(HERE/f)==h,f
        recorded=json.loads((folder/'raw.json').read_text())
        assert recorded['fixture_sha256']==raw['fixture_sha256']
        for old,new in zip(recorded['runs'],raw['runs']):
            for policy in ['balanced','drop-remainder']:
                check(old['input'],old['policies'][policy]);assert semantic(old['policies'][policy])==semantic(new['policies'][policy])
        assert recorded['partition_oracle']==raw['partition_oracle'] and recorded['associativity']==raw['associativity'] and recorded['invalid_inputs']==raw['invalid_inputs']
        if qa.get('observed_raw_sha256'):assert qa['observed_raw_sha256']==digest(folder/'raw.json')
    print(json.dumps(dict(status='passed',record=args.record,seal_record=args.seal_record,cases=8,policies=2,actual_worker_runs=16,workers_at_once=2,owned_remaining=0,partition_vectors=100,invalid_inputs=8,associativity_witness='integer1/1,float1/0')))
if __name__=='__main__':main()
