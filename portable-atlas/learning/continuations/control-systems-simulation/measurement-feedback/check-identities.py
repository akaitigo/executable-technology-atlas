"""Atlas: synthetic identity boundaries; no process observation or model call."""
import copy,hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('gate',ROOT/'resource-gate.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
# These fake IDs are test input only and are never written into the actual policy.
known=[{'pid':1000001,'ppid':1,'lstart':'synthetic first','comm':'/fixture/Google Chrome','cpu_percent_at_most':1},
       {'pid':1000002,'ppid':1000001,'lstart':'synthetic second','comm':'/fixture/chrome-headless-shell','cpu_percent_at_most':1}]
p={'known_idle_identities':known,'known_idle_group_cpu_at_most':1.5};rows=[{**{k:x[k] for k in ['pid','ppid','lstart','comm']},'cpu':0.0} for x in known];checks=[]
def test(name,values,complete,expected):
    observed=g.assess(values,p,complete);assert observed['process_condition_passed'] is expected,name
    checks.append({'case':name,'expected':expected,'observed':observed})
test('known-idle',rows,True,True)
test('trusted-absence',[{'pid':1000099,'ppid':1,'lstart':'synthetic','comm':'/fixture/python3','cpu':0}],True,True)
test('unknown-observation',rows,False,False);test('empty',[],True,False)
for name,delta,expected in [('cpu-boundary',{'cpu':1.0},True),('cpu-over',{'cpu':1.1},False),('pid-reuse',{'comm':'/fixture/python3'},False),('changed-parent',{'ppid':9},False),('changed-start',{'lstart':'changed'},False)]:
    values=copy.deepcopy(rows);values[0].update(delta);test(name,values,True,expected)
values=copy.deepcopy(rows);values[0]['cpu']=1;values[1]['cpu']=0.5;test('group-boundary',values,True,True)
values[1]['cpu']=0.6;test('group-over',values,True,False)
for name,comm in [('new-chrome','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),('new-safari','/Applications/Safari.app/Contents/MacOS/Safari'),('new-chromium','/fixture/chromium'),('new-java','/fixture/java'),('active-benchmark','/fixture/pgbench')]:
    test(name,rows+[{'pid':1000099,'ppid':1,'lstart':'new','comm':comm,'cpu':0}],True,False)
report={'title':'Atlas synthetic identity checks','passed':True,'cases':checks,'real_process_observations':0,'target_processes_started':0,'actual_policy_not_modified':True,'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['resource-gate.py','check-identities.py']}}
(ROOT/'observations/identity-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'finite_cases':len(checks)}))
