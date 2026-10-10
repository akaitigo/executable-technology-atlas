"""Atlas: synthetic complete/incomplete process snapshots; no process observations."""
import importlib.util,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('browser_gate',ROOT/'browser-resource-gate.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=json.loads((ROOT/'browser-gate-policy.json').read_text());k=p['known_idle_exception'];known={x:k[x] for x in ['pid','ppid','lstart','comm']};known['cpu']=0
other={**known,'pid':42};unrelated={**known,'pid':43,'comm':'/usr/bin/python3'}
cases=[('complete_absent',[unrelated],True,True,'confirmed_absent'),('empty_output',[],True,False,'unobserved'),('acquisition_failed',[],False,False,'unobserved'),('parse_incomplete',[unrelated],False,False,'unobserved'),('absent_other_runtime',[other],True,False,'confirmed_absent'),('present_match',[known],True,True,'confirmed_matching_idle'),('present_cpu_boundary',[{**known,'cpu':1}],True,True,'confirmed_matching_idle'),('present_cpu_high',[{**known,'cpu':1.1}],True,False,'present_but_not_approved'),('reused_nonruntime_comm',[{**known,'comm':'/usr/bin/python3'}],True,False,'present_but_not_approved'),('changed_start',[{**known,'lstart':'different'}],True,False,'present_but_not_approved'),('changed_parent',[{**known,'ppid':2}],True,False,'present_but_not_approved'),('present_and_other',[known,other],True,False,'confirmed_matching_idle')]
results=[]
for name,rows,complete,passed,state in cases:
 a=m.assess_process_snapshot(rows,p,complete);assert a['process_condition_passed'] is passed and a['known_identity_state']==state
 results.append({'case':name,'expected_pass':passed,'expected_identity':state,'observed':a,'passed':True})
report={'title':'Atlas browser process condition check','passed':True,'synthetic_cases':len(cases),'checks':results,'actual_process_observations':0,'browser_executed':False,'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['browser-resource-gate.py','browser-gate-policy.json','check-browser-gate.py']}}
(ROOT/'observations/browser-gate-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'synthetic_cases':len(cases)}))
