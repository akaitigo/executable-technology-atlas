"""Read-only checker; --record explicitly refreshes module evidence."""
import sys
sys.dont_write_bytecode=True
import argparse, hashlib, itertools, json, platform, re
from datetime import datetime,timezone
from pathlib import Path
from model import detect, experiment, load_case, normalize, digest
from oracle import expected,HAND
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def compare(rows,mode,window,threshold):
    raw=detect(rows,mode,window,threshold); answer=expected(rows,mode,window,threshold)
    assert raw['alertIds']==answer['alertIds']
    windows=[{'success':r['id'],'failureIds':sorted(r['failureIds']),'count':r['count']} for r in raw['decisionChain'] if r['stage']=='success-evaluation']
    assert windows==answer['windows']
    return {'raw':raw,'independentOracle':answer,'rawSha256':digest(raw)}

def measure():
    cases=[]
    for case in HAND:
        rows=load_case(case)
        for window in [29,30,31]:
            for threshold in [2,3,4]:
                for mode in ['arrival','event-time']:
                    value=compare(rows,mode,window,threshold)
                    if window==30 and threshold==3:assert value['raw']['alertIds']==HAND[case][mode]
                    cases.append({'input':{'case':case,'mode':mode,'window':window,'threshold':threshold},'inputSha256':digest(rows),**value})
    permutations=[]
    for rows in itertools.permutations(load_case('normal')):
        for mode in ['arrival','event-time']:
            value=compare(list(rows),mode,30,3)
            if mode=='event-time':assert value['raw']['alertIds']==['s1']
            permutations.append({'arrivalIds':[r['id'] for r in rows],'mode':mode,**value})
    good=load_case('normal')[0]
    invalid=[None,[],{},dict(good,time=True),dict(good,time='100'),dict(good,time=-1),dict(good,time=1001),dict(good,time=1.5),dict(good,user='real-user'),dict(good,action='other'),dict(good,id=''),dict(good,id=[]),dict(good,extra=0)]
    for bad in invalid:
        normalized,chain=normalize([bad]);assert normalized==[] and chain[0]['status']=='invalid-rejected'
    conflicts=[good,dict(good,time=101)]
    try:normalize(conflicts)
    except ValueError:pass
    else:raise AssertionError('conflicting duplicate accepted')
    rejects=1+len(invalid)
    for kwargs in [{'mode':'bad'},{'window':True},{'window':0},{'window':61},{'threshold':True},{'threshold':0},{'threshold':11}]:
        try:detect([good],**kwargs)
        except ValueError:rejects+=1
        else:raise AssertionError(kwargs)
    for rows in [{},[good]*101]:
        try:normalize(rows)
        except ValueError:rejects+=1
        else:raise AssertionError('top-level input accepted')
    assert next(r for r in detect(load_case('boundary'))['decisionChain'] if r['stage']=='success-evaluation')['failureIds']==['f1','f2','f3']
    assert sum(x['status']=='duplicate-ignored' for x in detect(load_case('duplicate'))['normalization'])==1
    assert sum(x['status']=='invalid-rejected' for x in detect(load_case('invalid'))['normalization'])==2
    source=(ROOT/'model.py').read_text(); mutants=[]
    for name,before,after,case in [('exclusive-lower',"row['time']-window<=f['time']", "row['time']-window<f['time']",'boundary'),('duplicate-counted',"if row['id'] in seen:","if False and row['id'] in seen:",'duplicate')]:
        assert before in source
        namespace={'__file__':str(ROOT/'model.py')};exec(compile(source.replace(before,after),'<in-memory-intentional-fault>','exec'),namespace)
        rows=load_case(case);faulty=namespace['detect'](rows)['alertIds'];correct=expected(rows,'event-time',30,3)['alertIds'];assert faulty!=correct
        mutants.append({'intentionalFault':name,'case':case,'faultyAlertIds':faulty,'independentExpected':correct,'detected':True})
    return {'fixedInputs':{case:load_case(case) for case in HAND},'fixtureFileSha256':sha(ROOT/'fixtures.json'),'cases':cases,'permutations':permutations,'inputRejects':rejects,'intentionalFaultComparison':mutants}

