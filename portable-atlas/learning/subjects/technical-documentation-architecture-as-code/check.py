import sys
sys.dont_write_bytecode=True
import argparse,copy,datetime,hashlib,json,platform,re
from html.parser import HTMLParser
from pathlib import Path
import api,model,oracle
R=model.ROOT
p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
def sha(b): return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def encoded(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
rows=[]
for scenario in model.SCENARIOS:
    row=model.experiment(scenario);row['oracle']=oracle.verify(row)
    row['inputSha256']=sha(encoded(row['contract']));row['rawSha256']=sha(encoded(row['result']));rows.append(row)
base=rows[0]
assert base['manifest']['implementationSha256']==sha((R/'api.py').read_bytes())
assert base['manifest']['contractSha256']==sha(encoded(json.loads((R/'contract.json').read_text())))
assert base['manifest']['artifacts']==base['observedArtifactSha256']
generated,manifest=model.generate(base['contract'],(R/'api.py').read_bytes())
assert generated==base['artifacts'] and manifest==base['manifest']
assert sha(b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
comparisons=0
for lower in range(-2,3):
    for upper in range(lower,4):
        for value in range(-100,101):
            expect=lower if value<lower else upper if value>upper else value
            assert api.clamp(value,lower,upper)==expect;comparisons+=1
for left in range(-100,101):
    for right in range(-100,101):
        assert api.add(left,right)==sum([left,right]);comparisons+=1
rejects=[]
for label,change in [
 ('schema',lambda c:c.update(schema=2)),('extra',lambda c:c.update(extra=1)),('empty',lambda c:c.update(functions=[])),
 ('title newline',lambda c:c.update(title='x\ny')),('duplicate',lambda c:c['functions'].append(copy.deepcopy(c['functions'][0]))),
 ('function',lambda c:c['functions'][0].update(name='divide')),('summary html',lambda c:c['functions'][0].update(summary='<script>')),
 ('bool argument',lambda c:c['functions'][0]['examples'][0].update(args=[True,0,10])),
 ('float argument',lambda c:c['functions'][0]['examples'][0].update(args=[1.0,0,10])),
 ('large argument',lambda c:c['functions'][0]['examples'][0].update(args=[101,0,10])),
 ('reversed bounds',lambda c:c['functions'][0]['examples'][0].update(args=[1,10,0])),
 ('arity',lambda c:c['functions'][0]['examples'][0].update(args=[1,2])),
 ('arbitrary stdout',lambda c:c['functions'][0]['examples'][0].update(stdout='hello\n')),
 ('no examples',lambda c:c['functions'][0].update(examples=[]))]:
    c=copy.deepcopy(base['contract']);change(c)
    try:model.validate(c)
    except ValueError as e:rejects.append({'input':label,'error':str(e)})
    else:raise AssertionError(label)
faults=[{'scenario':row['scenario'],'failures':row['result']['failures'],'independentOracle':'caught'} for row in rows if row['result']['status']=='rejected']
class Page(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[]
    def handle_starttag(self,t,attrs):
        d=dict(attrs)
        if 'id'in d:self.ids.append(d['id'])
        if t=='a' and 'href'in d:self.links.append(d['href'])
page=Page();page.feed((R/'index.html').read_text());assert len(page.ids)==len(set(page.ids))
for key in ['prediction','scenario','run','raw','answer','roadmap']:assert key in page.ids
readme=(R/'README.md').read_text();html=(R/'index.html').read_text()
for url in oracle.LOCATORS.values():assert url in readme and url in html
for marker in ['OpenAPI','Sphinx','C4','SLSA']:assert marker in readme and marker in html
for link in re.findall(r'\]\(([^)]+)\)',readme)+page.links:
    if link.startswith(('https://','#')):continue
    if a.record and link in {'evidence/run.json','evidence/bindings.json','evidence/ui-qa.json','evidence/routing-smoke.json'} and not (R/link).exists():continue
    target=(R/link.split('#')[0]).resolve();assert target.is_relative_to(R) and target.exists(),link
ui_path=R/'evidence/ui-qa.json';ui=None
if ui_path.exists():
    ui=json.loads(ui_path.read_text());assert ui['status']=='passed'
    assert len(ui['rows'])==8
    for observed in ui['rows']:
        expected=next(x for x in rows if x['scenario']==observed['scenario'])
        projection={'scenario':expected['scenario'],'status':expected['result']['status'],'failures':expected['result']['failures'],'stdout':[x['stdout'] for x in expected['result']['snippets']],'artifacts':expected['observedArtifactSha256']}
        assert observed['projection']==projection
        assert observed['projectionSha256']==sha(encoded(projection))
run={'schema':1,'executedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'python':platform.python_version(),'system':platform.system(),'release':platform.release(),'machine':platform.machine()},'command':'python3 -B check.py --record','measurements':{'scenarios':rows,'apiComparisons':comparisons,'inputRejects':rejects,'intentionalFaults':faults},'sourceBinding':oracle.LOCATORS}
if a.record:(R/'evidence/run.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n')
else:
    saved=json.loads((R/'evidence/run.json').read_text());assert saved['measurements']==run['measurements'] and saved['sourceBinding']==run['sourceBinding']
files={str(f.relative_to(R)):sha(f.read_bytes()) for f in sorted(R.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f!=R/'evidence/bindings.json'}
if a.record:(R/'evidence/bindings.json').write_text(json.dumps({'schema':1,'sha256':files,'sourceBinding':oracle.LOCATORS},ensure_ascii=False,indent=2)+'\n')
else:assert json.loads((R/'evidence/bindings.json').read_text())['sha256']==files
print(json.dumps({'status':'passed' if ui else 'core-passed-ui-pending','scenarios':len(rows),'actualSnippetRuns':sum(len(x['result']['snippets']) for x in rows),'apiComparisons':comparisons,'inputRejects':len(rejects),'intentionalFaults':len(faults),'roadmapLocalLinksSourceBinding':'passed','digestFiles':len(files),'actualIABRows':len(ui['rows']) if ui else 0,'mode':'record' if a.record else 'read-only'}))
