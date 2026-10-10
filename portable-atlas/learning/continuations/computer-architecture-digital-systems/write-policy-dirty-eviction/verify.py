# SPDX-License-Identifier: Apache-2.0
import argparse,copy,hashlib,json,platform,re,sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
import cache,oracle,route
HERE=Path(__file__).resolve().parent
SOURCE=['cache.py','oracle.py','verify.py','route.py','serve.py','fixtures.json','hand-oracle.json','index.html','source.html','README.md','VERIFICATION.md','coverage.json','sources.json','skills/atlas-write-policy-dirty-eviction/SKILL.md']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def literal(row):
 s=row['after'];return [row['return_byte'],s['block_address'],s['cache_bytes'],s['dirty'],s['memory'][1],s['memory'][3],s['memory_write_transactions'],s['memory_written_bytes'],s['writebacks'],row['victim_block_address']]
def compare(result,expected,broken):
 mismatches=[]
 for row,spec in zip(result['trace'],expected):
    state=row['after'];effective=state['memory'][:]
    if state['valid']:
        base=state['block_address'];assert base in range(0,256,4) and len(state['cache_bytes'])==4
        if state['dirty']:effective[base:base+4]=state['cache_bytes']
        elif not broken:assert state['cache_bytes']==spec['logical_memory'][base:base+4]
    else:assert state['cache_bytes']==[] and not state['dirty']
    addresses=[a for a in range(256) if effective[a]!=spec['logical_memory'][a]]
    wrong_return=row['return_byte']!=spec['expected_return_byte']
    if addresses or wrong_return:mismatches.append(dict(step=row['step'],addresses=addresses,wrong_return=wrong_return,expected_return=spec['expected_return_byte'],actual_return=row['return_byte']))
    if not broken:assert not addresses and not wrong_return
    if result['policy']=='write-through':assert not state['dirty'] and state['memory']==spec['logical_memory']
    if row['input']['op']=='flush' and not broken:assert state['memory']==spec['logical_memory'] and not state['dirty']
 return mismatches

def execute():
 fixtures=json.loads((HERE/'fixtures.json').read_text());hand=json.loads((HERE/'hand-oracle.json').read_text());runs=[]
 for f in fixtures:
    expected=oracle.sequential(f['trace']);policies={}
    for policy in cache.POLICIES:
        result=cache.execute(f['trace'],policy);mismatch=compare(result,expected,policy.startswith('broken'));result['oracle']=expected;result['expected_mismatches']=mismatch;result['comparison']='EXPECTED_MISMATCH' if mismatch else 'MATCH'
        tables=hand['tables'].get(f['id'],{});target=tables.get(policy)
        if target is None and f['id'] in ['dirty-flush','clean-eviction']:target=tables['write-back'] if policy.startswith('broken') or f['id']=='clean-eviction' else None
        if target is not None:assert [literal(r) for r in result['trace']]==target,(f['id'],policy)
        predicted={'dirty-eviction':[(3,[1],False),(4,[1],True)],'store-allocate-boundary':[(2,[255],False),(3,[255],True)]}.get(f['id'],[]) if policy.startswith('broken') else []
        assert [(r['step'],r['addresses'],r['wrong_return']) for r in mismatch]==predicted
        policies[policy]=result
    runs.append(dict(id=f['id'],input=f,policies=policies))
 boundaries=[]
 for address in range(256):
    value=oracle.initial_memory()[address]^255;other=4 if address<4 else 0
    trace=[dict(op='store',address=address,value=value),dict(op='load',address=address),dict(op='load',address=other),dict(op='load',address=address),dict(op='flush')];spec=oracle.sequential(trace)
    for policy in cache.POLICIES:
        result=cache.execute(trace,policy);mismatch=compare(result,spec,policy.startswith('broken'))
        if policy.startswith('broken'):assert [(r['step'],r['addresses'],r['wrong_return']) for r in mismatch]==[(2,[address],False),(3,[address],True),(4,[address],False)]
        else:assert result['final']['memory']==spec[-1]['logical_memory']
        boundaries.append(dict(address=address,value=value,other=other,policy=policy,return_bytes=[r['return_byte'] for r in result['trace']],expected_mismatches=mismatch,transactions=result['final']['memory_write_transactions'],bytes=result['final']['memory_written_bytes']))
 invalid_cases=[('trace-type',None,'write-back'),('unknown-policy',[],'other'),('trace-too-long',[dict(op='flush')]*65,'write-back'),('op-type',[0],'write-back'),('unknown-op',[dict(op='read',address=0)],'write-back'),('missing-value',[dict(op='store',address=1)],'write-back'),('flush-address',[dict(op='flush',address=0)],'write-back'),('load-extra',[dict(op='load',address=0,value=1)],'write-back')]
 for key in ['address','value']:
    for name,value in [('negative',-1),('overflow',256),('bool',True),('fraction',1.5),('string','1'),('nonfinite','NaN')]:
        op=dict(op='store',address=1,value=99);op[key]=value;invalid_cases.append((key+'-'+name,[op],'write-back'))
 invalid=[]
 for id,trace,policy in invalid_cases:
    try:cache.execute(trace,policy)
    except ValueError as e:invalid.append(dict(id=id,input=trace,policy=policy,status='EXPECTED_REFUSAL',error=str(e)))
    else:raise AssertionError(id)
 assert len(invalid)==20
 return dict(runs=runs,address_boundary_runs=boundaries,invalid_inputs=invalid,fixed_cases=6,fixed_steps=66,boundary_cases=768,boundary_steps=3840,scope='finite logical model; no hardware/durability/ordering',author_routing=dict(dirty=route.route('dirty'),fsync=route.route('fsync')))
