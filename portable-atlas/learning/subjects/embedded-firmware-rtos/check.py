"""Read-only default, --record explicitly updates module evidence."""
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,itertools,json,platform,re
from pathlib import Path
from datetime import datetime,timezone
from model import SCHEDULES,admissible,counter,latency,experiment,digest
from oracle import ALL,LEGAL,HAND,counter_expected,latency_expected
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def measure():
    generated=[list(p) for p in itertools.permutations(['MR','MW','IR','IW']) if p.index('MR')<p.index('MW') and p.index('IR')<p.index('IW')]
    assert sorted(generated)==sorted(ALL)
    classification=[];counter_rows=[];rejects=0
    for order in ALL:
        assert admissible(order)==(order in LEGAL)
        classification.append({'requestedOrder':order,'admitted':order in LEGAL,'reason':'ISR run-to-completion' if order not in LEGAL else 'single-core legal'})
        for mode in ['naive','critical']:
            if order not in LEGAL:
                try:counter(order,mode)
                except ValueError:rejects+=1
                else:raise AssertionError(order)
                continue
            raw=counter(order,mode);answer=counter_expected(order,mode);assert raw['counter']==answer
            if mode=='critical':assert raw['counter']==2
            counter_rows.append({'input':{'order':order,'mode':mode},'raw':raw,'rawSha256':digest(raw),'independentExpected':answer})
    for name,expected in HAND.items():
        for mode in ['naive','critical']:assert counter(SCHEDULES[name],mode)['counter']==expected[mode]
    latency_rows=[]
    for mode in ['naive','critical']:
        for hold in range(2,11):
            for arrival in range(13):
                for deadline in range(1,13):
                    raw=latency(mode,hold,arrival,deadline);answer=latency_expected(mode,hold,arrival,deadline)
                    assert {k:raw[k] for k in answer}==answer
                    assert raw['start']>=arrival and raw['complete']==raw['start']+1
                    assert [e['tick'] for e in raw['events']]==sorted(e['tick'] for e in raw['events'])
                    latency_rows.append({'input':{'mode':mode,'hold':hold,'arrival':arrival,'deadline':deadline},'inputSha256':digest([mode,hold,arrival,deadline]),'raw':raw,'rawSha256':digest(raw),'independentExpected':answer})
    assert latency('critical',3,1,3)['meetsDeadline'] is True
    assert latency('critical',4,1,3)['meetsDeadline'] is False
    assert latency('critical',3,3,1)['wait']==0
    for kwargs in [{'schedule':'invalid-isr'},{'schedule':'unknown'},{'mode':'bad'},{'hold':True},{'hold':1},{'hold':11},{'arrival':True},{'arrival':-1},{'arrival':13},{'arrival':1.5},{'deadline':True},{'deadline':0},{'deadline':13}]:
        try:experiment(**kwargs)
        except ValueError:rejects+=1
        else:raise AssertionError(kwargs)
    for order in [None,[],['MR','MR','IR','IW'],['MW','MR','IR','IW'],['MR','MW',None,'IW']]:
        try:counter(order)
        except ValueError:rejects+=1
        else:raise AssertionError(order)
    source=(ROOT/'model.py').read_text();faults=[]
    for name,before,after in [('critical-deferral-missing',"if mode=='critical' and op=='IR' and masked:","if False and mode=='critical' and op=='IR' and masked:"),('deadline-exclusive','response<=deadline','response<deadline'),('unlock-too-late','start=max(arrival,unlock)','start=max(arrival,unlock+1)')]:
        assert before in source;ns={};exec(compile(source.replace(before,after),'<in-memory-intentional-fault>','exec'),ns)
        if name=='critical-deferral-missing':faulty=ns['counter'](SCHEDULES['preempt-main'],'critical')['counter'];answer=counter_expected(SCHEDULES['preempt-main'],'critical')
        elif name=='deadline-exclusive':faulty=ns['latency']('critical',3,1,3)['meetsDeadline'];answer=latency_expected('critical',3,1,3)['meetsDeadline']
        else:faulty=ns['latency']('critical',3,3,1)['wait'];answer=latency_expected('critical',3,3,1)['wait']
        assert faulty!=answer;faults.append({'fault':name,'faultyResult':faulty,'independentExpected':answer,'detected':True})
    return {'allInterleavingClassification':classification,'counterComparisons':counter_rows,'latencyComparisons':latency_rows,'inputRejects':rejects,'intentionalFaults':faults,'handCounter':HAND,'handLatency':{'hold3Arrival1Deadline3':True,'hold4Arrival1Deadline3':False,'arrivalAtUnlockWait':0}}

