"""Atlas: synthetic saved inputs only; no compiler, JVM, browser or child process."""
import copy,json,hashlib,ast
from pathlib import Path
from priority_launcher import priority_gate,cpu_gate
from resource_parse import parse_processes
from resource_policy import evaluate
ROOT=Path(__file__).resolve().parent
checks=[]
def check(ok,n):
    if not ok:raise AssertionError(n)
    checks.append(n)
for p in ROOT.glob('*.py'):ast.parse(p.read_text());checks.append('Python syntax '+p.name)
def deny(*a):raise PermissionError('simulated denial')
check(not priority_gate(lambda *a:0,deny)['verified_before_exec'],'priority denial fails before exec')
check(not priority_gate(lambda *a:0,lambda *a:None)['verified_before_exec'],'unchanged priority fails')
check(priority_gate(lambda *a:10,deny)['verified_before_exec'],'existing nice10 accepted without setter')
check(not cpu_gate(12,deny,lambda *a:(12,13))['verified_before_exec'],'CPU limit denial fails')
check(not cpu_gate(12,lambda *a:None,lambda *a:(99,99))['verified_before_exec'],'CPU limit mismatch fails')
check(cpu_gate(12,lambda *a:None,lambda *a:(12,13))['verified_before_exec'],'CPU verified')
ref=json.loads((ROOT/'records/root-browser-reference.json').read_text());rows=[dict(x,cpu_percent_one_core=0.0,rss_kib=10) for x in ref['identities']];rows.append({'pid':777,'ppid':1,'lstart':'Tue Oct 6 10:00:00 2026','command':'python3','cpu_percent_one_core':0.0,'rss_kib':10})
def ps(rs):return '\n'.join(f"{x['pid']} {x['ppid']} {x['cpu_percent_one_core']} {x['rss_kib']} {x['lstart']} {x['command']}" for x in rs)
base={'summary':{'read_success':True,'idle_percent':80,'memory_free_percent':50,'available_memory_estimate_gib':4},'cpu_count':12,'loadavg':[3,3,3],'coordination':{'root_slot':True,'root_gui_idle':True,'other_target_count':0,'authorization':'SIMULATED ONLY'},'root_browser_reference':ref,'root_batch_decision':{'scope':'kotlin-property-delegation-lifecycle','allowed':True,'identities':ref['identities']},'process_observation':parse_processes(ps(rows),0,777)}
check(evaluate(base)['allowed'],'normal trusted headroom')
for name,text,code in [('empty','',0),('partial',ps(rows)+'\nbad',0),('self missing',ps(rows[:-1]),0),('read denied',ps(rows),1)]:
    r=copy.deepcopy(base);r['process_observation']=parse_processes(text,code,777);check(not evaluate(r)['allowed'],name)
for name,fn in [('no root batch decision',lambda r:r.update(root_batch_decision=None)),('approved PID renamed nonbrowser',lambda r:r['process_observation']['processes'][0].update(command='renamed-service')),('root PID reused',lambda r:r['process_observation']['processes'][0].update(lstart='Tue Oct 6 10:00:00 2026')),('GUI busy',lambda r:r['coordination'].update(root_gui_idle=False)),('load at six',lambda r:r.update(loadavg=[6,3,3])),('memory low',lambda r:r['summary'].update(memory_free_percent=39)),('busy aggregate',lambda r:r['summary'].update(idle_percent=65)),('unknown heavy',lambda r:r['process_observation'].update(heavy=None))]:
    r=copy.deepcopy(base);fn(r);check(not evaluate(r)['allowed'],name)
for name,cpu,expected in [('new idle ordinary Chrome still unapproved',0.2,False),('active ordinary Chrome',1.01,False)]:
    extra=dict(rows[-1],pid=888,command='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',cpu_percent_one_core=cpu);r=copy.deepcopy(base);r['process_observation']=parse_processes(ps(rows+[extra]),0,777);check(evaluate(r)['allowed']==expected,name)
extra=dict(rows[-1],pid=888,ppid=90274,command=rows[0]['command']);r=copy.deepcopy(base);r['process_observation']=parse_processes(ps(rows+[extra]),0,777);check(not evaluate(r)['allowed'],'changed root child requires review')
approved_extra=dict(rows[-1],pid=888,command='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome');r=copy.deepcopy(base);r['root_batch_decision']['identities'].append({k:approved_extra[k] for k in ['pid','ppid','lstart','command']});renamed=dict(approved_extra,command='neutral-service');r['process_observation']=parse_processes(ps(rows+[renamed]),0,777);check(not evaluate(r)['allowed'],'nonroot approved PID renamed outside browser filter rejected')
from run import validate_gate_binding
decisionfile=ROOT/'records/synthetic-decision.json';decisionfile.write_text(json.dumps(base['root_batch_decision']))
binding = {'root_batch_decision':base['root_batch_decision'],'root_batch_decision_file':{'path':str(decisionfile),'sha256':hashlib.sha256(decisionfile.read_bytes()).hexdigest()},'policy_input_hashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['resources.py','resource_parse.py','resource_policy.py']},'root_browser_reference_sha256':hashlib.sha256((ROOT/'records/root-browser-reference.json').read_bytes()).hexdigest(),'root_browser_reference':ref}
validate_gate_binding(binding);checks.append('resource input binding accepted')
for name,fn in [('policy changed',lambda x:x['policy_input_hashes'].update({'resources.py':'bad'})),('root reference changed',lambda x:x['root_browser_reference'].update(identities=[]))]:
    x=copy.deepcopy(binding);fn(x)
    try:validate_gate_binding(x)
    except RuntimeError:checks.append(name+' rejected')
    else:raise AssertionError(name)
record={'project' :'Atlas','kind':'synthetic-input-checks','passed':True,'target_starts':0,'checks':checks,'count':len(checks),'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')}}
(ROOT/'records/preflight.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'passed':True,'count':len(checks),'target_starts':0}))