def docs():
    for file in ['README.md','index.html','skills/atlas-detection-response-forensics/SKILL.md']:
        txt=(ROOT/file).read_text()
        links=re.findall(r'\]\(([^)]+)\)',txt) if file.endswith('.md') else re.findall(r'href="([^"]+)"',txt)
        for link in links:
            if link.startswith(('https://','http://','#')):continue
            target=((ROOT/file).parent/link.split('#')[0]).resolve()
            assert target.is_relative_to(ROOT) and target.exists(),link
    for file in ['README.md','index.html']:
        txt=(ROOT/file).read_text()
        for marker in ['未教材','実務判断','原典','800/92','800/61','800/86','chain of custody','event time']:
            assert marker in txt,(file,marker)
    from html.parser import HTMLParser
    class Fields(HTMLParser):
        def __init__(self):super().__init__();self.ids=[];self.in_title=False;self.title=''
        def handle_starttag(self,tag,attrs):
            if tag=='title':self.in_title=True
            self.ids.extend(v for k,v in attrs if k=='id')
        def handle_endtag(self,tag):
            if tag=='title':self.in_title=False
        def handle_data(self,data):
            if self.in_title:self.title+=data
    f=Fields();f.feed((ROOT/'index.html').read_text());assert f.title=='架空ログ検知・証拠の実験室';assert len(f.ids)==len(set(f.ids));assert all(x in f.ids for x in ['prediction','case','mode','window','threshold','run','raw'])

def files():return sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='bindings.json' and '__pycache__' not in p.parts)
p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();measured=measure()
if a.record:
    write(ROOT/'evidence/run.json',{'schemaVersion':1,'executedAt':datetime.now(timezone.utc).isoformat(),'command':'python3 -B check.py --record','environment':{'python':platform.python_version(),'system':platform.system(),'release':platform.release(),'machine':platform.machine()},'clock':'fixed synthetic integer event times; executedAt is real execution time','measurements':measured})
    write(ROOT/'evidence/bindings.json',{'algorithm':'sha256','files':{str(f.relative_to(ROOT)):sha(f) for f in files()},'sourceBinding':{'log management':'NIST SP 800-92 -> normalize and telemetry coverage; publication landing page verified, PDF timeout','incident response':'NIST SP 800-61 Rev.3 -> alert/incident distinction and Detect/Respond/Recover coverage','forensics':'NIST SP 800-86 §3/§4.2.2 -> hash limitations and preservation coverage','rule':'local synthetic 3 failures / 30 second rule, not a standard threshold','independentOracle':'oracle.py direct per-success set count plus HAND table, not separate-agent evaluation'},'recordedAt':datetime.now(timezone.utc).isoformat()})
docs()
assert json.loads((ROOT/'evidence/run.json').read_text())['measurements']==measured,'raw evidence mismatch'
assert json.loads((ROOT/'evidence/bindings.json').read_text())['files']=={str(f.relative_to(ROOT)):sha(f) for f in files()},'source/artifact digest mismatch'
ui=json.loads((ROOT/'evidence/ui-qa.json').read_text())
if ui['status']=='passed actual IAB HTTP QA':
    assert ui['ownedServerStopped'] and ui['ownedTabClosed']
    for observed in ui['rows']:
        row=dict(observed);got=row.pop('observedSha256');assert digest(row)==got
        if 'rawProjection' in row:
            observed=row['rawProjection'];inp=observed['input'];x=experiment(**inp);selected=x['selected']
            success=next(r for r in selected['decisionChain'] if r['stage']=='success-evaluation')
            oracle=expected(x['rawInput'],inp['mode'],inp['window'],inp['threshold'])
            recomputed={'input':inp,'inputSha256':x['inputSha256'],'normalizedSha256':selected['normalizedSha256'],'decisionChainSha256':selected['decisionChainSha256'],'alertIds':selected['alertIds'],'arrivalAlertIds':x['arrival']['alertIds'],'eventTimeAlertIds':x['eventTime']['alertIds'],'processingOrder':selected['processingOrder'],'failureIds':success['failureIds'],'count':success['count'],'oracleAlertIds':oracle['alertIds']}
            assert observed==recomputed,'actual UI raw projection mismatch'
        else:
            assert row['result']=='入力拒否'
            try:experiment(**row['input'])
            except ValueError:pass
            else:raise AssertionError('UI invalid API case no longer rejected')
print(json.dumps({'status':'passed' if ui['status']=='passed actual IAB HTTP QA' else 'core-passed-ui-pending','comparisons':len(measured['cases'])+len(measured['permutations']),'handCases':7,'inputRejects':measured['inputRejects'],'intentionalFaults':2,'roadmapLocalLinksSourceBinding':'passed','digestFiles':len(files()),'actualIABRows':len(ui.get('rows',[])),'mode':'record' if a.record else 'read-only'},ensure_ascii=False))