def docs():
    for file in ['README.md','index.html','skills/atlas-embedded-firmware-rtos/SKILL.md']:
        txt=(ROOT/file).read_text();links=re.findall(r'\]\(([^)]+)\)',txt) if file.endswith('.md') else re.findall(r'href="([^"]+)"',txt)
        for link in links:
            if link.startswith(('https://','http://','#')):continue
            target=((ROOT/file).parent/link.split('#')[0]).resolve();assert target.is_relative_to(ROOT) and target.exists(),link
    for file in ['README.md','index.html']:
        txt=(ROOT/file).read_text()
        for marker in ['未教材','実務判断','原典','interrupts.html','scheduling/index.html','mutexes.html','board_porting.html','dfu.html','watchdog.html','Safety','tick']:
            assert marker in txt,(file,marker)
    from html.parser import HTMLParser
    class Fields(HTMLParser):
        def __init__(self):super().__init__();self.ids=[];self.in_title=False;self.title=''
        def handle_starttag(self,t,a):
            if t=='title':self.in_title=True
            self.ids.extend(v for k,v in a if k=='id')
        def handle_endtag(self,t):
            if t=='title':self.in_title=False
        def handle_data(self,d):
            if self.in_title:self.title+=d
    f=Fields();f.feed((ROOT/'index.html').read_text());assert f.title=='ISR・main loop有限スケジュール実験室';assert len(f.ids)==len(set(f.ids));assert all(x in f.ids for x in ['prediction','schedule','mode','hold','arrival','deadline','run','raw'])
def files():return sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='bindings.json' and '__pycache__' not in p.parts)
p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();measured=measure()
if a.record:
    write(ROOT/'evidence/run.json',{'schemaVersion':1,'executedAt':datetime.now(timezone.utc).isoformat(),'environment':{'python':platform.python_version(),'system':platform.system(),'release':platform.release(),'machine':platform.machine()},'command':'python3 -B check.py --record','clock':'logical counter steps and separate synthetic latency ticks; no device timing','measurements':measured})
    write(ROOT/'evidence/bindings.json',{'algorithm':'sha256','files':{str(f.relative_to(ROOT)):sha(f) for f in files()},'recordedAt':datetime.now(timezone.utc).isoformat(),'sourceBinding':{'interrupt model':'Zephyr Interrupts Preventing Interruptions -> IRQ masking/latency; single-core non-nested simplified model','schedule':'Zephyr Scheduling -> ISR vs thread distinction; legal ordering scope','coverage':'Zephyr Board Porting/Build, Scheduling/Mutexes, Offloading ISR Work, DFU/Watchdog -> four unimplemented experiments','oracle':'oracle.py literal 6 orders, symbolic final writer, masked tick set; no model import','notClaimed':'real firmware, RTOS execution, device timing, Safety'}})
docs();assert json.loads((ROOT/'evidence/run.json').read_text())['measurements']==measured
assert json.loads((ROOT/'evidence/bindings.json').read_text())['files']=={str(f.relative_to(ROOT)):sha(f) for f in files()},'source/artifact digest mismatch'
ui=json.loads((ROOT/'evidence/ui-qa.json').read_text())
if ui['status']=='passed actual IAB HTTP QA':
    assert ui['ownedServerStopped'] and ui['ownedTabClosed']
    for observed in ui['rows']:
        row=dict(observed);got=row.pop('observedSha256');assert digest(row)==got
        if 'rawProjection' in row:
            obs=row['rawProjection'];x=experiment(**obs['input']);c=x['selected']['counter'];l=x['selected']['latency'];inp=x['input'];oracle={'counter':counter_expected(c['requestedOrder'],inp['mode']),'latency':latency_expected(inp['mode'],inp['hold'],inp['arrival'],inp['deadline'])}
            actual={'input':inp,'counter':c['counter'],'executedOrder':c['executedOrder'],'traceSha256':c['traceSha256'],'response':l['response'],'wait':l['wait'],'meetsDeadline':l['meetsDeadline'],'eventsSha256':l['eventsSha256'],'oracle':oracle}
            assert obs==actual,'actual UI raw projection mismatch'
        else:
            assert row['result']=='入力/未対応schedule拒否'
            try:experiment(**row['input'])
            except ValueError:pass
            else:raise AssertionError('invalid API no longer rejected')
print(json.dumps({'status':'passed' if ui['status']=='passed actual IAB HTTP QA' else 'core-passed-ui-pending','allInterleavings':6,'legal':3,'counterComparisons':len(measured['counterComparisons']),'latencyComparisons':len(measured['latencyComparisons']),'inputRejects':measured['inputRejects'],'intentionalFaults':3,'roadmapLocalLinksSourceBinding':'passed','digestFiles':len(files()),'actualIABRows':len(ui.get('rows',[])),'mode':'record' if a.record else 'read-only'},ensure_ascii=False))
