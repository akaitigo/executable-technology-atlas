import json,copy,subprocess
from pathlib import Path
from oracle import check
from checker import validate_browser
P=Path(__file__).resolve().parent
inp=json.loads((P/'cases.json').read_text())[0]['input'];lit=json.loads((P/'oracle.json').read_text())['normal-5']
r=json.loads(subprocess.check_output(['node','runner.mjs','normal-5'],cwd=P))['result']
rejected=[]
for field,value in [('alpha','1/2'),('render','20'),('stateAfterRender','5'),('current','25'),('totalTicks',3),('remainderMs',0)]:
    m=copy.deepcopy(r);m['trace'][0][field]=value
    try:check(m,inp,lit)
    except AssertionError:rejected.append(field)
    else:raise AssertionError(field)
b=json.loads((P/'evidence/browser.json').read_text())
for name in ['pixel','answer','stale','reset']:
    m=copy.deepcopy(b)
    if name=='pixel':m['cases'][0]['raw']['draws'][0]['rgba']=[0,0,0,0]
    elif name=='answer':m['cases'][0]['answer']='hardcoded wrong answer'
    elif name=='stale':m['stale']['new_retained']=False
    else:m['reset']['override']['passed']=False
    try:validate_browser(m)
    except AssertionError:rejected.append(name)
    else:raise AssertionError(name)
for inp in [[],{},dict(framesMs=[],mode='NORMAL'),dict(framesMs=[True],mode='NORMAL'),dict(framesMs=[101],mode='NORMAL'),dict(framesMs=[0]*9,mode='NORMAL'),dict(framesMs=[None],mode='NORMAL')]:
    r=subprocess.run(['node','runner.mjs','normal-5',json.dumps(inp)],cwd=P,text=True,capture_output=True);assert r.returncode==2 and json.loads(r.stdout)['result']['trace']==[]
print(json.dumps(dict(status='passed',mutants_rejected=len(rejected),mutants=rejected,schema_probes=7)))
