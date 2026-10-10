# SPDX-License-Identifier: Apache-2.0
import argparse,copy,hashlib,json,platform,re,sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
import model,oracle,route
HERE=Path(__file__).resolve().parent
SOURCE=['model.py','oracle.py','verify.py','route.py','serve.py','fixture.json','hand-oracle.json','index.html','source.html','README.md','VERIFICATION.md','coverage.json','sources.json','skills/atlas-priority-inheritance-blocking/SKILL.md']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def execute():
 fixture=json.loads((HERE/'fixture.json').read_text());hand=json.loads((HERE/'hand-oracle.json').read_text());assert fixture['cpu']==1 and fixture['locks']==['K'] and fixture['deadline_cases']==[4,2]
 runs=[]
 for mode in ['none','pi']:
    for due in fixture['deadline_cases']:
        r=model.simulate(mode,due);oracle.check(r,hand);runs.append(r)
 invalid=[]
 for mode,due in [('unknown',4),(None,4),(True,4),('',4),('pi',True),('pi',None),('pi','4'),('pi',-1),('pi',0),('pi',3),('pi',100)]:
    try:model.simulate(mode,due)
    except ValueError as e:invalid.append(dict(input=dict(mode=mode,h_deadline=due),status='EXPECTED_REFUSAL',error=str(e)))
    else:raise AssertionError('accepted invalid')
 mutations=[]
 for name in ['cpu','owner','effective','blocked','blocking','deadline']:
    r=copy.deepcopy(runs[2])
    if name=='cpu':r['cpu'][1]='M'
    elif name=='owner':r['rows'][1]['owner']='H'
    elif name=='effective':r['rows'][1]['tasks']['L']['effective']=1
    elif name=='blocked':r['rows'][1]['blocked']=[]
    elif name=='blocking':r['blocking']=0
    else:r['rows'][1]['tasks']['H']['deadline']=9
    try:oracle.check(r,hand)
    except AssertionError:mutations.append(dict(id=name,status='EXPECTED_REJECTION'))
    else:raise AssertionError(name)
 return dict(fixture=fixture,runs=runs,invalid_inputs=invalid,evidence_mutations=mutations,author_smoke=dict(supported=route.route('blocking'),unsupported=route.route('actual-rtos')),scope='finite abstract 1CPU 1lock; no real OS timing or safety certification')
def docs():
 for f in ['README.md','skills/atlas-priority-inheritance-blocking/SKILL.md']:
    for link in re.findall(r'\]\(([^)]+)\)',(HERE/f).read_text()):
        if not link.startswith(('https:','#')):assert ((HERE/f).parent/link.split('#')[0].split('?')[0]).resolve().exists(),link
 c=json.loads((HERE/'coverage.json').read_text());ids={r['id'] for r in json.loads((HERE/'sources.json').read_text())};assert 2<=len(c['next_experiments'])<=4 and all(r['source'] in ids for r in c['areas']+c['next_experiments'])
def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--record');g.add_argument('--seal-record',action='store_true');a=p.parse_args();started=datetime.now(timezone.utc).isoformat();raw=execute();name=a.record or 'attempt-01';folder=HERE/'observations'/name
 if a.record:
    assert re.fullmatch(r'attempt-[0-9]+',name);folder.mkdir(exist_ok=False);raw['attempt']=dict(command='python3 verify.py --record '+name,started_at_utc=started,completed_at_utc=datetime.now(timezone.utc).isoformat(),exit_code=0,toolchain=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),input_sha256=sha(HERE/'fixture.json'),hand_oracle_sha256=sha(HERE/'hand-oracle.json'),executed_source_sha256={f:sha(HERE/f) for f in ['model.py','oracle.py','verify.py']});(folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
 else:
    old=json.loads((folder/'raw.json').read_text());assert {k:v for k,v in old.items() if k!='attempt'}==raw
 docs();sources={f:sha(HERE/f) for f in SOURCE};qa=json.loads((HERE/'observations/ui-qa.json').read_text())
 if qa['status']=='passed':
    for k,f in [('observed_ui_sha256','index.html'),('observed_sources_sha256','sources.json'),('observed_coverage_sha256','coverage.json'),('observed_raw_sha256','observations/attempt-01/raw.json')]:assert qa[k]==sha(HERE/f)
    ui=json.loads((HERE/'observations/ui-matrix.json').read_text());assert len(ui['rows'])==36 and len({(r['mode'],r['h_deadline'],r['row']['time']) for r in ui['rows']})==36
    for r in ui['rows']:
        run=next(v for v in raw['runs'] if v['mode']==r['mode'] and v['h_deadline']==r['h_deadline']);assert r['row']==run['rows'][r['row']['time']]
        for key in ['blocking','finish','work','lateness','misses']:assert r[key]==run[key]
    state=json.loads((HERE/'observations/ui-state-transcript.json').read_text());assert state['prediction_changed']['prediction']=='guaranteed' and state['prediction_changed']['comparison']==state['prediction_changed']['answer']==''
    for name in ['mode_changed','deadline_changed']:assert all(state[name][k]=='' for k in ['prediction','comparison','answer'])
    assert [r['input'] for r in state['invalid']]==['-1','9','']
    for r in state['invalid']:assert all(r[k]==state['before_invalid'][k] for k in ['prediction','comparison','answer','state']) and r['error'].startswith('拒否')
 if a.record or a.seal_record:
    files=[f for f in folder.iterdir() if f.name!='receipt.json']+[f for f in (HERE/'observations').iterdir() if f.is_file() and f.name!='read-only-proof.json'];receipt=dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py '+('--seal-record' if a.seal_record else '--record '+name),exit_code=0,sources=sources,artifacts={str(f.relative_to(HERE)):sha(f) for f in files},checks=dict(hand_timeline_and_ownership='passed',conditions=4,boundary_states=36,expected_refusals=11,evidence_mutations=6,actual_iab=qa['status'],skill='author smoke; no independent AgentEval'));(folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 else:
    receipt=json.loads((folder/'receipt.json').read_text());assert receipt['sources']==sources
    for f,h in receipt['artifacts'].items():assert sha(HERE/f)==h,f
 print(json.dumps(dict(status='passed',conditions=4,boundary_states=36,blocking=[6,2],work_ticks=8,expected_refusals=11,evidence_mutations=6,record=a.record,seal_record=a.seal_record)))
if __name__=='__main__':main()
