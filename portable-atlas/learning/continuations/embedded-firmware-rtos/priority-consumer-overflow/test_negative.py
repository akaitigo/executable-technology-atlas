import json,copy,subprocess
from pathlib import Path
from oracle import check
from checker import browser_verify
P=Path(__file__).resolve().parent;fixtures=json.loads((P/'fixture.json').read_text());lit=json.loads((P/'oracle.json').read_text());pointer=json.loads((P/'evidence/current.json').read_text());raw=json.loads((P/'evidence'/pointer['raw']).read_text());base=raw['attempts'][0]['raw']['result'];caught=[]
for name in ['priority-as-fifo','accepted-as-completed','missed-drop','preemption','wrong-wait','fake-horizon-complete']:
 m=copy.deepcopy(base);inp=fixtures[0]['input'];literal=lit['priority-overflow']
 if name=='priority-as-fifo':m['completed']=list('ABC')
 elif name=='accepted-as-completed':m=copy.deepcopy(raw['attempts'][3]['raw']['result']);inp=fixtures[3]['input'];literal=lit['long-consumer'];m['counts']['completed']=3
 elif name=='missed-drop':m['dropped']=[]
 elif name=='preemption':m['intervals'][0]['end']=1
 elif name=='wrong-wait':m['events'][2]['wait']=0
 else:m=copy.deepcopy(raw['attempts'][11]['raw']['result']);inp=fixtures[11]['input'];literal=lit['accepted-fault'];m['counts']['completed']=3
 try:check(m,inp,literal)
 except AssertionError:caught.append(name)
 else:raise AssertionError(name)
b=json.loads((P/'evidence/browser.json').read_text())
for name in ['hardcoded-answer','SVG-not-actual','stale-applied','reset-retained']:
 m=copy.deepcopy(b)
 if name=='hardcoded-answer':m['cases'][18]['answer']='A,C,B fixed answer'
 elif name=='SVG-not-actual':m['cases'][0]['bars'][0]['end']='1'
 elif name=='stale-applied':m['stale']['new_retained']=False
 else:m['reset']['input-json']['after']['answer']='retained'
 try:browser_verify(m)
 except AssertionError:caught.append(name)
 else:raise AssertionError(name)
probes=[[],{},dict(fixtures[0]['input'],horizon=True),dict(fixtures[0]['input'],capacity=4),dict(fixtures[0]['input'],events=[dict(id='G',tick=0,priority=0,service=1)]),dict(fixtures[0]['input'],events=[dict(id='A',tick=0,priority=True,service=1)]),dict(fixtures[0]['input'],events=[dict(id='A',tick=0,priority=0,service=1.5)])]
for x in probes:
 r=subprocess.run(['python3','-B','model.py'],cwd=P,input=json.dumps(x),text=True,capture_output=True);assert r.returncode==2 and json.loads(r.stdout)['trace']==[]
print(json.dumps(dict(status='passed',mutants_rejected=len(caught),mutants=caught,schema_probes=len(probes))))