def docs():
 for f in ['README.md','skills/atlas-write-policy-dirty-eviction/SKILL.md']:
    for link in re.findall(r'\]\(([^)]+)\)',(HERE/f).read_text()):
        if not link.startswith(('https:','#')):assert ((HERE/f).parent/link.split('#')[0].split('?')[0]).resolve().exists(),link
 c=json.loads((HERE/'coverage.json').read_text());ids={r['id'] for r in json.loads((HERE/'sources.json').read_text())};assert 2<=len(c['next_experiments'])<=4 and all(r['source'] in ids for r in c['areas']+c['next_experiments'])
def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--record');g.add_argument('--seal-record',action='store_true');args=p.parse_args();started=datetime.now(timezone.utc).isoformat();raw=execute();name=args.record or 'attempt-01';folder=HERE/'observations'/name
 if args.record:
    assert re.fullmatch(r'attempt-[0-9]+',name);folder.mkdir(exist_ok=False);raw['attempt']=dict(command='python3 verify.py --record '+name,started_at_utc=started,completed_at_utc=datetime.now(timezone.utc).isoformat(),exit_code=0,toolchain=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),input_sha256=sha(HERE/'fixtures.json'),oracle_sha256=sha(HERE/'hand-oracle.json'),executed_source_sha256={f:sha(HERE/f) for f in ['cache.py','oracle.py','verify.py']})
    (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
 else:
    old=json.loads((folder/'raw.json').read_text());assert {k:v for k,v in old.items() if k!='attempt'}==raw
 docs();sources={f:sha(HERE/f) for f in SOURCE};qa=json.loads((HERE/'observations/ui-qa.json').read_text())
 if qa['status']=='passed':
    for k,f in [('observed_ui_sha256','index.html'),('observed_sources_sha256','sources.json'),('observed_coverage_sha256','coverage.json'),('observed_raw_sha256','observations/attempt-01/raw.json')]:assert qa[k]==sha(HERE/f)
    ui=json.loads((HERE/'observations/ui-matrix.json').read_text());assert len(ui['rows'])==12 and len(ui['refusals'])==3
    expected={('dirty-eviction',policy,step) for policy in cache.POLICIES for step in [2,3,4]}|{('dirty-flush','write-back',step) for step in [2,3]}|{('clean-eviction','write-back',1)}
    assert {(r['case'],r['policy'],r['step']) for r in ui['rows']}==expected
    assert all(r['status'].startswith('拒否') and r['retained']=='step 1/2: {"op":"load","address":4}' for r in ui['refusals'])
    for r in ui['rows']:
        result=next(f for f in raw['runs'] if f['id']==r['case'])['policies'][r['policy']];row=result['trace'][r['step']];assert r['literal']==literal(row)
 if args.record or args.seal_record:
    files=[f for f in folder.iterdir() if f.name!='receipt.json']+[f for f in (HERE/'observations').iterdir() if f.is_file() and f.name!='read-only-proof.json']
    receipt=dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py '+('--seal-record' if args.seal_record else '--record '+name),exit_code=0,sources=sources,artifacts={str(f.relative_to(HERE)):sha(f) for f in files},checks=dict(literal_and_memory='passed',fixed_expected_mismatch_cases=2,fixed_normal_policy_steps=44,fixed_fault_policy_steps=22,boundary_expected_mismatch_runs=256,expected_refusals=20,actual_iab=qa['status'],skill='author smoke; no independent AgentEval'))
    (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 else:
    receipt=json.loads((folder/'receipt.json').read_text());assert receipt['sources']==sources
    for f,h in receipt['artifacts'].items():assert sha(HERE/f)==h,f
 print(json.dumps(dict(status='passed',fixed_cases=6,policies=3,fixed_steps=66,address_boundary_cases=768,address_boundary_steps=3840,expected_refusals=20,record=args.record,seal_record=args.seal_record)))
if __name__=='__main__':main()
