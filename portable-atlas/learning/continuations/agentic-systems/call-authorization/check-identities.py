"""Atlas: pure resource-classification examples; no process or model execution."""
import copy, hashlib, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('gate',ROOT/'resource-gate.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
p=json.loads((ROOT/'gate-policy.json').read_text())
rows=[{**{k:x[k] for k in ['pid','ppid','lstart','comm']},'cpu':0.0} for x in p['known_idle_identities']]
main=next(i for i,x in enumerate(rows) if x['pid']==665)
idle=next(i for i,x in enumerate(rows) if x['pid']!=665)
checks=[]
def test(name,values,complete,expected):
    out=g.assess(values,p,complete);assert out['process_condition_passed'] is expected,name
    checks.append({'case':name,'expected':expected,'observed':out})
test('all-known-idle',rows,True,True)
test('trusted-absence',[{'pid':999999,'ppid':1,'lstart':'fixture','comm':'/usr/bin/python3','cpu':0.0}],True,True)
test('ps-incomplete',rows,False,False)
test('empty',[],True,False)
for name,index,delta,expected in [
    ('main-at-10',main,{'cpu':10.0},True),('main-over-10',main,{'cpu':10.1},False),
    ('other-at-1',idle,{'cpu':1.0},True),('other-over-1',idle,{'cpu':1.1},False),
    ('pid-reused-nonbrowser',main,{'comm':'/usr/bin/python3'},False),
    ('ppid-changed',main,{'ppid':99999},False),('start-changed',main,{'lstart':'different start'},False),
]:
    r=copy.deepcopy(rows);r[index].update(delta);test(name,r,True,expected)
for amount,expected in [(12,True),(13,False)]:
    r=copy.deepcopy(rows)
    for x in r[:amount]:x['cpu']=1.0
    test('group-'+str(amount),r,True,expected)
for label,comm in [('new-browser','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),('new-java','/jdk/bin/java'),('benchmark','/usr/local/bin/pgbench')]:
    test(label,rows+[{'pid':999999,'ppid':1,'lstart':'new fixture','comm':comm,'cpu':0.0}],True,False)
report={'title':'Atlas scoped runtime classification','passed':True,'cases':checks,'processes_observed':0,'processes_started':0,
        'sources':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['resource-gate.py','gate-policy.json','check-identities.py']}}
(ROOT/'observations/identity-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':True,'finite_cases':len(checks)}))
